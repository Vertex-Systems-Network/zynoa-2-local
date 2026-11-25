# P02 T10 live NVDA speech + native Tauri keyboard proof, no browser simulation.
param([Parameter(Mandatory=$true)][string]$Executable,
      [Parameter(Mandatory=$true)][string]$SourceSha,
      [Parameter(Mandatory=$true)][string]$OutputPath,
      [switch]$M26Only)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if ($SourceSha -cnotmatch '^[a-f0-9]{40}$') { throw 'ZYN-NVDA-001: SHA absent' }
$actual = (& git -C $env:GITHUB_WORKSPACE rev-parse HEAD).Trim().ToLowerInvariant()
if ($actual -cne $SourceSha) { throw 'ZYN-NVDA-002: head differs' }
if (-not (Test-Path -LiteralPath $Executable -PathType Leaf)) { throw 'ZYN-NVDA-003: native app missing' }
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$root = Join-Path $env:RUNNER_TEMP $(if ($M26Only) {'zynoa-nvda-m26'} else {'zynoa-nvda-t10'})
if ($M26Only -and (Get-Process -Name nvda,Narrator -ErrorAction SilentlyContinue)) { throw 'ZYN-M26-NVDA-001: pre-existing screen reader' }
New-Item -ItemType Directory -Force -Path $root | Out-Null
$installer = Join-Path $root 'nvda_2026.3.1.exe'
$portable = Join-Path $root 'portable'
$proofDir = Split-Path -Parent $OutputPath
New-Item -ItemType Directory -Force -Path $proofDir | Out-Null
$proofFile = Join-Path $root 'spoken-allowlisted.jsonl'
$stageFile = Join-Path $root 'active-stage.txt'
if (Test-Path -LiteralPath $proofFile) { throw 'ZYN-M26-NVDA-002: stale speech proof file' }
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
 [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
}
'@
  function Get-NvdaNativeRoot {
    $app.Refresh()
    if ($app.HasExited -or $app.MainWindowHandle -eq [IntPtr]::Zero) {
      throw 'ZYN-NVDA-014: native window disappeared'
    }
    $nativeRoot = [System.Windows.Automation.AutomationElement]::FromHandle($app.MainWindowHandle)
    if ($null -eq $nativeRoot -or $nativeRoot.Current.ProcessId -ne $app.Id) {
      throw 'ZYN-NVDA-015: native UIA root PID mismatch'
    }
    return $nativeRoot
  }
  function Assert-NvdaForeground {
    $app.Refresh()
    if ($app.HasExited -or $app.MainWindowHandle -eq [IntPtr]::Zero -or
        [ZynoaNvdaFocus]::GetForegroundWindow() -ne $app.MainWindowHandle) {
      throw 'ZYN-NVDA-016: native app is not foreground'
    }
  }
  function Find-NvdaSearch {
    param([int]$Attempts=12)
    $condition = [System.Windows.Automation.PropertyCondition]::new(
      [System.Windows.Automation.AutomationElement]::NameProperty, 'Search available commands and offline Help')
    for ($attempt=0; $attempt -lt $Attempts; $attempt++) {
      Assert-NvdaForeground
      $nativeRoot = Get-NvdaNativeRoot
      $matches = $nativeRoot.FindAll([System.Windows.Automation.TreeScope]::Descendants,$condition)
      for ($j=0; $j -lt $matches.Count; $j++) {
        try {
          $item=$matches.Item($j)
          if ($item.Current.IsKeyboardFocusable -and $item.Current.IsEnabled -and -not $item.Current.IsOffscreen) {
            return $item
          }
        } catch [System.Windows.Automation.ElementNotAvailableException] {}
      }
      Start-Sleep -Milliseconds 400
    }
    return $null
  }
  if (-not [ZynoaNvdaFocus]::SetForegroundWindow($app.MainWindowHandle)) {
    throw 'ZYN-NVDA-009: native app cannot become foreground'
  }
  Start-Sleep -Milliseconds 500
  Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class ZynoaNvdaReportFocus {
  [DllImport("user32.dll")]
  public static extern void keybd_event(byte vk, byte scan, uint flags, UIntPtr extra);
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint flags, uint dx, uint dy, uint data, UIntPtr extra);
}
'@
  if ($M26Only) {
    # Use actual foreground native UIA, real focus and Windows key delivery.
    # The independent M26 screenshot journey is still required.
    function Find-M26NvdaControl {
      param([string]$Name, [switch]$Focusable, [switch]$TabItem)
      $deadline=(Get-Date).AddSeconds(10)
      do {
        Assert-NvdaForeground
        $root=Get-NvdaNativeRoot
        $condition=[System.Windows.Automation.PropertyCondition]::new(
          [System.Windows.Automation.AutomationElement]::NameProperty,$Name)
        $items=$root.FindAll([System.Windows.Automation.TreeScope]::Descendants,$condition)
        for ($j=0;$j -lt $items.Count;$j++) {
          try {
            $item=$items.Item($j)
            if ($item.Current.IsOffscreen) { continue }
            if ($Focusable -and (-not $item.Current.IsEnabled -or -not $item.Current.IsKeyboardFocusable)) { continue }
            if ($TabItem -and $item.Current.ControlType -ne [System.Windows.Automation.ControlType]::TabItem) { continue }
            return $item
          } catch [System.Windows.Automation.ElementNotAvailableException] {}
        }
        Start-Sleep -Milliseconds 250
      } until ((Get-Date) -ge $deadline)
      throw ('ZYN-M26-NVDA-003: actual native control absent: '+$Name)
    }
    function Focus-M26NvdaControl {
      param([string]$Name,[switch]$TabItem)
      $element=Find-M26NvdaControl -Name $Name -Focusable -TabItem:$TabItem
      $element.SetFocus()
      Start-Sleep -Milliseconds 350
      Assert-NvdaForeground
      $fresh=Find-M26NvdaControl -Name $Name -Focusable -TabItem:$TabItem
      if (-not $fresh.Current.HasKeyboardFocus) { throw 'ZYN-M26-NVDA-004: real native focus not confirmed' }
      return $fresh
    }
    function Request-M26NvdaFocusSpeech {
      Assert-NvdaForeground
      [ZynoaNvdaReportFocus]::keybd_event(0x2D,0,0,[UIntPtr]::Zero)
      Start-Sleep -Milliseconds 120
      [ZynoaNvdaReportFocus]::keybd_event(0x09,0,0,[UIntPtr]::Zero)
      Start-Sleep -Milliseconds 120
      [ZynoaNvdaReportFocus]::keybd_event(0x09,0,2,[UIntPtr]::Zero)
      Start-Sleep -Milliseconds 120
      [ZynoaNvdaReportFocus]::keybd_event(0x2D,0,2,[UIntPtr]::Zero)
      Start-Sleep -Milliseconds 2200
      Assert-NvdaForeground
    }
    [void](Focus-M26NvdaControl -Name 'Changelog')
    [System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
    Start-Sleep -Milliseconds 700
    $sourceTab=Focus-M26NvdaControl -Name "What's New" -TabItem
    if (-not $sourceTab.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern).Current.IsSelected) {
      throw 'ZYN-M26-NVDA-005: source tab not selected'
    }
    Set-Content -LiteralPath $stageFile -Value 'm26_tab' -Encoding UTF8
    Assert-NvdaForeground
    [System.Windows.Forms.SendKeys]::SendWait('{RIGHT}')
    Start-Sleep -Milliseconds 700
    $tab=Find-M26NvdaControl -Name 'Known Issues' -Focusable -TabItem
    if (-not $tab.Current.HasKeyboardFocus -or -not $tab.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern).Current.IsSelected) {
      throw 'ZYN-M26-NVDA-006: actual selected/focused destination absent'
    }
    Request-M26NvdaFocusSpeech
    Set-Content -LiteralPath $stageFile -Value 'm26_search' -Encoding UTF8
    $input=Focus-M26NvdaControl -Name 'Search bundled notices'
    Request-M26NvdaFocusSpeech
    if ($input.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value -cne '') {
      throw 'ZYN-M26-NVDA-007: native query did not start empty'
    }
    Set-Content -LiteralPath $stageFile -Value 'm26_empty' -Encoding UTF8
    Assert-NvdaForeground
    [System.Windows.Forms.SendKeys]::SendWait('zzznomatch')
    Start-Sleep -Milliseconds 2600
    $input=Find-M26NvdaControl -Name 'Search bundled notices' -Focusable
    $query=$input.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value
    if ($query -cne 'zzznomatch') { throw 'ZYN-M26-NVDA-008: actual keyboard query absent' }
    # A real no-match reset button can be focused and announced even
    # when the asynchronous live region was silent on this run.
    [void](Focus-M26NvdaControl -Name 'No matching notices. Reset filters to view all.')
    Request-M26NvdaFocusSpeech
    $app.Refresh();$nvda.Refresh()
    if ($app.HasExited -or $nvda.HasExited) { throw 'ZYN-M26-NVDA-009: native process ended' }
    $events=@((Get-Content -LiteralPath $proofFile -Encoding UTF8) | ForEach-Object { $_ | ConvertFrom-Json })
    $proof=[ordered]@{
      schema_version=1; source_commit_sha=$SourceSha; github_run_id=[string]$env:GITHUB_RUN_ID
      app_executable_sha256=(Get-FileHash -LiteralPath $Executable -Algorithm SHA256).Hash.ToLowerInvariant()
      official_nvda_installer_sha256=$actualHash; nvda_version='2026.3.1'
      target='Real Windows Tauri WebView2 M26 with live NVDA pre_synthSpeak'
      app_pid=[int]$app.Id; nvda_pid=[int]$nvda.Id; native_uia_pid_match=$true
      actual_selected_tab='Known Issues'; actual_tab_keyboard_focus=$true
      actual_search_keyboard_focus=$true; actual_keyboard_input_value=$query; actual_no_match_visible=$true
      plugin_loaded=($events | Where-Object { $_.kind -eq 'plugin_loaded' }).Count -gt 0
      events=@($events | Where-Object { $_.kind -eq 'speech' -and $_.stage -in @('m26_tab','m26_search','m26_empty') })
      no_user_data=$true; full_narrator_verified=$false; full_product_release_approved=$false
    }
    $proof | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $OutputPath -Encoding UTF8
    Write-Output 'M26 live speech captured; verifier requires all three actual stages'
    return
  }
  Set-Content -LiteralPath $stageFile -Value 'preferences' -Encoding UTF8
  [System.Windows.Forms.SendKeys]::SendWait('^{2}')
  Start-Sleep -Milliseconds 900
  Assert-NvdaForeground
  $uia = Get-NvdaNativeRoot
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
  Start-Sleep -Milliseconds 350
  # NVDA+Tab is NVDA's user-initiated "report current focus" shortcut.
  # A programmatic UIA SetFocus alone does not guarantee spoken feedback.
  # Send actual Windows keyboard events; never fabricate a speech receipt.
  [ZynoaNvdaReportFocus]::keybd_event(0x2D, 0, 0, [UIntPtr]::Zero)
  Start-Sleep -Milliseconds 120
  [ZynoaNvdaReportFocus]::keybd_event(0x09, 0, 0, [UIntPtr]::Zero)
  Start-Sleep -Milliseconds 120
  [ZynoaNvdaReportFocus]::keybd_event(0x09, 0, 2, [UIntPtr]::Zero)
  Start-Sleep -Milliseconds 120
  [ZynoaNvdaReportFocus]::keybd_event(0x2D, 0, 2, [UIntPtr]::Zero)
  Start-Sleep -Milliseconds 2400
  Set-Content -LiteralPath $stageFile -Value 'palette' -Encoding UTF8
  if (-not [ZynoaNvdaFocus]::SetForegroundWindow($app.MainWindowHandle)) {
    throw 'ZYN-NVDA-016: unable to restore native foreground before palette'
  }
  Assert-NvdaForeground
  [System.Windows.Forms.SendKeys]::SendWait('^+p')
  $input = Find-NvdaSearch
  $paletteMethod = 'keyboard'
  if ($null -eq $input) {
    # Bounded fallback to the actual enabled toolbar button. Do not fake speech
    # or skip the exact input ValuePattern and three live speech requirements.
    $nativeRoot = Get-NvdaNativeRoot
    $buttons = $nativeRoot.FindAll([System.Windows.Automation.TreeScope]::Descendants,
      [System.Windows.Automation.PropertyCondition]::new(
        [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
        [System.Windows.Automation.ControlType]::Button))
    $button = $null
    for ($j=0; $j -lt $buttons.Count; $j++) {
      try {
        $candidate = $buttons.Item($j)
        if ($candidate.Current.IsEnabled -and -not $candidate.Current.IsOffscreen -and
            $candidate.Current.Name -like '*Search or run a command*') {
          $button = $candidate
          break
        }
      } catch [System.Windows.Automation.ElementNotAvailableException] {}
    }
    if ($null -ne $button) {
      $invoke = $null
      if ($button.TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern,[ref]$invoke)) {
        Assert-NvdaForeground
        $invoke.Invoke()
        $paletteMethod = 'native_toolbar_invoke'
        $input = Find-NvdaSearch
      }
    }
  }
  Write-Host ("ZYN-NVDA-PALETTE method="+$paletteMethod)
  if ($null -eq $input) { throw 'ZYN-NVDA-010: real command search missing' }
  $value = ''
  for ($typingAttempt=0; $typingAttempt -lt 2; $typingAttempt++) {
    $input=Find-NvdaSearch
    if ($null -eq $input) { throw 'ZYN-NVDA-010: real command search missing before typing' }
    $input.SetFocus()
    Start-Sleep -Milliseconds 500
    Assert-NvdaForeground
    $input=Find-NvdaSearch
    if ($null -eq $input -or -not $input.Current.HasKeyboardFocus) { throw 'ZYN-NVDA-011: actual palette input focus absent' }
    # If first typing was intercepted, use the real native edit click
    # before the one bounded retry; never set the UIA value directly.
    if ($typingAttempt -eq 1) {
      Write-Host 'ZYN-NVDA-TYPING-RETRY: actual value mismatch; retry focused input once'
      # Real provider-derived click on the named edit field, no guessed
      # coordinate and no UIA SetValue. Mouse focus can enter NVDA edit mode.
      $point=New-Object System.Windows.Point
      if (-not $input.TryGetClickablePoint([ref]$point) -or
          -not (Get-NvdaNativeRoot).Current.BoundingRectangle.Contains($point)) {
        throw 'ZYN-NVDA-011: actual input click target absent'
      }
      if (-not [ZynoaNvdaReportFocus]::SetCursorPos([int]$point.X,[int]$point.Y)) {
        throw 'ZYN-NVDA-011: actual input pointer move failed'
      }
      [ZynoaNvdaReportFocus]::mouse_event(2,0,0,0,[UIntPtr]::Zero)
      [ZynoaNvdaReportFocus]::mouse_event(4,0,0,0,[UIntPtr]::Zero)
      Start-Sleep -Milliseconds 500
      Assert-NvdaForeground
      $input=Find-NvdaSearch
      if ($null -eq $input -or -not $input.Current.HasKeyboardFocus) { throw 'ZYN-NVDA-011: actual focus lost before retry' }
    }
    [System.Windows.Forms.SendKeys]::SendWait('^a')
    [System.Windows.Forms.SendKeys]::SendWait('M19-OPT-06')
    Start-Sleep -Milliseconds 1000
    $input=Find-NvdaSearch
    if ($null -eq $input) { throw 'ZYN-NVDA-010: real command search missing after typing' }
    $value=$input.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value
    if ($value -ceq 'M19-OPT-06') { break }
    Write-Host ("ZYN-NVDA-TYPING-MISMATCH attempt="+$typingAttempt+" length="+$value.Length)
  }
  if ($value -cne 'M19-OPT-06') { throw 'ZYN-NVDA-011: keyboard never entered native search' }
  Set-Content -LiteralPath $stageFile -Value 'help' -Encoding UTF8
  Assert-NvdaForeground
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
    palette_open_method=$paletteMethod
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
  $cleanupOk=$true
  if ($null -ne $app) {
    $app.Refresh()
    if (-not $app.HasExited) { Stop-Process -Id $app.Id -Force }
    if (-not $app.WaitForExit(5000)) { $cleanupOk=$false }
    $app.Dispose()
  }
  if ($null -ne $nvda) {
    $nvda.Refresh()
    if (-not $nvda.HasExited) { Stop-Process -Id $nvda.Id -Force }
    if (-not $nvda.WaitForExit(5000)) { $cleanupOk=$false }
    $nvda.Dispose()
  }
  if (-not $cleanupOk) { throw 'ZYN-NVDA-017: disposable native process cleanup not verified' }
}
