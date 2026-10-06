#!/usr/bin/env bash
# 순서 7 V1: $1 = iso | base. 전체 suite(-k·--deselect·-x 없음) + --collect-only. 출력 C:/g372/out/.
set -uo pipefail
export APPDATA=C:/Users/HSLEE/AppData/Roaming HOME=C:/Users/HSLEE PYTHONIOENCODING=utf-8
export TMP=C:/g372/tmp TEMP=C:/g372/tmp TMPDIR=C:/g372/tmp
B=ae1b5886e6fd4b5b18d6096d8ac6076259719ff3
C=C:/g372/gmid-gate-cache/$B
PY=C:/Python314/python.exe
n=$1
R=C:/g372/$n
if [ "$n" = iso ]; then P=v1_T; else P=v1_base; fi
rm -rf C:/g372/pyc/col_$n; mkdir -p C:/g372/pyc/col_$n
PYTHONPYCACHEPREFIX=C:/g372/pyc/col_$n PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R $R/skills/analog-gmid-design/assets/tests --gmid-phase=3 --gmid-strict= --collect-only -q -p no:cacheprovider > C:/g372/out/collect_$n.txt 2>&1
echo "collect_$n exit $?" >> C:/g372/out/status_v1_$n.txt
rm -rf C:/g372/pyc/$P; mkdir -p C:/g372/pyc/$P
s=$(date +%s)
PYTHONPYCACHEPREFIX=C:/g372/pyc/$P PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R $R/skills/analog-gmid-design/assets/tests --gmid-phase=3 --gmid-strict= -rA > C:/g372/out/full_$n.txt 2>&1
echo "full_$n exit $? $(( $(date +%s)-s ))s" >> C:/g372/out/status_v1_$n.txt
git -C $R status --porcelain > C:/g372/out/status_after_$n.txt 2>&1
