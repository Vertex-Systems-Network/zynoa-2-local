# Live Microsoft Narrator speech probe, only on disposable GitHub Actions Windows.
param([Parameter(Mandatory=$true)][string]$Executable,
      [Parameter(Mandatory=$true)][string]$SourceSha,
      [Parameter(Mandatory=$true)][string]$OutputPath,
      [string]$DiagnosticBinarySourceSha='',
      [string]$DiagnosticBinarySha256='',
      [switch]$M26Only)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
if ($env:GITHUB_ACTIONS -ne 'true' -or $env:RUNNER_OS -ne 'Windows') { throw 'ZYN-NAR-001: disposable Windows CI only' }
if ($SourceSha -cnotmatch '^[a-f0-9]{40}$' -or ((& git -C $env:GITHUB_WORKSPACE rev-parse HEAD).Trim() -cne $SourceSha)) { throw 'ZYN-NAR-002: source SHA mismatch' }
if (-not (Test-Path -LiteralPath $Executable -PathType Leaf)) { throw 'ZYN-NAR-003: real app missing' }
# Diagnostic artifact reuse is explicit and can never satisfy exact-head acceptance.
$binarySourceSha=$SourceSha
if ($M26Only -and ($DiagnosticBinarySourceSha -ne '' -or $DiagnosticBinarySha256 -ne '')) { throw 'ZYN-M26-NAR-001: exact-head M26 binary required' }
if ($DiagnosticBinarySourceSha -ne '') {
  if ($DiagnosticBinarySourceSha -cnotmatch '^[a-f0-9]{40}$' -or $DiagnosticBinarySha256 -cnotmatch '^[a-f0-9]{64}$' -or (Get-FileHash -LiteralPath $Executable -Algorithm SHA256).Hash.ToLowerInvariant() -cne $DiagnosticBinarySha256) {
    throw 'ZYN-NAR-019: diagnostic executable digest mismatch'
  }
  $binarySourceSha=$DiagnosticBinarySourceSha
} elseif ($DiagnosticBinarySha256 -ne '') { throw 'ZYN-NAR-019: diagnostic source identity missing' }

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
 [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
 [DllImport("user32.dll")] public static extern void mouse_event(uint flags, uint dx, uint dy, uint data, UIntPtr extra);
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
function Get-CurrentNativeRoot {
  $app.Refresh()
  if ($app.HasExited -or $app.MainWindowHandle -eq [IntPtr]::Zero) { throw 'ZYN-NAR-011: native app unavailable' }
  $root=[System.Windows.Automation.AutomationElement]::FromHandle($app.MainWindowHandle)
  if ($null -eq $root -or $root.Current.ProcessId -ne $app.Id) { throw 'ZYN-NAR-012: native root identity mismatch' }
  return $root
}
function Find-FocusableNativeControl($Root,[string]$Label,[int]$Retries=12) {
  for ($retry=0;$retry -lt $Retries;$retry++) {
    # Re-read HWND/UIA root after each modal or provider transition.
    $Root=Get-CurrentNativeRoot
    $condition=[System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::NameProperty,$Label)
    $items=$Root.FindAll([System.Windows.Automation.TreeScope]::Descendants,$condition)
    for ($i=0;$i -lt $items.Count;$i++) {
      try {
        $item=$items.Item($i)
        if ($item.Current.IsEnabled -and $item.Current.IsKeyboardFocusable -and -not $item.Current.IsOffscreen) { return $item }
      } catch [System.Windows.Automation.ElementNotAvailableException] {}
    }
    Start-Sleep -Milliseconds 400
  }
  throw "ZYN-NAR-004: required native focus target missing: $Label"
}
function Get-PaletteNativeState {
  $root=Get-CurrentNativeRoot
  $result=[ordered]@{}
  foreach ($label in @('Command palette','Search available commands and offline Help','Interface appearance')) {
    $items=$root.FindAll([System.Windows.Automation.TreeScope]::Descendants,
      [System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::NameProperty,$label))
    $focusable=0
    for ($i=0;$i -lt $items.Count;$i++) {
      try { if ($items.Item($i).Current.IsEnabled -and $items.Item($i).Current.IsKeyboardFocusable -and -not $items.Item($i).Current.IsOffscreen) { $focusable++ } }
      catch [System.Windows.Automation.ElementNotAvailableException] {}
    }
    $result[$label]=[ordered]@{count=$items.Count;visible_focusable=$focusable}
  }
  return $result
}
function Find-ActualToolbarButton {
  $root=Get-CurrentNativeRoot
  $buttons=$root.FindAll([System.Windows.Automation.TreeScope]::Descendants,
    [System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::ControlTypeProperty,[System.Windows.Automation.ControlType]::Button))
  for ($j=0;$j -lt $buttons.Count;$j++) {
    try {
      $button=$buttons.Item($j)
      if ($button.Current.IsEnabled -and -not $button.Current.IsOffscreen -and $button.Current.Name -like '*Search or run a command*') { return $button }
    } catch [System.Windows.Automation.ElementNotAvailableException] {}
  }
  return $null
}
function Invoke-ActualToolbarClick($Button) {
  if ($null -eq $Button) { return $false }
  # No coordinate guesses: use the OS provider's actual named button bounds.
  $point=New-Object System.Windows.Point
  if (-not $Button.TryGetClickablePoint([ref]$point)) { return $false }
  $bounds=(Get-CurrentNativeRoot).Current.BoundingRectangle
  if (-not $bounds.Contains($point)) { throw 'ZYN-NAR-017: toolbar point outside verified app window' }
  if (-not [ZynoaNarratorKeyboard]::SetForegroundWindow($app.MainWindowHandle)) { throw 'ZYN-NAR-013: toolbar foreground failed' }
  if (-not [ZynoaNarratorKeyboard]::SetCursorPos([int]$point.X,[int]$point.Y)) { return $false }
  [ZynoaNarratorKeyboard]::mouse_event(2,0,0,0,[UIntPtr]::Zero)
  [ZynoaNarratorKeyboard]::mouse_event(4,0,0,0,[UIntPtr]::Zero)
  return $true
}
function Read-ActualNarratorPhrase([string]$Stage,$Control,[string]$ExpectedLabel) {
  $modifiers=@([byte]0x2D,[byte]0x14)
  if ($script:workingNarratorModifier -eq 0x14) { $modifiers=@([byte]0x14,[byte]0x2D) }
  foreach ($modifier in $modifiers) {
    $keyName=if ($modifier -eq 0x2D) { 'ExtendedInsert' } else { 'CapsLock' }
    # Never read the previous clipboard; the disposable CI clipboard is reset per attempt.
    $sentinel='ZYNOA-NARRATOR-'+[Guid]::NewGuid().ToString('N')
    Set-Clipboard -Value $sentinel
    $before=[ZynoaNarratorKeyboard]::GetClipboardSequenceNumber()
    if (-not [ZynoaNarratorKeyboard]::SetForegroundWindow($app.MainWindowHandle)) {
      throw 'ZYN-NAR-013: app foreground unavailable before spoken-item query'
    }
    # The keyboard focus and Narrator scan cursor may differ, especially in an
    # aria-activedescendant combobox. Force a genuine focus transition for the
    # palette, then move Narrator's reading cursor to the system cursor.
    if ($Stage -eq 'palette') {
      $close=Find-FocusableNativeControl (Get-CurrentNativeRoot) 'Close command palette' 4
      $close.SetFocus()
      Start-Sleep -Milliseconds 250
      $Control=Find-FocusableNativeControl (Get-CurrentNativeRoot) $ExpectedLabel 4
    }
    $Control.SetFocus()
    Start-Sleep -Milliseconds 700
    $nativeFocus=[System.Windows.Automation.AutomationElement]::FocusedElement
    $focusMatches=$false
    if ($null -ne $nativeFocus) {
      $focusMatches=$nativeFocus.Current.Name -eq $ExpectedLabel
    }
    # Microsoft Standard Narrator+Left bracket moves the reading cursor to
    # system focus. 0xDB is VK_OEM_4 on this English Windows runner.
    if ($Stage -ne 'preferences') {
      Send-NarratorChord ([byte[]]@($modifier,0xDB))
      Start-Sleep -Milliseconds 700
    } else {
      Start-Sleep -Milliseconds 500
    }
    $foregroundPid=[uint32]0
    [void][ZynoaNarratorKeyboard]::GetWindowThreadProcessId([ZynoaNarratorKeyboard]::GetForegroundWindow(),[ref]$foregroundPid)
    if ($foregroundPid -ne $app.Id) {
      # Narrator startup/help can briefly acquire foreground. Restore actual
      # app focus once and independently recheck before any speech command.
      if (-not [ZynoaNarratorKeyboard]::SetForegroundWindow($app.MainWindowHandle)) { throw 'ZYN-NAR-013: foreground recovery failed' }
      $Control.SetFocus()
      Start-Sleep -Milliseconds 500
      [void][ZynoaNarratorKeyboard]::GetWindowThreadProcessId([ZynoaNarratorKeyboard]::GetForegroundWindow(),[ref]$foregroundPid)
      if ($foregroundPid -ne $app.Id) { throw 'ZYN-NAR-017: foreground PID differs from native app' }
    }
    # Narrator+Tab reads the current item. Both default modifier keys are supported.
    Send-NarratorChord ([byte[]]@($modifier,0x09))
    Start-Sleep -Milliseconds 3000
    # Narrator+Ctrl+X copies the last actual spoken phrase on supporting OS versions.
    Send-NarratorChord ([byte[]]@($modifier,0x11,0x58))
    $changed=$false
    $length=0
    $knownLabels=@()
    $observedHash=''
    for ($i=0;$i -lt 16;$i++) {
      Start-Sleep -Milliseconds 350
      $after=[ZynoaNarratorKeyboard]::GetClipboardSequenceNumber()
      if ($after -eq $before) { continue }
      $changed=$true
      $candidate=Get-Clipboard -Raw
      if ($candidate -is [string] -and $candidate -ne $sentinel) {
        $length=$candidate.Length
        # No unrelated clipboard text leaves the disposable runner. A bounded
        # allowlist and digest distinguish genuine wrong-label announcements.
        $knownLabels=@()
        foreach ($known in @('Interface appearance','Search available commands and offline Help','Search views, help, settings','Command palette','Close command palette','Overview','Home and native startup status','Available commands and bundled Help results','Wiki mapping and link checker','Changelog','Known Issues','Search bundled notices','No matching notices','Changelog and release history','combo box','edit','list box','selected','scan mode','no item','no focus')) {
          if ($candidate.IndexOf($known,[StringComparison]::OrdinalIgnoreCase) -ge 0) { $knownLabels+=$known }
        }
        $sha=[System.Security.Cryptography.SHA256]::Create()
        try { $observedHash=[BitConverter]::ToString($sha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($candidate))).Replace('-','').ToLowerInvariant() }
        finally { $sha.Dispose() }
        $where=$candidate.IndexOf($ExpectedLabel,[StringComparison]::OrdinalIgnoreCase)
        if ($where -ge 0) {
          $start=[Math]::Max(0,$where-25)
          $len=[Math]::Min($candidate.Length-$start,$ExpectedLabel.Length+65)
          $excerpt=$candidate.Substring($start,$len).Replace([char]13,[char]32).Replace([char]10,[char]32)
          $script:workingNarratorModifier=$modifier
          $proof.attempts+= [ordered]@{stage=$Stage;modifier=$keyName;clipboard_changed=$true;
            clipboard_text_length=$length;expected_phrase_found=$true;foreground_pid=[int]$foregroundPid;system_focus_label_matches=$focusMatches;known_spoken_labels=$knownLabels;copied_phrase_sha256=$observedHash}
          return [ordered]@{stage=$Stage;label=$excerpt;clipboard_sequence_before=[int64]$before;
            clipboard_sequence_after=[int64]$after;actual_speech_clipboard_changed=$true}
        }
      }
    }
    # No arbitrary clipboard text is saved. Only booleans/length and PID are recorded.
    $proof.attempts+= [ordered]@{stage=$Stage;modifier=$keyName;clipboard_changed=$changed;
      clipboard_text_length=$length;expected_phrase_found=$false;foreground_pid=[int]$foregroundPid;system_focus_label_matches=$focusMatches;known_spoken_labels=$knownLabels;copied_phrase_sha256=$observedHash}
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
$script:workingNarratorModifier=[byte]0x2D
$proof=[ordered]@{schema_version=1;source_commit_sha=$SourceSha;github_run_id=[string]$env:GITHUB_RUN_ID;
 target='Real Microsoft Narrator speech copied from native Windows Tauri WebView2';
 binary_source_commit_sha=$binarySourceSha;diagnostic_artifact_reuse=($DiagnosticBinarySourceSha -ne '');
 app_executable_sha256=(Get-FileHash -LiteralPath $Executable -Algorithm SHA256).Hash.ToLowerInvariant();
 narrator_executable_sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant();
 narrator_signature_verified=$true;narrator_version=(Get-Item -LiteralPath $path).VersionInfo.FileVersion;
 app_pid=0;narrator_pid=0;native_uia_pid_match=$false;actual_keyboard_input_value='';actual_no_match_keyboard_input_value='';actual_no_match_result_verified=$false;
 os_version=[Environment]::OSVersion.Version.ToString();
 os_product_name=(Get-ItemProperty -LiteralPath 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion' -Name ProductName).ProductName;
 os_build_revision=[int](Get-ItemProperty -LiteralPath 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion' -Name UBR).UBR;
 palette_open_method='NotReached';palette_state=@();attempts=@();events=@();status='INCOMPLETE';no_user_data=$true;full_narrator_certified=$false;product_release_approved=$false}
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
  # Only before any speech has been captured: one bounded relaunch on a
  # fresh disposable host if the real WebView navigation is not ready.
  $prefsNav=$null
  for ($launch=0;$launch -lt 2;$launch++) {
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
    try {
      $prefsNav=Find-FocusableNativeControl $uia 'Preferences (Ctrl+2)' 45
      break
    } catch {
      if ($launch -ne 0 -or $_.Exception.Message -notlike 'ZYN-NAR-004:*') { throw }
      Write-Host 'ZYN-NAR-STARTUP-RETRY: real navigation unavailable; relaunch once before speech'
      Stop-Process -Id $app.Id -Force
      if (-not $app.WaitForExit(5000)) { throw 'ZYN-NAR-011: initial native process did not exit' }
      $app.Dispose()
      $app=$null
      Start-Sleep -Milliseconds 1500
    }
  }
  if ($null -eq $prefsNav) { throw 'ZYN-NAR-004: real Preferences navigation unavailable after bounded startup retry' }
  if ($M26Only) {
    $proof.target='Real Microsoft Narrator speech copied from native Windows Tauri WebView2 M26'
    function Assert-M26NarratorForeground {
      $app.Refresh()
      if ($app.HasExited -or [ZynoaNarratorKeyboard]::GetForegroundWindow() -ne $app.MainWindowHandle) {
        throw 'ZYN-M26-NAR-002: actual app foreground missing'
      }
      [void](Get-CurrentNativeRoot)
    }
    function Send-M26NarratorPassThrough([string]$Keys) {
      Assert-M26NarratorForeground
      Send-NarratorChord ([byte[]]@($script:workingNarratorModifier,0x33))
      Start-Sleep -Milliseconds 200
      [System.Windows.Forms.SendKeys]::SendWait($Keys)
      Start-Sleep -Milliseconds 850
      Assert-M26NarratorForeground
    }
    $nav=Find-FocusableNativeControl $uia 'Changelog'
    $proof.events+= (Read-ActualNarratorPhrase 'm26_entry' $nav 'Changelog')
    $nav=Find-FocusableNativeControl $uia 'Changelog'
    $nav.SetFocus()
    Start-Sleep -Milliseconds 250
    if (-not $nav.Current.HasKeyboardFocus) { throw 'ZYN-M26-NAR-003: native Changelog focus missing' }
    Send-M26NarratorPassThrough '{ENTER}'
    $sourceTab=Find-FocusableNativeControl $uia "What's New"
    if ($sourceTab.Current.ControlType -ne [System.Windows.Automation.ControlType]::TabItem -or
        -not $sourceTab.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern).Current.IsSelected) {
      throw 'ZYN-M26-NAR-004: native source tab selection missing'
    }
    $sourceTab.SetFocus()
    Start-Sleep -Milliseconds 250
    if (-not $sourceTab.Current.HasKeyboardFocus) { throw 'ZYN-M26-NAR-005: native source tab focus missing' }
    Send-M26NarratorPassThrough '{RIGHT}'
    $tab=Find-FocusableNativeControl $uia 'Known Issues'
    # Inactive roving tabs need not remain keyboard-focusable. Read their
    # actual SelectionItem state from the current root instead.
    $condition=[System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::NameProperty,"What's New")
    $previous=(Get-CurrentNativeRoot).FindFirst([System.Windows.Automation.TreeScope]::Descendants,$condition)
    if ($tab.Current.ControlType -ne [System.Windows.Automation.ControlType]::TabItem -or -not $tab.Current.HasKeyboardFocus -or
        -not $tab.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern).Current.IsSelected -or
        $null -eq $previous -or $previous.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern).Current.IsSelected) {
      throw 'ZYN-M26-NAR-006: actual native tab transition not verified'
    }
    $proof['actual_selected_tab']='Known Issues'
    $proof['actual_tab_keyboard_focus']=$true
    $proof['actual_previous_tab_deselected']=$true
    $proof.events+= (Read-ActualNarratorPhrase 'm26_tab' $tab 'Known Issues')
    $search=Find-FocusableNativeControl $uia 'Search bundled notices'
    $proof.events+= (Read-ActualNarratorPhrase 'm26_search' $search 'Search bundled notices')
    $search=Find-FocusableNativeControl $uia 'Search bundled notices'
    $search.SetFocus()
    Start-Sleep -Milliseconds 300
    if (-not $search.Current.HasKeyboardFocus -or $search.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value -cne '') {
      throw 'ZYN-M26-NAR-007: actual empty focused search missing'
    }
    $proof['actual_search_keyboard_focus']=$true
    Assert-M26NarratorForeground
    [System.Windows.Forms.SendKeys]::SendWait('zzznomatch')
    Start-Sleep -Milliseconds 1200
    $search=Find-FocusableNativeControl $uia 'Search bundled notices'
    $query=$search.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value
    if ($query -cne 'zzznomatch') { throw 'ZYN-M26-NAR-008: actual no-match query missing' }
    $empty=Find-FocusableNativeControl $uia 'No matching notices. Reset filters to view all.'
    $proof.actual_keyboard_input_value=$query
    $proof.actual_no_match_keyboard_input_value=$query
    $proof.actual_no_match_result_verified=$true
    $proof.events+= (Read-ActualNarratorPhrase 'm26_empty' $empty 'No matching notices')
    Send-M26NarratorPassThrough '{F1}'
    $heading=Find-FocusableNativeControl $uia 'Changelog and release history'
    $proof.events+= (Read-ActualNarratorPhrase 'm26_help' $heading 'Changelog and release history')
    $proof['actual_contextual_help_verified']=$true
    $app.Refresh();$narrator.Refresh()
    if ($app.HasExited -or $narrator.HasExited) { throw 'ZYN-M26-NAR-009: live native process ended' }
    $proof.status='CAPTURED'
    return
  }
  $prefsNav.SetFocus()
  [System.Windows.Forms.SendKeys]::SendWait('^{2}')
  Start-Sleep -Milliseconds 800
  try {
    $appearance=Find-FocusableNativeControl $uia 'Interface appearance' 6
  } catch {
    $prefsNav=Find-FocusableNativeControl $uia 'Preferences (Ctrl+2)' 8
    $invoke=$null
    if (-not $prefsNav.TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern,[ref]$invoke)) { throw }
    $invoke.Invoke()
    $appearance=Find-FocusableNativeControl $uia 'Interface appearance' 16
  }
  $proof.events+= (Read-ActualNarratorPhrase 'preferences' $appearance 'Interface appearance')
  # Re-use the Narrator modifier that actually produced the previous spoken phrase.
  # Keep app foreground, issue the documented pass-through, then send the real shortcut.
  if (-not [ZynoaNarratorKeyboard]::SetForegroundWindow($app.MainWindowHandle)) { throw 'ZYN-NAR-013: palette foreground failed' }
  $proof.palette_state+= [ordered]@{stage='before_shortcut';native=Get-PaletteNativeState}
  Send-NarratorChord ([byte[]]@($script:workingNarratorModifier,0x33))
  Start-Sleep -Milliseconds 200
  [System.Windows.Forms.SendKeys]::SendWait('^+p')
  Start-Sleep -Milliseconds 1000
  $proof.palette_state+= [ordered]@{stage='after_shortcut';native=Get-PaletteNativeState}
  $search=$null
  try {
    $search=Find-FocusableNativeControl $uia 'Search available commands and offline Help' 4
    $proof.palette_open_method='NarratorPassThroughCtrlShiftP'
  } catch {
    # Prefer the real named toolbar control, not an inaccessible stale root.
    $button=Find-ActualToolbarButton
    if ($null -ne $button) {
      $pattern=$null
      if ($button.TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern,[ref]$pattern)) {
        $pattern.Invoke()
        Start-Sleep -Milliseconds 1000
        $proof.palette_state+= [ordered]@{stage='after_native_invoke';native=Get-PaletteNativeState}
        try {
          $search=Find-FocusableNativeControl $uia 'Search available commands and offline Help' 4
          $proof.palette_open_method='NativeToolbarInvoke'
        } catch {}
      }
    }
    if ($null -eq $search) {
      # One bounded physical click from a fresh UIA named button, then require the real modal/input.
      $button=Find-ActualToolbarButton
      if (-not (Invoke-ActualToolbarClick $button)) { throw 'ZYN-NAR-018: actual command toolbar button could not open palette' }
      Start-Sleep -Milliseconds 1000
      $proof.palette_state+= [ordered]@{stage='after_native_click';native=Get-PaletteNativeState}
      $search=Find-FocusableNativeControl $uia 'Search available commands and offline Help' 8
      $proof.palette_open_method='NativeToolbarPhysicalClick'
    }
  }
  Write-Host ("ZYN-NAR-PALETTE method="+$proof.palette_open_method)
  # Exact prior speech receipt: both modifiers announced selected Overview,
  # not the input. This is expected aria-activedescendant behavior while results
  # exist. Use the genuine keyboard-operated empty-result state to verify the
  # input's own label without disabling its accessible result semantics.
  $search.SetFocus()
  [System.Windows.Forms.SendKeys]::SendWait('zynoa-no-match-7f6c')
  Start-Sleep -Milliseconds 850
  $search=Find-FocusableNativeControl $uia 'Search available commands and offline Help'
  $emptyValue=$search.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value
  if ($emptyValue -cne 'zynoa-no-match-7f6c') { throw 'ZYN-NAR-023: native no-result keyboard query mismatch' }
  $emptyRoot=Get-CurrentNativeRoot
  $emptyCondition=[System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::NameProperty,'No matching commands')
  $emptyResult=$emptyRoot.FindFirst([System.Windows.Automation.TreeScope]::Descendants,$emptyCondition)
  if ($null -eq $emptyResult) { throw 'ZYN-NAR-024: actual no-match result state absent' }
  $proof.actual_no_match_keyboard_input_value=$emptyValue
  $proof.actual_no_match_result_verified=$true
  $proof.events+= (Read-ActualNarratorPhrase 'palette' $search 'Search available commands and offline Help')
  # Narrator scan mode automatically stops in edit fields. Re-focus the
  # verified combobox after the spoken-label clipboard query, then type.
  $search=Find-FocusableNativeControl $uia 'Search available commands and offline Help'
  $search.SetFocus()
  Start-Sleep -Milliseconds 300
  # The field's actual ValuePattern is still checked below; do not set its
  # value directly or bypass the real keyboard journey.
  [System.Windows.Forms.SendKeys]::SendWait('^a')
  [System.Windows.Forms.SendKeys]::SendWait('M19-OPT-06')
  Start-Sleep -Milliseconds 1000
  $value=$search.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value
  if ($value -cne 'M19-OPT-06') { throw 'ZYN-NAR-014: native keyboard input missing' }
  $proof.actual_keyboard_input_value=$value
  # Independently require the real selected Help result's speech before
  # navigating. The fourth stage is not a replacement for input-label proof.
  $proof.events+= (Read-ActualNarratorPhrase 'palette_result' $search 'Wiki mapping and link checker')
  $search=Find-FocusableNativeControl $uia 'Search available commands and offline Help'
  $search.SetFocus()
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
  # Do not let a still-exiting screen reader or app contaminate the next
  # independent native journey. Only the disposable CI session is touched.
  $cleanupOk=$true
  if ($null -ne $app) {
    $app.Refresh()
    if (-not $app.HasExited) { Stop-Process -Id $app.Id -Force }
    if (-not $app.WaitForExit(5000)) { $cleanupOk=$false }
    $app.Dispose()
  }
  $readers=@(Get-Process -Name Narrator -ErrorAction SilentlyContinue)
  foreach ($reader in $readers) {
    try {
      if (-not $reader.HasExited) { Stop-Process -Id $reader.Id -Force -ErrorAction SilentlyContinue }
      if (-not $reader.WaitForExit(5000)) { $cleanupOk=$false }
    } finally { $reader.Dispose() }
  }
  if (Get-Process -Name Narrator -ErrorAction SilentlyContinue) { $cleanupOk=$false }
  Set-Clipboard -Value 'ZYNOA-NARRATOR-DISPOSABLE-CI-COMPLETE'
  if (-not $cleanupOk) { throw 'ZYN-NAR-025: disposable native process cleanup not verified' }
}
