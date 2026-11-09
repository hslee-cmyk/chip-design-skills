#!/usr/bin/env bash
# 새 test 파일만 스텁 reg_check(check_df23·main)와 함께 C:/g88/stub2에 두고 수집 수를 센다(병합본 기대 수집 수 계산용).
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
PY=C:/Python314/python.exe; O=C:/g88/out2; S=C:/g88/stub2
rm -rf $S; mkdir -p $S/tests/contracts $S/tests/tools
cp C:/g88/iso2/skills/analog-gmid-design/assets/tests/contracts/test_reg_check_df23.py $S/tests/contracts/
printf 'def check_df23(*a, **k):\n    return []\n\n\ndef main(argv=None):\n    return 0\n' > $S/tests/tools/reg_check.py
cd $S
P=C:/g88/pyc2_stub; rm -rf $P; mkdir -p $P
PYTHONPYCACHEPREFIX=$P $PY -P -m pytest --rootdir=$S --confcutdir=$S -o addopts= $S/tests/contracts/test_reg_check_df23.py --collect-only -q -p no:cacheprovider > $O/stub_collect.txt 2>&1
echo "stub_collect exit $?" >> $O/status.txt
tail -2 $O/stub_collect.txt
cd C:/g88
rm -rf $S
