"""b26pre 도달성 실험(b1 = HEAD + B34, 읽기 전용 import). 결과는 C:/g87/out/exp1.txt."""
import sys, json
A = "C:/g87/b1/skills/analog-gmid-design/assets"
sys.path.insert(0, A)
import sizing_recipe as sr  # noqa
import stick_diagram as sd  # noqa
OUT = open("C:/g87/out/exp1.txt", "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s); OUT.write(s + "\n"); OUT.flush()


lut = sr.build_toy_lut()
L, vds = 0.5e-6, 0.6
r = sr.size_transistor(gm=200e-6, gm_id=12.0, L=L, lut=lut, vds=vds)
gds = r.gm / lut.gm_gds_ratio(12.0, L, vds, 0.0)


def ctx_for(names, kind="nmos"):
    return sr.SizingContext(sized={n: {"ID": r.ID, "W": r.W, "L": L, "gm": r.gm, "gm_id": 12.0, "gds": gds,
                                        "kind": kind, "vds": vds, "vsb": 0.0} for n in names})


T = sr.Transistor
# 1. max_rounds=0, offset pair n_fingers=1
devs = [T("Ma", "nmos", source="Vtail", drain="Nd_a", gate="ga", n_fingers=1, finger_w=r.W),
        T("Mb", "nmos", source="Vtail", drain="Nd_b", gate="gb", n_fingers=1, finger_w=r.W)]
metrics = {"pair_area": {"type": "sum_area", "devices": ["Ma", "Mb"]}}
loose = [{"metric": "pair_area", "op": "<=", "value": 2 * r.W * L * 3.0}]
res = sr.run_matching_safety_with_finger_growth({"seg1": devs}, [("Ma", "Mb")], {("Ma", "Mb"): "offset"},
                                                 ctx_for(["Ma", "Mb"]), {"nmos": lut}, metrics, loose,
                                                 gm_id_bounds=(2.0, 28.0), max_rounds=0)
log("E1 max_rounds=0", res["unresolved_pair"], res["unresolved_reason"], res["audit"].ok, res["growth_rounds"],
    [(c.name, c.ok) for c in res["audit"].checks])
# 1b. max_rounds=1, loose -> growth applied in round 0, loop ends -> final repair
res = sr.run_matching_safety_with_finger_growth({"seg1": list(devs)}, [("Ma", "Mb")], {("Ma", "Mb"): "offset"},
                                                 ctx_for(["Ma", "Mb"]), {"nmos": lut}, metrics, loose,
                                                 gm_id_bounds=(2.0, 28.0), max_rounds=1)
log("E1b max_rounds=1", res["unresolved_pair"], res["unresolved_reason"], res["audit"].ok,
    [(g["round"], g["names"], g["result"]["applied"]) for g in res["growth_rounds"]],
    {k: [(t.name, t.n_fingers) for t in v] for k, v in res["rows"].items()})
# 1c. max_rounds=5 default loose
res = sr.run_matching_safety_with_finger_growth({"seg1": list(devs)}, [("Ma", "Mb")], {("Ma", "Mb"): "offset"},
                                                 ctx_for(["Ma", "Mb"]), {"nmos": lut}, metrics, loose,
                                                 gm_id_bounds=(2.0, 28.0))
log("E1c default loose", res["unresolved_pair"], res["unresolved_reason"], res["audit"].ok,
    [(g["round"], g["names"], g["result"]["applied"]) for g in res["growth_rounds"]],
    {k: [(t.name, t.n_fingers) for t in v] for k, v in res["rows"].items()}, res["ctx"].sized["Ma"]["W"] / r.W)

# 2. euler-blocked connected row, no pairs
star = [T("M1", "nmos", source="a", drain="x", gate="g1", n_fingers=1, finger_w=r.W),
        T("M2", "nmos", source="x", drain="b", gate="g2", n_fingers=1, finger_w=r.W),
        T("M3", "nmos", source="x", drain="c", gate="g3", n_fingers=1, finger_w=r.W)]
log("E2 build", {k: v.status for k, v in sd.build_stick_diagram([sr._dc_replace(t, stack_id="row") for t in star]).items()})
rows = {"row": [sr._dc_replace(t, stack_id="row") for t in star]}
res = sr.run_matching_safety_with_finger_growth(rows, [], {}, ctx_for(["M1", "M2", "M3"]), {"nmos": lut},
                                                 {}, [], gm_id_bounds=(2.0, 28.0))
log("E2 growth", res["unresolved_pair"], res["unresolved_reason"], res["audit"].ok,
    {k: [(t.name, t.stack_id) for t in v] for k, v in res["rows"].items()}, [(c.name, c.ok) for c in res["audit"].checks])
fr, fc = sr._fixup_euler_blocked_rows(rows, [], {}, ctx_for(["M1", "M2", "M3"]), {"nmos": lut}, {}, [])
log("E2 fixup direct", {k: [(t.name, t.stack_id) for t in v] for k, v in fr.items()})
# 2b. disconnected row
dis = [T("M1", "nmos", source="a", drain="b", gate="g1", n_fingers=1, finger_w=r.W),
       T("M2", "nmos", source="c", drain="d", gate="g2", n_fingers=1, finger_w=r.W)]
rows2 = {"row": [sr._dc_replace(t, stack_id="row") for t in dis]}
log("E2b build", {k: v.status for k, v in sd.build_stick_diagram(rows2["row"]).items()})
fr, fc = sr._fixup_euler_blocked_rows(rows2, [], {}, ctx_for(["M1", "M2"]), {"nmos": lut}, {}, [])
log("E2b fixup", {k: [(t.name, t.stack_id) for t in v] for k, v in fr.items()})
