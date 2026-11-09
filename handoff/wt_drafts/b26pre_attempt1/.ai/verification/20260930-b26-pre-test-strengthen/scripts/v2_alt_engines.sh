#!/usr/bin/env bash
# V2 ⑤: T의 새 test 파일 하나를 B34 전 엔진(dd60db6 archive)·backfill 정리 모의 base(C4B archive)에서 seed 0·1로 실행.
set -uo pipefail
export APPDATA=C:/Users/HSLEE/AppData/Roaming HOME=C:/Users/HSLEE PYTHONIOENCODING=utf-8
export TMP=C:/g342/tmp TEMP=C:/g342/tmp TMPDIR=C:/g342/tmp
B=6c724debd884dd1d31034f5279ae450f35e67fc4
C=C:/g342/gmid-gate-cache/$B
PY=C:/Python314/python.exe
for n in pre34 c4b; do
  R=C:/g342/$n
  for seed in 0 1; do
    rm -rf C:/g342/pyc/alt_${n}_$seed; mkdir -p C:/g342/pyc/alt_${n}_$seed
    PYTHONHASHSEED=$seed PYTHONPYCACHEPREFIX=C:/g342/pyc/alt_${n}_$seed PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R $R/skills/analog-gmid-design/assets/tests/contracts/test_b26pre_existing_paths.py --gmid-phase=3 --gmid-strict= -rA -p no:cacheprovider > C:/g342/out/alt_${n}_seed$seed.txt 2>&1
    echo "alt_${n}_seed$seed exit $? $(tail -n 1 C:/g342/out/alt_${n}_seed$seed.txt)" >> C:/g342/out/status_alt.txt
  done
done
