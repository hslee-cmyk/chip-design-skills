#!/usr/bin/env bash
# 3차 순서 3 미리보기(판정 아님): T + 2차 K(06099fa) 엔진·레지스트리 blob을 얹은 스크래치 합성 병합본 C:/g13/syn3에서
# 새 test 파일 green, V3·V4(a·b)·V6·V7·reg_check. base 판 캐시(c31e0b6) 도구. 출력 C:/g13/out/pv3_<tag>.txt
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
B=c31e0b686b360f607ebdaa47f8145f3b64657b75; S=C:/g13/syn3; H=$(git -C $S rev-parse HEAD)
C=C:/g13/gmid-gate-cache/$B; PY=C:/Python314/python.exe; O=C:/g13/out; A=skills/analog-gmid-design/assets
run() { local tag=$1; shift; rm -rf C:/g13/pyc_pv3_$tag; mkdir -p C:/g13/pyc_pv3_$tag; PYTHONPYCACHEPREFIX=C:/g13/pyc_pv3_$tag "$@" > $O/pv3_$tag.txt 2>&1; echo "pv3 $tag exit $?" >> $O/status.txt; }
run green env PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$S --confcutdir=$S --gmid-phase=2 --gmid-strict= $S/$A/tests/contracts/test_restore_plan_functions.py $S/$A/tests/contracts/test_d_delete_dead.py -q -p no:cacheprovider
run V4a $PY $C/test_lint.py --root $S --base $B --head $H --subject sizing_recipe:lut_conditions_from_npz
run V4b $PY $C/test_lint.py --root $S --base $B --head $H --subject run_harness:derived_spec --module-dir workspaces
run V6 $PY $C/source_lint.py --root $S --base $B --head $H
run V7 $PY $C/reachability.py --root $S --base $B --head $H
run REG $PY $S/$A/tests/tools/reg_check.py --registry $S/docs/03-analysis/gain-budget-gmid-sizing.function-registry.md --root $S
run V3 $PY $C/mutate_changed.py --root $S --base $B --head $H --pytest-ini $C/pytest_gate.ini --gmid-phase=2 --gmid-strict= --out $O/pv3_v3_mut.json
