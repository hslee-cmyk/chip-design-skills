"""입력 공통모드 y_icm 의 포화 창 -- 봉인 시점 경계 (사용자 결정 J-E 2026-10-08, 설계 41 §4.6 '입력 DC 정책' SP-2 (c), 확인 행 D-J5).

진입점: `saturation_window(unknown, root, values, gradient, rows) -> (lo, hi)`.

입력 DC 가 대기(`pending: SP-2`)인 회로는 입력 공통모드를 W4 자유 변수 y_icm 으로 두고(`writer_plan`), 그 범위는 입력 창
[Vin,min, Vin,max] ∩ [rail_lo, rail_hi] 다. 창의 경계는 **봉인 시점 값**이고 tol 을 포함한다: 입력 공통모드 x(= W4 뿌리 넷의 전압)를 움직였을 때
x 를 따라 움직이는 노드들의 VDS 가 영향받는 소자 전부에서 봉인 7 의 포화 판정 VDS ≥ VDsat + tol_VDsat 를 지키는 x 구간이다.

* 입력 `values` = x 에서 푼 노드전압(해 하나), `gradient(net, values) -> (g, {노드: ∂g/∂V})` = 노드 writer 식과 그 편미분(`block_columns` 의
  Newton 야코비안과 같은 식), `unknown` = 고정 노드(레일·목표·입력 DC)가 아닌 모든 노드, `rows` = ((d, s, 부호, slack), ...) -- 전도 MOS 마다
  VDS = 부호·(V(d) − V(s)) 의 두 넷과 그 점의 포화 여유 slack = VDS − VDsat − tol_VDsat (V, 음수면 이미 위반).
* 노드가 x 를 따라 움직이는 정도 s_n = dV_n/dx 는 선형 연립 s_n − Σ_j (∂g_n/∂V_j)·s_j = 0 (n ≠ x), s_x = 1 의 해다(고정 노드는 s = 0). 소자의 VDS 변화율은
  부호·(s_d − s_s) = a. a > 0 이면 x 아래쪽, a < 0 이면 위쪽에서 slack 이 닫힌다: x ≥ x0 − slack/a (a > 0), x ≤ x0 + slack/|a| (a < 0). a = 0(x 와 무관한 소자)
  은 제약이 아니다. 경계는 slack 의 VDS 1차 외삽이고(VDsat 의 x 의존은 해에서 한 번 잰 값으로 둔다) 마지막 판정은 봉인 7 이 한다.
* 반환 (lo, hi) = x 구간(제약이 없는 쪽은 ∓inf). 연립이 특이하거나 정의역 밖이면(`gradient` 가 `SealViolationError`) `None`.
* 상수 없음 -- 변화율이 0 인지는 부동소수 해상도(`sys.float_info.epsilon`)로 가른다.
"""
import math
import sys

import numpy

from gmid_engine.core import SealViolationError


def _sensitivities(unknown, root, values, gradient):
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


def saturation_window(unknown, root, values, gradient, rows):
    try:
        slope = _sensitivities(tuple(unknown), root, values, gradient)
    except SealViolationError:
        return None
    if slope is None:
        return None
    x0 = values[root]
    lo, hi = -math.inf, math.inf
    for d, s, sign, slack in rows:
        rate = sign * (slope.get(d, 0.0) - slope.get(s, 0.0))
        if abs(rate) <= sys.float_info.epsilon:
            continue
        reach = slack / abs(rate)
        if rate > 0:
            lo = max(lo, x0 - reach)
        else:
            hi = min(hi, x0 + reach)
    return lo, hi
