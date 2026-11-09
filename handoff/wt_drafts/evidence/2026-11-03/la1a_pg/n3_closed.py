# N3: PG-1 닫힌 식 측정. 미정 θ 전류가 든 기저 행을 세고(N), 행 순서 전파로 안 풀려 LP 가 필요한 행(n)을 잰다. 닫힌 식과 HiGHS LP 비교.
# 닫힌 식: (a) 입력 소자 gm 등식(행 값 = gm_b/g, 미지 하나)을 먼저 (b) 양의 미지 하나인 행: x ≥ (f − rest)/c 를 단조 반복 (c) 양의 미지 둘 이상이고 묶이는 행은 '필요 행'으로 센다.
# (c) 처리 대안: 같은 입력쌍(블록 입력 소자, 같은 kind·공통 source) 전류 등식으로 푼다.
# usage: n3_closed.py [circuit ...]  결과 = n3_closed.jsonl
from n0_common import *
import numpy as np
from scipy.optimize import linprog
OUT = HERE / "n3_closed.jsonl"
M1 = {}
for ln in open(HERE / "m1_current_facts_integ.jsonl", encoding="utf-8"):
    d = json.loads(ln); M1[d["circuit"]] = d
for CIR in (sys.argv[1:] or ALL):
    use_d1("d1")
    sctx = build_ctx(CIR, 40, 200.0)
    rung = sctx.rungs[0]
    given = {c for c, _v in rung.theta}
    variables = list(sctx.domain.variables)
    unknown = [v.component[1] for v in variables if v.component[0] == "current" and v.component not in given]
    schema = l0._schema(sctx)
    alias = l0._current_alias(sctx)
    th = dict(rung.theta)
    known = {c[1]: v for c, v in th.items() if c[0] == "current"}
    known.update({s: float(v) for s, v in schema.fixed})
    known.update({c[1]: 0.0 for c in sctx.domain.zeros if c[0] == "current"})
    rows_col = dict(sctx.dc.base.column("device", "start.row"))
    wmin = float(sctx.domain.w_min_m)
    floor = {m: wmin * math.exp(r.ln_idu) / r.l_chosen for m, r in rows_col.items() if r.ln_idu is not None}
    basis = next(v for _k, v in sctx.dc.base.column("graph", "dc_current_basis"))
    macro = sctx.dc.base.value("graph", "start", "macro")
    gm = dict((str(k), float(v)) for k, v in macro.gm) if macro is not None and macro.gm else {}
    eq = {}
    pins = dict(sctx.dc.base.column("device", "pins"))
    kinds = dict(sctx.dc.base.column("device", "kind"))
    pairs = []
    for bi in M1[CIR]["blocks"]:
        ins = bi["inputs"]
        for dev in ins:
            if bi["key"] in gm and dev in rows_col:
                eq[dev] = gm[bi["key"]] / rows_col[dev].gm_id_chosen
        for i in range(len(ins)):
            for j in range(i + 1, len(ins)):
                a_, b_ = ins[i], ins[j]
                if kinds.get(a_) == kinds.get(b_) and dict(pins[a_]).get("s") == dict(pins[b_]).get("s"):
                    pairs.append((a_, b_))
    # 행 정리
    rows = []
    for m, terms in basis.rows:
        if m not in floor and m not in eq:
            continue
        cf = {}; rest = 0.0
        for t in terms:
            s, sg = alias.get(t.source, (t.source, 1.0))
            w = float(t.num) / t.den * sg
            if s in unknown:
                cf[s] = cf.get(s, 0.0) + w
            else:
                rest += w * known.get(s, 0.0)
        cf = {k: v for k, v in cf.items() if v != 0.0}
        if not cf:
            continue
        if sum(cf.values()) < 0 and rest <= 0:
            cf = {k: -v for k, v in cf.items()}; rest = -rest
        rows.append((m, cf, rest))
    N = len(rows)
    pos1 = [r for r in rows if sum(1 for v in r[1].values() if v > 0) == 1]
    pos2 = [r for r in rows if sum(1 for v in r[1].values() if v > 0) >= 2]
    pos0 = [r for r in rows if sum(1 for v in r[1].values() if v > 0) == 0]
    lo = {v.component[1]: math.exp(v.lo) for v in variables if v.component[0] == "current" and v.component[1] in unknown}

    def closed(use_eq, use_pair):
        x = dict(lo)
        conflict = []
        pinned = {}
        # 쌍 등식: 두 입력 소자 행이 같다 -> 큰 쪽으로
        need = dict(floor)
        if use_eq:
            need.update(eq)
        if use_pair:
            tail_extra = {}
            for a_, b_ in pairs:
                v = max(need.get(a_, 0.0), need.get(b_, 0.0))
                need[a_] = need[b_] = v
        for _ in range(len(unknown) + len(rows) + 2):
            moved = False
            for m, cf, rest in rows:
                p = [k for k, v in cf.items() if v > 0]
                if len(p) != 1:
                    continue
                k = p[0]
                val = (need.get(m, 0.0) - rest - sum(v * x[s] for s, v in cf.items() if s != k)) / cf[k]
                if val > x[k] * (1 + 1e-12):
                    x[k] = val; moved = True
            if not moved:
                break
        bind = []
        for m, cf, rest in pos2:
            val = sum(v * x[s] for s, v in cf.items()) + rest
            if val < need.get(m, 0.0) * (1 - 1e-9):
                bind.append((m, val, need.get(m, 0.0)))
        # 묶이는 둘 양 계수 행: 쌍 등식이면 입력쌍 쪽 요구를 올려 다시 푼다(꼬리 = 쌍 합)
        return x, bind

    x0, bind0 = closed(False, False)
    x1, bind1 = closed(True, False)
    # 쌍 있는 회로: 꼬리 행 묶임을 쌍 전류 올림으로 해소
    x2, bind2 = closed(False, True)
    if bind2 and pairs:
        for a_, b_ in pairs:
            floor2 = max(v[2] for v in bind2) / 2
            floor[a_] = max(floor.get(a_, 0), floor2); floor[b_] = max(floor.get(b_, 0), floor2)
        x2, bind2 = closed(False, True)
    # LP 대조 (K 스케일)
    K = 1e12
    A = [[-cf.get(k, 0.0) for k in unknown] for m, cf, rest in rows if m in floor]
    B = [(rest - floor[m]) * K for m, cf, rest in rows if m in floor]
    r = linprog(np.ones(len(unknown)), A_ub=np.array(A) if A else None, b_ub=np.array(B) if B else None, bounds=[(lo[k] * K, None) for k in unknown], method="highs") if unknown else None
    lp = {k: float(v) / K for k, v in zip(unknown, r.x)} if r is not None and r.success else None
    diff = None if lp is None else max((abs(lp[k] - x0[k]) / max(lp[k], 1e-30) for k in unknown), default=0.0)
    row = {"circuit": CIR, "N_rows_with_unknown": N, "pos1": len(pos1), "pos2": [(m, cf) for m, cf, _r in pos2], "pos0": [m for m, _c, _r in pos0], "unknown": unknown,
           "binding_pos2_no_eq": bind0, "binding_pos2_with_pair": bind2, "closed_floor": x0, "closed_with_pair": x2, "closed_with_eq": x1, "lp_floor": lp, "max_rel_diff_lp_vs_closed": diff,
           "pairs": pairs, "eq": {k: v for k, v in eq.items()}, "input_rows": {a_: None for p in pairs for a_ in p}}
    for a_, b_ in pairs:
        for nm, xx in (("closed", x0), ("pair", x2), ("lp", lp or {})):
            row.setdefault("pair_I", {}).setdefault(nm, {})
            for dev in (a_, b_):
                tt = dict((t.source, float(t.num) / t.den) for mm, ts in basis.rows if mm == dev for t in ts)
                val = 0.0; okk = True
                for s, w in tt.items():
                    s2, sg = alias.get(s, (s, 1.0))
                    if s2 in xx:
                        val += w * sg * xx[s2]
                    elif s2 in known:
                        val += w * sg * known[s2]
                    else:
                        okk = False
                row["pair_I"][nm][dev] = val if okk else None
    app(OUT, row)
    print(CIR, "N", N, "pos1", len(pos1), "pos2", [m for m, _c, _r in pos2], "bind", [b[0] for b in bind0], "rel", diff, flush=True)
