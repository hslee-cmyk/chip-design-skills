# N5: PG-4 값 선언 저항 가지 쓰기 순서. nmcnr: S 전류(M301 = gm_b/g)를 고정하고 I_RL 을 바꾼다(M302 = M301 + I_RL, 기저 행 그대로). V_out 대 포화 여유·소신호 행.
# 물리: M301·M302 포화 여유 max-min 이 V_out* 를 정한다(전류 scale 무관). I_RL = (V_out* − V_agnd)/R. V_out* < V_agnd 면 θ ln 좌표로 못 쓴다(스키마 제거만 표현).
# 스키마 제거안(O-169)은 엔진 수정 금지라 '같은 동작점 값'을 θ 로 넣어 근사(표지). 결과 = n5_rl.jsonl
from n0_common import *
CIR, RUN = "nmcnr_amplifier", "NCd1"
OUT = HERE / "n5_rl.jsonl"
use_d1(RUN)
sctx = build_ctx(CIR, 40, 200.0)
tg = targets(sctx)
theta = load_theta(CIR, RUN)
_v, _t, cells = l0._box_centre(sctx, sctx.rungs[0])
rows_col = dict(sctx.dc.base.column("device", "start.row"))
macro = sctx.dc.base.value("graph", "start", "macro")
gm = dict((str(k), float(v)) for k, v in macro.gm)
gm_req = gm["('Vout',)"]
I301_gm = gm_req / rows_col["M301"].gm_id_chosen
app(OUT, {"case": "inputs", "gm_req": gm_req, "I301_gm": I301_gm, "gm_id_301": rows_col["M301"].gm_id_chosen, "pins": {m: dict(dict(sctx.dc.base.column("device", "pins"))[m]) for m in ("M301", "M302")}, "kinds": {m: dict(sctx.dc.base.column("device", "kind"))[m] for m in ("M301", "M302")}})
for tagI, I301 in (("I301=floor(NC)", theta[("current", "M302")] - theta[("current", "RL")]), ("I301=gm eq", I301_gm)):
    for I in (theta[("current", "RL")], 1e-9, 1e-7, 1e-6, 2e-6, 4e-6, 8e-6, 1.2e-5, 1.6e-5, 2e-5, 2.4e-5, 2.8e-5, 3.2e-5):
        t = dict(theta)
        t[("current", "RL")] = I
        t[("current", "M302")] = I301 + I
        r, raw = ev(sctx, t, cells)
        vout = None; seal = {}
        if r.evaluation is not None:
            vs = dict(r.evaluation.snapshot.column("node", "dc_v"))
            vout = float(vs.get("Vout")) if vs.get("Vout") is not None else None
        for c in (r.constraints or ()):
            if c.name.startswith(("seal7:M301", "seal7:M302", "seal7_sat:M301", "seal7_sat:M302")) or (":M301" in c.name or ":M302" in c.name):
                seal[c.name] = round(float(c.c), 3)
        row = {"case": tagI, "I_RL": I, "Vout": vout, "status": r.status, "judge": judge(tg, raw), "seal": seal, "fail": None if r.failure is None else str(dict(r.failure.detail))[:160]}
        app(OUT, row)
        print(tagI, "%.3g" % I, r.status, vout, {k: v[0] for k, v in row["judge"].items() if k in ("gain_ss_db", "gbw_ss_hz", "pm_ss_deg", "swing_out_v")}, {k: v for k, v in seal.items() if "seal" in k}, row["fail"], flush=True)
print("done")
