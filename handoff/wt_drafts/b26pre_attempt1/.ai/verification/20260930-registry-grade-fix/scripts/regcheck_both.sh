#!/usr/bin/env bash
# 병합본 reg_check 도구를 병합본·base 레지스트리에 돌린다(출력 C:/g11/out/regcheck_<m|base>.txt)
RC=C:/g11/m/skills/analog-gmid-design/assets/tests/tools/reg_check.py
REG=docs/03-analysis/gain-budget-gmid-sizing.function-registry.md
for n in m base; do
  PYTHONDONTWRITEBYTECODE=1 C:/Python314/python.exe -P $RC --registry C:/g11/$n/$REG --root C:/g11/$n > C:/g11/out/regcheck_$n.txt 2>&1
  echo "$n exit $?"
done
