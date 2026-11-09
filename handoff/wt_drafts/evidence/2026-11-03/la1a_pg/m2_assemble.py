# M2: PG-1 대안별 출발점 조립 -- 칸 0 독립 성분 + 미정 θ 전류(대안) 로 커널 평가, 종속 성분(B ln IDu·y·R)은 R6 대용 탐색.
# R6 대용 = 독립 성분 고정, 종속 좌표만 Halton 표본(HC-1·TB-1 미병합이라 R6 자체를 못 부름 -- 측정 도구, 규칙 후보 아님).
# 표본에서 봉인이 나오면 '그 독립 성분에 KVL 정합 종속 값이 존재한다'는 양성 증거, 안 나오면 '표본 N 안에 없음'(음성 증명 아님).
# usage: m2_assemble.py <circuit> [alt ...] [--n N] [--front]   결과 = m2_assemble.jsonl, 케이스마다 append. 엔진 파일 무변경.
import sys, dataclasses
import numpy as np
from scipy.optimize import linprog
from pg_common import *

ivc = sys.modules["gmid_engine.search.iv_context"]
ff = sys.modules["gmid_engine.search.find_front"]
from gmid_engine.metrics import ACH_KEY, ParamTables, block_spec
from gmid_engine.search.start_values import GainInputs
from gmid_engine.search import find_front
from gmid_engine.search.kernel import evaluate

OUT = HERE / "m2_assemble.jsonl"
args = sys.argv[1:]
N = 200
if "--n" in args:
    i = args.index("--n"); N = int(args[i + 1]); del args[i:i + 2]
FRONT = "--front" in args
if FRONT:
    args.remove("--front")
CIR = args[0]
ALTS = args[1:] or ["A0", "NA", "RA"]


def gain_inputs_d1(p, views, lut, constraints):
    """DEC-105 (1) + design D1: 버퍼 블록 목표 없음, Σ_j 전부. found_db 없으면 뷰 정의 불능(as-built 경로 대신 사유)."""
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


ivc._gain_inputs = gain_inputs_d1


def halton(i, primes):
    out = []
    for b in primes:
        f, r, k = 1.0, 0.0, i
        while k > 0:
            f /= b; r += f * (k % b); k //= b
        out.append(r)
    return out


PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113, 127, 131, 137, 139, 149, 151, 157, 163]
lut, pdk, rule = load_env()
t0 = time.time()
a, b, sctx = build(CIR, lut, pdk, rule, budget_s=150.0)
base_row = {"circuit": CIR, "case": "ctx", "stage_a": a.status}
if sctx is None:
    app(OUT, base_row); raise SystemExit
rungs = sctx.rungs
rung = rungs[0]
variables, theta0, cells = l0._box_centre(sctx, rung)
schema = l0._schema(sctx)
given = {c for c, _v in rung.theta}
rows_col = dict(sctx.dc.base.column("device", "start.row"))
macro = sctx.dc.base.value("graph", "start", "macro")
gm_blocks = dict((str(k), float(v)) for k, v in macro.gm) if macro is not None and macro.gm else {}
w_min = float(sctx.domain.w_min_m)
fixed = {s: float(v) for s, v in schema.fixed}
fixed.update({c[1]: 0.0 for c in sctx.domain.zeros if c[0] == "current"})
alias = l0._current_alias(sctx)
cone = [(m, [(float(t.num) / t.den * alias.get(t.source, (t.source, 1.0))[1], alias.get(t.source, (t.source, 1.0))[0]) for t in terms]) for m, terms in schema.current_cone]
var_cur = [v for v in variables if v.component[0] == "current"]
known = {v.component[1]: theta0[v.component] for v in var_cur if v.component in given}
known.update(fixed)
unknown = [v for v in var_cur if v.component not in given]
ukeys = [v.component[1] for v in unknown]
uindex = {k: i for i, k in enumerate(ukeys)}
floor = {m: w_min * math.exp(r.ln_idu) / r.l_chosen for m, r in rows_col.items() if r.ln_idu is not None}
roles = dict(sctx.dc.base.column("device", "dc_role"))
kinds = dict(sctx.dc.base.column("device", "kind"))
# 블록 입력 소자 gm 방정식 -- start 필드의 현재 칸 0 선택 gm/ID 로
from gmid_engine.search.iv_currents import _blocks as _iv_blocks
input_of = {}
capt_view = next((v for v in sctx.dc.base.value("graph", "kernel", "views")) if False else (), None) if False else None
base_row.update({"n_theta": len(variables), "unknown": ukeys, "known": known, "floors": floor, "gm_blocks": gm_blocks, "macro_records": [str(r)[:160] for r in (macro.records if macro else ())],
                 "L_nm": {str(c[1]): round(v * 1e9) for c, v in rung.theta if c[0] == "L"}, "dc_role": {k: str(v) for k, v in roles.items()},
                 "box_cur": [[v.component[1], math.exp(v.lo), math.exp(v.hi)] for v in unknown], "t_s": round(time.time() - t0, 1)})
