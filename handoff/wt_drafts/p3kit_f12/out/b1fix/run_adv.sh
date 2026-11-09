#!/usr/bin/env bash
# S1 adversarial: V5 diff_hash vs second target (listed-unit files) on honest a198913 / adv A 99e2570 / adv C 639b6b1. No cd.
export TMP=C:/g347/tmp TEMP=C:/g347/tmp APPDATA="C:/Users/HSLEE/AppData/Roaming" HOME="C:/Users/HSLEE"
R=C:/g347/f/r; PY=C:/Python314/python.exe; K=C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/p3kit_f12
A=skills/analog-gmid-design/assets/tests/contracts
L="$A/test_b34_grammar_explicit.py $A/test_d_delete_dead.py $A/test_d_delete_telescopic.py $A/test_dup_kcl_edges.py $A/test_dup_w_calc.py $A/test_ts6_dead_probes.py"
for h in a198913 99e2570 639b6b1; do
  v5=$("$PY" -B C:/g347/out/weakening_diff_6c724de.py --root "$R" --base 37f776a --head "$h" | "$PY" -c "import json,sys;r=json.load(sys.stdin);print(r['verdict'],len(r['findings']),len(r['diff_paths']),r['diff_hash'])")
  t2=$("$PY" -B C:/g347/gt/tools/gates/merge_gate.py diff-hash --repo "$R" --base 37f776a --head "$h" $L)
  eq=$("$PY" -B "$K/f12_equiv.py" "$R" 37f776a "$h" "C:/g347/out/equiv_adv_$h.json" --approved "$K/out/approved_v5_7_mock.txt" \
       --only $A/test_b34_grammar_explicit.py $A/test_dup_kcl_edges.py | tail -1)
  echo "$h | V5 $v5 | target2 $t2 | equiv $eq"
done
