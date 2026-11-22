# P01-T10: actual Windows Tauri process screenshot, not a browser preview.
param(
    [Parameter(Mandatory = $true)][int]$TargetPid,
    [Parameter(Mandatory = $true)][string]$OutputDirectory,
    [Parameter(Mandatory = $true)][string]$SourceSha
)
$ErrorActionPreference = 'Stop'
if ($SourceSha -notmatch '^[0-9a-f]{40}$') { throw 'ZYN-SCREEN-001: invalid source commit' }
Add-Type -AssemblyName System.Drawing
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
$width = $bounds.Right - $bounds.Left
$height = $bounds.Bottom - $bounds.Top
if ($width -lt 900 -or $height -lt 620 -or $width -gt 4000 -or $height -gt 3000) {
    throw 'ZYN-SCREEN-005: invalid desktop window dimensions'
}
if (-not [ZynoaScreenWin32]::SetForegroundWindow($hwnd)) {
    throw 'ZYN-SCREEN-006: native window cannot become foreground'
}
Start-Sleep -Milliseconds 800
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
    source = 'GitHub Windows Actions actual Tauri process'
    screen = 'Overview (empty workspace)'
    capture_status = 'candidate_pending_visual_review'
    capture_verified = $false
    window_width = $width
    window_height = $height
    sha256 = $hash
    alt_text = 'Zynoa native desktop Overview with local startup and disabled workspace creation'
    privacy = 'Disposable CI fixture with no user content or secrets'
}
$meta | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (
    Join-Path $OutputDirectory 'M01-S01.capture.json') -Encoding UTF8
Write-Output 'Candidate native screenshot captured, human verification remains pending'
