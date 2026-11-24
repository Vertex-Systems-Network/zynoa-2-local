# Live Microsoft Narrator speech probe, only on disposable GitHub Actions Windows.
param([Parameter(Mandatory=$true)][string]$Executable,
      [Parameter(Mandatory=$true)][string]$SourceSha,
      [Parameter(Mandatory=$true)][string]$OutputPath)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
if ($env:GITHUB_ACTIONS -ne 'true' -or $env:RUNNER_OS -ne 'Windows') { throw 'ZYN-NAR-001: disposable Windows CI only' }
if ($SourceSha -cnotmatch '^[a-f0-9]{40}$' -or ((& git -C $env:GITHUB_WORKSPACE rev-parse HEAD).Trim() -cne $SourceSha)) { throw 'ZYN-NAR-002: source SHA mismatch' }
if (-not (Test-Path -LiteralPath $Executable -PathType Leaf)) { throw 'ZYN-NAR-003: real app missing' }
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class ZynoaNarratorKeyboard {
 [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
 [DllImport("user32.dll")] public static extern uint GetClipboardSequenceNumber();
 [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
 [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
 [DllImport("user32.dll")] public static extern uint MapVirtualKey(uint code, uint mapType);
 [DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte scan, uint flags, UIntPtr extra);
}
'@
function Send-NarratorChord([byte[]]$Keys) {
  foreach ($key in $Keys) {
    $flags=if ($key -eq 0x2D) { [uint32]1 } else { [uint32]0 }
    $scan=[byte]([ZynoaNarratorKeyboard]::MapVirtualKey($key,0) -band 0xFF)
    [ZynoaNarratorKeyboard]::keybd_event($key,$scan,$flags,[UIntPtr]::Zero)
    Start-Sleep -Milliseconds 80
  }
  for ($i=$Keys.Count-1; $i -ge 0; $i--) {
    $key=$Keys[$i]
    $flags=if ($key -eq 0x2D) { [uint32]3 } else { [uint32]2 }
    $scan=[byte]([ZynoaNarratorKeyboard]::MapVirtualKey($key,0) -band 0xFF)
    [ZynoaNarratorKeyboard]::keybd_event($key,$scan,$flags,[UIntPtr]::Zero)
    Start-Sleep -Milliseconds 80
  }
}
function Find-FocusableNativeControl($Root,[string]$Label) {
  for ($retry=0;$retry -lt 12;$retry++) {
    $items=$Root.FindAll([System.Windows.Automation.TreeScope]::Descendants,
      [System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::NameProperty,$Label))
    for ($i=0;$i -lt $items.Count;$i++) {
      try {
        $item=$items.Item($i)
        if ($item.Current.IsEnabled -and $item.Current.IsKeyboardFocusable -and -not $item.Current.IsOffscreen) { return $item }
      } catch [System.Windows.Automation.ElementNotAvailableException] {}
    }
    Start-Sleep -Milliseconds 400
  }
  throw 'ZYN-NAR-004: required native focus target missing'
}
function Read-ActualNarratorPhrase([string]$Stage,$Control,[string]$ExpectedLabel) {
  foreach ($modifier in @([byte]0x2D,[byte]0x14)) {
    $keyName=if ($modifier -eq 0x2D) { 'ExtendedInsert' } else { 'CapsLock' }
    # Never read the previous clipboard; the disposable CI clipboard is reset per attempt.
    $sentinel='ZYNOA-NARRATOR-'+[Guid]::NewGuid().ToString('N')
    Set-Clipboard -Value $sentinel
    $before=[ZynoaNarratorKeyboard]::GetClipboardSequenceNumber()
    if (-not [ZynoaNarratorKeyboard]::SetForegroundWindow($app.MainWindowHandle)) {
      throw 'ZYN-NAR-013: app foreground unavailable before spoken-item query'
    }
    $Control.SetFocus()
    Start-Sleep -Milliseconds 1200
    $foregroundPid=[uint32]0
    [void][ZynoaNarratorKeyboard]::GetWindowThreadProcessId([ZynoaNarratorKeyboard]::GetForegroundWindow(),[ref]$foregroundPid)
    if ($foregroundPid -ne $app.Id) { throw 'ZYN-NAR-017: foreground PID differs from native app' }
    # Narrator+Tab reads the current item. Both default modifier keys are supported.
    Send-NarratorChord ([byte[]]@($modifier,0x09))
    Start-Sleep -Milliseconds 3000
    # Narrator+Ctrl+X copies the last actual spoken phrase on supporting OS versions.
    Send-NarratorChord ([byte[]]@($modifier,0x11,0x58))
    $changed=$false
    $length=0
    for ($i=0;$i -lt 16;$i++) {
      Start-Sleep -Milliseconds 350
      $after=[ZynoaNarratorKeyboard]::GetClipboardSequenceNumber()
      if ($after -eq $before) { continue }
      $changed=$true
      $candidate=Get-Clipboard -Raw
      if ($candidate -is [string] -and $candidate -ne $sentinel) {
        $length=$candidate.Length
        $where=$candidate.IndexOf($ExpectedLabel,[StringComparison]::OrdinalIgnoreCase)
        if ($where -ge 0) {
          $start=[Math]::Max(0,$where-25)
          $len=[Math]::Min($candidate.Length-$start,$ExpectedLabel.Length+65)
          $excerpt=$candidate.Substring($start,$len).Replace([char]13,[char]32).Replace([char]10,[char]32)
          $proof.attempts+= [ordered]@{stage=$Stage;modifier=$keyName;clipboard_changed=$true;
            clipboard_text_length=$length;expected_phrase_found=$true;foreground_pid=[int]$foregroundPid}
          return [ordered]@{stage=$Stage;label=$excerpt;clipboard_sequence_before=[int64]$before;
            clipboard_sequence_after=[int64]$after;actual_speech_clipboard_changed=$true}
        }
      }
    }
    # No arbitrary clipboard text is saved. Only booleans/length and PID are recorded.
    $proof.attempts+= [ordered]@{stage=$Stage;modifier=$keyName;clipboard_changed=$changed;
      clipboard_text_length=$length;expected_phrase_found=$false;foreground_pid=[int]$foregroundPid}
    Write-Output ("ZYN-NAR-RETRY stage={0}; key={1}; clipboard_changed={2}; text_length={3}" -f $Stage,$keyName,$changed,$length) | Out-Host
  }
  throw "ZYN-NAR-005: actual copied speech missing for stage $Stage after both Narrator modifiers; inspect OS support and receipt attempts"
}
$path=Join-Path $env:WINDIR 'System32\Narrator.exe'
if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw 'ZYN-NAR-006: Microsoft Narrator unavailable on runner' }
$signature=Get-AuthenticodeSignature -LiteralPath $path
if ($signature.Status -ne 'Valid' -or $null -eq $signature.SignerCertificate -or $signature.SignerCertificate.Subject -notmatch 'Microsoft') { throw 'ZYN-NAR-007: Microsoft signature unavailable' }
if (Get-Process -Name Narrator -ErrorAction SilentlyContinue) { throw 'ZYN-NAR-008: pre-existing Narrator session' }
if (Get-Process -Name nvda -ErrorAction SilentlyContinue) { throw 'ZYN-NAR-009: competing screen reader' }
$app=$null
$narrator=$null
$proof=[ordered]@{schema_version=1;source_commit_sha=$SourceSha;github_run_id=[string]$env:GITHUB_RUN_ID;
 target='Real Microsoft Narrator speech copied from native Windows Tauri WebView2';
 app_executable_sha256=(Get-FileHash -LiteralPath $Executable -Algorithm SHA256).Hash.ToLowerInvariant();
 narrator_executable_sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant();
 narrator_signature_verified=$true;narrator_version=(Get-Item -LiteralPath $path).VersionInfo.FileVersion;
 app_pid=0;narrator_pid=0;native_uia_pid_match=$false;actual_keyboard_input_value='';
 os_version=[Environment]::OSVersion.Version.ToString();
 os_product_name=(Get-ItemProperty -LiteralPath 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion' -Name ProductName).ProductName;
 os_build_revision=[int](Get-ItemProperty -LiteralPath 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion' -Name UBR).UBR;
 palette_open_method='NotReached';attempts=@();events=@();status='INCOMPLETE';no_user_data=$true;full_narrator_certified=$false;product_release_approved=$false}
try {
  Start-Process -FilePath $path | Out-Null
  for ($i=0;$i -lt 40;$i++) {
    Start-Sleep -Milliseconds 500
    $found=@(Get-Process -Name Narrator -ErrorAction SilentlyContinue)
    if ($found.Count -eq 1) { $narrator=$found[0];break }
  }
  if ($null -eq $narrator) { throw 'ZYN-NAR-010: Narrator process unavailable' }
  $proof.narrator_pid=[int]$narrator.Id
  # Let the installed reader finish its initial startup before foregrounding the app.
  Start-Sleep -Milliseconds 3500
  $app=Start-Process -FilePath $Executable -PassThru
  $proof.app_pid=[int]$app.Id
  $uia=$null
  for ($i=0;$i -lt 100;$i++) {
    Start-Sleep -Milliseconds 400
    $app.Refresh()
    if ($app.HasExited) { throw 'ZYN-NAR-011: real native app exited' }
    if ($app.MainWindowHandle -ne [IntPtr]::Zero) {
      $uia=[System.Windows.Automation.AutomationElement]::FromHandle($app.MainWindowHandle)
      if ($null -ne $uia -and $uia.Current.ProcessId -eq $app.Id) { break }
      $uia=$null
    }
  }
  if ($null -eq $uia) { throw 'ZYN-NAR-012: native app identity unavailable' }
  $proof.native_uia_pid_match=$true
  if (-not [ZynoaNarratorKeyboard]::SetForegroundWindow($app.MainWindowHandle)) { throw 'ZYN-NAR-013: foreground failed' }
  Start-Sleep -Milliseconds 600
  [System.Windows.Forms.SendKeys]::SendWait('^{2}')
  Start-Sleep -Milliseconds 1000
  $appearance=Find-FocusableNativeControl $uia 'Interface appearance'
  $proof.events+= (Read-ActualNarratorPhrase 'preferences' $appearance 'Interface appearance')
  # The last-spoken-phrase command succeeded in the prior actual run, but
  # the next app shortcut was intercepted or its dialog was not focusable.
  # Microsoft Standard Narrator+3 passes the next key(s) to the application.
  # Re-anchor native app foreground, then use the documented pass-through.
  if (-not [ZynoaNarratorKeyboard]::SetForegroundWindow($app.MainWindowHandle)) { throw 'ZYN-NAR-013: palette foreground failed' }
  Send-NarratorChord ([byte[]]@(0x2D,0x33))
  Start-Sleep -Milliseconds 200
  Send-NarratorChord ([byte[]]@(0x11,0x10,0x50))
  Start-Sleep -Milliseconds 1200
  $search=$null
  try {
    $search=Find-FocusableNativeControl $uia 'Search available commands and offline Help'
    $proof.palette_open_method='NarratorPassThroughCtrlShiftP'
  } catch {
    # A real toolbar control is a legitimate alternative accessible entry
    # point. Never inject DOM events or manufacture speech to pass this test.
    $uia=[System.Windows.Automation.AutomationElement]::FromHandle($app.MainWindowHandle)
    $buttons=$uia.FindAll([System.Windows.Automation.TreeScope]::Descendants,
      [System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::ControlTypeProperty,[System.Windows.Automation.ControlType]::Button))
    $opened=$false
    for ($j=0;$j -lt $buttons.Count;$j++) {
      try {
        $button=$buttons.Item($j)
        if (-not $button.Current.IsEnabled -or $button.Current.Name -notlike '*Search or run a command*') { continue }
        $pattern=$null
        if ($button.TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern,[ref]$pattern)) {
          $pattern.Invoke()
          $opened=$true
          break
        }
      } catch [System.Windows.Automation.ElementNotAvailableException] {}
      catch [System.InvalidOperationException] {}
    }
    if (-not $opened) { throw 'ZYN-NAR-018: actual command toolbar button could not open palette' }
    Start-Sleep -Milliseconds 1000
    $search=Find-FocusableNativeControl $uia 'Search available commands and offline Help'
    $proof.palette_open_method='NativeToolbarInvoke'
  }
  Write-Host ("ZYN-NAR-PALETTE method="+$proof.palette_open_method)
  $proof.events+= (Read-ActualNarratorPhrase 'palette' $search 'Search available commands and offline Help')
  # Narrator scan mode automatically stops in edit fields. Re-focus the
  # verified combobox after the spoken-label clipboard query, then type.
  $search.SetFocus()
  Start-Sleep -Milliseconds 300
  [System.Windows.Forms.SendKeys]::SendWait('M19-OPT-06')
  Start-Sleep -Milliseconds 1000
  $value=$search.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value
  if ($value -cne 'M19-OPT-06') { throw 'ZYN-NAR-014: native keyboard input missing' }
  $proof.actual_keyboard_input_value=$value
  [System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
  Start-Sleep -Milliseconds 1800
  # Real Help heading may be non-keyboard-focusable in the native provider;
  # the selected option's real toggle button is also a valid spoken target.
  $heading=$null
  try {
    $heading=Find-FocusableNativeControl $uia 'Wiki mapping and link checker'
  } catch {
    $heading=Find-FocusableNativeControl $uia 'M19-OPT-06 Wiki mapping and link checker'
  }
  $proof.events+= (Read-ActualNarratorPhrase 'help' $heading 'Wiki mapping and link checker')
  $app.Refresh();$narrator.Refresh()
  if ($app.HasExited -or $narrator.HasExited) { throw 'ZYN-NAR-015: native process ended before proof' }
  $proof.status='CAPTURED'
} finally {
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutputPath) | Out-Null
  $proof | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $OutputPath -Encoding UTF8
  if ($null -ne $app) { $app.Refresh();if (-not $app.HasExited) { Stop-Process -Id $app.Id -Force };$app.Dispose() }
  Get-Process -Name Narrator -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
  Set-Clipboard -Value 'ZYNOA-NARRATOR-DISPOSABLE-CI-COMPLETE'
}
