#!/usr/bin/env bash
# 재시도 3차 순서 3: 수집 비교(base2 vs iso3, diag3), V5 base->T, strict, rehash. 결과는 C:/g88/o3r.
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
B=0f237862c007f6a53122f2bdfb3c87e6366ec133; T=572d767e0d74a98523e6795928224ad65568c712
C=C:/g88/gmid-gate-cache3/$B; PY=C:/Python314/python.exe; O=C:/g88/o3r
cd C:/g88
for n in base2 iso3 diag3; do
  R=C:/g88/$n; P=C:/g88/pyc3_col_$n; rm -rf $P; mkdir -p $P
  PYTHONPYCACHEPREFIX=$P PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R --gmid-phase=2 --gmid-strict= $R/skills/analog-gmid-design/assets/tests --collect-only -q -p no:cacheprovider > $O/collect_$n.txt 2>&1
  echo "collect_$n exit $?" >> $O/status.txt
done
P=C:/g88/pyc3_cmp; rm -rf $P; mkdir -p $P
PYTHONPYCACHEPREFIX=$P $PY C:/g88/s3/cmp_collect.py $O/collect_base2.txt $O/collect_iso3.txt $O/cmp_base_T.json > /dev/null 2>&1; echo "cmp1 exit $?" >> $O/status.txt
PYTHONPYCACHEPREFIX=$P $PY C:/g88/s3/cmp_collect.py $O/collect_base2.txt $O/collect_diag3.txt $O/cmp_base_diag.json > /dev/null 2>&1; echo "cmp2 exit $?" >> $O/status.txt
P=C:/g88/pyc3_v5; rm -rf $P; mkdir -p $P
PYTHONPYCACHEPREFIX=$P $PY $C/weakening_diff.py --root C:/g88/iso3 --base $B --head $T > $O/v5_base_T.txt 2>&1; echo "v5 exit $?" >> $O/status.txt
P=C:/g88/pyc3_st; rm -rf $P; mkdir -p $P
PYTHONPYCACHEPREFIX=$P PYTHONPATH=$C $PY -P C:/g88/s3/strict_check.py C:/g88/iso3 $B 20260930-df23-registry-record "PYTHONPYCACHEPREFIX=C:/g88/pyc_v1 PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=C:/g88/m3 --confcutdir=C:/g88/m3 --gmid-phase=2 --gmid-strict= C:/g88/m3/skills/analog-gmid-design/assets/tests" > $O/strict_check.txt 2>&1; echo "strict exit $?" >> $O/status.txt
$PY -B C:/g88/s3/rehash.py C:/g88/out3/red_T.jsonl > $O/rehash.txt 2>&1; echo "rehash exit $?" >> $O/status.txt
echo PRE3_DONE >> $O/status.txt
