#!/usr/bin/env bash
# V2 ⑤: T의 새 test 파일 하나를 B34 전 엔진(dd60db6 archive)·backfill 정리 모의 base(C4B archive)에서 seed 0·1로 실행.
set -uo pipefail
export APPDATA=C:/Users/HSLEE/AppData/Roaming HOME=C:/Users/HSLEE PYTHONIOENCODING=utf-8
export TMP=C:/g372/tmp TEMP=C:/g372/tmp TMPDIR=C:/g372/tmp
B=ae1b5886e6fd4b5b18d6096d8ac6076259719ff3
C=C:/g372/gmid-gate-cache/$B
PY=C:/Python314/python.exe
for n in pre34 c4b; do
  R=C:/g372/$n
  for seed in 0 1; do
    rm -rf C:/g372/pyc/alt_${n}_$seed; mkdir -p C:/g372/pyc/alt_${n}_$seed
    PYTHONHASHSEED=$seed PYTHONPYCACHEPREFIX=C:/g372/pyc/alt_${n}_$seed PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R $R/skills/analog-gmid-design/assets/tests/contracts/test_b26pre_existing_paths.py --gmid-phase=3 --gmid-strict= -rA -p no:cacheprovider > C:/g372/out/alt_${n}_seed$seed.txt 2>&1
    echo "alt_${n}_seed$seed exit $? $(tail -n 1 C:/g372/out/alt_${n}_seed$seed.txt)" >> C:/g372/out/status_alt.txt
  done
done
