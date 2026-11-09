#!/usr/bin/env bash
# measure only: real V3 (G1 proto gate) on M9 -> M10 prototype (with prototype test). args: <base> <head> <label>
export TMP=C:/g323/tmp TEMP=C:/g323/tmp APPDATA="C:/Users/HSLEE/AppData/Roaming" HOME="C:/Users/HSLEE" PYTHONIOENCODING=utf-8
R=C:/g323/r; GC=C:/g323/cache/tools/gates; B="$1"; H="$2"; L="$3"
rm -f "C:/g323/out/${L}.jsonl"
s=$(date +%s)
C:/Python314/python.exe -B "$GC/mutate_changed.py" --root $R --base "$B" --head "$H" --pytest-ini "$GC/pytest_gate.ini" \
  --out "C:/g323/out/${L}.jsonl" --gmid-phase=3 --gmid-strict= > "C:/g323/out/${L}.json" 2> "C:/g323/out/${L}.err"
echo "exit=$? seconds=$(( $(date +%s)-s ))" > "C:/g323/out/${L}.done"
