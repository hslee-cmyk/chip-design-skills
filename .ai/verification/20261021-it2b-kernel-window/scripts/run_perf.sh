#!/bin/bash
# IT-2b I-perf: perf_it2b.py 를 base(b @56080584)·head(h @c4eaa137) 에서 회로 둘(common_gate_amplifier, nmcnr_amplifier)에 순차 실행(재개).
set -u
S=C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_it2b_audit; PY=/c/Python314/python.exe
export APPDATA="C:\\Users\\HSLEE\\AppData\\Roaming"
export PYTHONDONTWRITEBYTECODE=1
OUT=$S/out/perf; P=$OUT/progress.txt; touch $P
for c in common_gate_amplifier nmcnr_amplifier; do
  for side in BASE:b HEAD:h; do
    s=${side%%:*}; cl=${side##*:}
    if grep -q "^$s $c rc=0" $P; then continue; fi
    $PY -I $S/scripts/perf_it2b.py $S/$cl $s $c $OUT/theta_$c.json $OUT/perf_${s}_$c.json --reps 7 > $OUT/log_${s}_$c.txt 2>&1
    echo "$s $c rc=$?" >> $P
  done
done
echo DONE >> $P
