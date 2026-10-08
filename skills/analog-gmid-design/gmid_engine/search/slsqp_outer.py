"""외층 ε-제약 SLSQP 한 번 (설계 design_mod6_search_front 6.2, DEC-54·77, LR10).

진입점: `solve_eps(sctx, start, minimize, eps, origin) -> SolveResult`.

* 변수: `SearchDomain.variables`(ln_idu·y·ln current·ln R) + 칸이 구간인(lo < hi) MOS 의 L(칸 bounds). L 칸 index 벡터는
  시작점 것을 그대로 쓴다(L-a) -- 칸이 한 점인 L 은 고정값이다. 결정변수 밖 값은 바꾸지 않는다. [r8, S-4f] 1변수 노드 writer 의
  ln_idu 하한은 시작 칸의 칸 정점 하한(`cell_floor.ln_idu_floors(one_var_only=True, start=시작 θ)`).
* 목적 = `minimize` 축 값 / 그 축 분해능, ε = (축, 상한) 이면 제약 (ε − 값)/분해능 ≥ 0(설계 5절). 분해능: 면적 = b_A(정의역),
  전력 = 시작점의 b_P(`Objectives.power_resolution_w` -- 풀이 하나 동안 고정해 목적 함수가 θ 마다 축척을 바꾸지 않게).
  다른 제약 = 커널 결과의 정규화 행 + θ 전류 원뿔 행. 가중합 없음(DEC-77).
* `fun`·`jac`·`constraints` 는 모두 같은 x 의 같은 평가를 읽는다(x 의 float.hex 로 묶음 -- 커널 1회). jac 은 `fd_jacobian`
  (parent = 그 x 의 평가). x 평가의 parent = 직전 수락 반복(callback).
* **한도는 평가 수로 센다(결정론)**: SLSQP 반복 상한 = Σᵢ ⌈log2((hiᵢ − loᵢ)/hᵢ)⌉(좌표마다 bounds 폭을 FD 스텝 hᵢ 까지 반으로
  가르는 수의 합 -- K_max 와 같은 bisection 논리, hᵢ = 시작점 FD 스텝). 평가 예산: `sctx.counters["kernel_calls"] ≥
  sctx.eval_budget` 이면 끝(`eval_budget`). 벽시계 `sctx.deadline` 은 바깥 정지(`wall_budget`, 기록 -- 이것으로 끝난 실행만
  결정론 밖).
* 실패 처리(설계 6.2): x 가 받아들일 상태가 아니거나 제약 행 이름 집합이 시작점과 달라지면 마지막 수락 반복을 중심으로 상자 반경을
  절반으로 줄여 다시 시작한다(반경 = 정의역 bounds 반폭 -- 설계 '격자 반경 × 2^m' 의 m 은 U-47 보류, S-7). 재시작 상한 =
  max_i ⌈log2(반경ᵢ/hᵢ)⌉. 상수 페널티 없음. 실패 점의 부분 목적값은 없어(size_and_seal 실패 = 예외) 봉인 6·7 실패도 재시작이다(S-10).
* **FD 열 고정**(오케스트레이터 결정 S-16): 수락된 x 에서 FD 열이 양방향 모두 받아들일 상태가 아니면 그 변수를 지금 값으로 고정하고
  (bounds lo = hi = x) 같은 중심에서 SLSQP 를 다시 돈다(재시작 수에 넣지 않음, `frozen` 에 기록). 중심이 바뀌면(새 수락 반복에서
  재시작) 고정을 푼다. 모든 변수가 고정되면 끝(`all_columns_frozen`). 0 도함수를 지어내지 않는다.
* `best` = 수락 반복 중 모든 제약 c ≥ 0 인 점에서 목적 최소(동률은 seq 작은 쪽). 없으면 None.
"""
import math
import time

import numpy as np
from scipy.optimize import minimize as scipy_minimize

from gmid_engine.sizing import THETA_L

from .cell_floor import ln_idu_floors
from .fd_jacobian import fd_jacobian
from .kernel import evaluate
from .search_values import ACCEPTED_STATUSES, AXIS_AREA, AXIS_POWER, CON_EPS, STAGE_SLSQP, SolveResult, Variable


class _Abort(Exception):
    """SLSQP 실행을 끊는 내부 신호(재시작·열 고정·예산 끝). 이 파일 밖으로 나가지 않는다."""

    def __init__(self, reason, x=None, column=None):
        super().__init__(reason)
        self.reason = reason
        self.x = x
        self.column = column


