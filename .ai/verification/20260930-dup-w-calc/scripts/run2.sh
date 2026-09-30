#!/usr/bin/env bash
# P8 순서 3: 수집(base·T), 그리고 $1=base -> base 전체 실행, $1=red -> T red 수집 전체 실행. 결과는 C:/g12/out/.
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
B=b7d179817245a99cccea45cd5f7642f9815dcec0
C=C:/g12/gmid-gate-cache/$B
PY=C:/Python314/python.exe
O=C:/g12/out
if [ "$1" = collect ]; then
for n in base iso; do
  R=C:/g12/${n}2; rm -rf C:/g12/pyc2_col_$n; mkdir -p C:/g12/pyc2_col_$n
  PYTHONPYCACHEPREFIX=C:/g12/pyc2_col_$n PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R --gmid-phase=2 --gmid-strict= $R/skills/analog-gmid-design/assets/tests --collect-only -q -p no:cacheprovider > $O/collect2_$n.txt 2>&1
  echo "collect_$n exit $?" >> $O/status2.txt
done
fi
if [ "$1" = base ]; then
R=C:/g12/base2; rm -rf C:/g12/pyc2_full_base; mkdir -p C:/g12/pyc2_full_base
s=$(date +%s)
PYTHONPYCACHEPREFIX=C:/g12/pyc2_full_base PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R --gmid-phase=2 --gmid-strict= $R/skills/analog-gmid-design/assets/tests -q -rfE -p no:cacheprovider > $O/full2_base.txt 2>&1
echo "full_base exit $? $(( $(date +%s)-s ))s" >> $O/status2.txt
fi
if [ "$1" = red ]; then
R=C:/g12/iso2; rm -rf C:/g12/pyc2_full_iso; mkdir -p C:/g12/pyc2_full_iso; rm -f $O/red2_T.jsonl
s=$(date +%s)
GMID_RED_CAPTURE=$O/red2_T.jsonl GMID_INTERFACE_CARD=$R/docs/02-design/specs/20260930-dup-w-calc.interface.md PYTHONPYCACHEPREFIX=C:/g12/pyc2_full_iso PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R -p merge_gate --continue-on-collection-errors --gmid-phase=2 --gmid-strict= $R/skills/analog-gmid-design/assets/tests -q -rfE -p no:cacheprovider > $O/full2_T_red.txt 2>&1
echo "full_T_red exit $? $(( $(date +%s)-s ))s" >> $O/status2.txt
fi
