# -*- coding: utf-8 -*-
import json
D = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-10-30/"
R = [json.loads(l) for l in open(D + "m_gc8a/results.jsonl", encoding="utf8")]
rows = []
iso_circ = []
for r in R:
    v = r["variants"]["biasFree"]; vf = r["variants"]["biasF"]
    nm = lambda comps: ", ".join((c["root"] + ("(입력점)" if c["has_input_point"] else "")) for c in comps) or "-"
    f = lambda k: str(v[k]["n"])
    if v["isolated_drain_only_nets"]:
        iso_circ.append(r["circuit"])
    rows.append("| %s | %d | %s | %s | %s | %s | %s / %s / %s / %s | %s |" % (
        r["circuit"], r["n_mos"], "선언" if r["input_declared"] else "pending",
        nm(v["floating_components"]), nm(vf["floating_components"]),
        ", ".join(v["isolated_drain_only_nets"]) or "-",
        f("I1_root_min"), f("I1x_any_net_of_floating"), f("I2_root_min_plus_isolated"), f("I2x_any_plus_isolated"),
        ",".join(r["kcl_zero_mos_nullspace"]) or "-"))
tab = "\n".join(rows)
body = open(D + "m_gc8a/md_template.txt", encoding="utf8").read()
body = body.replace("@@TAB@@", tab).replace("@@ISO@@", "%d회로(%s)" % (len(iso_circ), ", ".join(iso_circ)))
open(D + "m_gc8a_conduction_axis.md", "w", encoding="utf8").write(body)
print(tab)
print(iso_circ)
