#!/usr/bin/env bash
# FU spec card '작성 전 실측' -- PT3(design 30 §10 PT3 정의) 전체를 base·FU 두 트리에서 실행하고 junit를 남긴다.
# 인자: <tree> <label> <cache tools/gates 경로> <out dir>. 결과는 <out>/<label>.pt3.junit.xml·<label>.pt3.txt(append 아님 -- 실행마다 새 파일).
set -u
T="$1"; L="$2"; C="$3"; O="$4"
export APPDATA="C:/Users/HSLEE/AppData/Roaming" HOME="C:/Users/HSLEE"
PC="$(mktemp -d)"
cd "$T" || exit 9
start=$(date +%s)
PYTHONPATH="$C" PYTHONPYCACHEPREFIX="$PC" C:/Python314/python.exe -P -m pytest -c "$C/pytest_gate.ini" \
  --rootdir="$T" --confcutdir="$T" "$T/skills/analog-gmid-design/assets/tests" --gmid-phase=3 \
  -q -p no:cacheprovider --junitxml="$O/$L.pt3.junit.xml" > "$O/$L.pt3.txt" 2>&1
rc=$?
echo "exit=$rc seconds=$(( $(date +%s) - start ))" >> "$O/$L.pt3.txt"
