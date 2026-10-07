"""층 0 최소형 시작점 -- θ 상자 중심에서 출발한 봉인 여유 최대-최소 점 (계획 DEC-71 최소형 = R D18·U-49·PUD DF-10,
오케스트레이터 결정 2026-10-08 'feasibility centering').

진입점: `layer0_start(sctx, origin=()) -> Layer0Result`(S0 당 1회, `find_front` 가 부른다 -- 결과 시작점은 `start_points` 의
첫 후보, 출처 "layer0").

최소형의 범위: DC 정합(봉인 통과) 시작점 하나. 블록 gain 예산(GB3 블록 분해·GB4 상한표)·LR5 knee·GB5 근사식·슬루 선언은
쓰지 않는다 -- 그것들은 최소형 밖의 정밀화다(U-49·D18). 입력은 선언·유도된 것만: θ 상자(`SearchDomain`), 봉인 항목 margin
(sizing 봉인 보고), 탐색 제약 행(W 하한·반전 하한·전류 원뿔).

1. **상자 중심**(자연 좌표): 변수마다 bounds 중점 -- ln 좌표 변수(전류·저항)는 ln 중점(= 기하 중심), `ln_idu` 는 그 좌표의
   중점, `y` 는 창 중앙. L 은 소자마다 L 칸(PDK bin 안 LUT 점 구간) 중 칸의 ln 중점이 전체 L 범위 [최소 칸 lo, 최대 칸 hi] 의
   ln 중점에 가장 가까운 칸(동률은 index 작은 쪽)을 고르고, 그 칸 안 L 은 칸 중점(bin 안 L 은 선형 보간 좌표라 선형 중점).
2. **전류 중심**(커널 0): MOS 전류는 θ 전류의 선형식(`schema.current_cone`)이라 상자 중심이 원뿔 밖일 수 있다(차 전류 행).
   그래서 θ 전류 변수만 움직여 'MOS 전류가 그 kind 전류 상자의 기하 중심에서 ln 거리로 가장 덜 벗어나는 점'(Chebyshev 중심)
   을 푼다: 최소화 u, 제약 I_m/I_c,m − e^(−u) ≥ 0, e^u − I_m/I_c,m ≥ 0(원뿔의 MOS 행 중 θ 전류를 하나라도 읽는 행 -- 값 선언
   이상원만 읽는 행은 움직일 수 없어 뺀다), I_c,m = 그 MOS kind 의
   `SearchDomain.current_box` 기하 중심. 기저 원소가 MOS 하나뿐인 행은 상자 중심에서 u = 0 이라 1 의 중심과 같다.
   수렴 판정은 scipy SLSQP 기본값(이 문제는 커널이 없어 판정 분해능 단위가 없다 -- 부동소수 수준).
3. **최대-최소**(커널): 시작점을 평가해 받아들일 상태(봉인 통과·봉인 7 대기)가 아니면(전류 중심이 원뿔 밖이어도) [S-4b,
   오케스트레이터 결정 2026-10-08] 같은 변수·같은 L 칸에서 Halton 열(스크램블 없음) 점을 순서대로 평가해 처음 받아들일 상태인
   점을 출발점으로 삼는다(`_halton_probe` -- 한도는 평가 예산 규칙). 그래도 없으면 끝(`start_<사유>+probe_<한도>`, 층 0 시작점
   없음). 받아들일 상태면 변수 x(정의역 연속 변수 + 칸이 구간인 L) 와 t 로
   최대화 t, 제약 s_i(x) − t ≥ 0(봉인 항목 i = 1..8 중 시작점 margin 이 유한한 항목, s_i = 1 − margin_i -- margin ≤ 1 이 pass
   이므로 s_i ≥ 0 ⇔ pass, 단위는 그 항목 허용오차), 그리고 경성 제약 c ≥ 0: W 하한(`w_min`)·반전 하한(`inversion_floor`)·
   전류 원뿔(`current_cone`) 행. 원뿔·W 하한 행은 판정 분해능 단위가 봉인 margin 과 달라(원뿔 c ≤ 1, W 는 제조 격자 칸)
   최소값 경쟁에 넣지 않는다 -- 넣으면 원뿔 c → 1(한 전류 → 꺼짐 전류)로 끌린다. 목적 −t 의 수렴 판정 = SLSQP ftol 1(t 의
   단위 = 허용오차 한 칸, `solve_eps` 와 같은 규칙).
   * fun·jac·constraints 는 같은 x 의 같은 평가(x float.hex 로 묶음 -- 커널 1회), jac 은 `fd_jacobian`(parent = 그 x 의 평가),
     x 평가의 parent = 직전 수락 반복. t 열은 해석적(−1/0).
   * 한도·실패 처리는 `solve_eps` 와 같다: maxiter = Σᵢ ⌈log2((hiᵢ − loᵢ)/hᵢ)⌉, 받아들일 상태가 아니거나 행 이름 집합이 바뀌면
     마지막 수락 반복 중심으로 상자 반경을 절반으로 재시작(상한 ⌈log2(최대 반경/최소 hᵢ)⌉), FD 열 양방향 실패는 그 변수 고정,
     평가 예산·벽시계 도달은 끝.
4. 결과 시작점 = 수락 반복 중 (경성 제약 모두 ≥ 0, min s_i 최대, seq 작은 쪽) 순으로 가장 좋은 점. 커널 결과는 평가 캐시에
   있어 `start_points` 의 재확인은 캐시 적중(커널 0)이다.
"""
import dataclasses
import math
import time

