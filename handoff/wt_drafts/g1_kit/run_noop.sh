#!/usr/bin/env bash
# 계약 11 무동작 미리보기: 게이트 V3·V4·V6·V7 도구를 실행하거나 reachability를 import하는 기존 redteam 케이스를 한 복제본에서 돌린다.
#   bash run_noop.sh <scratch C:/g<n>> <복제본(b|p2)> <이름표> [--only <케이스 앞부분>]... [--no-default]
#   기본 11케이스(아래 DEFAULT)에 --only로 준 케이스를 더한다(여러 번 줄 수 있음, 예: --only 33- --only 34- --only 35-).
#   --no-default면 기본 11케이스를 빼고 --only로 준 것만 돌린다(--only가 하나도 없으면 거부).
# 결과: g1_kit/out/noop_<이름표>.jsonl(run_all 로그 사본) + .txt. 판정은 auditor 몫 -- 이건 착수 전 미리보기.
set -euo pipefail
[ $# -ge 3 ] || { echo "usage: run_noop.sh <C:/g<n>> <복제본> <이름표> [--only X]... [--no-default]"; exit 2; }
S="$1"; C="$2"; L="$3"; shift 3
K=C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/g1_kit
PY=C:/Python314/python.exe
case "$S" in C:/g[0-9]*) ;; *) echo "scratch must be C:/g<n>"; exit 2;; esac
case "$C" in ""|.|*/*|*\\*) echo "복제본은 <scratch> 아래 이름 하나(b|p2 등): '$C'"; exit 2;; esac
case "$L" in ""|.|*/*|*\\*) echo "이름표는 경로 구분자 없는 이름: '$L'"; exit 2;; esac
DEFAULT=(v3_survivor v7_unwired 06-v4 07-v4 09-v6 23-v4 26-gate-output 27f-v6 28-v3 29-v4 31-v3)
EXTRA=(); USE_DEFAULT=1
while [ $# -gt 0 ]; do
  case "$1" in
    --only) [ $# -ge 2 ] && [ -n "$2" ] || { echo "--only 뒤에 케이스 이름이 없다"; exit 2; }; EXTRA+=("$2"); shift 2 ;;
    --no-default) USE_DEFAULT=0; shift ;;
    *) echo "모르는 인자: $1"; exit 2 ;;
  esac
done
CASES=()
[ "$USE_DEFAULT" = 1 ] && CASES+=("${DEFAULT[@]}")
CASES+=("${EXTRA[@]+"${EXTRA[@]}"}")
[ ${#CASES[@]} -gt 0 ] || { echo "--no-default인데 --only가 없다"; exit 2; }
ONLY=(); for x in "${CASES[@]}"; do ONLY+=(--only "$x"); done
mkdir -p "$S/tmp_$L"
export TMP="$S/tmp_$L" TEMP="$S/tmp_$L" TMPDIR="$S/tmp_$L" PYTHONIOENCODING=utf-8
# (pre-dafe) 자식 bash는 APPDATA·HOME·USERPROFILE을 잃는다 -> 없으면 V3 기준 실행의 pytest(사용자 site-packages)가 'No module named pytest'(exit 1)
#   -> BaselineFailed(exit 2). 옛 기준선(noop_base·noop_base_4a286f0·noop_*_a17b8bd)의 28·31·34·35·v3_survivor FAIL이 이것이었다(2026-10-06 실측).
export HOME=C:/Users/HSLEE USERPROFILE='C:\Users\HSLEE' APPDATA='C:\Users\HSLEE\AppData\Roaming' LOCALAPPDATA='C:\Users\HSLEE\AppData\Local'
"$PY" -B -c "import pytest" || { echo "[중단] $PY에서 pytest를 import하지 못한다(APPDATA·사용자 site-packages 확인)"; exit 2; }
set +e
"$PY" -B "$S/$C/tools/gates/redteam/run_all.py" --phase 0.5 --mode direct --repo "$S/$C" "${ONLY[@]}" > "$K/out/noop_$L.txt" 2>&1
rc=$?
set -e
LOG=$(ls -t "$S/$C/tools/gates/redteam/logs/"*-direct.jsonl | head -1)
cp "$LOG" "$K/out/noop_$L.jsonl"
echo "cases ${CASES[*]}" >> "$K/out/noop_$L.txt"
echo "exit $rc log $LOG" >> "$K/out/noop_$L.txt"
