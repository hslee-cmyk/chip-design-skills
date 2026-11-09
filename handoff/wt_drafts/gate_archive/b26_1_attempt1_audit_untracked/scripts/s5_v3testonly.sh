#!/usr/bin/bash
# V3(test-only 구간): base 판 mutate_changed.py B1..T1 -- 기대 targets [](엔진 diff 0)
set -euo pipefail
A=C:/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-b26-rail-accessor-set-audit
B1=6df4bd7fd9920e752da4b16bff9b0513caf78362
T1=c247a7697fad8f4695a89d6c9fd0683b900e86fd
ID=20260930-b26-rail-accessor-set
O=$A/.ai/verification/$ID/out
S=C:/g412
C=$S/gmid-gate-cache/$B1
PY=C:/Python314/python.exe
mkdir -p $S/tmp_v3 $S/pycache_v3
export TMP=$S/tmp_v3 TEMP=$S/tmp_v3 TMPDIR=$S/tmp_v3 PYTHONPYCACHEPREFIX=$S/pycache_v3
set +e
$PY $C/mutate_changed.py --root $S/iso --base $B1 --head $T1 --pytest-ini $C/pytest_gate.ini --python $PY \
  --gmid-phase=3 --gmid-strict= --out $O/order3_v3_testonly.json > $O/order3_v3_testonly.stdout.txt 2>&1
echo "rc=$?" >> $O/order3_v3_testonly.stdout.txt
cat $O/order3_v3_testonly.stdout.txt | head -c 3000
echo; head -c 3000 $O/order3_v3_testonly.json 2>/dev/null || true
