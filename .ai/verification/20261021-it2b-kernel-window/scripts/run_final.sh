#!/bin/bash
# IT-2b 감사 마무리(순차, 재개 가능). 단계 1 red-green(r·f·h, 바뀐 test 파일 다섯) -> 단계 2 측정(HEAD2 = h @c4eaa137 9회로 + HEAD2_rep2 9회로,
# two_stage_ota_sf BASE·PREFIX·HEAD(m @dc334fef 엔진 615ef68b)) -> 단계 3 전체 suite(h, test 파일 하나당 프로세스 하나, --run-slow).
set -u
S=C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_it2b_audit; PY=/c/Python314/python.exe
export APPDATA="C:\\Users\\HSLEE\\AppData\\Roaming"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONIOENCODING=utf-8
# ---- 1
FILES="gmid_engine/tests/search/test_fd_jacobian.py gmid_engine/tests/sizing/test_block_columns.py gmid_engine/tests/sizing/test_input_window.py gmid_engine/tests/sizing/test_output_structure.py gmid_engine/tests/sizing/test_s2_values.py"
for CL in r f h; do
  OUT=$S/out/rg4_$CL; mkdir -p $OUT
  cd $S/$CL/skills/analog-gmid-design
  for f in $FILES; do
    n=$(basename $f .py)
    if grep -qF "DONE $f " $OUT/summary.txt 2>/dev/null; then continue; fi
    $PY -m pytest -p no:cacheprovider -q -rfE --tb=short --run-slow --junitxml=$OUT/$n.xml $f > $OUT/$n.txt 2>&1
    echo "DONE $f rc=$? | $(tail -1 $OUT/$n.txt)" >> $OUT/summary.txt
  done
done
# ---- 2
OUT=$S/out/run; P=$OUT/progress_runs.txt; touch $P
one() {  # side clone circuit tag
  key="$1$4 $3"
  if grep -q "^$key rc=0" $P; then return; fi
  $PY -I $S/scripts/measure_it2b.py $S/$2 $1 $3 library $OUT --tag "$4" > $OUT/log_$1$4_$3.txt 2>&1
  echo "$key rc=$?" >> $P
}
LIB="common_gate_amplifier current_reuse_telescopic_ota folded_cascode nmcnr_amplifier pushpull_follower_buffer sf_pushpull_output_opamp two_stage_ota two_stage_ota_sf ngcc_3stage_ff"
for c in $LIB; do one HEAD2 h $c ""; done
one BASE b two_stage_ota_sf ""
one PREFIX f two_stage_ota_sf ""
one HEAD m two_stage_ota_sf ""
for c in $LIB; do one HEAD2 h $c _rep2; done
echo "STAGE2_DONE" >> $P
# ---- 3
OUT=$S/out/suite; mkdir -p $OUT/junit $OUT/logs; touch $OUT/summary.txt
cd $S/h/skills/analog-gmid-design
for f in $(find gmid_engine/tests -name 'test_*.py' -not -path '*/fixtures/*' | sort); do
  if grep -qF "DONE $f " $OUT/summary.txt; then continue; fi
  n=$(echo $f | sed 's#gmid_engine/tests/##; s#/#__#g; s#\.py$##')
  $PY $S/scripts/run_one.py $OUT/junit/$n.xml $f > $OUT/logs/$n.txt 2>&1
  rc=$?
  res=$(grep -E "passed|failed|error|no tests ran|deselected" $OUT/logs/$n.txt | tail -1)
  mem=$(grep "^RUN_ONE" $OUT/logs/$n.txt | tail -1)
  echo "DONE $f rc=$rc | $res | $mem" >> $OUT/summary.txt
done
echo "ALL_DONE" >> $OUT/summary.txt
