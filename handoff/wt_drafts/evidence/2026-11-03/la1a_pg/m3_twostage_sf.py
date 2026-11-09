# M3: two_stage_ota_sf GBW 행 통과 수 19 -> 1 의 물리 결정자 분해. 측정 도구(엔진 무변경), 값은 재작성 범위·실현 가능성 입력.
# 1) base(as-built 하한 비활성) 와 d1(design D1 규칙) 칸 0 점의 원시 값(ugf, pm, gain, gm, W, Cc, cgg) 비교
# 2) 요인 분리: base 칸 0 에서 L 만 d1 값으로 / 칸 0 값 + Cc 스캔으로 'GBW 달성 가능 여부' 를 잰다(궤적 무관)
# 3) 외층 궤적: 봉인점마다 (seq, ugf, pm, gain, Cc, gm_M1, I_M6) -> 통과 수가 궤적 산물인지 본다.
# usage: m3_twostage_sf.py <mode: base|d1> [circuit]
import sys
from pg_common import *

ivc = sys.modules["gmid_engine.search.iv_context"]
from gmid_engine.metrics import ACH_KEY, ParamTables, block_spec
from gmid_engine.search.start_values import GainInputs
from gmid_engine.search import find_front
from gmid_engine.search.kernel import evaluate

MODE = sys.argv[1]
CIR = sys.argv[2] if len(sys.argv) > 2 else "two_stage_ota_sf"
OUT = HERE / "m3_twostage_sf.jsonl"


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


if MODE == "d1":
    ivc._gain_inputs = gain_inputs_d1
lut, pdk, rule = load_env()
a, b, sctx = build(CIR, lut, pdk, rule, budget_s=300.0)
rung = sctx.rungs[0]
variables, theta, cells, u = l0.centre_start(sctx, rung)
cons = {str(x.metric): x for x in sctx.ss_constraints}
macro = sctx.dc.base.value("graph", "start", "macro")
rows_col = dict(sctx.dc.base.column("device", "start.row"))


def raw(res):
    """봉인점 원시 값 -- 스냅샷 필드에서 읽음."""
    out = {"status": res.status, "seq": res.seq}
    th = dict(res.theta)
    for k, v in th.items():
        if k[0] == "capacitance":
            out["C_" + k[1]] = v
        if k[0] == "L" and k[1] in ("M1", "M5", "M6", "M8"):
            out["L_" + k[1]] = v
        if k[0] == "current":
            out["I_" + k[1]] = v
        if k[0] == "ln_idu" and k[1] in ("M1", "M6", "M8"):
            out["lnidu_" + k[1]] = v
    out["rows"] = {c.name.split(":")[-1]: round(float(c.c), 3) for c in (res.constraints or ()) if c.name.startswith(("ss:", "spec:")) and c.c is not None}
    if res.evaluation is not None and res.status == "sealed":
        snap = res.evaluation.snapshot
        for name in ("ugf_ss_hz", "pm_ss_deg", "gain_ss_db"):
            f = snap.field("graph", "metrics", name) if False else None
        try:
            ss = dict(snap.column("device", "ss"))
            for m in ("M1", "M6", "M8"):
                d = ss.get(m)
                if d is not None:
                    out["gm_" + m] = float(getattr(d, "gm", float("nan")))
                    out["gds_" + m] = float(getattr(d, "gds", float("nan")))
                    out["cgg_" + m] = float(getattr(d, "cgg", float("nan")))
            op = dict(snap.column("device", "dc_op"))
            for m in ("M1", "M6", "M8", "M7"):
                if m in op:
                    out["W_" + m] = float(op[m].W); out["Id_" + m] = float(op[m].ID) if hasattr(op[m], "ID") else None
        except Exception as exc:
            out["ss_err"] = repr(exc)[:200]
    return out


app(OUT, {"mode": MODE, "case": "macro", "gm": [(str(k), float(v)) for k, v in macro.gm] if macro and macro.gm else None, "rec": [str(r)[:200] for r in macro.records] if macro else None,
          "L_nm": {str(c[1]): round(v * 1e9) for c, v in rung.theta if c[0] == "L"}, "cap": [(str(c[1]), v) for c, v in rung.theta if c[0] == "capacitance"],
          "cur": [(str(c[1]), v) for c, v in rung.theta if c[0] == "current"], "lnidu": {str(c[1]): round(v, 3) for c, v in rung.theta if c[0] == "ln_idu"},
          "cons": {k: repr(v)[:160] for k, v in cons.items()}, "columns_hint": None})
res0 = evaluate(sctx, theta, cells, origin=(("stage", "pg"),))
app(OUT, {"mode": MODE, "case": "rung0", **raw(res0)})
# Cc 스캔(칸 0, 나머지 고정): GBW 물리 ≈ gm1/(2π Cc). 면적·PM 함께
cap_keys = [k for k in theta if k[0] == "capacitance"]
for f in (0.25, 0.5, 0.7, 1.0, 1.4, 2.0):
    t = dict(theta)
    for k in cap_keys:
        t[k] = theta[k] * f
    r = evaluate(sctx, t, cells, origin=(("stage", "pg"),))
    app(OUT, {"mode": MODE, "case": "cc_scan", "f": f, **raw(r)})
# 전류 스케일(입력쌍·2단 전류 ×k): 같은 밀도에서 gm ∝ I -- GBW 달성 가능성
cur_keys = [k for k in theta if k[0] == "current"]
for f in (0.5, 1.0, 1.5, 2.0, 3.0):
    t = dict(theta)
    for k in cur_keys:
        t[k] = theta[k] * f
    r = evaluate(sctx, t, cells, origin=(("stage", "pg"),))
    app(OUT, {"mode": MODE, "case": "i_scan", "f": f, **raw(r)})
if len(sys.argv) > 3:
    # 요인 분리 입력: 다른 모드 칸 0 의 L 을 이 θ 에 이식
    pass
fr = find_front(sctx, [])
pts = sorted((r for r in sctx.cache.values() if r.status == "sealed"), key=lambda r: r.seq)
app(OUT, {"mode": MODE, "case": "front", "n_front": len(getattr(fr, "front", ()) or ()), "n_sealed": len(pts), "points": [raw(r) for r in pts]})
print("done", MODE)
