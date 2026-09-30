#!/usr/bin/env bash
C=C:/g17/gmid-gate-cache/cd6417026696091fd0ce02603a11a3729af3147e
which git > C:/g17/o7/spy_env.txt; git --version >> C:/g17/o7/spy_env.txt; env | grep -iE '^(PATH|PYTHON|GIT|HOME|TMP|TEMP)' >> C:/g17/o7/spy_env.txt
PYTHONDONTWRITEBYTECODE=1 C:/Python314/python.exe C:/g17/probe/c3b_no_failing.py C:/g17/o7/spy_tool.py $C/pytest_gate.ini C:/g17/o7/spy_c3b2.json > C:/g17/o7/spy_c3b2.txt 2>&1
