# launch.ps1 -- start the run.cmd made by make_job.py OUTSIDE the Claude Code process tree
# (WMI Win32_Process.Create; the new cmd.exe's parent is WmiPrvSE.exe). ASCII only (PowerShell 5.1 reads
# BOM-less files as the ANSI code page).
# Usage (inline PowerShell is rejected by EL1, so always -File):
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File launch.ps1 -JobDir C:\gNNN\scripts\job1
# Writes <JobDir>\launch.json (ProcessId, CreationDateUtc, ParentProcessId, ParentName, ...) and prints the
# same JSON line. exit 0 = launched, 2 = usage/state error (nothing launched), 3 = WMI failure.
param(
    [Parameter(Mandatory = $true)][string]$JobDir
)
$ErrorActionPreference = 'Stop'
function Fail([int]$code, [string]$msg) { [Console]::Error.WriteLine("launch: $msg"); exit $code }

$JobDir = $JobDir.Replace('/', '\').TrimEnd('\')
$resolvedPath = Join-Path $JobDir 'job.resolved.json'
if (-not (Test-Path -LiteralPath $resolvedPath)) { Fail 2 "missing: $resolvedPath (run make_job.py first)" }
$job = Get-Content -LiteralPath $resolvedPath -Raw -Encoding UTF8 | ConvertFrom-Json
$launchJson = Join-Path $JobDir 'launch.json'
foreach ($p in @($launchJson, $job.rc, $job.pid)) {
    if (Test-Path -LiteralPath $p) { Fail 2 "already exists (previous run) -- use a new job_dir: $p" }
}
if (-not (Test-Path -LiteralPath $job.cmd)) { Fail 2 "missing: $($job.cmd)" }
if (-not (Test-Path -LiteralPath $job.cwd)) { New-Item -ItemType Directory -Path $job.cwd | Out-Null }

$cmdLine = 'C:\Windows\System32\cmd.exe /d /s /c ""' + $job.cmd + '""'
$startup = New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly -Property @{ ShowWindow = [uint16]0 }
try {
    $r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
        CommandLine = $cmdLine; CurrentDirectory = $job.cwd; ProcessStartupInformation = $startup }
} catch { Fail 3 ("Invoke-CimMethod failed: " + $_.Exception.Message) }
if ($r.ReturnValue -ne 0) { Fail 3 "Win32_Process.Create ReturnValue=$($r.ReturnValue)" }

$procId = [int]$r.ProcessId
$p = Get-CimInstance Win32_Process -Filter "ProcessId=$procId"
$parentName = $null; $creation = $null; $ppid = $null
if ($p) {
    $creation = $p.CreationDate.ToUniversalTime().ToString('o'); $ppid = [int]$p.ParentProcessId
    $pp = Get-CimInstance Win32_Process -Filter "ProcessId=$ppid"
    if ($pp) { $parentName = $pp.Name }
}
$info = [ordered]@{
    ProcessId = $procId; CreationDateUtc = $creation; ParentProcessId = $ppid; ParentName = $parentName
    CommandLine = $cmdLine; LauncherPid = $PID; LaunchedAtUtc = (Get-Date).ToUniversalTime().ToString('o')
}
$out = $info | ConvertTo-Json -Compress
[System.IO.File]::WriteAllText($launchJson, $out + "`n", (New-Object System.Text.UTF8Encoding $false))
Write-Output $out
exit 0
