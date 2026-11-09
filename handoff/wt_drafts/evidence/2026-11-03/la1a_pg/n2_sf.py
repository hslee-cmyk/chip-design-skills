# N2: sf GBW 원인 재판정. (a) 같은 전류에서 M16 묶음 밀도만 바꿈(검증자 표 재현) (b) N13 시상수 추정과 GBW 대응(세 손잡이) (c) 가드·행 대조.
# 조건: 시제품 NCd1 출발 θ. 엔진 = integ-it12. 결과 = n2_sf.jsonl 케이스마다 append.
from n0_common import *
CIR, RUN = "sf_pushpull_output_opamp", "NCd1"
OUT = HERE / "n2_sf.jsonl"
use_d1(RUN)
sctx = build_ctx(CIR, 40, 280.0)
tg = targets(sctx)
theta = load_theta(CIR, RUN)
_v, _t, cells = l0._box_centre(sctx, sctx.rungs[0])
rows_col = dict(sctx.dc.base.column("device", "start.row"))
print("ties", [(rep, m) for rep, m in sctx.domain.ties if rep[0] == "ln_idu"])
print("lnidu vars", {k[1]: round(v, 2) for k, v in theta.items() if k[0] == "ln_idu"})
for m in ("M13", "M14", "M15", "M16", "M20", "M9", "M10", "M11", "M12"):
    r = rows_col.get(m)
    if r:
        app(OUT, {"case": "start_row", "m": m, "gm_lo": r.gm_id_lo, "gm_hi": r.gm_id_hi, "gm_chosen": r.gm_id_chosen, "ln_idu": r.ln_idu,
                  "L": r.l_chosen, "sources": [str(s)[:90] for s in r.sources][:12]})
res0, raw0 = ev(sctx, theta, cells)
op0 = dict(res0.evaluation.snapshot.column("device", "dc_op"))
print("DeviceOp attrs", [a for a in dir(next(iter(op0.values()))) if not a.startswith("_")])


def caps_of(snap):
    out = {}
    ss = dict(snap.column("device", "ss")) if False else {}
    return out


NET = {"N13_gates": ("M14", "M16", "M20"), "N12_gates": ("M13", "M15")}


def rep(tag, th, res_key=None):
    r, raw = ev(sctx, th, cells)
    row = {"case": "knob", "tag": tag, "status": r.status, "judge": judge(tg, raw), "fail": None if r.failure is None else str(dict(r.failure.detail))[:120],
           "P_mW": None if not r.objectives else round(r.objectives.power_w * 1e3, 4), "area_um2": None if not r.objectives else round(r.objectives.area_m2 * 1e12, 2)}
    if r.evaluation is not None:
        ops = dict(r.evaluation.snapshot.column("device", "dc_op"))
        if ops:
            row["W_um"] = {m: round(ops[m].W * 1e6, 2) for m in ("M9", "M10", "M13", "M14", "M15", "M16", "M20", "M11", "M12") if m in ops}
            row["gm_uS"] = {m: round(ops[m].gm * 1e6, 3) for m in ("M13", "M14", "M16", "M15") if m in ops and hasattr(ops[m], "gm")}
            row["cgg_fF"] = {}
            for m in ("M13", "M14", "M15", "M16", "M20"):
                o = ops.get(m)
                if o is not None:
                    for attr in ("cgg", "Cgg", "cgs"):
                        if hasattr(o, attr):
                            row["cgg_fF"][m] = round(getattr(o, attr) * 1e15, 2)
                            break
            R = dict(r.theta).get(("resistance", "R1c"))
            row["R1c"] = R
            cg = row["cgg_fF"]
            if all(m in cg for m in ("M14", "M16", "M20")) and "M13" in row["gm_uS"] and row["gm_uS"]["M13"] > 0:
                C = (cg["M14"] + cg["M16"] + cg["M20"]) * 1e-15
                tau = C * (R + 1e6 / row["gm_uS"]["M13"])
                row["tau_N13_ns"] = round(tau * 1e9, 3)
                row["fp_N13_MHz"] = round(1 / (2 * math.pi * tau) / 1e6, 3)
    app(OUT, row)
    print(tag, r.status, {k: v[0] for k, v in row["judge"].items() if k in ("gbw_ss_hz", "pm_ss_deg", "noise_excess_th", "offset_excess")}, row.get("fp_N13_MHz"), row.get("P_mW"))


rep("start", theta)
for dv in (1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0):
    t = dict(theta); t[("ln_idu", "M16")] = theta[("ln_idu", "M16")] + dv
    rep("M16 ln_idu +%g" % dv, t)
for f in (0.5, 0.2, 0.1, 0.05):
    t = dict(theta); t[("resistance", "R1c")] = theta[("resistance", "R1c")] * f
    rep("R1c x%g" % f, t)
for k in (3, 10, 30, 100):
    t = dict(theta); t[("current", "R1c")] = theta[("current", "R1c")] * k; t[("resistance", "R1c")] = theta[("resistance", "R1c")] / k
    rep("I_R1c x%g" % k, t)
for k in (3, 10, 30):
    t = dict(theta)
    t[("current", "R1c")] = theta[("current", "R1c")] * k; t[("resistance", "R1c")] = theta[("resistance", "R1c")] / k
    t[("current", "M9")] = theta[("current", "M9")] * k
    rep("both x%g" % k, t)
print("done")
