# M6b: sf_pushpull W_min 하한 출발점에서 M9 전류·R1c 가지 전류를 따로 올린다(요인 분리). 측정 엔진 = integ-it12.
import os
os.environ.setdefault("PG_ENGINE_ROOT", "C:/Users/HSLEE/Documents/Todoc/fpga/wt/integ-it12/skills/analog-gmid-design")
import ast
from pg_common import *
from gmid_engine.search.kernel import evaluate
CIR, RUN = "sf_pushpull_output_opamp", "NCd1"
OUT = HERE / "m6b_sf_factor.jsonl"
lut, pdk, rule = load_env()
a, b, sctx = build(CIR, lut, pdk, rule, budget_s=200.0)
fn = pathlib.Path(r"C:/Users/HSLEE/AppData/Local/Temp/la1a_pg_a/proto/out") / ("v2start_%s_k1_v2m_spec_%s.json" % (CIR, RUN))
theta = {ast.literal_eval(k): float(v) for k, v in json.loads(fn.read_text(encoding="utf-8"))["theta"].items()}
_v, _t, cells = l0._box_centre(sctx, sctx.rungs[0])
row0 = {"I": {k[1]: v for k, v in theta.items() if k[0] == "current"}, "R": {k[1]: v for k, v in theta.items() if k[0] == "resistance"}, "C": {k[1]: v for k, v in theta.items() if k[0] == "capacitance"}}
app(OUT, row0); print(row0)
mg = sctx.dc.base.value("graph", "start", "macro")
print("macro", [(str(k), float(v)) for k, v in mg.gm], [str(x)[:120] for x in mg.records])
for name, keys in (("M9", [("current", "M9")]), ("R1c", [("current", "R1c")]), ("R1ab", [("current", "R1a"), ("current", "R1b")])):
    for f in (1, 3, 10, 30, 100):
        t = dict(theta)
        for k in keys:
            t[k] = theta[k] * f
            r = ("resistance", k[1])
            if r in t:
                t[r] = theta[r] / f
        res = evaluate(sctx, t, cells, origin=(("stage", "pg"),))
        rows = {c.name.split(":")[-1][:8]: round(float(c.c), 3) for c in (res.constraints or ()) if c.name.startswith("ss:") and c.c is not None}
        rec = {"scale": name, "k": f, "status": res.status, "gbw": rows.get("gbw_ss_h"), "pm": rows.get("pm_ss_de"), "gain": rows.get("gain_ss_"), "noise": rows.get("noise_ex"), "P": res.objectives.power_w if res.objectives else None, "fail": None if res.failure is None else str(dict(res.failure.detail))[:100]}
        app(OUT, rec); print(rec)
