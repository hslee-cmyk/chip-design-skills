#!/usr/bin/env bash
# backfill card V3 -- 현재 도구(gate master 0f23786 판 mutate_changed.py, archive 사본 C:/g128/gate0)를 모의 사슬 BP..H에 실제로 돌린다.
#   bash run_v3_tool.sh <base> <head> <label>   결과: C:/g128/out/v3tool_<label>.{jsonl,json,log}
set -euo pipefail
export HOME=/c/Users/HSLEE APPDATA=/c/Users/HSLEE/AppData/Roaming PYTHONIOENCODING=utf-8
export TMP=C:/g128/tmp TEMP=C:/g128/tmp
B=$1; H=$2; L=$3
G=C:/g128/gate0/tools/gates
O=C:/g128/out/v3tool_$L
rm -f "$O.jsonl"
t0=$(date +%s)
rc=0
C:/Python314/python.exe -B "$G/mutate_changed.py" --root C:/g128/sim/r --base "$B" --head "$H" --pytest-ini "$G/pytest_gate.ini" \
  --python C:/Python314/python.exe --gmid-phase=2 --gmid-strict= --out "$O.jsonl" > "$O.json" 2> "$O.err" || rc=$?
echo "exit=$rc elapsed_s=$(( $(date +%s) - t0 ))" > "$O.log"
