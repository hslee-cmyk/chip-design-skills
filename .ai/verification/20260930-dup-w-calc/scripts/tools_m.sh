#!/usr/bin/env bash
# 순서 7: V4·V5·V6·V7(인자 $1=fast) 또는 V3($1=v3) 게이트 도구(base 판 캐시, 스크립트 형태 -P 없이). 출력 C:/g12/out/tool_<V>.txt
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
B=6158a5f8cf3b005abd010c05e1fa09fb6e3a6c25; M=40f5dbff2aaca8ce0fbfbe10634cd47b712afb44
C=C:/g12/gmid-gate-cache/$B; PY=C:/Python314/python.exe; R=C:/g12/m; O=C:/g12/out
A=skills/analog-gmid-design/assets
run() { local tag=$1; shift; rm -rf C:/g12/pyc_t_$tag; mkdir -p C:/g12/pyc_t_$tag; PYTHONPYCACHEPREFIX=C:/g12/pyc_t_$tag "$@" > $O/tool_$tag.txt 2>&1; echo "$tag exit $?" >> $O/status_tools.txt; }
if [ "$1" = fast ]; then
run V5 $PY $C/weakening_diff.py --root $R --base $B --head $M
run V6 $PY $C/source_lint.py --root $R --base $B --head $M
run V7 $PY $C/reachability.py --root $R --base $B --head $M
run V4 $PY $C/test_lint.py --root $R --base $B --head $M --interface-card $R/docs/02-design/specs/20260930-dup-w-calc.interface.md --subject sizing_recipe:width_from_id_density
run REG_m $PY $R/$A/tests/tools/reg_check.py --registry $R/docs/03-analysis/gain-budget-gmid-sizing.function-registry.md --root $R
run REG_base $PY $R/$A/tests/tools/reg_check.py --registry C:/g12/base/docs/03-analysis/gain-budget-gmid-sizing.function-registry.md --root C:/g12/base
fi
if [ "$1" = v3 ]; then
run V3 $PY $C/mutate_changed.py --root $R --base $B --head $M --pytest-ini $C/pytest_gate.ini --gmid-phase=2 --gmid-strict= --out $O/v3_mut.json
fi
echo "DONE $1" >> $O/status_tools.txt
