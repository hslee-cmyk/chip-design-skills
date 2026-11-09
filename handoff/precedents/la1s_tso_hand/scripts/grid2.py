"""2차 스윕: 1차 경향(작은 Cc, 짧은 L3, 높은 gm/ID1이 전력 감소)을 따라 범위를 좁혀 다시 스윕."""
import itertools, json, sys, time
import design as D

out = open(sys.argv[1], "a", encoding="utf-8")
grid = {"g1": [17, 20, 24], "g3": [11, 14, 17], "g5": [11], "L1": [0.5e-6], "L3": [2.5e-7, 3.5e-7, 5e-7],
        "L5": [5e-7], "Cc": [0.3e-12, 0.45e-12, 0.6e-12]}
keys = list(grid)
t0 = time.time()
for vals in itertools.product(*[grid[k] for k in keys]):
    x = dict(zip(keys, vals))
    if x["g3"] > x["g1"]:
        continue
    try:
        s = D.solve_currents(x)
    except Exception as e:
        out.write(json.dumps({"x": x, "err": str(e)[:120]}) + "\n")
        continue
    if s is None:
        out.write(json.dumps({"x": x, "err": "pm_unreachable"}) + "\n")
        continue
    I1, I6, r = s
    out.write(json.dumps({"x": x, "I1": I1, "I6": I6, "gain_db": r["gain_db"], "gbw": r["gbw"], "pm": r["pm"],
                          "power_uW": r["power_W"] * 1e6, "min_sat": min(r["sat_margin"].values()),
                          "vcm": r["nodes"]["VCM"], "W": {k: v["W"] for k, v in r["dev"].items()}}) + "\n")
    out.flush()
out.write(json.dumps({"done": True, "sec": time.time() - t0}) + "\n")
