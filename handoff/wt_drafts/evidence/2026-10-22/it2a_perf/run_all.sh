#!/usr/bin/env bash
# IT-2a 소급 측정 -- 순차 실행 (메모리 부족 전례). 결과는 perf.jsonl 에 케이스마다 append.
set -e
export APPDATA="C:\\Users\\HSLEE\\AppData\\Roaming"
S=C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_it2a_perf
E=C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-10-22/it2a_perf
PY=/c/Python314/python.exe
for mode in ${MODES:-profile plain}; do
  for c in ${CIRCUITS:-folded_cascode two_stage_ota}; do
    for side in base head; do
      echo "$(date +%T) start $mode $c $side" >> $E/progress.txt
      $PY -I $E/perf.py $S/$side $side $c $mode $E > $E/log_${side}_${c}_${mode}.txt 2>&1 || echo "$(date +%T) FAIL $mode $c $side rc=$?" >> $E/progress.txt
      echo "$(date +%T) done $mode $c $side" >> $E/progress.txt
    done
  done
done
