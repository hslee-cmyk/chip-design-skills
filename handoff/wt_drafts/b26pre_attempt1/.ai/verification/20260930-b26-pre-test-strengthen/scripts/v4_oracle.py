"""V4 oracle 대조 -- auditor가 spec card 입력을 card 문장에서 직접 만들어 base 엔진(T 트리 = base 엔진)에 넣고 (c) 기준선 값을 다시 잰다.
test 파일을 import하지 않는다. argv: <엔진 assets 디렉터리> <출력 json> <scratch 디렉터리>
"""
import json
import os
import sys

ASSETS, OUTP, TMPD = sys.argv[1:4]
os.makedirs(TMPD, exist_ok=True)
os.chdir(TMPD)   # 엔진이 상대 경로에 쓰더라도 scratch 안에만
sys.path.insert(0, ASSETS)
import sizing_recipe as sr   # noqa: E402
import stick_diagram as sd   # noqa: E402

os.makedirs(TMPD, exist_ok=True)
lut = sr.build_toy_lut()
L = 0.5e-6
r = sr.size_transistor(gm=200e-6, gm_id=12.0, L=L, lut=lut, vds=0.6)
W0 = r.W
S = {"ID": r.ID, "W": W0, "L": L, "gm": r.gm, "gm_id": 12.0, "gds": r.gm / lut.gm_gds_ratio(12.0, L, 0.6, 0.0),
     "kind": "nmos", "vds": 0.6, "vsb": 0.0}
TR = sr.Transistor


def topo(stem, netlist, symmetry=None, **extra):
    d = {"topology_name": stem, "schema_version": "2.0", "supply_nets": ["vdd", "gnd"], "netlist": netlist,
         "symmetry": symmetry or {"matching_pairs": [], "dispositions": []}}
    d.update(extra)
    p = os.path.join(TMPD, stem + ".topology.json")
    json.dump(d, open(p, "w", encoding="utf-8"))
    return p


def nl(n, k, s, d, g):
    return {"name": n, "kind": k, "source": s, "drain": d, "gate": g}


def star():
    return [TR("M1", "nmos", source="na", drain="nx", gate="g1", n_fingers=1, finger_w=W0, stack_id="row"),
            TR("M2", "nmos", source="nx", drain="nb", gate="g2", n_fingers=1, finger_w=W0, stack_id="row"),
            TR("M3", "nmos", source="nx", drain="nc", gate="g3", n_fingers=1, finger_w=W0, stack_id="row")]


def pair():
    return [TR("Ma", "nmos", source="vtail", drain="nda", gate="ga", n_fingers=1, finger_w=W0, stack_id="seg1"),
            TR("Mb", "nmos", source="vtail", drain="ndb", gate="gb", n_fingers=1, finger_w=W0, stack_id="seg1")]


def ctx(names, p):
    return sr.SizingContext(sized={n: dict(S) for n in names}, topology_path=p)


def ent(t):
    return nl(t.name, t.kind, t.source, t.drain, t.gate)


def names(rows):
    return sorted(t.name for v in rows.values() for t in v)


def euler_ok(res):
    e = [c for c in res["audit"].checks if c.name.startswith("1. euler[")]
    st = sd.build_stick_diagram([t for v in res["rows"].values() for t in v])
    return {"n_euler_checks": len(e), "all_euler_ok": all(c.ok for c in e),
            "stick_status": sorted({k: s.status for k, s in st.items()}.items())}


M = {"pair_area": {"type": "sum_area", "devices": ["Ma", "Mb"]}}
LOOSE = [{"metric": "pair_area", "op": "<=", "value": 2 * W0 * L * 3.0}]
out = {}

# 계약 1
p1 = topo("c1", [ent(t) for t in pair()],
          symmetry={"matching_pairs": [{"names": ["Ma", "Mb"], "matching_sensitivity": "offset", "current_forced": False}],
                    "dispositions": []},
          device_roles={"Ma": {"gm_id_role": "", "L_role": ""}, "Mb": {"gm_id_role": "", "L_role": ""}},
          sizing_roles={"metrics": {"pair_area": {"type": "sum_area", "unit": "m^2", "devices": ["Ma", "Mb"]}},
                        "constraints": [{"metric": "pair_area", "op": "<=", "value": 2 * W0 * L * 3}]})
res = sr.optimize_full_circuit_budget(p1, {"known_sizing": {"Ma": S, "Mb": S}, "min_finger_w": 0.1e-6, "max_finger_w": 40e-6,
                                           "L_min": 0.1e-6, "gm_id_bounds": (2.0, 28.0),
                                           "stack_groups_override": {"pair_row": ["Ma", "Mb"]}})
