#!/usr/bin/env bash
# B34 순서 7: $1 = v1 | green | fast | v3. 결과는 C:/g299/out/. 게이트 도구는 base 판 캐시(스크립트 형태, -P 없이).
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
export TMP=C:/g299/tmp TEMP=C:/g299/tmp
B=7243f2846210c0dba62329acb77885f84a26ff76
M=c851e54aa6a4c330a3545eb75d477e961cd25d62
C=C:/g299/gmid-gate-cache/$B
PY=C:/Python314/python.exe
O=C:/g299/out
R=C:/g299/iso
ID=20260930-b34-grammar-explicit
if [ "$1" = v1 ]; then
rm -rf C:/g299/pyc_col_m; mkdir -p C:/g299/pyc_col_m
PYTHONPYCACHEPREFIX=C:/g299/pyc_col_m PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R --gmid-phase=3 --gmid-strict= $R/skills/analog-gmid-design/assets/tests --collect-only -q -p no:cacheprovider > $O/collect_m.txt 2>&1
echo "collect_m exit $?" >> $O/status.txt
rm -rf C:/g299/pyc_v1_m; mkdir -p C:/g299/pyc_v1_m
s=$(date +%s)
PYTHONPYCACHEPREFIX=C:/g299/pyc_v1_m PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R --gmid-phase=3 --gmid-strict= $R/skills/analog-gmid-design/assets/tests -rfE > $O/v1_m.txt 2>&1
echo "v1_m exit $? $(( $(date +%s)-s ))s" >> $O/status.txt
fi
if [ "$1" = green ]; then
rm -rf C:/g299/pyc_green_m; mkdir -p C:/g299/pyc_green_m; rm -f $O/red_M.jsonl
GMID_RED_CAPTURE=$O/red_M.jsonl GMID_INTERFACE_CARD=$R/docs/02-design/specs/$ID.interface.md PYTHONPYCACHEPREFIX=C:/g299/pyc_green_m PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R -p merge_gate --gmid-phase=3 --gmid-strict= $R/skills/analog-gmid-design/assets/tests/contracts/test_b34_grammar_explicit.py -rA -q -p no:cacheprovider > $O/green_m.txt 2>&1
echo "green_m exit $?" >> $O/status.txt
fi
run() { local tag=$1; shift; rm -rf C:/g299/pyc_t_$tag; mkdir -p C:/g299/pyc_t_$tag; PYTHONPYCACHEPREFIX=C:/g299/pyc_t_$tag "$@" > $O/tool_$tag.txt 2>&1; echo "$tag exit $?" >> $O/status_tools.txt; }
if [ "$1" = fast ]; then
run V5 $PY $C/weakening_diff.py --root $R --base $B --head $M
run V5T $PY $C/weakening_diff.py --root $R --base $B --head d504784862151205c1d10d3efa263469e6f620ab
run V6 $PY $C/source_lint.py --root $R --base $B --head $M
run V7 $PY $C/reachability.py --root $R --base $B --head $M
run V4 $PY $C/test_lint.py --root $R --interface-card $R/docs/02-design/specs/$ID.interface.md --base $B --head $M
fi
if [ "$1" = v3 ]; then
s=$(date +%s)
run V3 $PY $C/mutate_changed.py --root $R --base $B --head $M --pytest-ini $C/pytest_gate.ini --gmid-phase=3 --gmid-strict= --out $O/v3_mut.json
echo "V3 elapsed $(( $(date +%s)-s ))s" >> $O/status_tools.txt
fi
echo "DONE $1" >> $O/status_tools.txt
