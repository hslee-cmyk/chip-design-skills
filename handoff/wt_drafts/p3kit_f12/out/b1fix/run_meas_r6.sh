#!/usr/bin/env bash
# F2 r6 재측정(6c724de 사슬 C:/g409/f). No cd. 결과는 C:/g409/out/*.txt에 케이스마다 쓴다.
set -u
export TMP=C:/g409/tmp TEMP=C:/g409/tmp APPDATA="C:/Users/HSLEE/AppData/Roaming" HOME="C:/Users/HSLEE" PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=C:/g409/tmp/pyc
R=C:/g409/f/r; PY=C:/Python314/python.exe; O=C:/g409/out; K=C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/p3kit_f12
B0=8324968
EXCL='^(\.ai/verification/|docs/03-analysis/gain-budget-gmid-sizing-function-audit/probe_stage_partition\.py$)'
A=skills/analog-gmid-design/assets/tests/contracts
[ -d /c/g409/gt/tools/gates ] || { mkdir -p /c/g409/gt && git -C "$R" archive 6c724de tools/gates | tar -x -C /c/g409/gt; }
cp -f "$K/test_p3_shim_delete.proto.py" "$O/test_p3sd_r6.py"; cp -f "$K/test_p3_shim_delete.proto.py.pre-r6.bak" "$O/test_p3sd_r3.py"
S="$O/summary.txt"; : > "$S"
for h in 5913897 a16b306 bf0ada2 a1a49c2 a760c78; do
  for e in ast exec; do
    "$PY" -B "$O/e3b_$e.py" "$R" "$B0" "$h" "$EXCL" > "$O/e3b_${e}_$h.txt" 2>&1; rc=$?
    echo "E3B[$e] $h rc=$rc $(grep -v '^E3b FAIL' "$O/e3b_${e}_$h.txt" | tr '\n' ' ') FAIL=$(grep -c '^E3b FAIL' "$O/e3b_${e}_$h.txt") files=$(grep '^E3b FAIL' "$O/e3b_${e}_$h.txt" | sed 's/^E3b FAIL //; s/:.*//' | sort -u | wc -l) b34=$(grep '^E3b FAIL' "$O/e3b_${e}_$h.txt" | grep -c b34)" >> "$S"
  done
  W="C:/g409/w_$h"
  [ -d "$W" ] || git -C "$R" worktree add -q --detach "$W" "$h"
  for v in r3 r6; do
    P3SD_KIT="$K" P3SD_ROOT="$W" P3SD_REPORT="$O/proto_${v}_unres_$h.txt" "$PY" -B -P -m pytest -q -p no:cacheprovider --rootdir="$O" "$O/test_p3sd_$v.py" > "$O/proto_${v}_$h.txt" 2>&1
    echo "PROTO[$v] $h rc=$? $(tail -1 "$O/proto_${v}_$h.txt") | $(head -1 "$O/proto_${v}_unres_$h.txt" 2>/dev/null) b34=$(grep -c b34 "$O/proto_${v}_unres_$h.txt" 2>/dev/null) errs=$(grep -c 'Error' "$O/proto_${v}_$h.txt")" >> "$S"
  done
done
for h in a16b306 a1a49c2 a760c78; do
  W="C:/g409/w_$h"
  PYTHONPATH=C:/g409/gt/tools/gates "$PY" -B -P -m pytest -c C:/g409/gt/tools/gates/pytest_gate.ini --rootdir="$W" --confcutdir="$W" \
    "$W/$A/test_b34_grammar_explicit.py" --gmid-phase=3 -q -p no:cacheprovider > "$O/b34_$h.txt" 2>&1
  echo "B34 $h rc=$? $(tail -1 "$O/b34_$h.txt") attrerr=$(grep -c "^E *AttributeError: module 'stick_diagram' has no attribute" "$O/b34_$h.txt") c8fail=$(grep -c '^FAILED .*test_b34_c8' "$O/b34_$h.txt")" >> "$S"
done
cat "$S"
