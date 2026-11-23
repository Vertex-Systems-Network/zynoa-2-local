# P02 actual native Windows three-launch observational timings; not an approved budget.
param(
  [Parameter(Mandatory=$true)][string]$Executable,
  [Parameter(Mandatory=$true)][string]$SourceSha,
  [Parameter(Mandatory=$true)][string]$OutputPath
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if ($SourceSha -cnotmatch '^[a-f0-9]{40}$') { throw 'ZYN-PERF-001: invalid SHA' }
if (-not $env:GITHUB_WORKSPACE -or -not $env:GITHUB_RUN_ID) { throw 'ZYN-PERF-002: CI environment missing' }
if (-not (Test-Path -LiteralPath $Executable -PathType Leaf)) { throw 'ZYN-PERF-003: native binary missing' }
$actual = (& git -C $env:GITHUB_WORKSPACE rev-parse HEAD).Trim().ToLowerInvariant()
if ($actual -cne $SourceSha) { throw 'ZYN-PERF-004: checked-out SHA mismatch' }
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class ZynoaPerfWin32 {
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hwnd);
}
'@
$exeSha = (Get-FileHash -LiteralPath $Executable -Algorithm SHA256).Hash.ToLowerInvariant()
$samples = [System.Collections.Generic.List[object]]::new()
for ($index=1; $index -le 3; $index++) {
  $proc = $null
  $timer = [System.Diagnostics.Stopwatch]::StartNew()
  try {
    $proc = Start-Process -FilePath $Executable -PassThru
    $ready = $false
    $deadline = (Get-Date).AddSeconds(60)
    do {
      Start-Sleep -Milliseconds 125
      $proc.Refresh()
      if ($proc.HasExited) { throw 'ZYN-PERF-005: process exited before real window appeared' }
      $hwnd = $proc.MainWindowHandle
      if ($hwnd -ne [IntPtr]::Zero -and [ZynoaPerfWin32]::IsWindowVisible($hwnd)) {
        try {
          $element = [System.Windows.Automation.AutomationElement]::FromHandle($hwnd)
          if ($null -ne $element -and $element.Current.ProcessId -eq $proc.Id -and -not $element.Current.IsOffscreen) {
            $ready = $true
            break
          }
        } catch [System.Windows.Automation.ElementNotAvailableException] {}
      }
    } until ((Get-Date) -ge $deadline)
    $timer.Stop()
    if (-not $ready) { throw 'ZYN-PERF-006: no visible same-PID UIA window in 60 seconds' }
    $samples.Add([ordered]@{
      sample_index = $index
      native_process_id = [int]$proc.Id
      window_first_visible_ms = [int64]$timer.ElapsedMilliseconds
      real_native_visible_hwnd = $true
      native_uia_window_pid_matches = $true
      process_alive_when_sampled = $true
    })
  } finally {
    if ($null -ne $proc) {
      $proc.Refresh()
      if (-not $proc.HasExited) {
        Stop-Process -Id $proc.Id -Force -ErrorAction Stop
        Start-Sleep -Milliseconds 300
      }
      $proc.Dispose()
    }
  }
}
$receipt = [ordered]@{
  schema_version = 1
  source_commit_sha = $SourceSha
  github_run_id = [string]$env:GITHUB_RUN_ID
  target = 'Real GitHub Actions Windows Tauri native main-window UIA'
  executable_sha256 = $exeSha
  measurement = 'three sequential warm process launches, same executable, visible same-PID UIA HWND'
  samples = @($samples.ToArray())
  sample_count = 3
  native_test_environment = 'GitHub-hosted Windows runner'
  full_screen_reader_verified = $false
  performance_budget_approved = $false
  no_user_data = $true
}
$dir = Split-Path -Path $OutputPath -Parent
if ($dir) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
$receipt | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath $OutputPath -Encoding utf8
Write-Output 'P02 real sequential native window sample receipt written: budget remains unapproved'
