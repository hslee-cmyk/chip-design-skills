"""입력 포트 창 끝 식 -- 영역 경계 행의 교집합 (사용자 결정 J-E 2026-10-08·O-61 P2, 설계 41 §4.6 SP-2 (c)·4.7-3 2, 확인 행 D-J5).

진입점: `saturation_window(unknown, root, values, gradient, rows, *, slope=None) -> (dlo, dhi, slope) | None`.

창 끝 식(행 교집합)은 이 함수 하나에만 있다. 입력 공통모드 x(= `root` 넷)를 움직였을 때 x 를 따라 움직이는 노드의 전압 차가 영향받는
소자 전부에서 행 여유 ≥ 0 을 지키는 **이동량** Δ 구간 [dlo, dhi](출발점 x₀ = 0 기준)이다. 끝은 봉인 시점 값이고 행의 여유가 정한다(판정 여유 0 -- tol 항 없음, O-204).

* 입력 `values` = x 에서 푼 노드전압(해 하나), `gradient(net, values) -> (g, {노드: ∂g/∂V})` = 노드 writer 식과 그 편미분(`block_columns._Circuit.writer_grad` 의
  Newton 야코비안과 같은 식), `unknown` = 고정 노드(레일·목표·입력 DC)가 아닌 모든 노드(x 로 움직이는 고정 노드 포함),
  `rows` = ((a, b, sign, slack, kind), ...) -- `_helpers_dc_solve.Circuit.region_rows` 의 5원소 행: 여유가 기대는 전압 차의 두 넷 a·b, 부호 sign(여유의 x 미분 =
  sign·(s_a − s_b)), 그 점의 여유 slack(V, 음수면 이미 영역 밖), 행 종류 kind. **`kind` 는 창 계산에 쓰지 않는다.**
* `root` = 넷 하나(그 넷의 s = 1). 쌍·묶음은 받지 않는다(넷 이름이 아니면 `TypeError`, `unknown` 에 없으면 `ValueError` -- 조용히 다른 연립을 풀지 않는다).
* 노드가 x 를 따라 움직이는 정도 s_n = dV_n/dx 는 선형 연립 s_n − Σ_j (∂g_n/∂V_j)·s_j = 0 (root 가 아닌 n), root 행은 s = 1, 고정 노드는 s = 0 의 해다.
  행의 변화율은 sign·(s_a − s_b) = a. a > 0 이면 Δ 아래쪽, a < 0 이면 위쪽에서 slack 이 닫힌다: Δ ≥ −slack/a (a > 0), Δ ≤ slack/|a| (a < 0). 경계는 slack 의
  1차 외삽이고(VDsat 의 x 의존은 해에서 한 번 잰 값으로 둔다) 마지막 판정은 봉인이 한다.
* 변화율 |a| 가 부동소수 해상도(`sys.float_info.epsilon`, V/V 행 분해능) 이하인 행은 x 를 따라 움직이지 않는 행이라 끝을 만들지 않고 건너뛴다. 건너뛴 행의 slack 이
  음수이면 그 행은 x 와 무관하게 이미 영역 밖이라 창이 정의되지 않는다 -> `None`(fail-closed).
* `slope`(키워드 전용, {넷: dV/dx})를 주면 안의 감도 연립을 풀지 않고 그 감도로 끝만 낸다(KVL 고정 구조 -- 감도 정본은 부르는 쪽). 그때
  앞 넷 인자(`unknown`·`root`·`values`·`gradient`)는 읽지 않고 반환 slope = 받은 값.
* 반환 (dlo, dhi, slope) = Δ 구간(제약이 없는 쪽은 ∓inf)과 감도. 연립이 특이하거나 정의역 밖이면(`gradient` 가 `SealViolationError`) `None`.
* 상수 없음 -- 변화율이 0 인지는 부동소수 해상도(`sys.float_info.epsilon`)로 가른다.
"""
import math
import sys

import numpy

from gmid_engine.core import SealViolationError


def _sensitivities(unknown, root, values, gradient):
    if not isinstance(root, str):
        raise TypeError("saturation_window: root 는 넷 이름 하나여야 한다(쌍·묶음 없음): %r" % (root,))
    if root not in unknown:
        raise ValueError("saturation_window: root %r 가 unknown 에 없다" % (root,))
    index = {net: i for i, net in enumerate(unknown)}
    n = len(unknown)
    matrix = numpy.zeros((n, n))
    rhs = numpy.zeros(n)
    for net in unknown:
        i = index[net]
        matrix[i, i] = 1.0
        if net == root:
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


def saturation_window(unknown, root, values, gradient, rows, *, slope=None):
    if slope is None:
        try:
            slope = _sensitivities(tuple(unknown), root, values, gradient)
        except SealViolationError:
            return None
        if slope is None:
            return None
    lo, hi = -math.inf, math.inf
    for a, b, sign, slack, _kind in rows:
        rate = sign * (slope.get(a, 0.0) - slope.get(b, 0.0))
        if abs(rate) <= sys.float_info.epsilon:
            if slack < 0:
                return None
            continue
        reach = slack / abs(rate)
        if rate > 0:
            lo = max(lo, -reach)
        else:
            hi = min(hi, reach)
    return lo, hi, slope