import numpy as np
from scipy.optimize import minimize as scipy_minimize

from gmid_engine.sizing import THETA_CURRENT, THETA_L

from .cone_rows import cone_rows
from .fd_jacobian import fd_jacobian
from .kernel import evaluate
from .search_values import (
    ACCEPTED_STATUSES,
    CON_INVERSION,
    CON_WMIN,
    STATUS_FAILED,
    StartPoint,
    Variable,
)

SOURCE_LAYER0 = "layer0"
STAGE_LAYER0 = "layer0"
ROW_SEAL_ITEM = "seal_item"
_HARD_PREFIXES = (CON_WMIN + ":", CON_INVERSION + ":")


@dataclasses.dataclass(frozen=True)
class Layer0Result:
    """층 0 결과. `start` = StartPoint(출처 "layer0") 또는 None, `t` = 그 점의 min s_i(봉인 여유, 허용오차 단위) 또는 None,
    `hard_ok` = 그 점의 경성 제약(W 하한·반전 하한·원뿔)이 모두 ≥ 0, `stop` = 종료 사유, `centre_u` = 전류 중심 문제의 해 u
    (MOS 전류의 상자 중심 대비 최대 ln 편차, θ 전류가 없으면 None), `start_status` = 출발점 평가 상태, `start_failure` = 그
    FailureRecord 또는 None, `iterations`·`restarts`·`aborts`·`frozen` = 최대-최소 풀이 기록, `kernel_calls` = 이 단계의 커널
    평가 수, `rows` = t 행 이름(봉인 항목) tuple, `probes` = S-4b Halton 시험 점 수(중심이 받아들여졌으면 0), `origin_point` =
    최대-최소 출발점 출처("centre" 또는 "halton:<k>", 시작점 없으면 None).

    **의미 한정**: 층 0 시작점은 DC 정합(봉인 통과) 가능성만 뜻한다 -- W·면적 상한 선언이 없어(S-3b) pA 전류·거대 W 점일 수
    있고, 탐색은 그 점을 출발 근거 이상으로 쓰지 않는다(front·보고 값이 아니다)."""

    start: object
    t: object
    hard_ok: bool
    stop: str
    centre_u: object
    start_status: str
    start_failure: object
    iterations: int
    restarts: int
    aborts: tuple
    frozen: tuple
    kernel_calls: int
    rows: tuple
    probes: int
    origin_point: object


class _Abort(Exception):
    """최대-최소 SLSQP 실행을 끊는 내부 신호. 이 파일 밖으로 나가지 않는다."""

    def __init__(self, reason, x=None, column=None):
        super().__init__(reason)
        self.reason = reason
        self.x = x
        self.column = column


def _box_centre(sctx):
    variables = list(sctx.domain.variables)
    theta = {v.component: (math.exp((v.lo + v.hi) / 2) if v.log else (v.lo + v.hi) / 2) for v in variables}
    cells = []
    for mos, table in sctx.domain.l_cells:
        mid = (math.log(min(c[0] for c in table)) + math.log(max(c[1] for c in table))) / 2
        j = min(range(len(table)), key=lambda i: (abs((math.log(table[i][0]) + math.log(table[i][1])) / 2 - mid), i))
        lo, hi = table[j]
        cells.append(j)
        theta[(THETA_L, mos)] = (lo + hi) / 2
        if lo < hi:
            variables.append(Variable((THETA_L, mos), False, lo, hi))
    return tuple(variables), theta, tuple(cells)


