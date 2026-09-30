#!/usr/bin/env bash
# 순서 7: $1=v1 -> 병합본 전체 V1(+수집), green -> 새 test 파일을 red 수집 플러그인·-rA로. 출력 C:/g13/out/
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
B=04c72481a8903c53e861ef7eb2895ffca53838d3
C=C:/g13/gmid-gate-cache/$B; PY=C:/Python314/python.exe; O=C:/g13/out; R=C:/g13/m
ID=20260930-restore-plan-functions
if [ "$1" = v1 ]; then
rm -rf C:/g13/pyc_col_m; mkdir -p C:/g13/pyc_col_m
PYTHONPYCACHEPREFIX=C:/g13/pyc_col_m PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R --gmid-phase=2 --gmid-strict= $R/skills/analog-gmid-design/assets/tests --collect-only -q -p no:cacheprovider > $O/collect_m.txt 2>&1
echo "collect_m exit $?" >> $O/status.txt
rm -rf C:/g13/pyc_v1_m; mkdir -p C:/g13/pyc_v1_m
s=$(date +%s)
PYTHONPYCACHEPREFIX=C:/g13/pyc_v1_m PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R --gmid-phase=2 --gmid-strict= $R/skills/analog-gmid-design/assets/tests > $O/v1_m.txt 2>&1
echo "v1_m exit $? $(( $(date +%s)-s ))s" >> $O/status.txt
fi
if [ "$1" = green ]; then
rm -rf C:/g13/pyc_green_m; mkdir -p C:/g13/pyc_green_m; rm -f $O/red_M.jsonl
GMID_RED_CAPTURE=$O/red_M.jsonl GMID_INTERFACE_CARD=$R/docs/02-design/specs/$ID.interface.md PYTHONPYCACHEPREFIX=C:/g13/pyc_green_m PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R -p merge_gate --gmid-phase=2 --gmid-strict= $R/skills/analog-gmid-design/assets/tests/contracts/test_restore_plan_functions.py $R/skills/analog-gmid-design/assets/tests/contracts/test_d_delete_dead.py -rA -q -p no:cacheprovider > $O/green_m.txt 2>&1
echo "green_m exit $?" >> $O/status.txt
fi
