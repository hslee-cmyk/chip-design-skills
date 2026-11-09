#!/bin/bash
cd "$(dirname "$0")"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="C:/Users/HSLEE/AppData/Roaming/Python/Python314/site-packages"
for c in common_gate_amplifier current_reuse_telescopic_ota folded_cascode ngcc_3stage_ff nmcnr_amplifier pushpull_follower_buffer sf_pushpull_output_opamp two_stage_ota two_stage_ota_sf; do
  echo "start $c $(date +%T)" >> driver.log
  python run_one.py $c >> "log_$c.txt" 2>&1
  echo "end $c rc=$? $(date +%T)" >> driver.log
done
echo ALLDONE >> driver.log
