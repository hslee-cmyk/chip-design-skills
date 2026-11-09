# run_flow.ps1 -- generate GDS, run DRC and LVS for two_stage_ota (KLayout batch). Usage: run_flow.ps1 <tag> [gen|drc|lvs|all]
# klayout_app.exe is a GUI-subsystem binary: call operator returns early, so every run waits on the process.
param([string]$tag = "it", [string]$what = "all")
$k = 'C:\Users\HSLEE\AppData\Roaming\KLayout\klayout_app.exe'
$d = 'C:\Users\HSLEE\AppData\Local\Temp\la1s_tso_hand\layout'
$t = 'C:\pdk\sky130_klayout_pdk\tech\sky130'
$gds = "$d\two_stage_ota.gds"
function KL([string[]]$a, [string]$log) {
  $p = Start-Process -FilePath $k -ArgumentList $a -Wait -PassThru -NoNewWindow -RedirectStandardOutput $log -RedirectStandardError "$log.err"
  return $p.ExitCode
}
if ($what -in @('gen','all')) {
  if (Test-Path $gds) { Remove-Item $gds -Confirm:$false }
  $rc = KL @('-b','-r',"`"$d\gen_gds.py`"",'-rd',"design=`"$d\two_stage_ota_design_for_layout.json`"",'-rd',"rules=`"$d\sky130_layout_rules.json`"",'-rd',"out=`"$gds`"",'-rd','top=two_stage_ota','-rd','pins=vdd,gnd,vin_n,vin_p,OUT,bias','-rd','ptap=gnd','-rd','ntap=vdd') "$d\gen_$tag.log"
  "gen rc=$rc"; Get-Content "$d\gen_$tag.log" -Tail 2; Get-Content "$d\gen_$tag.log.err" -Tail 5
  if (Test-Path $gds) { "sha256 " + (Get-FileHash $gds -Algorithm SHA256).Hash + " size " + (Get-Item $gds).Length }
}
if ($what -in @('drc','all')) {
  $rc = KL @('-b','-r',"`"$t\drc\sky130A_mr.drc`"",'-rd',"input=`"$gds`"",'-rd',"report=`"$d\drc_$tag.lyrdb`"",'-rd','feol=true','-rd','beol=true','-rd','thr=2') "$d\drc_$tag.log"
  "drc rc=$rc"
  $x = [xml](Get-Content "$d\drc_$tag.lyrdb" -Raw)
  $items = @($x.'report-database'.items.item)
  "violations " + $items.Count
  $items | Group-Object { $_.category } | Sort-Object Count -Descending | ForEach-Object { "  {0,5} {1}" -f $_.Count, $_.Name }
}
if ($what -in @('lvs','all')) {
  $rc = KL @('-b','-r',"`"$t\lvs\sky130.lvs`"",'-rd',"input=`"$gds`"",'-rd',"report=`"$d\lvs_$tag.lvsdb`"",'-rd',"schematic=`"$d\two_stage_ota.cdl`"",'-rd',"target_netlist=`"$d\two_stage_ota_ext_$tag.cir`"",'-rd','thr=2') "$d\lvs_$tag.log"
  "lvs rc=$rc"; Get-Content "$d\lvs_$tag.log" | Select-String -Pattern "match|ERROR|Error" | Select-Object -Last 5
}
