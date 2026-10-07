"""외층 ε-제약 SLSQP 한 번 (설계 design_mod6_search_front 6.2, DEC-54·77, LR10).

진입점: `solve_eps(sctx, start, minimize, eps, deadline, origin) -> SolveResult`.

* 변수: `SearchDomain.variables`(ln_idu·y·ln current·ln R) + 칸이 구간인(lo < hi) MOS 의 L(칸 bounds). L 칸 index 벡터는
  시작점 것을 그대로 쓴다(L-a) -- 칸이 한 점인 L 은 고정값이다. 결정변수 밖 값은 바꾸지 않는다.
* 목적 = `minimize` 축 값 / 그 축 분해능(b_P 또는 b_A), ε = (축, 상한) 이면 제약 (ε − 값)/분해능 ≥ 0(설계 5절). 다른 제약 =
  커널 결과의 정규화 행(봉인 6·반전 하한·목적 축 spec 제약) + θ 전류 원뿔 행. 가중합 없음(DEC-77).
* `fun`·`jac`·`constraints` 는 모두 같은 x 의 같은 평가를 읽는다(x 의 float.hex 로 묶음 -- 커널 1회). jac 은 `fd_jacobian`
  (parent = 그 x 의 평가). x 평가의 parent = 직전 수락 반복(callback).
* 실패 처리(설계 6.2): x 또는 FD 열이 받아들일 상태가 아니거나 제약 행 이름 집합이 시작점과 달라지면 그 SLSQP 실행을 끊고
  마지막 수락 반복을 중심으로 상자 반경을 절반으로 줄여 다시 시작한다. 반경 = 정의역 bounds 반폭(설계의 '격자 반경 × 2^m' 대신
  -- m 을 정할 예산 식이 U-47 보류라 전역 bounds 에서 시작해 줄인다, CONTRACT 열린 항목 S-7). 재시작 상한 =
  max_i ⌈log2(반경ᵢ/hᵢ)⌉(K_max 와 같은 bisection 논리). 상수 페널티 없음.
* 종료: SLSQP 수렴(ftol = 정규화 목적 한 칸 = 1), 반복 상한(= 남은 예산 / ((n + 1)·평가 시간 중앙값)), 벽시계 `deadline`
  (time.perf_counter 기준) 도달, 재시작 상한.
* `best` = 수락 반복 중 모든 제약 c ≥ 0 인 점에서 목적 최소(동률은 seq 작은 쪽). 없으면 None.
"""
import math
import statistics
import time

import numpy as np
from scipy.optimize import minimize as scipy_minimize

from gmid_engine.sizing import THETA_L

from .fd_jacobian import fd_jacobian
from .kernel import evaluate
from .search_values import ACCEPTED_STATUSES, AXIS_POWER, CON_EPS, STAGE_SLSQP, SolveResult, Variable


class _Abort(Exception):
    """SLSQP 실행을 끊는 내부 신호(재시작 또는 예산 끝). 이 파일 밖으로 나가지 않는다."""

    def __init__(self, reason, x=None, component=None):
        super().__init__(reason)
        self.reason = reason
        self.x = x
        self.component = component


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
    names = {v.component for v in variables} | set(fixed)
    for comp in theta:
        if comp not in names:
            fixed[comp] = theta[comp]
    x0 = []
    for v in variables:
        raw = theta[v.component]
        x0.append(min(max(math.log(raw) if v.log else raw, v.lo), v.hi))
    return tuple(variables), fixed, x0


def _axis_value(result, axis):
    return result.objectives.power_w if axis == AXIS_POWER else result.objectives.area_m2


def _axis_scale(sctx, axis):
    return sctx.domain.power_resolution_w if axis == AXIS_POWER else sctx.domain.area_resolution_m2


def _rows(sctx, result, eps):
    rows = list(result.constraints) + list(result.cone)
    names = tuple(r.name for r in rows)
    values = [r.c for r in rows]
    if eps is not None:
        axis, bound = eps
        values.append((bound - _axis_value(result, axis)) / _axis_scale(sctx, axis))
        names += (CON_EPS + ":" + axis,)
    return names, np.asarray(values, dtype=float)


