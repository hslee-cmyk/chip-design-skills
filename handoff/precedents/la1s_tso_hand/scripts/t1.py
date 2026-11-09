import json, sys, time
import design as D
x = {"g1": 17, "g3": 11, "g5": 11, "L1": 1e-6, "L3": 1e-6, "L5": 1e-6, "Cc": 1e-12}
t = time.time()
r = D.evaluate(x, 20e-6, 100e-6)
t1 = time.time() - t
t = time.time()
s = D.solve_currents(x)
t2 = time.time() - t
with open(sys.argv[1], "a", encoding="utf-8") as f:
    f.write(json.dumps({"eval_s": t1, "gain": r["gain_db"], "gbw": r["gbw"], "pm": r["pm"], "nodes": r["nodes"],
                        "sat": r["sat_margin"]}) + "\n")
    if s:
        I1, I6, r2 = s
        f.write(json.dumps({"solve_s": t2, "I1": I1, "I6": I6, "gain": r2["gain_db"], "gbw": r2["gbw"], "pm": r2["pm"],
                            "W": {k: v["W"] for k, v in r2["dev"].items()}}) + "\n")
    else:
        f.write("solve None %.1f\n" % t2)
