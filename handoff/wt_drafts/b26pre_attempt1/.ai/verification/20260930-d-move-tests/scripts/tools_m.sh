#!/usr/bin/env bash
# 순서 7: V3·V4·V5·V6·V7 게이트 도구(base 판 캐시, 스크립트 형태 -P 없이). 출력 C:/g10/out/tool_<V>.txt
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
B=efbf14a4908c27bc1e5481a5cde91b0cca57a693; M=1adbb7653f49cca3cd79a4fc7944b14f61ba0619
C=C:/g10/gmid-gate-cache/$B; PY=C:/Python314/python.exe; R=C:/g10/m; O=C:/g10/out
A=skills/analog-gmid-design/assets
run() { local tag=$1; shift; mkdir -p C:/g10/pyc_t_$tag; PYTHONPYCACHEPREFIX=C:/g10/pyc_t_$tag "$@" > $O/tool_$tag.txt 2>&1; echo "$tag exit $?" >> $O/status_tools.txt; }
run V5 $PY $C/weakening_diff.py --root $R --base $B --head $M
run V6 $PY $C/source_lint.py --root $R --base $B --head $M
run V7 $PY $C/reachability.py --root $R --base $B --head $M
run V4 $PY $C/test_lint.py --root $R --base $B --head $M --module-dir $A/tests/tools --subject regression_runner:run_regression_case --subject interleave_splits:find_interleaved_symmetric_splits
run V4ic $PY $C/test_lint.py --root $R --base $B --head $M --interface-card $R/docs/02-design/specs/20260930-d-move-tests.interface.md
run V3 $PY $C/mutate_changed.py --root $R --base $B --head $M --pytest-ini $C/pytest_gate.ini --gmid-phase=2 --gmid-strict= --out $O/v3_mut.json
echo DONE >> $O/status_tools.txt
