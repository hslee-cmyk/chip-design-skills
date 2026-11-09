#!/usr/bin/env bash
# measure only: V3 (G1 proto) per card on the main scratch clone (worktree root failed: "unable to read tree")
set -u
export TMP=/c/g226/tmp TEMP=/c/g226/tmp APPDATA="C:/Users/HSLEE/AppData/Roaming" HOME="C:/Users/HSLEE" PYTHONIOENCODING=utf-8
C=/c/g226/cache/tools/gates; O=/c/g226/out
C:/Python314/python.exe -B -c "
import json
for l in open('C:/g226/out/chain.jsonl',encoding='utf-8'):
    r=json.loads(l); print(r['card'],r['base'],r['head'])" | tr -d '\r' | while read c b h; do
  s=$(date +%s)
  PYTHONPATH=$C C:/Python314/python.exe -B $C/mutate_changed.py --root C:/g226/r --base $b --head $h --pytest-ini $C/pytest_gate.ini --python C:/Python314/python.exe --gmid-phase=3 --gmid-strict= --out $O/v3_$c.jsonl > $O/v3_$c.json 2>&1
  echo "$c V3 exit $? $(( $(date +%s)-s ))s" >> $O/v3_rerun.txt
done
echo finished >> $O/v3_rerun.txt
