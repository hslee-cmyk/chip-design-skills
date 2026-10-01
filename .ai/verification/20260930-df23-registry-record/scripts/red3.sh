#!/usr/bin/env bash
# 재시도 3차 순서 3: T=572d767 격리 복제본 C:/g88/iso3에서 red 수집 전체 실행. base 판 캐시(0f23786, tools/gates 트리 a8e5a4a).
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
B=0f237862c007f6a53122f2bdfb3c87e6366ec133
C=C:/g88/gmid-gate-cache3/$B; PY=C:/Python314/python.exe; O=C:/g88/out3; R=C:/g88/iso3
P=C:/g88/pyc3_red; rm -rf $P; mkdir -p $P; rm -f $O/red_T.jsonl
cd C:/g88
s=$(date +%s)
GMID_RED_CAPTURE=$O/red_T.jsonl GMID_INTERFACE_CARD=$R/docs/02-design/specs/20260930-df23-registry-record.interface.md PYTHONPYCACHEPREFIX=$P PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R -p merge_gate --continue-on-collection-errors --gmid-phase=2 --gmid-strict= $R/skills/analog-gmid-design/assets/tests -q -rfE -p no:cacheprovider > $O/full_T_red.txt 2>&1
echo "full_T_red exit $? $(( $(date +%s)-s ))s" >> $O/status.txt
