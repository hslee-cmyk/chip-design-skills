#!/usr/bin/env bash
# V4 (1) 발견이 기존 test의 것인지: base·병합본 같은 파일에 --subject sizing_recipe:optimize_multistage
C=C:/g10/gmid-gate-cache/efbf14a4908c27bc1e5481a5cde91b0cca57a693; export APPDATA="C:/Users/HSLEE/AppData/Roaming"
F=skills/analog-gmid-design/assets/tests/unit/test_selftest_sizing_recipe.py
for R in base m; do
  PYTHONPYCACHEPREFIX=C:/g10/pyc_t_v4x C:/Python314/python.exe $C/test_lint.py --root C:/g10/$R --subject sizing_recipe:optimize_multistage $F > C:/g10/out/tool_V4_om_$R.txt 2>&1
  echo "$R exit $?"
done
