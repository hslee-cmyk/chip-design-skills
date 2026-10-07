# usage: bash run.sh <clone_root> <label> <seed> [extra pytest target args...]
set -euo pipefail
ROOT=$1; LABEL=$2; SEED=$3; shift 3
C=C:/g393/gmid-gate-cache/863a037cc0d774bb984006ea39966c5e4dd741ab
OUT=C:/g393/out
mkdir -p $OUT C:/g393/bt C:/g393/pyc_$LABEL C:/g393/tmp
export APPDATA=C:/Users/HSLEE/AppData/Roaming HOME=C:/Users/HSLEE PYTHONIOENCODING=utf-8
export TMP=C:/g393/tmp TEMP=C:/g393/tmp TMPDIR=C:/g393/tmp
export PYTHONHASHSEED=$SEED
export PYTHONPYCACHEPREFIX=C:/g393/pyc_$LABEL
export PYTHONPATH=$C
export GMID_RED_CAPTURE=$OUT/red_$LABEL.jsonl
export GMID_INTERFACE_CARD=$ROOT/docs/02-design/specs/20261001-b26-backfill-interdig-final-audit.interface.md
rm -f $GMID_RED_CAPTURE
if [ $# -eq 0 ]; then TGT=$ROOT/skills/analog-gmid-design/assets/tests; else TGT="$*"; fi
set +e
C:/Python314/python.exe -P -m pytest -c $C/pytest_gate.ini --rootdir=$ROOT --confcutdir=$ROOT \
  --gmid-phase=3 --gmid-strict= -p merge_gate --continue-on-collection-errors \
  --basetemp=C:/g393/bt/$LABEL -p no:cacheprovider -rfE -q $TGT > $OUT/pytest_$LABEL.txt 2>&1
rc=$?
set -e
echo "rc=$rc" >> $OUT/pytest_$LABEL.txt
tail -n 3 $OUT/pytest_$LABEL.txt
