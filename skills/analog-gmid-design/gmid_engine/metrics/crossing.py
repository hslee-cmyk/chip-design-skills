"""|T(jω)| = level 첫 교차 -- 격자 괄호 + log ω 이분 (설계 design_mod1_lut_mod5_mna 3.4 `ugf_ss_hz`·`gbw_ss_hz`).

진입점: `find_crossing`.

1. 격자 위 |T| 에서 |T(0)| > level 이고 처음으로 |T| ≤ level 이 되는 칸을 괄호로 잡는다. |T(0)| ≤ level 이면 교차 없음
   (`dc_not_above_level`, definitional).
2. 격자 끝까지 |T| > level 이면 상단 괄호를 극점·영점 상계로 유도한다: ω > max|p| 에서
   |T(jω)| ≤ |K|·Π(ω + |z|)/Π(ω − |p|) (삼각부등식, K 는 격자 끝점에서 잰 값으로 맞춘 이득). 극점 수 > 영점 수면 상계가
   단조 감소하므로 ω 를 두 배씩 늘려 상계 < level 인 ω 를 찾는다(부동소수 상한까지 -- 넘치면 `crossing_bracket_overflow`).
   극점 수 < 영점 수, 또는 같고 |K| ≥ level 이면 위쪽 교차가 보장되지 않는다(`no_crossing_above`, definitional).
   상계로 잡은 끝점은 실제 풀이로 |T| ≤ level 을 확인한다(어긋나면 `crossing_bound_violated`, numeric).
3. 이분: lo > 0 이면 기하 중점, lo = 0 이면 산술 중점. 정지 = (a) 중점이 끝점과 같은 부동소수(분해능 끝) 또는
   (b) | |T(mid)| − level | ≤ 사후 오차(MNA 풀이로 구별 불가). 정지 상수 없음.
예외를 던지지 않는다 -- 정의 불가는 `Crossing.undefined` 값이다(quantity 는 부르는 쪽이 준 이름).
"""
import math

from ._helpers_product import check_factors, product_at
from .mna_types import Crossing, Undefined


def _absent(level, quantity, code, category, **detail):
    return Crossing(level=level, undefined=Undefined(quantity, code, category, tuple(sorted(detail.items()))))


def _rational_bound(poles, zeros, gain, omega):
    num = math.prod(omega + abs(z) for z in zeros)
    den = math.prod(omega - abs(p) for p in poles)
    return gain * num / den


def _upper_bracket(factors, omegas, values, level, quantity):
    """(ω_hi, T(ω_hi)) 또는 Crossing(정의 불가)."""
    # |s| = 0 근은 뺀다: T(0) 이 유한한(여기 닿았다면 유한) 계에서 원점 극점은 원점 영점과 상쇄된 전하 모드다(용량 전용 노드).
    # 근은 인수 공통 규약 속성(`Factor`: 계 극점·그 행·열 영점, `ProbeFactor`: T 자신의 극점·영점)에서 읽는다.
    poles = tuple(p for f in factors for p in f.poles if p != 0)
    zeros = tuple(z for f in factors for z in f.zeros if z != 0)
    top = float(omegas[-1])
    if len(poles) < len(zeros) or top <= 0:
        return _absent(level, quantity, "no_crossing_above", "definitional", poles=len(poles), zeros=len(zeros))
    s = complex(0, top)
    shape = math.prod(abs(s - z) for z in zeros) / math.prod(abs(s - p) for p in poles)
    gain = abs(values[-1]) / shape
    if len(poles) == len(zeros) and gain >= level:
        return _absent(level, quantity, "no_crossing_above", "definitional", asymptote=gain)
    pole_top = max((abs(p) for p in poles), default=0.0)
    omega = top if top > pole_top else pole_top * 2
    while _rational_bound(poles, zeros, gain, omega) >= level:
        omega *= 2
        if not math.isfinite(omega):
            return _absent(level, quantity, "crossing_bracket_overflow", "numeric")
    value, _, undefined = product_at(factors, omega)
    if undefined:
        return Crossing(level=level, undefined=undefined[0])
    if abs(value) > level:
        return _absent(level, quantity, "crossing_bound_violated", "numeric", omega=omega, magnitude=abs(value))
    return omega, value


def find_crossing(factors, omegas, values, level, quantity):
    """루프 인수 tuple, 공유 격자, 격자 위 T 값, level, 정의 불가 사유에 붙일 양 이름 -> `Crossing`."""
    check_factors(factors)
    level = float(level)
    if not level > 0 or not math.isfinite(level):
        raise ValueError("find_crossing: level 은 양의 유한수여야 한다: %r" % level)
    mags = abs(values)
    if not mags[0] > level:
        return _absent(level, quantity, "dc_not_above_level", "definitional", dc_magnitude=float(mags[0]))
    lo = hi = v_hi = None
    for i in range(1, len(omegas)):
        if mags[i] <= level:
            lo = float(omegas[i - 1])
            hi, v_hi = float(omegas[i]), complex(values[i])
            break
    if hi is None:
        upper = _upper_bracket(factors, omegas, values, level, quantity)
        if isinstance(upper, Crossing):
            return upper
        lo = float(omegas[-1])
        hi, v_hi = upper
    best_omega, best_value, resolution = hi, v_hi, None
    steps = 0
    while True:
        mid = math.sqrt(lo * hi) if lo > 0 else (lo + hi) / 2
        if not lo < mid < hi:
            break
        value, err, undefined = product_at(factors, mid)
        if undefined:
            return Crossing(level=level, undefined=undefined[0])
        steps += 1
        best_omega, best_value, resolution = mid, value, err
        diff = abs(value) - level
        if abs(diff) <= err:
            break
        if diff > 0:
            lo = mid
        else:
            hi = mid
    return Crossing(
        level=level, omega=best_omega, value=best_value, lo=lo, hi=hi, steps=steps, resolution=resolution,
    )
