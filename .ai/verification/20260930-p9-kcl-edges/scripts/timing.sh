#!/usr/bin/env bash
# E-INST 기준값·시간 3회씩(eq 복제본, base) 후 V3 기준 실행 시간(T head, kcl_series_union.find 인벤토리 144 = 병합본 1(d) 모양의 최대 인벤토리 근사, 그리고 kcl_series_union 72).
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
bash C:/g47/scripts/einst_time.sh C:/g47/eq base folded_cascode 3
bash C:/g47/scripts/einst_time.sh C:/g47/eq base current_reuse_telescopic_ota 3
C=C:/g47/gmid-gate-cache/7535799302a9ff7cfbfcadb2281d16bf136fadcf
for k in kcl_series_union kcl_series_union.find; do
PYTHONPYCACHEPREFIX=C:/g47/pyc_v3b PYTHONPATH=$C C:/Python314/python.exe -P C:/g47/scripts/v3_baseline.py C:/g47/iso c8d55dbfc8772fe1d37c2a559a50aa4454fc965b $C/pytest_gate.ini C:/g47/out/v3_inv_c8d55db.json $k C:/g47/out/v3_baseline_$k.json >> C:/g47/out/v3_baseline.txt 2>&1
done
echo done >> C:/g47/out/v3_baseline.txt
