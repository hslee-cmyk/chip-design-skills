#!/usr/bin/env bash
# measure only: run a per-state job ($1 = pt3 | einst | vtools) over states base(M1 base) + card heads as they appear in chain.jsonl
set -u
JOB=$1; O=/c/g226/out; K=/c/g226/kit
B0=1a1841657a2ea88f92e04455c2041adc660f0629
CARDS=(gmid_lut topology_authoring circuit_state_graph gmid_sizing_engine circuit_metrics theta_search sizing_layout_convergence instance_report_builder)
head_of() { C:/Python314/python.exe -B -c "
import json,sys
for l in open('C:/g226/out/chain.jsonl',encoding='utf-8'):
    r=json.loads(l)
    if r['card']==sys.argv[1]: print(r['head'] if not r.get('gen_error') else 'ERR'); break" "$1"; }
wait_head() { local h=""; while [ -z "$h" ]; do h=$(head_of "$1"); [ -z "$h" ] && sleep 30; done; echo "$h"; }
base_of() { C:/Python314/python.exe -B -c "
import json,sys
for l in open('C:/g226/out/chain.jsonl',encoding='utf-8'):
    r=json.loads(l)
    if r['card']==sys.argv[1]: print(r['base']); break" "$1"; }
export TMP=/c/g226/tmp TEMP=/c/g226/tmp APPDATA="C:/Users/HSLEE/AppData/Roaming" HOME="C:/Users/HSLEE" PYTHONIOENCODING=utf-8
if [ "$JOB" = pt3 ]; then
  git -C /c/g226/pt checkout -q --detach $B0; bash $K/pt3.sh C:/g226/pt base /c/g226/cache/tools/gates $O; tail -2 $O/base.pt3.txt >> $O/pt3_summary.txt; echo "base $B0" >> $O/pt3_summary.txt
  for c in "${CARDS[@]}"; do h=$(wait_head $c); [ "$h" = ERR ] && break
    git -C /c/g226/pt checkout -q --detach $h; git -C /c/g226/pt clean -qfdx
    bash $K/pt3.sh C:/g226/pt $c /c/g226/cache/tools/gates $O; echo "$c $h" >> $O/pt3_summary.txt; tail -2 $O/$c.pt3.txt >> $O/pt3_summary.txt; done
elif [ "$JOB" = einst ]; then
  EL=C:/g226/kit/e_lib.py; EI=C:/g226/kit/e_inst_p3.py; ISO=C:/g226/ei
  [ -d /c/g226/ei ] || git -C /c/g226/r worktree add -q --detach $ISO $B0
  one() { local L=$1 C=$2; git -C $ISO checkout -q --detach $C; git -C $ISO clean -qfdx
    PYTHONPYCACHEPREFIX="$(mktemp -d)" C:/Python314/python.exe -B -P $EL $ISO $O/ei/$L.elib.json >> $O/ei/log.txt 2>&1; echo "$L elib exit=$? $C" >> $O/ei/log.txt
    for cc in current_reuse_telescopic_ota folded_cascode; do s=$(date +%s)
      PYTHONPYCACHEPREFIX="$(mktemp -d)" C:/Python314/python.exe -B -P $EI $ISO $cc $O/ei/$L.$cc.einst.json > $O/ei/$L.$cc.stdout.txt 2>&1; echo "$L einst $cc exit=$? s=$(( $(date +%s)-s ))" >> $O/ei/log.txt; done
    git -C $ISO clean -qfdx; }
  mkdir -p $O/ei; one base $B0
  for c in "${CARDS[@]}"; do h=$(wait_head $c); [ "$h" = ERR ] && break; one $c $h; done
elif [ "$JOB" = vtools ]; then
  for c in "${CARDS[@]}"; do h=$(wait_head $c); [ "$h" = ERR ] && break; b=$(base_of $c)
    bash $K/vtools.sh C:/g226/vt $b $h $c >> $O/vtools_summary.txt 2>&1; echo "$c $b $h" >> $O/vtools_summary.txt; done
fi
echo "$JOB finished" >> $O/states_driver.txt
