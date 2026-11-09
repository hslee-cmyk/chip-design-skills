#!/usr/bin/env bash
# D0b 작성 전 실측(측정 전용): 격리 복제본 $1의 커밋 $2에서 D0a plan 시제품을 design 30 §6.3 MP_ARGS로 돌려 $3(json)에 쓴다.
#   bash run_plan.sh <복제본 루트(C:/g<n>/...)> <rev> <출력 json> [<move_plan 사본>]
# 게이트 모듈은 복제본 작업 트리의 tools/gates(G1 시제품 설치본)에서 import된다(시제품 = D0a 계약 1과 같은 방식).
set -u
ROOT=$1; REV=$2; OUT=$3; MP=${4:-C:/g162/tmp/move_plan_proto.py}
case "$ROOT" in C:/g162/*) ;; *) echo "scratch must be under C:/g162"; exit 2;; esac
MP_ARGS=(--plan docs/01-plan/features/gain-budget-gmid-sizing.plan.md
         --registry docs/03-analysis/gain-budget-gmid-sizing.function-registry.md
         --split sizing_recipe.py stick_diagram.py topology_library.py design_report.py audit_current_forced.py
         --keep audit_current_forced.py
         --aliases '{"optimizer": "theta_search.py"}')
s=$(date +%s)
C:/Python314/python.exe -B "$MP" plan --root "$ROOT" --rev "$REV" "${MP_ARGS[@]}" > "$OUT"
rc=$?
echo "plan rev=$REV exit=$rc $(( $(date +%s)-s ))s -> $OUT"
