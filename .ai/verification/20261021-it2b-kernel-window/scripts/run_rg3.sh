#!/bin/bash
# IT-2b 최종 red-green: r(56080584 엔진 + dc334fef test 파일), f(c4506f47 엔진 + dc334fef test 파일), h(dc334fef) -- 바뀐 test 파일 다섯, 파일 하나당 프로세스 하나.
set -u
S=C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_it2b_audit; PY=/c/Python314/python.exe
export APPDATA="C:\\Users\\HSLEE\\AppData\\Roaming"
export PYTHONDONTWRITEBYTECODE=1
FILES="gmid_engine/tests/search/test_fd_jacobian.py gmid_engine/tests/sizing/test_block_columns.py gmid_engine/tests/sizing/test_input_window.py gmid_engine/tests/sizing/test_output_structure.py gmid_engine/tests/sizing/test_s2_values.py"
for CL in r f h; do
  OUT=$S/out/rg3_$CL; mkdir -p $OUT
  cd $S/$CL/skills/analog-gmid-design
  for f in $FILES; do
    n=$(basename $f .py)
    if grep -qF "DONE $f " $OUT/summary.txt 2>/dev/null; then continue; fi
    $PY -m pytest -p no:cacheprovider -q -rfE --tb=short --run-slow --junitxml=$OUT/$n.xml $f > $OUT/$n.txt 2>&1
    echo "DONE $f rc=$? | $(tail -1 $OUT/$n.txt)" >> $OUT/summary.txt
  done
done
echo ALL_DONE >> $S/out/rg3_h/summary.txt
