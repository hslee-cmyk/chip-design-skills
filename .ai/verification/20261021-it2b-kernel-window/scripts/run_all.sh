#!/bin/bash
# IT-2b 감사 측정: heldout 4(HEAD, OS 칸) -> library 9 회로마다 BASE(b @56080584) · PREFIX(f 엔진 @c4506f47) · HEAD(h @dc334fef) · HEAD_rep2(h) 순차.
# 재개: progress_runs.txt 에 '<side> <circuit> rc=0' 이 있으면 건너뜀.
set -u
S=C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_it2b_audit; OUT=$S/out/run; PY=/c/Python314/python.exe
export APPDATA="C:\\Users\\HSLEE\\AppData\\Roaming"
export PYTHONDONTWRITEBYTECODE=1
mkdir -p $OUT
P=$OUT/progress_runs.txt; touch $P
one() {  # side clone circuit set tag
  key="$1$5 $3"
  if grep -q "^$key rc=0" $P; then return; fi
  $PY -I $S/scripts/measure_it2b.py $S/$2 $1 $3 $4 $OUT --tag "$5" > $OUT/log_$1$5_$3.txt 2>&1
  echo "$key rc=$?" >> $P
}
for c in cnr_ota erfc_ota r2r_opamp rfc_ota; do one HEAD h $c heldout ""; done
LIB="common_gate_amplifier current_reuse_telescopic_ota folded_cascode ngcc_3stage_ff nmcnr_amplifier pushpull_follower_buffer sf_pushpull_output_opamp two_stage_ota two_stage_ota_sf"
for c in $LIB; do
  one BASE b $c library ""
  one PREFIX f $c library ""
  one HEAD h $c library ""
  one HEAD h $c library _rep2
done
echo ALL_DONE >> $P
