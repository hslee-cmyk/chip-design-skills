# procs.ps1 -- list python/pytest processes as one JSON line (read only). ASCII only.
# Usage: powershell.exe -NoProfile -ExecutionPolicy Bypass -File procs.ps1
$ErrorActionPreference = 'Stop'
$ps = @(Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='python3.exe' OR Name='pythonw.exe' OR Name='pytest.exe'" |
    ForEach-Object { @{ pid = [int]$_.ProcessId; ppid = [int]$_.ParentProcessId; name = $_.Name;
                        created = $_.CreationDate.ToUniversalTime().ToString('o'); cmd = [string]$_.CommandLine } })
Write-Output (ConvertTo-Json -InputObject $ps -Compress -Depth 3)
exit 0
