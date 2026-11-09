#!/usr/bin/bash
# 순서 3: strict_set, V5(weakening_diff), V4(test_lint), V3(mutate_changed, test-only 구간) -- base 판 도구, 복제본 안
set -euo pipefail
A=C:/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-b26-rail-accessor-set-audit
B1=6df4bd7fd9920e752da4b16bff9b0513caf78362
T1=c247a7697fad8f4695a89d6c9fd0683b900e86fd
ID=20260930-b26-rail-accessor-set
O=$A/.ai/verification/$ID/out
SC=$A/.ai/verification/$ID/scripts
S=C:/g412
C=$S/gmid-gate-cache/$B1
PY=C:/Python314/python.exe
ISO=$S/iso
export TMP=$S/tmp TEMP=$S/tmp TMPDIR=$S/tmp PYTHONPYCACHEPREFIX=$S/pycache
$PY $SC/strict_set.py $C $ISO $B1 $ID > $O/order3_strict_set.txt 2>&1 || echo "strict rc=$?" >> $O/order3_strict_set.txt
set +e
$PY $C/weakening_diff.py --root $ISO --base $B1 --head $T1 > $O/order3_v5_weakening_diff.json 2> $O/order3_v5_weakening_diff.err
echo "v5 rc=$?" > $O/order3_tools_rc.txt
$PY $C/test_lint.py --root $ISO --interface-card $ISO/docs/02-design/specs/$ID.interface.md --base $B1 --head $T1 > $O/order3_v4_test_lint.json 2> $O/order3_v4_test_lint.err
echo "v4 rc=$?" >> $O/order3_tools_rc.txt
echo done
