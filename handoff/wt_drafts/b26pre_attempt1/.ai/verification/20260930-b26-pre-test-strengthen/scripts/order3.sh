#!/usr/bin/env bash
# 순서 3: 새 test 파일 단독(seed 0·1) + V3 mutate_changed 1회. 출력은 C:/g341/out/.
set -uo pipefail
export APPDATA=C:/Users/HSLEE/AppData/Roaming HOME=C:/Users/HSLEE PYTHONIOENCODING=utf-8
export TMP=C:/g341/tmp TEMP=C:/g341/tmp TMPDIR=C:/g341/tmp
B=6c724debd884dd1d31034f5279ae450f35e67fc4
T=d2b2ed71ce506b010e5d87c03add007069a5a322
C=C:/g341/gmid-gate-cache/$B
PY=C:/Python314/python.exe
R=C:/g341/iso
F=$R/skills/analog-gmid-design/assets/tests/contracts/test_b26pre_existing_paths.py
mkdir -p C:/g341/out
for seed in 0 1; do
  rm -rf C:/g341/pyc/new_$seed; mkdir -p C:/g341/pyc/new_$seed
  PYTHONHASHSEED=$seed PYTHONPYCACHEPREFIX=C:/g341/pyc/new_$seed PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R $F --gmid-phase=3 --gmid-strict= -rA -p no:cacheprovider > C:/g341/out/new_seed$seed.txt 2>&1
  echo "new_seed$seed exit $?" >> C:/g341/out/status.txt
done
if [ "${1:-}" = v3 ]; then
  s=$(date +%s)
  PYTHONPYCACHEPREFIX=C:/g341/pyc/v3 $PY -B $C/mutate_changed.py --root $R --base $B --head $T --pytest-ini $C/pytest_gate.ini --python $PY --gmid-phase=3 --gmid-strict= --out C:/g341/out/v3.jsonl > C:/g341/out/v3_stdout.txt 2>&1
  echo "v3 exit $? $(( $(date +%s)-s ))s" >> C:/g341/out/status.txt
fi
