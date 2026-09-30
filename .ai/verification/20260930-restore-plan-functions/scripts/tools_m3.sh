#!/usr/bin/env bash
# 순서 7: $1=fast -> V4·V5·V6·V7·reg_check, v3 -> V3. base 판 캐시 도구를 스크립트 형태(-P 없이). 출력 C:/g13/out/tool_<V>.txt
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
B=c31e0b686b360f607ebdaa47f8145f3b64657b75; M=f1c4b7dc0955a48ae3705e2f993eeaeb119d236d
C=C:/g13/gmid-gate-cache/$B; PY=C:/Python314/python.exe; R=C:/g13/m3; O=C:/g13/out
A=skills/analog-gmid-design/assets
run() { local tag=$1; shift; rm -rf C:/g13/pyc3_t_$tag; mkdir -p C:/g13/pyc3_t_$tag; PYTHONPYCACHEPREFIX=C:/g13/pyc3_t_$tag "$@" > $O/tool3_$tag.txt 2>&1; echo "$tag exit $?" >> $O/status3_tools.txt; }
if [ "$1" = fast ]; then
run V5 $PY $C/weakening_diff.py --root $R --base $B --head $M
run V6 $PY $C/source_lint.py --root $R --base $B --head $M
run V7 $PY $C/reachability.py --root $R --base $B --head $M
run V4a $PY $C/test_lint.py --root $R --base $B --head $M --subject sizing_recipe:lut_conditions_from_npz
run V4b $PY $C/test_lint.py --root $R --base $B --head $M --subject run_harness:derived_spec --module-dir workspaces
run V4card $PY $C/test_lint.py --root $R --base $B --head $M --interface-card $R/docs/02-design/specs/20260930-restore-plan-functions.interface.md
run REG_m $PY $R/$A/tests/tools/reg_check.py --registry $R/docs/03-analysis/gain-budget-gmid-sizing.function-registry.md --root $R
run REG_base $PY $R/$A/tests/tools/reg_check.py --registry C:/g13/base3/docs/03-analysis/gain-budget-gmid-sizing.function-registry.md --root C:/g13/base3
fi
if [ "$1" = v3 ]; then
run V3 $PY $C/mutate_changed.py --root $R --base $B --head $M --pytest-ini $C/pytest_gate.ini --gmid-phase=2 --gmid-strict= --out $O/v3_mut3.json
fi
echo "DONE $1" >> $O/status3_tools.txt
