import json, sys, collections, glob, os
def load(tag):
    return [json.loads(l) for l in open(f"results2_{tag}.jsonl", encoding="utf-8")]
def recordonly(p1, p2):
    """count record-only / review / stop firings (GB2 stop reasons) in transfer view, forward cells only where cell-level"""
    F = set(p1["forward"])
    stops = []
    for d in p2["rule9"]["a_forward"]: stops.append(("9a", d))
    for d in p2["rule9"]["c"]: stops.append(("9c", d["block"] + "@" + d["out"]))
    for k, v in p1["cells"].items():
        if v == "CSCD_review": stops.append(("dual_out", k))
    for g in p1["pass3"]: stops.append(("pass3", g))
    for cy in p2["cycles"]:
        for kk in cy["klass"].split("|"):
            if "4" in kk.split("+"): stops.append(("loop4", "-".join(cy["nodes"])))
            if "nah_2active" in kk: stops.append(("loop_nah", "-".join(cy["nodes"])))
            if "3a" in kk.split("+"): stops.append(("loop3a_unimpl", "-".join(cy["nodes"])))
    for n, k in p1["drive_kind"].items():
        if n in F and (k.startswith("REVIEW") or k.startswith("UNDEF") or k == "TAP"): stops.append(("drive_" + k, n))
    for x in p1["undefined_start"]: stops.append(("undef_start", x[0]))
    for m in p2["residual_merges"]: stops.append(("residual_merge(DEC81 or multi-input)", m["node"]))
    for d in p2["dec63"]:
        if d["kind"] != "buffer": stops.append(("dec63_multi", d["u"]))
    for o in p2["block_overlap"]: stops.append(("block_overlap", f"{o[0]}/{o[1]}:{o[2]}"))
    return stops
tags = sys.argv[1:]
for tag in tags:
    print("########", tag)
    for r in load(tag):
        p1, p2 = r["part1"], r["part2"]
        st = recordonly(p1, p2)
        cnt = collections.Counter(s[0] for s in st)
        print(f"  {p1['circuit'][:28]:28s} cyc={p2['n_cycles_node']:3d} cls={p2['cycle_class_node']} starts={len(p1['starts'])} stops={dict(cnt)}")
