# P01-T10: actual Windows Tauri process screenshot, not a browser preview.
param(
    [Parameter(Mandatory = $true)][int]$TargetPid,
    [Parameter(Mandatory = $true)][string]$OutputDirectory,
    [Parameter(Mandatory = $true)][string]$SourceSha,
    [Parameter(Mandatory = $true)][string]$BuiltSha
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
        [Parameter(Mandatory = $true)][string]$Shortcut,
        [Parameter(Mandatory = $true)][string]$ScreenTitle,
        [Parameter(Mandatory = $true)][string]$Description
    )
    $proc.Refresh()
    if ($proc.HasExited -or -not [ZynoaScreenWin32]::IsWindowVisible($hwnd)) {
        throw 'ZYN-SCREEN-016: native window is no longer running and visible'
    }
    [System.Windows.Forms.SendKeys]::SendWait($Shortcut)
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
    $viewMeta | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (
        Join-Path $OutputDirectory ($ScreenshotId + '.capture.json')) -Encoding UTF8
    Write-Output ('Native candidate captured: ' + $ScreenshotId)
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
    # T04: open palette from Help, type allowlisted view and execute with Enter.
    # Focus moves to destination main on palette navigation; never run arbitrary code.
    $OutputDirectory = $m02Output
    [System.Windows.Forms.SendKeys]::SendWait('^+p')
    Start-Sleep -Milliseconds 500
    Save-NativeFollowup -ScreenshotId 'P02-T04-ENTER-NAV' -Shortcut 'workbench{ENTER}' -ScreenTitle 'P02 palette keyboard navigation to Workbench' -Description 'Real Windows Tauri Workbench navigated by opening Ctrl+Shift+P palette, entering workbench and pressing Enter'
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
    Save-NativeFollowup -ScreenshotId 'P02-T03-RAIL-COLLAPSED' -Shortcut '{F1}^{5}' -ScreenTitle 'P02 narrow collapsed navigation rail' -Description 'Real 898px native Tauri workbench with responsive collapsed icon rail, active Workbench and full-width main content'
    Save-NativeFollowup -ScreenshotId 'P02-T03-RAIL-EXPANDED' -Shortcut '%n' -ScreenTitle 'P02 narrow expanded navigation rail' -Description 'Real 898px native Tauri after Alt+N expands labelled navigation groups and retains active Workbench'
    Save-NativeFollowup -ScreenshotId 'P02-T03-RAIL-RESTORED' -Shortcut '%n' -ScreenTitle 'P02 narrow navigation rail restored' -Description 'Real 898px native Tauri after Alt+N collapses the sidebar again without navigating away'



}
