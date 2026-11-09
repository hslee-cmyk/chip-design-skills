#!/usr/bin/env bash
# 순서 7: 병합본 수집 + V1 전체 실행(-k·--deselect·-x 없음). 결과는 C:/g10/out/ 파일로.
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
B=efbf14a4908c27bc1e5481a5cde91b0cca57a693
C=C:/g10/gmid-gate-cache/$B
PY=C:/Python314/python.exe
O=C:/g10/out
R=C:/g10/m
rm -rf C:/g10/pyc_col_m C:/g10/pyc_v1_m; mkdir -p C:/g10/pyc_col_m C:/g10/pyc_v1_m
PYTHONPYCACHEPREFIX=C:/g10/pyc_col_m PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R --gmid-phase=2 --gmid-strict= $R/skills/analog-gmid-design/assets/tests --collect-only -q -p no:cacheprovider > $O/collect_m.txt 2>&1
echo "collect_m exit $?" >> $O/status_m.txt
s=$(date +%s)
PYTHONPYCACHEPREFIX=C:/g10/pyc_v1_m PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R --gmid-phase=2 --gmid-strict= $R/skills/analog-gmid-design/assets/tests > $O/v1_m.txt 2>&1
echo "v1_m exit $? $(( $(date +%s)-s ))s" >> $O/status_m.txt
echo DONE >> $O/status_m.txt