pr = res["pipeline_result"]
c3c = [c for c in pr["repaired_audit"].checks if c.name.startswith("3c.")] if "repaired_audit" in pr else []
out["c1"] = {"has_repaired_rows": "repaired_rows" in pr, "has_repaired_audit": "repaired_audit" in pr,
             "has_growth_rounds": "growth_rounds" in pr, "audit_ok": res["audit_ok"],
             "n_3c": len(c3c), "3c_ok": [c.ok for c in c3c], "repaired_row_keys": sorted(pr.get("repaired_rows", {})),
             "repaired_names": names(pr.get("repaired_rows", {})),
             "stack_ids_eq_rows": {t.stack_id for t in pr["transistors"]} == set(pr.get("repaired_rows", {}))}

# 계약 2
p2 = topo("c2", [ent(t) for t in star()])
res = sr.run_matching_safety_with_finger_growth({"row": star()}, [], {}, ctx(["M1", "M2", "M3"], p2), {"nmos": lut}, {}, [],
                                                gm_id_bounds=(11.9, 12.1))
out["c2"] = {"rows": {k: [(t.name, t.n_fingers, t.stack_id) for t in v] for k, v in res["rows"].items()}}

# 계약 3
p3 = topo("c3", [ent(t) for t in pair() + star()])
B = dict(gm_id_bounds=(2.0, 28.0))
a = sr.run_matching_safety_with_finger_growth({"seg1": pair()}, [("Ma", "Mb")], {("Ma", "Mb"): "offset"}, ctx(["Ma", "Mb"], p3),
                                              {"nmos": lut}, M, LOOSE, max_rounds=0, **B)
b = sr.run_matching_safety_with_finger_growth({"seg1": pair(), "row": star()}, [("Ma", "Mb")], {("Ma", "Mb"): "offset"},
                                              ctx(["Ma", "Mb", "M1", "M2", "M3"], p3), {"nmos": lut}, M, LOOSE, max_rounds=0, **B)
c = sr.run_matching_safety_with_finger_growth({"seg1": pair()}, [("Ma", "Mb")], {("Ma", "Mb"): "ratio"}, ctx(["Ma", "Mb"], p3),
                                              {"nmos": lut}, M, LOOSE, **B)
d = sr.run_matching_safety_with_finger_growth({"seg1": pair(), "row": star()}, [("Ma", "Mx")], {("Ma", "Mx"): "offset"},
                                              ctx(["Ma", "Mb", "M1", "M2", "M3"], p3), {"nmos": lut}, M, LOOSE, **B)
e = sr.run_matching_safety_with_finger_growth({"row": star()}, [], {}, ctx(["M1", "M2", "M3"], p3), {"nmos": lut}, {}, [], **B)


def summ(x):
    return {"growth_rounds": x["growth_rounds"], "unresolved_pair": x["unresolved_pair"],
            "unresolved_reason": x["unresolved_reason"], "relaxed_pairs": x["relaxed_pairs"], "audit_ok": x["audit"].ok,
            "rows": {k: [(t.name, t.n_fingers, t.stack_id) for t in v] for k, v in x["rows"].items()}, **euler_ok(x)}


out["c3"] = {"a": summ(a), "b": summ(b), "c": summ(c), "d": summ(d), "e": summ(e)}


# 계약 4
def c4(omit):
    keys = [("hub_merge", "nmos", "gnd"), ("hub_merge", "nmos", "ntail"), ("current_mirror", "nmos", "nb"), ("diff_pair", "nmos", "ntail")]
    disp = [{"tag": t, "kind": k, "key": n, "category": "real_match", "reason": "audit"} for (t, k, n) in keys if (t, k, n) != omit]
    p = topo("c4_%s" % (omit[0] + omit[2] if omit else "none"),
             [nl("M1", "nmos", "gnd", "nb", "nb"), nl("M2", "nmos", "gnd", "nout", "nb"),
              nl("Ma", "nmos", "ntail", "nda", "nga"), nl("Mb", "nmos", "ntail", "ndb", "ngb")],
             symmetry={"matching_pairs": [], "dispositions": disp},
             _netlist_sections_structured={"blk": {"devices": ["M1", "M2", "Ma", "Mb"]}})
    ch = [x for x in sd.run_full_circuit_audit_from_topology(p).checks if x.name.startswith("3.")]
    return {"n": len(ch), "ok": [x.ok for x in ch], "omit_in_detail": bool(omit) and repr(omit) in ch[0].detail}


