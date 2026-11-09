"""고른 설계점의 소자표·노드·성능을 파일로 쓴다(손계산 결과 기록)."""
import json, math, sys
import design as D

x = json.loads(sys.argv[1])
ws = json.loads(sys.argv[3]) if len(sys.argv) > 3 else None
if "I1" in x:
    I1, I6 = x.pop("I1"), x.pop("I6")
    r = D.evaluate(x, I1, I6, ws)
else:
    I1, I6, r = D.solve_currents(x)
rec = {"x": x, "I1": I1, "I6": I6, "ws": ws, "gain_db": r["gain_db"], "gbw_hz": r["gbw"], "pm_deg": r["pm"],
       "power_uW": r["power_W"] * 1e6, "Rz": r["Rz"], "nodes": r["nodes"],
       "dev": {n: {k: (v if not isinstance(v, dict) else v) for k, v in p.items()} for n, p in r["dev"].items()},
       "sat_margin": r["sat_margin"]}
with open(sys.argv[2], "w", encoding="utf-8") as f:
    json.dump(rec, f, indent=1)
