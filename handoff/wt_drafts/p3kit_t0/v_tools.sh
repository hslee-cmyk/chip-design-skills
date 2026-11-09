#!/usr/bin/env bash
# T0 card(20260930-p3-tests-location-free) V3·V4·V5·V6·V7 모양 사전 점검 -- 격리 복제본에서만(측정 전용).
#   bash v_tools.sh <복제본 루트(T 커밋 checkout)> <base sha> <T sha> <게이트 캐시 tools/gates> <출력 디렉터리> [interface card]
# --subject 373 방식은 진단용(판정 입력 아님 -- 공식 V4는 --interface-card 단독, 브리프 3.2). r2t 뒤 이 방식은 기존 줄의 FAIL을 낸다(공허 아님의 증거).
# 게이트 캐시 = `git archive <gate master> tools/gates`를 푼 것. card phase 3 → --gmid-phase=3(V1과 같은 값, design 30 §10 PT3).
# V4: interface card 신규 시그니처 0행(test-only) -- md_sync_kit/v4_subjects.py와 같은 처리(A/*.py 최상위 def·class 전부를 --subject로).
set -u
ROOT=$1; BASE=$2; HEAD=$3; C=$4; OUT=$5
export APPDATA='C:\Users\HSLEE\AppData\Roaming' PYTHONIOENCODING=utf-8
PY=/c/Python314/python.exe
mkdir -p "$OUT"
for t in weakening_diff source_lint reachability; do
  s=$(date +%s)
  PYTHONPATH=$C $PY -B $C/$t.py --root "$ROOT" --base "$BASE" --head "$HEAD" > "$OUT/$t.json" 2>&1
  echo "$t exit $? $(( $(date +%s)-s ))s"
done
$PY -B C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/md_sync_kit/v4_subjects.py "$ROOT" "$OUT/v4_subjects.txt"
# r2t(2026-10-02, review_t0_fu B1): v4_subjects.py(write_text)는 Windows에서 CRLF를 쓴다 -- `read -r`가 `\r`을 남겨
# subject 373개가 하나도 맞지 않아 findings가 전부 NO-SUBJECT(공허 PASS)였다. `\r`을 떼고, 개수를 출력해 공허를 드러낸다.
args=(); while read -r x; do x=${x%$'\r'}; [ -n "$x" ] && args+=(--subject "$x"); done < "$OUT/v4_subjects.txt"
case "${args[*]}" in *$'\r'*) echo "[중단] subject에 CR이 남았다" >&2; exit 2;; esac
echo "v4 subjects $(( ${#args[@]} / 2 ))"
s=$(date +%s)
PYTHONPATH=$C $PY -B $C/test_lint.py --root "$ROOT" --base "$BASE" --head "$HEAD" --module-dir skills/analog-gmid-design/assets "${args[@]}" > "$OUT/test_lint.json" 2>&1
echo "test_lint exit $? $(( $(date +%s)-s ))s"
# 공식 V4 입력(--interface-card 단독 -- 브리프 3.2 V4 행)도 함께 잰다: 6번째 인자 = interface card 경로(없으면 생략).
if [ -n "${6:-}" ]; then
  s=$(date +%s)
  PYTHONPATH=$C $PY -B $C/test_lint.py --root "$ROOT" --base "$BASE" --head "$HEAD" --interface-card "$6" > "$OUT/test_lint_iface.json" 2>&1
  echo "test_lint(iface) exit $? $(( $(date +%s)-s ))s"
fi
s=$(date +%s)
PYTHONPATH=$C $PY -B $C/mutate_changed.py --root "$ROOT" --base "$BASE" --head "$HEAD" --pytest-ini $C/pytest_gate.ini \
  --python C:/Python314/python.exe --gmid-phase=3 --gmid-strict= --out "$OUT/v3.jsonl" > "$OUT/mutate_changed.json" 2>&1
echo "mutate_changed exit $? $(( $(date +%s)-s ))s"
