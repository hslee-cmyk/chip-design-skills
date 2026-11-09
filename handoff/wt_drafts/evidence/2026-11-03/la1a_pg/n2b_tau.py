# N2b: N13 시상수 추정과 GBW 대응(조건부 기전 확인). τ = C_N13 × (R1c + 1/gm_M13). C_N13 = M14·M16·M20 Cgg(LUT caps). 손잡이 셋: M16 묶음 밀도, R1c 가지 전류(V_R 유지), 둘 다 고정한 기준.
# 판별: GBW 가 τ 하나의 함수로 모이는가. 한 노드 근사라 조건부. 결과 = n2b_tau.jsonl
from n0_common import *
from gmid_engine.lut import caps
CIR, RUN = "sf_pushpull_output_opamp", "NCd1"
OUT = HERE / "n2b_tau.jsonl"
use_d1(RUN)
sctx = build_ctx(CIR, 40, 280.0)
tg = targets(sctx)
theta = load_theta(CIR, RUN)
_v, _t, cells = l0._box_centre(sctx, sctx.rungs[0])
memo = sctx.dc.lut.memo


def tau_of(r):
    ops = dict(r.evaluation.snapshot.column("device", "dc_op"))
    C = 0.0
    det = {}
    for m in ("M14", "M16", "M20"):
        o = ops[m]
        c = caps(memo, o.kind, o.L, o.vgs, o.vds, o.vsb, o.W)
        C += float(c.cgg); det[m] = round(float(c.cgg) * 1e15, 1)
    o13 = ops["M13"]
    gm13 = o13.gm_id * o13.current
    R = dict(r.theta)[("resistance", "R1c")]
    tau = C * (R + 1 / gm13)
    return tau, det, gm13, R


def rep(tag, th):
    r, raw = ev(sctx, th, cells)
    row = {"tag": tag, "status": r.status, "judge": judge(tg, raw), "P_mW": None if not r.objectives else round(r.objectives.power_w * 1e3, 4)}
    if r.status == "sealed":
        tau, det, gm13, R = tau_of(r)
        row.update(tau_ns=round(tau * 1e9, 3), fp_MHz=round(1 / (2 * math.pi * tau) / 1e6, 3), cgg_fF=det, gm13_uS=round(gm13 * 1e6, 3), R=R)
    app(OUT, row)
    j = row["judge"]
    print(tag, r.status, "GBW", j.get("gbw_ss_hz", [None])[0], "PM", j.get("pm_ss_deg", [None])[0], "fp", row.get("fp_MHz"), "C", row.get("cgg_fF"), "R", row.get("R"), flush=True)


rep("start", theta)
for dv in (1, 2, 3, 4, 5, 6):
    t = dict(theta); t[("ln_idu", "M16")] = theta[("ln_idu", "M16")] + dv
    rep("M16+%d" % dv, t)
for k in (3, 10, 30, 100):
    t = dict(theta); t[("current", "R1c")] = theta[("current", "R1c")] * k; t[("resistance", "R1c")] = theta[("resistance", "R1c")] / k
    rep("IR1c x%d" % k, t)
print("done")
