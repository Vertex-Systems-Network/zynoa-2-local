# P02 native UI Automation probe: actual Tauri WebView2 HWND, no browser mocks.
# This is scoped keyboard/name evidence, NOT manual screen-reader certification.
param(
  [Parameter(Mandatory=$true)][int]$TargetPid,
  [Parameter(Mandatory=$true)][string]$OutputPath,
  [Parameter(Mandatory=$true)][string]$SourceSha
)
$ErrorActionPreference = 'Stop'
if ($SourceSha -cnotmatch '^[a-f0-9]{40}$') { throw 'ZYN-A11Y-001: invalid source SHA' }

Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class ZynoaA11yForeground {
  [DllImport("user32.dll")]
  public static extern bool SetForegroundWindow(IntPtr hwnd);
}
'@
$process = Get-Process -Id $TargetPid -ErrorAction Stop
$process.Refresh()
if ($process.HasExited -or $process.MainWindowHandle -eq [IntPtr]::Zero) {
  throw 'ZYN-A11Y-002: actual native window is not available'
}
if (-not [ZynoaA11yForeground]::SetForegroundWindow($process.MainWindowHandle)) {
  throw 'ZYN-A11Y-003: unable to focus native Tauri window'
}
$root = [System.Windows.Automation.AutomationElement]::FromHandle($process.MainWindowHandle)
if ($null -eq $root -or $root.Current.ProcessId -ne $TargetPid) {
  throw 'ZYN-A11Y-004: UI Automation window PID mismatch'
}
function Find-NativeName {
  param([Parameter(Mandatory=$true)][string]$Label)
  $predicate = [System.Windows.Automation.PropertyCondition]::new(
    [System.Windows.Automation.AutomationElement]::NameProperty, $Label)
  $matches = $root.FindAll([System.Windows.Automation.TreeScope]::Descendants, $predicate)
  $visibleCandidate = $null
  for ($index = 0; $index -lt $matches.Count; $index++) {
    try {
      $item = $matches.Item($index)
      if ($item.Current.IsOffscreen) { continue }
      # A named static label and the real native control can share the same
      # UIA Name. Prefer a keyboard-focusable control over a text node.
      if ($item.Current.IsKeyboardFocusable) { return $item }
      if ($null -eq $visibleCandidate) { $visibleCandidate = $item }
    } catch [System.Windows.Automation.ElementNotAvailableException] {}
  }
  return $visibleCandidate
}
function Wait-NativeName {
  param([Parameter(Mandatory=$true)][string]$Label, [int]$MaxAttempts=20)
  for ($attempt = 0; $attempt -lt $MaxAttempts; $attempt++) {
    $item = Find-NativeName -Label $Label
    if ($null -ne $item) { return $item }
    Start-Sleep -Milliseconds 250
  }
  return $null
}
function Read-NativeTextInputValue {
  param([Parameter(Mandatory=$true)]$Control)
  # WebView2 may report the active ARIA list option as FocusedElement even
  # while the HTML combobox itself is receiving keystrokes. Read the *input*
  # provider's actual ValuePattern: focus labels alone cannot pass this probe.
  try {
    $valuePattern = $Control.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
    if ($null -ne $valuePattern) {
      return [string]$valuePattern.Current.Value
    }
  } catch [System.InvalidOperationException] {
    return $null
  } catch [System.Windows.Automation.ElementNotAvailableException] {
    return $null
  }
  return $null
}
function Find-NativeVisibleNameFragment {
  param([Parameter(Mandatory=$true)][string]$Fragment)
  $all = $root.FindAll([System.Windows.Automation.TreeScope]::Descendants,
                       [System.Windows.Automation.Condition]::TrueCondition)
  for ($index=0; $index -lt $all.Count; $index++) {
    try {
      $element = $all.Item($index)
      if ($element.Current.IsOffscreen) { continue }
      if ($element.Current.Name.Contains($Fragment)) { return $element }
    } catch [System.Windows.Automation.ElementNotAvailableException] {}
  }
  return $null
}
$results = [ordered]@{}
$diagnostics = [ordered]@{}
$issues = [System.Collections.Generic.List[string]]::new()
$clock = [System.Diagnostics.Stopwatch]::StartNew()
try {
  # Default shortcut map: probe BEFORE the existing screenshot script remaps keys.
  [System.Windows.Forms.SendKeys]::SendWait('^{2}')
  Start-Sleep -Milliseconds 350
  $diagnostics['settings_specific_disabled_control_visible'] = $null -ne (Find-NativeName -Label 'Choose folder')
  foreach ($label in @('Interface appearance', 'Navigation density')) {
    $control = Wait-NativeName -Label $label
    $present = $null -ne $control
    $enabled = if ($present) { [bool]$control.Current.IsEnabled } else { $false }
    $focusable = if ($present) { [bool]$control.Current.IsKeyboardFocusable } else { $false }
    $diagnostics[$label] = [ordered]@{
      present = $present
      enabled = $enabled
      keyboard_focusable = $focusable
    }
    $ok = $present -and $enabled -and $focusable
    $results[$label] = [bool]$ok
    if (-not $ok) { $issues.Add('Required native accessible preference missing: ' + $label) }
  }

  [System.Windows.Forms.SendKeys]::SendWait('^+p')
  $dialog = Wait-NativeName -Label 'Command palette'
  $searchControl = Wait-NativeName -Label 'Search available commands and offline Help'
  $results['modal_named'] = $null -ne $dialog
  $results['search_input_named'] = $null -ne $searchControl -and
    $searchControl.Current.IsEnabled -and $searchControl.Current.IsKeyboardFocusable
  $diagnostics['search_control_accessibility'] = [ordered]@{
    present = $null -ne $searchControl
    focusable = if ($null -ne $searchControl) { [bool]$searchControl.Current.IsKeyboardFocusable } else { $false }
    enabled = if ($null -ne $searchControl) { [bool]$searchControl.Current.IsEnabled } else { $false }
  }
  if (-not $results['modal_named']) { $issues.Add('Command palette modal missing accessible name') }
  if (-not $results['search_input_named']) { $issues.Add('Search input missing accessible name/focusability') }

  # Probe real keyboard INPUT, not merely UIA's current aria-activedescendant:
  # the latter can legitimately be a ListItem with OS-reported keyboard focus.
  $focusObservation = 'none'
  try {
    $focused = [System.Windows.Automation.AutomationElement]::FocusedElement
    if ($null -ne $focused) {
      if ($focused.Current.ControlType -eq [System.Windows.Automation.ControlType]::ListItem) {
        $focusObservation = 'aria_active_descendant_list_item'
      } elseif ($focused.Current.Name -eq 'Search available commands and offline Help') {
        $focusObservation = 'named_search_input'
      } else {
        $focusObservation = 'other_provider_element'
      }
    }
  } catch [System.Windows.Automation.ElementNotAvailableException] {}

  $probeValue = 'M19-OPT-06'  # fixed allowlisted local ID, not private user input
  [System.Windows.Forms.SendKeys]::SendWait($probeValue)
  $confirmedValue = $null
  for ($attempt = 0; $attempt -lt 20; $attempt++) {
    if ($null -ne $searchControl) {
      $confirmedValue = Read-NativeTextInputValue -Control $searchControl
    }
    if ($confirmedValue -ceq $probeValue) { break }
    Start-Sleep -Milliseconds 250
  }
  $typedInExactInput = $confirmedValue -ceq $probeValue
  $diagnostics['search_focus'] = [ordered]@{
    provider_focus_kind = $focusObservation
    method = 'real_keyboard_text_and_input_ValuePattern'
    exact_local_probe_id = $probeValue
    query_reflected_by_input_provider = $typedInExactInput
  }
  $results['keyboard_focus_enters_modal_search'] = [bool]$typedInExactInput
  if (-not $typedInExactInput) {
    $issues.Add('Keyboard text did not reach the actual named command search input')
  }

  $optionVisible = $false
  if ($typedInExactInput) {
    for ($attempt = 0; $attempt -lt 20; $attempt++) {
      $optionVisible = $null -ne (Find-NativeVisibleNameFragment -Fragment 'Wiki mapping and link checker')
      if ($optionVisible) { break }
      Start-Sleep -Milliseconds 250
    }
  }
  $results['keyboard_query_filters_to_exact_option'] = [bool]$optionVisible
  if (-not $optionVisible) {
    $issues.Add('Typed option ID did not expose matching local Help result')
  }

  $detailVisible = $false
  if ($optionVisible) {
    [System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
    for ($attempt = 0; $attempt -lt 24; $attempt++) {
      $paletteGone = $null -eq (Find-NativeName -Label 'Command palette')
      $optionHeading = Find-NativeVisibleNameFragment -Fragment 'Wiki mapping and link checker'
      if ($paletteGone -and $null -ne $optionHeading) {
        $detailVisible = $true
        break
      }
      Start-Sleep -Milliseconds 250
    }
  }
  $results['enter_opens_exact_option_help'] = [bool]$detailVisible
  if (-not $detailVisible) {
    $issues.Add('Enter did not open the exact bundled Help option detail')
  }

  # A separate reopened dialog must still dismiss with Escape; this tests the
  # modal on its return path after navigation, not only on initial appearance.
  [System.Windows.Forms.SendKeys]::SendWait('^+p')
  $reopened = $null -ne (Wait-NativeName -Label 'Command palette')
  $results['modal_reopens_after_help_navigation'] = [bool]$reopened
  if (-not $reopened) {
    $issues.Add('Command modal did not reopen after keyboard Help navigation')
  }
  if ($reopened) {
    [System.Windows.Forms.SendKeys]::SendWait('{ESC}')
  }
  $modalDismissed = $false
  for ($attempt = 0; $attempt -lt 16; $attempt++) {
    if ($null -eq (Find-NativeName -Label 'Search available commands and offline Help')) {
      $modalDismissed = $true
      break
    }
    Start-Sleep -Milliseconds 250
  }
  $results['escape_dismisses_modal'] = $modalDismissed
  if (-not $modalDismissed) { $issues.Add('Escape did not close reopened native command dialog') }
} finally {
  # Restore the default Overview navigation before the existing screenshot suite.
  [System.Windows.Forms.SendKeys]::SendWait('{ESC}')
  [System.Windows.Forms.SendKeys]::SendWait('^{1}')
  Start-Sleep -Milliseconds 350
  $clock.Stop()
}
$proof = [ordered]@{
  schema_version = 1
  module = 'M02'
  source_commit_sha = $SourceSha
  target = 'Real Windows Tauri WebView2 UI Automation HWND'
  native_pid_matched = $true
  scope = 'Scoped accessible-name, keyboard focus and dialog dismissal probe'
  results = $results
  diagnostics = $diagnostics
  issues = @($issues)
  duration_ms = [int64]$clock.ElapsedMilliseconds
  full_screen_reader_verified = $false
  all_option_controls_verified = $false
  final_screenshot_manifest_verified = $false
  no_user_data = $true
  status = if ($issues.Count -eq 0) { 'SCOPED_NATIVE_UIA_PASS' } else { 'SCOPED_NATIVE_UIA_FAILED' }
}
$parent = Split-Path -Parent $OutputPath
New-Item -Path $parent -ItemType Directory -Force | Out-Null
$proof | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $OutputPath -Encoding utf8
Write-Output ('P02 Windows native UIA: ' + $proof.status)
if ($issues.Count -gt 0) {
  throw ('ZYN-A11Y-005: ' + ($issues -join '; '))
}
