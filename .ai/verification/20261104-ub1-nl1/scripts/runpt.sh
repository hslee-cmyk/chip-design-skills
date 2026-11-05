#!/bin/bash
# usage: runpt.sh <label> <pytest args...>   -- 격리 복제본에서 pytest, 결과를 run3/out/<label>.txt 에 쓴다
R=C:/Users/HSLEE/AppData/Local/Temp/la1s_ub1_audit
ROOT=${AUDIT_ROOT:-$R/iso3}
mkdir -p $R/run3/out
label=$1; shift
free=$(awk '/MemFree/{print int($2/1024)}' /proc/meminfo)
echo "free_before_mb=$free" > $R/run3/out/$label.meta
if [ "$free" -lt 3700 ]; then echo "LOW MEMORY $free MB, not started" | tee -a $R/run3/out/$label.meta; exit 3; fi
cd $ROOT/skills/analog-gmid-design || exit 4
export APPDATA=C:/Users/HSLEE/AppData/Roaming USERPROFILE=C:/Users/HSLEE OPENBLAS_NUM_THREADS=1 PYTHONPYCACHEPREFIX=$R/pyc3 PYTHONUTF8=1
python -m pytest "$@" -p no:cacheprovider --tb=short -q -rfE > $R/run3/out/$label.txt 2>&1
rc=$?
free2=$(awk '/MemFree/{print int($2/1024)}' /proc/meminfo)
echo "rc=$rc free_after_mb=$free2" >> $R/run3/out/$label.meta
cat $R/run3/out/$label.meta
tail -25 $R/run3/out/$label.txt
