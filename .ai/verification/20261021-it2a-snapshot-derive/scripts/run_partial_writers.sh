#!/bin/bash
set -u
S=C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_it2a_audit; OUT=$S/out/run4; PY=/c/Python314/python.exe
export APPDATA="C:\Users\HSLEE\AppData\Roaming"
mkdir -p $OUT
for c in folded_cascode two_stage_ota_sf; do
  $PY -I $S/scripts/measure_it2a_v3.py $S/b BASE $c library $OUT > $OUT/log_BASE_$c.txt 2>&1; echo "BASE $c rc=$?" >> $OUT/progress.txt
  $PY -I $S/scripts/measure_it2a_v3.py $S/h HEAD $c library $OUT > $OUT/log_HEAD_$c.txt 2>&1; echo "HEAD $c rc=$?" >> $OUT/progress.txt
done
echo DONE >> $OUT/progress.txt
