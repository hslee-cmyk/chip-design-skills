#!/usr/bin/env bash
# 사용: run_rt.sh <복제본> <tmp> <태그>  -- base 게이트(복제본 tools/gates = dd60db6 판)로 redteam 전체 + --cases 0.5
set -uo pipefail
R=$1; T=$2; TAG=$3; O=/c/g186/out/rt_$TAG.txt
export APPDATA=C:/Users/HSLEE/AppData/Roaming TEMP=$T TMP=$T TMPDIR=$T PYTHONDONTWRITEBYTECODE=1
cd "$R" || exit 9
{
echo "start_full $(date -Iseconds)"
C:/Python314/python.exe tools/gates/redteam/run_all.py --phase 0.5 --mode direct --repo "$R" > /c/g186/out/rt_${TAG}_full.stdout 2>&1
echo "exit_full $?"
echo "end_full $(date -Iseconds)"
C:/Python314/python.exe tools/gates/redteam/run_all.py --cases 0.5 --mode direct --repo "$R" > /c/g186/out/rt_${TAG}_cases.stdout 2>&1
echo "exit_cases $?"
echo "end_cases $(date -Iseconds)"
ls -t "$R"/tools/gates/redteam/logs/
} > "$O" 2>&1