app(OUT, base_row)


def lp_floor(eq=()):
    """min Σ x s.t. 행 ≥ W_min 전류(모든 MOS 행), x 상자 안. eq = ((행 MOS, 값 A), ...) -- 그 행 = 값(gm 방정식)."""
    n = len(ukeys)
    if n == 0:
        return {}, "no_unknown"
    A, B_, Aeq, Beq = [], [], [], []
    eqd = dict(eq)
    for m, terms in cone:
        coef = np.zeros(n); rest = 0.0; hit = False
        for w, s in terms:
            if s in uindex:
                coef[uindex[s]] += w; hit = True
            else:
                rest += w * known.get(s, 0.0)
        if not hit:
            continue
        if m in eqd:
            Aeq.append(coef); Beq.append(eqd[m] - rest)
        elif m in floor:
            A.append(-coef); B_.append(rest - floor[m])
    bounds = [(math.exp(v.lo), math.exp(v.hi)) for v in unknown]
    r = linprog(np.ones(n), A_ub=np.array(A) if A else None, b_ub=np.array(B_) if B_ else None, A_eq=np.array(Aeq) if Aeq else None, b_eq=np.array(Beq) if Beq else None, bounds=bounds, method="highs")
    if not r.success:
        return None, str(r.message)[:120]
    return {k: float(x) for k, x in zip(ukeys, r.x)}, "ok"


def rows_summary(res):
    out = {}
    for c in res.constraints or ():
        if c.name.startswith(("ss:", "spec:")):
            out[c.name.split(":")[-1]] = round(float(c.c), 3) if c.c is not None else None
    return out


def dep_vars():
    out = []
    for v in variables:
        k, name = v.component
        if k in ("y", "resistance"):
            out.append(v)
        elif k == "ln_idu" and str(roles.get(name, "")).lower().find("bias") >= 0:
            out.append(v)
    return out


def assemble(alt):
    th = dict(theta0)
    if alt == "A0":
        _v, th2, _c, _u = l0.centre_start(sctx, rung)
        return dict(th2), "as_built_centre"
    eq = ()
    if alt == "RA":            # W_min + 매크로 gm 방정식(미지 있는 입력 소자 행)
        eq = tuple(EQ.items())
    x, why = lp_floor(eq)
    if x is None:
        return None, why
    for v in unknown:
        th[v.component] = min(max(x[v.component[1]], math.exp(v.lo)), math.exp(v.hi))
    return th, why


# gm 방정식: 입력 소자 전류 = gm_b / (gm/ID)
EQ = {}
capt = {}
_orig = si._state
if gm_blocks:
    # 블록 입력 소자 = transfer 뷰 블록의 roles input/follower (m1 사실과 같음)
    m1 = None
    for ln in open(HERE / "m1_current_facts.jsonl", encoding="utf-8"):
        d = json.loads(ln)
        if d["circuit"] == CIR:
            m1 = d
    if m1:
        for bi in m1["blocks"]:
            gm = gm_blocks.get(bi["key"])
            for dev in bi["inputs"]:
                terms = dict((s, c) for c, s in next((t for m, t in cone if m == dev), []))
                if any(s in uindex for s in terms) and gm is not None:
                    EQ[dev] = gm / rows_col[dev].gm_id_chosen
app(OUT, {"circuit": CIR, "case": "eq", "EQ": EQ})

