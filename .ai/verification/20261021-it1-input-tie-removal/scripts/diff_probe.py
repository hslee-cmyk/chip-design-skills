"""base(e98d0b0f 코드) 대 HEAD S0 탐침 비교. y 키 이름 바꿈(input_common_mode -> HEAD 입력 포트 W4 뿌리 넷)을 적용한 뒤 남는 차이를 원인별로 본다."""
import json, sys
b = json.load(open(sys.argv[1], encoding="utf-8")); h = json.load(open(sys.argv[2], encoding="utf-8"))
out = {}
def rename(x, root):
    s = json.dumps(x, ensure_ascii=False, sort_keys=True)
    return json.loads(s.replace('"input_common_mode"', json.dumps(root))) if root else x
for c in b:
    B, H = b[c], h[c]
    wb = dict((n, w) for n, w in B.get("writers", [])); wh = dict((n, w) for n, w in H.get("writers", []))
    root = next((n for n, w in wb.items() if w["y_key"] == "input_common_mode"), None)
    tie_nets = sorted(n for n, w in wb.items() if w["relation"] == "input_tie")
    cb = dict((d, x) for d, x in B.get("coords", [])); ch = dict((d, x) for d, x in H.get("coords", []))
    newwriters = sorted(d for d in cb if cb[d] != ch.get(d))
    r = {"status": [B.get("status"), H.get("status")], "y_root": root, "input_tie_nets_base": tie_nets,
         "writer_nets_changed": sorted(n for n in set(wb) | set(wh) if wb.get(n) != wh.get(n)),
         "coord_changed": {d: [cb.get(d), ch.get(d)] for d in newwriters},
         "domain_ties_count": [len(B.get("domain_ties") or []), len(H.get("domain_ties") or [])],
         "domain_vars_count": [len(B.get("domain_variables_raw") or []), len(H.get("domain_variables_raw") or [])],
         "ach_dof": [B.get("ach_dof"), H.get("ach_dof")]}
    vb = rename(B.get("domain_variables_raw") or [], root); vh = H.get("domain_variables_raw") or []
    sb = {json.dumps(v, sort_keys=True) for v in vb}; sh = {json.dumps(v, sort_keys=True) for v in vh}
    r["domain_vars_added"] = sorted(sh - sb)[:10]; r["domain_vars_removed"] = sorted(sb - sh)[:10]
    tb = rename(B.get("domain_ties") or [], root); th = H.get("domain_ties") or []
    stb = {json.dumps(v, sort_keys=True) for v in tb}; sth = {json.dumps(v, sort_keys=True) for v in th}
    r["domain_ties_added"] = sorted(sth - stb)[:10]; r["domain_ties_removed"] = sorted(stb - sth)[:10]
    for f in ("theta_schema", "start_rungs", "start_uncovered"):
        x, y = rename(B.get(f), root), H.get(f)
        r[f + "_equal_after_rename"] = x == y
        if x != y and isinstance(x, (list, dict)):
            xs = json.dumps(x, sort_keys=True); ys = json.dumps(y, sort_keys=True)
            r[f + "_mentions_new_writers"] = {d: (d in ys) for d in newwriters}
            r[f + "_len"] = [len(xs), len(ys)]
    out[c] = r
json.dump(out, open(sys.argv[3], "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)
for c, r in out.items():
    print(c, json.dumps({k: v for k, v in r.items() if k not in ("ach_dof",)}, ensure_ascii=False)[:900])
    a0, a1 = r["ach_dof"]
    if a0 != a1:
        print("   ach_dof diff keys:", [k for k in (a0 or {}) if (a0 or {}).get(k) != (a1 or {}).get(k)], {k: [(a0 or {}).get(k), (a1 or {}).get(k)] for k in ("n_equations", "n_variables", "status", "structural_rank")})
