# M3b: two_stage_ota_sf 칸 0 요인 분리 -- base θ 에서 한 요인씩 d1 값으로 바꿔 GBW·PM·gain 원시 값 변화를 잰다(궤적 무관).
# d1 칸 0 값은 m3_twostage_sf.jsonl 'macro' 행에서 읽지 않고 같은 규칙으로 컨텍스트를 두 번 만들어 얻는다. 엔진 무변경.
import sys
from pg_common import *
ivc = sys.modules["gmid_engine.search.iv_context"]
from gmid_engine.metrics import ACH_KEY, ParamTables, block_spec
from gmid_engine.search.start_values import GainInputs
from gmid_engine.search.kernel import evaluate
from gmid_engine.sizing import METRICS_KEY
CIR = "two_stage_ota_sf"
OUT = HERE / "m3b_factor.jsonl"
orig = ivc._gain_inputs


def gain_inputs_d1(p, views, lut, constraints):
    if not any(m == "gain_ss_db" and op == ">=" for m, op, _v in constraints):
        return None, (("gain_l", "constraint_not_declared"),)
    gain = dict(p.column("graph", "gain_checks")).get(ACH_KEY)
    view = next((v for v in views if v.kind == "transfer"), None)
    found = [b.found_db for b in gain.blocks]
    goal = max(float(v) for m, op, v in constraints if m == "gain_ss_db" and op == ">=")
    total = float(sum(found))
    local = p.value("graph", ACH_KEY, "local_inputs").view
    keep = [(block_spec(view, b, local), goal * f / total) for b, f in zip(view.blocks, found) if b.kind != "buffer"]
    return GainInputs(local, ParamTables(lut.memo, local.w_keys, local.grids), tuple(keep)), ()


lut, pdk, rule = load_env()
a, b, sb = build(CIR, lut, pdk, rule)
vb, tb, cb, _u = l0.centre_start(sb, sb.rungs[0])
ivc._gain_inputs = gain_inputs_d1
a2, b2, sd = build(CIR, lut, pdk, rule)
vd, td, cd, _u = l0.centre_start(sd, sd.rungs[0])
ivc._gain_inputs = orig


def metric(res, name):
    if res.evaluation is None:
        return None
    try:
        return float(res.evaluation.snapshot.value("graph", METRICS_KEY, name))
    except Exception:
        return None


def report(tag, ctx, th, cells):
    r = evaluate(ctx, th, cells, origin=(("stage", "pg"),))
    rows = {c.name.split(":")[-1]: round(float(c.c), 3) for c in (r.constraints or ()) if c.name.startswith("ss:") and c.c is not None}
    row = {"tag": tag, "status": r.status, "rows": rows, "fail": None if r.failure is None else str(dict(r.failure.detail))[:160]}
    if r.evaluation is not None:
        snap = r.evaluation.snapshot
        fields = {}
        for f in ("ugf_ss_hz", "pm_ss_deg", "gain_ss_db", "rout_ss_ohm", "gbw_ss_hz"):
            v = None
            for kind_key in (METRICS_KEY,):
                try:
                    v = snap.value("graph", kind_key, f)
                except Exception:
                    v = None
            fields[f] = getattr(v, "value", v)
        row["raw"] = {k: (float(v) if isinstance(v, (int, float)) else repr(v)[:50]) for k, v in fields.items()}
        op = dict(snap.column("device", "dc_op"))
        row["W_um"] = {m: round(op[m].W * 1e6, 2) for m in ("M1", "M6", "M8") if m in op}
    app(OUT, row)
    print(tag, r.status, rows.get("gbw_ss_hz>="), rows.get("pm_ss_deg>="), rows.get("gain_ss_db>="), row.get("raw"))


def mix(base, other, kinds):
    th = dict(base)
    for k, v in other.items():
        if k in th and k[0] in kinds:
            th[k] = v
    return th


report("base", sd, tb, cb)
report("d1", sd, td, cd)
report("base+L_d1", sd, mix(tb, td, ("L",)), cd)
report("base+lnidu_d1", sd, mix(tb, td, ("ln_idu",)), cb)
report("base+I_d1", sd, mix(tb, td, ("current",)), cb)
report("base+L+lnidu_d1", sd, mix(tb, td, ("L", "ln_idu")), cd)
report("base+L+I_d1", sd, mix(tb, td, ("L", "current")), cd)
for f in (0.7, 0.5):
    t = mix(tb, td, ("L",))
    t[("capacitance", "Cc")] = tb[("capacitance", "Cc")] * f
    report("base+L_d1,Cc*%.1f" % f, sd, t, cd)
    t = dict(tb); t[("capacitance", "Cc")] = tb[("capacitance", "Cc")] * f
    report("base,Cc*%.1f" % f, sd, t, cb)
app(OUT, {"tag": "theta", "base": {str(k): v for k, v in tb.items()}, "d1": {str(k): v for k, v in td.items()}})
print("done")
