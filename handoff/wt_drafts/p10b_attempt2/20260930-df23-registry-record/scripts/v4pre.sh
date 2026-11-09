#!/usr/bin/env bash
# 재시도 2차 순서 3: T(04e1697)에서 test_lint 사전 실행(code 없음 -- (4)(3)(5)는 지금, (2)는 병합 뒤).
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
B=0f237862c007f6a53122f2bdfb3c87e6366ec133; T=04e1697f6fa93e1ba1844bf3517852d493808f06
C=C:/g88/gmid-gate-cache/$B; PY=C:/Python314/python.exe; R=C:/g88/iso2; A=skills/analog-gmid-design/assets; O=C:/g88/out2
cd C:/g88
P=C:/g88/pyc2_v4card; rm -rf $P; mkdir -p $P
PYTHONPYCACHEPREFIX=$P $PY $C/test_lint.py --root $R --base $B --head $T --module-dir $A/tests/tools --interface-card $R/docs/02-design/specs/20260930-df23-registry-record.interface.md > $O/pre_V4card_T.txt 2>&1
echo "card exit $?"
P=C:/g88/pyc2_v4subj; rm -rf $P; mkdir -p $P
PYTHONPYCACHEPREFIX=$P $PY $C/test_lint.py --root $R --base $B --head $T --module-dir $A/tests/tools --subject reg_check:check_df23 --subject reg_check:main > $O/pre_V4subj_T.txt 2>&1
echo "subj exit $?"
for f in pre_V4card_T pre_V4subj_T; do $PY -B C:/g88/scripts2/v4sum.py $O/$f.txt; done
