# Actual Windows WebView2 keyboard/UI Automation probe, synthetic runner profile only.
param(
 [Parameter(Mandatory=$true)][string]$Executable,
 [Parameter(Mandatory=$true)][string]$SourceSha,
 [Parameter(Mandatory=$true)][string]$OutputDirectory
)
$ErrorActionPreference='Stop'
if ($env:GITHUB_ACTIONS -ne 'true' -or $SourceSha -cnotmatch '^[a-f0-9]{40}$') { throw 'ZYN-CHAT-PROBE-001: disposable CI only' }
if ((git rev-parse HEAD).Trim() -cne $SourceSha) { throw 'ZYN-CHAT-PROBE-002: source mismatch' }
$expected=Join-Path $env:GITHUB_WORKSPACE 'apps\desktop\src-tauri\target\release\zynoa_desktop.exe'
if ([IO.Path]::GetFullPath($Executable) -ine [IO.Path]::GetFullPath($expected)) { throw 'ZYN-CHAT-PROBE-003: unexpected executable' }
if (Test-Path -LiteralPath $OutputDirectory) { throw 'ZYN-CHAT-PROBE-004: proof directory already exists' }
New-Item -ItemType Directory -Path $OutputDirectory | Out-Null
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class ChatProbeWindow {
 [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hwnd);
 [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
 [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hwnd, int command);
 [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hwnd, out RECT rect);
 [StructLayout(LayoutKind.Sequential)] public struct RECT {public int Left,Top,Right,Bottom;}
}
'@
$script:app=$null
$script:root=$null
$script:hwnd=[IntPtr]::Zero
$title='P03 synthetic conversation'
$content='P03 synthetic persisted message'
function Start-Native {
 $script:app=Start-Process -FilePath $Executable -PassThru
 for ($i=0;$i -lt 90;$i++) {
   Start-Sleep -Milliseconds 500
   $script:app.Refresh()
   if ($script:app.HasExited) { throw 'ZYN-CHAT-PROBE-005: native process exited' }
   if ($script:app.MainWindowHandle -ne [IntPtr]::Zero) {break}
 }
 $script:hwnd=$script:app.MainWindowHandle
 if ($script:hwnd -eq [IntPtr]::Zero) {throw 'ZYN-CHAT-PROBE-006: window missing'}
 [void][ChatProbeWindow]::ShowWindow($script:hwnd,3)
 [void][ChatProbeWindow]::SetForegroundWindow($script:hwnd)
 $script:root=[System.Windows.Automation.AutomationElement]::FromHandle($script:hwnd)
 if ($null -eq $script:root -or $script:root.Current.ProcessId -ne $script:app.Id) {throw 'ZYN-CHAT-PROBE-007: HWND/PID mismatch'}
}
function Stop-Native {
 if ($null -ne $script:app) {
   $script:app.Refresh()
   if (!$script:app.HasExited) {
     [void]$script:app.CloseMainWindow()
     if (!$script:app.WaitForExit(10000)) {Stop-Process -Id $script:app.Id -Force; $script:app.WaitForExit()}
   }
 }
 $script:root=$null
}
function Wait-Name([string]$Name,[string]$Type='', [bool]$Enabled=$false) {
 $condition=[System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::NameProperty,$Name)
 for ($i=0;$i -lt 80;$i++) {
   $matches=$script:root.FindAll([System.Windows.Automation.TreeScope]::Descendants,$condition)
   for ($j=0;$j -lt $matches.Count;$j++) {
     try {
       $e=$matches.Item($j)
       if ($Type -and $e.Current.ControlType.ProgrammaticName -ne ('ControlType.'+$Type)) {continue}
       if ($Enabled -and !$e.Current.IsEnabled) {continue}
       if (!$e.Current.IsOffscreen -or $Type) {return $e}
     } catch [System.Windows.Automation.ElementNotAvailableException] {}
   }
   Start-Sleep -Milliseconds 250
 }
 throw ('ZYN-CHAT-PROBE-008: required UI control missing: '+$Name)
}
function Focus-Control($Control) {
 $pattern=$null
 if ($Control.TryGetCurrentPattern([System.Windows.Automation.ScrollItemPattern]::Pattern,[ref]$pattern)) {$pattern.ScrollIntoView()}
 [void][ChatProbeWindow]::SetForegroundWindow($script:hwnd)
 if ([ChatProbeWindow]::GetForegroundWindow() -ne $script:hwnd) {throw 'ZYN-CHAT-PROBE-009: foreground mismatch'}
 $Control.SetFocus()
 Start-Sleep -Milliseconds 150
}
function Click-Control([string]$Name) {
 $control=Wait-Name $Name 'Button' $true
 Focus-Control $control
 $pattern=$control.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern)
 $pattern.Invoke()
}
function Type-Exact([string]$Name,[string]$Text) {
 $control=Wait-Name $Name 'Edit' $true
 Focus-Control $control
 [System.Windows.Forms.SendKeys]::SendWait($Text)
 for ($i=0;$i -lt 20;$i++) {
   $control=Wait-Name $Name 'Edit' $true
   $value=$control.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
   if ($value.Current.Value -ceq $Text) {return}
   Start-Sleep -Milliseconds 250
 }
 throw 'ZYN-CHAT-PROBE-010: keyboard input was not reflected by actual UIA value'
}
function Capture([string]$Name) {
 [void][ChatProbeWindow]::SetForegroundWindow($script:hwnd)
 Start-Sleep -Milliseconds 400
 if ([ChatProbeWindow]::GetForegroundWindow() -ne $script:hwnd) {throw 'ZYN-CHAT-PROBE-011: screenshot foreground mismatch'}
 $rect=New-Object ChatProbeWindow+RECT
 if (![ChatProbeWindow]::GetWindowRect($script:hwnd,[ref]$rect)) {throw 'ZYN-CHAT-PROBE-012: window rect unavailable'}
 $screen=[System.Windows.Forms.SystemInformation]::VirtualScreen
 $x=[Math]::Max($screen.Left,$rect.Left);$y=[Math]::Max($screen.Top,$rect.Top)
 $w=[Math]::Min($screen.Right,$rect.Right)-$x;$h=[Math]::Min($screen.Bottom,$rect.Bottom)-$y
 if ($w -lt 800 -or $h -lt 500) {throw 'ZYN-CHAT-PROBE-013: capture too small'}
 $bitmap=[System.Drawing.Bitmap]::new($w,$h)
 try {
   $graphics=[System.Drawing.Graphics]::FromImage($bitmap)
   try {$graphics.CopyFromScreen($x,$y,0,0,$bitmap.Size)} finally {$graphics.Dispose()}
   $colors=[System.Collections.Generic.HashSet[int]]::new()
   for ($ix=0;$ix -lt 20;$ix++) {for ($iy=0;$iy -lt 15;$iy++) {[void]$colors.Add($bitmap.GetPixel([int](($w-1)*$ix/20),[int](($h-1)*$iy/15)).ToArgb())}}
   if ($colors.Count -lt 6) {throw 'ZYN-CHAT-PROBE-014: blank capture'}
   $path=Join-Path $OutputDirectory $Name
   $bitmap.Save($path,[System.Drawing.Imaging.ImageFormat]::Png)
 } finally {$bitmap.Dispose()}
}
function Read-Vault([string]$Stage) {
 $env:ZYNOA_CHAT_PROOF_STAGE=$Stage
 $env:ZYNOA_CHAT_PROOF_DIR=$OutputDirectory
 python scripts/verify_p03_chat_ui_database.py
 if ($LASTEXITCODE -ne 0) {throw 'ZYN-CHAT-PROBE-015: independent SQLite verification failed'}
}
try {
 Read-Vault 'empty'
 Start-Native
 $firstPid=$script:app.Id
 Click-Control 'Chat'
 [void](Wait-Name 'Conversation title' 'Edit' $true)
 [void](Wait-Name 'No saved conversations.')
 Capture 'M03-S01-candidate.png'
 Type-Exact 'Conversation title' $title
 Click-Control 'Create conversation'
 [void](Wait-Name 'Message' 'Edit' $true)
 Type-Exact 'Message' $content
 Click-Control 'Save message'
 [void](Wait-Name $content)
 Stop-Native
 Read-Vault 'saved'
 Start-Native
 $secondPid=$script:app.Id
 if ($firstPid -eq $secondPid) {throw 'ZYN-CHAT-PROBE-016: process identity not distinct'}
 Click-Control 'Chat'
 Click-Control $title
 [void](Wait-Name $content)
 [void](Wait-Name 'Message' 'Edit' $true)
 Capture 'M03-S02-candidate.png'
 Stop-Native
 Read-Vault 'reopened'
 $images=[ordered]@{}
 foreach ($name in @('M03-S01-candidate.png','M03-S02-candidate.png')) {
   $images[$name]=(Get-FileHash -LiteralPath (Join-Path $OutputDirectory $name) -Algorithm SHA256).Hash.ToLowerInvariant()
 }
 $proof=[ordered]@{schema_version=1;source_commit_sha=$SourceSha;executable_sha256=(Get-FileHash -LiteralPath $Executable -Algorithm SHA256).Hash.ToLowerInvariant();method='actual Windows Tauri UIA, real keyboard ValuePattern readback and independent read-only SQLite';first_pid=$firstPid;reopened_pid=$secondPid;synthetic_only=$true;empty_profile=$true;keyboard_input_verified=$true;ui_create_save=$true;ui_reopen_readback=$true;database_reopen_identity_verified=$true;images=$images;visual_review='candidate_pending_visual_review';full_accessibility_certified=$false;model_inference_claimed=$false}
 $proof | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'p03-chat-ui-proof.json') -Encoding utf8
 Write-Output 'P03 scoped real native chat interaction and independent restart readback passed'
} finally {Stop-Native}
