#!/usr/bin/env bash
# UD-6 (D-11 (가) + W-1 (가)) measure only -- NOT a role artifact (test-author/code-author/auditor do not read this kit).
# Rebuild the D0b-base stand-in on gate master, apply the D-11 (가) N3.10 MOD1 token `_QUERY_CACHE_MAX`, and re-measure
# D0b '작성 전 실측' 2/3/4/5/6 with D0a contract-2 statement keys (binding names, MP_STMT_KEY=names).
#   bash build.sh <gate master rev>
# Scratch: C:/g222 only (isolated --no-local clone, origin removed, empty hooksPath, TMP/TEMP under C:/g222).
set -euo pipefail
REV=$1
S=/c/g222; SC=C:/g222
SRC=C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills
D=C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts
K=$D/p3ud6_kit
PY="C:/Python314/python.exe -B"
export TMP=$SC/tmp TEMP=$SC/tmp PYTHONIOENCODING=utf-8 MSYS_NO_PATHCONV=1
mkdir -p $S/tmp $S/nohooks $K/out
R=$SC/r
O=$K/out
if [ ! -e $S/r ]; then
  git clone -q -c core.autocrlf=false --no-hardlinks --no-local "$SRC" "$R"
  git -C "$R" remote remove origin
  git -C "$R" config core.hooksPath $SC/nohooks
  git -C "$R" config core.autocrlf false
fi
G="git -C $R -c user.name=m -c user.email=m@x"
git -C "$R" checkout -q --detach "$REV"
echo "base $(git -C $R rev-parse HEAD)" | tee $O/build.txt
$PY $D/p3fq_kit/fu_standin.py "$R" | tee -a $O/build.txt
$G commit -q -am "FU stand-in (measure only)"
# install_proto.py (13:24 KST 2026-10-02 판) anchors on gate-master mutate_changed.py/rt.py -- no dd60db6 checkout
# (p3fq_kit/build_plan.sh's dd60db6 step fails with this install_proto: '앵커 mc print: 0개').
$PY $D/g1_kit/install_proto.py "$R" | tee -a $O/build.txt
$G add -A tools && $G commit -q -m "G1 proto stand-in (measure only)"
B=$(git -C $R rev-parse HEAD); echo "B (pre D-11) $B" | tee -a $O/build.txt
source $D/p3kit_m1/mpargs.sh
MP=$D/p3kit_m1/move_plan_sim.py
run() { # $1 name $2 key $3 rev
  local s=$(date +%s); set +e
  MP_STMT_KEY=$2 $PY $MP plan --root "$R" --rev "$3" "${MP_ARGS[@]}" > $O/plan_$1.json; local rc=$?; set -e
  echo "plan $1 key=$2 rev=$3 exit=$rc $(( $(date +%s)-s ))s" | tee -a $O/build.txt
}
run names_base names "$B"
# D-11 (가): N3.10 MOD1 token (same bytes as p3fq_kit/variant.py qtok == p3_followup_questions.md §1.4 new text)
$PY $D/p3fq_kit/variant.py "$R" qtok | tee -a $O/build.txt
$G commit -q -am "D-11 (ga) N3.10 MOD1 _QUERY_CACHE_MAX (measure only)"; Q=$(git -C $R rev-parse HEAD)
git -C "$R" diff -U0 "$B" "$Q" > $O/d11_plan_line.diff
run names_q names "$Q"
run hash_q hash "$Q"
# regen sim on Q (D0b code commit stand-in): registry dest column + rule column, 보류(Phase 3) -> 보류(Phase 4)
$PY $D/p3kit_d0b/regen_registry.py "$R/docs/03-analysis/gain-budget-gmid-sizing.function-registry.md" $O/plan_names_q.json $O/regen_rows_q.json | tee -a $O/build.txt
$PY $D/p3kit_d0b/regen_registry.py "$R/docs/03-analysis/gain-budget-gmid-sizing.function-registry.md" $O/plan_names_q.json $O/regen_rows_q_w.json --write | tee -a $O/build.txt
$PY $K/hold_swap.py "$R/docs/03-analysis/gain-budget-gmid-sizing.function-registry.md" | tee -a $O/build.txt
$G commit -q -am "D0b regen sim on Q (measure only)"; RG=$(git -C $R rev-parse HEAD)
git -C "$R" diff --numstat "$Q" "$RG" | tee -a $O/build.txt
run names_rg names "$RG"
$PY $D/p3kit_d0b/analyze_plan.py $O/plan_names_base.json $O/an_names_base.json | tee -a $O/build.txt
$PY $D/p3kit_d0b/analyze_plan.py $O/plan_names_q.json $O/an_names_q.json $O/plan_names_base.json | tee -a $O/build.txt
$PY $D/p3kit_d0b/analyze_plan.py $O/plan_hash_q.json $O/an_hash_q.json $O/plan_names_q.json | tee -a $O/build.txt
$PY $D/p3kit_d0b/analyze_plan.py $O/plan_names_rg.json $O/an_names_rg.json $O/plan_names_q.json | tee -a $O/build.txt
echo "B=$B Q=$Q RG=$RG" | tee -a $O/build.txt
