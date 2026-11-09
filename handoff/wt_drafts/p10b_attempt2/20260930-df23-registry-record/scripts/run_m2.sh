#!/usr/bin/env bash
# 재시도 2차 순서 7: $1 = v1 | collect | green. 병합본 격리 복제본 C:/g88/m2. 결과는 C:/g88/out3.
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
B=0f237862c007f6a53122f2bdfb3c87e6366ec133
C=C:/g88/gmid-gate-cache/$B; PY=C:/Python314/python.exe; O=C:/g88/out3; R=C:/g88/m2
cd C:/g88
case "$1" in
v1)
  P=C:/g88/pyc3_v1; rm -rf $P; mkdir -p $P
  s=$(date +%s)
  PYTHONPYCACHEPREFIX=$P PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R --gmid-phase=2 --gmid-strict= $R/skills/analog-gmid-design/assets/tests > $O/v1_m.txt 2>&1
  echo "v1_m exit $? $(( $(date +%s)-s ))s" >> $O/status.txt ;;
collect)
  P=C:/g88/pyc3_col; rm -rf $P; mkdir -p $P
  PYTHONPYCACHEPREFIX=$P PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R --gmid-phase=2 --gmid-strict= $R/skills/analog-gmid-design/assets/tests --collect-only -q -p no:cacheprovider > $O/collect_m.txt 2>&1
  echo "collect_m exit $?" >> $O/status.txt ;;
green)
  P=C:/g88/pyc3_green; rm -rf $P; mkdir -p $P; rm -f $O/red_M.jsonl
  GMID_RED_CAPTURE=$O/red_M.jsonl GMID_INTERFACE_CARD=$R/docs/02-design/specs/20260930-df23-registry-record.interface.md PYTHONPYCACHEPREFIX=$P PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R -p merge_gate --gmid-phase=2 --gmid-strict= $R/skills/analog-gmid-design/assets/tests/contracts/test_reg_check_df23.py $R/skills/analog-gmid-design/assets/tests/contracts/test_reg_check.py -rA -p no:cacheprovider > $O/green_m.txt 2>&1
  echo "green_m exit $?" >> $O/status.txt
  [ -f $O/red_M.jsonl ] && echo "red_M lines $(wc -l < $O/red_M.jsonl)" >> $O/status.txt || echo "red_M absent (0 records)" >> $O/status.txt ;;
esac
