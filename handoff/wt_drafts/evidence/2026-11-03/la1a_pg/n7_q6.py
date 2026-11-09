# N7: Q6 재현 가능한 정의의 측정 -- 'K-1 (ii) = 행·가드 안 Σ면적 최소 공동 선택, 순서 규칙 없음'.
# 측정 풀이 = 한계 비 강하(결정적): 매 걸음 모든 B 좌표의 +δ 후보를 전부 평가하고 Δ면적/Δ가드가 가장 좋은 것 하나를 옮긴다. 동률 = 정렬 키. 변수 나열 순서를 뒤집어 같은 결과인지 확인한다.
# 면적 항: 매 후보에서 전류를 같은 순수 함수로 재전파((1) 전류 고정, (3) 가지 = W_min·IDu(현재 밀도)/L 전파, 값 미선언 R 은 V_R 유지). 진짜 R6·R7 아님, 정합 판정 = 커널 봉인.
# 변형: guard(통과하던 offset·noise 유지), guard+gain(전회로 gain ≥ 시작값), none. 표에 J_point 최소 여유(봉인 7 slack)와 스윙·ICMR 을 넣는다.
# usage: n7_q6.py <circuit> <run> [delta]  결과 = n7_q6.jsonl 케이스마다 append
from n0_common import *
CIR, RUN = sys.argv[1], sys.argv[2]
DELTA = float(sys.argv[3]) if len(sys.argv) > 3 else 0.25
OUT = HERE / "n7_q6.jsonl"
FROZEN = os.environ.get("PG_FROZEN") == "1"   # 면적 항 전류 고정: (3) 전류를 K-1 (i) 해 밀도에서 한 번 내고 고정, W ≥ W_min 행을 밀도 상한으로
use_d1(RUN)
sctx = build_ctx(CIR, 40, 200.0)
tg = targets(sctx)
theta0 = load_theta(CIR, RUN)
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
unknown = [k for k in theta0 if k[0] == "current" and k not in given and k[1] != "RL"]
var = {v.component: v for v in sctx.domain.variables}
B_vars = sorted(k for k in theta0 if k[0] == "ln_idu" and roles.get(k[1]) == "B")
macro = sctx.dc.base.value("graph", "start", "macro")
gm = dict((str(k), float(v)) for k, v in macro.gm) if macro is not None and macro.gm else {}
eq = {}
if RUN.startswith("RC"):
    for ln in open(HERE / "m1_current_facts_integ.jsonl", encoding="utf-8"):
        d = json.loads(ln)
        if d["circuit"] == CIR:
            for bi in d["blocks"]:
                for dev in bi["inputs"]:
                    if bi["key"] in gm and dev in rows_col:
                        eq[dev] = gm[bi["key"]] / rows_col[dev].gm_id_chosen


def repropagate(th):
    """(3): 밀도가 바뀌면 W_min 하한 전류와 그 KCL 전파를 다시 낸다. 값 미선언 R 은 V_R 유지."""
    f = {}
    for m, r in rows_col.items():
        if r.ln_idu is None:
            continue
        ln = th.get(("ln_idu", m), r.ln_idu)
        f[m] = wmin * math.exp(ln) / r.l_chosen
    f.update({m: max(v, f.get(m, 0.0)) for m, v in eq.items()})
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
        if r_k in t and theta0[k] > 0:
            t[r_k] = theta0[r_k] * theta0[k] / x[k[1]]
        t[k] = x[k[1]]
    return t


def passing(raw):
    return {m for m, v in raw.items() if m in tg and v is not None and ((v >= tg[m][1]) if tg[m][0] == ">=" else (v <= tg[m][1]))}


def slack(r):
    """봉인 7(포화) 최소 여유 V -- 보고 항목에서."""
    if r.evaluation is None:
        return None
    for it in r.evaluation.report.items:
        if getattr(it, "item", None) == 7:
            d = dict(getattr(it, "detail", ()) or ())
            return d.get("slack_v", getattr(it, "margin", None))
    return None


