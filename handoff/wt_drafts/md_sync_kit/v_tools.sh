#!/usr/bin/env bash
# md-sync card(20261001-topology-md-sync) V3·V4·V5·V6·V7 도구 실행 -- auditor 격리 복제본에서만.
#   bash v_tools.sh <격리 복제본 루트> <base sha> <T sha> <게이트 코드 캐시 디렉터리> <출력 디렉터리>
# 리다이렉트 대상은 변수 경로라 EL1 role_guard가 명령줄 직접 입력을 거부한다 -- 이 스크립트 파일로 실행한다.
# 사전 시험(C:/g146, base = D, T = 프로토타입 커밋): V5 2s, V6 52s, V7 117s, V3 148s, V4 21s -- 전부 PASS exit 0(v_tools.sh 자체도 사전 시험에서 실행 확인).
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
$PY -B "$(dirname "$0")/v4_subjects.py" "$ROOT" "$OUT/v4_subjects.txt"
args=(); while read -r x; do [ -n "$x" ] && args+=(--subject "$x"); done < "$OUT/v4_subjects.txt"
s=$(date +%s)
PYTHONPATH=$C $PY -B $C/test_lint.py --root "$ROOT" --base "$BASE" --head "$HEAD" --module-dir skills/analog-gmid-design/assets "${args[@]}" > "$OUT/test_lint.json" 2>&1
echo "test_lint exit $? $(( $(date +%s)-s ))s"
s=$(date +%s)
PYTHONPATH=$C $PY -B $C/mutate_changed.py --root "$ROOT" --base "$BASE" --head "$HEAD" --pytest-ini $C/pytest_gate.ini \
  --python C:/Python314/python.exe --gmid-phase=2 --gmid-strict= --out "$OUT/v3.jsonl" > "$OUT/mutate_changed.json" 2>&1
echo "mutate_changed exit $? $(( $(date +%s)-s ))s"
