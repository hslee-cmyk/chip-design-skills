#!/usr/bin/env bash
# Phase 4 design v0.8 measurement (review4 B1/S1): HEAD git-archive clone, read-only on the repo.
# Usage: bash p4v08_measure.sh <repo> <scratch>   (scratch is created and must be deleted afterwards)
set -e
R=$1; S=$2
mkdir -p $S/iso $S/cache $S/pyc
git -C $R rev-parse --short HEAD
git -C $R archive HEAD | tar -x -C $S/iso
cp -r $S/iso/tools/gates/. $S/cache/
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
T=$S/iso/skills/analog-gmid-design/assets/tests
PT4(){ PYTHONPATH=$S/cache PYTHONPYCACHEPREFIX=$S/pyc C:/Python314/python.exe -B -P -m pytest -c $S/cache/pytest_gate.ini --rootdir=$S/iso --confcutdir=$S/iso "$@" --gmid-phase=4 -p no:cacheprovider; }
for opt in "" "--gmid-dod"; do echo "=== opt=[$opt]"; PT4 $T/contracts/test_ic11.py $opt -rA -q 2>&1 | tail -8 || true; done
echo "== contracts -k legacy"; PT4 $T/contracts -k legacy --collect-only -q 2>&1 | tail -4 || true
echo "== tests -k lut_axis"; PT4 $T -k lut_axis --collect-only -q 2>&1 | tail -4 || true
echo "== all"; PT4 $T --collect-only -q 2>&1 | tail -2 || true
