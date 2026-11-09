#!/usr/bin/env bash
# B33 착수 키트: 공격 33 측정용 케이스(gen_attack33.py -- card 계약 문장에서 만든 기대값)를 base 도구와 시제품(fixed)에 돌려
# card '판정 유형 근거' 표(base 13 FAIL = red 12 + registry-reexport-other 목록, 시제품 26/26 PASS)를 다시 본다.
#   bash run_attack33.sh <원본 저장소> <커밋> <scratch 디렉터리(없어야 함)> <출력 jsonl>
# scratch 안에 복제본 두 벌(base = 커밋 그대로, head = 커밋 + 시제품 reachability.py)을 만들고 그 안에서만 실행한다.
set -euo pipefail
export HOME=/c/Users/HSLEE
export APPDATA=/c/Users/HSLEE/AppData/Roaming
export PYTHONIOENCODING=utf-8
K=$(cd "$(dirname "$0")" && pwd)
SRC=$1; REV=$2; S=$3; OUT=$4
PY=/c/Python314/python.exe
test ! -e "$S"
mkdir -p "$S/tmp"
export TMP="$S/tmp" TEMP="$S/tmp"
for v in base head; do
  git clone -q --no-hardlinks --no-local --no-checkout "$SRC" "$S/$v"
  git -C "$S/$v" remote remove origin
  git -C "$S/$v" config core.hooksPath "$S/nohooks"
  git -C "$S/$v" checkout -q -B master "$REV"
  "$PY" -B "$K/gen_attack33.py" "$S/$v/tools/gates/redteam/attacks/33-v7-registry-edges"
done
mkdir -p "$S/nohooks"
cp "$K/reachability_b33.py" "$S/head/tools/gates/reachability.py"
"$PY" -B "$K/run_redteam_variants.py" "$OUT" "$S/base:-" "$S/head:fixed" -- --phase 0.5 --mode direct --only 33-v7-registry-edges