out["c4"] = {"none": c4(None), "mirror": c4(("current_mirror", "nmos", "nb")), "diff": c4(("diff_pair", "nmos", "ntail")),
             "hub_gnd": c4(("hub_merge", "nmos", "gnd"))}


# 계약 5·6
def cas():
    return [TR("M1", "nmos", source="ntail", drain="nx1", gate="ninp"), TR("M2", "nmos", source="ntail", drain="nx2", gate="ninn"),
            TR("M1c", "nmos", source="nx1", drain="no1", gate="nvc"), TR("M2c", "nmos", source="nx2", drain="no2", gate="nvc"),
            TR("M3", "pmos", source="vdd", drain="no1", gate="nvp"), TR("M4", "pmos", source="vdd", drain="no2", gate="nvp"),
            TR("M5", "nmos", source="gnd", drain="ntail", gate="nvb")]


out["c5"] = {"groups": {k: list(v) for k, v in sr.resolve_stack_layout(cas(), [], {}).items()}}
g6a = sd.propose_vertical_stack_id_gap_fill(cas(), [], {"M1": {"vertical_stack_id": "colA"}})
g6b = sd.propose_vertical_stack_id_gap_fill(cas(), [], {"M1": {"vertical_stack_id": "colA"}}, inputs=("ninp", "ninn"),
                                            outputs=("no1", "no2"), biases=("nvb", "nvc", "nvp"))
out["c6"] = {"a_proposals": g6a["proposals"], "b_proposals": g6b["proposals"], "b_conflicts": g6b["conflicts"],
             "b_components": sorted(sorted(x) for x in g6b["components_used"])}

# 계약 7
p7 = topo("c7", [nl("M1", "nmos", "ntail", "no1", "ninp"), nl("M2", "nmos", "ntail", "no2", "ninn"), nl("M3", "pmos", "vdd", "no1", "no1"),
                 nl("M4", "pmos", "vdd", "no2", "no1"), nl("M5", "nmos", "gnd", "ntail", "nvb"), nl("M6", "nmos", "gnd", "NQ", "nvb"),
                 nl("M7", "nmos", "gnd", "nq", "nvb")])
_t, meta = sd.load_topology(p7)
rv = meta["_device_roles_gap_fill_review_needed"] or []
out["c7"] = {"case_collisions": [{k: sorted(v) for k, v in x["case_collisions"].items()} for x in rv
                                 if isinstance(x, dict) and "case_collisions" in x]}


# 계약 10
def c10(tap, other, stem):
    p = topo(stem, [nl("M1", "nmos", "ntail", "nd1", "ninp"), nl("M2", "nmos", "ntail", "nd2", "ninn"), nl("M3", "pmos", "vdd", "nd1", "nbp"),
                    nl("M4", "pmos", "vdd", "nd2", "nbp"), nl("M5", "nmos", "gnd", "ntail", "nvb"),
                    nl("Mx1", "nmos", "gnd", "nx1", tap), nl("Mx2", "nmos", "gnd", "nx2", tap), nl("My", "nmos", "gnd", "ny", other)])
    _t, m = sd.load_topology(p)
    af = m["_device_roles_autofilled"]
    ro = {n: (af.get(n, {}).get("gm_id_role"), af.get(n, {}).get("L_role")) for n in ("Mx1", "Mx2", "My")}
    return {"roles": ro, "review_pairs": sorted(sorted(x["names"]) for x in m["_matching_pairs_needs_review"])}


out["c10"] = {"tap_p": c10("ninp", "ninn", "c10p"), "tap_n": c10("ninn", "ninp", "c10n")}


# 계약 11
def br(n):
    ts = [TR("Mt", "nmos", source="gnd", drain="ntail", gate="nb")]
    for k in range(1, n + 1):
        ts += [TR("Mi%d" % k, "nmos", source="ntail", drain="no%d" % k, gate="ni%d" % k),
               TR("Ml%d" % k, "pmos", source="vdd", drain="no%d" % k, gate="nbp")]
    return ts


def trc(rr):
    return [(x["direction"], x["position"], list(x["devices"]), x["shared_source"]) for x in rr["candidates"]]


out["c11"] = {"n2_all": trc(sd.find_differential_pair_candidates(br(2))), "n3_all": trc(sd.find_differential_pair_candidates(br(3)))}
json.dump(out, open(OUTP, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print(json.dumps(out, ensure_ascii=False, default=str)[:6000])
