# run_flow_fc.ps1 -- folded_cascode: GDS 생성, DRC, LVS (KLayout batch, Start-Process -Wait). Usage: run_flow_fc.ps1 <tag> <design_json> [gen|drc|lvs|all] [ring]
param([string]$tag = "it", [string]$design = "", [string]$what = "all", [string]$ring = "1", [string]$local = "0")
$k = 'C:\Users\HSLEE\AppData\Roaming\KLayout\klayout_app.exe'
$d = 'C:\Users\HSLEE\AppData\Local\Temp\la1s_fc_hand\layout'
$t = 'C:\pdk\sky130_klayout_pdk\tech\sky130'
$gds = "$d\folded_cascode_$tag.gds"
function KL([string[]]$a, [string]$log) {
  $p = Start-Process -FilePath $k -ArgumentList $a -Wait -PassThru -NoNewWindow -RedirectStandardOutput $log -RedirectStandardError "$log.err"
  return $p.ExitCode
}
if ($what -in @('gen','all')) {
  if (Test-Path $gds) { Remove-Item $gds -Confirm:$false }
  $rc = KL @('-b','-r',"`"$d\gen_gds_fc.py`"",'-rd',"design=`"$design`"",'-rd',"rules=`"$d\sky130_layout_rules.json`"",'-rd',"out=`"$gds`"",'-rd','top=folded_cascode','-rd','pins=vdd,gnd,vin_n,vin_p,out,vb1,vb2,bias3','-rd','ptap=gnd','-rd','ntap=vdd','-rd',"ring=$ring",'-rd',"local=$local") "$d\gen_$tag.log"
  "gen rc=$rc"; Get-Content "$d\gen_$tag.log" -Tail 2; Get-Content "$d\gen_$tag.log.err" -Tail 8
  if (Test-Path $gds) { "sha256 " + (Get-FileHash $gds -Algorithm SHA256).Hash + " size " + (Get-Item $gds).Length }
}
if ($what -in @('drc','all')) {
  $rc = KL @('-b','-r',"`"$t\drc\sky130A_mr.drc`"",'-rd',"input=`"$gds`"",'-rd',"report=`"$d\drc_$tag.lyrdb`"",'-rd','feol=true','-rd','beol=true','-rd','thr=2') "$d\drc_$tag.log"
  "drc rc=$rc"
  $x = [xml](Get-Content "$d\drc_$tag.lyrdb" -Raw)
  $items = @($x.'report-database'.items.item | Where-Object { $_ })
  "violations " + $items.Count
  $items | Group-Object { $_.category } | Sort-Object Count -Descending | ForEach-Object { "  {0,5} {1}" -f $_.Count, $_.Name }
}
if ($what -in @('lvs','all')) {
  $rc = KL @('-b','-r',"`"$t\lvs\sky130.lvs`"",'-rd',"input=`"$gds`"",'-rd',"report=`"$d\lvs_$tag.lvsdb`"",'-rd',"schematic=`"$d\folded_cascode_$tag.cdl`"",'-rd',"target_netlist=`"$d\folded_cascode_ext_$tag.cir`"",'-rd','thr=2') "$d\lvs_$tag.log"
  "lvs rc=$rc"; Get-Content "$d\lvs_$tag.log" | Select-String -Pattern "match|ERROR|Error" | Select-Object -Last 5
}
