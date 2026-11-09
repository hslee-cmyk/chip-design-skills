import json, sys
rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8") if l.startswith("{")]
ok = [r for r in rows if "power_uW" in r and r["gain_db"] >= 57 and r["min_sat"] > 0]
ok.sort(key=lambda r: r["power_uW"])
with open(sys.argv[2], "w", encoding="utf-8") as f:
    f.write("total %d feasible %d\n" % (len(rows), len(ok)))
    for r in ok[:25]:
        x = r["x"]
        f.write("P=%.1fuW I1=%.2fu I6=%.1fu gain=%.1f pm=%.1f sat=%.3f vcm=%.3f | g1=%s g3=%s g5=%s L1=%.2g L3=%.2g L5=%.2g Cc=%.2gp | W6=%.1fu\n" % (
            r["power_uW"], r["I1"] * 1e6, r["I6"] * 1e6, r["gain_db"], r["pm"], r["min_sat"], r["vcm"],
            x["g1"], x["g3"], x["g5"], x["L1"] * 1e6, x["L3"] * 1e6, x["L5"] * 1e6, x["Cc"] * 1e12, r["W"]["M6"] * 1e6))
