#!/usr/bin/env bash
# 순서 3 (20260930-df23-registry-record): $1 = collect | full_base | red_T. 결과는 C:/g88/out/ 파일로.
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
B=a796468889741bb7eb8da121ffefb0589cb2b769
C=C:/g88/gmid-gate-cache/$B
PY=C:/Python314/python.exe
O=C:/g88/out
case "$1" in
collect)
  for n in base iso; do
    R=C:/g88/$n; P=C:/g88/pyc_col_$n; rm -rf $P; mkdir -p $P
    PYTHONPYCACHEPREFIX=$P PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R --gmid-phase=2 --gmid-strict= $R/skills/analog-gmid-design/assets/tests --collect-only -q -p no:cacheprovider > $O/collect_$n.txt 2>&1
    echo "collect_$n exit $?" >> $O/status.txt
  done ;;
full_base)
  R=C:/g88/base; P=C:/g88/pyc_full_base; rm -rf $P; mkdir -p $P
  s=$(date +%s)
  PYTHONPYCACHEPREFIX=$P PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R --gmid-phase=2 --gmid-strict= $R/skills/analog-gmid-design/assets/tests -q -rfE -p no:cacheprovider > $O/full_base.txt 2>&1
  echo "full_base exit $? $(( $(date +%s)-s ))s" >> $O/status.txt ;;
red_T)
  R=C:/g88/iso; P=C:/g88/pyc_full_iso; rm -rf $P; mkdir -p $P; rm -f $O/red_T.jsonl
  s=$(date +%s)
  GMID_RED_CAPTURE=$O/red_T.jsonl GMID_INTERFACE_CARD=$R/docs/02-design/specs/20260930-df23-registry-record.interface.md PYTHONPYCACHEPREFIX=$P PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R -p merge_gate --continue-on-collection-errors --gmid-phase=2 --gmid-strict= $R/skills/analog-gmid-design/assets/tests -q -rfE -p no:cacheprovider > $O/full_T_red.txt 2>&1
  echo "full_T_red exit $? $(( $(date +%s)-s ))s" >> $O/status.txt ;;
esac
