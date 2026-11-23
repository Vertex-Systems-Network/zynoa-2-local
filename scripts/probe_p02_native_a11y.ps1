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
$issues = [System.Collections.Generic.List[string]]::new()
$clock = [System.Diagnostics.Stopwatch]::StartNew()
try {
  # Default shortcut map: probe BEFORE the existing screenshot script remaps keys.
  [System.Windows.Forms.SendKeys]::SendWait('^{2}')
  Start-Sleep -Milliseconds 350
  foreach ($label in @('Interface appearance', 'Navigation density')) {
    $control = Wait-NativeName -Label $label
    $ok = $null -ne $control -and $control.Current.IsEnabled -and
      $control.Current.IsKeyboardFocusable
    $results[$label] = [bool]$ok
    if (-not $ok) { $issues.Add('Required native accessible preference missing: ' + $label) }
  }

  [System.Windows.Forms.SendKeys]::SendWait('^+p')
  $dialog = Wait-NativeName -Label 'Command palette'
  $input = Wait-NativeName -Label 'Search available commands and offline Help'
  $results['modal_named'] = $null -ne $dialog
  $results['search_input_named'] = $null -ne $input -and
    $input.Current.IsEnabled -and $input.Current.IsKeyboardFocusable
  if (-not $results['modal_named']) { $issues.Add('Command palette modal missing accessible name') }
  if (-not $results['search_input_named']) { $issues.Add('Search input missing accessible name/focusability') }

  $searchFocused = $false
  for ($attempt = 0; $attempt -lt 16; $attempt++) {
    try {
      $focused = [System.Windows.Automation.AutomationElement]::FocusedElement
      if ($null -ne $focused -and
          $focused.Current.Name -eq 'Search available commands and offline Help') {
        $searchFocused = $true
        break
      }
    } catch [System.Windows.Automation.ElementNotAvailableException] {}
    Start-Sleep -Milliseconds 250
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
