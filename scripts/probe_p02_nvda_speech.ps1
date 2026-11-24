# P02 T10 live NVDA speech + native Tauri keyboard proof, no browser simulation.
param([Parameter(Mandatory=$true)][string]$Executable,
      [Parameter(Mandatory=$true)][string]$SourceSha,
      [Parameter(Mandatory=$true)][string]$OutputPath)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if ($SourceSha -cnotmatch '^[a-f0-9]{40}$') { throw 'ZYN-NVDA-001: SHA absent' }
$actual = (& git -C $env:GITHUB_WORKSPACE rev-parse HEAD).Trim().ToLowerInvariant()
if ($actual -cne $SourceSha) { throw 'ZYN-NVDA-002: head differs' }
if (-not (Test-Path -LiteralPath $Executable -PathType Leaf)) { throw 'ZYN-NVDA-003: native app missing' }
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$root = Join-Path $env:RUNNER_TEMP 'zynoa-nvda-t10'
New-Item -ItemType Directory -Force -Path $root | Out-Null
$installer = Join-Path $root 'nvda_2026.3.1.exe'
$portable = Join-Path $root 'portable'
$proofDir = Split-Path -Parent $OutputPath
New-Item -ItemType Directory -Force -Path $proofDir | Out-Null
$proofFile = Join-Path $root 'spoken-allowlisted.jsonl'
$stageFile = Join-Path $root 'active-stage.txt'
Set-Content -LiteralPath $stageFile -Value 'initial' -Encoding UTF8
$expectedHash = '6f80a5b0ca720a7d0d314b5be212f37388bbe81a1107ac3298c1821a1cd3f052'
Invoke-WebRequest -Uri 'https://download.nvaccess.org/releases/2026.3.1/nvda_2026.3.1.exe' -OutFile $installer -TimeoutSec 150
$actualHash = (Get-FileHash -LiteralPath $installer -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualHash -cne $expectedHash) { throw 'ZYN-NVDA-004: official installer hash mismatch' }
$setup = Start-Process -FilePath $installer -ArgumentList @('--minimal','--create-portable-silent',"--portable-path=$portable") -PassThru -Wait
if ($setup.ExitCode -ne 0 -or -not (Test-Path (Join-Path $portable 'nvda.exe'))) { throw 'ZYN-NVDA-005: portable NVDA creation failed' }
$profile = Join-Path $portable 'userConfig'
$pluginDir = Join-Path $profile 'scratchpad\globalPlugins'
New-Item -ItemType Directory -Force -Path $pluginDir | Out-Null
Copy-Item -LiteralPath (Join-Path $env:GITHUB_WORKSPACE 'scripts\nvda\zynoaAudit.py') -Destination (Join-Path $pluginDir 'zynoaAudit.py')
@'
[general]
showWelcomeDialogAtStartup = False
[development]
enableScratchpadDir = True
'@ | Set-Content -LiteralPath (Join-Path $profile 'nvda.ini') -Encoding UTF8
$env:ZYNOA_NVDA_SPEECH_PROOF = $proofFile
$env:ZYNOA_NVDA_STAGE_FILE = $stageFile
$nvda = $null
$app = $null
try {
  $nvda = Start-Process -FilePath (Join-Path $portable 'nvda.exe') -ArgumentList @('--minimal',"--config-path=$profile") -PassThru
  $loaded = $false
  for ($i=0; $i -lt 90; $i++) {
    Start-Sleep -Milliseconds 500
    if (Test-Path -LiteralPath $proofFile) {
      $loaded = (Get-Content -LiteralPath $proofFile -Raw).Contains('"plugin_loaded"')
      if ($loaded) { break }
    }
    $nvda.Refresh()
    if ($nvda.HasExited) { break }
  }
  if (-not $loaded) { throw 'ZYN-NVDA-006: real NVDA speech observer never loaded' }
  $app = Start-Process -FilePath $Executable -PassThru
  $ready = $false
  for ($i=0; $i -lt 90; $i++) {
    Start-Sleep -Milliseconds 400
    $app.Refresh()
    if ($app.HasExited) { throw 'ZYN-NVDA-007: native app exited prematurely' }
    if ($app.MainWindowHandle -ne [IntPtr]::Zero) {
      $uia = [System.Windows.Automation.AutomationElement]::FromHandle($app.MainWindowHandle)
      if ($null -ne $uia -and $uia.Current.ProcessId -eq $app.Id) {
        $ready = $true
        break
      }
    }
  }
  if (-not $ready) { throw 'ZYN-NVDA-008: native application unavailable in UIA' }
  Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class ZynoaNvdaFocus {
 [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
}
'@
  if (-not [ZynoaNvdaFocus]::SetForegroundWindow($app.MainWindowHandle)) {
    throw 'ZYN-NVDA-009: native app cannot become foreground'
  }
  Start-Sleep -Milliseconds 500
  Set-Content -LiteralPath $stageFile -Value 'preferences' -Encoding UTF8
  [System.Windows.Forms.SendKeys]::SendWait('^{2}')
  Start-Sleep -Milliseconds 900
  $appearanceMatches = $uia.FindAll(
    [System.Windows.Automation.TreeScope]::Descendants,
    [System.Windows.Automation.PropertyCondition]::new(
      [System.Windows.Automation.AutomationElement]::NameProperty, 'Interface appearance'))
  $appearance = $null
  for ($i=0; $i -lt $appearanceMatches.Count; $i++) {
    try {
      $candidate = $appearanceMatches.Item($i)
      if ($candidate.Current.IsKeyboardFocusable -and $candidate.Current.IsEnabled -and -not $candidate.Current.IsOffscreen) {
        $appearance = $candidate
        break
      }
    } catch [System.Windows.Automation.ElementNotAvailableException] {}
  }
  if ($null -eq $appearance) {
    throw 'ZYN-NVDA-013: no actual focusable Preferences selector found'
  }
  $appearance.SetFocus()
  Start-Sleep -Milliseconds 2300
  Set-Content -LiteralPath $stageFile -Value 'palette' -Encoding UTF8
  [System.Windows.Forms.SendKeys]::SendWait('^+p')
  Start-Sleep -Milliseconds 1200
  $input = $uia.FindFirst(
    [System.Windows.Automation.TreeScope]::Descendants,
    [System.Windows.Automation.PropertyCondition]::new(
      [System.Windows.Automation.AutomationElement]::NameProperty,
      'Search available commands and offline Help'))
  if ($null -eq $input) { throw 'ZYN-NVDA-010: real command search missing' }
  $input.SetFocus()
  Start-Sleep -Milliseconds 1600
  [System.Windows.Forms.SendKeys]::SendWait('M19-OPT-06')
  Start-Sleep -Milliseconds 1000
  $value = $input.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value
  if ($value -cne 'M19-OPT-06') { throw 'ZYN-NVDA-011: keyboard never entered native search' }
  Set-Content -LiteralPath $stageFile -Value 'help' -Encoding UTF8
  [System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
  Start-Sleep -Milliseconds 2700
  $app.Refresh(); $nvda.Refresh()
  if ($app.HasExited -or $nvda.HasExited) { throw 'ZYN-NVDA-012: app or NVDA died during journey' }
  $events = @((Get-Content -LiteralPath $proofFile -Encoding UTF8) | ForEach-Object { $_ | ConvertFrom-Json })
  $proof = [ordered]@{
    schema_version=1
    source_commit_sha=$SourceSha
    github_run_id=[string]$env:GITHUB_RUN_ID
    app_executable_sha256=(Get-FileHash -LiteralPath $Executable -Algorithm SHA256).Hash.ToLowerInvariant()
    official_nvda_installer_sha256=$actualHash
    nvda_version='2026.3.1'
    target='Real Windows Tauri WebView2 with live NVDA pre_synthSpeak'
    app_pid=[int]$app.Id
    nvda_pid=[int]$nvda.Id
    native_uia_pid_match=$true
    actual_keyboard_input_value=$value
    plugin_loaded=($events | Where-Object { $_.kind -eq 'plugin_loaded' }).Count -gt 0
    events=@($events | Where-Object { $_.kind -eq 'speech' })
    no_user_data=$true
    full_narrator_verified=$false
    performance_budget_approved=$false
  }
  $proof | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $OutputPath -Encoding UTF8
  Write-Output 'Live NVDA speech stream captured; validator will reject absent required announcements'
} finally {
  if ($null -ne $app) { $app.Refresh(); if (-not $app.HasExited) { Stop-Process -Id $app.Id -Force }; $app.Dispose() }
  if ($null -ne $nvda) { $nvda.Refresh(); if (-not $nvda.HasExited) { Stop-Process -Id $nvda.Id -Force }; $nvda.Dispose() }
}
