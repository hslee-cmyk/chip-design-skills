"""독립 확인: review_b26pre의 backfill 구별 입력(nohub_blocked)을 b1 원본·변이 2종에 돌린다. 출력 C:/g103/out/exp_backfill3.txt"""
import sys
sys.argv = ["x"]
sys.path.insert(0, "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/b26_reconcile")
import exp_backfill as E  # noqa: E402

sr0, LUT, T = E.sr0, E.LUT, E.T
r = sr0.size_transistor(gm=200e-6, gm_id=12.0, L=0.5e-6, lut=LUT, vds=0.6)
W0 = r.W
S = {"ID": r.ID, "W": W0, "L": 0.5e-6, "gm": r.gm, "gm_id": 12.0,
     "gds": r.gm / LUT.gm_gds_ratio(12.0, 0.5e-6, 0.6, 0.0), "kind": "nmos", "vds": 0.6, "vsb": 0.0}
out = open("C:/g103/out/exp_backfill3.txt", "w", encoding="utf-8")
for mx in (1, 2, 3, 5):
    row = [T("Ma", "nmos", source="n2", drain="n1", gate="ga", n_fingers=1, finger_w=W0, stack_id="seg1"),
           T("Mb", "nmos", source="n4", drain="n2", gate="gb", n_fingers=1, finger_w=W0, stack_id="seg1"),
           T("Mp", "nmos", source="n2", drain="n5", gate="gp", n_fingers=1, finger_w=W0, stack_id="seg1")]
    ctx = sr0.SizingContext(sized={t.name: dict(S) for t in row}, topology_path=None)
    for k, m in E.MODS.items():
        res = m.run_matching_safety_with_finger_growth({"seg1": list(row)}, [("Ma", "Mb")], {("Ma", "Mb"): "offset"}, ctx,
                                                       {"nmos": LUT}, {}, [], gm_id_bounds=(11.9, 12.1), max_rounds=mx)
        c3b = [c.ok for c in res["audit"].checks if c.name.startswith("3b.")]
        out.write("max_rounds=%d %-9s interdig_ok=%s audit3b=%s reason=%s rows=%s\n" % (
            mx, k, [e["interdig_ok"] for e in res["relaxed_pairs"]], c3b, res["unresolved_reason"],
            {rn: [t.name for t in v] for rn, v in res["rows"].items()}))
out.close()
print(open("C:/g103/out/exp_backfill3.txt", encoding="utf-8").read())
