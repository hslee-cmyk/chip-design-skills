# N5b: 값 선언 R 회로의 V_out* = M301·M302 포화 여유 max-min. VDSAT 는 LUT 조회(측정 도구). I_RL 은 θ 로만 넣을 수 있어 V_out ≥ agnd 만 평가, 아래쪽 여유는 V_out 과 VDsat 로 계산.
from n0_common import *
from gmid_engine.lut.vdsat_query import vdsat
CIR, RUN = "nmcnr_amplifier", "RCd1"
OUT = HERE / "n5b_vstar.jsonl"
use_d1(RUN)
sctx = build_ctx(CIR, 40, 200.0)
theta = load_theta(CIR, RUN)
_v, _t, cells = l0._box_centre(sctx, sctx.rungs[0])
memo = sctx.dc.lut.memo
I301 = theta[("current", "M302")] - theta[("current", "RL")]
for I in (theta[("current", "RL")], 1e-7, 1e-6, 4e-6, 1.2e-5, 2.8e-5):
    t = dict(theta); t[("current", "RL")] = I; t[("current", "M302")] = I301 + I
    r, raw = ev(sctx, t, cells)
    ops = dict(r.evaluation.snapshot.column("device", "dc_op"))
    row = {"I_RL": I}
    vs = dict(r.evaluation.snapshot.column("node", "dc_v"))
    row["Vout"] = float(vs["Vout"])
    for m in ("M301", "M302"):
        o = ops[m]
        vd = float(vdsat(memo, o.kind, o.w_key, o.L, o.vgs, max(o.vds, 1e-3), max(o.vsb, 0.0)))
        row[m] = {"vds": round(float(o.vds), 4), "vdsat": round(vd, 4), "margin": round(float(o.vds) - vd, 4)}
    row["seal7_slack"] = next((dict(getattr(it, "detail", ()) or ()).get("slack_v") for it in r.evaluation.report.items if it.item == 7), None)
    row["seal7_worst"] = next((dict(getattr(it, "detail", ()) or ()).get("worst") for it in r.evaluation.report.items if it.item == 7), None)
    app(OUT, row); print(row, flush=True)
print("done")
