#!/usr/bin/env bash
# 순서 7 V1: $1 = iso | base. 전체 suite(-k·--deselect·-x 없음) + --collect-only. 출력 C:/g342/out/.
set -uo pipefail
export APPDATA=C:/Users/HSLEE/AppData/Roaming HOME=C:/Users/HSLEE PYTHONIOENCODING=utf-8
export TMP=C:/g342/tmp TEMP=C:/g342/tmp TMPDIR=C:/g342/tmp
B=6c724debd884dd1d31034f5279ae450f35e67fc4
C=C:/g342/gmid-gate-cache/$B
PY=C:/Python314/python.exe
n=$1
R=C:/g342/$n
if [ "$n" = iso ]; then P=v1_T; else P=v1_base; fi
rm -rf C:/g342/pyc/col_$n; mkdir -p C:/g342/pyc/col_$n
PYTHONPYCACHEPREFIX=C:/g342/pyc/col_$n PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R $R/skills/analog-gmid-design/assets/tests --gmid-phase=3 --gmid-strict= --collect-only -q -p no:cacheprovider > C:/g342/out/collect_$n.txt 2>&1
echo "collect_$n exit $?" >> C:/g342/out/status_v1_$n.txt
rm -rf C:/g342/pyc/$P; mkdir -p C:/g342/pyc/$P
s=$(date +%s)
PYTHONPYCACHEPREFIX=C:/g342/pyc/$P PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R $R/skills/analog-gmid-design/assets/tests --gmid-phase=3 --gmid-strict= -rA > C:/g342/out/full_$n.txt 2>&1
echo "full_$n exit $? $(( $(date +%s)-s ))s" >> C:/g342/out/status_v1_$n.txt
git -C $R status --porcelain > C:/g342/out/status_after_$n.txt 2>&1
