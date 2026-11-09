#!/usr/bin/env bash
# measure only: interface_card.py (gate 4a286f0 copy) on each draft with --root = scratch worktree at the card base; parse_spec_card on each
set -u
DR=$1; O=/c/g226/out; GM=/c/g226/gm/tools/gates
echo "{" > $O/iface.json.tmp; first=1
for pair in "2 topology_authoring" "3 circuit_state_graph" "4 gmid_sizing_engine" "5 circuit_metrics" "6 theta_search" "8 sizing_layout_convergence" "9 instance_report_builder"; do
  set -- $pair; k=$1; c=$2
  b=$(C:/Python314/python.exe -B -c "
import json,sys
for l in open('C:/g226/out/chain.jsonl',encoding='utf-8'):
    r=json.loads(l)
    if r['card']==sys.argv[1]: print(r['base'])" $c | tr -d '\r')
  git -C C:/g226/vt checkout -q --detach $b
  out=$(PYTHONIOENCODING=utf-8 PYTHONPATH=$GM C:/Python314/python.exe -B $GM/interface_card.py $DR/draft_p3_m$k.spec.md --root C:/g226/vt --out $O/m$k.interface.generated.md 2>&1); rc=$?
  rows=$(C:/Python314/python.exe -B -c "
import re,sys
t=open(sys.argv[1],encoding='utf-8').read()
sec=t.split('## 관찰 가능한 계약')[1].split('## 신규 시그니처')[0]
rows=[l for l in sec.splitlines() if l.startswith('| ') and not l.startswith('| 모듈') ]
print(len(rows), '; '.join(r.split('|')[2].strip() for r in rows)[:200])" $O/m$k.interface.generated.md 2>&1 | tr -d '\r')
  [ $first = 1 ] || echo "," >> $O/iface.json.tmp; first=0
  C:/Python314/python.exe -B -c "import json,sys; print(json.dumps(sys.argv[1])+': '+json.dumps(sys.argv[2]))" $c "exit $rc, 기존 함수 표 행 $rows" >> $O/iface.json.tmp
done
echo "}" >> $O/iface.json.tmp; mv $O/iface.json.tmp $O/iface.json; cat $O/iface.json
