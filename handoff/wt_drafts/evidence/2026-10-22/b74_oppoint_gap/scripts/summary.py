import json, math, sys
from pathlib import Path
import table
OUT = Path(r"C:\Users\HSLEE\Documents\Todoc\fpga\wt\_scratch_b74\out")
allrec = {}
for c in ("two_stage_ota", "ngcc_3stage_ff", "folded_cascode"):
    recs = table.rows(c); allrec[c] = recs
    print("==", c)
    print("dev  W_um    n1  wf1   vgs    vds    vsb   tolV | net: id  dVgs  vdsat | s1: id dVgs | s5: id dVgs gm gds vdsat(eng) | f5: id dVgs vdsat bin | total: id dVgs")
    for r in recs:
        def g(v, k, f="%.3f"):
            x = r.get(v + "." + k); return "-" if x is None else f % x
        print("%-4s %8.2f %4d %5.3f %.3f %.3f %.3f %.4f | %s %s %s | %s %s | %s %s %s %s %s(%s) | %s %s %s %s | %s %s" % (
            r["device"], r["W_um"], r["n"], r["wf_um"], r["vgs"], r["vds"], r["vsb"], r["dc_tol_v"],
            g("net", "id_ratio"), g("net", "dvgs_mV", "%+.1f"), g("net", "vdsat", "%.4f"),
            g("s1", "id_ratio"), g("s1", "dvgs_mV", "%+.1f"),
            g("s5", "id_ratio"), g("s5", "dvgs_mV", "%+.1f"), g("s5", "gm_ratio"), g("s5", "gds_ratio"), g("s5", "vdsat", "%.4f"), "%.4f" % (r["vdsat_eng"] or -1),
            g("f5", "id_ratio"), g("f5", "dvgs_mV", "%+.1f"), g("f5", "vdsat", "%.4f"), r.get("f5.bin"),
            g("total", "id_ratio"), g("total", "dvgs_mV", "%+.1f")))
(OUT / "summary_rows.json").write_text(json.dumps(allrec, indent=1), encoding="utf-8")
