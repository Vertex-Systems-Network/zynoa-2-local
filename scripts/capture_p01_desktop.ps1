# P01-T10: actual Windows Tauri process screenshot, not a browser preview.
param(
    [Parameter(Mandatory = $true)][int]$TargetPid,
    [Parameter(Mandatory = $true)][string]$OutputDirectory,
    [Parameter(Mandatory = $true)][string]$SourceSha,
    [Parameter(Mandatory = $true)][string]$BuiltSha,
    [switch]$M26Only
)
$ErrorActionPreference = 'Stop'
if ($SourceSha -notmatch '^[0-9a-f]{40}$') { throw 'ZYN-SCREEN-001: invalid source commit' }
if ($BuiltSha -notmatch '^[0-9a-f]{40}$' -or $BuiltSha -ne $SourceSha) {
    throw 'ZYN-SCREEN-015: screenshot source and checked-out build commits must match'
}
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class ZynoaScreenWin32 {
    [StructLayout(LayoutKind.Sequential)]
    public struct Rect { public int Left; public int Top; public int Right; public int Bottom; }
    [DllImport("user32.dll")]
    public static extern bool GetWindowRect(IntPtr hwnd, out Rect rect);
    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr hwnd);
    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hwnd);
    [DllImport("user32.dll", SetLastError=true)]
    public static extern bool MoveWindow(IntPtr hwnd, int x, int y, int width, int height, bool repaint);
    // DWMWA_EXTENDED_FRAME_BOUNDS=9 excludes invisible Win10/11 resize/shadow margins.
    [DllImport("dwmapi.dll", PreserveSig=true)]
    public static extern int DwmGetWindowAttribute(IntPtr hwnd, int attribute, out Rect rect, int size);
}
'@
$proc = Get-Process -Id $TargetPid -ErrorAction Stop
$proc.Refresh()
$hwnd = $proc.MainWindowHandle
if ($hwnd -eq [IntPtr]::Zero) { throw 'ZYN-SCREEN-002: no native window handle' }
if (-not [ZynoaScreenWin32]::IsWindowVisible($hwnd)) {
    throw 'ZYN-SCREEN-003: native window not visible'
}
$bounds = [ZynoaScreenWin32+Rect]::new()
if (-not [ZynoaScreenWin32]::GetWindowRect($hwnd, [ref]$bounds)) {
    throw 'ZYN-SCREEN-004: cannot resolve native window bounds'
}
# A CI runner may have a 1024x768 desktop: move and resize the native
# window fully into the *working area* so the taskbar is NEVER photographed.
$workArea = [System.Windows.Forms.Screen]::FromHandle($hwnd).WorkingArea
if ($workArea.Width -lt 912 -or $workArea.Height -lt 632) {
    throw 'ZYN-SCREEN-005: insufficient display area for a real native screenshot'
}
$fits = $bounds.Left -ge $workArea.Left -and $bounds.Top -ge $workArea.Top -and
        $bounds.Right -le $workArea.Right -and $bounds.Bottom -le $workArea.Bottom
if (-not $fits) {
    $fittedWidth = [Math]::Min(1180, $workArea.Width - 12)
    $fittedHeight = [Math]::Min(760, $workArea.Height - 12)
    if (-not [ZynoaScreenWin32]::MoveWindow($hwnd, $workArea.Left + 6, $workArea.Top + 6,
        $fittedWidth, $fittedHeight, $true)) {
        throw 'ZYN-SCREEN-009: unable to fit native window inside display working area'
    }
    Start-Sleep -Milliseconds 900
    if (-not [ZynoaScreenWin32]::GetWindowRect($hwnd, [ref]$bounds)) {
        throw 'ZYN-SCREEN-010: moved window bounds unavailable'
    }
}
$width = $bounds.Right - $bounds.Left
$height = $bounds.Bottom - $bounds.Top
if ($width -lt 900 -or $height -lt 620 -or
    $bounds.Left -lt $workArea.Left -or $bounds.Top -lt $workArea.Top -or
    $bounds.Right -gt $workArea.Right -or $bounds.Bottom -gt $workArea.Bottom) {
    throw 'ZYN-SCREEN-011: window still overlaps desktop/taskbar'
}
if (-not [ZynoaScreenWin32]::SetForegroundWindow($hwnd)) {
    throw 'ZYN-SCREEN-006: native window cannot become foreground'
}
Start-Sleep -Milliseconds 800
# GetWindowRect includes invisible DWM resize margins. Never capture desktop
# pixels through those margins or pretend cropping a browser preview is proof.
$visibleBounds = [ZynoaScreenWin32+Rect]::new()
$sizeOfRect = [System.Runtime.InteropServices.Marshal]::SizeOf($visibleBounds)
$dwmStatus = [ZynoaScreenWin32]::DwmGetWindowAttribute(
    $hwnd, 9, [ref]$visibleBounds, $sizeOfRect)
if ($dwmStatus -ne 0) {
    throw 'ZYN-SCREEN-012: DWM visible frame bounds unavailable'
}
$bounds = $visibleBounds
$width = $bounds.Right - $bounds.Left
$height = $bounds.Bottom - $bounds.Top
if ($width -lt 880 -or $height -lt 600 -or
    $bounds.Left -lt $workArea.Left -or $bounds.Top -lt $workArea.Top -or
    $bounds.Right -gt $workArea.Right -or $bounds.Bottom -gt $workArea.Bottom) {
    throw 'ZYN-SCREEN-013: visible native frame outside display working area'
}
$bitmap = [System.Drawing.Bitmap]::new($width, $height)
try {
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    try {
        $graphics.CopyFromScreen($bounds.Left, $bounds.Top, 0, 0,
            [System.Drawing.Size]::new($width, $height))
    } finally { $graphics.Dispose() }
    $colors = [System.Collections.Generic.HashSet[int]]::new()
    for ($x = 0; $x -lt 16; $x++) {
        for ($y = 0; $y -lt 12; $y++) {
            $px = [Math]::Min($width - 1, [Math]::Floor(($x + 0.5) * $width / 16))
            $py = [Math]::Min($height - 1, [Math]::Floor(($y + 0.5) * $height / 12))
            [void]$colors.Add($bitmap.GetPixel([int]$px, [int]$py).ToArgb())
        }
    }
    if ($colors.Count -lt 6) { throw 'ZYN-SCREEN-007: blank or monochrome capture' }
    New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
    $png = Join-Path $OutputDirectory 'M01-S01.png'
    if (Test-Path -LiteralPath $png) { throw 'ZYN-SCREEN-008: refuse replacing existing image' }
    $bitmap.Save($png, [System.Drawing.Imaging.ImageFormat]::Png)
} finally { $bitmap.Dispose() }
$png = Join-Path $OutputDirectory 'M01-S01.png'
$hash = (Get-FileHash -LiteralPath $png -Algorithm SHA256).Hash.ToLowerInvariant()
$meta = [ordered]@{
    screenshot_id = 'M01-S01'
    source_commit_sha = $SourceSha
    built_commit_sha = $BuiltSha
    source = 'GitHub Windows Actions actual Tauri process'
    screen = 'Overview (empty workspace)'
    capture_status = 'candidate_pending_visual_review'
    capture_verified = $false
    window_width = $width
    window_height = $height
    window_fully_visible = $true
    frame_bounds_source = 'DwmGetWindowAttribute DWMWA_EXTENDED_FRAME_BOUNDS (9)'
    desktop_work_area = "$($workArea.Width)x$($workArea.Height)"
    sha256 = $hash
    alt_text = 'Zynoa native desktop Overview with local startup and disabled workspace creation'
    privacy = 'Disposable CI fixture with no user content or secrets'
}
$meta | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (
    Join-Path $OutputDirectory 'M01-S01.capture.json') -Encoding UTF8