for alt in ALTS:
    t1 = time.time()
    th, why = assemble(alt)
    row = {"circuit": CIR, "case": "alt", "alt": alt, "why": why}
    if th is None:
        app(OUT, row); continue
    row["x"] = {k: th[("current", k)] for k in ukeys if ("current", k) in th}
    res0 = evaluate(sctx, th, cells, origin=(("stage", "pg"),))
    row["first_status"] = res0.status
    if res0.failure is not None:
        row["first_fail"] = {"class": res0.failure.failure_class, "devices": list(res0.failure.devices), "reason": dict(res0.failure.detail).get("reason"), "item": dict(res0.failure.detail).get("item"), "margin": res0.failure.margin, "detail": str(dict(res0.failure.detail))[:500]}
    row["first_rows"] = rows_summary(res0)
    dv = dep_vars()
    row["n_dep"] = len(dv)
    row["dep"] = [list(map(str, v.component)) for v in dv]
    hist, sealed, best = {}, 0, None
    first_sealed = res0 if res0.status in l0.ACCEPTED_STATUSES else None
    sealed_rows = []
    if first_sealed is not None:
        sealed += 1
        sealed_rows.append(rows_summary(first_sealed))
    for i in range(1, N + 1):
        if time.time() - t1 > 170:
            row["sample_cut"] = i
            break
        u = halton(i + 20, PRIMES[:max(1, len(dv))])
        t = dict(th)
        for ui, v in zip(u, dv):
            lo, hi = v.lo, v.hi
            if v.component[0] == "ln_idu":      # 측정 창: 칸 0 값 주변(LUT 정의역 밖 표본 낭비 방지, 측정 도구 -- 규칙 아님)
                c0 = theta0[v.component]
                lo, hi = max(lo, c0 - 4.0), min(hi, c0 + 4.0)
            val = lo + ui * (hi - lo)
            t[v.component] = math.exp(val) if v.log else val
        r = evaluate(sctx, t, cells, origin=(("stage", "pg"),))
        if r.status in l0.ACCEPTED_STATUSES:
            sealed += 1
            first_sealed = first_sealed or r
            sealed_rows.append(rows_summary(r))
        else:
            key = (dict(r.failure.detail).get("item") or dict(r.failure.detail).get("reason") or r.failure.failure_class) if r.failure is not None else r.status
            hist[str(key)] = hist.get(str(key), 0) + 1
    row["n_sampled"] = i if dv else 0
    row["sealed"] = sealed
    row["fail_hist"] = dict(sorted(hist.items(), key=lambda kv: -kv[1])[:6])
    if sealed_rows:
        keys = sorted({k for s in sealed_rows for k in s})
        row["sealed_rows_best"] = {k: max((s[k] for s in sealed_rows if s.get(k) is not None), default=None) for k in keys}
    if first_sealed is not None:
        row["sealed_rows_first"] = rows_summary(first_sealed)
        row["power_w"] = first_sealed.objectives.power_w if first_sealed.objectives else None
        row["area_m2"] = first_sealed.objectives.area_m2 if first_sealed.objectives else None
        if FRONT:
            start = l0.StartPoint("layer0", first_sealed.theta, cells, l0.SOURCE_LAYER0)
            lr = l0.Layer0Result(start, 0.0, True, "pg_forced", None, first_sealed.status, None, 0, 0, (), (), 0, 0, (), 0, alt)
            ff.layer0_start = lambda s, origin=(): lr
            n0 = len(sctx.cache)
            try:
                sctx.deadline = None
                fr = find_front(sctx, [])
                allr = [r for r in sctx.cache.values() if r.status == "sealed"]
                agg = {}
                for r in allr:
                    for k, v in rows_summary(r).items():
                        if v is None:
                            continue
                        z = agg.setdefault(k, [0, -1e99]); z[0] += int(v >= 0); z[1] = max(z[1], v)
                row["front"] = {"n_front": len(getattr(fr, "front", ()) or ()), "n_sealed_total": len(allr), "rows": agg}
            except Exception:
                row["front_error"] = traceback.format_exc()[-800:]
    row["t_s"] = round(time.time() - t1, 1)
    app(OUT, row)
    print(CIR, alt, row.get("first_status"), "sealed", sealed, "of", row.get("n_sampled"), flush=True)
print("done")
