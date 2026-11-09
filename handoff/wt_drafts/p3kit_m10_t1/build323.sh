#!/usr/bin/env bash
# measure only (NOT a role artifact): M1-base stand-in on gate master 2183f2e in scratch C:/g323.
# chain: 2183f2e -> FU stand-in -> T0-W1 stand-in -> G1 proto (g1_kit) -> D0a stand-in -> D0b regen stand-in = M1 base
# (D-11 (ga) N3.10 MOD1 token is already in 2183f2e -- committed 29d2fc2; no stand-in step)
set -euo pipefail
REV=2183f2e
S=/c/g323; SC=C:/g323
SRC=C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills
K=$SC/kit
PY="C:/Python314/python.exe -B"
export TMP=$SC/tmp TEMP=$SC/tmp PYTHONIOENCODING=utf-8 MSYS_NO_PATHCONV=1 MP_STMT_KEY=names
R=$SC/r; O=$SC/out
git clone -q -c core.autocrlf=false --no-hardlinks --no-local "$SRC" "$R"
git -C "$R" remote remove origin
git -C "$R" config core.hooksPath $SC/nohooks
git -C "$R" config core.autocrlf false
G="git -C $R -c user.name=m -c user.email=m@x"
git -C "$R" checkout -q --detach "$REV"
echo "start $(git -C $R rev-parse HEAD)" | tee $O/build.txt
grep -c "_QUERY_CACHE_MAX" "$R/docs/01-plan/features/gain-budget-gmid-sizing.plan.md" | sed 's/^/D11 token lines in plan: /' | tee -a $O/build.txt
$PY $K/fu_standin.py "$R" | tee -a $O/build.txt
$G commit -q -am "FU stand-in (measure only)"; echo "FU $(git -C $R rev-parse HEAD)" | tee -a $O/build.txt
$PY $K/t0w1_standin.py "$R" | tee -a $O/build.txt
$G commit -q -am "T0 W-1 stand-in (measure only)"; echo "T0W1 $(git -C $R rev-parse HEAD)" | tee -a $O/build.txt
$PY $K/install_proto.py "$R" | tee -a $O/build.txt
$G add -A tools && $G commit -q -m "G1 proto stand-in (measure only)"; echo "G1 $(git -C $R rev-parse HEAD)" | tee -a $O/build.txt
mkdir -p $R/tools/migrate; cp $K/move_plan_sim.py $R/tools/migrate/move_plan.py
$G add -A tools && $G commit -q -m "D0a stand-in (measure only)"; D0A=$(git -C $R rev-parse HEAD); echo "D0a $D0A" | tee -a $O/build.txt
source $K/mpargs.sh
$PY $K/move_plan_sim.py plan --root "$R" --rev HEAD "${MP_ARGS[@]}" > $O/plan_pre_regen.json || echo "plan pre exit $?" | tee -a $O/build.txt
REG=docs/03-analysis/gain-budget-gmid-sizing.function-registry.md
$PY $K/regen_registry.py "$R/$REG" $O/plan_pre_regen.json $O/regen_rows.json --write | tail -3 | tee -a $O/build.txt
sed -i 's/보류(Phase 3)/보류(Phase 4)/g' "$R/$REG"
$G commit -q -am "D0b regen stand-in (measure only)"; B=$(git -C $R rev-parse HEAD); echo "M1BASE $B" | tee -a $O/build.txt
set +e
$PY $K/move_plan_sim.py plan --root "$R" --rev HEAD "${MP_ARGS[@]}" > $O/plan_M1base.json; echo "plan M1base exit $?" | tee -a $O/build.txt
mkdir -p $S/cache/tools; rm -rf $S/cache/tools/gates; cp -r $R/tools/gates $S/cache/tools/gates
echo done | tee -a $O/build.txt