def _layout(sctx, start):
    variables = list(sctx.domain.variables)
    fixed = {}
    theta = dict(start.theta)
    for (mos, cells), j in zip(sctx.domain.l_cells, start.cells):
        lo, hi = cells[j]
        if lo < hi:
            variables.append(Variable((THETA_L, mos), False, lo, hi))
        else:
            fixed[(THETA_L, mos)] = lo
    # [r8, S-4f] 1변수 노드 writer(diode·소스 추종)의 ln_idu 상자 하한 = 시작 칸의 칸 정점 하한(시작 좌표는 넘지 않음) -- 칸이 고정된
    # 이 풀이 안에서 상수. 정점 아래 좌표에서 그 노드 근이 늘 없어 SLSQP 가 실패 재시작만 하는 영역을 상자에서 뺀다.
    for i, floor in ln_idu_floors(sctx, variables, start.cells, one_var_only=True, start=theta).items():
        variables[i] = Variable(variables[i].component, variables[i].log, floor, variables[i].hi)
    names = {v.component for v in variables} | set(fixed)
    for comp in theta:
        if comp not in names:
            fixed[comp] = theta[comp]
    x0, exact = [], []
    for v in variables:
        raw = theta[v.component]
        coord = math.log(raw) if v.log else raw
        x0.append(min(max(coord, v.lo), v.hi))
        exact.append(raw if x0[-1] == coord else None)    # bounds 로 잘리지 않았으면 시작 θ 원값
    return tuple(variables), fixed, x0, tuple(exact)


def _axis_value(result, axis):
    return result.objectives.power_w if axis == AXIS_POWER else result.objectives.area_m2


def _rows(result, eps, scales):
    rows = list(result.constraints) + list(result.cone)
    names = tuple(r.name for r in rows)
    values = [r.c for r in rows]
    if eps is not None:
        axis, bound = eps
        values.append((bound - _axis_value(result, axis)) / scales[axis])
        names += (CON_EPS + ":" + axis,)
    return names, np.asarray(values, dtype=float)


def _budget_stop(sctx):
    if sctx.eval_budget is not None and sctx.counters["kernel_calls"] >= sctx.eval_budget:
        return "eval_budget"
    if sctx.deadline is not None and time.perf_counter() > sctx.deadline:
        return "wall_budget"
    return None


