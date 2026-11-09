#!/usr/bin/env bash
# 재시도 2차 순서 3: 수집 비교(base2 vs iso2), V5 base->T, 계약 5 (c) base 재계산. 결과는 C:/g88/out2.
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
B=0f237862c007f6a53122f2bdfb3c87e6366ec133; T=04e1697f6fa93e1ba1844bf3517852d493808f06
C=C:/g88/gmid-gate-cache/$B; PY=C:/Python314/python.exe; O=C:/g88/out2
cd C:/g88
for n in base2 iso2; do
  R=C:/g88/$n; P=C:/g88/pyc2_col_$n; rm -rf $P; mkdir -p $P
  PYTHONPYCACHEPREFIX=$P PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=$R --confcutdir=$R --gmid-phase=2 --gmid-strict= $R/skills/analog-gmid-design/assets/tests --collect-only -q -p no:cacheprovider > $O/collect_$n.txt 2>&1
  echo "collect_$n exit $?" >> $O/status.txt
done
P=C:/g88/pyc2_cmp; rm -rf $P; mkdir -p $P
PYTHONPYCACHEPREFIX=$P $PY C:/g88/scripts/cmp_collect.py $O/collect_base2.txt $O/collect_iso2.txt $O/cmp_collect.json > /dev/null 2>&1
echo "cmp exit $?" >> $O/status.txt
P=C:/g88/pyc2_v5; rm -rf $P; mkdir -p $P
PYTHONPYCACHEPREFIX=$P $PY $C/weakening_diff.py --root C:/g88/iso2 --base $B --head $T > $O/v5_base_T.txt 2>&1
echo "v5 exit $?" >> $O/status.txt
P=C:/g88/pyc2_rc; rm -rf $P; mkdir -p $P
PYTHONPYCACHEPREFIX=$P $PY -P C:/g88/scripts/df23_recount.py C:/g88/base2 $O/recount_base.json > $O/recount_base_stdout.txt 2>&1
echo "recount_base exit $?" >> $O/status.txt
PYTHONPYCACHEPREFIX=$P PYTHONPATH=$C $PY -P C:/g88/scripts/strict_check.py C:/g88/iso2 $B 20260930-df23-registry-record "PYTHONPYCACHEPREFIX=C:/g88/pyc_v1 PYTHONPATH=$C $PY -P -m pytest -c $C/pytest_gate.ini --rootdir=C:/g88/m2 --confcutdir=C:/g88/m2 --gmid-phase=2 --gmid-strict= C:/g88/m2/skills/analog-gmid-design/assets/tests" > $O/strict_check.txt 2>&1
echo "strict exit $?" >> $O/status.txt
echo PRE2_DONE >> $O/status.txt