def solve_eps(sctx, start, minimize, eps, deadline, origin):
    variables, fixed, x0 = _layout(sctx, start)
    lo = np.asarray([v.lo for v in variables], dtype=float)
    hi = np.asarray([v.hi for v in variables], dtype=float)
    scale = _axis_scale(sctx, minimize)
    tag = origin + (("stage", STAGE_SLSQP), ("minimize", minimize), ("eps", eps))

    def to_theta(x):
        out = dict(fixed)
        for v, value in zip(variables, x):
            value = min(max(float(value), v.lo), v.hi)
            out[v.component] = math.exp(value) if v.log else value
        return out

    state = {"parent": None, "points": {}, "accepted": [], "names": None}

    def point(x):
        x = np.asarray(x, dtype=float)
        hx = tuple(float(v).hex() for v in x)
        hit = state["points"].get(hx)
        if hit is not None:
            return hit
        if time.perf_counter() > deadline:
            raise _Abort("budget", x)
        res = evaluate(sctx, to_theta(x), start.cells, parent=state["parent"], origin=tag)
        if res.status not in ACCEPTED_STATUSES:
            raise _Abort("candidate_failure", x)
        names, cvals = _rows(sctx, res, eps)
        if state["names"] is None:
            state["names"] = names
        elif names != state["names"]:
            raise _Abort("constraint_set_changed", x)
        entry = {"x": x, "res": res, "f": _axis_value(res, minimize) / scale, "c": cvals, "jac": None}
        state["points"][hx] = entry
        return entry

    def jac_of(x):
        entry = point(x)
        if entry["jac"] is None:
            cols = fd_jacobian(sctx, variables, entry["x"], entry["res"], start.cells, to_theta, tag)
            gf = np.zeros(len(variables))
            gc = np.zeros((len(entry["c"]), len(variables)))
            for i, (col, step) in enumerate(cols):
                if col is None:
                    raise _Abort("fd_column_failure", entry["x"], variables[i].component)
                if step == 0:
                    continue
                names, cvals = _rows(sctx, col, eps)
                if names != state["names"]:
                    raise _Abort("constraint_set_changed", entry["x"])
                gf[i] = (_axis_value(col, minimize) / scale - entry["f"]) / step
                gc[:, i] = (cvals - entry["c"]) / step
            entry["jac"] = (gf, gc)
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
    steps = [abs(step) for _col, step in fd_jacobian(sctx, variables, first["x"], first["res"], start.cells,
                                                         to_theta, tag) if step]
    h_min = min(steps) if steps else float(np.min(radius))
    cap = max(1, int(math.ceil(math.log2(float(np.max(radius)) / h_min)))) if h_min > 0 else 1
    restarts, iterations, stop, aborts = 0, 0, "converged", []
    centre = first["x"]
    while True:
        shrink = 2 ** restarts
        box_lo = np.maximum(lo, centre - radius / shrink) if restarts else lo
        box_hi = np.minimum(hi, centre + radius / shrink) if restarts else hi
        t_eval = statistics.median(sctx.eval_times) if sctx.eval_times else None
        remaining = deadline - time.perf_counter()
        if remaining <= 0:
            stop = "budget"
            break
        maxiter = max(1, int(remaining / ((n + 1) * t_eval))) if t_eval else 1
        cons = {"type": "ineq", "fun": lambda x: point(x)["c"], "jac": lambda x: jac_of(x)[1]}
        try:
            out = scipy_minimize(lambda x: point(x)["f"], centre, jac=lambda x: jac_of(x)[0], method="SLSQP",
                                 bounds=list(zip(box_lo, box_hi)), constraints=[cons], callback=accept,
                                 options={"ftol": 1, "maxiter": maxiter})
            iterations += int(out.nit)
            point(out.x)
            accept(out.x)
            stop = "converged" if out.success else "slsqp_" + str(out.status)
            break
        except _Abort as exc:
            stop = exc.reason
            aborts.append(exc.reason if exc.component is None else exc.reason + ":" + ":".join(exc.component))
            if exc.reason == "budget":
                break
            restarts += 1
            if restarts > cap:
                stop = "restart_cap"
                break
            if exc.reason == "fd_column_failure" and np.array_equal(exc.x, state["accepted"][-1]["x"]):
                stop = "fd_column_failure_at_centre"   # 같은 중심의 같은 FD 열이 다시 실패할 뿐이라 재시작이 진전 없음(S-16)
                break
            centre = state["accepted"][-1]["x"]
    best = None
    for entry in state["accepted"]:
        if np.all(entry["c"] >= 0) and (best is None or (entry["f"], entry["res"].seq) < (best["f"], best["res"].seq)):
            best = entry
    history = tuple(e["res"] for e in state["accepted"])
    return SolveResult(None if best is None else best["res"], eps, minimize, iterations, restarts, stop, history,
                       tuple(aborts))
