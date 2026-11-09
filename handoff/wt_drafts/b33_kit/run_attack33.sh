#!/usr/bin/env bash
# B33 착수 키트: 공격 33 측정용 케이스(gen_attack33.py -- card 계약 문장에서 만든 기대값)를 base 도구와 시제품(fixed)에 돌려
# card '판정 유형 근거' 표(30단계: red 12 + 거부 13 + known_limit 1 + 대조군·면제 4; 시제품 30/30 PASS)를 다시 본다.
#   bash run_attack33.sh <원본 저장소> <커밋> <scratch 디렉터리(없어야 함)> <출력 jsonl> [시제품 변형 목록, 기본 fixed]
#   예) VARIANTS 자리에 fixed,xout,bare,draft,loose,nosuper -- 잘못된 구현 시제품(reachability_b33.py _V 표)도 같은 단계에 돌린다.
# 경로 주의(review3 m4): scratch·출력·저장소 경로는 `C:/...` 형식으로 준다. MSYS 형식(`/c/...`)을 주면
#   run_redteam_variants.py의 Windows Python subprocess(cwd=...)가 NotADirectoryError로 죽는다.
# 실행 시간(2026-10-01 실측, C:/g138): 복제 2벌 + base 1회 약 2.5분, 변형 1개당 약 2~2.5분 -- base + 변형 6개 958초.
#   변형을 더 넣거나 동시 측정이 있으면 harness 기본 background 한도(30분)에 가까워지니 timeout을 늘려 background로 돌린다.
#   (run_headline.sh의 m4 과거 V7 쌍 29개는 따로 약 40분 -- review3 실측.)
# scratch 안에 복제본 두 벌(base = 커밋 그대로, head = 커밋 + 시제품 reachability.py)을 만들고 그 안에서만 실행한다.
set -euo pipefail
export HOME=/c/Users/HSLEE
export APPDATA=/c/Users/HSLEE/AppData/Roaming
export PYTHONIOENCODING=utf-8
K=$(cd "$(dirname "$0")" && pwd)
SRC=$1; REV=$2; S=$3; OUT=$4; VARIANTS=${5:-fixed}
PY=/c/Python314/python.exe
test ! -e "$S"
mkdir -p "$S/tmp"
export TMP="$S/tmp" TEMP="$S/tmp"
for v in base head; do
  git clone -c core.autocrlf=false -q --no-hardlinks --no-local --no-checkout "$SRC" "$S/$v"
  git -C "$S/$v" remote remove origin
  git -C "$S/$v" config core.hooksPath "$S/nohooks"
  git -C "$S/$v" checkout -q -B master "$REV"
  "$PY" -B "$K/gen_attack33.py" "$S/$v/tools/gates/redteam/attacks/33-v7-registry-edges"
done
mkdir -p "$S/nohooks"
cp "$K/reachability_b33.py" "$S/head/tools/gates/reachability.py"
"$PY" -B "$K/run_redteam_variants.py" "$OUT" "$S/base:-" "$S/head:$VARIANTS" -- --phase 0.5 --mode direct --only 33-v7-registry-edges
