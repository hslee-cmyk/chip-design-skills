# M6: 칸 0 미정 θ 전류를 W_min 하한(k=1)에서 k 배로 올릴 때 출발점 소신호 행이 어떻게 변하는가.
# 물리 질문: W_min 하한 출발점이 '매크로 망 밖 극점'을 얼마나 낮추는가(같은 ln IDu 에서 gm ∝ I). R 있는 가지는 V_R 유지(R ∝ 1/I).
# 측정 엔진 = integ-it12. usage: m6_floor_sweep.py <circuit> <run>
import os, sys
os.environ.setdefault("PG_ENGINE_ROOT", "C:/Users/HSLEE/Documents/Todoc/fpga/wt/integ-it12/skills/analog-gmid-design")
import ast
from pg_common import *
from gmid_engine.search.kernel import evaluate
CIR, RUN = sys.argv[1], sys.argv[2]
OUT = HERE / "m6_floor_sweep.jsonl"
lut, pdk, rule = load_env()
a, b, sctx = build(CIR, lut, pdk, rule, budget_s=200.0)
fn = pathlib.Path(r"C:/Users/HSLEE/AppData/Local/Temp/la1a_pg_a/proto/out") / ("v2start_%s_k1_v2m_spec_%s.json" % (CIR, RUN))
theta = {ast.literal_eval(k): float(v) for k, v in json.loads(fn.read_text(encoding="utf-8"))["theta"].items()}
_v, _t, cells = l0._box_centre(sctx, sctx.rungs[0])
given = {c for c, _v in sctx.rungs[0].theta}
unknown = [k for k in theta if k[0] == "current" and k not in given and "RL" not in k[1]]
names = [k[1] for k in unknown]
rkeys = {k[1]: ("resistance", k[1]) for k in unknown if ("resistance", k[1]) in theta}
for f in (1, 3, 10, 30, 100, 300, 1000):
    t = dict(theta)
    for k in unknown:
        t[k] = theta[k] * f
        if k[1] in rkeys:
            t[rkeys[k[1]]] = theta[rkeys[k[1]]] / f
    r = evaluate(sctx, t, cells, origin=(("stage", "pg"),))
    rows = {c.name.split(":")[-1]: round(float(c.c), 3) for c in (r.constraints or ()) if c.name.startswith("ss:") and c.c is not None}
    app(OUT, {"circuit": CIR, "run": RUN, "k": f, "names": names, "I": {k[1]: t[k] for k in unknown}, "status": r.status, "rows": rows, "unmeasured": [str(u)[:60] for u in (r.unmeasured or ())][:4],
              "power_w": r.objectives.power_w if r.objectives else None, "area_m2": r.objectives.area_m2 if r.objectives else None, "fail": None if r.failure is None else str(dict(r.failure.detail))[:140]})
print("done")
