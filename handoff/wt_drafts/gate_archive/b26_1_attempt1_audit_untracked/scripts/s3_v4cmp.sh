#!/usr/bin/bash
set -euo pipefail
A=C:/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-b26-rail-accessor-set-audit
B1=6df4bd7fd9920e752da4b16bff9b0513caf78362
T1=c247a7697fad8f4695a89d6c9fd0683b900e86fd
ID=20260930-b26-rail-accessor-set
O=$A/.ai/verification/$ID/out
SC=$A/.ai/verification/$ID/scripts
S=C:/g412
C=$S/gmid-gate-cache/$B1
export TMP=$S/tmp TEMP=$S/tmp TMPDIR=$S/tmp PYTHONPYCACHEPREFIX=$S/pycache
C:/Python314/python.exe $SC/v4_compare.py $C $S/iso $B1 $T1 $S/iso/docs/02-design/specs/$ID.interface.md \
  $O/order3_v4_test_lint.json $O/order3_v4_compare.json $O/order3_v4_test_lint_B1files.json > $O/order3_v4_compare.txt
cat $O/order3_v4_compare.txt
