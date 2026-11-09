# M7: PG-4 -- 값 선언 저항 가지 θ 전류(측정 대상 1/9). 나머지 θ 고정, RL 전류만 바꿔 출력 노드 전압·봉인·소신호 행을 잰다.
# 물리: 가지가 레일 agnd 로 닫히면 I_R = (V_out - V_agnd)/R 이고 θ ln 좌표는 I_R > 0 만 표현한다. 측정 엔진 = integ-it12.
import os, sys
os.environ.setdefault("PG_ENGINE_ROOT", "C:/Users/HSLEE/Documents/Todoc/fpga/wt/integ-it12/skills/analog-gmid-design")
import ast
from pg_common import *
from gmid_engine.search.kernel import evaluate
CIR, RUN = "nmcnr_amplifier", "NCd1"
OUT = HERE / "m7_rl_sweep.jsonl"
lut, pdk, rule = load_env()
a, b, sctx = build(CIR, lut, pdk, rule, budget_s=200.0)
fn = pathlib.Path(r"C:/Users/HSLEE/AppData/Local/Temp/la1a_pg_a/proto/out") / ("v2start_%s_k1_v2m_spec_%s.json" % (CIR, RUN))
theta = {ast.literal_eval(k): float(v) for k, v in json.loads(fn.read_text(encoding="utf-8"))["theta"].items()}
_v, _t, cells = l0._box_centre(sctx, sctx.rungs[0])
k = ("current", "RL")
for I in (theta[k], 1e-12, 1e-9, 1e-7, 1e-6, 4e-6, 1e-5, 2e-5, 3e-5, 3.5e-5):
    t = dict(theta); t[k] = I
    r = evaluate(sctx, t, cells, origin=(("stage", "pg"),))
    rows = {c.name.split(":")[-1]: round(float(c.c), 3) for c in (r.constraints or ()) if c.name.startswith("ss:") and c.c is not None}
    vout = None
    if r.evaluation is not None:
        try:
            vout = float(dict(r.evaluation.snapshot.column("node", "dc_v"))["Vout"])
        except Exception as exc:
            vout = repr(exc)[:80]
    app(OUT, {"I_RL": I, "status": r.status, "Vout": vout, "rows": rows, "fail": None if r.failure is None else str(dict(r.failure.detail))[:160]})
    print(I, r.status, vout, rows.get("gain_ss_db>="), rows.get("gbw_ss_hz>="), rows.get("pm_ss_deg>="))
print("done")
