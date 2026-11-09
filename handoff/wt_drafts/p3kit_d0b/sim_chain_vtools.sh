#!/usr/bin/env bash
# D0b card V3·V4·V5·V6·V7 모양 사전 점검(측정 전용): 복제본에 base(D0a 대역) -> test 커밋 -> code 커밋(재생성 + 보류 3->4) 사슬을 만들고
# base 판 게이트(G1 시제품 설치본)로 도구를 돌린다.
#   bash sim_chain_vtools.sh <복제본 루트> <시작 rev> <interface card> <출력 디렉터리>
set -u
export APPDATA="C:/Users/HSLEE/AppData/Roaming" HOME="C:/Users/HSLEE" PYTHONIOENCODING=utf-8
ROOT=$1; START=$2; CARD=$3; OUT=$4
case "$ROOT" in C:/g162/*) ;; *) echo "scratch must be under C:/g162"; exit 2;; esac
K=C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/p3kit_d0b
PY=C:/Python314/python.exe
A=skills/analog-gmid-design/assets
REG=docs/03-analysis/gain-budget-gmid-sizing.function-registry.md
G="git -C $ROOT -c user.name=m -c user.email=m@x"
mkdir -p "$OUT"
git -C "$ROOT" checkout -q --detach "$START"
# base: D0a 대역(시제품을 tools/migrate/move_plan.py로)
mkdir -p "$ROOT/tools/migrate" && cp C:/g162/tmp/move_plan_proto.py "$ROOT/tools/migrate/move_plan.py"
git -C "$ROOT" add tools/migrate/move_plan.py && $G commit -q -m "D0a stand-in (measure only)"
B=$(git -C "$ROOT" rev-parse HEAD)
# test 커밋: 시제품 test를 실제 위치·경로로
"$PY" -B - "$K/test_p3_registry_dest.proto.py" "$ROOT/$A/tests/contracts/test_p3_registry_dest.py" <<'PYEOF'
import sys
t = open(sys.argv[1], encoding="utf-8").read()
t = t.replace('_ROOT = pathlib.Path(os.environ["P3RD_ROOT"])', '_ROOT = pathlib.Path(__file__).resolve().parents[5]')
t = t.replace('_TOOL = os.environ["P3RD_TOOL"]', '_TOOL = str(_ROOT / "tools" / "migrate" / "move_plan.py")')
open(sys.argv[2], "w", encoding="utf-8", newline="\n").write(t)
PYEOF
git -C "$ROOT" add "$A/tests/contracts/test_p3_registry_dest.py" && $G commit -q -m "test: D0b proto (measure only)"
T=$(git -C "$ROOT" rev-parse HEAD)
# code 커밋: 재생성 + 보류(Phase 3) -> 보류(Phase 4)
V_KEEP=0 V_A6=0 V_LIFT=0 bash "$K/run_plan.sh" "$ROOT" HEAD "$OUT/chain_plan_T.json" C:/g162/tmp/move_plan_proto.py
"$PY" -B "$K/regen_registry.py" "$ROOT/$REG" "$OUT/chain_plan_T.json" "$OUT/chain_rows.json" --write
sed -i 's/보류(Phase 3)/보류(Phase 4)/g' "$ROOT/$REG"
git -C "$ROOT" add "$REG" && $G commit -q -m "code: D0b regen sim (measure only)"
H=$(git -C "$ROOT" rev-parse HEAD)
echo "B=$B T=$T H=$H" | tee "$OUT/chain.txt"
GC=C:/g162/gc; rm -rf "$GC"; mkdir -p "$GC"; git -C "$ROOT" archive "$B" tools/gates | tar -x -C "$GC"; C="$GC/tools/gates"
for t in weakening_diff source_lint reachability; do
  s=$(date +%s); PYTHONPATH=$C "$PY" -B "$C/$t.py" --root "$ROOT" --base "$B" --head "$H" > "$OUT/v_$t.json" 2>&1; echo "$t exit $? $(( $(date +%s)-s ))s"
done
s=$(date +%s); PYTHONPATH=$C "$PY" -B "$C/test_lint.py" --root "$ROOT" --base "$B" --head "$H" --interface-card "$CARD" > "$OUT/v_test_lint.json" 2>&1; echo "test_lint exit $? $(( $(date +%s)-s ))s"
s=$(date +%s); PYTHONPATH=$C "$PY" -B "$C/mutate_changed.py" --root "$ROOT" --base "$B" --head "$H" --pytest-ini "$C/pytest_gate.ini" \
  --python C:/Python314/python.exe --gmid-phase=3 --gmid-strict= --out "$OUT/v3.jsonl" > "$OUT/v_mutate_changed.json" 2>&1; echo "mutate_changed exit $? $(( $(date +%s)-s ))s"
git -C "$ROOT" checkout -q --detach "$START"
