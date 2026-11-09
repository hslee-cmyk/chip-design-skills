"""design_for_layout -> LVS 기준 CDL (W = m·w_s, 더미 포함; Ibg·CL 은 이상 소자·측정 부하라 레이아웃 밖)."""
import json, sys
des = json.load(open(sys.argv[1], encoding="utf-8"))
model = {"nmos": "sky130_fd_pr__nfet_01v8", "pmos": "sky130_fd_pr__pfet_01v8"}
bulk = {"nmos": "gnd", "pmos": "vdd"}
pins = "vdd gnd vin_n vin_p out vb1 vb2 bias3"
L = ["* folded_cascode hand design for LVS (Ibg = ideal source between pins vb1/vb2, CL = measurement load: not drawn)",
     ".SUBCKT folded_cascode " + pins]
# 더미는 행 양 끝에서 같은 단자(끝 넷·레일)를 가지는 병렬 소자 -- 추출기가 병렬 소자를 하나로 합치므로 기준도 합친다
merged = {}
for n, d in list(des["devices"].items()):
    if d.get("dummy"):
        key = (d["kind"], d["d"], d["g"], d["s"], d["L"])
        if key in merged:
            merged[key]["m_w"] += d["w_s"] * d["m"]
        else:
            merged[key] = dict(d, name=n, m_w=d["w_s"] * d["m"])
devs = {n: dict(d, m_w=d["w_s"] * d["m"]) for n, d in des["devices"].items() if not d.get("dummy")}
devs.update({v["name"]: v for v in merged.values()})
for n, d in devs.items():
    W = d["m_w"] * 1e6
    inst = n if n.startswith("M") else "M" + n  # SPICE/CDL 첫 글자 = 소자 종류(M = MOSFET)
    L.append("%s %s %s %s %s %s w=%.6gu l=%.6gu" % (inst, d["d"], d["g"], d["s"], bulk[d["kind"]], model[d["kind"]], W, d["L"] * 1e6))
L.append(".ENDS")
open(sys.argv[2], "w", encoding="utf-8").write("\n".join(L) + "\n")
