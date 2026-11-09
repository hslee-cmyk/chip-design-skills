import json, sys
from pathlib import Path
EV = Path(r"C:\Users\HSLEE\Documents\Todoc\fpga\wt\_drafts\evidence\2026-10-22\it2c_spice_frame")
OUT = Path(r"C:\Users\HSLEE\Documents\Todoc\fpga\wt\_scratch_b74\out")
res = {}
for c in ("two_stage_ota", "ngcc_3stage_ff", "folded_cascode"):
    d = json.loads((OUT / f"{c}.circop.json").read_text(encoding="utf-8"))
    eng = json.loads((EV / "engine" / f"{c}.engine.json").read_text(encoding="utf-8"))
    an = json.loads((EV / "analysis" / f"{c}.analysis.json").read_text(encoding="utf-8"))
    it2c = {n: v["spice"] for n, v in an["configs"]["B"]["node_at_x0"].items()}
    print("==", c, "node: engine | (SPICE-engine mV) net m5 f5 | it2c_net")
    rows = {}
    for n, ve in sorted(d["engine_nodes"].items()):
        if n in ("gnd",) or n.lower() not in d["modes"]["net"]["nodes"]:
            continue
        diffs = {m: 1e3 * (d["modes"][m]["nodes"][n.lower()] - ve) for m in ("net", "m5", "f5")}
        rows[n] = dict(engine=ve, **{m + "_mV": x for m, x in diffs.items()}, it2c_net_mV=None if n not in it2c else 1e3 * (it2c[n] - ve))
        print("%-8s %.4f | %+8.1f %+8.1f %+8.1f | %s" % (n, ve, diffs["net"], diffs["m5"], diffs["f5"], "-" if n not in it2c else "%+.1f" % (1e3 * (it2c[n] - ve))))
    # slack VDS-VDSAT-tol per device
    tol = {r["device"]: r["tol"] for r in eng["rows"]}
    sl = {}
    print("   device slack (V): engine | net m5 f5")
    for r in eng["rows"]:
        m = r["device"]
        se = r["vds"] * 1 - r["vdsat"] - r["tol"]
        vals = {}
        for mode in ("net", "m5", "f5"):
            dv = d["modes"][mode]["devices"].get(m)
            vals[mode] = None if dv is None else abs(dv["vds"]) - abs(dv["vdsat"]) - r["tol"]
        sl[m] = dict(engine=se, **vals)
        print("   %-4s %+.4f | %+.4f %+.4f %+.4f" % (m, se, vals["net"], vals["m5"], vals["f5"]))
    res[c] = {"nodes": rows, "slack": sl}
(OUT / "circ_cmp.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
