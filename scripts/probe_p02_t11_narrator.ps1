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
 [DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte scan, uint flags, UIntPtr extra);
}
'@
function Send-NarratorChord([byte[]]$Keys) {
  foreach ($key in $Keys) {
    [ZynoaNarratorKeyboard]::keybd_event($key,0,0,[UIntPtr]::Zero)
    Start-Sleep -Milliseconds 80
  }
  for ($i=$Keys.Count-1; $i -ge 0; $i--) {
    [ZynoaNarratorKeyboard]::keybd_event($Keys[$i],0,2,[UIntPtr]::Zero)
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
  # Never read the previous clipboard content; overwrite disposable CI clipboard.
  $sentinel='ZYNOA-NARRATOR-'+[Guid]::NewGuid().ToString('N')
  Set-Clipboard -Value $sentinel
  $before=[ZynoaNarratorKeyboard]::GetClipboardSequenceNumber()
  $Control.SetFocus()
  Start-Sleep -Milliseconds 700
  # Microsoft documented Narrator+Tab reads current item; Insert is the SR key.
  Send-NarratorChord ([byte[]]@(0x2D,0x09))
  Start-Sleep -Milliseconds 2200
  # Microsoft documented Narrator+Ctrl+X copies the actual last spoken phrase.
  Send-NarratorChord ([byte[]]@(0x2D,0x11,0x58))
  for ($i=0;$i -lt 12;$i++) {
    Start-Sleep -Milliseconds 300
    $after=[ZynoaNarratorKeyboard]::GetClipboardSequenceNumber()
    if ($after -eq $before) { continue }
    $candidate=Get-Clipboard -Raw
    if ($candidate -is [string] -and $candidate -ne $sentinel) {
      $where=$candidate.IndexOf($ExpectedLabel,[StringComparison]::OrdinalIgnoreCase)
      if ($where -ge 0) {
        $start=[Math]::Max(0,$where-25)
        $len=[Math]::Min($candidate.Length-$start,$ExpectedLabel.Length+65)
        $excerpt=$candidate.Substring($start,$len).Replace([char]13,[char]32).Replace([char]10,[char]32)
        return [ordered]@{stage=$Stage;label=$excerpt;clipboard_sequence_before=[int64]$before;
          clipboard_sequence_after=[int64]$after;actual_speech_clipboard_changed=$true}
      }
    }
  }
  throw "ZYN-NAR-005: actual copied speech missing for stage $Stage"
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
 events=@();status='INCOMPLETE';no_user_data=$true;full_narrator_certified=$false;product_release_approved=$false}
try {
  Start-Process -FilePath $path | Out-Null
  for ($i=0;$i -lt 40;$i++) {
    Start-Sleep -Milliseconds 500
    $found=@(Get-Process -Name Narrator -ErrorAction SilentlyContinue)
    if ($found.Count -eq 1) { $narrator=$found[0];break }
  }
  if ($null -eq $narrator) { throw 'ZYN-NAR-010: Narrator process unavailable' }
  $proof.narrator_pid=[int]$narrator.Id
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
  [System.Windows.Forms.SendKeys]::SendWait('^+p')
  Start-Sleep -Milliseconds 1000
  $search=Find-FocusableNativeControl $uia 'Search available commands and offline Help'
  $proof.events+= (Read-ActualNarratorPhrase 'palette' $search 'Search available commands and offline Help')
  [System.Windows.Forms.SendKeys]::SendWait('M19-OPT-06')
  Start-Sleep -Milliseconds 1000
  $value=$search.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value
  if ($value -cne 'M19-OPT-06') { throw 'ZYN-NAR-014: native keyboard input missing' }
  $proof.actual_keyboard_input_value=$value
  [System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
  Start-Sleep -Milliseconds 1800
  $heading=Find-FocusableNativeControl $uia 'Wiki mapping and link checker'
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
