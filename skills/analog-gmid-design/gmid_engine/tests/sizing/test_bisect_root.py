"""`bisect_root(f, lo, hi, iterations) -> (x | None, f_lo, f_hi)` -- CONTRACT 5.6b [r2].

f(lo) == 0 -> lo, f(hi) == 0 -> hi. 부호가 같으면 (None, f_lo, f_hi). 아니면 iterations 번 반으로 줄이며(가운데 값 0 이면 그 점)
마지막 구간 가운데. f 는 끝점 2회 + 반복마다 1회. f 값은 실수 또는 ±inf. 기대값은 손계산과 이 파일의 독립 이분법.
"""
import math

import pytest

from gmid_engine.sizing import bisect_root


class Counted:
    def __init__(self, f):
        self.f, self.n = f, 0

    def __call__(self, x):
        self.n += 1
        return self.f(x)


def ref(f, lo, hi, n):
    flo, fhi = f(lo), f(hi)
    if flo == 0:
        return lo
    if fhi == 0:
        return hi
    if (flo > 0) == (fhi > 0):
        return None
    for _ in range(n):
        m = 0.5 * (lo + hi)
        fm = f(m)
        if fm == 0:
            return m
        if (fm > 0) == (flo > 0):
            lo, flo = m, fm
        else:
            hi = m
    return 0.5 * (lo + hi)


def test_hand_three_iterations():
    f = Counted(lambda x: x - 0.3)
    x, flo, fhi = bisect_root(f, 0.0, 1.0, 3)
    # [0,1] -> 0.5(+) -> [0,0.5] -> 0.25(−) -> [0.25,0.5] -> 0.375(+) -> [0.25,0.375] -> 가운데 0.3125
    assert x == 0.3125
    assert (flo, fhi) == (-0.3, 0.7)
    assert f.n == 2 + 3


@pytest.mark.parametrize("n", [0, 1, 5, 20, 52])
@pytest.mark.parametrize("root", [0.123, 0.77, 1e-9])
def test_matches_reference_and_error_bound(n, root):
    f = Counted(lambda x: math.tanh(x - root))
    x, _, _ = bisect_root(f, 0.0, 1.0, n)
    g = Counted(lambda t: math.tanh(t - root))
    assert x == ref(g, 0.0, 1.0, n)
    assert abs(x - root) <= 0.5 ** (n + 1) + 1e-15
    assert f.n == g.n <= 2 + n               # 가운데 값이 정확히 0 이면 그 반복에서 멈춘다


def test_decreasing_function():
    x, flo, fhi = bisect_root(lambda t: 0.4 - t, 0.0, 1.0, 30)
    assert abs(x - 0.4) <= 2 ** -31 and flo > 0 > fhi


def test_endpoint_roots():
    assert bisect_root(lambda t: t, 0.0, 1.0, 10)[0] == 0.0
    assert bisect_root(lambda t: t - 1.0, 0.0, 1.0, 10)[0] == 1.0


def test_exact_midpoint_root_returned():
    f = Counted(lambda t: t - 0.5)
    assert bisect_root(f, 0.0, 1.0, 10)[0] == 0.5


def test_same_sign_none():
    x, flo, fhi = bisect_root(lambda t: t + 1.0, 0.0, 1.0, 10)
    assert x is None and (flo, fhi) == (1.0, 2.0)
    assert bisect_root(lambda t: -t - 1.0, 0.0, 1.0, 10)[0] is None


def test_infinite_values_have_sign():
    """g 평가가 정의역 밖이면 ±inf 로 부호만 준다 -- 끝이 −inf/+inf 여도 근을 찾는다."""
    def f(t):
        if t < 0.2:
            return -math.inf
        if t > 0.9:
            return math.inf
        return t - 0.6
    x, flo, fhi = bisect_root(f, 0.0, 1.0, 40)
    assert flo == -math.inf and fhi == math.inf
    assert abs(x - 0.6) <= 2 ** -40
    assert bisect_root(lambda t: math.inf, 0.0, 1.0, 5)[0] is None
