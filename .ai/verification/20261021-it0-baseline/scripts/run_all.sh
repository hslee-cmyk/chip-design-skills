#!/bin/bash
# IT-0 전 회로 측정 실행기: AB·SIM(library 9 + heldout 4), AB 래퍼 없음(무해 확인), AB 둘째 실행(결정성 V4)
S=$(cd "$(dirname "$0")/.." && pwd); OUT="$S/out/run"; PY=/c/Python314/python.exe
LIB="common_gate_amplifier current_reuse_telescopic_ota folded_cascode ngcc_3stage_ff nmcnr_amplifier pushpull_follower_buffer sf_pushpull_output_opamp two_stage_ota two_stage_ota_sf"
HO="cnr_ota erfc_ota r2r_opamp rfc_ota"
mkdir -p "$OUT"
for c in $LIB; do
  for side in AB SIM; do repo="$S/it0-iso"; [ $side = SIM ] && repo="$S/it0-sim"
    $PY -I "$S/scripts/measure_it0.py" "$repo" $side $c library "$OUT" > "$OUT/log_${side}_$c.txt" 2>&1; echo "$side $c rc=$?" >> "$OUT/progress.txt"; done
done
for c in $HO; do for side in AB SIM; do repo="$S/it0-iso"; [ $side = SIM ] && repo="$S/it0-sim"
  $PY -I "$S/scripts/measure_it0.py" "$repo" $side $c heldout "$OUT" > "$OUT/log_${side}_$c.txt" 2>&1; echo "$side $c rc=$?" >> "$OUT/progress.txt"; done; done
for c in $LIB; do
  $PY -I "$S/scripts/measure_it0.py" "$S/it0-iso" AB $c library "$OUT" --nowrap --tag _nowrap > "$OUT/log_nowrap_$c.txt" 2>&1; echo "nowrap $c rc=$?" >> "$OUT/progress.txt"
  $PY -I "$S/scripts/measure_it0.py" "$S/it0-iso" AB $c library "$OUT" --tag _rep2 > "$OUT/log_rep2_$c.txt" 2>&1; echo "rep2 $c rc=$?" >> "$OUT/progress.txt"
  $PY -I "$S/scripts/measure_it0.py" "$S/it0-sim" SIM $c library "$OUT" --tag _rep2 > "$OUT/log_simrep2_$c.txt" 2>&1; echo "simrep2 $c rc=$?" >> "$OUT/progress.txt"
done
echo DONE >> "$OUT/progress.txt"