Write-Output 'Candidate native screenshot captured, human verification remains pending'
# Capture additional views from the same *real* Tauri window: no browser/mock fallback.
# Keep supplementary P01 preview IDs distinct from unimplemented final screen IDs.
$script:previousFrameHash = $hash
function Save-NativeFollowup {
    param(
        [Parameter(Mandatory = $true)][string]$ScreenshotId,
        [Parameter(Mandatory = $true)][AllowEmptyString()][string]$Shortcut,
        [Parameter(Mandatory = $true)][string]$ScreenTitle,
        [Parameter(Mandatory = $true)][string]$Description,
        [Parameter(Mandatory = $false)][string]$OptionId = "",
        [Parameter(Mandatory = $false)][string]$FinalCandidateId = ""
    )
    $proc.Refresh()
    if ($proc.HasExited -or -not [ZynoaScreenWin32]::IsWindowVisible($hwnd)) {
        throw 'ZYN-SCREEN-016: native window is no longer running and visible'
    }
    if ($Shortcut -ne "") { [System.Windows.Forms.SendKeys]::SendWait($Shortcut) }
    Start-Sleep -Milliseconds 900
    $viewBitmap = [System.Drawing.Bitmap]::new($width, $height)
    try {
        $viewGraphics = [System.Drawing.Graphics]::FromImage($viewBitmap)
        try {
            $viewGraphics.CopyFromScreen($bounds.Left, $bounds.Top, 0, 0,
                [System.Drawing.Size]::new($width, $height))
        } finally { $viewGraphics.Dispose() }
        # WebView2 can expose a still-visible native HWND before its next view
        # has painted. Retry only transient compositor blanks, never approve one.
        $colors = [System.Collections.Generic.HashSet[int]]::new()
        for ($attempt = 1; $attempt -le 3; $attempt++) {
            if ($attempt -gt 1) {
                Start-Sleep -Milliseconds 800
                $refreshGraphics = [System.Drawing.Graphics]::FromImage($viewBitmap)
                try {
                    $refreshGraphics.CopyFromScreen($bounds.Left, $bounds.Top, 0, 0,
                        [System.Drawing.Size]::new($width, $height))
                } finally { $refreshGraphics.Dispose() }
            }
            $colors.Clear()
            # Clean, mostly uniform layouts legitimately have fewer than six colors
            # on a 12x10 grid. 24x16 still rejects monochrome/blank frames.
            for ($x = 0; $x -lt 24; $x++) {
                for ($y = 0; $y -lt 16; $y++) {
                    $px = [int][Math]::Min($width - 1, [Math]::Floor(($x + 0.5) * $width / 24))
                    $py = [int][Math]::Min($height - 1, [Math]::Floor(($y + 0.5) * $height / 16))
                    [void]$colors.Add($viewBitmap.GetPixel($px, $py).ToArgb())
                }
            }
            if ($colors.Count -ge 6) { break }
            Write-Warning ('ZYN-SCREEN-017: blank candidate ' + $ScreenshotId +
                ' during bounded frame read attempt ' + $attempt + '/3')
        }
        if ($colors.Count -lt 6) {
            # Diagnostic-only frame is neither candidate evidence nor VERIFIED.
            New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
            $debugFrame = Join-Path $OutputDirectory ('DEBUG-' + $ScreenshotId + '.png')
            $viewBitmap.Save($debugFrame, [System.Drawing.Imaging.ImageFormat]::Png)
            throw 'ZYN-SCREEN-017: blank native follow-up frame'
        }
        $out = Join-Path $OutputDirectory ($ScreenshotId + '.png')
        if (Test-Path -LiteralPath $out) { throw 'ZYN-SCREEN-018: refuse replacing native evidence' }
        $viewBitmap.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)
    } finally { $viewBitmap.Dispose() }
    $viewHash = (Get-FileHash -LiteralPath $out -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($viewHash -eq $script:previousFrameHash) {
        throw ('ZYN-SCREEN-019: native view navigation/scroll did not change pixels: ' + $ScreenshotId)
    }
    $script:previousFrameHash = $viewHash
    $viewMeta = [ordered]@{
        screenshot_id = $ScreenshotId
        source_commit_sha = $SourceSha
        built_commit_sha = $BuiltSha
        source = 'GitHub Windows Actions actual Tauri process'
        screen = $ScreenTitle
        capture_status = 'candidate_pending_visual_review'
        capture_verified = $false
        window_width = $width
        window_height = $height
        window_fully_visible = $true
        frame_bounds_source = 'DwmGetWindowAttribute DWMWA_EXTENDED_FRAME_BOUNDS (9)'
        desktop_work_area = "$($workArea.Width)x$($workArea.Height)"
        sha256 = $viewHash
        alt_text = $Description
        privacy = 'Disposable CI fixture with no user content or secrets'
    }
    if ($OptionId -ne "") {
        if ($OptionId -notmatch '^M(02|19)-OPT-0[1-8]$') {
            throw 'ZYN-SCREEN-040: invalid typed option reference capture ID'
        }
        $viewMeta['option_id'] = $OptionId
        $viewMeta['interaction'] = 'palette:exact-id:enter:option-detail'
    }
    if ($FinalCandidateId -ne "") {
        if ($FinalCandidateId -cnotmatch '^M(02|19)-(S0[1-7]|OPT-0[1-8])$' -or
            $ScreenshotId -cne ('P02-T10-CTRL-' + $FinalCandidateId)) {
            throw 'ZYN-SCREEN-041: final-control candidate identity mismatch'
        }
        $viewMeta['candidate_final_asset_id'] = $FinalCandidateId
        $viewMeta['interaction'] = 'actual-native-screen-or-control:keyboard'
        $viewMeta['evidence_limit'] = 'NOT a final manifest screenshot or independent visual approval'
    }
    $viewMeta | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (
        Join-Path $OutputDirectory ($ScreenshotId + '.capture.json')) -Encoding UTF8
    Write-Output ('Native candidate captured: ' + $ScreenshotId)
}

