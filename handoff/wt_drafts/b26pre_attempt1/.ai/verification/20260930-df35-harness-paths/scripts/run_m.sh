#!/usr/bin/env bash
# DF-35 순서 7: $1=v1 -> 병합본 수집 + 전체 V1, green -> 새 test 파일을 red 수집 플러그인·-rA로. 출력 C:/g14/out/
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
B=c4e5fef0d8ad6ba8eddbd8e2fb6c81a5ceea20da
C=C:/g14/gmid-gate-cache/$B; PY=C:/Python314/python.exe; O=C:/g14/out; R=C:/g14/m
ID=20260930-df35-harness-paths
if [ "$1" = v1 ]; then
rm -rf C:/g14/pyc_col_m; mkdir -p C:/g14/pyc_col_m
PYTHONPYCACHEPREFIX=C:/g14/pyc_col_m PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R --gmid-phase=2 --gmid-strict= $R/skills/analog-gmid-design/assets/tests --collect-only -q -p no:cacheprovider > $O/collect_m.txt 2>&1
echo "collect_m exit $?" >> $O/status.txt
rm -rf C:/g14/pyc_v1_m; mkdir -p C:/g14/pyc_v1_m
s=$(date +%s)
PYTHONPYCACHEPREFIX=C:/g14/pyc_v1_m PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R --gmid-phase=2 --gmid-strict= $R/skills/analog-gmid-design/assets/tests > $O/v1_m.txt 2>&1
echo "v1_m exit $? $(( $(date +%s)-s ))s" >> $O/status.txt
fi
if [ "$1" = green ]; then
rm -rf C:/g14/pyc_green_m; mkdir -p C:/g14/pyc_green_m; rm -f $O/red_M.jsonl
GMID_RED_CAPTURE=$O/red_M.jsonl GMID_INTERFACE_CARD=$R/docs/02-design/specs/$ID.interface.md PYTHONPYCACHEPREFIX=C:/g14/pyc_green_m PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R -p merge_gate --gmid-phase=2 --gmid-strict= $R/skills/analog-gmid-design/assets/tests/contracts/test_df35_harness_paths.py -rA -q -p no:cacheprovider > $O/green_m.txt 2>&1
echo "green_m exit $?" >> $O/status.txt
fi
