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
