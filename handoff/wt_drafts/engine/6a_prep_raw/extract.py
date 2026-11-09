# -*- coding: utf-8 -*-
"""6a prep: current-function structure extraction on 9 library circuits (isolated clone /c/g458/repo).
Appends one JSON line per circuit (WP-11)."""
import sys, os, json, io, traceback, contextlib
A = r"C:\g458\repo\skills\analog-gmid-design\assets"
sys.path.insert(0, A)
OUT = r"C:\g458\work\extract.jsonl"
open(OUT, "w").close()
import stick_diagram as SD
import sizing_recipe as SR
LIB = os.path.join(A, "library")
names = sorted(f[:-len(".topology.json")] for f in os.listdir(LIB) if f.endswith(".topology.json") and not f.startswith("_"))

def safe(fn):
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            return {"ok": fn()}
    except Exception as e:
        return {"err": f"{type(e).__name__}: {str(e)[:300]}"}

for n in names:
    p = os.path.join(LIB, n + ".topology.json")
    raw = json.load(open(p, encoding="utf-8"))
    rec = {"circuit": n}
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            trs, meta = SD.load_topology(p)
    except Exception as e:
        rec["load_err"] = f"{type(e).__name__}: {e}"
        with open(OUT, "a", encoding="utf-8") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        continue
    rails = meta["rails"]
    by = {t.name: t for t in trs}
    ports = {k: v for k, v in (raw.get("ports") or {}).items() if not k.startswith("_")}
    ins = sorted(k for k, v in ports.items() if v.get("direction") == "input")
    outs = sorted(k for k, v in ports.items() if v.get("direction") == "output")
    rec["rails"] = sorted(rails.nets)
    rec["ports_in"], rec["ports_out"] = ins, outs
    rec["n_dev"] = len(trs)
    rec["passives"] = [(e["name"], e.get("kind"), e.get("terminals")) for e in (raw.get("passive_elements") or [])]
    rec["ideal_sources"] = [(e["name"], e.get("kind"), e.get("terminals")) for e in (raw.get("ideal_sources") or [])]
    rec["gap_filled_roles"] = sorted(k for k in (meta.get("device_roles") or {}) if k not in (raw.get("device_roles") or {}))
    rec["diode"] = safe(lambda: sorted(t.name for t in trs if SR.is_diode_connected(t)))
    rec["true_mirror_groups"] = safe(lambda: SR.true_current_mirror_groups(by, rails=rails))
    rec["l_sharing_classes"] = safe(lambda: SR.l_sharing_classes(by, meta, meta["symmetry"]["matching_pairs"]))
    rec["l_sharing_classes_conn_only"] = safe(lambda: SR.l_sharing_classes(by, {"rails": rails}, ()))
    rec["vgs_alias_map_declared"] = safe(lambda: SR.vgs_alias_map(meta))
    rec["gain_stage_tails_declared"] = safe(lambda: SR.gain_stage_tails(by, meta))
    def mc():
        r = SD.find_matching_candidates(trs, rails=rails)
        return {k: {f"{kk}": [t.name for t in vv] for kk, vv in v.items()} for k, v in r.items()}
    rec["matching_candidates"] = safe(mc)
    def dpl1():
        r = SD._diff_pair_layer1_groups(trs, rails=rails)
        return {str(k[:2]): [t.name for t in v] for k, v in r.items()}
    rec["diff_pair_layer1"] = safe(dpl1)
    def dpc():
        r = SD.find_differential_pair_candidates(trs, inputs=ins, outputs=outs, rails=rails)
        return json.loads(json.dumps(r, default=str)) if r is not None else None
    rec["diff_pair_candidates"] = safe(dpc)
    def sym():
        seed = {r: r for r in rails.nets}
        if len(ins) == 2:
            seed[ins[0]] = ins[1]; seed[ins[1]] = ins[0]
        if len(outs) == 2:
            seed[outs[0]] = outs[1]; seed[outs[1]] = outs[0]
        elif len(outs) == 1:
            seed[outs[0]] = outs[0]
        v = SD.find_structural_symmetry_candidates(trs, seed)
        self_sym = sorted(k for k, x in v.device_map.items() if k == x)
        pairs = sorted({tuple(sorted((k, x))) for k, x in v.device_map.items() if k != x})
        return {"pairs": pairs, "self": self_sym, "unresolved": sorted(v.unresolved),
                "conflicts": len(v.conflicts), "low_conf": sorted(sorted(s) for s in v.low_confidence_pairs)}
    rec["symmetry_mirror"] = safe(sym)
    rec["signal_path_nodes"] = safe(lambda: sorted(SR.signal_path_nodes(by, set(ins), set(outs))))
    rec["kcl_series_union_conn_only"] = safe(lambda: {k: v for k, v in SD.kcl_series_union(trs, [], rails=rails).items() if len(v) > 1})
    rec["kcl_edges_conn_only"] = safe(lambda: [(a, b, net) for a, b, kind, net in SD._kcl_and_matching_edges(trs, [], rails=rails)])
    def tr():
        d = SD.trace_vdd_to_gnd_branches(trs); u = SD.trace_gnd_to_vdd_branches(trs)
        return {"down": len(d["branches"]), "down_term": sorted({b["terminates_at"] for b in d["branches"]}),
                "up": len(u["branches"]), "up_term": sorted({b["terminates_at"] for b in u["branches"]})}
    rec["trace_branches_namelit"] = safe(tr)
    rec["declared_vsid"] = sorted({r.get("vertical_stack_id") for r in (raw.get("device_roles") or {}).values() if isinstance(r, dict) and r.get("vertical_stack_id")})
    rec["declared_stages"] = None
    for m in ((raw.get("sizing_roles") or {}).get("metrics") or {}).values():
        if isinstance(m, dict) and m.get("type") == "gain_stages_sum":
            rec["declared_stages"] = m.get("stages")
    rec["compensation_stage_devices"] = (raw.get("compensation") or {}).get("stage_devices")
    with open(OUT, "a", encoding="utf-8") as f: f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
    print("done", n, flush=True)
