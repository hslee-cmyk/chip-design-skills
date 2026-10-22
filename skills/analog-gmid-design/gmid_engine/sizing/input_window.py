"""입력 포트 창 끝 식 -- 영역 경계 행의 교집합 (사용자 결정 J-E 2026-10-08·O-61 P2, 설계 41 §4.6 SP-2 (c)·4.7-3 2, 확인 행 D-J5).

진입점: `saturation_window(unknown, roots, values, gradient, rows, *, slope=None) -> (dlo, dhi, slope) | None`.

창 끝 식(행 교집합)은 이 함수 하나에만 있다. 입력 공통모드 x(= `roots` 가 함께 움직이는 넷)를 움직였을 때 x 를 따라 움직이는 노드의 전압 차가 영향받는
소자 전부에서 행 여유 ≥ 0 을 지키는 **이동량** Δ 구간 [dlo, dhi](출발점 x₀ = 0 기준)이다. 끝은 봉인 시점 값이고 tol 을 포함한다(행의 여유가 정한다).

* 입력 `values` = x 에서 푼 노드전압(해 하나), `gradient(net, values) -> (g, {노드: ∂g/∂V})` = 노드 writer 식과 그 편미분(`_helpers_dc_solve.Circuit`
  의 Newton 야코비안과 같은 식), `unknown` = 고정 노드(레일·목표·입력 DC)가 아닌 모든 노드(x 로 움직이는 고정 노드 포함),
  `rows` = ((a, b, sign, slack, kind), ...) -- `Circuit.region_rows` 의 5원소 행: 여유가 기대는 전압 차의 두 넷 a·b, 부호 sign(여유의 x 미분 =
  sign·(s_a − s_b)), 그 점의 여유 slack(V, 음수면 이미 영역 밖), 행 종류 kind. **`kind` 는 창 계산에 쓰지 않는다.**
* `roots` 원소 = 넷이면 그 넷의 s = 1(커널 뿌리·선언 포트 묶음), 쌍 `(행 넷, 고정 넷)` 이면 행 넷의 식을 s_고정넷 = 1 로 바꾼다(측정 구성 follower 의
  'W4 뿌리 행을 V_out = x 로 바꾼 같은 연립').
* 노드가 x 를 따라 움직이는 정도 s_n = dV_n/dx 는 선형 연립 s_n − Σ_j (∂g_n/∂V_j)·s_j = 0 (roots 가 아닌 n), roots 행은 위 식, 고정 노드는 s = 0 의 해다.
  행의 변화율은 sign·(s_a − s_b) = a. a > 0 이면 Δ 아래쪽, a < 0 이면 위쪽에서 slack 이 닫힌다: Δ ≥ −slack/a (a > 0), Δ ≤ slack/|a| (a < 0). a = 0
  은 제약이 아니다. 경계는 slack 의 1차 외삽이고(VDsat 의 x 의존은 해에서 한 번 잰 값으로 둔다) 마지막 판정은 봉인이 한다.
* `slope`(키워드 전용, {넷: dV/dx})를 주면 안의 감도 연립을 풀지 않고 그 감도로 끝만 낸다(KVL 고정 구조 -- 감도 정본은 부르는 쪽). 그때
  `unknown`·`gradient` 는 읽지 않고 반환 slope = 받은 값.
* 반환 (dlo, dhi, slope) = Δ 구간(제약이 없는 쪽은 ∓inf)과 감도. 연립이 특이하거나 정의역 밖이면(`gradient` 가 `SealViolationError`) `None`.
* 상수 없음 -- 변화율이 0 인지는 부동소수 해상도(`sys.float_info.epsilon`)로 가른다.
"""
import math
import sys

import numpy

from gmid_engine.core import SealViolationError


def _sensitivities(unknown, roots, values, gradient):
    index = {net: i for i, net in enumerate(unknown)}
    n = len(unknown)
    plain = frozenset(r for r in roots if isinstance(r, str))
    replaced = {r[0]: r[1] for r in roots if not isinstance(r, str)}
    matrix = numpy.zeros((n, n))
    rhs = numpy.zeros(n)
    for net in unknown:
        i = index[net]
        if net in replaced:
            matrix[i, index[replaced[net]]] = 1.0
            rhs[i] = 1.0
            continue
        matrix[i, i] = 1.0
        if net in plain:
            rhs[i] = 1.0
            continue
        _g, grad = gradient(net, values)
        for other, derivative in grad.items():
            if other in index:
                matrix[i, index[other]] -= derivative
    try:
        solution = numpy.linalg.solve(matrix, rhs)
    except numpy.linalg.LinAlgError:
        return None
    return {net: float(solution[index[net]]) for net in unknown}


def saturation_window(unknown, roots, values, gradient, rows, *, slope=None):
    if slope is None:
        try:
            slope = _sensitivities(tuple(unknown), tuple(roots), values, gradient)
        except SealViolationError:
            return None
        if slope is None:
            return None
    lo, hi = -math.inf, math.inf
    for a, b, sign, slack, _kind in rows:
        rate = sign * (slope.get(a, 0.0) - slope.get(b, 0.0))
        if abs(rate) <= sys.float_info.epsilon:
            continue
        reach = slack / abs(rate)
        if rate > 0:
            lo = max(lo, -reach)
        else:
            hi = min(hi, reach)
    return lo, hi, slope
