#!/bin/bash
# Dry run: E1 discrimination @7535799, E4(c) @da03c0e, E4(d) @H. Times appended to $O/e4cd_times.txt
set -uo pipefail
export APPDATA="C:/Users/HSLEE/AppData/Roaming" HOME="C:/Users/HSLEE"
R=/c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills
G=C:/g112; ISO=$G/iso; O=$G/out; S=$G/scripts; PY=C:/Python314/python.exe
H=0f237862c007f6a53122f2bdfb3c87e6366ec133; T=$O/e4cd_times.txt
sw() { git -C $ISO checkout -- workspaces ; git -C $ISO clean -fdxq ; git -C $ISO checkout -q --detach $1 ; echo "switch $1 -> $(git -C $ISO rev-parse HEAD) status_lines=$(git -C $ISO status --porcelain --ignored | wc -l)" >> $T; }
mainchk() { git -C $R status --porcelain --ignored > $G/snap/main_$1.txt; if diff -q $G/snap/main_before.txt $G/snap/main_$1.txt >/dev/null; then echo "main status same ($1)" >> $T; else echo "MAIN STATUS CHANGED ($1)" >> $T; fi; }
run() { local n=$1; shift; local s=$(date +%s); "$@" > $O/$n.log 2>&1; echo "$n exit=$? $(( $(date +%s)-s ))s" >> $T; }

# E1 discrimination
sw 7535799
REV=7535799; mkdir -p $G/cache_$REV && git -C $ISO archive $REV tools/gates | tar -x -C $G/cache_$REV; CACHE=$G/cache_$REV/tools/gates
s=$(date +%s); PYTHONPATH=$CACHE PYTHONPYCACHEPREFIX=$(mktemp -d -p $G/pyc) $PY -P -m pytest -c $CACHE/pytest_gate.ini --rootdir=$ISO --confcutdir=$ISO $ISO/skills/analog-gmid-design/assets/tests --gmid-phase=1 -k "dup_w_calc or dup_kcl_edges" --collect-only -q > $O/e1_collect_7535799.txt 2>&1; echo "e1disc exit=$? $(( $(date +%s)-s ))s" >> $T
echo "e1disc w_calc=$(grep -c '^skills/analog-gmid-design/assets/tests/contracts/test_dup_w_calc.py::' $O/e1_collect_7535799.txt) kcl=$(grep -c '^skills/analog-gmid-design/assets/tests/contracts/test_dup_kcl_edges.py::' $O/e1_collect_7535799.txt)" >> $T

# E4(c)
sw da03c0e
run elib_da03c0e $PY -B -P $S/e_lib.py $ISO $O/elib_da03c0e.json
mainchk elib_da03
run einst_da03_crt $PY -B -P $S/e_inst_df35.py $ISO current_reuse_telescopic_ota base $O/einst_da03c0e_current_reuse_telescopic_ota.json
mainchk einst_da03_crt
run einst_da03_fc $PY -B -P $S/e_inst_df35.py $ISO folded_cascode base $O/einst_da03c0e_folded_cascode.json
mainchk einst_da03_fc
echo "post da03 iso status:" >> $T; git -C $ISO status --porcelain --ignored >> $T

# E4(d)
sw $H
run elib_H $PY -B -P $S/e_lib.py $ISO $O/elib_H.json
run einst_H_crt $PY -B -P $S/e_inst_df36.py $ISO current_reuse_telescopic_ota $O/einst_H_current_reuse_telescopic_ota.json
run einst_H_fc $PY -B -P $S/e_inst_df36.py $ISO folded_cascode $O/einst_H_folded_cascode.json
mainchk final
echo "post H iso status:" >> $T; git -C $ISO status --porcelain --ignored >> $T
echo DONE >> $T
