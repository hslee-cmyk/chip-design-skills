#!/usr/bin/env bash
# f12_equiv runs (old r4 = pre-b1fix.bak, new = b1fix) on old F1 mock d37ffc5 and fixed F1 mock a198913. No cd.
export TMP=C:/g347/tmp TEMP=C:/g347/tmp APPDATA="C:/Users/HSLEE/AppData/Roaming" HOME="C:/Users/HSLEE"
R=C:/g347/f/r; K=C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/p3kit_f12; PY=C:/Python314/python.exe
cp -f "$K/f12_equiv.pre-b1fix.bak" C:/g347/out/f12_equiv_r4.py
cp -f "$K/f12_execstr.py" C:/g347/out/f12_execstr.py
D17="--d17 C:/g347/f/out/f1sim_names.json"
run() {  # $1 judge  $2 head  $3 label  $4 approved file or none
  if [ "$4" = none ]; then A=""; else A="--approved $4"; fi
  echo "== $3"; "$PY" -B "$1" "$R" 37f776a "$2" "C:/g347/out/equiv_$3.json" $D17 $A | tail -1
}
run C:/g347/out/f12_equiv_r4.py d37ffc5 r4_old_7 "$K/out/approved_v5_7_mock.txt"
run C:/g347/out/f12_equiv_r4.py a198913 r4_fix_7 "$K/out/approved_v5_7_mock.txt"
run "$K/f12_equiv.py" d37ffc5 b1_old_7 "$K/out/approved_v5_7_mock.txt"
run "$K/f12_equiv.py" a198913 b1_fix_7 "$K/out/approved_v5_7_mock.txt"
run "$K/f12_equiv.py" a198913 b1_fix_5 "$K/out/approved_v5_5_mock.txt"
run "$K/f12_equiv.py" a198913 b1_fix_none none
