#!/bin/bash
# UD-17 보조: current_reuse θ* 평가가 해시 시드에 따라 갈리는지(vertical_stack 순환 의존 오류 vs 성공) 확인. 결과 C:/g67/out/seed.jsonl
P=/c/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/ud17_scripts/ud17_eval.py
PY=C:/Python314/python.exe
export APPDATA='C:\Users\HSLEE\AppData\Roaming' PYTHONUSERBASE='C:\Users\HSLEE\AppData\Roaming\Python'
TC="$(cat /c/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/p4_scripts/out/cr_theta.json)"
for s in 0 1 2 3 4 5 6 7; do
  PYTHONHASHSEED=$s UD17_VS=clamp $PY -B $P current_reuse_telescopic_ota "$TC" C:/g67/out/seed.jsonl C_seed_$s > /c/g67/out/s$s.log 2>&1 &
done
wait
echo done
