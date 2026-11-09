#!/usr/bin/env bash
# D0b 작성 전 실측(측정 전용): mk_variant.py 변형을 네 조합으로 돌려 요약한다.
#   bash run_variants.sh <복제본 루트> <rev> <출력 디렉터리> <비교 기준 plan json>
set -u
ROOT=$1; REV=$2; OUT=$3; REF=$4
K=C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/p3kit_d0b
PY=C:/Python314/python.exe
"$PY" -B "$K/mk_variant.py" C:/g162/tmp/move_plan_proto.py C:/g162/tmp/plan_variant.py
run() {
  local name=$1
  bash "$K/run_plan.sh" "$ROOT" "$REV" "$OUT/plan_var_$name.json" C:/g162/tmp/plan_variant.py
  "$PY" -B "$K/analyze_plan.py" "$OUT/plan_var_$name.json" "$OUT/an_var_$name.json" "$REF"
}
V_KEEP=0 V_A6=0 V_LIFT=0; export V_KEEP V_A6 V_LIFT; run none
V_KEEP=1; export V_KEEP; run keep
V_A6=1; export V_A6; run keep_a6
V_LIFT=1; export V_LIFT; run keep_a6_lift
