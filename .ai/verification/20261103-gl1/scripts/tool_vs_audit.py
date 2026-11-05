"""Compare the tool output with the 2026-10-29 audit data. usage: python -I tool_vs_audit.py <tool out> <audit dir> <out json>"""
import collections, csv, json, sys
from pathlib import Path

tool, aud, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
new = json.loads((tool / "calls.json").read_text(encoding="utf-8"))
old = json.loads((aud / "calls.json").read_text(encoding="utf-8"))
print("old keys", list(old[0])[:12], len(old))
get = lambda c, *ks: next((c[k] for k in ks if k in c), None)
oldk = collections.Counter((get(c, "callee_mod", "def_mod", "target_mod"), get(c, "callee", "name", "func"), get(c, "caller_mod", "caller"), get(c, "line", "lineno")) for c in old)
newk = collections.Counter((c["callee_mod"], c["callee"], c["caller_mod"], c["line"]) for c in new)
same_mod_old = sum(v for k, v in oldk.items() if k[0] == k[2])
only_old = oldk - newk
only_new = newk - oldk
rows = list(csv.DictReader(open(tool / "b_candidates.tsv", encoding="utf-8", newline=""), delimiter="\t"))
cls = {(r["callee_mod"], r["callee"]): r for r in rows}
by_name = collections.defaultdict(list)
for k, r in cls.items():
    by_name[k[1]].append(r)
B = {"B1": ["ss_circuit", "mos_stamps", "two_terminal_stamps", "admittance_pair"], "B2": ["vdsat", "tol_vdsat_table"], "B3": ["op_point", "forward_point"],
     "B4": ["net_model"], "B5": ["block_gain_model_of", "ParamTables"], "B6": ["current_box"], "B7": ["centre_start"], "B8": ["input_terminal_nets"],
     "B9_B10": ["mos_terminal_nets", "two_terminal_nets"], "B11": ["dc_edges_unpruned"], "B12": ["supplies_declaration"], "B13": ["dc_inputs_from_spec"], "B15": ["offsets", "orient"]}
tab = {}
cnt = collections.Counter()
for b, names in B.items():
    for n in names:
        rs = by_name.get(n, [])
        tab["%s:%s" % (b, n)] = [(r["class"], r["n_sites"], r["pairs_b"], r["pairs_not_b"], r["pairs_d"]) for r in rs] or "not_shared_now"
        cnt[rs[0]["class"] if rs else "not_shared_now"] += 1
res = {"n_new": len(new), "n_old": len(old), "old_same_module_sites": same_mod_old, "only_old_nonsamemod": sum(v for k, v in only_old.items() if k[0] != k[2]),
       "only_new": sum(only_new.values()), "sample_only_old": [list(k) for k, _ in list(only_old.items()) if k[0] != k[2]][:15], "sample_only_new": [list(k) for k in list(only_new)[:15]],
       "class_counts_all": dict(collections.Counter(r["class"] for r in rows)), "n_shared": len(rows), "audit_B_function_table": tab, "audit_B_function_classes": dict(cnt),
       "class_B_rows": [dict(r) for r in rows if r["class"] == "B"]}
out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print({k: res[k] for k in res if k not in ("audit_B_function_table",)})
print(tab)
