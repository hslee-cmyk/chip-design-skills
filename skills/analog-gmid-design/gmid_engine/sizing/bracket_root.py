"""괄호 안 빠른 근 찾기 (Brent 법, 설계 3.4 '1변수 SCC' 의 bisection 을 같은 수렴 판정으로 대체, 계획 N3.6).

진입점: `bracket_root(f, lo, hi, tol) -> (x | None, f_lo, f_hi)`.

`bisect_root` 와 같은 약속이다: f 는 실수 또는 ±inf(조회 정의역 밖이지만 부호가 정해지는 쪽), 끝점 부호가 같으면(어느 쪽도 0 이
아님) (None, f_lo, f_hi), 끝점이 0 이면 그 끝점. 다른 점은 끝점 사이 점을 고르는 방식뿐이다.

* 수렴 판정 = bisection 과 같다: 돌려주는 x 는 부호가 바뀌는 구간 [x, c] 의 한 끝이고 그 폭 ≤ tol/2 -- 곧 근과의 거리
  ≤ tol/2 (bisection 의 마지막 구간 폭 ≤ tol 의 가운데값과 같은 보증). 허용오차를 느슨하게 하지 않는다.
* 점 고르기: 유한한 세 점이 있으면 역 2차 보간(없으면 할선), 그 걸음이 반구간(|c − b|/2) 안이고 전전 걸음의 절반보다 작을 때만 받고 아니면
  이분. f 가 ±inf 인 점이 끝점에 있으면 보간하지 않고 이분(부호만 안다). 보간 걸음이 tol/4 보다 작으면 tol/4 만큼
  구간 안쪽으로 밀어(근 반대편 확인) 구간을 닫는다.
* 상한: 반복이 `k_max(hi − lo, tol)` 를 넘으면 남은 반복은 순수 이분 -> 총 평가 ≤ 2·k_max + 6 (순수 bisection 은 k_max).
  보통 f 가 매끈하고 거의 선형이라 k_max 의 몇 분의 1 이다. 상수 없음(tol/4·tol/2 는 판정식의 분수, 부동소수 해상도는 2·eps·|b|).
"""
import math
import sys

from .k_max import k_max

_EPS = sys.float_info.epsilon


def _is_finite(*values):
    return all(math.isfinite(v) for v in values)


def bracket_root(f, lo, hi, tol):
    f_lo, f_hi = f(lo), f(hi)
    if f_lo == 0:
        return lo, f_lo, f_hi
    if f_hi == 0:
        return hi, f_lo, f_hi
    if (f_lo > 0) == (f_hi > 0):
        return None, f_lo, f_hi
    width = hi - lo
    cap = k_max(width, tol) if width > tol else 1
    a, b, c = lo, hi, hi
    fa, fb, fc = f_lo, f_hi, f_hi
    d = e = b - a
    n = 0
    while True:
        if (fb > 0) == (fc > 0):                      # b·c 가 같은 부호 -> 근을 괄호하는 쪽을 a 로 되돌린다
            c, fc = a, fa
            d = e = b - a
        if abs(fc) < abs(fb):                         # b = 근에 더 가까운(|f| 작은) 점
            a, b, c = b, c, b
            fa, fb, fc = fb, fc, fb
        tol1 = tol / 2 / 2 + 2 * _EPS * abs(b)
        xm = (c - b) / 2
        if abs(xm) <= tol1 or fb == 0:
            return b, f_lo, f_hi
        n += 1
        step_ok = n <= cap and abs(e) >= tol1 and abs(fa) > abs(fb) and _is_finite(fa, fb, fc)
        if step_ok:
            s = fb / fa
            if a == c:                                # 할선
                p, q = 2 * xm * s, 1 - s
            else:                                     # 역 2차 보간
                q, r = fa / fc, fb / fc
                p = s * (2 * xm * q * (q - r) - (b - a) * (r - 1))
                q = (q - 1) * (r - 1) * (s - 1)
            step = -p / q if q != 0 else math.inf     # b 에서 보간 근까지(부호 포함)
            if 2 * abs(step) < abs(e) and abs(step) < abs(xm):
                e, d = d, step
            else:
                d = e = xm
        else:
            d = e = xm
        a, fa = b, fb
        b += d if abs(d) > tol1 else math.copysign(tol1, xm)
        fb = f(b)
