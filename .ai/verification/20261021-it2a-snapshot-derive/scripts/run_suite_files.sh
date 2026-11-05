#!/bin/bash
# IT-2a 전체 suite: tests 아래 test_*.py 파일 하나당 pytest 프로세스 하나, 순차, --run-slow. 재개 가능(summary 에 'DONE <파일>' 이 있으면 건너뜀).
# usage: bash run_suite_files.sh <clone h|b> <out 하위 이름> [파일 목록 파일(없으면 전부)]
set -u
S=C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_it2a_audit; PY=/c/Python314/python.exe
CL=$1; OUT=$S/out/$2; LIST=${3:-}
mkdir -p $OUT/junit $OUT/logs
export APPDATA="C:\\Users\\HSLEE\\AppData\\Roaming"
export PYTHONDONTWRITEBYTECODE=1
cd $S/$CL/skills/analog-gmid-design
if [ -n "$LIST" ]; then FILES=$(cat $LIST); else FILES=$(find gmid_engine/tests -name 'test_*.py' | sort); fi
touch $OUT/summary.txt
for f in $FILES; do
  if grep -qF "DONE $f " $OUT/summary.txt; then continue; fi
  n=$(echo $f | sed 's#gmid_engine/tests/##; s#/#__#g; s#\.py$##')
  $PY $S/scripts/run_one.py $OUT/junit/$n.xml $f > $OUT/logs/$n.txt 2>&1
  rc=$?
  res=$(grep -E "passed|failed|error|no tests ran|deselected" $OUT/logs/$n.txt | tail -1)
  mem=$(grep "^RUN_ONE" $OUT/logs/$n.txt | tail -1)
  echo "DONE $f rc=$rc | $res | $mem" >> $OUT/summary.txt
done
echo "ALL_DONE" >> $OUT/summary.txt
