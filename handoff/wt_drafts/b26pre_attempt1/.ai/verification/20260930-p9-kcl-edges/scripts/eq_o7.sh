#!/usr/bin/env bash
# P9 순서 7: 같은 경로 C:/g47/eq에서 base와 병합본을 번갈아(같은 시각대) E-INST 2회씩 + E-LIB 1회씩.
export APPDATA="C:/Users/HSLEE/AppData/Roaming"
B=7535799302a9ff7cfbfcadb2281d16bf136fadcf; M=b7765b047ac510b7150a3b99b102891e4083e970
co() { git -C C:/g47/eq checkout -q --detach $1 && git -C C:/g47/eq clean -fdxq; echo "checkout $1 $(git -C C:/g47/eq rev-parse HEAD) st=$(git -C C:/g47/eq status --porcelain | wc -l)" >> C:/g47/out/einst.txt; }
for rnd in 1 2; do
  co $B; for c in folded_cascode current_reuse_telescopic_ota; do bash C:/g47/scripts/einst.sh C:/g47/eq o7base$rnd $c 1; done
  co $M; for c in folded_cascode current_reuse_telescopic_ota; do bash C:/g47/scripts/einst.sh C:/g47/eq o7m$rnd $c 1; done
done
co $B; PYTHONDONTWRITEBYTECODE=1 C:/Python314/python.exe -P C:/g47/scripts/e_lib.py C:/g47/eq C:/g47/out/elib_base_o7.json > C:/g47/out/elib_base_o7.txt 2>&1
co $M; PYTHONDONTWRITEBYTECODE=1 C:/Python314/python.exe -P C:/g47/scripts/e_lib.py C:/g47/eq C:/g47/out/elib_m.json > C:/g47/out/elib_m.txt 2>&1
echo "EQ_O7 DONE st=$(git -C C:/g47/eq status --porcelain | wc -l)" >> C:/g47/out/einst.txt
