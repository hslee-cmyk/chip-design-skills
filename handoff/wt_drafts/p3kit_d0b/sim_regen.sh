#!/usr/bin/env bash
# D0b 작성 전 실측(측정 전용): 레지스트리 열 재생성 모의 -> 같은 규칙으로 plan 재실행 -> reg_mismatch·배정 사상 불변(멱등) 확인.
#   bash sim_regen.sh <복제본 루트> <기준 rev> <이름> <plan 사본 .py> [V_KEEP V_A6 V_LIFT 값 3개]
# 기준 rev에서 plan -> regen_registry --write -> 측정용 커밋 -> plan 재실행. 브랜치를 만들지 않고 detached 커밋만 쓴다.
set -u
ROOT=$1; REV=$2; NAME=$3; MP=$4
V_KEEP=${5:-0} V_A6=${6:-0} V_LIFT=${7:-0}; export V_KEEP V_A6 V_LIFT
case "$ROOT" in C:/g162/*) ;; *) echo "scratch must be under C:/g162"; exit 2;; esac
K=C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/p3kit_d0b
PY=C:/Python314/python.exe
O=C:/g162/out
REG=docs/03-analysis/gain-budget-gmid-sizing.function-registry.md
git -C "$ROOT" checkout -q --detach "$REV"
bash "$K/run_plan.sh" "$ROOT" HEAD "$O/regen_${NAME}_before.json" "$MP"
"$PY" -B "$K/regen_registry.py" "$ROOT/$REG" "$O/regen_${NAME}_before.json" "$O/regen_${NAME}_rows.json" --write
git -C "$ROOT" -c user.name=m -c user.email=m@x commit -q -am "D0b regen sim $NAME (measure only)"
echo "regen commit $(git -C "$ROOT" rev-parse HEAD)"
git -C "$ROOT" diff --stat HEAD~1 HEAD
bash "$K/run_plan.sh" "$ROOT" HEAD "$O/regen_${NAME}_after.json" "$MP"
"$PY" -B "$K/analyze_plan.py" "$O/regen_${NAME}_after.json" "$O/an_regen_${NAME}_after.json" "$O/regen_${NAME}_before.json"
git -C "$ROOT" checkout -q --detach "$REV"
