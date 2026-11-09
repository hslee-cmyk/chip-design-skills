#!/usr/bin/env bash
# 순서 7: V3·V4·V5·V6·V7 도구 + v_intro. 출력 C:/g342/out/tool_*.txt
set -uo pipefail
export APPDATA=C:/Users/HSLEE/AppData/Roaming HOME=C:/Users/HSLEE PYTHONIOENCODING=utf-8
export TMP=C:/g342/tmp TEMP=C:/g342/tmp TMPDIR=C:/g342/tmp
B=6c724debd884dd1d31034f5279ae450f35e67fc4
T=d2b2ed71ce506b010e5d87c03add007069a5a322
C=C:/g342/gmid-gate-cache/$B
PY=C:/Python314/python.exe
R=C:/g342/iso
IC=$R/docs/02-design/specs/20260930-b26-pre-test-strengthen.interface.md
run() { local n=$1; shift; local s=$(date +%s); PYTHONPYCACHEPREFIX=C:/g342/pyc/tool_$n "$@" > C:/g342/out/tool_$n.txt 2>&1; echo "tool_$n exit $? $(( $(date +%s)-s ))s" >> C:/g342/out/status_tools.txt; }
run V3 $PY -B $C/mutate_changed.py --root $R --base $B --head $T --pytest-ini $C/pytest_gate.ini --python $PY --gmid-phase=3 --gmid-strict= --out C:/g342/out/v3.jsonl
run V4 $PY -B $C/test_lint.py --root $R --base $B --head $T --interface-card $IC
run V5 $PY -B $C/weakening_diff.py --root $R --base $B --head $T
run V6 $PY -B $C/source_lint.py --root $R --base $B --head $T
run V7 $PY -B $C/reachability.py --root $R --base $B --head $T
PYTHONPATH=$C $PY -B -P -c "import merge_gate as mg, role_paths as rp, sys; o=mg.TreeView(['-C','$R'],'$B'); import inspect; print([n for n in dir(rp) if 'plan' in n.lower()]); print([n for n in dir(mg) if 'plan' in n.lower()])" > C:/g342/out/plan_names.txt 2>&1
