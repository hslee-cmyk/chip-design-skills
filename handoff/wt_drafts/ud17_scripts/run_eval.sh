#!/bin/bash
# UD-17 측정 1단계: θ* 한 점(clamp/extrap/raise) + 전체 실행(clamp/extrap) 두 회로. 결과 C:/g67/out/eval.jsonl
P=/c/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/ud17_scripts/ud17_eval.py
PY=C:/Python314/python.exe
export APPDATA="${APPDATA:-C:\\Users\\HSLEE\\AppData\\Roaming}"
export PYTHONUSERBASE="${PYTHONUSERBASE:-C:\\Users\\HSLEE\\AppData\\Roaming\\Python}"
O=C:/g67/out/eval.jsonl
TF='{"Ibg": 5e-07, "r_split_M1_M2": 0.5, "r_mirror_M3_M4": 1.5, "kcl_fold_M6": 1.0, "kcl_fold_M5": 1.0}'
TC="$(cat /c/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/p4_scripts/out/cr_theta.json)"
UD17_VS=clamp  $PY -B $P folded_cascode "$TF" $O F_theta_clamp  > /c/g67/out/e1.log 2>&1 &
UD17_VS=extrap $PY -B $P folded_cascode "$TF" $O F_theta_extrap > /c/g67/out/e2.log 2>&1 &
UD17_VS=clamp  $PY -B $P current_reuse_telescopic_ota "$TC" $O C_theta_clamp  > /c/g67/out/e3.log 2>&1 &
UD17_VS=extrap $PY -B $P current_reuse_telescopic_ota "$TC" $O C_theta_extrap > /c/g67/out/e4.log 2>&1 &
UD17_VS=clamp  $PY -B $P folded_cascode --full $O F_full_clamp  > /c/g67/out/e5.log 2>&1 &
UD17_VS=extrap $PY -B $P folded_cascode --full $O F_full_extrap > /c/g67/out/e6.log 2>&1 &
UD17_VS=clamp  $PY -B $P current_reuse_telescopic_ota --full $O C_full_clamp  > /c/g67/out/e7.log 2>&1 &
UD17_VS=extrap $PY -B $P current_reuse_telescopic_ota --full $O C_full_extrap > /c/g67/out/e8.log 2>&1 &
wait
echo done
