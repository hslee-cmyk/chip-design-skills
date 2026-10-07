"""|T(jω)| = level 첫 교차 -- 격자 괄호 + log ω 이분 (설계 design_mod1_lut_mod5_mna 3.4 `ugf_ss_hz`·`gbw_ss_hz`).

진입점: `find_crossing`.

1. 격자 위 |T| 에서 |T(0)| > level 이고 처음으로 |T| ≤ level 이 되는 칸을 괄호로 잡는다. |T(0)| ≤ level 이면 교차 없음
   (`reason = "dc_not_above_level"`).
2. 격자 끝까지 |T| > level 이면 상단 괄호를 극점·영점 상계로 유도한다: ω > max|p| 에서
   |T(jω)| ≤ |K|·Π(ω + |z|)/Π(ω − |p|) (삼각부등식, K 는 격자 끝점에서 잰 값으로 맞춘 이득). 극점 수 > 영점 수면 상계가
   단조 감소하므로 ω 를 두 배씩 늘려 상계 < level 인 ω 를 찾는다(부동소수 상한까지 -- 넘치면 NONCONVERGENT).
   극점 수 < 영점 수, 또는 같고 |K| ≥ level 이면 위쪽 교차가 보장되지 않는다(`reason = "no_crossing_above"`).
   상계로 잡은 끝점은 실제 풀이로 |T| ≤ level 을 확인한다(어긋나면 NONCONVERGENT).
3. 이분: lo > 0 이면 기하 중점, lo = 0 이면 산술 중점. 정지 = (a) 중점이 끝점과 같은 부동소수(분해능 끝) 또는
   (b) | |T(mid)| − level | ≤ 사후 오차(MNA 풀이로 구별 불가). 정지 상수 없음.
"""
import math

from gmid_engine.core import NonconvergentError

from ._helpers_product import product_at
from .mna_types import Crossing


def _rational_bound(poles, zeros, gain, omega):
    num = math.prod(omega + abs(z) for z in zeros)
    den = math.prod(omega - abs(p) for p in poles)
    return gain * num / den


def _upper_bracket(factors, omegas, values, level):
    poles = tuple(p for f in factors for p in f.response.roots.poles)
    zeros = tuple(z for f in factors for z in f.response.roots.zeros[f.column])
    if len(poles) < len(zeros):
        return None
    top = float(omegas[-1])
    if top <= 0:
        return None
    s = complex(0, top)
    shape = math.prod(abs(s - z) for z in zeros) / math.prod(abs(s - p) for p in poles)
    gain = abs(values[-1]) / shape
    if len(poles) == len(zeros) and gain >= level:
        return None
    pole_top = max((abs(p) for p in poles), default=0.0)
    omega = top if top > pole_top else pole_top * 2
    while _rational_bound(poles, zeros, gain, omega) >= level:
        omega *= 2
        if not math.isfinite(omega):
            raise NonconvergentError(detail={"reason": "crossing_bracket_overflow", "level": level})
    value, _ = product_at(factors, omega)
    if abs(value) > level:
        raise NonconvergentError(
            detail={"reason": "crossing_bound_violated", "level": level, "omega": omega, "magnitude": abs(value)}
        )
    return omega, value


def find_crossing(factors, omegas, values, level):
    """루프 인수 tuple, 공유 격자, 격자 위 T 값, level -> `Crossing`."""
    level = float(level)
    if not level > 0 or not math.isfinite(level):
        raise ValueError("find_crossing: level 은 양의 유한수여야 한다: %r" % level)
    mags = abs(values)
    if not mags[0] > level:
        return Crossing(level=level, reason="dc_not_above_level")
    lo, v_lo, hi, v_hi = None, None, None, None
    for i in range(1, len(omegas)):
        if mags[i] <= level:
            lo, v_lo = float(omegas[i - 1]), complex(values[i - 1])
            hi, v_hi = float(omegas[i]), complex(values[i])
            break
    if hi is None:
        upper = _upper_bracket(factors, omegas, values, level)
        if upper is None:
            return Crossing(level=level, reason="no_crossing_above")
        lo, v_lo = float(omegas[-1]), complex(values[-1])
        hi, v_hi = upper
    best_omega, best_value, resolution = hi, v_hi, None
    steps = 0
    while True:
        mid = math.sqrt(lo * hi) if lo > 0 else (lo + hi) / 2
        if not lo < mid < hi:
            break
        value, err = product_at(factors, mid)
        steps += 1
        best_omega, best_value, resolution = mid, value, err
        diff = abs(value) - level
        if abs(diff) <= err:
            break
        if diff > 0:
            lo, v_lo = mid, value
        else:
            hi, v_hi = mid, value
    return Crossing(
        level=level, omega=best_omega, value=best_value, lo=lo, hi=hi, steps=steps, resolution=resolution,
    )
