#!/usr/bin/env bash
# B33 착수 키트: 머리 수치 재측정(미도달 115→39, V3 쌍 ×1.31, 정적 인벤토리, 과거 판정 기록 V7 쌍 불변).
#   bash run_headline.sh <격리 복제본 루트(이력 포함, HEAD = 측정 커밋)> <출력 디렉터리>
# 복제본 HEAD 도구 = base 도구, 시제품 reachability_b33.py(fixed) = 개정 규칙(card 문장 구현, 측정용 -- code-author 산출물 아님).
# 결과는 출력 디렉터리에 단계마다 append(중간 실패해도 남김). 저장소 쓰기 없음.
set -euo pipefail
export HOME=/c/Users/HSLEE
export APPDATA=/c/Users/HSLEE/AppData/Roaming
export PYTHONIOENCODING=utf-8
K=$(cd "$(dirname "$0")" && pwd)
ROOT=$1
OUT=$2
PY=/c/Python314/python.exe
mkdir -p "$OUT"
test -d "$ROOT/.git"
echo "HEAD $(git -C "$ROOT" rev-parse HEAD)" > "$OUT/head.txt"
"$PY" -B "$K/m1_head.py" "$ROOT" "$OUT/m1.jsonl"
"$PY" -B "$K/m5_inventory.py" "$ROOT" "$ROOT/tools/gates/reachability.py" "$OUT/m5.json"
"$PY" -B "$K/m4_records.py" "$ROOT" "$OUT/m4.jsonl" "$ROOT/tools/gates/reachability.py"
echo done >> "$OUT/head.txt"
