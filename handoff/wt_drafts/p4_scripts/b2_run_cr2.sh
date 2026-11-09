#!/bin/bash
# B2 측정 4단계: current_reuse θ* 한 점 -- 축별 격자 밖 계수, 노드전압 conflicts, 축 거부 모드 평가. 결과 C:/g61/out/
P=/c/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/p4_scripts
PY=C:/Python314/python.exe
export APPDATA="${APPDATA:-C:\\Users\\HSLEE\\AppData\\Roaming}"
export PYTHONUSERBASE="${PYTHONUSERBASE:-C:\\Users\\HSLEE\\AppData\\Roaming\\Python}"
export P4_CIRCUIT=current_reuse_telescopic_ota
O=/c/g61/out
TH="$(cat $O/cr_theta.json)"
$PY -B $P/b2_axes.py C:/g61/repo "$TH" C:/g61/out/axes_cr.json > $O/d1.log 2>&1 &
$PY -B $P/b2_nodes.py C:/g61/repo "$TH" C:/g61/out/nodes_cr.json > $O/d2.log 2>&1 &
P4_AXIS=raise $PY -B $P/b2_eval.py C:/g61/sim CR_theta_A_raise --out $O/cr2.jsonl --theta "$TH" > $O/d3.log 2>&1 &
wait
echo done
