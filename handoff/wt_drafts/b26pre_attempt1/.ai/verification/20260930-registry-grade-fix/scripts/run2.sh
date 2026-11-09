#!/usr/bin/env bash
# 순서 3: 수집(base·T), base 전체 실행, T red 수집 전체 실행. 결과는 C:/g11/out2/ 파일로.
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
B=9b9cbe3f60f83fe578a1db34cd502740771f13d8
C=C:/g11/gmid-gate-cache/$B
PY=C:/Python314/python.exe
O=C:/g11/out2
for n in base iso; do
  R=C:/g11/${n}2; mkdir -p C:/g11/pyc2_col_$n
  PYTHONPYCACHEPREFIX=C:/g11/pyc2_col_$n PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R --gmid-phase=2 --gmid-strict= $R/skills/analog-gmid-design/assets/tests --collect-only -q -p no:cacheprovider > $O/collect_$n.txt 2>&1
  echo "collect_$n exit $?" >> $O/status.txt
done
R=C:/g11/base2; mkdir -p C:/g11/pyc2_full_base
s=$(date +%s)
PYTHONPYCACHEPREFIX=C:/g11/pyc2_full_base PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R --gmid-phase=2 --gmid-strict= $R/skills/analog-gmid-design/assets/tests -q -rfE -p no:cacheprovider > $O/full_base.txt 2>&1
echo "full_base exit $? $(( $(date +%s)-s ))s" >> $O/status.txt
R=C:/g11/iso2; mkdir -p C:/g11/pyc2_full_iso; rm -f $O/red_T.jsonl
s=$(date +%s)
GMID_RED_CAPTURE=$O/red_T.jsonl GMID_INTERFACE_CARD=$R/docs/02-design/specs/20260930-registry-grade-fix.interface.md PYTHONPYCACHEPREFIX=C:/g11/pyc2_full_iso PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R -p merge_gate --continue-on-collection-errors --gmid-phase=2 --gmid-strict= $R/skills/analog-gmid-design/assets/tests -q -rfE -p no:cacheprovider > $O/full_T_red.txt 2>&1
echo "full_T_red exit $? $(( $(date +%s)-s ))s" >> $O/status.txt
echo DONE >> $O/status.txt
