"""devtb.json -> 소자 대조 표(markdown). 비율은 SPICE(변형, 엔진 W 로 환산)/엔진. dVGS_eq = ln(ID_spice/ID_eng)/(gm/ID)_eng."""
import json
import math
import sys
from pathlib import Path

OUT = Path(r"C:\Users\HSLEE\Documents\Todoc\fpga\wt\_scratch_b74\out")


def rows(name):
    d = json.loads((OUT / f"{name}.devtb.json").read_text(encoding="utf-8"))
    lines = []
    for m, r in d["devices"].items():
        e = r["engine"]
        sd = r["spice_dev"]
        scale = {p["variant"]: p["scale"] for p in d["plan"] if p["device"] == m}
        rec = {"device": m, "W_um": e["W"] * 1e6, "n": int(r["netlist"]["m"]), "wf_um": r["netlist"]["w"] * 1e6,
               "vgs": e["vgs"], "vds": e["vds"], "vsb": e["vsb"], "id_eng": e["id"], "gm_id_eng": e["gm_id"],
               "dc_tol_v": e["dc_tol_v"], "vdsat_eng": e["vdsat"], "tol_vdsat": e["tol_vdsat"]}
        for v, s in sd.items():
            sc = scale[v]
            idv = abs(s["id"]) * sc
            rec[f"{v}.id_ratio"] = idv / e["id"]
            rec[f"{v}.dvgs_mV"] = 1e3 * math.log(idv / e["id"]) / e["gm_id"]
            rec[f"{v}.gm_ratio"] = abs(s["gm"]) * sc / e["gm"]
            rec[f"{v}.gds_ratio"] = abs(s["gds"]) * sc / e["gds"]
            rec[f"{v}.vdsat"] = s["vdsat"]
            rec[f"{v}.vth"] = s["vth"]
            rec[f"{v}.bin"] = (s.get("bin_wmin"), s.get("bin_wmax"), s.get("bin_lmin"), s.get("bin_lmax"))
        ic = r["spice_in_circuit_x0"]
        rec["circ.id"] = ic["id"]
        rec["circ.vgs"] = ic["vgs"]
        rec["circ.vds"] = ic["vds"]
        rec["circ.vdsat"] = ic["vdsat"]
        lines.append(rec)
    return lines


if __name__ == "__main__":
    for c in sys.argv[1:]:
        for rec in rows(c):
            print(c, json.dumps(rec, default=lambda x: round(x, 5) if isinstance(x, float) else x))
