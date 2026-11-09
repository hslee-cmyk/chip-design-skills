#!/bin/bash
# B2 측정 3단계: folded θ* 한 점 평가(축 거부 모드), current_reuse 전체 실행(S_A 축 계수, S1 원점 이동). 결과 C:/g61/out/cr.jsonl
P=/c/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/p4_scripts/b2_eval.py
PY=C:/Python314/python.exe
export APPDATA="${APPDATA:-C:\\Users\\HSLEE\\AppData\\Roaming}"
export PYTHONUSERBASE="${PYTHONUSERBASE:-C:\\Users\\HSLEE\\AppData\\Roaming\\Python}"
O=/c/g61/out
TH='{"Ibg": 5e-07, "r_split_M1_M2": 0.5, "r_mirror_M3_M4": 1.5, "kcl_fold_M6": 1.0, "kcl_fold_M5": 1.0}'
P4_AXIS=raise $PY -B $P C:/g61/sim F_theta_A_raise --out $O/cr.jsonl --theta "$TH" > $O/c0.log 2>&1
P4_AXIS=count $PY -B $P C:/g61/sim F_theta_A_count --out $O/cr.jsonl --theta "$TH" > $O/c00.log 2>&1
P4_SIM=S1 $PY -B $P C:/g61/sim F_theta_S1 --out $O/cr.jsonl --theta "$TH" > $O/c01.log 2>&1
$PY -B $P C:/g61/sim F_theta_A --out $O/cr.jsonl --theta "$TH" > $O/c02.log 2>&1
P4_SIM=S3 $PY -B $P C:/g61/sim F_theta_S3 --out $O/cr.jsonl --theta "$TH" > $O/c03.log 2>&1
P4_CIRCUIT=current_reuse_telescopic_ota P4_AXIS=count $PY -B $P C:/g61/sim CR_A_count_full --out $O/cr.jsonl --full > $O/c1.log 2>&1 &
P4_CIRCUIT=current_reuse_telescopic_ota P4_SIM=S1 $PY -B $P C:/g61/sim CR_S1_full --out $O/cr.jsonl --full > $O/c2.log 2>&1 &
P4_CIRCUIT=current_reuse_telescopic_ota $PY -B $P C:/g61/sim CR_A_full --out $O/cr.jsonl --full > $O/c3.log 2>&1 &
wait
echo done
