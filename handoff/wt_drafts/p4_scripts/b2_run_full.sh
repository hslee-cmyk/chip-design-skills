#!/bin/bash
# B2 측정: folded_cascode 전체 실행 5벌(병렬), 결과는 C:/g61/out/full.jsonl에 케이스마다 append.
P=/c/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/p4_scripts/b2_eval.py
PY=C:/Python314/python.exe
# 백그라운드 실행 환경에 APPDATA가 없어 사용자 site-packages(numpy)를 못 찾는 경우 대비
export APPDATA="${APPDATA:-C:\\Users\\HSLEE\\AppData\\Roaming}"
export PYTHONUSERBASE="${PYTHONUSERBASE:-C:\\Users\\HSLEE\\AppData\\Roaming\\Python}"
O=/c/g61/out
mkdir -p $O
$PY -B $P C:/g61/repo A_head_full --out $O/full.jsonl --full > $O/l1.log 2>&1 &
$PY -B $P C:/g61/sim A_sim_full --out $O/full.jsonl --full > $O/l2.log 2>&1 &
P4_SIM=S1 $PY -B $P C:/g61/sim S1_full --out $O/full.jsonl --full > $O/l3.log 2>&1 &
P4_SIM=S2 $PY -B $P C:/g61/sim S2_full --out $O/full.jsonl --full > $O/l4.log 2>&1 &
P4_SIM=S3 P4_AXIS=count $PY -B $P C:/g61/sim S3_full --out $O/full.jsonl --full > $O/l5.log 2>&1 &
wait
echo done
