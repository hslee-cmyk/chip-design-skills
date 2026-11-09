#!/bin/bash
# B2 측정 2단계: VS 축 밖 조회(DF-27 #25 상당) -- S_A·S3 계수와 거부 모드 전체 실행. 결과 C:/g61/out/axis.jsonl
P=/c/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/p4_scripts/b2_eval.py
PY=C:/Python314/python.exe
export APPDATA="${APPDATA:-C:\\Users\\HSLEE\\AppData\\Roaming}"
export PYTHONUSERBASE="${PYTHONUSERBASE:-C:\\Users\\HSLEE\\AppData\\Roaming\\Python}"
O=/c/g61/out
P4_AXIS=count $PY -B $P C:/g61/sim A_count_full --out $O/axis.jsonl --full > $O/a1.log 2>&1 &
P4_AXIS=raise $PY -B $P C:/g61/sim A_raise_full --out $O/axis.jsonl --full > $O/a2.log 2>&1 &
P4_SIM=S3 P4_AXIS=raise $PY -B $P C:/g61/sim S3_raise_full --out $O/axis.jsonl --full > $O/a3.log 2>&1 &
P4_SIM=S2 P4_AXIS=count $PY -B $P C:/g61/sim S2_count_full --out $O/axis.jsonl --full > $O/a4.log 2>&1 &
wait
echo done
