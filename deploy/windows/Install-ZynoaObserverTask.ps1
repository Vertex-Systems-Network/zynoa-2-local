# Windows-only P00 observer task preview/optional registration.
# This does NOT run an autonomous coding model or grant GitHub write access.
# Current-user, least-privilege, AT LOGON only; not a true 24/7 service.
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [Parameter(Mandatory = $true)][string] $RepoRoot,
    [Parameter(Mandatory = $true)][string] $HostRoot,
    [string] $PythonExe = "python.exe",
    [switch] $Install
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
if (-not $IsWindows -and $PSVersionTable.PSVersion.Major -ge 6) {
    throw "Windows Task Scheduler is required"
}
$repo = (Resolve-Path -LiteralPath $RepoRoot -ErrorAction Stop).ProviderPath
$hostDir = (Resolve-Path -LiteralPath $HostRoot -ErrorAction Stop).ProviderPath
if (-not (Test-Path -LiteralPath (Join-Path $repo "docs/state/PHASE.json") -PathType Leaf)) {
    throw "Trusted Zynoa source state is missing"
}
if ($repo.Contains('"') -or $hostDir.Contains('"')) {
    throw "Ambiguous path quoting is prohibited"
}
$command = Get-Command -Name $PythonExe -CommandType Application -ErrorAction Stop
$python = $command.Source
if (-not $python -or $python.Contains('"')) {
    throw "Invalid Python executable"
}
& $python -m tools.host_bootstrap --repo-root $repo --host-root $hostDir inspect
if ($LASTEXITCODE -ne 0) { throw "Host storage integrity or phase check failed" }
$user = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
if ([string]::IsNullOrWhiteSpace($user)) {
    throw "Current Windows user identity missing"
}
$taskName = "Zynoa-P00-ReadOnlyObserver"
$phaseFile = Join-Path $repo "docs/state/PHASE.json"
$dbFile = Join-Path $hostDir "state/controller.db"
$arguments = '-m tools.phase_worker --repo Vertex-Systems-Network/zynoa-2-local --state "' +
    $phaseFile + '" --db "' + $dbFile + '" --interval 30'
$action = New-ScheduledTaskAction -Execute $python -Argument $arguments -WorkingDirectory $repo
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $user
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 2) -ExecutionTimeLimit (New-TimeSpan -Seconds 0)
if (-not $Install) {
    [pscustomobject]@{
        status = "PREVIEW_ONLY"
        task = $taskName
        installation_performed = $false
        autostart_mode = "AT_LOGON_CURRENT_USER"
        github_writes = 0
        model_execution = $false
        works_after_user_logoff = $false
    } | ConvertTo-Json -Compress
    return
}
if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    throw "Existing task requires independent operator reconciliation"
}
if ($PSCmdlet.ShouldProcess($taskName, "Register current-user read-only observer at logon")) {
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -ErrorAction Stop | Out-Null
    [pscustomobject]@{
        status = "REGISTERED_AT_LOGON"
        task = $taskName
        installation_performed = $true
        github_writes = 0
        model_execution = $false
        works_after_user_logoff = $false
    } | ConvertTo-Json -Compress
}
