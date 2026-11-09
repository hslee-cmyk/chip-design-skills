"""design_for_layout 으로 SPICE 1회(손가락별 기하 = 그 json 의 finger_geom). 결과 json 과 요약 줄 append.

usage: fc_run_spice.py <design_for_layout.json> <workdir> <stem> <summary.txt> [iref] [extra.json]
"""
import json, sys
import fc_spice as SP
import mismatch as MM

des = json.load(open(sys.argv[1], encoding="utf-8"))
sim = dict(des["sim"])
if len(sys.argv) > 5 and sys.argv[5] != "-":
    sim["iref"] = float(sys.argv[5])
extra = json.load(open(sys.argv[6], encoding="utf-8")) if len(sys.argv) > 6 else None
res = SP.run(SP.netlist(des, sim, extra), sys.argv[2], sys.argv[3])
mar = SP.sat_margins(res, des)
d = des["devices"]
gm = {n: res["dev"].get(n.upper(), {}).get("gm", float("nan")) * d[n]["m"] for n in ("M1", "M3", "M10")}
s1 = MM.sigma_vt("nmos", d["M1"]["L"], d["M1"]["w_s"], d["M1"]["m"])[0]
s3 = MM.sigma_vt("pmos", d["M3"]["L"], d["M3"]["w_s"], d["M3"]["m"])[0]
s10 = MM.sigma_vt("nmos", d["M10"]["L"], d["M10"]["w_s"], d["M10"]["m"])[0]
oe = (1 + ((gm["M3"] * s3) ** 2 + (gm["M10"] * s10) ** 2) / (gm["M1"] * s1) ** 2) ** 0.5
ne = 1 + (gm["M3"] + gm["M10"]) / gm["M1"]
real = {n: m for n, m in mar.items() if not n.startswith("DUM")}
res.update({"sim": sim, "margins": mar, "offset_excess": oe, "noise_excess_th": ne,
            "min_margin": min(real.values()) if real else None, "min_margin_dev": min(real, key=real.get) if real else None})
json.dump(res, open("%s/%s.json" % (sys.argv[2], sys.argv[3]), "w", encoding="utf-8"), indent=1)
with open(sys.argv[4], "a", encoding="utf-8") as f:
    f.write("%s | iref %.6g | A0 %s dB GBW %s MHz PM %s | P %s uW | out %.4f | min margin %.3f (%s) | oe %.3f ne %.3f\n" % (
        sys.argv[3], sim["iref"], res["a0db"], (res["fu"] or 0) / 1e6, res.get("pm"), (res.get("power_W") or 0) * 1e6,
        res.get("out") or float("nan"), res["min_margin"], res["min_margin_dev"], oe, ne))