def _current_centre(sctx, variables, theta):
    schema = sctx.dc.schema
    index = [i for i, v in enumerate(variables) if v.component[0] == THETA_CURRENT]
    if not index or not schema.current_cone:
        return theta, None
    kinds = dict(sctx.dc.base.column("device", "kind"))
    box = dict(sctx.domain.current_box)
    ref = {m: math.sqrt(box[kinds[m]][0] * box[kinds[m]][1]) for m, _t in schema.current_cone}
    pos = {variables[i].component[1]: k for k, i in enumerate(index)}
    fixed = {name: float(v) for name, v in schema.fixed}
    # θ 전류를 하나도 읽지 않는 행(값 선언 이상원만으로 정해지는 MOS 전류)은 움직일 수 없으므로 편차 경쟁에서 뺀다 -- 넣으면
    # u 가 그 고정 편차로 정해져 나머지 행이 느슨해진다(원뿔 경계까지 허용).
    rows = tuple((m, tuple((float(t.num) / t.den, t.source) for t in terms)) for m, terms in schema.current_cone
                 if any(t.source in pos for t in terms))
    n = len(index)

    def currents(z):
        x = {name: math.exp(z[k]) for name, k in pos.items()}
        out = []
        for m, terms in rows:
            out.append(sum(w * (x[s] if s in x else fixed[s]) for w, s in terms) / ref[m])
        return np.asarray(out, dtype=float)

    def d_currents(z):
        out = np.zeros((len(rows), n))
        for r, (m, terms) in enumerate(rows):
            for w, s in terms:
                if s in pos:
                    out[r, pos[s]] += w * math.exp(z[pos[s]]) / ref[m]
        return out

    def cons(v):
        q = currents(v[:n])
        return np.concatenate([q - math.exp(-v[n]), math.exp(v[n]) - q])

    def cons_jac(v):
        dq = d_currents(v[:n])
        lower = np.hstack([dq, np.full((len(rows), 1), math.exp(-v[n]))])
        upper = np.hstack([-dq, np.full((len(rows), 1), math.exp(v[n]))])
        return np.vstack([lower, upper])

    z0 = [math.log(theta[variables[i].component]) for i in index]
    q0 = currents(z0)
    u0 = max((abs(math.log(q)) for q in q0 if q > 0), default=0.0)
    bounds = [(variables[i].lo, variables[i].hi) for i in index] + [(0.0, None)]
    grad = np.zeros(n + 1)
    grad[n] = 1.0
    out = scipy_minimize(lambda v: v[n], np.asarray(z0 + [u0], dtype=float), jac=lambda v: grad, method="SLSQP",
                         bounds=bounds, constraints=[{"type": "ineq", "fun": cons, "jac": cons_jac}])
    moved = dict(theta)
    for k, i in enumerate(index):
        moved[variables[i].component] = math.exp(min(max(float(out.x[k]), variables[i].lo), variables[i].hi))
    return moved, float(out.x[n])


def _item_slacks(res):
    report = res.evaluation.report
    return tuple((ROW_SEAL_ITEM + ":" + str(it.item), 1 - it.margin) for it in report.items
                 if it.margin is not None and math.isfinite(it.margin))


def _hard(res):
    rows = [(r.name, r.c) for r in res.constraints if r.name.startswith(_HARD_PREFIXES)]
    return tuple(rows) + tuple((r.name, r.c) for r in res.cone)


def _budget_stop(sctx):
    if sctx.eval_budget is not None and sctx.counters["kernel_calls"] >= sctx.eval_budget:
        return "eval_budget"
    if sctx.deadline is not None and time.perf_counter() > sctx.deadline:
        return "wall_budget"
    return None


