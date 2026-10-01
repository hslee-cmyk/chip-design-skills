#!/usr/bin/env bash
# P9 순서 7 V3: 병합본 인벤토리 -> 기준 실행 시간(kcl_series_union.find, 가장 큰 인벤토리) -> mutate_changed(--timeout $1)
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
C=C:/g47/gmid-gate-cache/7535799302a9ff7cfbfcadb2281d16bf136fadcf; M=b7765b047ac510b7150a3b99b102891e4083e970
PYTHONPYCACHEPREFIX=C:/g47/pyc_inv PYTHONPATH=$C C:/Python314/python.exe -P C:/g47/scripts/v3_inv.py C:/g47/m $M C:/g47/out/v3_inv_m.json > C:/g47/out/v3_inv_m.txt 2>&1
for k in kcl_series_union.find kcl_series_union; do
PYTHONPYCACHEPREFIX=C:/g47/pyc_v3b PYTHONPATH=$C C:/Python314/python.exe -P C:/g47/scripts/v3_baseline.py C:/g47/m $M $C/pytest_gate.ini C:/g47/out/v3_inv_m.json $k C:/g47/out/v3_baseline_m_$k.json >> C:/g47/out/v3_baseline_m.txt 2>&1
done
bash C:/g47/scripts/tools_m.sh v3 $1
