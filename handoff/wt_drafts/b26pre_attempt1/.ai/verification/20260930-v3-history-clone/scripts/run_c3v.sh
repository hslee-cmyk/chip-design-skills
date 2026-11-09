#!/usr/bin/env bash
# 계약 3 변형 b·c를 병합본 도구와 base 도구로
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
C=C:/g17/gmid-gate-cache/cd6417026696091fd0ce02603a11a3729af3147e
PY=C:/Python314/python.exe
O=C:/g17/o7
PYTHONDONTWRITEBYTECODE=1 $PY C:/g17/probe/make_c3_variants.py
for v in c3b_no_failing c3c_failing_last; do
  PYTHONDONTWRITEBYTECODE=1 $PY C:/g17/probe/$v.py C:/g17/isom/tools/gates/mutate_changed.py $C/pytest_gate.ini $O/${v}_m.json > $O/${v}_m.txt 2>&1
  echo "$v merged exit $?" >> $O/status.txt
  PYTHONDONTWRITEBYTECODE=1 $PY C:/g17/probe/$v.py $C/mutate_changed.py $C/pytest_gate.ini $O/${v}_base.json > $O/${v}_base.txt 2>&1
  echo "$v base exit $?" >> $O/status.txt
done
