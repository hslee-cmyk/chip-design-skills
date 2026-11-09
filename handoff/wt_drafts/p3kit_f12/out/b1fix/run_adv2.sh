#!/usr/bin/env bash
# adv D 9b7e54f (embedded oracle swap) / adv E 65b37a8 (embedded read left via SD): V5, target2, f12_equiv (B34 only), contract 5 (b) embedded scan. No cd.
export TMP=C:/g347/tmp TEMP=C:/g347/tmp APPDATA="C:/Users/HSLEE/AppData/Roaming" HOME="C:/Users/HSLEE"
R=C:/g347/f/r; PY=C:/Python314/python.exe; K=C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/p3kit_f12
A=skills/analog-gmid-design/assets/tests/contracts
L="$A/test_b34_grammar_explicit.py $A/test_d_delete_dead.py $A/test_d_delete_telescopic.py $A/test_dup_kcl_edges.py $A/test_dup_w_calc.py $A/test_ts6_dead_probes.py"
for h in 9b7e54f 65b37a8; do
  v5=$("$PY" -B C:/g347/out/weakening_diff_6c724de.py --root "$R" --base 37f776a --head "$h" | "$PY" -c "import json,sys;r=json.load(sys.stdin);print(r['verdict'],len(r['findings']),len(r['diff_paths']),r['diff_hash'])")
  t2=$("$PY" -B C:/g347/gt/tools/gates/merge_gate.py diff-hash --repo "$R" --base 37f776a --head "$h" $L)
  "$PY" -B "$K/f12_equiv.py" "$R" 37f776a "$h" "C:/g347/out/equiv_adv_$h.json" --approved "$K/out/approved_v5_7_mock.txt" --only $A/test_b34_grammar_explicit.py > /dev/null
  eq=$("$PY" -c "import json;r=json.load(open('C:/g347/out/equiv_adv_$h.json',encoding='utf-8'));b=r['files']['$A/test_b34_grammar_explicit.py'];print(b['verdict'],b['failed'])")
  "$PY" -B "$K/f12_execstr.py" "$R" "$h" "C:/g347/out/execstr_$h.json" --drop C:/g347/out/sd_drop49.json > /dev/null
  sc=$("$PY" -c "import json;r=json.load(open('C:/g347/out/execstr_$h.json',encoding='utf-8'));print([(x['line'],x.get('sd_drop_reads')) for x in r['exec'] if x.get('sd_drop_reads') or x.get('e3')])")
  echo "$h | V5 $v5 | target2 $t2 | equiv $eq | 5b-embedded $sc"
done