# Separate M26 journey: reuse real DWM capture, never expand the 69-frame T10 budget.
if ($M26Only) {
    Add-Type -AssemblyName UIAutomationClient
    Add-Type -AssemblyName UIAutomationTypes
    if (-not $env:GITHUB_RUN_ID) { throw 'ZYN-M26-001: CI run identity missing' }
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class ZynoaM26Foreground {
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
}
'@
    function Assert-M26Foreground {
        $proc.Refresh()
        if ($proc.HasExited -or [ZynoaM26Foreground]::GetForegroundWindow() -ne $hwnd) {
            throw 'ZYN-M26-002: actual app not foreground'
        }
    }
    function Wait-M26Name {
        param([string]$Name, [switch]$Focusable, [switch]$Disabled, [switch]$Fragment, [switch]$Reveal)
        $deadline = (Get-Date).AddSeconds(10)
        do {
            Assert-M26Foreground
            $root = [System.Windows.Automation.AutomationElement]::FromHandle($hwnd)
            if ($null -eq $root -or $root.Current.ProcessId -ne $TargetPid) {
                throw 'ZYN-M26-003: UIA root PID mismatch'
            }
            $condition = if ($Fragment) {
                [System.Windows.Automation.Condition]::TrueCondition
            } else {
                [System.Windows.Automation.PropertyCondition]::new(
                    [System.Windows.Automation.AutomationElement]::NameProperty, $Name)
            }
            $items = $root.FindAll([System.Windows.Automation.TreeScope]::Descendants, $condition)
            for ($i=0; $i -lt $items.Count; $i++) {
                try {
                    $item = $items.Item($i)
                    if ($Fragment -and -not ([string]$item.Current.Name).Contains($Name)) { continue }
                    if ($Focusable -and (-not $item.Current.IsKeyboardFocusable -or -not $item.Current.IsEnabled)) { continue }
                    if ($Disabled -and $item.Current.IsEnabled) { continue }
                    if ($item.Current.IsOffscreen -and -not $Focusable -and -not $Disabled) {
                        if ($Reveal) {
                            # Real UIA scroll/focus only. An offscreen marker must
                            # become visible before a screenshot can be accepted.
                            $pattern = $null
                            if ($item.TryGetCurrentPattern([System.Windows.Automation.ScrollItemPattern]::Pattern,[ref]$pattern)) {
                                $pattern.ScrollIntoView()
                            } elseif ($item.Current.IsKeyboardFocusable -and $item.Current.IsEnabled) {
                                $item.SetFocus()
                            }
                        }
                        continue
                    }
                    return $item
                } catch [System.Windows.Automation.ElementNotAvailableException] {}
            }
            Start-Sleep -Milliseconds 250
        } until ((Get-Date) -ge $deadline)
        throw ('ZYN-M26-004: required native control absent: ' + $Name)
    }
    function Send-M26Key {
        param([string]$Keys)
        Assert-M26Foreground
        [System.Windows.Forms.SendKeys]::SendWait($Keys)
        Start-Sleep -Milliseconds 250
    }
    function Focus-M26Control {
        param([string]$Name, [switch]$Fragment)
        $element = Wait-M26Name -Name $Name -Focusable -Fragment:$Fragment
        try {
            $scroll = $element.GetCurrentPattern([System.Windows.Automation.ScrollItemPattern]::Pattern)
            if ($null -ne $scroll) { $scroll.ScrollIntoView() }
        } catch [System.InvalidOperationException] {}
        $element.SetFocus()
        $deadline=(Get-Date).AddSeconds(5)
        do {
            Assert-M26Foreground
            try {
                $fresh=Wait-M26Name -Name $Name -Focusable -Fragment:$Fragment
                if ($fresh.Current.HasKeyboardFocus -and -not $fresh.Current.IsOffscreen) { return $fresh }
            } catch [System.Windows.Automation.ElementNotAvailableException] {}
            Start-Sleep -Milliseconds 150
        } until ((Get-Date) -ge $deadline)
        throw ('ZYN-M26-018: native keyboard focus not confirmed: '+$Name)
    }
    $observations = [System.Collections.Generic.List[object]]::new()
    function Capture-M26 {
        param([string]$Id, [string]$Heading, [string]$Description)
        [void](Wait-M26Name -Name $Heading -Reveal)
        Assert-M26Foreground
        Save-NativeFollowup -ScreenshotId $Id -Shortcut '' -ScreenTitle $Heading -Description $Description
        Assert-M26Foreground
        [void](Wait-M26Name -Name $Heading)
        $observations.Add([ordered]@{screenshot_id=$Id; actual_visible_uia_name=$Heading; foreground_window_verified=$true})
    }
    $tabTransitions = [System.Collections.Generic.List[object]]::new()
    function Read-M26Tab {
        param([string]$Name)
        Assert-M26Foreground
        $root = [System.Windows.Automation.AutomationElement]::FromHandle($hwnd)
        if ($null -eq $root -or $root.Current.ProcessId -ne $TargetPid) {
            throw 'ZYN-M26-003: UIA root PID mismatch'
        }
        $nameCondition = [System.Windows.Automation.PropertyCondition]::new(
            [System.Windows.Automation.AutomationElement]::NameProperty, $Name)
        $typeCondition = [System.Windows.Automation.PropertyCondition]::new(
            [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
            [System.Windows.Automation.ControlType]::TabItem)
        $condition = [System.Windows.Automation.AndCondition]::new($nameCondition,$typeCondition)
        $tab = $root.FindFirst([System.Windows.Automation.TreeScope]::Descendants,$condition)
        if ($null -eq $tab) { return $null }
        $pattern = $null
        if (-not $tab.TryGetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern,[ref]$pattern)) {
            throw ('ZYN-M26-011: native tab selection provider unavailable: ' + $Name)
        }
        return [pscustomobject]@{
            Element=$tab
            Selected=[bool]$pattern.Current.IsSelected
            Focused=[bool]$tab.Current.HasKeyboardFocus
            Enabled=[bool]$tab.Current.IsEnabled
            Visible=(-not $tab.Current.IsOffscreen)
        }
    }
    function Wait-M26SelectedFocus {
        param([string]$Name)
        $deadline=(Get-Date).AddSeconds(8)
        do {
            try {
                $state=Read-M26Tab -Name $Name
                if ($null -ne $state -and $state.Selected -and $state.Focused -and $state.Enabled -and $state.Visible) {
                    return $state
                }
            } catch [System.Windows.Automation.ElementNotAvailableException] {}
            Start-Sleep -Milliseconds 200
        } until ((Get-Date) -ge $deadline)
        # Report only fixed fixture tab states, never arbitrary accessible names.
        $state=Read-M26Tab -Name $Name
        if ($null -ne $state) {
            Write-Host ("ZYN-M26-TAB name="+$Name+" selected="+$state.Selected+" focus="+$state.Focused+" visible="+$state.Visible)
        }
        throw ('ZYN-M26-005: native selected tab and keyboard focus did not reach ' + $Name)
    }
    function Open-M26Tab {
        param([string]$From, [string]$Keys, [string]$To)
        $source=Read-M26Tab -Name $From
        if ($null -eq $source -or -not $source.Selected -or -not $source.Enabled) {
            throw ('ZYN-M26-012: unexpected source tab selection: '+$From)
        }
        $source.Element.SetFocus()
        [void](Wait-M26SelectedFocus -Name $From)
        # A single actual key; never retry by clicking or selecting destination.
        Send-M26Key -Keys $Keys
        [void](Wait-M26SelectedFocus -Name $To)
        $old=Read-M26Tab -Name $From
        if ($null -eq $old -or $old.Selected) { throw 'ZYN-M26-013: source tab still selected' }
        $tabTransitions.Add([ordered]@{from=$From;key=$Keys;to=$To;source_focus_and_selection=$true;destination_focus_and_selection=$true;previous_tab_deselected=$true})
        Write-Host ("ZYN-M26-TAB-PASS "+$From+" "+$Keys+" "+$To)
    }
    [void](Focus-M26Control -Name 'Changelog')
    Send-M26Key -Keys '{ENTER}'
    Capture-M26 -Id 'M26-CAND-S01' -Heading 'No verified releases' -Description 'Actual native Changelog release unavailable state, without invented signed data'
    [void](Wait-M26Name -Name 'Check release feed' -Disabled)
    Open-M26Tab -From "What's New" -Keys '{RIGHT}' -To 'Known Issues'
    Capture-M26 -Id 'M26-CAND-S02' -Heading 'Select a capability notice' -Description 'Actual native Known Issues view showing bundled capability notices, not live GitHub issues'
    $search = Focus-M26Control -Name 'Search bundled notices'
    Send-M26Key -Keys 'zzznomatch'
    $value = $search.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
    if ($null -eq $value -or $value.Current.Value -cne 'zzznomatch') {
        throw 'ZYN-M26-006: typed text did not reach real notice search'
    }
    Capture-M26 -Id 'M26-CAND-SEARCH-EMPTY' -Heading 'No matching notices. Reset filters to view all.' -Description 'Actual native typed search query, no-match feedback and reset control'
    [void](Focus-M26Control -Name 'Reset filters')
    Send-M26Key -Keys '{ENTER}'
    $resetDeadline=(Get-Date).AddSeconds(8)
    $queryReset=$false
    do {
        $freshSearch=Wait-M26Name -Name 'Search bundled notices' -Focusable
        try {
            $queryReset=($freshSearch.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value -ceq '')
        } catch [System.Windows.Automation.ElementNotAvailableException] {}
        if ($queryReset) { break }
        Start-Sleep -Milliseconds 200
    } until ((Get-Date) -ge $resetDeadline)
    if (-not $queryReset) { throw 'ZYN-M26-019: actual search reset did not clear input' }
    $notice=Focus-M26Control -Name 'Backup and restore not available' -Fragment
    if ($notice.Current.ControlType -ne [System.Windows.Automation.ControlType]::Button) {
        throw 'ZYN-M26-020: notice target is not a native button'
    }
    Send-M26Key -Keys '{ENTER}'
    [void](Wait-M26Name -Name 'Not a released fix or live issue status.' -Reveal)
    $detailProof=[ordered]@{query_before='zzznomatch';query_after_reset=$freshSearch.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value;notice_title='Backup and restore not available';activation='focused_native_button_enter';detail_marker='Not a released fix or live issue status.'}
    Capture-M26 -Id 'M26-CAND-S04' -Heading 'Not a released fix or live issue status.' -Description 'Actual selected bundled capability notice, no verified linked issue or merge receipt'
    [void](Wait-M26Name -Name 'Open linked issue' -Disabled)
    Open-M26Tab -From 'Known Issues' -Keys '{RIGHT}' -To 'Version History'
    Capture-M26 -Id 'M26-CAND-S03' -Heading 'No verified versions' -Description 'Actual native empty verified version history, comparison intentionally disabled'
    [void](Wait-M26Name -Name 'Compare versions' -Disabled)
    Open-M26Tab -From 'Version History' -Keys '{RIGHT}' -To 'Module Changes'
    function Read-M26ModuleFilter {
        Assert-M26Foreground
        $combo = Wait-M26Name -Name 'Module' -Focusable
        $selectedValue = ''
        $valuePattern = $null
        if ($combo.TryGetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern,[ref]$valuePattern)) {
            $selectedValue = [string]$valuePattern.Current.Value
        }
        if ($selectedValue -notin @('All modules','M23','M24','M25','M26')) {
            $selection = $null
            if ($combo.TryGetCurrentPattern([System.Windows.Automation.SelectionPattern]::Pattern,[ref]$selection)) {
                $selectedItems = @($selection.Current.GetSelection())
                if ($selectedItems.Count -eq 1) { $selectedValue = [string]$selectedItems[0].Current.Name }
            }
        }
        $group = Wait-M26Name -Name 'Bundled capability notices'
        $buttons = $group.FindAll([System.Windows.Automation.TreeScope]::Descendants,
            [System.Windows.Automation.PropertyCondition]::new(
                [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
                [System.Windows.Automation.ControlType]::Button))
        $known = @('Backup and restore not available','Data relocation not available','Signed updates not available','Live change and release data not available')
        $titles = [System.Collections.Generic.List[string]]::new()
        for ($j=0; $j -lt $buttons.Count; $j++) {
            $name = [string]$buttons.Item($j).Current.Name
            $matched = @($known | Where-Object { $name.Contains($_) })
            if ($matched.Count -ne 1) { throw 'ZYN-M26-014: unexpected bundled notice button' }
            $titles.Add($matched[0])
        }
        return [pscustomobject]@{SelectedValue=$selectedValue;Titles=@($titles.ToArray())}
    }
    function Wait-M26ModuleFilter {
        param([string]$ExpectedValue,[string[]]$ExpectedTitles,[int]$Seconds=8)
        $deadline=(Get-Date).AddSeconds($Seconds)
        do {
            try {
                $state=Read-M26ModuleFilter
                if ($state.SelectedValue -ceq $ExpectedValue -and
                    $state.Titles.Count -eq $ExpectedTitles.Count -and
                    (($state.Titles -join '|') -ceq ($ExpectedTitles -join '|'))) { return $state }
            } catch [System.Windows.Automation.ElementNotAvailableException] {}
            Start-Sleep -Milliseconds 250
        } until ((Get-Date) -ge $deadline)
        return $null
    }
    $allTitles=@('Backup and restore not available','Data relocation not available','Signed updates not available','Live change and release data not available')
    $initialFilter=Wait-M26ModuleFilter -ExpectedValue 'All modules' -ExpectedTitles $allTitles
    if ($null -eq $initialFilter) { throw 'ZYN-M26-015: default module filter value or actual notice inventory mismatch' }
    [void](Focus-M26Control -Name 'Module')
    # Send discrete keys to the actual native select. The collapsed select
    # should commit on arrow; if not, explicitly open and commit by keyboard.
    Send-M26Key -Keys '{HOME}'
    Send-M26Key -Keys '{DOWN}'
    $filterMethod='collapsed_keyboard'
    $filtered=Wait-M26ModuleFilter -ExpectedValue 'M23' -ExpectedTitles @($allTitles[0]) -Seconds 3
    if ($null -eq $filtered) {
        [void](Focus-M26Control -Name 'Module')
        Send-M26Key -Keys '%{DOWN}{HOME}{DOWN}{ENTER}'
        $filterMethod='expanded_keyboard'
        $filtered=Wait-M26ModuleFilter -ExpectedValue 'M23' -ExpectedTitles @($allTitles[0])
    }
    if ($null -eq $filtered) {
        $actual=Read-M26ModuleFilter
        $safeValue=if ($actual.SelectedValue -in @('All modules','M23','M24','M25','M26')) {$actual.SelectedValue} else {'provider_unavailable'}
        Write-Host ("ZYN-M26-FILTER selected="+$safeValue+" notice_count="+$actual.Titles.Count)
        throw 'ZYN-M26-016: real module selection and filtered notice inventory not verified'
    }
    $filterProof=[ordered]@{initial_value=$initialFilter.SelectedValue;initial_titles=@($initialFilter.Titles);selected_value=$filtered.SelectedValue;filtered_titles=@($filtered.Titles);keyboard_method=$filterMethod}
    Write-Host ("ZYN-M26-FILTER-PASS "+$filterMethod+" M23 one actual notice")
    Capture-M26 -Id 'M26-CAND-S05' -Heading 'Select a capability notice' -Description 'Actual native module-filtered capability notices after keyboard selection, not released history'
    [void](Focus-M26Control -Name 'Reset filters')
    Send-M26Key -Keys '{ENTER}'
    $resetFilter=Wait-M26ModuleFilter -ExpectedValue 'All modules' -ExpectedTitles $allTitles
    if ($null -eq $resetFilter) { throw 'ZYN-M26-017: module reset did not restore real inventory' }
    $filterProof['reset_value']=$resetFilter.SelectedValue
    $filterProof['reset_titles']=@($resetFilter.Titles)
    Open-M26Tab -From 'Module Changes' -Keys '{RIGHT}' -To 'Audit Timeline'
    Capture-M26 -Id 'M26-CAND-S06' -Heading 'Audit access is not enabled' -Description 'Actual native audit timeline boundary with no authorized private event query or export'
    [void](Wait-M26Name -Name 'Export change history' -Disabled)
    Open-M26Tab -From 'Audit Timeline' -Keys '{RIGHT}' -To 'Notifications'
    Capture-M26 -Id 'M26-CAND-S07' -Heading 'Notification settings unavailable' -Description 'Actual native notification preference boundary with disabled notification and unread settings'
    [void](Wait-M26Name -Name "Enable What's New notifications" -Disabled)
    Open-M26Tab -From 'Notifications' -Keys '{END}' -To 'Migration Notes'
    Capture-M26 -Id 'M26-CAND-S08' -Heading 'No verified migration notes' -Description 'Actual native migration warning boundary with unavailable release-specific recovery guidance'
    [void](Wait-M26Name -Name 'View rollback guidance' -Disabled)
    Open-M26Tab -From 'Migration Notes' -Keys '{HOME}' -To "What's New"
    Send-M26Key -Keys '{F1}'
    Capture-M26 -Id 'M26-CAND-HELP' -Heading 'Changelog and release history' -Description 'Actual F1 native contextual navigation to bundled Changelog and release history Help article'
    $receipt = [ordered]@{
        schema_version=1; source_commit_sha=$SourceSha; built_commit_sha=$BuiltSha
        github_run_id=[string]$env:GITHUB_RUN_ID; native_process_id=$TargetPid
        status='M26_NATIVE_CANDIDATES_ONLY'; no_user_data=$true
        independent_visual_review=$false; screen_reader_verified=$false
        observations=@($observations.ToArray())
        tab_transitions=@($tabTransitions.ToArray())
        module_filter=$filterProof
        notice_detail=$detailProof
    }
    $receipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (
        Join-Path $OutputDirectory 'M26-journey.capture.json') -Encoding UTF8
    return
}

