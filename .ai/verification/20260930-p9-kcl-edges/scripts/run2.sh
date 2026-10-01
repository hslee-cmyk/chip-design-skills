#!/usr/bin/env bash
# P9 순서 3: collect(base·iso) / base 전체 / red(T, merge_gate red 수집). 결과 C:/g47/out/.
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
B=7535799302a9ff7cfbfcadb2281d16bf136fadcf
C=C:/g47/gmid-gate-cache/$B
PY=C:/Python314/python.exe
O=C:/g47/out
if [ "$1" = collect ]; then
for n in iso2; do
  R=C:/g47/$n; rm -rf C:/g47/pyc_col_$n; mkdir -p C:/g47/pyc_col_$n
  PYTHONPYCACHEPREFIX=C:/g47/pyc_col_$n PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R --gmid-phase=2 --gmid-strict= $R/skills/analog-gmid-design/assets/tests --collect-only -q -p no:cacheprovider > $O/collect_$n.txt 2>&1
  echo "collect_$n exit $?" >> $O/status.txt
done
fi
if [ "$1" = base ]; then
R=C:/g47/base; rm -rf C:/g47/pyc_full_base; mkdir -p C:/g47/pyc_full_base
s=$(date +%s)
PYTHONPYCACHEPREFIX=C:/g47/pyc_full_base PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R --gmid-phase=2 --gmid-strict= $R/skills/analog-gmid-design/assets/tests -q -rfE -p no:cacheprovider > $O/full_base.txt 2>&1
echo "full_base exit $? $(( $(date +%s)-s ))s" >> $O/status.txt
fi
if [ "$1" = red ]; then
R=C:/g47/iso2; rm -rf C:/g47/pyc2_full_iso; mkdir -p C:/g47/pyc2_full_iso; rm -f $O/red_T2.jsonl
s=$(date +%s)
GMID_RED_CAPTURE=$O/red_T2.jsonl GMID_INTERFACE_CARD=$R/docs/02-design/specs/20260930-p9-kcl-edges.interface.md PYTHONPYCACHEPREFIX=C:/g47/pyc2_full_iso PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R -p merge_gate --continue-on-collection-errors --gmid-phase=2 --gmid-strict= $R/skills/analog-gmid-design/assets/tests -q -rfE -p no:cacheprovider > $O/full_T2_red.txt 2>&1
echo "full_T2_red exit $? $(( $(date +%s)-s ))s" >> $O/status.txt
fi
