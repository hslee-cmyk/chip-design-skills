# N4: B 밀도 방향(U-124)과 W_min 전류 하한의 값 출처.
# 시제품 받아들인 θ 에서 B 밀도 좌표를 차례로 '면적 최소 쪽(ln IDu 큰 쪽)'으로 옮긴다. 정합 판정 = 커널 봉인(J_point 대용), 가드 근사 = 그 점에서 통과하던 소신호 행(offset·noise)을 깨지 않음.
# 그다음 전류 하한 세 출처를 비교한다: F0 칸 값 밀도(자리값) / F1 최종 밀도(R6 뒤) / F2 S·F 행만(B 행 없음: B 만의 가지는 상자 하한 -- 값 없음을 보임).
# R 있는 가지는 V_R 유지(R ∝ 1/I). usage: n4_bdir.py <circuit> <run> 결과 = n4_bdir.jsonl
from n0_common import *
import numpy as np
CIR, RUN = sys.argv[1], sys.argv[2]
OUT = HERE / "n4_bdir.jsonl"
use_d1(RUN)
sctx = build_ctx(CIR, 40, 200.0)
tg = targets(sctx)
theta = load_theta(CIR, RUN)
_v, _t, cells = l0._box_centre(sctx, sctx.rungs[0])
roles = None
for ln in open(HERE / "m4_proto_r5r6v2.jsonl", encoding="utf-8"):
    d = json.loads(ln)
    if d.get("circuit") == CIR and d.get("stage") == "base" and d.get("roles"):
        roles = {k: v[0] for k, v in d["roles"].items()}
rows_col = dict(sctx.dc.base.column("device", "start.row"))
wmin = float(sctx.domain.w_min_m)
basis = next(v for _k, v in sctx.dc.base.column("graph", "dc_current_basis"))
schema = l0._schema(sctx)
alias = l0._current_alias(sctx)
given = {c for c, _v in sctx.rungs[0].theta}
unknown = [k for k in theta if k[0] == "current" and k not in given]
B_vars = sorted(k for k in theta if k[0] == "ln_idu" and roles.get(k[1]) == "B")
ORDER = os.environ.get("PG_ORDER", "name")
var = {v.component: v for v in sctx.domain.variables}


def summ(tag, th):
    r, raw = ev(sctx, th, cells)
    row = {"circuit": CIR, "run": RUN, "tag": tag, "status": r.status, "judge": judge(tg, raw), "P_mW": None if not r.objectives else r.objectives.power_w * 1e3,
           "area_um2": None if not r.objectives else r.objectives.area_m2 * 1e12, "fail": None if r.failure is None else str(dict(r.failure.detail))[:120]}
    return r, raw, row


def passing(raw):
    return {m for m, v in raw.items() if m in tg and v is not None and ((v >= tg[m][1]) if tg[m][0] == ">=" else (v <= tg[m][1]))}


r0, raw0, row0 = summ("start", theta)
app(OUT, row0)
if ORDER == "area":   # 면적 최소 목적: 게이트 면적 기여가 큰 묶음부터(같은 VGS 묶음 대표의 ln_idu 를 움직일 때 줄어드는 W·L 합 기준)
    ops0 = dict(r0.evaluation.snapshot.column("device", "dc_op"))
    def area_gain(k):
        t = dict(theta); t[k] = theta[k] + 1.0
        r_, _ = ev(sctx, t, cells)
        return r_.objectives.area_m2 if r_.objectives else 1e9
    B_vars = sorted(B_vars, key=area_gain)
