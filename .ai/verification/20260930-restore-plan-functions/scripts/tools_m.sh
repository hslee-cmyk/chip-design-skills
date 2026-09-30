#!/usr/bin/env bash
# 순서 7: $1=fast -> V4·V5·V6·V7·reg_check, v3 -> V3. base 판 캐시 도구를 스크립트 형태(-P 없이). 출력 C:/g13/out/tool_<V>.txt
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
B=04c72481a8903c53e861ef7eb2895ffca53838d3; M=2889a45d70b388e49011ad2cff4c3f0aadf126e7
C=C:/g13/gmid-gate-cache/$B; PY=C:/Python314/python.exe; R=C:/g13/m; O=C:/g13/out
A=skills/analog-gmid-design/assets
run() { local tag=$1; shift; rm -rf C:/g13/pyc_t_$tag; mkdir -p C:/g13/pyc_t_$tag; PYTHONPYCACHEPREFIX=C:/g13/pyc_t_$tag "$@" > $O/tool_$tag.txt 2>&1; echo "$tag exit $?" >> $O/status_tools.txt; }
if [ "$1" = fast ]; then
run V5 $PY $C/weakening_diff.py --root $R --base $B --head $M
run V6 $PY $C/source_lint.py --root $R --base $B --head $M
run V7 $PY $C/reachability.py --root $R --base $B --head $M
run V4 $PY $C/test_lint.py --root $R --base $B --head $M --interface-card $R/docs/02-design/specs/20260930-restore-plan-functions.interface.md --subject sizing_recipe:lut_conditions_from_npz --subject run_harness:derived_spec
run REG_m $PY $R/$A/tests/tools/reg_check.py --registry $R/docs/03-analysis/gain-budget-gmid-sizing.function-registry.md --root $R
run REG_base $PY $R/$A/tests/tools/reg_check.py --registry C:/g13/base/docs/03-analysis/gain-budget-gmid-sizing.function-registry.md --root C:/g13/base
fi
if [ "$1" = v3 ]; then
run V3 $PY $C/mutate_changed.py --root $R --base $B --head $M --pytest-ini $C/pytest_gate.ini --gmid-phase=2 --gmid-strict= --out $O/v3_mut.json
fi
echo "DONE $1" >> $O/status_tools.txt
