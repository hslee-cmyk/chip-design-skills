import json, re, sys
a = json.load(open(sys.argv[1], encoding="utf-8"))
b = json.load(open(sys.argv[2], encoding="utf-8"))
print("status", a["status"], b["status"])
print("slices", len(a["luts"]), "slice_has_VDSAT all", all(v["slice_has_VDSAT"] for v in a["luts"].values()),
      "cap_grid_eq all", all(all(v.get("cap_grid_eq_slice", [True])) for v in a["luts"].values()))
chg = [0, 0, 0]
for k in a["luts"]:
    x, y = a["luts"][k], b["luts"][k]
    ev = x["edge"]["vds_min_v"], y["edge"]["vds_min_v"]
    eg = x["edge"]["vgs_min_v"], y["edge"]["vgs_min_v"]
    chg[0] += ev[0] != ev[1]
    chg[1] += eg[0] != eg[1] or x["edge"]["by_bin"] != y["edge"]["by_bin"]
    chg[2] += x["ref_vds"] != y["ref_vds"]
    if k in ("nmos/1000", "pmos/1000", "nmos/72", "pmos/84"):
        print(k, "vds_min", ev, "vgs_min", eg, "ref(A->B)", list(x["ref_vds"].values()), list(y["ref_vds"].values()), "bins", x["edge"]["by_bin"], y["edge"]["by_bin"])
print("slice changes vds_min/vgs_min/ref", chg)
for k in a.get("graph_start", {}):
    print("gs", k, a["graph_start"][k]["fp"] == b["graph_start"][k]["fp"])
print("inactive same", a.get("inactive") == b.get("inactive"), "conflicts same", a.get("conflicts") == b.get("conflicts"))
pat = re.compile(r"(\w+)=('[^']*'|[-\d.e]+|None)")
same_base = 0
for dev in a.get("rows", {}):
    x, y = a["rows"][dev], b["rows"][dev]
    same_base += x["fp"] == x["baseline_fp"]
    fx, fy = x["value"], y["value"]
    head_x = fx.split("sources=")[0]
    head_y = fy.split("sources=")[0]
    dx = dict(pat.findall(head_x)); dy = dict(pat.findall(head_y))
    print(dev, "A_is_baseline", x["fp"] == x["baseline_fp"], "B_is_baseline", y["fp"] == y["baseline_fp"], "point", x["point"], y["point"], {k: (dx[k], dy[k]) for k in dx if dx[k] != dy.get(k)})
    sx = re.findall(r"Bound\(quantity='(\w+)', side='(\w+)', source='([^']+)', value=([-\d.e]+)\)", fx)
    sy = re.findall(r"Bound\(quantity='(\w+)', side='(\w+)', source='([^']+)', value=([-\d.e]+)\)", fy)
    print("   only A:", sorted(set(sx) - set(sy))[:8])
    print("   only B:", sorted(set(sy) - set(sx))[:8])
print("A matching baseline", same_base, "of", len(a.get("rows", {})))
