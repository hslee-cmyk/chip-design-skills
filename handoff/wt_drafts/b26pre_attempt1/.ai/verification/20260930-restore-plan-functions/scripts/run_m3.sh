#!/usr/bin/env bash
# 순서 7: $1=v1 -> 병합본 전체 V1(+수집), green -> 새 test 파일을 red 수집 플러그인·-rA로. 출력 C:/g13/out/
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
B=c31e0b686b360f607ebdaa47f8145f3b64657b75
C=C:/g13/gmid-gate-cache/$B; PY=C:/Python314/python.exe; O=C:/g13/out; R=C:/g13/m3
ID=20260930-restore-plan-functions
if [ "$1" = v1 ]; then
rm -rf C:/g13/pyc3_col_m; mkdir -p C:/g13/pyc3_col_m
PYTHONPYCACHEPREFIX=C:/g13/pyc3_col_m PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R --gmid-phase=2 --gmid-strict= $R/skills/analog-gmid-design/assets/tests --collect-only -q -p no:cacheprovider > $O/collect3_m.txt 2>&1
echo "collect3_m exit $?" >> $O/status.txt
rm -rf C:/g13/pyc3_v1_m3; mkdir -p C:/g13/pyc3_v1_m3
s=$(date +%s)
PYTHONPYCACHEPREFIX=C:/g13/pyc3_v1_m3 PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R --gmid-phase=2 --gmid-strict= $R/skills/analog-gmid-design/assets/tests > $O/v1_m3.txt 2>&1
echo "v1_m3 exit $? $(( $(date +%s)-s ))s" >> $O/status.txt
fi
if [ "$1" = green ]; then
rm -rf C:/g13/pyc3_green_m3; mkdir -p C:/g13/pyc3_green_m3; rm -f $O/red3_M.jsonl
GMID_RED_CAPTURE=$O/red3_M.jsonl GMID_INTERFACE_CARD=$R/docs/02-design/specs/$ID.interface.md PYTHONPYCACHEPREFIX=C:/g13/pyc3_green_m3 PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R -p merge_gate --gmid-phase=2 --gmid-strict= $R/skills/analog-gmid-design/assets/tests/contracts/test_restore_plan_functions.py $R/skills/analog-gmid-design/assets/tests/contracts/test_d_delete_dead.py -rA -q -p no:cacheprovider > $O/green_m3.txt 2>&1
echo "green_m3 exit $?" >> $O/status.txt
fi
