#!/bin/bash
# IT-2b green(h = edffaa1c) 바뀐 test 파일 다섯 + D 변형 재실행(m = edffaa1c).
set -u
S=C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_it2b_audit; PY=/c/Python314/python.exe
export APPDATA="C:\\Users\\HSLEE\\AppData\\Roaming"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONIOENCODING=utf-8
FILES="gmid_engine/tests/search/test_fd_jacobian.py gmid_engine/tests/sizing/test_block_columns.py gmid_engine/tests/sizing/test_input_window.py gmid_engine/tests/sizing/test_output_structure.py gmid_engine/tests/sizing/test_s2_values.py"
OUT=$S/out/rg_h2; mkdir -p $OUT
cd $S/h/skills/analog-gmid-design
for f in $FILES; do
  n=$(basename $f .py)
  if grep -qF "DONE $f " $OUT/summary.txt 2>/dev/null; then continue; fi
  $PY -m pytest -p no:cacheprovider -q -rfE --tb=short --run-slow --junitxml=$OUT/$n.xml $f > $OUT/$n.txt 2>&1
  echo "DONE $f rc=$? | $(tail -1 $OUT/$n.txt)" >> $OUT/summary.txt
done
rm -f $S/out/mutate_d2.jsonl
$PY -I $S/scripts/mutate_d.py $S/m $S/out/mutate_d2.jsonl > $S/out/mutate_d2.log 2>&1
echo ALL_DONE >> $OUT/summary.txt