def report(tag, th, extra=None):
    r, raw = ev(sctx, th, cells)
    row = {"circuit": CIR, "run": RUN, "delta": DELTA, "tag": tag, "status": r.status, "judge": judge(tg, raw), "area_um2": None if not r.objectives else r.objectives.area_m2 * 1e12,
           "P_mW": None if not r.objectives else r.objectives.power_w * 1e3, "slack_v": slack(r),
           "moved": {k[1]: round(th[k] - theta0[k], 2) for k in B_vars if abs(th[k] - theta0[k]) > 1e-9}, "x": {k[1]: float("%.4g" % th[k]) for k in unknown}, "fail": None if r.failure is None else str(dict(r.failure.detail))[:120]}
    row.update(extra or {})
    app(OUT, row)
    j = row["judge"]
    print(tag, r.status, "GBW", j.get("gbw_ss_hz", [None])[0], "PM", j.get("pm_ss_deg", [None])[0], "gain", j.get("gain_ss_db", [None])[0], "off", j.get("offset_excess", [None])[0], "noise", j.get("noise_excess_th", [None])[0], "A", row["area_um2"], "P", row["P_mW"], "slack", row["slack_v"], row["moved"], flush=True)
    return r, raw


start = repropagate(theta0)
r0, raw0 = report("start", start)
keep = passing(raw0) & {"offset_excess", "noise_excess_th"}
gain0 = raw0.get("gain_ss_db")
WMIN0 = {c.name: float(c.c) for c in (r0.constraints or ()) if c.name.startswith("w_min") and c.c is not None}   # 시작점에 이미 있는 위반은 더 나빠지지만 않게(θ 밖 소자가 칸 값을 읽는 도구 한계)
app(OUT, {"circuit": CIR, "run": RUN, "tag": "order_independence", "frozen": False, "same_under_reversed_list": None, "note_wmin_start_neg": {k: round(v, 3) for k, v in WMIN0.items() if v < 0}})


def ratio(mode, names):
    th = dict(start)
    r_, raw_ = ev(sctx, th, cells)
    A = r_.objectives.area_m2
    steps = 0
    for _ in range(600):
        best = None
        g0 = sum(raw_.get(m, 0.0) for m in keep)
        for k in names:
            if th[k] + DELTA > var[k].hi:
                continue
            t = dict(th); t[k] = th[k] + DELTA
            if not FROZEN:
                t = repropagate(t)
            r, raw = ev(sctx, t, cells)
            if r.status != "sealed":
                continue
            if FROZEN and any(c.name.startswith("w_min") and c.c is not None and c.c < min(-1e-9, WMIN0.get(c.name, 0.0)) for c in (r.constraints or ())):
                continue
            if mode != "none" and not keep <= passing(raw):
                continue
            if mode == "guard+gain" and gain0 is not None and raw.get("gain_ss_db", -1e9) < gain0:
                continue
            a = r.objectives.area_m2
            dA = A - a
            if dA <= 0:
                continue
            dg = max(sum(raw.get(m, 0.0) for m in keep) - g0, 0.0) if (keep and mode != "none") else 0.0
            score = dA / (dg + 1e-6) if (keep and mode != "none") else dA
            key = (score, k[1])
            if best is None or key > best[0]:
                best = (key, k, t, a, raw)
        if best is None:
            break
        th = best[2]; A = best[3]; raw_ = best[4]; steps += 1
    return th, steps


if os.environ.get("PG_CHECK3") == "1":   # 최종 밀도로 (3) 을 다시 내면 고정 전류와 같은가, 다르면 그 점의 값
    th, n = ratio("guard", B_vars)
    t3 = repropagate(th)
    report("recheck3", t3, {"frozen_x": {k[1]: float("%.4g" % th[k]) for k in unknown}})
    print("done"); raise SystemExit
for mode in ("guard", "guard+gain", "none"):
    th, n = ratio(mode, B_vars)
    report(("frozen:" if FROZEN else "ratio:") + mode, th, {"steps": n, "keep": sorted(keep)})
th2, _n2 = ratio("guard", list(reversed(B_vars)))
same = all(abs(th2[k] - ratio("guard", B_vars)[0][k]) < 1e-12 for k in B_vars)
app(OUT, {"circuit": CIR, "run": RUN, "frozen": FROZEN, "tag": "order_independence", "same_under_reversed_list": same})
print("order independent", same)
print("done")
