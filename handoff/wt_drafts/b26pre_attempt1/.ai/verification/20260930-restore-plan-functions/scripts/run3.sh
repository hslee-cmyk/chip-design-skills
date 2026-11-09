#!/usr/bin/env bash
# 복원 card 3차 순서 3: $1=collect -> base·T 수집, base -> base 전체 실행, red -> T red 수집 전체 실행. 결과는 C:/g13/out/.
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
B=c31e0b686b360f607ebdaa47f8145f3b64657b75
C=C:/g13/gmid-gate-cache/$B
PY=C:/Python314/python.exe
O=C:/g13/out
ID=20260930-restore-plan-functions
if [ "$1" = collect ]; then
for n in base iso; do
  R=C:/g13/${n}3; rm -rf C:/g13/pyc3_col_$n; mkdir -p C:/g13/pyc3_col_$n
  PYTHONPYCACHEPREFIX=C:/g13/pyc3_col_$n PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R --gmid-phase=2 --gmid-strict= $R/skills/analog-gmid-design/assets/tests --collect-only -q -p no:cacheprovider > $O/collect3_$n.txt 2>&1
  echo "collect3_$n exit $?" >> $O/status.txt
done
fi
if [ "$1" = base ]; then
R=C:/g13/base3; rm -rf C:/g13/pyc3_full_base; mkdir -p C:/g13/pyc3_full_base
s=$(date +%s)
PYTHONPYCACHEPREFIX=C:/g13/pyc3_full_base PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R --gmid-phase=2 --gmid-strict= $R/skills/analog-gmid-design/assets/tests -q -rfE -p no:cacheprovider > $O/full3_base.txt 2>&1
echo "full3_base exit $? $(( $(date +%s)-s ))s" >> $O/status.txt
fi
if [ "$1" = red ]; then
R=C:/g13/iso3; rm -rf C:/g13/pyc3_full_iso; mkdir -p C:/g13/pyc3_full_iso; rm -f $O/red3_T.jsonl
s=$(date +%s)
GMID_RED_CAPTURE=$O/red3_T.jsonl GMID_INTERFACE_CARD=$R/docs/02-design/specs/$ID.interface.md PYTHONPYCACHEPREFIX=C:/g13/pyc3_full_iso PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R -p merge_gate --continue-on-collection-errors --gmid-phase=2 --gmid-strict= $R/skills/analog-gmid-design/assets/tests -q -rfE -p no:cacheprovider > $O/full3_T_red.txt 2>&1
echo "full3_T_red exit $? $(( $(date +%s)-s ))s" >> $O/status.txt
fi
