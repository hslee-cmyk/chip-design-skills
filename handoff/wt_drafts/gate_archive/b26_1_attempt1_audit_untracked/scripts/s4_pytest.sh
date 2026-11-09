#!/usr/bin/bash
# 전체 suite 실행. env: TAG(이름), CLONE(복제본 루트), SEED(PYTHONHASHSEED), RED(1이면 -p merge_gate 수집)
set -euo pipefail
A=C:/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-b26-rail-accessor-set-audit
B1=6df4bd7fd9920e752da4b16bff9b0513caf78362
ID=20260930-b26-rail-accessor-set
O=$A/.ai/verification/$ID/out
S=C:/g412
C=$S/gmid-gate-cache/$B1
PY=C:/Python314/python.exe
mkdir -p $S/tmp_$TAG $S/pycache_$TAG
export TMP=$S/tmp_$TAG TEMP=$S/tmp_$TAG TMPDIR=$S/tmp_$TAG PYTHONPYCACHEPREFIX=$S/pycache_$TAG PYTHONHASHSEED=$SEED PYTHONPATH=$C
ARGS=(-P -m pytest -c $C/pytest_gate.ini --rootdir=$CLONE --confcutdir=$CLONE --gmid-phase=3 --gmid-strict= -q -rA)
if [ "$RED" = 1 ]; then
  export GMID_RED_CAPTURE=$S/red_$TAG.jsonl GMID_INTERFACE_CARD=$CLONE/docs/02-design/specs/$ID.interface.md
  : > $GMID_RED_CAPTURE
  ARGS+=(-p merge_gate --continue-on-collection-errors)
fi
ARGS+=($CLONE/skills/analog-gmid-design/assets/tests)
echo "cmd: PYTHONHASHSEED=$SEED PYTHONPATH=$C $PY ${ARGS[*]}" > $O/pytest_$TAG.cmd.txt
set +e
$PY "${ARGS[@]}" > $O/pytest_$TAG.out.txt 2>&1
echo "rc=$?" >> $O/pytest_$TAG.cmd.txt
if [ "$RED" = 1 ]; then cp $S/red_$TAG.jsonl $O/red_$TAG.jsonl; fi
tail -3 $O/pytest_$TAG.out.txt
