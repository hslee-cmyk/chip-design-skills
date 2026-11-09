# M5: 시제품이 받아들인 출발 θ(v2start) 를 커널로 다시 평가해 성능 행과 전류·gm 을 재고, 그 점 하나에서 as-built 외층(start 강제)을 돈다.
# 측정 엔진 = integ-it12(시제품과 같은 base). usage: m5_eval_start.py <circuit> <run> [--front]
import os, sys
os.environ.setdefault("PG_ENGINE_ROOT", "C:/Users/HSLEE/Documents/Todoc/fpga/wt/integ-it12/skills/analog-gmid-design")
import ast
from pg_common import *

ivc = sys.modules["gmid_engine.search.iv_context"]
ff = sys.modules["gmid_engine.search.find_front"]
from gmid_engine.metrics import ACH_KEY, ParamTables, block_spec
from gmid_engine.search.start_values import GainInputs
from gmid_engine.search import find_front
from gmid_engine.search.kernel import evaluate

CIR, RUN = sys.argv[1], sys.argv[2]
FRONT = "--front" in sys.argv
OUT = HERE / "m5_eval_start.jsonl"
if RUN.endswith("d1"):
    def gain_inputs_d1(p, views, lut, constraints):
        if not any(m == "gain_ss_db" and op == ">=" for m, op, _v in constraints):
            return None, (("gain_l", "constraint_not_declared"),)
        gain = dict(p.column("graph", "gain_checks")).get(ACH_KEY)
        view = next((v for v in views if v.kind == "transfer"), None)
        found = [b.found_db for b in gain.blocks] if gain is not None else []
        goal = max(float(v) for m, op, v in constraints if m == "gain_ss_db" and op == ">=")
        if gain is None or view is None or not gain.blocks or len(view.blocks) != len(gain.blocks) or any(f is None for f in found):
            return None, (("gain_l", "found_db_missing"),)
        total = float(sum(found))
        local = p.value("graph", ACH_KEY, "local_inputs").view
        keep = [(block_spec(view, b, local), goal * f / total) for b, f in zip(view.blocks, found) if b.kind != "buffer"]
        return GainInputs(local, ParamTables(lut.memo, local.w_keys, local.grids), tuple(keep)), ()
    ivc._gain_inputs = gain_inputs_d1

lut, pdk, rule = load_env()
a, b, sctx = build(CIR, lut, pdk, rule, budget_s=200.0)
fn = pathlib.Path(r"C:/Users/HSLEE/AppData/Local/Temp/la1a_pg_a/proto/out") / ("v2start_%s_k1_v2m_spec_%s.json" % (CIR, RUN))
row = {"circuit": CIR, "run": RUN, "start_file": fn.exists()}
if sctx is None or not fn.exists():
    app(OUT, row); raise SystemExit
theta = {ast.literal_eval(k): float(v) for k, v in json.loads(fn.read_text(encoding="utf-8"))["theta"].items()}
_v, _t, cells = l0._box_centre(sctx, sctx.rungs[0])


def rows_of(res):
    return {c.name.split(":")[-1]: round(float(c.c), 3) for c in (res.constraints or ()) if c.name.startswith(("ss:", "spec:")) and c.c is not None}


res = evaluate(sctx, theta, cells, origin=(("stage", "pg"),))
row["hard_rows"] = sorted(((c.name, round(float(c.c), 3)) for c in (res.constraints or ()) if not c.name.startswith(("ss:", "spec:")) and c.c is not None), key=lambda x: x[1])[:6]
row.update(status=res.status, fail=None if res.failure is None else str(dict(res.failure.detail))[:300], rows=rows_of(res),
           currents={k[1]: v for k, v in theta.items() if k[0] == "current"},
           power_w=res.objectives.power_w if res.objectives else None, area_m2=res.objectives.area_m2 if res.objectives else None,
           L_nm={k[1]: round(v * 1e9) for k, v in theta.items() if k[0] == "L"})
if FRONT and res.status in l0.ACCEPTED_STATUSES:
    start = l0.StartPoint("layer0", res.theta, cells, l0.SOURCE_LAYER0)
    lr = l0.Layer0Result(start, 0.0, True, "pg_forced", None, res.status, None, 0, 0, (), (), 0, (), 0, RUN)
    ff.layer0_start = lambda s, origin=(): lr
    try:
        t1 = time.time()
        fr = find_front(sctx, [])
        pts = [r for r in sctx.cache.values() if r.status == "sealed"]
        agg = {}
        for r in pts:
            for k, v in rows_of(r).items():
                z = agg.setdefault(k, [0, -1e99]); z[0] += int(v >= 0); z[1] = max(z[1], v)
        row["front"] = {"n_front": len(getattr(fr, "front", ()) or ()), "n_sealed": len(pts), "rows": agg, "s": round(time.time() - t1, 1)}
    except Exception:
        row["front_error"] = traceback.format_exc()[-700:]
app(OUT, row)
print("done", CIR, RUN, row.get("status"), row.get("rows"))
