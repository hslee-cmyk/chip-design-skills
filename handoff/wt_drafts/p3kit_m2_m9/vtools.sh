#!/usr/bin/env bash
# scratch: V3/V6/V7 (G1 proto in $C) on root $1, base $2, head $3, label $4
set -u
export TMP=/c/g226/tmp TEMP=/c/g226/tmp APPDATA="C:/Users/HSLEE/AppData/Roaming" HOME="C:/Users/HSLEE" PYTHONIOENCODING=utf-8
ROOT=$1; B=$2; H=$3; L=$4; C=/c/g226/cache/tools/gates; O=/c/g226/out
s=$(date +%s); PYTHONPATH=$C C:/Python314/python.exe -B $C/mutate_changed.py --root $ROOT --base $B --head $H --pytest-ini $C/pytest_gate.ini --python C:/Python314/python.exe --gmid-phase=3 --gmid-strict= --out $O/v3_$L.jsonl > $O/v3_$L.json 2>&1; echo "V3 exit $? $(( $(date +%s)-s ))s"
for t in source_lint reachability; do s=$(date +%s); PYTHONPATH=$C C:/Python314/python.exe -B $C/$t.py --root $ROOT --base $B --head $H > $O/v_${t}_$L.json 2>&1; echo "$t exit $? $(( $(date +%s)-s ))s"; done
