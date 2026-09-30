#!/usr/bin/env bash
# 순서 7: 병합본 수집 + V1 전체 실행(-k·--deselect·-x 없음) + red 파일 green(-rA, red 수집 플러그인). 결과는 C:/g12/out/.
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
B=b7d179817245a99cccea45cd5f7642f9815dcec0
C=C:/g12/gmid-gate-cache/$B
PY=C:/Python314/python.exe
O=C:/g12/out
R=C:/g12/m2
rm -rf C:/g12/pyc2_col_m C:/g12/pyc2_v1_m C:/g12/pyc2_green_m; mkdir -p C:/g12/pyc2_col_m C:/g12/pyc2_v1_m C:/g12/pyc2_green_m
PYTHONPYCACHEPREFIX=C:/g12/pyc2_col_m PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R --gmid-phase=2 --gmid-strict= $R/skills/analog-gmid-design/assets/tests --collect-only -q -p no:cacheprovider > $O/collect2_m.txt 2>&1
echo "collect_m exit $?" >> $O/status2_m.txt
s=$(date +%s)
PYTHONPYCACHEPREFIX=C:/g12/pyc2_v1_m PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R --gmid-phase=2 --gmid-strict= $R/skills/analog-gmid-design/assets/tests > $O/v1_m2.txt 2>&1
echo "v1_m exit $? $(( $(date +%s)-s ))s" >> $O/status2_m.txt
rm -f $O/red2_m.jsonl
GMID_RED_CAPTURE=$O/red2_m.jsonl GMID_INTERFACE_CARD=$R/docs/02-design/specs/20260930-dup-w-calc.interface.md PYTHONPYCACHEPREFIX=C:/g12/pyc2_green_m PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R -p merge_gate --continue-on-collection-errors --gmid-phase=2 --gmid-strict= $R/skills/analog-gmid-design/assets/tests/contracts/test_dup_w_calc.py -rA -p no:cacheprovider > $O/green2_m.txt 2>&1
echo "green_m exit $?" >> $O/status2_m.txt
echo DONE >> $O/status2_m.txt
