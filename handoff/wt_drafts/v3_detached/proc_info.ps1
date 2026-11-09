# proc_info.ps1 -- liveness + ancestor chain of one PID as one JSON line (read only). ASCII only.
# Usage: powershell.exe -NoProfile -ExecutionPolicy Bypass -File proc_info.ps1 -ProcId 1234 [-CreationDateUtc <launch.json value>]
# Output: {"alive":bool,"same_process":bool|null,"name":..,"ancestors":[{"pid":..,"name":..}],"under_claude":bool}
# same_process: with -CreationDateUtc, guards against PID reuse (creation time must match).
param(
    [Parameter(Mandatory = $true)][int]$ProcId,
    [string]$CreationDateUtc = ''
)
$ErrorActionPreference = 'Stop'
$p = Get-CimInstance Win32_Process -Filter "ProcessId=$ProcId"
if (-not $p) {
    Write-Output (@{ alive = $false; same_process = $null; name = $null; ancestors = @(); under_claude = $false } | ConvertTo-Json -Compress)
    exit 0
}
$same = $null
if ($CreationDateUtc) {
    $same = ($p.CreationDate.ToUniversalTime().ToString('o') -eq $CreationDateUtc)
}
$anc = @(); $cur = $p; $seen = @{}
for ($i = 0; $i -lt 20; $i++) {
    $ppid = [int]$cur.ParentProcessId
    if ($ppid -le 0 -or $seen.ContainsKey($ppid)) { break }
    $seen[$ppid] = 1
    $pp = Get-CimInstance Win32_Process -Filter "ProcessId=$ppid"
    if (-not $pp) { $anc += @{ pid = $ppid; name = '<gone>' }; break }
    # parent created after child => PID was reused by an unrelated process; chain ends here
    if ($pp.CreationDate -gt $cur.CreationDate) { $anc += @{ pid = $ppid; name = '<reused>' }; break }
    $anc += @{ pid = $ppid; name = $pp.Name }
    $cur = $pp
}
$under = [bool]($anc | Where-Object { $_.name -like 'claude*' })
Write-Output (@{ alive = $true; same_process = $same; name = $p.Name; ancestors = $anc; under_claude = $under } | ConvertTo-Json -Compress -Depth 4)
exit 0
