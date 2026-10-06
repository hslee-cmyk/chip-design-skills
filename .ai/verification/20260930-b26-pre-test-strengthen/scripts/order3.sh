#!/usr/bin/env bash
# 순서 3: 새 test 파일 단독(seed 0·1) + V3 mutate_changed 1회. 출력은 C:/g371/out/.
set -uo pipefail
export APPDATA=C:/Users/HSLEE/AppData/Roaming HOME=C:/Users/HSLEE PYTHONIOENCODING=utf-8
export TMP=C:/g371/tmp TEMP=C:/g371/tmp TMPDIR=C:/g371/tmp
B=ae1b5886e6fd4b5b18d6096d8ac6076259719ff3
T=e4d5833f89a9a96db7410ce4bfc53703f4f9ef3f
C=C:/g371/gmid-gate-cache/$B
PY=C:/Python314/python.exe
R=C:/g371/iso
F=$R/skills/analog-gmid-design/assets/tests/contracts/test_b26pre_existing_paths.py
mkdir -p C:/g371/out
for seed in 0 1; do
  rm -rf C:/g371/pyc/new_$seed; mkdir -p C:/g371/pyc/new_$seed
  PYTHONHASHSEED=$seed PYTHONPYCACHEPREFIX=C:/g371/pyc/new_$seed PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R $F --gmid-phase=3 --gmid-strict= -rA -p no:cacheprovider --basetemp=C:/g371/tmp/bt_$seed > C:/g371/out/new_seed$seed.txt 2>&1
  echo "new_seed$seed exit $?" >> C:/g371/out/status.txt
done
if [ "${1:-}" = v3 ]; then
  s=$(date +%s)
  PYTHONPYCACHEPREFIX=C:/g371/pyc/v3 $PY -B $C/mutate_changed.py --root $R --base $B --head $T --pytest-ini $C/pytest_gate.ini --python $PY --gmid-phase=3 --gmid-strict= --out C:/g371/out/v3.jsonl > C:/g371/out/v3_stdout.txt 2>&1
  echo "v3 exit $? $(( $(date +%s)-s ))s" >> C:/g371/out/status.txt
fi
