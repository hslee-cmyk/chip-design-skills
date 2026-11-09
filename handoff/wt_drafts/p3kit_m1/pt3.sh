#!/usr/bin/env bash
# scratch: PT3 (design 30 §10 -- PT with --gmid-phase=3) on tree $1, label $2, gates cache $3, out $4
set -u
T="$1"; L="$2"; C="$3"; O="$4"
export APPDATA="C:/Users/HSLEE/AppData/Roaming" HOME="C:/Users/HSLEE" TMP=/c/g200/tmp TEMP=/c/g200/tmp
PC="$(mktemp -d)"
start=$(date +%s)
PYTHONPATH="$C" PYTHONPYCACHEPREFIX="$PC" C:/Python314/python.exe -P -m pytest -c "$C/pytest_gate.ini" \
  --rootdir="$T" --confcutdir="$T" "$T/skills/analog-gmid-design/assets/tests" --gmid-phase=3 \
  -q -p no:cacheprovider --junitxml="$O/$L.pt3.junit.xml" > "$O/$L.pt3.txt" 2>&1
rc=$?
echo "exit=$rc seconds=$(( $(date +%s) - start ))" >> "$O/$L.pt3.txt"
