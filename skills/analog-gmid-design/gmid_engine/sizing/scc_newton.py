"""순환 블록 감쇠 Newton -- Gauss-Seidel 이 수축하지 않는 SCC 의 잔차 방정식 풀이 (계획 N3.6 수렴 판정·SC-c, 오케스트레이터
결정 2026-10-08 'q ≥ 1 이면 SCC 잔차에 감쇠 Newton', 계약 5.5b).

진입점: `newton_solve(nodes, values, evaluate, tolerance, width, devices=()) -> (values, (k, norms, tol, K_max))`.

* `evaluate(values) -> (residuals, jacobian) | None`: SCC 노드 순서의 잔차 r_i = V_i − g_i(V)(writer 식)와 야코비안
  J = ∂r/∂V(SCC 노드끼리, n × n 행 tuple). 그 점이 정의역 밖(LUT 조회 실패·빈 창)이면 None.
* `tolerance(values) -> tol`(V, 양수), `width` = K_max 계산 폭(V). 반복 k 마다 J 를 LU 분해(scipy `lu_factor` -- metrics 점
  풀이와 같은 방식, 영 피벗이면 reason `newton_singular`)해 Newton 걸음 Δ = −J⁻¹r 를 풀고, ‖r‖∞ ≤ tol 이고 ‖Δ‖∞ ≤ tol 이면
  수렴(r7: 다음 보정 = 노드전압 오차 추정 -- 나쁜 조건 SCC 에서 잔차만 작은 점을 받지 않는다). 아니면 k ≥ K_max =
  `k_max(width, tol)` 이면 `NonconvergentError`(reason `newton_iteration_cap`). 역추적 선 탐색: α = 1 부터 반씩 줄이며
  정의역 안이고 ‖r(V + αΔ)‖₂ < ‖r(V)‖₂ 인 첫 α 를 받는다(Newton 방향은 ½‖r‖₂² 의 하강 방향이라 충분히 작은 α 면 줄어든다 --
  ‖·‖∞ 는 매끄럽지 않아 하강이 보장되지 않는다. 수렴 판정은 ‖r‖∞). α < 1 이고 α·‖Δ‖∞ < tol(더 줄인 걸음은 노드를 허용오차보다
  덜 움직인다) 이거나 시험점이 부동소수로 현재 점과 같아질 때까지 받을 α 가 없으면 reason `newton_line_search`. 시작점이 정의역 밖이면 reason `newton_start_outside_domain`. margin = ‖r‖∞/tol(시작점 밖이면 None),
  detail nodes·iterations·norms(반복마다 ‖r‖∞)·tol·k_max. 상수 없음(감쇠 비 = 반, 정지 = tol·K_max·걸음 α·‖Δ‖∞ < tol·부동소수 해상도).
* 입력 `values` 는 바꾸지 않는다.
"""
import numpy
import scipy.linalg

from gmid_engine.core import NonconvergentError

from .k_max import k_max
from .s2_values import REASON_NEWTON_CAP, REASON_NEWTON_LINE_SEARCH, REASON_NEWTON_SINGULAR, REASON_NEWTON_START


def _fail(reason, nodes, devices, k, norms, tol, limit, margin):
    return NonconvergentError(devices=tuple(devices), margin=margin,
                              detail={"reason": reason, "nodes": tuple(nodes), "iterations": k, "norms": tuple(norms),
                                      "tol": tol, "k_max": limit})


def newton_solve(nodes, values, evaluate, tolerance, width, devices=()):
    current = dict(values)
    system = evaluate(current)
    if system is None:
        raise _fail(REASON_NEWTON_START, nodes, devices, 0, (), None, None, None)
    norms = []
    k = 0
    while True:
        residuals, jacobian = system
        r = numpy.asarray(residuals, dtype=float)
        norm = float(numpy.max(numpy.abs(r)))
        norms.append(norm)
        tol = tolerance(current)
        limit = k_max(width, tol)
        lu, piv = scipy.linalg.lu_factor(numpy.asarray(jacobian, dtype=float))
        if not numpy.diag(lu).all():
            raise _fail(REASON_NEWTON_SINGULAR, nodes, devices, k, norms, tol, limit, norm / tol)
        step = scipy.linalg.lu_solve((lu, piv), -r)
        reach = float(numpy.max(numpy.abs(step)))
        if norm <= tol and reach <= tol:                # 잔차와 다음 보정(= 노드전압 오차 추정, 2차 수렴) 둘 다 tol 안
            return current, (k, tuple(norms), tol, limit)
        if k >= limit:
            raise _fail(REASON_NEWTON_CAP, nodes, devices, k, norms, tol, limit, norm / tol)
        alpha = 1.0
        while True:
            if alpha < 1 and alpha * reach < tol:          # 더 줄인 걸음은 노드를 tol 보다 덜 움직인다 -- 받을 α 없음
                raise _fail(REASON_NEWTON_LINE_SEARCH, nodes, devices, k, norms, tol, limit, norm / tol)
            trial = dict(current)
            for node, d in zip(nodes, step):
                trial[node] = current[node] + alpha * float(d)
            if all(trial[node] == current[node] for node in nodes):
                raise _fail(REASON_NEWTON_LINE_SEARCH, nodes, devices, k, norms, tol, limit, norm / tol)
            candidate = evaluate(trial)
            if candidate is not None and float(numpy.dot(candidate[0], candidate[0])) < float(numpy.dot(r, r)):
                current, system = trial, candidate
                break
            alpha = alpha / 2
        k += 1
