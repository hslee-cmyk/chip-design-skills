#!/usr/bin/env bash
# b1fix3 re-measure on chain C:/g399/f (gate 6c724de) + gate master 863a037 tree scan. No cd. Args: BASE F1 F2
# (review_p3_f1_b1fix2 m1~m5 -- kit f12_execstr/f12_equiv/f12_f1sim b1fix3 판; drop = 사슬 출력 SD 49 + ACF 2)
set -u
export TMP=C:/g399/tmp TEMP=C:/g399/tmp APPDATA="C:/Users/HSLEE/AppData/Roaming" HOME="C:/Users/HSLEE"
R=C:/g399/f/r; PY=C:/Python314/python.exe; K=C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/p3kit_f12; O=C:/g399/out
BASE=$1; F1=$2; F2=$3
A=skills/analog-gmid-design/assets/tests/contracts
[ -d /c/g399/gt/tools/gates ] || { mkdir -p /c/g399/gt && git -C "$R" archive 6c724de tools/gates | tar -x -C /c/g399/gt; }
[ -d /c/g399/gt863/tools/gates ] || { mkdir -p /c/g399/gt863 && git -C "$R" archive 863a037 tools/gates | tar -x -C /c/g399/gt863; }
echo "== tools diff 6c724de..863a037: $(git -C "$R" diff --name-only 6c724de 863a037 -- tools | wc -l) files"
"$PY" - <<'EOF'
import json, re
log = open("C:/g399/chain.log", encoding="utf-8").read()
sd = eval(re.search(r"stick_diagram\.py dropped 49 (\[.*?\])", log).group(1))
acf = eval(re.search(r"audit_current_forced\.py dropped 2 (\[.*?\])", log).group(1))
assert len(sd) == 49 and len(acf) == 2
json.dump(sd, open("C:/g399/out/sd_drop49.json", "w", encoding="utf-8"))
json.dump(acf, open("C:/g399/out/acf_drop2.json", "w", encoding="utf-8"))
print("acf drop", acf)
EOF
echo "== execstr scan"
for c in "$BASE" "$F1" 6c724de 863a037; do
  echo "-- $c"; "$PY" -B "$K/f12_execstr.py" "$R" "$c" "$O/execstr_$c.json" --drop "$O/sd_drop49.json" --drop-acf "$O/acf_drop2.json"
done
echo "== V5 (gate weakening_diff 6c724de) + target2"
L="$A/test_b34_grammar_explicit.py $A/test_d_delete_dead.py $A/test_d_delete_telescopic.py $A/test_dup_kcl_edges.py $A/test_dup_w_calc.py $A/test_ts6_dead_probes.py"
v5=$("$PY" -B /c/g399/gt/tools/gates/weakening_diff.py --root "$R" --base "$BASE" --head "$F1" | "$PY" -c "import json,sys;r=json.load(sys.stdin);print(r['verdict'],len(r['findings']),len(r['diff_paths']),r['diff_hash'])")
t2=$("$PY" -B /c/g399/gt/tools/gates/merge_gate.py diff-hash --repo "$R" --base "$BASE" --head "$F1" $L)
echo "V5 $v5 | target2 $t2"
echo "== f12_equiv"
D17="--d17 C:/g399/f/out/f1sim_names.json"
for spec in "7:$K/out/approved_v5_7_mock.txt" "5:$K/out/approved_v5_5_mock.txt" "none:"; do
  lab=${spec%%:*}; ap=${spec#*:}
  if [ -z "$ap" ]; then AP=""; else AP="--approved $ap"; fi
  echo "-- $lab"; "$PY" -B "$K/f12_equiv.py" "$R" "$BASE" "$F1" "$O/equiv_$lab.json" $D17 $AP > "$O/equiv_$lab.stdout" 2>&1; echo "rc=$?"
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
  W="C:/g399/w_$c"
  [ -d "$W" ] || git -C "$R" worktree add -q --detach "$W" "$c"
  PYTHONPATH=C:/g399/gt/tools/gates PYTHONPYCACHEPREFIX=C:/g399/tmp/pyc "$PY" -P -m pytest \
    -c C:/g399/gt/tools/gates/pytest_gate.ini --rootdir="$W" --confcutdir="$W" \
    "$W/$A/test_b34_grammar_explicit.py" --gmid-phase=3 -q -p no:cacheprovider > "$O/b34_$c.txt" 2>&1
  echo "$c rc=$? $(tail -1 "$O/b34_$c.txt")"
done
echo "== parse_spec_card (gate 863a037 role_paths)"
"$PY" -B - <<'EOF'
import hashlib, json, sys
sys.path.insert(0, r"C:\g399\gt863\tools\gates")
import role_paths as rp
p = r"C:\Users\HSLEE\Documents\Todoc\fpga\wt\_drafts\draft_p3_f1.spec.md"
b = open(p, "rb").read()
card = rp.parse_spec_card(b.decode("utf-8"), expect_id="20261002-p3-callers-update")
print(json.dumps({k: (v if not isinstance(v, (set, frozenset)) else sorted(v)) for k, v in card.items()
                  if k in ("id", "phase", "evidence_type", "gate_change", "approval", "approvals")}, ensure_ascii=False, default=str)[:800])
print("sha256", hashlib.sha256(b).hexdigest(), "bytes", len(b))
EOF
