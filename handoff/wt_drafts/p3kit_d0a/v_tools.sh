#!/usr/bin/env bash
# D0a card(20260930-p3-move-plan-tool) V3·V4·V5·V6·V7 모양 사전 점검 -- 격리 복제본에서만(측정 전용).
#   bash v_tools.sh <복제본 루트> <base sha> <head sha> <게이트 캐시 tools/gates> <interface card 파일> <출력 디렉터리>
# card phase 3 → --gmid-phase=3. V4: interface card의 `move_plan | main` 행(`*` 행은 test_lint가 뺀다) + --module-dir tools/migrate
# (선례 20260922-ts1-extract-tool V4 -- `--module-dir .`·`tools.migrate.extract_selftest:main` 꼴. 여기서는 card 표 그대로 쓰려고 tools/migrate).
set -u
ROOT=$1; BASE=$2; HEAD=$3; C=$4; CARD=$5; OUT=$6
export APPDATA='C:\Users\HSLEE\AppData\Roaming' PYTHONIOENCODING=utf-8
PY=/c/Python314/python.exe
mkdir -p "$OUT"
for t in weakening_diff source_lint reachability; do
  s=$(date +%s)
  PYTHONPATH=$C $PY -B $C/$t.py --root "$ROOT" --base "$BASE" --head "$HEAD" > "$OUT/$t.json" 2>&1
  echo "$t exit $? $(( $(date +%s)-s ))s"
done
s=$(date +%s)
PYTHONPATH=$C $PY -B $C/test_lint.py --root "$ROOT" --base "$BASE" --head "$HEAD" --interface-card "$CARD" --module-dir tools/migrate > "$OUT/test_lint.json" 2>&1
echo "test_lint exit $? $(( $(date +%s)-s ))s"
s=$(date +%s)
PYTHONPATH=$C $PY -B $C/mutate_changed.py --root "$ROOT" --base "$BASE" --head "$HEAD" --pytest-ini $C/pytest_gate.ini \
  --python C:/Python314/python.exe --gmid-phase=3 --gmid-strict= --out "$OUT/v3.jsonl" > "$OUT/mutate_changed.json" 2>&1
echo "mutate_changed exit $? $(( $(date +%s)-s ))s"
