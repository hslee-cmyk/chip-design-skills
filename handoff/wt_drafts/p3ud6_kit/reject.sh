#!/usr/bin/env bash
# measure only: D0b '작성 전 실측' 5 (fact samples on Q/RG) and 6 (14 reject inputs on the RG copy), names keys.
#   bash reject.sh <Q> <RG>
set -uo pipefail
Q=$1; RG=$2
SC=C:/g222; R=$SC/r
D=C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts; K=$D/p3ud6_kit; O=$K/out
PY="C:/Python314/python.exe -B"
export TMP=$SC/tmp TEMP=$SC/tmp PYTHONIOENCODING=utf-8 MSYS_NO_PATHCONV=1
source $D/p3kit_m1/mpargs.sh
MP=$D/p3kit_m1/move_plan_sim.py
G="git -C $R -c user.name=m -c user.email=m@x"
: > $O/sim5.jsonl
$PY $K/sim5.py $R $Q $O/plan_names_q.json $O/sim5.jsonl base_Q
$PY $K/sim5.py $R $RG $O/plan_names_rg.json $O/sim5.jsonl regen_RG $O/plan_names_q.json
for id in R-A1 R-A2 R-A3 R-A4 R-A5 R-A6 R-A7 R-B1 R-B2 R-B3 R-C1 R-C2 R-D1 R-E1; do
  git -C $R checkout -q --detach $RG
  $PY $K/mk_reject.py $R $id || { echo "$id apply failed" >> $O/sim5.err; continue; }
  $G commit -q -am "reject $id (measure only)" --allow-empty
  H=$(git -C $R rev-parse HEAD)
  if [ $id = R-A7 ]; then PJ=-; else
    MP_STMT_KEY=names $PY $MP plan --root $R --rev $H "${MP_ARGS[@]}" > $O/plan_rej_$id.json; echo "$id plan exit=$?"; PJ=$O/plan_rej_$id.json; fi
  $PY $K/sim5.py $R $H $PJ $O/sim5.jsonl $id $O/plan_names_rg.json
done
git -C $R checkout -q --detach $RG
