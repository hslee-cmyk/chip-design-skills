#!/bin/bash
# IT-2a 재측정(v2 하네스, 지문 칸 포함): 회로마다 BASE(b @d3bdbd39) -> HEAD(h @314387bb) 순차, two_stage_ota_sf 는 HEAD_rep2 추가
set -u
S=C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_it2a_audit; OUT=$S/out/run2; PY=/c/Python314/python.exe
export APPDATA="C:\Users\HSLEE\AppData\Roaming"
LIB="two_stage_ota_sf common_gate_amplifier current_reuse_telescopic_ota folded_cascode ngcc_3stage_ff nmcnr_amplifier pushpull_follower_buffer sf_pushpull_output_opamp two_stage_ota"
mkdir -p $OUT
for c in $LIB; do
  $PY -I $S/scripts/measure_it2a_v2.py $S/b BASE $c library $OUT > $OUT/log_BASE_$c.txt 2>&1; echo "BASE $c rc=$?" >> $OUT/progress.txt
  $PY -I $S/scripts/measure_it2a_v2.py $S/h HEAD $c library $OUT > $OUT/log_HEAD_$c.txt 2>&1; echo "HEAD $c rc=$?" >> $OUT/progress.txt
  if [ $c = two_stage_ota_sf ]; then
    $PY -I $S/scripts/measure_it2a_v2.py $S/h HEAD $c library $OUT --tag _rep2 > $OUT/log_HEADrep2_$c.txt 2>&1; echo "HEADrep2 $c rc=$?" >> $OUT/progress.txt
  fi
done
echo DONE >> $OUT/progress.txt
