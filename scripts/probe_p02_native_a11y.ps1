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
  for ($index = 0; $index -lt $matches.Count; $index++) {
    try {
      $item = $matches.Item($index)
      if (-not $item.Current.IsOffscreen) { return $item }
    } catch [System.Windows.Automation.ElementNotAvailableException] {}
  }
  return $null
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

  $searchFocused = $false
  $focusMethod = 'unverified'
  $observedFocusKind = 'none'
  for ($attempt = 0; $attempt -lt 16; $attempt++) {
    try {
      if ($null -ne $searchControl -and $searchControl.Current.HasKeyboardFocus) {
        $searchFocused = $true
        $focusMethod = 'native_control_has_keyboard_focus'
        break
      }
      $focused = [System.Windows.Automation.AutomationElement]::FocusedElement
      if ($null -ne $focused) {
        if ($focused.Current.Name -eq 'Search available commands and offline Help') {
          $searchFocused = $true
          $focusMethod = 'focused_element_exact_accessible_name'
          break
        } elseif ($focused.Current.Name -eq 'Command palette') {
          $observedFocusKind = 'dialog'
        } elseif ($focused.Current.Name -ne '') {
          $observedFocusKind = 'other_named_element'
        } else {
          $observedFocusKind = 'unnamed_element'
        }
      }
    } catch [System.Windows.Automation.ElementNotAvailableException] {}
    Start-Sleep -Milliseconds 250
  }
  $diagnostics['search_focus'] = [ordered]@{
    method = $focusMethod
    last_focus_kind = $observedFocusKind
  }
  $results['keyboard_focus_enters_modal_search'] = $searchFocused
  if (-not $searchFocused) { $issues.Add('Native keyboard focus did not reach command search') }

  [System.Windows.Forms.SendKeys]::SendWait('{ESC}')
  $modalDismissed = $false
  for ($attempt = 0; $attempt -lt 16; $attempt++) {
    if ($null -eq (Find-NativeName -Label 'Search available commands and offline Help')) {
      $modalDismissed = $true
      break
    }
    Start-Sleep -Milliseconds 250
  }
  $results['escape_dismisses_modal'] = $modalDismissed
  if (-not $modalDismissed) { $issues.Add('Escape did not close native command dialog') }
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