def _maxmin(sctx, variables, theta0, cells, first, tag):
    lo = np.asarray([v.lo for v in variables], dtype=float)
    hi = np.asarray([v.hi for v in variables], dtype=float)
    fixed = {k: v for k, v in theta0.items() if k not in {v.component for v in variables}}
    t_names = tuple(name for name, _s in _item_slacks(first))
    h_names = tuple(name for name, _c in _hard(first))
    n = len(variables)
    state = {"parent": first, "points": {}, "accepted": [], "frozen": set()}

    def to_theta(x):
        out = dict(fixed)
        for v, value in zip(variables, x):
            value = min(max(float(value), v.lo), v.hi)
            out[v.component] = math.exp(value) if v.log else value
        return out

    def rows_of(res):
        if res.status not in ACCEPTED_STATUSES:
            return None
        ts, hs = _item_slacks(res), _hard(res)
        if tuple(a for a, _ in ts) != t_names or tuple(a for a, _ in hs) != h_names:
            return False
        return np.asarray([s for _a, s in ts], dtype=float), np.asarray([c for _a, c in hs], dtype=float)

    def point(x, res=None):
        x = np.array(x[:n], dtype=float)      # 복사 -- SLSQP 가 넘긴 배열을 제자리에서 바꿔도 저장한 x 가 키와 어긋나지 않게
        hx = tuple(float(v).hex() for v in x)
        hit = state["points"].get(hx)
        if hit is not None:
            return hit
        if res is None:
            stop = _budget_stop(sctx)
            if stop is not None:
                raise _Abort(stop, x)
            res = evaluate(sctx, to_theta(x), cells, parent=state["parent"], origin=tag)
        rows = rows_of(res)
        if rows is None:
            raise _Abort("candidate_failure", x)
        if rows is False:
            raise _Abort("constraint_set_changed", x)
        entry = {"x": x, "res": res, "s": rows[0], "c": rows[1], "jac": None}
        state["points"][hx] = entry
        return entry

    def jac_of(x):
        entry = point(x)
        skip = frozenset(state["frozen"])
        if entry["jac"] is None or entry["jac"][2] != skip:
            cols = fd_jacobian(sctx, variables, entry["x"], entry["res"], cells, to_theta, tag, skip)
            gs = np.zeros((len(t_names), n))
            gc = np.zeros((len(h_names), n))
            for i, (col, step) in enumerate(cols):
                if col is None:
                    raise _Abort("fd_column_failure", entry["x"], i)
                if step == 0:
                    continue
                rows = rows_of(col)
                if rows is None or rows is False:
                    raise _Abort("constraint_set_changed", entry["x"])
                gs[:, i] = (rows[0] - entry["s"]) / step
                gc[:, i] = (rows[1] - entry["c"]) / step
            entry["jac"] = (gs, gc, skip)
        return entry["jac"]

    def cons(v):
        e = point(v)
        return np.concatenate([e["s"] - v[n], e["c"]])

    def cons_jac(v):
        gs, gc, _skip = jac_of(v)
        top = np.hstack([gs, np.full((len(t_names), 1), -1.0)])
        bottom = np.hstack([gc, np.zeros((len(h_names), 1))])
        return np.vstack([top, bottom])

    def accept(v):
        entry = point(v)
        state["parent"] = entry["res"]
        state["accepted"].append(entry)

    start = point(np.asarray([_coord(v, theta0[v.component]) for v in variables], dtype=float), first)
    accept(start["x"])
    steps0 = fd_jacobian(sctx, variables, start["x"], first, cells, to_theta, tag, frozenset())
    h = np.asarray([abs(step) for _col, step in steps0], dtype=float)
    resolved = [int(math.ceil(math.log2((hi[i] - lo[i]) / h[i]))) for i in range(n) if h[i] > 0]
    maxiter = max(1, sum(max(r, 1) for r in resolved))
    radius = (hi - lo) / 2
    cap = max(1, int(math.ceil(math.log2(float(np.max(radius)) / float(np.min(h[h > 0])))))) if np.any(h > 0) else 1
    grad = np.zeros(n + 1)
    grad[n] = -1.0
    restarts, iterations, stop, aborts, frozen_log = 0, 0, "converged", [], []
    centre = start["x"]
    while True:
        shrink = 2 ** restarts
        box_lo = np.maximum(lo, centre - radius / shrink) if restarts else lo.copy()
        box_hi = np.minimum(hi, centre + radius / shrink) if restarts else hi.copy()
        for i in state["frozen"]:
            box_lo[i] = box_hi[i] = centre[i]
        here = point(centre)
        v0 = np.concatenate([centre, [float(np.min(here["s"]))]])
        try:
            out = scipy_minimize(lambda v: -v[n], v0, jac=lambda v: grad, method="SLSQP",
                                 bounds=list(zip(box_lo, box_hi)) + [(None, None)],
                                 constraints=[{"type": "ineq", "fun": cons, "jac": cons_jac}],
                                 callback=accept, options={"ftol": 1, "maxiter": maxiter})
            iterations += int(out.nit)
            accept(out.x)
            stop = "converged" if out.success else "slsqp_" + str(out.status)
            break
        except _Abort as exc:
            stop = exc.reason
            if exc.reason in ("eval_budget", "wall_budget"):
                aborts.append(exc.reason)
                break
            if exc.reason == "fd_column_failure":
                if not np.array_equal(exc.x, state["accepted"][-1]["x"]):
                    accept(exc.x)
                    state["frozen"].clear()
                state["frozen"].add(exc.column)
                frozen_log.append(variables[exc.column].component)
                aborts.append("frozen:" + ":".join(variables[exc.column].component))
                centre = state["accepted"][-1]["x"]
                if len(state["frozen"]) == n:
                    stop = "all_columns_frozen"
                    break
                continue
            aborts.append(exc.reason)
            restarts += 1
            if restarts > cap:
                stop = "restart_cap"
                break
            if not np.array_equal(centre, state["accepted"][-1]["x"]):
                state["frozen"].clear()
            centre = state["accepted"][-1]["x"]
    best = max(state["accepted"], key=lambda e: (bool(np.all(e["c"] >= 0)), float(np.min(e["s"])), -e["res"].seq))
    return best, stop, iterations, restarts, tuple(aborts), tuple(frozen_log), t_names


