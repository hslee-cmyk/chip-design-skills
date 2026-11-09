#!/bin/bash
# 사본(C:/g60/base, git archive 7535799) 전체 test 1회: junit(test별 시간) + 실행 줄 합집합(covplug).
set -u
cd /c/g60/base
export PYTHONPATH="C:/g60/scripts;C:/Users/HSLEE/AppData/Roaming/Python/Python314/site-packages" PYTHONDONTWRITEBYTECODE=1 COVPLUG_OUT=C:/g60/out/executed_lines.json
C:/Python314/python.exe -P -m pytest -c tools/gates/pytest_gate.ini --rootdir=. --confcutdir=. -q -p no:cacheprovider \
  -p covplug --gmid-phase=2 --gmid-strict= --junitxml=C:/g60/out/junit_base.xml > /c/g60/out/pytest_full.txt 2>&1
echo "exit $?" >> /c/g60/out/pytest_full.txt
