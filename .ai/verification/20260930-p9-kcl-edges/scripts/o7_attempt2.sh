#!/usr/bin/env bash
# P9 2차 순서 7(재사용 경로). 사용: o7_attempt2.sh <M2 전체 해시>. audit worktree에서 C:/g47/m2 격리 복제 -> 재사용 조건·레지스트리 대조(o7_reuse.py)
# -> reg_check -> V4·V5·V6·V7(base 판 캐시, --root C:/g47/m2). 결과 C:/g47/out/a2_*.
set -e
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
M2=$1; W=C:/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-p9-kcl-edges-audit
B=7535799302a9ff7cfbfcadb2281d16bf136fadcf; C=C:/g47/gmid-gate-cache/$B; PY=C:/Python314/python.exe; R=C:/g47/m2; O=C:/g47/out
rm -rf $R
git clone -q -c core.longpaths=true --no-hardlinks --no-local --no-checkout $W $R
git -C $R remote remove origin
git -C $R checkout -q --detach $M2
echo "m2 $(git -C $R rev-parse HEAD) remotes=$(git -C $R remote | wc -l) st=$(git -C $R status --porcelain | wc -l)" > $O/a2_status.txt
git -C $R fetch -q --no-tags C:/g47/m HEAD   # 1st M b7765b0 + K 16a71fa objects (C:/g47/m detached HEAD)
PYTHONDONTWRITEBYTECODE=1 $PY -P C:/g47/scripts/o7_reuse.py $R $M2 $O/a2_reuse.json > $O/a2_reuse.txt 2>&1
set +e
mkdir -p C:/g47/pyc_a2_reg; PYTHONPYCACHEPREFIX=C:/g47/pyc_a2_reg $PY $R/skills/analog-gmid-design/assets/tests/tools/reg_check.py --registry $R/docs/03-analysis/gain-budget-gmid-sizing.function-registry.md --root $R > $O/a2_reg_check.txt 2>&1; echo "reg_check exit $?" >> $O/a2_status.txt
run() { local tag=$1; shift; rm -rf C:/g47/pyc_a2_$tag; mkdir -p C:/g47/pyc_a2_$tag; PYTHONPYCACHEPREFIX=C:/g47/pyc_a2_$tag "$@" > $O/a2_tool_$tag.txt 2>&1; echo "$tag exit $?" >> $O/a2_status.txt; }
run V5 $PY $C/weakening_diff.py --root $R --base $B --head $M2
run V6 $PY $C/source_lint.py --root $R --base $B --head $M2
run V7 $PY $C/reachability.py --root $R --base $B --head $M2
run V4 $PY $C/test_lint.py --root $R --base $B --head $M2 --subject stick_diagram:kcl_series_union --subject stick_diagram:_kcl_and_matching_edges
echo "m2 after st=$(git -C $R status --porcelain | wc -l)" >> $O/a2_status.txt
cat $O/a2_status.txt $O/a2_reuse.txt