Save-NativeFollowup -ScreenshotId 'M01-S01-continued' -Shortcut '{PGDN}' -ScreenTitle 'Overview (continued below fold)' -Description 'Zynoa native Overview foundation progress, lower scroll position and footer'
Save-NativeFollowup -ScreenshotId 'P01-Settings-preview' -Shortcut '^{2}' -ScreenTitle 'Settings (disabled P01 controls)' -Description 'Zynoa native Settings foundation screen with intentionally unavailable preferences'
Save-NativeFollowup -ScreenshotId 'P01-Recovery-preview' -Shortcut '^{3}' -ScreenTitle 'Recovery (no verified backups)' -Description 'Zynoa native Recovery foundation screen with disabled restore action'
Save-NativeFollowup -ScreenshotId 'P01-Diagnostics-preview' -Shortcut '^{4}' -ScreenTitle 'Diagnostics (capability summary)' -Description 'Zynoa native Diagnostics read-only summary with remote reporting disabled'


# P02 native screenshot candidates: source/build SHA remains bound to the
# same verified real Tauri executable. No browser mock, synthetic screenshot,
# or "capture_verified=true" claim. These artifacts require visual review.
if ($env:ZYNOA_CAPTURE_P02 -eq '1') {
    $m02Output = Join-Path (Split-Path -Parent $OutputDirectory) 'M02'
    $m19Output = Join-Path (Split-Path -Parent $OutputDirectory) 'M19'
    New-Item -ItemType Directory -Force -Path $m02Output, $m19Output | Out-Null
    $OutputDirectory = $m02Output
    Save-NativeFollowup -ScreenshotId 'M02-S03' -Shortcut '^{5}' -ScreenTitle 'P02 native workbench panels' -Description 'Native Windows Zynoa workbench, runtime state and keyboard-accessible tabs'
    # Actual keyboard navigation from the focused Workbench main region:
    # Tab 1-2 toolbar, Tab 3 help, Tab 4 active tab, Tab 5 active tabpanel.
    # Screenshot is candidate evidence only, independently review visible focus ring.
    Save-NativeFollowup -ScreenshotId 'M02-OPT-07' -Shortcut '{TAB}{TAB}{TAB}{TAB}{TAB}' -ScreenTitle 'Workbench keyboard focus' -Description 'Real Tauri Workbench keyboard-focused active tabpanel with visible focus ring (review pending)'
    # T02.12: from the keyboard-focused Workbench tabpanel, Shift+Tab to the selected tab,
    # End switches to Keyboard guide, Tab focuses its panel. Candidate only.
    Save-NativeFollowup -ScreenshotId 'M02-S07' -Shortcut '+{TAB}{END}{TAB}' -ScreenTitle 'P02 native keyboard guide' -Description 'Native Tauri Workbench keyboard guide accessed with End key in ARIA tablist, panel focus visible'
    # From keyboard-guide focused panel, Shift+Tab to tab, Left to Layout controls,
    # Tab into panel, Tab to range, Tab to Compact toggle, Enter enables compact rows.
    # This is native source-SHA-bound candidate, not final screenshot acceptance.
    Save-NativeFollowup -ScreenshotId 'M02-OPT-03' -Shortcut '+{TAB}{LEFT}{TAB}{TAB}{TAB}{ENTER}{PGDN}' -ScreenTitle 'P02 compact properties panel preview' -Description 'Real Tauri Workbench layout tab showing compact sample property rows, keyboard-enabled pressed toggle and session-only feedback'
    # The Layout tab and its real controls are already active here. Capture
    # the slider via a keyboard-only reverse Tab from the compact toggle;
    # two ArrowRight keys change the actual 40% pane width to 50%.
    # This avoids a fragile late-page View/ARIA tab re-entry and verifies
    # the slider while the same live native Workbench is still present.
    Save-NativeFollowup -ScreenshotId 'P02-T10-CTRL-M02-OPT-06' -Shortcut '+{TAB}{RIGHT}{RIGHT}{PGUP}' -ScreenTitle 'M02 actual split pane slider' -Description 'Real native Workbench Layout slider changed with Shift+Tab and keyboard arrows from compact property toggle; live pane ratio updates visibly without assuming a fixed numeric percentage' -FinalCandidateId 'M02-OPT-06'
    # The slider is an <input type=range>. App deliberately ignores Ctrl+1..6
    # while input owns focus. F1 is a supported global shortcut even from input,
    # and Help remounts with main-content focus, so Ctrl+6 can then navigate.
    [System.Windows.Forms.SendKeys]::SendWait('{F1}')
    Start-Sleep -Milliseconds 350
    Save-NativeFollowup -ScreenshotId 'M02-S05' -Shortcut '^{6}' -ScreenTitle 'P02 native component gallery' -Description 'Real Tauri component gallery with semantic token swatches, state chips and interactive input'
    # From focused main after Ctrl+6: Tab toolbar command, Tab help, Tab primary action.
    # Activate primary selection; PageDown reveals the actual button/feedback states.
    Save-NativeFollowup -ScreenshotId 'P02-T02-06' -Shortcut '{TAB}{TAB}{TAB}{ENTER}{PGDN}' -ScreenTitle 'P02 component interaction states' -Description 'Real Tauri Components page with selected action, disabled example and independent status feedback; candidate awaiting native visual review'
    Save-NativeFollowup -ScreenshotId 'M02-S06' -Shortcut '^{2}' -ScreenTitle 'P02 native appearance settings' -Description 'Session-only theme and density selectors with unavailable native relocation labelled'
    Save-NativeFollowup -ScreenshotId 'M02-S04' -Shortcut '^+p' -ScreenTitle 'P02 native command palette' -Description 'Native modal command palette with focusable search and allowlisted navigation commands'
    # T04: native keyboard-only no-matches and Escape recovery from the palette.
    # These remain candidate captures; focus restoration also has source regressions.
    Save-NativeFollowup -ScreenshotId 'P02-T04-NO-MATCH' -Shortcut 'zzzznotacommand' -ScreenTitle 'P02 command palette empty search state' -Description 'Real Windows Tauri command palette with unmatched local search query and no matching commands message'
    Save-NativeFollowup -ScreenshotId 'P02-T04-ESCAPE' -Shortcut '{ESC}' -ScreenTitle 'P02 command palette dismissed by Escape' -Description 'Real Tauri Preferences after keyboard Escape dismisses command palette and returns focus to connected opener'
    $OutputDirectory = $m19Output
    Save-NativeFollowup -ScreenshotId 'M19-S01' -Shortcut '{ESC}{F1}' -ScreenTitle 'P02 native offline Help Center' -Description 'Bundled offline Help Center article library and searchable local help interface'
    # Real keyboard-operated Help navigation from focused main:
    # two toolbar buttons; Articles then Tour, Troubleshooting, FAQ, Wiki.
    # Captures are SHA-bound machine candidates, never visual approval.
    Save-NativeFollowup -ScreenshotId 'M19-S04' -Shortcut '{TAB}{TAB}{TAB}{TAB}{TAB}{ENTER}{PGDN}' -ScreenTitle 'M19 offline guided tour' -Description 'Real Tauri Help guided tour with lesson progress, offline article link and working Previous, Next and Restart buttons'
    Save-NativeFollowup -ScreenshotId 'M19-S05' -Shortcut '{TAB}{ENTER}' -ScreenTitle 'M19 troubleshooting wizard' -Description 'Real Tauri Help recovery wizard with actionable next and solved steps and local article guidance'
    Save-NativeFollowup -ScreenshotId 'M19-S06' -Shortcut '{TAB}{TAB}{ENTER}' -ScreenTitle 'M19 Wiki source map' -Description 'Real native Help Wiki source mappings, strict local link validation and unpublished remote Wiki disclaimer'
    # Six modes: Wiki -> Articles takes five reverse Tabs; Articles -> Search
    # needs six forward Tabs. Exact keyboard order must match new options tab.
    Save-NativeFollowup -ScreenshotId 'M19-S02' -Shortcut '+{TAB}+{TAB}+{TAB}+{TAB}+{TAB}{ENTER}{TAB}{TAB}{TAB}{TAB}{TAB}{TAB}theme' -ScreenTitle 'M19 offline search results' -Description 'Real native bundled Help search with active theme keyword, local article results and category selector'
    Save-NativeFollowup -ScreenshotId 'M19-S03' -Shortcut '{TAB}{TAB}{ENTER}{PGDN}' -ScreenTitle 'M19 offline article reader' -Description 'Real Tauri Help article opened from an actual offline search result with section headings and related guides'
    # Re-enter Help from Preferences for a known focused main, then select the
    # new offline Option reference. Separate gestures avoid nested SendKeys.
    [System.Windows.Forms.SendKeys]::SendWait('^{2}')
    Start-Sleep -Milliseconds 300
    [System.Windows.Forms.SendKeys]::SendWait('{F1}')
    Start-Sleep -Milliseconds 300
    Save-NativeFollowup -ScreenshotId 'M19-OPTION-REFERENCE-CI' -Shortcut '{TAB}{TAB}{TAB}{TAB}{ENTER}{PGDN}' -ScreenTitle 'M19 complete local option reference' -Description 'Real Windows Tauri Help option directory listing M02/M19 option IDs and their defaults, privacy boundaries and recovery instructions'
    # Focus stays on Option reference workflow; three Tabs select FAQ.
    Save-NativeFollowup -ScreenshotId 'M19-FAQ-GLOSSARY-CI' -Shortcut '{TAB}{TAB}{TAB}{ENTER}{PGDN}' -ScreenTitle 'M19 local FAQ and glossary' -Description 'Real Tauri Help FAQ question disclosures, linked local guides and six glossary definitions'
    # T05/T06: additional real interactive Gallery and live Preferences
    # screenshots from this same verified running Tauri window. Session-only.
    $OutputDirectory = $m02Output
    Save-NativeFollowup -ScreenshotId 'P02-T06-GALLERY-READY' -Shortcut '^{6}{PGDN}{PGDN}' -ScreenTitle 'P02 gallery example states ready' -Description 'Actual native Components gallery with keyboard-operable ready loading empty error offline state explorer and clearly illustrative content'
    # Route away/back to restore main keyboard focus before the ten Tab stops:
    # toolbar command/help, action buttons, text field, five state controls.
    # SendKeys does not accept nested combined Ctrl sequences as one string.
    # Separate each native gesture; precisely ten Tab stops select the Offline
    # example after two toolbar actions, two gallery actions and the input.
    [System.Windows.Forms.SendKeys]::SendWait('^{2}')
    Start-Sleep -Milliseconds 300
    [System.Windows.Forms.SendKeys]::SendWait('^{6}')
    Start-Sleep -Milliseconds 300
    for ($stepIndex = 0; $stepIndex -lt 10; $stepIndex++) {
        [System.Windows.Forms.SendKeys]::SendWait('{TAB}')
    }
    Save-NativeFollowup -ScreenshotId 'P02-T06-GALLERY-OFFLINE' -Shortcut '{ENTER}{PGDN}{PGDN}' -ScreenTitle 'P02 gallery selected offline example' -Description 'Actual native Components state explorer after selecting the illustrative Offline button with keyboard and seeing recovery guidance'
    # Use the same focused five-button gallery; reverse Tab changes Offline to
    # Loading, then forward Tabs select Empty and Error. No simulated pixels.
    Save-NativeFollowup -ScreenshotId 'P02-T06-GALLERY-LOADING' -Shortcut '+{TAB}+{TAB}+{TAB}{ENTER}{PGDN}' -ScreenTitle 'P02 selected illustrative loading example' -Description 'Native Tauri Gallery state explorer with selected Loading example and no active worker'
    Save-NativeFollowup -ScreenshotId 'P02-T06-GALLERY-EMPTY' -Shortcut '{TAB}{ENTER}{PGDN}' -ScreenTitle 'P02 selected illustrative empty example' -Description 'Native Tauri Gallery state explorer with selected Empty example and restore-to-ready guidance'
    Save-NativeFollowup -ScreenshotId 'P02-T06-GALLERY-ERROR' -Shortcut '{TAB}{ENTER}{PGDN}' -ScreenTitle 'P02 selected illustrative error example' -Description 'Native Tauri Gallery state explorer with selected Error example and safe recovery text'
    Save-NativeFollowup -ScreenshotId 'P02-T05-PREFERENCES-LIVE' -Shortcut '^{2}{PGDN}' -ScreenTitle 'P02 session appearance preference feedback' -Description 'Real Tauri Preferences window with effective theme source current density reduced motion indicator and session reset control'
    # T04: open palette from Help, type allowlisted view and execute with Enter.
    # Focus moves to destination main on palette navigation; never run arbitrary code.
    $OutputDirectory = $m02Output
    [System.Windows.Forms.SendKeys]::SendWait('^+p')
    Start-Sleep -Milliseconds 500
    Save-NativeFollowup -ScreenshotId 'P02-T04-ENTER-NAV' -Shortcut 'workbench{ENTER}' -ScreenTitle 'P02 palette keyboard navigation to Workbench' -Description 'Real Windows Tauri Workbench navigated by opening Ctrl+Shift+P palette, entering workbench and pressing Enter'
    # P02 unified local search: real keyboard query -> exact option -> article.
    # Native images are machine candidates, never final visual certification.
    $OutputDirectory = $m19Output
    [System.Windows.Forms.SendKeys]::SendWait('^+p')
    Start-Sleep -Milliseconds 500
    Save-NativeFollowup -ScreenshotId 'M19-UNIFIED-OPTION-RESULTS' -Shortcut 'M19-OPT-06' -ScreenTitle 'P02 unified palette exact option lookup' -Description 'Running Windows Tauri command palette with actual local result for exact M19-OPT-06 Wiki option'
    Save-NativeFollowup -ScreenshotId 'M19-UNIFIED-OPTION-DEST' -Shortcut '{ENTER}{PGDN}' -ScreenTitle 'P02 unified palette opens exact option' -Description 'Running Windows Tauri Help option reference opened by selecting the exact M19-OPT-06 palette result'
    [System.Windows.Forms.SendKeys]::SendWait('^+p')
    Start-Sleep -Milliseconds 500
    Save-NativeFollowup -ScreenshotId 'M19-UNIFIED-ARTICLE-RESULTS' -Shortcut 'Data and diagnostics boundaries' -ScreenTitle 'P02 unified palette offline article search' -Description 'Running Windows Tauri command palette with locally indexed Data and diagnostics boundaries article result'
    Save-NativeFollowup -ScreenshotId 'M19-UNIFIED-ARTICLE-DEST' -Shortcut '{ENTER}{PGDN}' -ScreenTitle 'P02 unified palette opens offline article' -Description 'Running Windows Tauri Help reader opened from the exact offline Data and diagnostics boundaries article search'

    # P02-T10: complete 16-option native Help reference coverage. Real option
    # detail pages, not a claim about unverified final control screenshots.
    foreach ($moduleId in @('M02', 'M19')) {
        for ($optionNumber = 1; $optionNumber -le 8; $optionNumber++) {
            $numberText = '{0:D2}' -f $optionNumber
            $optionId = "$moduleId-OPT-$numberText"
            $referenceId = "$moduleId-T10-REF-OPT-$numberText"
            $OutputDirectory = if ($moduleId -eq 'M02') { $m02Output } else { $m19Output }
            [System.Windows.Forms.SendKeys]::SendWait('^{2}')
            Start-Sleep -Milliseconds 250
            [System.Windows.Forms.SendKeys]::SendWait('^+p')
            Start-Sleep -Milliseconds 300
            Save-NativeFollowup -ScreenshotId $referenceId -Shortcut ($optionId + '{ENTER}{PGDN}') -ScreenTitle ("P02 native Help option reference " + $optionId) -Description ("Real Windows Tauri local Help option detail opened from exact " + $optionId + " palette lookup with usage, limits and recovery") -OptionId $optionId
        }
    }
    $OutputDirectory = $m19Output

    # P02-T10: 15 missing *actual* Windows UI/control candidate journeys.
    # The other 14 final asset IDs already have direct live native view candidates.
    # M02/M19 option Help references are NOT substituted for user-facing controls.
    # Each frame has its own immutable target identity and a pending-review receipt.
    # This is not a manifest promotion or a screen-reader signoff.
    Add-Type -AssemblyName UIAutomationClient
    Add-Type -AssemblyName UIAutomationTypes
    function Focus-P02NativeControl {
        param([Parameter(Mandatory=$true)][string]$AccessibleName)
        $uiaRoot = [System.Windows.Automation.AutomationElement]::FromHandle($hwnd)
        if ($null -eq $uiaRoot -or $uiaRoot.Current.ProcessId -ne $TargetPid) {
            throw 'ZYN-SCREEN-042: native UI Automation handle/PID mismatch'
        }
        $condition = [System.Windows.Automation.PropertyCondition]::new(
            [System.Windows.Automation.AutomationElement]::NameProperty, $AccessibleName)
        for ($attempt=0; $attempt -lt 18; $attempt++) {
            $items = $uiaRoot.FindAll([System.Windows.Automation.TreeScope]::Descendants, $condition)
            for ($itemIndex=0; $itemIndex -lt $items.Count; $itemIndex++) {
                try {
                    $item = $items.Item($itemIndex)
                    if (-not $item.Current.IsEnabled -or -not $item.Current.IsKeyboardFocusable) { continue }
                    $item.SetFocus()
                    Start-Sleep -Milliseconds 150
                    return
                } catch [System.Windows.Automation.ElementNotAvailableException] {
                    # Transient React WebView2 rerender; bounded retry.
                } catch [System.InvalidOperationException] {
                    # Offscreen control may become focusable after native scroll.
                }
            }
            Start-Sleep -Milliseconds 250
        }
        throw ('ZYN-SCREEN-043: actual named native keyboard target absent: ' + $AccessibleName)
    }
    $OutputDirectory = $m02Output
    Save-NativeFollowup -ScreenshotId 'P02-T10-CTRL-M02-S01' -Shortcut '^{1}' -ScreenTitle 'M02 actual global shell' -Description 'Real Tauri Overview workspace shell with native sidebar, read-only startup state and disabled unimplemented workspace creation' -FinalCandidateId 'M02-S01'
    Save-NativeFollowup -ScreenshotId 'P02-T10-CTRL-M02-S02' -Shortcut '%n' -ScreenTitle 'M02 actual navigation rail' -Description 'Real Tauri native navigation rail after keyboard Alt+N collapses the sidebar without leaving Overview' -FinalCandidateId 'M02-S02'
    [System.Windows.Forms.SendKeys]::SendWait('%n')
    [System.Windows.Forms.SendKeys]::SendWait('^{2}')
    Start-Sleep -Milliseconds 300
    Focus-P02NativeControl -AccessibleName 'Navigation density'
    Save-NativeFollowup -ScreenshotId 'P02-T10-CTRL-M02-OPT-01' -Shortcut '{HOME}{DOWN}{TAB}{PGDN}' -ScreenTitle 'M02 actual density preference control' -Description 'Real native Preferences density selector changed to Compact with immediately applied session-only UI density feedback' -FinalCandidateId 'M02-OPT-01'
    [System.Windows.Forms.SendKeys]::SendWait('^{2}')
    Focus-P02NativeControl -AccessibleName 'Interface appearance'
    Save-NativeFollowup -ScreenshotId 'P02-T10-CTRL-M02-OPT-02' -Shortcut '{HOME}{DOWN}{DOWN}{TAB}' -ScreenTitle 'M02 actual theme preference control' -Description 'Real native Preferences appearance selector changed to Light with reflected UI theme and truthful session-only boundary' -FinalCandidateId 'M02-OPT-02'
    [System.Windows.Forms.SendKeys]::SendWait('^+p')
    Start-Sleep -Milliseconds 300
    Focus-P02NativeControl -AccessibleName 'Search available commands and offline Help'
    Save-NativeFollowup -ScreenshotId 'P02-T10-CTRL-M02-OPT-05' -Shortcut 'preferences' -ScreenTitle 'M02 actual command search control' -Description 'Real Windows native command palette text input with typed Preferences query and matching allowlisted app command' -FinalCandidateId 'M02-OPT-05'
    [System.Windows.Forms.SendKeys]::SendWait('{ESC}')
# A static summary would be identical to the theme selector capture.
    # Focus the distinct read-only motion status in the actual native app.
    # Tab then Shift+Tab confirms it participates in keyboard navigation.
    Start-Sleep -Milliseconds 250
    Focus-P02NativeControl -AccessibleName 'Reduced motion (M02-OPT-08)'
    Save-NativeFollowup -ScreenshotId 'P02-T10-CTRL-M02-OPT-08' -Shortcut '{TAB}+{TAB}' -ScreenTitle 'M02 actual reduced-motion read-only status' -Description 'Real native Preferences read-only Windows motion status with its own keyboard focus ring; no manual OS toggle or persisted preference' -FinalCandidateId 'M02-OPT-08'

    $OutputDirectory = $m19Output
    [System.Windows.Forms.SendKeys]::SendWait('^{2}')
    [System.Windows.Forms.SendKeys]::SendWait('{F1}')
    Start-Sleep -Milliseconds 350
    Focus-P02NativeControl -AccessibleName 'Search offline help'
    Save-NativeFollowup -ScreenshotId 'P02-T10-CTRL-M19-OPT-01' -Shortcut 'theme' -ScreenTitle 'M19 actual offline article search' -Description 'Real Windows Help search control with typed theme query, bundled local matching articles and category filtering' -FinalCandidateId 'M19-OPT-01'
    # Leave the Help <input> via category selector then first article result
    # before invoking Ctrl+2; application shortcuts intentionally do not
    # hijack native text/select inputs.
    Save-NativeFollowup -ScreenshotId 'P02-T10-CTRL-M19-OPT-02' -Shortcut '{TAB}{TAB}^{2}{F1}{PGDN}' -ScreenTitle 'M19 actual contextual F1 Help' -Description 'Real native Preferences opened into relevant bundled contextual Help using F1 without internet or external content' -FinalCandidateId 'M19-OPT-02'
    [System.Windows.Forms.SendKeys]::SendWait('^{2}')
    [System.Windows.Forms.SendKeys]::SendWait('{F1}')
    Focus-P02NativeControl -AccessibleName 'Troubleshooting wizard'
    Save-NativeFollowup -ScreenshotId 'P02-T10-CTRL-M19-OPT-03' -Shortcut '{ENTER}{PGDN}' -ScreenTitle 'M19 actual troubleshooting recovery steps' -Description 'Real native bundled troubleshooting wizard with selected issue first step and safe offline recovery actions' -FinalCandidateId 'M19-OPT-03'
    [System.Windows.Forms.SendKeys]::SendWait('^{2}')
    [System.Windows.Forms.SendKeys]::SendWait('{F1}')
    # OPT-04 must show actual glossary, not an unchanged Articles & search
    # page. A real named mode-button Invoke is idempotent across repaint.
    $glossaryRoot=[System.Windows.Automation.AutomationElement]::FromHandle($hwnd)
    if ($null -eq $glossaryRoot -or $glossaryRoot.Current.ProcessId -ne $TargetPid) { throw 'ZYN-SCREEN-042: glossary native UIA handle/PID mismatch' }
    $glossaryCondition=[System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::NameProperty,'FAQ & glossary')
    $glossaryActivated=$false
    for ($glossaryAttempt=0;$glossaryAttempt -lt 8;$glossaryAttempt++) {
        $glossaryRoot=[System.Windows.Automation.AutomationElement]::FromHandle($hwnd)
        $items=$glossaryRoot.FindAll([System.Windows.Automation.TreeScope]::Descendants,$glossaryCondition)
        for ($gi=0;$gi -lt $items.Count;$gi++) {
            try {
                $button=$items.Item($gi)
                if ($button.Current.ControlType -ne [System.Windows.Automation.ControlType]::Button -or -not $button.Current.IsEnabled) { continue }
                $invoke=$null
                if ($button.TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern,[ref]$invoke)) {
                    $invoke.Invoke()
                    $glossaryActivated=$true
                    break
                }
            } catch [System.Windows.Automation.ElementNotAvailableException] {}
        }
        if ($glossaryActivated) { break }
        Start-Sleep -Milliseconds 200
    }
    if (-not $glossaryActivated) { throw 'ZYN-SCREEN-045: actual glossary mode activation failed' }
    Focus-P02NativeControl -AccessibleName 'Does a native connection mean my work is saved?'
    $glossaryHeading=[System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::NameProperty,'Glossary')
    $glossaryVisible=$false
    for ($gi=0;$gi -lt 8;$gi++) {
        $glossaryRoot=[System.Windows.Automation.AutomationElement]::FromHandle($hwnd)
        $heading=$glossaryRoot.FindFirst([System.Windows.Automation.TreeScope]::Descendants,$glossaryHeading)
        if ($null -ne $heading) {
            try {
                if (-not $heading.Current.IsOffscreen) { $glossaryVisible=$true;break }
                $scroll=$null
                if ($heading.TryGetCurrentPattern([System.Windows.Automation.ScrollItemPattern]::Pattern,[ref]$scroll)) { $scroll.ScrollIntoView() }
            } catch [System.Windows.Automation.ElementNotAvailableException] {}
        }
        Start-Sleep -Milliseconds 200
    }
    if (-not $glossaryVisible) { throw 'ZYN-SCREEN-046: actual glossary heading not visible' }
    Save-NativeFollowup -ScreenshotId 'P02-T10-CTRL-M19-OPT-04' -Shortcut '' -ScreenTitle 'M19 actual offline glossary' -Description 'Real native Help FAQ and glossary panel showing bundled definitions rather than a fake external dictionary' -FinalCandidateId 'M19-OPT-04'
    # UIA-focus the real first FAQ <summary>, never guess tab order after
    # React/WebView2 has re-rendered the FAQ section. The actual disclosure
    # must be keyboard focusable or the capture fails closed (ZYN-SCREEN-043).
    # Do not PageDown after Enter: that moves the expanded answer out of frame.
    # The prior glossary frame intentionally scrolls below the fold. Return to
    # the actual FAQ tab before looking up its disclosure. UIA InvokePattern
    # activates the real local mode idempotently even if the preceding keyboard
    # focus was lost during a WebView2 repaint. No guessed Tab sequence.
    $faqRoot = [System.Windows.Automation.AutomationElement]::FromHandle($hwnd)
    if ($null -eq $faqRoot -or $faqRoot.Current.ProcessId -ne $TargetPid) {
        throw 'ZYN-SCREEN-042: FAQ native UIA handle/PID mismatch'
    }
    $faqCondition = [System.Windows.Automation.PropertyCondition]::new(
        [System.Windows.Automation.AutomationElement]::NameProperty, 'FAQ & glossary')
    $faqTab = $null
    for ($faqAttempt=0; $faqAttempt -lt 8; $faqAttempt++) {
        $faqItems = $faqRoot.FindAll([System.Windows.Automation.TreeScope]::Descendants, $faqCondition)
        for ($faqIndex=0; $faqIndex -lt $faqItems.Count; $faqIndex++) {
            try {
                $candidate = $faqItems.Item($faqIndex)
                if (-not $candidate.Current.IsEnabled -or -not $candidate.Current.IsKeyboardFocusable) { continue }
                $candidate.SetFocus()
                # Use the real provider's button activation when available;
                # otherwise send an actual keyboard Enter to its focused tab.
                $invoke = $null
                if ($candidate.TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern, [ref]$invoke)) {
                    $invoke.Invoke()
                } else {
                    [System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
                }
                $faqTab = $candidate
                break
            } catch [System.Windows.Automation.ElementNotAvailableException] {
                # Retry actual rerendered native element, never a mock.
            } catch [System.InvalidOperationException] {}
        }
        if ($null -ne $faqTab) { break }
        Start-Sleep -Milliseconds 250
    }
    if ($null -eq $faqTab) { throw 'ZYN-SCREEN-044: actual FAQ tab could not be activated' }
    Start-Sleep -Milliseconds 400
    # The page itself is scrollable; UIA ScrollItemPattern (if exposed by
    # WebView2) explicitly brings the real question into view before focus.
    $faqQuestion = [System.Windows.Automation.PropertyCondition]::new(
        [System.Windows.Automation.AutomationElement]::NameProperty, 'Does a native connection mean my work is saved?')
    $question = $faqRoot.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $faqQuestion)
    if ($null -ne $question) {
        try {
            $scrollItem = $null
            if ($question.TryGetCurrentPattern([System.Windows.Automation.ScrollItemPattern]::Pattern, [ref]$scrollItem)) {
                $scrollItem.ScrollIntoView()
            }
        } catch [System.Windows.Automation.ElementNotAvailableException] {}
        catch [System.InvalidOperationException] {}
    }
    # Keep the strict named real native focus gate and actual Enter disclosure.
    Focus-P02NativeControl -AccessibleName 'Does a native connection mean my work is saved?'
    Save-NativeFollowup -ScreenshotId 'P02-T10-CTRL-M19-OPT-05' -Shortcut '{ENTER}' -ScreenTitle 'M19 actual FAQ expanded question' -Description 'Real native Help FAQ with keyboard-expanded disclosure and linked offline guidance' -FinalCandidateId 'M19-OPT-05'
    [System.Windows.Forms.SendKeys]::SendWait('^{2}')
    [System.Windows.Forms.SendKeys]::SendWait('{F1}')
    Focus-P02NativeControl -AccessibleName 'Wiki & link checker'
    [System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
    Start-Sleep -Milliseconds 250
    Focus-P02NativeControl -AccessibleName 'Check bundled article and Wiki mappings'
    Save-NativeFollowup -ScreenshotId 'P02-T10-CTRL-M19-OPT-06' -Shortcut '{ENTER}{PGDN}' -ScreenTitle 'M19 actual local Wiki link checker' -Description 'Real native Wiki source mappings with keyboard-triggered local mapping check; remote GitHub Wiki explicitly unverified' -FinalCandidateId 'M19-OPT-06'
    [System.Windows.Forms.SendKeys]::SendWait('^{2}')
    [System.Windows.Forms.SendKeys]::SendWait('{F1}')
    Start-Sleep -Milliseconds 250
    Focus-P02NativeControl -AccessibleName 'Prepare local report'
    Save-NativeFollowup -ScreenshotId 'P02-T10-CTRL-M19-OPT-07' -Shortcut '{ENTER}{PGDN}' -ScreenTitle 'M19 actual local article error report' -Description 'Real native Help article report opened with a sanitized copy-only payload and no network submission' -FinalCandidateId 'M19-OPT-07'
    Save-NativeFollowup -ScreenshotId 'P02-T10-CTRL-M19-OPT-08' -Shortcut '^{2}{F1}' -ScreenTitle 'M19 actual offline Help indicator' -Description 'Real native Help catalog ready indicator and bundled article inventory without offline-mode false toggle or network dependency' -FinalCandidateId 'M19-OPT-08'
    $OutputDirectory = $m19Output

    # T02.07: verify real native narrow viewport without falsifying responsive screenshots.
    # Tauri enforces a 900px minimum width; the CI desktop starts wider (~998px visible).
    $priorWidth = $width
    $targetWidth = [int][Math]::Min(912, $workArea.Width - 12)
    $targetHeight = [int][Math]::Min(660, $workArea.Height - 12)
    if (-not [ZynoaScreenWin32]::MoveWindow($hwnd, $workArea.Left + 6, $workArea.Top + 6, $targetWidth, $targetHeight, $true)) {
        throw 'ZYN-SCREEN-020: cannot resize real native window for responsive visual proof'
    }
    Start-Sleep -Milliseconds 900
    $narrowVisible = [ZynoaScreenWin32+Rect]::new()
    $narrowStatus = [ZynoaScreenWin32]::DwmGetWindowAttribute($hwnd, 9, [ref]$narrowVisible, $sizeOfRect)
    if ($narrowStatus -ne 0) { throw 'ZYN-SCREEN-021: narrow native DWM frame unavailable' }
    $narrowWidth = $narrowVisible.Right - $narrowVisible.Left
    $narrowHeight = $narrowVisible.Bottom - $narrowVisible.Top
    if ($narrowWidth -gt 920 -or $narrowWidth -ge $priorWidth -or $narrowWidth -lt 880 -or $narrowHeight -lt 600 -or
        $narrowVisible.Left -lt $workArea.Left -or $narrowVisible.Top -lt $workArea.Top -or
        $narrowVisible.Right -gt $workArea.Right -or $narrowVisible.Bottom -gt $workArea.Bottom) {
        throw 'ZYN-SCREEN-022: resized frame did not meet real narrow native viewport requirements'
    }
    $script:bounds = $narrowVisible
    $script:width = $narrowWidth
    $script:height = $narrowHeight
    $OutputDirectory = $m02Output
    Save-NativeFollowup -ScreenshotId 'P02-T02-07' -Shortcut '^{6}' -ScreenTitle 'P02 narrow native gallery' -Description 'Real Tauri resizable window near the 900px minimum, gallery adaptive layout and component metrics'
    Save-NativeFollowup -ScreenshotId 'P02-T02-07-continued' -Shortcut '{PGDN}' -ScreenTitle 'P02 narrow gallery continued' -Description 'Real native narrow window after PageDown, component cards and swatches responsive without horizontal clipping'
    # T02.12: capture BOTH explicit appearance choices at measured native narrow size.
    # Ctrl+2 focuses main, Tab x3 focuses Appearance, Home+Down x2 picks Light.
    # Shift+Tab returns to Appearance; Home+Down picks Dark. No saved preferences.
    Save-NativeFollowup -ScreenshotId 'P02-T02-12-LIGHT' -Shortcut '^{2}{TAB}{TAB}{TAB}{HOME}{DOWN}{DOWN}{TAB}' -ScreenTitle 'P02 explicit light appearance' -Description 'Real Tauri Preferences after selecting Light appearance in the native selector (session only)'
    Save-NativeFollowup -ScreenshotId 'P02-T02-12-DARK' -Shortcut '+{TAB}{HOME}{DOWN}{TAB}' -ScreenTitle 'P02 explicit dark appearance' -Description 'Real Tauri Preferences after selecting Dark appearance in the native selector (session only)'

    # M02-OPT-04: F1 leaves the focused Appearance selector for bundled Help;
    # Ctrl+5 then enters Workbench and End activates the keyboard-guide tab.
    # This remains a real Tauri screenshot candidate, never a final manifest proof.
    Save-NativeFollowup -ScreenshotId 'M02-OPT-04' -Shortcut '{F1}^{5}{TAB}{TAB}{TAB}{TAB}{END}{TAB}{PGDN}' -ScreenTitle 'P02 user-configurable navigation shortcuts' -Description 'Real Windows Tauri keyboard guide with six interactive Ctrl+1 through Ctrl+6 shortcut selectors and reset to defaults'
    # From focused keyboard-guide panel, Tab first selector, choose Ctrl+2 for
    # Overview. The occupied key swaps with Preferences; second candidate shows
    # that change without saving any user preference.
    Save-NativeFollowup -ScreenshotId 'P02-T02-OPT-04-swapped' -Shortcut '{TAB}{HOME}{DOWN}{TAB}' -ScreenTitle 'P02 swapped shortcut settings preview' -Description 'Native Tauri after swapping the Overview Ctrl+1 navigation binding with Ctrl+2; in-memory change only'

    # T03 narrow desktop navigation: escape select focus via F1 and return to
    # Workbench Ctrl+5. The 900px native minimum triggers automatic collapse.
    # Alt+N expands then re-collapses the SAME live Tauri navigation rail.
    [System.Windows.Forms.SendKeys]::SendWait('{F1}')
    Start-Sleep -Milliseconds 400
    Save-NativeFollowup -ScreenshotId 'P02-T03-RAIL-COLLAPSED' -Shortcut '^{5}' -ScreenTitle 'P02 narrow collapsed navigation rail' -Description 'Real 898px native Tauri workbench with responsive collapsed icon rail, active Workbench and full-width main content'
    Save-NativeFollowup -ScreenshotId 'P02-T03-RAIL-EXPANDED' -Shortcut '%n' -ScreenTitle 'P02 narrow expanded navigation rail' -Description 'Real 898px native Tauri after Alt+N expands labelled navigation groups and retains active Workbench'
    Save-NativeFollowup -ScreenshotId 'P02-T03-RAIL-RESTORED' -Shortcut '%n' -ScreenTitle 'P02 narrow navigation rail restored' -Description 'Real 898px native Tauri after Alt+N collapses the sidebar again without navigating away'



}
