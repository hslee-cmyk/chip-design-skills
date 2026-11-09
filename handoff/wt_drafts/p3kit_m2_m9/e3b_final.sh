#!/usr/bin/env bash
# scratch: E3b-form (design §10 E3B_AST with module substituted) base B -> final chain head, new FAILs only (vs base self-compare)
export PYTHONIOENCODING=utf-8 TMP=/c/g200/tmp TEMP=/c/g200/tmp
ISO=$1; B=$2; HF=$3; O=/c/g200/out
EXCL='^(\.ai/verification/|docs/03-analysis/gain-budget-gmid-sizing-function-audit/probe_stage_partition\.py$)'
for m in sizing_recipe topology_library design_report stick_diagram audit_current_forced; do
 echo "== $m"
 C:/Python314/python.exe -B /c/g200/tools/e3b_$m.py "$ISO" $B $B "$EXCL" | tr -d '\r' | grep "FAIL" | sort > $O/e3b_${m}_bb.txt
 C:/Python314/python.exe -B /c/g200/tools/e3b_$m.py "$ISO" $B $HF "$EXCL" | tr -d '\r' > $O/e3b_${m}_final.txt
 head -1 $O/e3b_${m}_final.txt; echo "new FAIL: $(grep FAIL $O/e3b_${m}_final.txt | sort | comm -23 - $O/e3b_${m}_bb.txt | wc -l)"
 grep FAIL $O/e3b_${m}_final.txt | sort | comm -23 - $O/e3b_${m}_bb.txt | head -12
done
