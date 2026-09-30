#!/usr/bin/env bash
# 순서 3: 수집(base·T), base 전체 실행, T red 수집 전체 실행. 결과는 C:/g10/out/ 파일로.
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
B=efbf14a4908c27bc1e5481a5cde91b0cca57a693
C=C:/g10/gmid-gate-cache/$B
PY=C:/Python314/python.exe
O=C:/g10/out
for n in base iso; do
  R=C:/g10/$n; mkdir -p C:/g10/pyc_col_$n
  PYTHONPYCACHEPREFIX=C:/g10/pyc_col_$n PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R --gmid-phase=2 --gmid-strict= $R/skills/analog-gmid-design/assets/tests --collect-only -q -p no:cacheprovider > $O/collect_$n.txt 2>&1
  echo "collect_$n exit $?" >> $O/status.txt
done
R=C:/g10/base; mkdir -p C:/g10/pyc_full_base
s=$(date +%s)
PYTHONPYCACHEPREFIX=C:/g10/pyc_full_base PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R --gmid-phase=2 --gmid-strict= $R/skills/analog-gmid-design/assets/tests -q -rfE -p no:cacheprovider > $O/full_base.txt 2>&1
echo "full_base exit $? $(( $(date +%s)-s ))s" >> $O/status.txt
R=C:/g10/iso; mkdir -p C:/g10/pyc_full_iso; rm -f $O/red_T.jsonl
s=$(date +%s)
GMID_RED_CAPTURE=$O/red_T.jsonl GMID_INTERFACE_CARD=$R/docs/02-design/specs/20260930-d-move-tests.interface.md PYTHONPYCACHEPREFIX=C:/g10/pyc_full_iso PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R -p merge_gate --continue-on-collection-errors --gmid-phase=2 --gmid-strict= $R/skills/analog-gmid-design/assets/tests -q -rfE -p no:cacheprovider > $O/full_T_red.txt 2>&1
echo "full_T_red exit $? $(( $(date +%s)-s ))s" >> $O/status.txt
echo DONE >> $O/status.txt