def _coord(var, value):
    return min(max(math.log(value) if var.log else value, var.lo), var.hi)


def _primes(count):
    out, k = [], 1
    while len(out) < count:
        k += 1
        if all(k % p for p in out):
            out.append(k)
    return out


def _radical_inverse(index, base):
    value, scale = 0.0, 1.0 / base
    while index:
        index, digit = divmod(index, base)
        value += digit * scale
        scale /= base
    return value


def _halton_probe(sctx, variables, theta0, cells, tag):
    """S-4b: 상자 중심이 받아들일 상태가 아니면 Halton 열(소수 기저, 스크램블 없음, index 1 부터)의 k 번째 점을 변수 자연 좌표
    (bounds 위 선형 = ln 변수는 ln 좌표)에 놓아 순서대로 평가하고, 처음 받아들일 상태인 점에서 멈춘다. 한도 = 평가 예산 규칙
    (`_budget_stop`: kernel_calls ≥ E_B 또는 벽시계). 벽시계(deadline)가 없을 때만 시험 점 수 ≤ E_B 를 더한다 -- 원뿔 밖 점은
    커널 0 이라 커널 수만으로는 끝나지 않는다. 둘 다 없으면 시험하지 않는다(`probe_budget_undeclared`)."""
    bases = _primes(len(variables))
    tried = 0
    while True:
        stop = _budget_stop(sctx)
        if stop is not None:
            return None, tried, "probe_" + stop
        if sctx.deadline is None:
            if sctx.eval_budget is None:
                return None, tried, "probe_budget_undeclared"
            if tried >= sctx.eval_budget:
                return None, tried, "probe_eval_budget"
        tried += 1
        theta = dict(theta0)
        for var, base in zip(variables, bases):
            value = var.lo + _radical_inverse(tried, base) * (var.hi - var.lo)
            theta[var.component] = math.exp(value) if var.log else value
        res = evaluate(sctx, theta, cells, origin=tag + (("probe", tried),))
        if res.status in ACCEPTED_STATUSES:
            return res, tried, None


def layer0_start(sctx, origin=()):
    calls0 = sctx.counters["kernel_calls"]
    tag = origin + (("stage", STAGE_LAYER0),)
    variables, theta, cells = _box_centre(sctx)
    theta, centre_u = _current_centre(sctx, variables, theta)
    failure, probes, source = None, 0, "centre"
    if any(r.c <= 0 for r in cone_rows(sctx.dc.schema, tuple(sorted(theta.items())))):
        start_status = "centre_outside_cone"
        first = None
    else:
        first = evaluate(sctx, theta, cells, origin=tag)
        start_status, failure = first.status, first.failure
        if first.status not in ACCEPTED_STATUSES:
            first = None
    if first is None:
        first, probes, why = _halton_probe(sctx, variables, theta, cells, tag)
        if first is None:
            reason = start_status
            if failure is not None:
                reason = dict(failure.detail).get("reason") or failure.failure_class
            return Layer0Result(None, None, False, "start_" + str(reason) + "+" + why, centre_u, start_status, failure,
                                0, 0, (), (), sctx.counters["kernel_calls"] - calls0, (), probes, None)
        source = "halton:" + str(probes)
        theta = dict(first.theta)
    best, stop, iterations, restarts, aborts, frozen, t_names = _maxmin(sctx, variables, theta, cells, first, tag)
    res = best["res"]
    start = StartPoint("layer0", res.theta, cells, SOURCE_LAYER0)
    return Layer0Result(start, float(np.min(best["s"])), bool(np.all(best["c"] >= 0)), stop, centre_u, start_status,
                        failure, iterations, restarts, aborts, frozen, sctx.counters["kernel_calls"] - calls0, t_names,
                        probes, source)
