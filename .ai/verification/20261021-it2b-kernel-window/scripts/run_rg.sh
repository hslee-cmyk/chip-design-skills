#!/bin/bash
# IT-2b red(r = 56080584 + head test 파일) / green(h = 4ed8aca4): 바뀐 test 파일 다섯, 파일 하나당 pytest 프로세스 하나, --run-slow.
set -u
S=C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_it2b_audit; PY=/c/Python314/python.exe
export APPDATA="C:\\Users\\HSLEE\\AppData\\Roaming"
export PYTHONDONTWRITEBYTECODE=1
FILES="gmid_engine/tests/search/test_fd_jacobian.py gmid_engine/tests/sizing/test_block_columns.py gmid_engine/tests/sizing/test_input_window.py gmid_engine/tests/sizing/test_output_structure.py gmid_engine/tests/sizing/test_s2_values.py"
for CL in r h; do
  OUT=$S/out/rg_$CL; mkdir -p $OUT
  cd $S/$CL/skills/analog-gmid-design
  for f in $FILES; do
    n=$(basename $f .py)
    if grep -qF "DONE $f " $OUT/summary.txt 2>/dev/null; then continue; fi
    $PY -m pytest -p no:cacheprovider -q -rfE --tb=short --run-slow --junitxml=$OUT/$n.xml $f > $OUT/$n.txt 2>&1
    echo "DONE $f rc=$? | $(tail -1 $OUT/$n.txt)" >> $OUT/summary.txt
  done
done
echo ALL_DONE >> $S/out/rg_h/summary.txt
