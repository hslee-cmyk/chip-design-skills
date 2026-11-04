#!/bin/bash
# IT-2a 셋째 판: 9회로 HEAD(h @5f35b8f3) v2 하네스, 순차. BASE 는 run2/BASE 재사용(엔진 base 불변).
set -u
S=C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_it2a_audit; OUT=$S/out/run3; PY=/c/Python314/python.exe
export APPDATA="C:\Users\HSLEE\AppData\Roaming"
LIB="common_gate_amplifier current_reuse_telescopic_ota folded_cascode ngcc_3stage_ff nmcnr_amplifier pushpull_follower_buffer sf_pushpull_output_opamp two_stage_ota two_stage_ota_sf"
mkdir -p $OUT
for c in $LIB; do
  if grep -q "^HEAD $c rc=0" $OUT/progress.txt 2>/dev/null; then continue; fi
  $PY -I $S/scripts/measure_it2a_v2.py $S/h HEAD $c library $OUT > $OUT/log_HEAD_$c.txt 2>&1; echo "HEAD $c rc=$?" >> $OUT/progress.txt
done
echo DONE >> $OUT/progress.txt
