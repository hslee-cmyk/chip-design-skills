#!/bin/bash
# IT-2a 9회로 측정: BASE(d3bdbd39) / HEAD(5517c8b4) / HEAD 둘째(결정성), 순차 실행
set -u
S=C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_it2a_audit; OUT=$S/out/run; PY=/c/Python314/python.exe
export APPDATA="C:\Users\HSLEE\AppData\Roaming"
LIB="common_gate_amplifier current_reuse_telescopic_ota folded_cascode ngcc_3stage_ff nmcnr_amplifier pushpull_follower_buffer sf_pushpull_output_opamp two_stage_ota two_stage_ota_sf"
mkdir -p $OUT
for c in $LIB; do
  $PY -I $S/scripts/measure_it2a.py $S/b BASE $c library $OUT > $OUT/log_BASE_$c.txt 2>&1; echo "BASE $c rc=$?" >> $OUT/progress.txt
  $PY -I $S/scripts/measure_it2a.py $S/h HEAD $c library $OUT > $OUT/log_HEAD_$c.txt 2>&1; echo "HEAD $c rc=$?" >> $OUT/progress.txt
  $PY -I $S/scripts/measure_it2a.py $S/h HEAD $c library $OUT --tag _rep2 > $OUT/log_HEADrep2_$c.txt 2>&1; echo "HEADrep2 $c rc=$?" >> $OUT/progress.txt
done
echo DONE >> $OUT/progress.txt