def solve_eps(sctx, start, minimize, eps, origin):
    variables, fixed, x0, exact = _layout(sctx, start)
    lo = np.asarray([v.lo for v in variables], dtype=float)
    hi = np.asarray([v.hi for v in variables], dtype=float)
    tag = origin + (("stage", STAGE_SLSQP), ("minimize", minimize), ("eps", eps))
    state = {"parent": None, "points": {}, "accepted": [], "names": None, "frozen": set(), "scales": None}

    def to_theta(x):
        out = dict(fixed)
        for i, (v, value) in enumerate(zip(variables, x)):
            value = min(max(float(value), v.lo), v.hi)
            if value == x0[i] and exact[i] is not None:
                out[v.component] = exact[i]     # 시작 좌표 그대로면 시작 θ 원값 -- ln→exp 왕복 1 ulp 로 키가 바뀌지 않게
            else:
                out[v.component] = math.exp(value) if v.log else value
        return out

    def point(x):
        x = np.array(x, dtype=float, copy=True)   # SLSQP 는 x 배열을 제자리에서 바꾼다 -- 복사본만 저장·키로 쓴다
        hx = tuple(float(v).hex() for v in x)
        hit = state["points"].get(hx)
        if hit is not None:
            return hit
        stop = _budget_stop(sctx)
        if stop is not None:
            raise _Abort(stop, x)
        res = evaluate(sctx, to_theta(x), start.cells, parent=state["parent"], origin=tag)
        if res.status not in ACCEPTED_STATUSES:
            raise _Abort("candidate_failure", x)
        if state["scales"] is None:          # 첫 받아들인 점(시작점)의 b_P 로 고정
            state["scales"] = {AXIS_POWER: res.objectives.power_resolution_w, AXIS_AREA: sctx.domain.area_resolution_m2}
        names, cvals = _rows(res, eps, state["scales"])
        if state["names"] is None:
            state["names"] = names
        elif names != state["names"]:
            raise _Abort("constraint_set_changed", x)
        entry = {"x": x, "res": res, "f": _axis_value(res, minimize) / state["scales"][minimize], "c": cvals,
                 "jac": None}
        state["points"][hx] = entry
        return entry

    def jac_of(x):
        entry = point(x)
        if entry["jac"] is None or entry["jac"][2] != frozenset(state["frozen"]):
            skip = frozenset(state["frozen"])
            cols = fd_jacobian(sctx, variables, entry["x"], entry["res"], start.cells, to_theta, tag, skip)
            gf = np.zeros(len(variables))
            gc = np.zeros((len(entry["c"]), len(variables)))
            for i, (col, step) in enumerate(cols):
                if col is None:
                    raise _Abort("fd_column_failure", entry["x"], i)
                if step == 0:
                    continue
                names, cvals = _rows(col, eps, state["scales"])
                if names != state["names"]:
                    raise _Abort("constraint_set_changed", entry["x"])
                gf[i] = (_axis_value(col, minimize) / state["scales"][minimize] - entry["f"]) / step
                gc[:, i] = (cvals - entry["c"]) / step
            entry["jac"] = (gf, gc, skip)
        return entry["jac"]

    def accept(xk):
        entry = point(xk)
        state["parent"] = entry["res"]
        state["accepted"].append(entry)

    try:
        first = point(np.asarray(x0, dtype=float))
    except _Abort as exc:
        return SolveResult(None, eps, minimize, 0, 0, "start_" + exc.reason, ())
    accept(first["x"])
    n = len(variables)
    radius = (hi - lo) / 2
    steps0 = fd_jacobian(sctx, variables, first["x"], first["res"], start.cells, to_theta, tag, frozenset())
    h = np.asarray([abs(step) for _col, step in steps0], dtype=float)
    resolved = [int(math.ceil(math.log2((hi[i] - lo[i]) / h[i]))) for i in range(n) if h[i] > 0]
    maxiter = max(1, sum(max(r, 1) for r in resolved))
    cap = max(1, int(math.ceil(math.log2(float(np.max(radius)) / float(np.min(h[h > 0])))))) if np.any(h > 0) else 1
    # [결정 11] SLSQP 입력 행 척도: 행마다 1 / max(1, |시작점 c|) -- 양의 상수 배라 feasible 집합·`best` 판정(원 c ≥ 0)은 그대로고, 면적 예산
    # 행(c ~ 1e6, 분모 b_A)처럼 크기가 몇 자릿수 다른 행이 QP 부분문제를 '제약 비호환'(status 4)으로 만드는 것을 막는다.
    row_w = 1.0 / np.maximum(1.0, np.abs(first["c"]))
    f_w = 1.0 / max(1.0, abs(first["f"]))           # 목적도 같은 이유로 SLSQP 입력만 척도(best 비교는 원 f); ftol 도 f_w 배 = 목적 분해능 1 단위(종전 ftol = 1)
    restarts, iterations, stop, aborts, frozen_log = 0, 0, "converged", [], []
    centre = first["x"]
    while True:
        shrink = 2 ** restarts
        box_lo = np.maximum(lo, centre - radius / shrink) if restarts else lo.copy()
        box_hi = np.minimum(hi, centre + radius / shrink) if restarts else hi.copy()
        for i in state["frozen"]:
            box_lo[i] = box_hi[i] = centre[i]
        cons = {"type": "ineq", "fun": lambda x: point(x)["c"] * row_w, "jac": lambda x: jac_of(x)[1] * row_w[:, None]}
        try:
            out = scipy_minimize(lambda x: point(x)["f"] * f_w, np.array(centre, copy=True), jac=lambda x: jac_of(x)[0] * f_w, method="SLSQP",
                                 bounds=list(zip(box_lo, box_hi)), constraints=[cons], callback=accept,
                                 options={"ftol": f_w, "maxiter": maxiter})
            iterations += int(out.nit)
            point(out.x)
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
                    accept(exc.x)                # 받아들일 상태로 평가된 반복점(SLSQP 가 jac 을 물은 점) -- 새 중심
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
    best = None
    for entry in state["accepted"]:
        if np.all(entry["c"] >= 0) and (best is None or (entry["f"], entry["res"].seq) < (best["f"], best["res"].seq)):
            best = entry
    history = tuple(e["res"] for e in state["accepted"])
    return SolveResult(None if best is None else best["res"], eps, minimize, iterations, restarts, stop, history,
                       tuple(aborts), tuple(frozen_log))
