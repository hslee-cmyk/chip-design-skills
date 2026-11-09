#!/usr/bin/env bash
# DF-35 순서 3: $1=collect -> base·T 수집, base -> base 전체 실행, red -> T red 수집 전체 실행. 결과는 C:/g14/out/.
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
B=c4e5fef0d8ad6ba8eddbd8e2fb6c81a5ceea20da
C=C:/g14/gmid-gate-cache/$B
PY=C:/Python314/python.exe
O=C:/g14/out
ID=20260930-df35-harness-paths
if [ "$1" = collect ]; then
for n in base iso; do
  R=C:/g14/$n; rm -rf C:/g14/pyc_col_$n; mkdir -p C:/g14/pyc_col_$n
  PYTHONPYCACHEPREFIX=C:/g14/pyc_col_$n PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R --gmid-phase=2 --gmid-strict= $R/skills/analog-gmid-design/assets/tests --collect-only -q -p no:cacheprovider > $O/collect_$n.txt 2>&1
  echo "collect_$n exit $?" >> $O/status.txt
done
fi
if [ "$1" = base ]; then
R=C:/g14/base; rm -rf C:/g14/pyc_full_base; mkdir -p C:/g14/pyc_full_base
s=$(date +%s)
PYTHONPYCACHEPREFIX=C:/g14/pyc_full_base PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R --gmid-phase=2 --gmid-strict= $R/skills/analog-gmid-design/assets/tests -q -rfE -p no:cacheprovider > $O/full_base.txt 2>&1
echo "full_base exit $? $(( $(date +%s)-s ))s" >> $O/status.txt
fi
if [ "$1" = red ]; then
R=C:/g14/iso; rm -rf C:/g14/pyc_full_iso; mkdir -p C:/g14/pyc_full_iso; rm -f $O/red_T.jsonl
s=$(date +%s)
GMID_RED_CAPTURE=$O/red_T.jsonl GMID_INTERFACE_CARD=$R/docs/02-design/specs/$ID.interface.md PYTHONPYCACHEPREFIX=C:/g14/pyc_full_iso PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R -p merge_gate --continue-on-collection-errors --gmid-phase=2 --gmid-strict= $R/skills/analog-gmid-design/assets/tests -q -rfE -p no:cacheprovider > $O/full_T_red.txt 2>&1
echo "full_T_red exit $? $(( $(date +%s)-s ))s" >> $O/status.txt
fi
