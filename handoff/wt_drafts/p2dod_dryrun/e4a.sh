#!/bin/bash
# E4(a) dry run: PT2 and PT2 --gmid-dod at H, sequential, clean before each.
set -uo pipefail
export APPDATA="C:/Users/HSLEE/AppData/Roaming" HOME="C:/Users/HSLEE"
G=C:/g112; ISO=$G/iso; O=$G/out; PY=C:/Python314/python.exe
H=0f237862c007f6a53122f2bdfb3c87e6366ec133; CACHE=$G/cache_$H/tools/gates
PT2() { PYTHONPATH=$CACHE PYTHONPYCACHEPREFIX=$(mktemp -d -p $G/pyc) $PY -P -m pytest -c $CACHE/pytest_gate.ini --rootdir=$ISO --confcutdir=$ISO $ISO/skills/analog-gmid-design/assets/tests --gmid-phase=2 "$@"; }
git -C $ISO checkout -- workspaces ; git -C $ISO clean -fdxq
echo "pre1 status lines: $(git -C $ISO status --porcelain --ignored | wc -l)" >> $O/e4a_times.txt
s=$(date +%s); PT2 -q --color=no > $O/e4_pt2.txt 2>&1; rc=$?; echo "pt2 exit=$rc $(( $(date +%s)-s ))s" >> $O/e4a_times.txt
echo "post1 status:" >> $O/e4a_times.txt; git -C $ISO status --porcelain --ignored >> $O/e4a_times.txt
git -C $ISO checkout -- workspaces ; git -C $ISO clean -fdxq
s=$(date +%s); PT2 --gmid-dod -q --color=no > $O/e4_pt2_dod.txt 2>&1; rc=$?; echo "pt2dod exit=$rc $(( $(date +%s)-s ))s" >> $O/e4a_times.txt
echo "post2 status:" >> $O/e4a_times.txt; git -C $ISO status --porcelain --ignored >> $O/e4a_times.txt
echo DONE >> $O/e4a_times.txt
