#!/usr/bin/env bash
# b1fix2 re-measure on chain C:/g374/f (gate 6c724de). No cd. Args: BASE F1 F2
set -u
export TMP=C:/g374/tmp TEMP=C:/g374/tmp APPDATA="C:/Users/HSLEE/AppData/Roaming" HOME="C:/Users/HSLEE"
R=C:/g374/f/r; PY=C:/Python314/python.exe; K=C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/p3kit_f12; O=C:/g374/out
BASE=$1; F1=$2; F2=$3
A=skills/analog-gmid-design/assets/tests/contracts
[ -d /c/g374/gt/tools/gates ] || { mkdir -p /c/g374/gt && git -C "$R" archive 6c724de tools/gates | tar -x -C /c/g374/gt; }
"$PY" - <<'EOF'
import json, re
log = open("C:/g374/chain.log", encoding="utf-8").read()
names = eval(re.search(r"stick_diagram\.py dropped 49 (\[.*?\])", log).group(1))
assert len(names) == 49
json.dump(names, open("C:/g374/out/sd_drop49.json", "w", encoding="utf-8"))
EOF
echo "== execstr scan"
for c in "$BASE" "$F1" 6c724de; do
  echo "-- $c"; "$PY" -B "$K/f12_execstr.py" "$R" "$c" "$O/execstr_$c.json" --drop "$O/sd_drop49.json" | cut -c1-400
done
echo "== V5 (gate weakening_diff) + target2"
L="$A/test_b34_grammar_explicit.py $A/test_d_delete_dead.py $A/test_d_delete_telescopic.py $A/test_dup_kcl_edges.py $A/test_dup_w_calc.py $A/test_ts6_dead_probes.py"
v5=$("$PY" -B /c/g374/gt/tools/gates/weakening_diff.py --root "$R" --base "$BASE" --head "$F1" | "$PY" -c "import json,sys;r=json.load(sys.stdin);print(r['verdict'],len(r['findings']),len(r['diff_paths']),r['diff_hash'])")
t2=$("$PY" -B /c/g374/gt/tools/gates/merge_gate.py diff-hash --repo "$R" --base "$BASE" --head "$F1" $L)
echo "V5 $v5 | target2 $t2"
echo "== f12_equiv"
D17="--d17 C:/g374/f/out/f1sim_names.json"
for spec in "7:$K/out/approved_v5_7_mock.txt" "5:$K/out/approved_v5_5_mock.txt" "none:"; do
  lab=${spec%%:*}; ap=${spec#*:}
  if [ -z "$ap" ]; then AP=""; else AP="--approved $ap"; fi
  echo "-- $lab"; "$PY" -B "$K/f12_equiv.py" "$R" "$BASE" "$F1" "$O/equiv_$lab.json" $D17 $AP | tail -1 | "$PY" -c "import json,sys;r=json.loads(sys.stdin.read());print('stdout files',r.get('files'),'pass',r.get('pass'),'listed',len(r.get('listed',{})),'fail',len(r.get('fail',{})),'d17',r.get('d17_expect_vs_f1sim_diff'))"
  "$PY" -c "
import json;r=json.load(open('$O/equiv_$lab.json',encoding='utf-8'))
fs=r['files'];c={}
for p,v in fs.items(): c[v['verdict']]=c.get(v['verdict'],0)+1
b=fs.get('$A/test_b34_grammar_explicit.py',{})
print(len(fs),c,'d17diff',r.get('d17_expect_vs_f1sim_diff'),'B34',b.get('verdict'),b.get('failed'),{k:x.get('verdict') for k,x in b.get('exec_strings',{}).items()})
print('FAIL',{p:v['failed'] for p,v in fs.items() if v['verdict']=='FAIL'})"
done
echo "== B34 pytest"
for c in "$F1" "$F2"; do
  W="C:/g374/w_$c"
  [ -d "$W" ] || git -C "$R" worktree add -q --detach "$W" "$c"
  PYTHONPATH=C:/g374/gt/tools/gates PYTHONPYCACHEPREFIX=C:/g374/tmp/pyc "$PY" -P -m pytest \
    -c C:/g374/gt/tools/gates/pytest_gate.ini --rootdir="$W" --confcutdir="$W" \
    "$W/$A/test_b34_grammar_explicit.py" --gmid-phase=3 -q -p no:cacheprovider > "$O/b34_$c.txt" 2>&1
  echo "$c rc=$? $(tail -1 "$O/b34_$c.txt")"
done
