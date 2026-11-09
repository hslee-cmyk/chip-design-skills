#!/usr/bin/env bash
# measure only: E-LIB (e_lib.py) + E-INST (e_inst_p3.py) at labelled revs, same checkout path C:/g323/ei. args: <label>=<rev> ...
export TMP=C:/g323/tmp TEMP=C:/g323/tmp APPDATA="C:/Users/HSLEE/AppData/Roaming" HOME="C:/Users/HSLEE" PYTHONIOENCODING=utf-8
R=C:/g323/r; ISO=C:/g323/ei; O=C:/g323/out/ei; K=C:/g323/kit
mkdir -p $O
[ -d $ISO ] || git -C $R worktree add -q --detach $ISO HEAD
for lr in "$@"; do
  L=${lr%%=*}; V=${lr#*=}
  git -C $ISO checkout -q --detach "$V"; git -C $ISO clean -qfdx
  PYTHONPYCACHEPREFIX="$(mktemp -d)" C:/Python314/python.exe -B -P $K/e_lib.py $ISO $O/$L.elib.json >> $O/log.txt 2>&1; echo "$L elib exit=$? $V" >> $O/log.txt
  for cc in folded_cascode current_reuse_telescopic_ota; do s=$(date +%s)
    PYTHONPYCACHEPREFIX="$(mktemp -d)" C:/Python314/python.exe -B -P $K/e_inst_p3.py $ISO $cc $O/$L.$cc.einst.json > $O/$L.$cc.stdout.txt 2>&1
    echo "$L einst $cc exit=$? s=$(( $(date +%s)-s ))" >> $O/log.txt; done
  git -C $ISO checkout -q -- . ; git -C $ISO clean -qfdx
done
echo finished >> $O/log.txt
