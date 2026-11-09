#!/usr/bin/env bash
# backfill card library 계측 -- base(BP 트리 = a796468+B34+b26pre 시제품)와 fix(H 트리) 사본에서 lib_measure.py.
#   bash run_lib.sh <circuit...>   (elib는 항상 먼저)  결과: C:/g128/out/lib_<copy>_<what>.json
set -euo pipefail
export HOME=/c/Users/HSLEE APPDATA=/c/Users/HSLEE/AppData/Roaming PYTHONIOENCODING=utf-8 PYTHONHASHSEED=0
K=C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/b26bf_kit
for c in base fix; do
  C:/Python314/python.exe -B "$K/lib_measure.py" C:/g128/lib/$c elib C:/g128/out/lib_${c}_elib.json > C:/g128/out/lib_${c}_elib.log 2>&1 &
done
wait
for circ in "$@"; do
  for c in base fix; do
    C:/Python314/python.exe -B "$K/lib_measure.py" C:/g128/lib/$c einst "$circ" C:/g128/out/lib_${c}_${circ}.json > C:/g128/out/lib_${c}_${circ}.log 2>&1 &
  done
  wait
done
echo done
