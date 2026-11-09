"""B2 재현 -- run_matching_safety_with_finger_growth가 돌려주는 relaxed_pairs[i]["interdig_ok"]와
반환 audit의 `3b.…[a/b]` 체크 ok가 다른 입력(검토 review_b26pre.md B1 `nohub_blocked`).
사용: python -B bf_repro.py <copy>   (C:/g106/<copy>의 엔진을 import). 결과는 stdout과 C:/g106/out/bf_<copy>.txt."""
import sys

copy = sys.argv[1] if len(sys.argv) > 1 else "base"
A = "C:/g106/%s/skills/analog-gmid-design/assets" % copy
sys.path.insert(0, A)
import json, os, tempfile  # noqa: E402
import sizing_recipe as sr  # noqa: E402
import stick_diagram as sd  # noqa: E402

lut = sr.build_toy_lut()
r = sr.size_transistor(gm=200e-6, gm_id=12.0, L=0.5e-6, lut=lut, vds=0.6)
W0 = r.W
S = {"ID": r.ID, "W": W0, "L": 0.5e-6, "gm": r.gm, "gm_id": 12.0, "gds": r.gm / lut.gm_gds_ratio(12.0, 0.5e-6, 0.6, 0.0),
     "kind": "nmos", "vds": 0.6, "vsb": 0.0}
T = sr.Transistor
ROW = [T("Ma", "nmos", source="n2", drain="n1", gate="ga", n_fingers=1, finger_w=W0, stack_id="seg1"),
       T("Mb", "nmos", source="n4", drain="n2", gate="gb", n_fingers=1, finger_w=W0, stack_id="seg1"),
       T("Mp", "nmos", source="n2", drain="n5", gate="gp", n_fingers=1, finger_w=W0, stack_id="seg1")]
d = tempfile.mkdtemp(prefix="bf_", dir="C:/g106/out")
topo = os.path.join(d, "bf.topology.json")
with open(topo, "w", encoding="utf-8") as fh:
    json.dump({"topology_name": "bf", "schema_version": "2.0", "supply_nets": ["vdd", "gnd"],
               "netlist": [{"name": t.name, "kind": t.kind, "source": t.source, "drain": t.drain, "gate": t.gate} for t in ROW],
               "symmetry": {"matching_pairs": [], "dispositions": []}}, fh)
ctx = sr.SizingContext(sized={t.name: dict(S) for t in ROW}, topology_path=topo)
metrics = {"pair_area": {"type": "sum_area", "devices": ["Ma", "Mb"]}}
loose = [{"metric": "pair_area", "op": "<=", "value": 2 * W0 * 0.5e-6 * 3.0}]

lines = ["copy=%s" % copy, "pre-check build_stick_diagram(ROW)['seg1'].status = %s" % sd.build_stick_diagram(ROW)["seg1"].status]
for mr in (1, 2, 3, 5):
    for mset in ("metrics", "empty"):
        m, c = (metrics, loose) if mset == "metrics" else ({}, [])
        res = sr.run_matching_safety_with_finger_growth({"seg1": list(ROW)}, [("Ma", "Mb")], {("Ma", "Mb"): "offset"}, ctx,
                                                        {"nmos": lut}, m, c, gm_id_bounds=(11.9, 12.1), max_rounds=mr)
        rp = res["relaxed_pairs"]
        c3b = [(ch.name, ch.ok) for ch in res["audit"].checks if ch.name.startswith("3b.")]
        lines.append("max_rounds=%d %s: reason=%s relaxed=%s | audit 3b=%s | rows=%s" % (
            mr, mset, res["unresolved_reason"], [(e["pair"], e["interdig_ok"]) for e in rp], c3b,
            {k: [t.name for t in v] for k, v in res["rows"].items()}))
out = "\n".join(lines)
print(out)
with open("C:/g106/out/bf_%s.txt" % copy, "w", encoding="utf-8") as fh:
    fh.write(out + "\n")
