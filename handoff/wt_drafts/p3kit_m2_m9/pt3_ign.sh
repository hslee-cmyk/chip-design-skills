#!/usr/bin/env bash
# scratch measurement only: PT3 with the 3 unit selftests ignored (to see failures beyond the complete-shim collection errors)
set -u
T="$1"; L="$2"; C="$3"; O="$4"
export APPDATA="C:/Users/HSLEE/AppData/Roaming" HOME="C:/Users/HSLEE" TMP=/c/g200/tmp TEMP=/c/g200/tmp
PC="$(mktemp -d)"; U="$T/skills/analog-gmid-design/assets/tests/unit"
start=$(date +%s)
PYTHONPATH="$C" PYTHONPYCACHEPREFIX="$PC" C:/Python314/python.exe -P -m pytest -c "$C/pytest_gate.ini" \
  --rootdir="$T" --confcutdir="$T" "$T/skills/analog-gmid-design/assets/tests" --gmid-phase=3 \
  --ignore="$U/test_selftest_topology_library.py" --ignore="$U/test_selftest_design_report.py" --ignore="$U/test_selftest_sizing_recipe.py" \
  -q -p no:cacheprovider -rf --junitxml="$O/$L.pt3.junit.xml" > "$O/$L.pt3.txt" 2>&1
rc=$?
echo "exit=$rc seconds=$(( $(date +%s) - start ))" >> "$O/$L.pt3.txt"