keep = passing(raw0) & {"offset_excess", "noise_excess_th"}
out = {}
for guard in (False, True):
    th = dict(theta)
    moved = {}
    for k in B_vars:
        v = var[k]
        cur = th[k]
        lo, hi = cur, min(v.hi, cur + 12.0)
        best = cur
        step = 1.0
        x = cur
        while x + step <= hi:
            t = dict(th); t[k] = x + step
            r, raw = ev(sctx, t, cells)
            if r.status != "sealed" or (guard and not keep <= passing(raw)):
                break
            x += step; best = x
        # 한 칸 분해능 다듬기
        a, b = best, min(best + step, hi)
        for _ in range(3):
            m = (a + b) / 2
            t = dict(th); t[k] = m
            r, raw = ev(sctx, t, cells)
            if r.status == "sealed" and (not guard or keep <= passing(raw)):
                a = m
            else:
                b = m
        th[k] = a
        if a != cur:
            moved[k[1]] = [round(cur, 2), round(a, 2)]
    tag = ("area_dir_guard" if guard else "area_dir") + ("@" + ORDER if ORDER != "name" else "")
    r, raw, row = summ(tag, th)
    row["moved"] = moved; row["keep"] = sorted(keep); row["guard_is"] = "keep rows that passed at start (approximation of R7)" if guard else None
    app(OUT, row)
    out[tag] = dict(th); out[("area_dir_guard" if guard else "area_dir")] = dict(th)
    print(CIR, tag, row["status"], {k: v[0] for k, v in row["judge"].items()}, row["P_mW"], moved, flush=True)


# 전류 하한 값 출처 비교
def floors(th, mode):
    out_ = {}
    for m, r in rows_col.items():
        if r.ln_idu is None:
            continue
        role = roles.get(m)
        ln = th.get(("ln_idu", m), r.ln_idu)
        if mode == "F0":
            ln = r.ln_idu
        elif mode == "F2" and role == "B":
            continue
        out_[m] = wmin * math.exp(ln) / r.l_chosen
    return out_


def prop(th, mode):
    f = floors(th, mode)
    x = {k[1]: math.exp(var[k].lo) for k in unknown}
    known = {c[1]: v for c, v in th.items() if c[0] == "current" and c not in unknown}
    known.update({s: float(v) for s, v in schema.fixed})
    rows = []
    for m, terms in basis.rows:
        if m not in f:
            continue
        cf = {}; rest = 0.0
        for t in terms:
            s, sg = alias.get(t.source, (t.source, 1.0))
            w = float(t.num) / t.den * sg
            if s in x:
                cf[s] = cf.get(s, 0.0) + w
            else:
                rest += w * known.get(s, 0.0)
        if cf and any(v != 0 for v in cf.values()):
            if sum(cf.values()) < 0 and rest <= 0:
                cf = {k_: -v for k_, v in cf.items()}; rest = -rest
            rows.append((m, cf, rest))
    for _ in range(len(rows) + 3):
        mv = False
        for m, cf, rest in rows:
            p = [k_ for k_, v in cf.items() if v > 0]
            if len(p) != 1:
                continue
            val = (f[m] - rest - sum(v * x[s] for s, v in cf.items() if s != p[0])) / cf[p[0]]
            if val > x[p[0]] * (1 + 1e-12):
                x[p[0]] = val; mv = True
        if not mv:
            break
    t = dict(th)
    for k in unknown:
        r_k = ("resistance", k[1])
        if r_k in t and k in th and th[k] > 0:
            t[r_k] = th[r_k] * th[k] / x[k[1]]
        t[k] = x[k[1]]
    return t, x


for base_tag, th in (("start", theta), ("area_dir_guard", out["area_dir_guard"]), ("area_dir", out["area_dir"])):
    for mode in ("F0", "F1", "F2"):
        t, x = prop(th, mode)
        r, raw, row = summ(base_tag + "+" + mode, t)
        row["x"] = {k: float("%.3g" % v) for k, v in x.items()}
        row["R"] = {k[1]: float("%.4g" % v) for k, v in t.items() if k[0] == "resistance"}
        app(OUT, row)
        print(CIR, base_tag, mode, row["status"], row["x"], {k: v[0] for k, v in row["judge"].items() if k in ("gbw_ss_hz", "pm_ss_deg")}, row["P_mW"], row["fail"], flush=True)
print("done")
