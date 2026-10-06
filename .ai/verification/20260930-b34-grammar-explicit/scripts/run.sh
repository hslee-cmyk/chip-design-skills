#!/usr/bin/env bash
# B34 순서 3: $1 = collect | base | red. 결과는 C:/g291/out/.
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
export TMP=C:/g291/tmp TEMP=C:/g291/tmp
B=7243f2846210c0dba62329acb77885f84a26ff76
C=C:/g291/gmid-gate-cache/$B
PY=C:/Python314/python.exe
O=C:/g291/out
ID=20260930-b34-grammar-explicit
if [ "$1" = collect ]; then
for n in base iso; do
  R=C:/g291/$n; rm -rf C:/g291/pyc_col_$n; mkdir -p C:/g291/pyc_col_$n
  PYTHONPYCACHEPREFIX=C:/g291/pyc_col_$n PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R --gmid-phase=3 --gmid-strict= $R/skills/analog-gmid-design/assets/tests --collect-only -q -p no:cacheprovider > $O/collect_$n.txt 2>&1
  echo "collect_$n exit $?" >> $O/status.txt
done
fi
if [ "$1" = base ]; then
R=C:/g291/base; rm -rf C:/g291/pyc_full_base; mkdir -p C:/g291/pyc_full_base
s=$(date +%s)
PYTHONPYCACHEPREFIX=C:/g291/pyc_full_base PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R --gmid-phase=3 --gmid-strict= $R/skills/analog-gmid-design/assets/tests -q -rfE -p no:cacheprovider > $O/full_base.txt 2>&1
echo "full_base exit $? $(( $(date +%s)-s ))s" >> $O/status.txt
fi
if [ "$1" = red ]; then
R=C:/g291/iso; rm -rf C:/g291/pyc_full_iso; mkdir -p C:/g291/pyc_full_iso; rm -f $O/red_T.jsonl
s=$(date +%s)
GMID_RED_CAPTURE=$O/red_T.jsonl GMID_INTERFACE_CARD=$R/docs/02-design/specs/$ID.interface.md PYTHONPYCACHEPREFIX=C:/g291/pyc_full_iso PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R -p merge_gate --continue-on-collection-errors --gmid-phase=3 --gmid-strict= $R/skills/analog-gmid-design/assets/tests -q -rfE -p no:cacheprovider > $O/full_T_red.txt 2>&1
echo "full_T_red exit $? $(( $(date +%s)-s ))s" >> $O/status.txt
fi
