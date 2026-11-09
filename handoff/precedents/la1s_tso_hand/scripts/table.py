import json, sys
r = json.load(open(sys.argv[1], encoding="utf-8"))
with open(sys.argv[2], "w", encoding="utf-8") as f:
    f.write("gain %.2f dB  gbw %.3f MHz  pm %.2f deg  power %.2f uW  Rz %.0f ohm  I1 %.3f uA  I6 %.2f uA\n" % (
        r["gain_db"], r["gbw_hz"] / 1e6, r["pm_deg"], r["power_uW"], r["Rz"], r["I1"] * 1e6, r["I6"] * 1e6))
    f.write("nodes %s\n" % {k: round(v, 4) for k, v in r["nodes"].items()})
    f.write("dev kind L[um] W[um] ID[uA] gm/ID VGS VDS VDSAT sat_margin gm[uS] gds[uS] CGS[fF] CDD[fF] w_s[um]\n")
    for n, p in r["dev"].items():
        f.write("%s %s %.3g %.3f %.3f %.2f %.3f %.3f %.3f %.3f %.2f %.4f %.2f %.2f %.2f\n" % (
            n, p["kind"], p["L"] * 1e6, p["W"] * 1e6, p["ID"] * 1e6, p["gm"] / p["ID"], p["VGS"], p["VDS"], p["VDSAT"],
            r["sat_margin"][n], p["gm"] * 1e6, p["gds"] * 1e6, p["caps"]["CGS"] * 1e15, p["caps"]["CDD"] * 1e15, p["w_s"] * 1e6))
