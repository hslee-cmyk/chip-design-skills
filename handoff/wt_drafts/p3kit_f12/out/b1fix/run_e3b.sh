#!/usr/bin/env bash
# design 30 §10 E3B_AST (6c724de design, verbatim) on old F2 mock da36b86 / fixed F2 mock 35d83ca. B0 = G1 50298e3. No cd.
export TMP=C:/g347/tmp TEMP=C:/g347/tmp
C:/Python314/python.exe -B C:/g347/extract_e3b.py
EXCL='^(\.ai/verification/|docs/03-analysis/gain-budget-gmid-sizing-function-audit/probe_stage_partition\.py$)'
for h in da36b86 35d83ca; do
  C:/Python314/python.exe -B C:/g347/out/e3b_ast.py C:/g347/f/r 50298e3 "$h" "$EXCL" > "C:/g347/out/e3b_$h.txt" 2>&1
  echo "== $h rc=$? $(grep -v '^E3b FAIL' "C:/g347/out/e3b_$h.txt" | tr '\n' ' ') FAIL=$(grep -c '^E3b FAIL' "C:/g347/out/e3b_$h.txt") b34=$(grep '^E3b FAIL' "C:/g347/out/e3b_$h.txt" | grep -c b34)"
done
