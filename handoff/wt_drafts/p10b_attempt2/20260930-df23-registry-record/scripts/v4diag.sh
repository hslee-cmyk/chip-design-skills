#!/usr/bin/env bash
# V4 (2) 진단: 병합본 복제본을 C:/g88/v4diag로 따로 복제, test 파일의 _p10b_check 호출을 직접 호출로 치환(작업 트리만, 커밋 없음),
# test_lint를 파일 목록 형태로 실행. 대조로 치환 전 파일도 같은 형태로 실행.
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
B=0f237862c007f6a53122f2bdfb3c87e6366ec133
C=C:/g88/gmid-gate-cache/$B; PY=C:/Python314/python.exe; O=C:/g88/out3; R=C:/g88/v4diag
A=skills/analog-gmid-design/assets
TF=$A/tests/contracts/test_reg_check_df23.py
cd C:/g88
rm -rf $R
git clone -q -c core.longpaths=true --no-hardlinks --no-local C:/g88/m2 $R
P=C:/g88/pyc3_v4diag; rm -rf $P; mkdir -p $P
PYTHONPYCACHEPREFIX=$P $PY $C/test_lint.py --root $R --module-dir $A/tests/tools --interface-card $R/docs/02-design/specs/20260930-df23-registry-record.interface.md $TF > $O/v4diag_orig.txt 2>&1
echo "v4diag_orig exit $?" > $O/v4diag_status.txt
$PY -B C:/g88/scripts3/v4_inline_diag.py $R >> $O/v4diag_status.txt 2>&1
PYTHONPYCACHEPREFIX=$P $PY $C/test_lint.py --root $R --module-dir $A/tests/tools --interface-card $R/docs/02-design/specs/20260930-df23-registry-record.interface.md $TF > $O/v4diag_inlined.txt 2>&1
echo "v4diag_inlined exit $?" >> $O/v4diag_status.txt
