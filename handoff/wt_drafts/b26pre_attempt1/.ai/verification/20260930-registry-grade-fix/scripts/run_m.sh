#!/usr/bin/env bash
# 순서 7: 병합본 수집 + V1 전체 실행 + green(red 파일, 플러그인) + 게이트 도구. 결과는 C:/g11/out/.
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
B=06b9cd23e0a1698142c0ddb67031fe03f462d35f; M=5afe45eddb1c5496157c7340fc4aa6d88a6a9dcb
C=C:/g11/gmid-gate-cache/$B; PY=C:/Python314/python.exe; O=C:/g11/out; R=C:/g11/m
A=skills/analog-gmid-design/assets
rm -rf C:/g11/pyc_col_m C:/g11/pyc_v1_m C:/g11/pyc_green_m; mkdir -p C:/g11/pyc_col_m C:/g11/pyc_v1_m C:/g11/pyc_green_m
PYTHONPYCACHEPREFIX=C:/g11/pyc_col_m PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R --gmid-phase=2 --gmid-strict= $R/$A/tests --collect-only -q -p no:cacheprovider > $O/collect_m.txt 2>&1
echo "collect_m exit $?" >> $O/status_m.txt
s=$(date +%s)
PYTHONPYCACHEPREFIX=C:/g11/pyc_v1_m PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R --gmid-phase=2 --gmid-strict= $R/$A/tests > $O/v1_m.txt 2>&1
echo "v1_m exit $? $(( $(date +%s)-s ))s" >> $O/status_m.txt
rm -f $O/red_m.jsonl
GMID_RED_CAPTURE=$O/red_m.jsonl GMID_INTERFACE_CARD=$R/docs/02-design/specs/20260930-registry-grade-fix.interface.md PYTHONPYCACHEPREFIX=C:/g11/pyc_green_m PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R -p merge_gate --continue-on-collection-errors --gmid-phase=2 --gmid-strict= $R/$A/tests/contracts/test_reg_check.py -rA -p no:cacheprovider > $O/green_m.txt 2>&1
echo "green_m exit $?" >> $O/status_m.txt
run() { local tag=$1; shift; mkdir -p C:/g11/pyc_t_$tag; PYTHONPYCACHEPREFIX=C:/g11/pyc_t_$tag "$@" > $O/tool_$tag.txt 2>&1; echo "$tag exit $?" >> $O/status_m.txt; }
run V5 $PY $C/weakening_diff.py --root $R --base $B --head $M
run V6 $PY $C/source_lint.py --root $R --base $B --head $M
run V7 $PY $C/reachability.py --root $R --base $B --head $M
run V4 $PY $C/test_lint.py --root $R --base $B --head $M --module-dir $A/tests/tools --subject reg_check:check --subject reg_check:main
run V3 $PY $C/mutate_changed.py --root $R --base $B --head $M --pytest-ini $C/pytest_gate.ini --gmid-phase=2 --gmid-strict= --out $O/v3_mut.json
echo DONE >> $O/status_m.txt
