#!/usr/bin/env bash
# scratch: design 30 §10 E3 / E3b (verbatim python) and the same E3b expression generalised to every split module; IMPORT-ANY verbatim.
set -u
export TMP=/c/g200/tmp TEMP=/c/g200/tmp APPDATA="C:/Users/HSLEE/AppData/Roaming" HOME="C:/Users/HSLEE" PYTHONIOENCODING=utf-8
ISO=C:/g200/r; B0=$1; HD=$2; TREE_B=$3; TREE_H=$4; L=$5
PY="C:/Python314/python.exe -B"; O=/c/g200/out; T=/c/g200/tools
GC=C:/g200/cache/tools/gates
EXCL='^(\.ai/verification/|docs/03-analysis/gain-budget-gmid-sizing-function-audit/probe_stage_partition\.py$)'
. $T/mpargs.sh
for rev in "$B0" "$HD"; do
  $PY $T/e3_ast.py "$ISO" "$rev" | tr -d '\r' > $T/../out/e3_$L.$rev.txt; echo "E3 rev=$rev rc=${PIPESTATUS[0]} stmt=$(grep -c '^stmt ' $T/../out/e3_$L.$rev.txt) call=$(grep -c '^call ' $T/../out/e3_$L.$rev.txt) outside_excl=$(sed 's/^[A-Za-z-]* //; s/:[0-9]*$//' $T/../out/e3_$L.$rev.txt | sort -u | grep -v -E "$EXCL" | grep -c .)"
done
for m in stick_diagram sizing_recipe topology_library design_report audit_current_forced; do
  sed "s/stick_diagram/$m/g" $T/e3b_ast.py > $T/e3b_$m.py
  echo "== E3b-form module=$m"
  $PY $T/e3b_$m.py "$ISO" "$B0" "$HD" "$EXCL" | tr -d '\r' | head -20; echo "rc=${PIPESTATUS[0]}"
done
. $T/import_any_fn.sh
for tr in "$TREE_B" "$TREE_H"; do echo "== IMPORT-ANY $tr"; import_any "$tr"; echo "import_any rc=$?"; done
