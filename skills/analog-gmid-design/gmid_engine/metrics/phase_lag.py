"""T(0) 대비 누적 위상 지연 -- 실제 풀이로 언랩 (설계 design_mod1_lut_mod5_mna 3.3 '위상 언랩', 3.4 PM 정의).

진입점: `phase_lag`.

* 시작점 = ω = 0 의 실수 해 T(0)(위상 0 또는 π) -- '충분히 낮은 시작 주파수' 상수가 필요 없다.
* 0 < ω < ω_end 인 격자점과 끝점 (ω_end, T_end) 를 차례로 지나며 칸마다 Δφ = arg(T_k / T_{k-1})(주값)를 더한다.
* |Δφ| ≥ π/2 인 칸은 중점(기하, 아래 끝이 0 이면 산술)을 실제로 풀어 둘로 나눈다(명시적 작업 목록 -- 재귀 한도 없음).
  중점이 끝점과 같은 부동소수가 되도록 좁혀도 |Δφ| ≥ π/2 이면 jω 축 위 영점·극점이라 위상이 정의되지 않는다 ->
  NONCONVERGENT(그 ω 와 함께). T 가 정확히 0 인 표본도 위상이 없어 같은 처리.
* 극점·영점 고유값은 쓰지 않는다(격자 배치 전용).
"""
import cmath
import math

from gmid_engine.core import NonconvergentError

from ._helpers_product import product_at


def _segment(factors, start, end):
    total = 0.0
    work = [(start, end)]
    while work:
        (w0, t0), (w1, t1) = work.pop()
        if t0 == 0 or t1 == 0:
            raise NonconvergentError(detail={"reason": "zero_response_on_axis", "omega_lo": w0, "omega_hi": w1})
        step = cmath.phase(t1 / t0)
        if abs(step) < math.pi / 2:
            total += step
            continue
        mid = math.sqrt(w0 * w1) if w0 > 0 else (w0 + w1) / 2
        if not w0 < mid < w1:
            raise NonconvergentError(detail={"reason": "phase_jump_unresolved", "omega_lo": w0, "omega_hi": w1})
        t_mid, _ = product_at(factors, mid)
        work.append(((mid, t_mid), (w1, t1)))
        work.append(((w0, t0), (mid, t_mid)))
    return total


def phase_lag(factors, omegas, values, omega_end, value_end):
    """루프 인수, 공유 격자, 격자 위 T, 끝점 (ω_end, T_end) -> T(0) 대비 누적 지연(rad, 지연이 양수)."""
    points = [(float(w), complex(v)) for w, v in zip(omegas, values) if w < omega_end]
    points.append((float(omega_end), complex(value_end)))
    accumulated = 0.0
    for start, end in zip(points, points[1:]):
        accumulated += _segment(factors, start, end)
    return -accumulated
