"""SPICE gm(손가락당 × m)과 Pelgrom σ 로 offset 가드(offset_excess <= sqrt2)와 잡음 가드(1 + gm3/gm1 <= 2) 손 판정."""
import json, sys
import mismatch as MM
des = json.load(open(sys.argv[1], encoding="utf-8"))
sp = json.load(open(sys.argv[2], encoding="utf-8"))
d = des["devices"]
gm1 = sp["dev"]["M1"]["gm"] * d["M1"]["m"]
gm3 = sp["dev"]["M3"]["gm"] * d["M3"]["m"]
s1, n1 = MM.sigma_vt("nmos", d["M1"]["L"], d["M1"]["w_s"], d["M1"]["m"])
s3, n3 = MM.sigma_vt("pmos", d["M3"]["L"], d["M3"]["w_s"], d["M3"]["m"])
oe = MM.offset_excess(gm1, gm3, s1, s3)
with open(sys.argv[3], "w", encoding="utf-8") as f:
    json.dump({"gm1": gm1, "gm3": gm3, "sigma1_mV": s1 * 1e3, "slope1": n1, "sigma3_mV": s3 * 1e3, "slope3": n3,
               "offset_excess": oe, "offset_ok": oe <= 2 ** 0.5, "noise_excess_th": 1 + gm3 / gm1,
               "noise_ok": 1 + gm3 / gm1 <= 2}, f, indent=1)
