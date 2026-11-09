# N6: two_stage_ota_sf 요인 분리를 원시 값으로(m3b 를 c 대신 Hz·deg·dB), 엔진 = design-v115(m3 와 같음). 궤적 통과 수는 eval_budget 40·None 둘 다.
import os
os.environ["PG_ENGINE_ROOT"] = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-v115/skills/analog-gmid-design"
from n0_common import *
CIR = "two_stage_ota_sf"
OUT = HERE / "n6_twostage_raw.jsonl"
orig = ivc._gain_inputs
sb = build_ctx(CIR, 40, 200.0)
vb, tb, cb, _u = l0.centre_start(sb, sb.rungs[0])
ivc._gain_inputs = gain_inputs_d1
sd = build_ctx(CIR, 40, 200.0)
vd, td, cd, _u = l0.centre_start(sd, sd.rungs[0])
tg = targets(sd)


def mix(base, other, kinds):
    t = dict(base)
    for k, v in other.items():
        if k in t and k[0] in kinds:
            t[k] = v
    return t


def rep(tag, ctx, th, cells):
    r, raw = ev(ctx, th, cells)
    row = {"tag": tag, "status": r.status, "judge": judge(tg, raw), "P_mW": None if not r.objectives else r.objectives.power_w * 1e3}
    app(OUT, row)
    print(tag, r.status, {k[:5]: v[0] for k, v in row["judge"].items() if k[:3] in ("gbw", "pm_", "gai")}, flush=True)


rep("base", sd, tb, cb)
rep("d1", sd, td, cd)
rep("base+L_d1", sd, mix(tb, td, ("L",)), cd)
rep("base+lnidu_d1", sd, mix(tb, td, ("ln_idu",)), cb)
rep("base+I_d1", sd, mix(tb, td, ("current",)), cb)
rep("base+L+lnidu_d1", sd, mix(tb, td, ("L", "ln_idu")), cd)
t = dict(td); t[("capacitance", "Cc")] = td[("capacitance", "Cc")] * 0.7
rep("d1,Cc*0.7", sd, t, cd)
t = dict(td)
for k in td:
    if k[0] == "current":
        t[k] = td[k] * 1.5
rep("d1,I*1.5", sd, t, cd)
ivc._gain_inputs = orig
for mode in ("base", "d1"):
    for eb in (40, None):
        ivc._gain_inputs = gain_inputs_d1 if mode == "d1" else orig
        s = build_ctx(CIR, eb, 280.0)
        log = []
        _o = km.ss_constraint_rows

        def w(bundle, declared, model_error=(), _o=_o):
            log.append({str(k.metric): v.value for k, v in bundle.entries})
            return _o(bundle, declared, model_error)
        km.ss_constraint_rows = w
        fr = find_front(s, [])
        km.ss_constraint_rows = _o
        tt = targets(s)
        gb = [x.get("gbw_ss_hz") for x in log if x.get("gbw_ss_hz") is not None]
        gn = [x.get("gain_ss_db") for x in log if x.get("gain_ss_db") is not None]
        row = {"tag": "outer", "mode": mode, "eval_budget": eb, "E_B": s.eval_budget, "n_front": len(getattr(fr, "front", ()) or ()), "points": len(log),
               "gbw_pass": sum(1 for v in gb if v >= tt["gbw_ss_hz"][1]), "gbw_max": max(gb) if gb else None, "gain_pass": sum(1 for v in gn if v >= tt["gain_ss_db"][1]), "gain_max": max(gn) if gn else None,
               "all_pass": sum(1 for x in log if all(x.get(m) is not None and (x[m] >= tt[m][1] if tt[m][0] == ">=" else x[m] <= tt[m][1]) for m in tt))}
        app(OUT, row)
        print(row, flush=True)
print("done")
