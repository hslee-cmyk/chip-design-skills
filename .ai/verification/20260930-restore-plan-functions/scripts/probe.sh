#!/usr/bin/env bash
# 격리 사전 검사: $1=복제본 이름(iso|base), $2=태그, $3..=추가 pytest 인자(없으면 전체 tests). 판정 명령 + -p iso_probe.
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
B=04c72481a8903c53e861ef7eb2895ffca53838d3
C=C:/g13/gmid-gate-cache/$B
R=C:/g13/$1; TAG=$2; shift 2
TGT=${1:-$R/skills/analog-gmid-design/assets/tests}
rm -rf C:/g13/pyc_probe_$TAG; mkdir -p C:/g13/pyc_probe_$TAG
ISO_PROBE_OUT=C:/g13/out/probe_$TAG.json ISO_PROBE_ROOT=$R ISO_PROBE_MAIN=C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills \
PYTHONPYCACHEPREFIX=C:/g13/pyc_probe_$TAG PYTHONPATH="$C;C:/g13/scripts" C:/Python314/python.exe -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R -p iso_probe --gmid-phase=2 --gmid-strict= $TGT -q -p no:cacheprovider > C:/g13/out/probe_$TAG.txt 2>&1
echo "probe_$TAG exit $?" >> C:/g13/out/status.txt
