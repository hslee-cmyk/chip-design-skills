#!/usr/bin/env bash
# 계약 11 무동작 미리보기: 게이트 V3·V4·V6·V7 도구를 실행하거나 reachability를 import하는 기존 redteam 케이스를 한 복제본에서 돌린다.
#   bash run_noop.sh <scratch C:/g<n>> <복제본(b|p2)> <이름표>
# 결과: g1_kit/out/noop_<이름표>.jsonl(run_all 로그 사본) + .txt. 판정은 auditor 몫 -- 이건 착수 전 미리보기.
set -euo pipefail
S="$1"; C="$2"; L="$3"
K=C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/g1_kit
PY=C:/Python314/python.exe
case "$S" in C:/g*) ;; *) echo "scratch must be C:/g<n>"; exit 2;; esac
mkdir -p "$S/tmp_$L"
export TMP="$S/tmp_$L" TEMP="$S/tmp_$L" TMPDIR="$S/tmp_$L" PYTHONIOENCODING=utf-8
set +e
"$PY" -B "$S/$C/tools/gates/redteam/run_all.py" --phase 0.5 --mode direct --repo "$S/$C" \
  --only v3_survivor --only v7_unwired --only 06-v4 --only 07-v4 --only 09-v6 --only 23-v4 --only 26-gate-output \
  --only 27f-v6 --only 28-v3 --only 29-v4 --only 31-v3 > "$K/out/noop_$L.txt" 2>&1
rc=$?
set -e
LOG=$(ls -t "$S/$C/tools/gates/redteam/logs/"*-direct.jsonl | head -1)
cp "$LOG" "$K/out/noop_$L.jsonl"
echo "exit $rc log $LOG" >> "$K/out/noop_$L.txt"
