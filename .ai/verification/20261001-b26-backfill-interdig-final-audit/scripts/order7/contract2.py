"""계약 2(바뀌지 않는 것)·V10(card '재현') 대조 -- auditor 독립 스크립트(test 파일을 import하지 않는다).
usage: python -P contract2.py <clone_root> <workdir> <out.json>
입력은 spec card '재현'·'관찰 가능한 계약' 문장에서 직접 만든다:
  행 seg1 = [Ma(n2,n1,ga), Mb(n4,n2,gb), Mp(n2,n5,gp)], nmos, n_fingers 1, finger_w W0, stack_id seg1,
  W0·S = size_transistor(gm=200e-6, gm_id=12.0, L=0.5e-6, lut=toy_lut, vds=0.6), 매칭 [(Ma,Mb)] offset,
  lut_by_kind {nmos: toy_lut}, constraints [], gm_id_bounds (11.9, 12.1), max_rounds m.
  metrics: 없음 = {}, 있음 = {"pair_area": sum_area [Ma, Mb]}(selftest L4d와 같은 꼴, constraints는 []).
추가 입력(계약 2 범위 넓히기): 반환 자리 (iii)(iv) -- 둘째 쌍 (Mc,Mx) 없음 / (Mc,Md) finger_w None / n_fingers 1·2,
  allow_layout_relaxation=False(gm_id_violation), 3b만 남는 경우(매칭 쌍 하나가 같은 행 offset -- 판정은 출력 그대로).
반환에서 rows·audit 체크·unresolved_*·growth_rounds 길이·relaxed_pairs 전부를 적고, relaxed 쌍마다 반환 audit 3b ok를 함께 적는다."""
import json, os, sys

root, work, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
assets = os.path.join(root, "skills", "analog-gmid-design", "assets")
sys.path.insert(0, assets)
import sizing_recipe as sr  # noqa: E402

assert os.path.normcase(os.path.abspath(sr.__file__)).startswith(os.path.normcase(os.path.abspath(assets))), sr.__file__
os.makedirs(work, exist_ok=True)
lut = sr.build_toy_lut()
L, GMID, VDS = 0.5e-6, 12.0, 0.6
r = sr.size_transistor(gm=200e-6, gm_id=GMID, L=L, lut=lut, vds=VDS)
W0 = r.W
S = {"ID": r.ID, "W": W0, "L": L, "gm": r.gm, "gm_id": GMID,
     "gds": r.gm / lut.gm_gds_ratio(GMID, L, VDS, 0.0), "kind": "nmos", "vds": VDS, "vsb": 0.0}


def T(name, s, d, g, fw=W0, sid="seg1", nf=1):
    return sr.Transistor(name, "nmos", source=s, drain=d, gate=g, n_fingers=nf, finger_w=fw, stack_id=sid)


def seg1():
    return [T("Ma", "n2", "n1", "ga"), T("Mb", "n4", "n2", "gb"), T("Mp", "n2", "n5", "gp")]


METRICS = {"none": {}, "pair_area": {"pair_area": {"type": "sum_area", "devices": ["Ma", "Mb"]}}}


def run(label, rows, pairs, sens, m, metrics, allow=True):
    devs = [t for v in rows.values() for t in v]
    doc = {"topology_name": "c2", "schema_version": "2.0", "supply_nets": ["vdd", "gnd"],
           "netlist": [{"name": t.name, "kind": t.kind, "source": t.source, "drain": t.drain, "gate": t.gate}
                       for t in devs],
           "symmetry": {"matching_pairs": [], "dispositions": []}}
    p = os.path.join(work, label + ".topology.json")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2)
    ctx = sr.SizingContext(sized={t.name: dict(S) for t in devs}, topology_path=p)
    res = sr.run_matching_safety_with_finger_growth(
        rows, pairs, sens, ctx, {"nmos": lut}, METRICS[metrics], [],
        gm_id_bounds=(11.9, 12.1), max_rounds=m, allow_layout_relaxation=allow)
    checks = [(c.name, bool(c.ok)) for c in res["audit"].checks]
    rp = []
    for e in res["relaxed_pairs"]:
        a, b = e["pair"]
        c3b = [c for c in res["audit"].checks if c.name.startswith("3b.") and f"[{a}/{b}]" in c.name]
        rp.append({"pair": list(e["pair"]), "reason": e["reason"], "trim_recommended": e["trim_recommended"],
                   "interdig_ok": e["interdig_ok"], "audit_3b": [(c.name, bool(c.ok)) for c in c3b],
                   "consistent": len(c3b) == 1 and e["interdig_ok"] is c3b[0].ok})
    return {"label": label, "m": m, "metrics": metrics, "allow_layout_relaxation": allow,
            "rows": {k: [[t.name, t.n_fingers, t.stack_id] for t in v] for k, v in res["rows"].items()},
            "audit_ok": bool(res["audit"].ok), "audit_checks": checks,
            "unresolved_pair": list(res["unresolved_pair"]) if isinstance(res["unresolved_pair"], tuple) else res["unresolved_pair"],
            "unresolved_reason": res["unresolved_reason"], "growth_rounds_len": len(res["growth_rounds"]),
            "relaxed_pairs": rp}


cases = []
for metrics in ("none", "pair_area"):
    for m in (1, 2, 3, 5):
        cases.append(run(f"repro_m{m}_{metrics}", {"seg1": seg1()}, [("Ma", "Mb")], {("Ma", "Mb"): "offset"}, m, metrics))
    off2 = {("Ma", "Mb"): "offset", ("Mc", "Mx"): "offset"}
    cases.append(run(f"pnf_{metrics}", {"seg1": seg1(), "seg2": [T("Mc", "vt", "nc", "gc", sid="seg2")]},
                     [("Ma", "Mb"), ("Mc", "Mx")], off2, 3, metrics))
    off3 = {("Ma", "Mb"): "offset", ("Mc", "Md"): "offset"}
    cases.append(run(f"nofw_{metrics}", {"seg1": seg1(), "seg2": [T("Mc", "vt", "nc", "gc", fw=None, sid="seg2"),
                                                                 T("Md", "vt", "nd", "gd", fw=None, sid="seg2")]},
                     [("Ma", "Mb"), ("Mc", "Md")], off3, 3, metrics))
    cases.append(run(f"gna_{metrics}", {"seg1": seg1(), "seg2": [T("Mc", "vt", "nc", "gc", sid="seg2", nf=1),
                                                                T("Md", "vt", "nd", "gd", sid="seg2", nf=2)]},
                     [("Ma", "Mb"), ("Mc", "Md")], off3, 3, metrics))
    cases.append(run(f"gmidv_{metrics}", {"seg1": seg1()}, [("Ma", "Mb")], {("Ma", "Mb"): "offset"}, 3, metrics, allow=False))
    # 같은 행 공통 source offset 쌍(정리할 일 없는 행) -- 무동작 대조
    cases.append(run(f"plain_{metrics}", {"seg1": [T("Ma", "vt", "n1", "ga"), T("Mb", "vt", "n2", "gb")]},
                     [("Ma", "Mb")], {("Ma", "Mb"): "offset"}, 3, metrics))

out = {"root": root, "sizing_recipe": sr.__file__, "W0": W0, "PYTHONHASHSEED": os.environ.get("PYTHONHASHSEED"),
       "cases": cases}
with open(out_path, "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=1)
for c in cases:
    print(c["label"], c["unresolved_reason"], c["growth_rounds_len"], sorted(c["rows"]),
          [(e["pair"], e["interdig_ok"], [x[1] for x in e["audit_3b"]], e["consistent"]) for e in c["relaxed_pairs"]])
