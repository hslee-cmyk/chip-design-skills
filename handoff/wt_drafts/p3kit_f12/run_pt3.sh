#!/usr/bin/env bash
# F1/F2 작성 전 실측(측정 전용) -- design 30 §10 PT3(PT에서 --gmid-phase=3)을 worktree 하나에서 전체 실행하고 junit를 남긴다(fu_pt3.sh와 같은 명령).
#   bash run_pt3.sh <worktree> <label> <cache tools/gates> <out dir>
set -u
T="$1"; L="$2"; C="$3"; O="$4"
case "$T" in C:/g202/*) ;; *) echo "worktree must be under C:/g202"; exit 2;; esac
export APPDATA="C:/Users/HSLEE/AppData/Roaming" HOME="C:/Users/HSLEE" TMP=C:/g202/tmp TEMP=C:/g202/tmp
PC="$(mktemp -d -p C:/g202/tmp)"
cd "$T" || exit 9
start=$(date +%s)
PYTHONPATH="$C" PYTHONPYCACHEPREFIX="$PC" C:/Python314/python.exe -P -m pytest -c "$C/pytest_gate.ini" \
  --rootdir="$T" --confcutdir="$T" "$T/skills/analog-gmid-design/assets/tests" --gmid-phase=3 \
  -q -p no:cacheprovider --junitxml="$O/$L.pt3.junit.xml" > "$O/$L.pt3.txt" 2>&1
rc=$?
echo "exit=$rc seconds=$(( $(date +%s) - start ))" >> "$O/$L.pt3.txt"
