#!/bin/bash
# IT-2a 전체 suite(--run-slow), 단위별 순차(lut 는 파일별). 인자: <clone 이름 h|b> <out 하위 이름>
set -u
S=C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_it2a_audit; PY=/c/Python314/python.exe
CL=$1; OUT=$S/out/$2; mkdir -p $OUT
export APPDATA="C:\Users\HSLEE\AppData\Roaming"
export PYTHONDONTWRITEBYTECODE=1
cd $S/$CL/skills/analog-gmid-design
UNITS="gmid_engine/tests/test_conftest_slow_marker.py"
for d in authoring convergence core generality graph integration layout metrics pipeline search sizing structure; do UNITS="$UNITS gmid_engine/tests/$d"; done
for f in gmid_engine/tests/lut/test_*.py; do UNITS="$UNITS $f"; done
for u in $UNITS; do
  n=$(echo $u | sed 's#gmid_engine/tests/##; s#/#_#g; s#\.py##')
  $PY -m pytest -p no:cacheprovider -q -rfE --tb=short --run-slow --junitxml=$OUT/junit_$n.xml $u > $OUT/log_$n.txt 2>&1
  echo "$u rc=$? $(tail -1 $OUT/log_$n.txt)" >> $OUT/summary.txt
done
echo DONE >> $OUT/summary.txt
