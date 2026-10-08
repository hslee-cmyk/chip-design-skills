"""`bracket_root(f, lo, hi, tol) -> (x | None, f_lo, f_hi)` -- CONTRACT 5.6c [r9] (사용자 승인 2026-10-08, 성능 항목 1).

기준은 `gmid_engine/sizing/CONTRACT.md` 5.6c 문장만 쓴다(`bracket_root.py` 소스는 열람하지 않았다). 계약에서 읽은 관찰 가능한 약속:
  (1) f 는 끝점 2회를 먼저 부른다. f(lo) == 0 이면 lo, f(hi) == 0 이면 hi. 끝점 부호가 같으면 (None, f_lo, f_hi) -- 이때 f 는 끝점마다
      정확히 1회(중간 점 평가 없음).
  (2) 수렴 판정 = bisection 과 같은 보증: 반환 x 는 부호가 바뀌는 구간의 한 끝이고 그 구간 폭 ≤ tol/2. 그래서
      (a) 평가한 점 중 f(x)·f(c) ≤ 0 이고 |c − x| ≤ tol/2 인 c 가 있다(x 자신도 평가한 점이다 -- 구간 끝은 평가로만 안다),
      (b) 부호가 바뀌는 점(근·부호 있는 불연속)이 x 에서 tol/2 안에 있다(단조 f 면 참 근과의 거리 ≤ tol/2),
      (c) 같은 tol 의 bisection(마지막 구간 폭 ≤ tol 의 가운데)과 서로 tol 이내(단조 f).
  (3) 평가 수(끝점 2회 포함) ≤ 2·k_max(hi − lo, tol) + 6, k_max = ceil(log2(width/tol))(width ≤ tol 이면 1, CONTRACT 5.6).
  (4) f 값은 실수 또는 ±inf(부호만 주는 정의역 밖 값) -- 끝점·내부 어디서든.

oracle 종류(00-common N0.4):
  * (a) 구성으로 정답이 정해진 합성 입력: 근·부호 바뀌는 점을 test 가 정해 함수를 만든다(1차식, 근을 정한 다항식 곱, sin, 계단·±inf
    계단, 근 위치를 정한 tanh 합). 기대값 = 그 점들과 계약 부등식 (2)(3).
  * (b) 다른 방법: 이 파일의 독립 bisection `ref_bisect`(CONTRACT 5.6b 문장 그대로 -- `bisect_root` 는 생산 호출부가 없어 지워질
    것이라(사용자 승인 성능 항목 1) 엔진 것을 쓰지 않고 test 쪽 기준 구현으로 옮겼다)와 근을 정하지 못한 단조 합성 함수의 근
    (`fine_root`: 부동소수 구간이 더 줄지 않을 때까지 이분).
  * `ref_bisect` 자체는 손계산(옛 test_bisect_root 의 3회 손 예)과 오차 상계로 먼저 검증한다(기준 구현의 기준).
피검 함수(`bracket_root`)로 기대값을 만들지 않는다.
"""
import math
import random

import pytest

from gmid_engine.sizing import bracket_root

EPS = 2.220446049250313e-16          # IEEE-754 double 기계 엡실론(2^-52) -- 계약 '부동소수 해상도 2·eps·|x|' 의 eps


class Counted:
    """f 를 감싸 호출 인자를 순서대로 기록한다(평가 수·평가한 점)."""

    def __init__(self, f):
        self.f, self.args, self.vals = f, [], []

    def __call__(self, x):
        v = self.f(x)
        self.args.append(x)
        self.vals.append(v)
        return v

    @property
    def n(self):
        return len(self.args)


def kmax_ref(width, tol):
    """CONTRACT 5.6 문장 그대로(독립 구현): ceil(log2(width/tol)), width ≤ tol 이면 1."""
    return 1 if width <= tol else math.ceil(math.log2(width / tol))


def ref_bisect(f, lo, hi, n):
    """CONTRACT 5.6b 문장 그대로의 독립 bisection: 끝점 0 이면 그 끝, 부호 같으면 None, 아니면 n 번 반으로 줄이며(가운데 값 0 이면
    그 점) 마지막 구간의 가운데."""
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


def fine_root(f, lo, hi):
    """단조 f 의 근을 부동소수 구간이 더 줄지 않을 때까지 이분(oracle (b)). 반환 = 마지막 구간의 가운데(오차 ≤ ulp 수준)."""
    flo = f(lo)
    for _ in range(2000):
        m = 0.5 * (lo + hi)
        if m <= lo or m >= hi:
            break
        fm = f(m)
        if fm == 0:
            return m
        if (fm > 0) == (flo > 0):
            lo, flo = m, fm
        else:
            hi = m
    return 0.5 * (lo + hi)


def opposite(a, b):
    """f(x)·f(c) ≤ 0 -- ±inf 도 부호로(0·inf 의 nan 을 피해 직접 판정)."""
    return a == 0 or b == 0 or (a > 0) != (b > 0)


def slack(lo, hi):
    """계약의 부동소수 해상도(2·eps·|x|) 만큼의 여유 -- tol 이 아니라 표현 한계."""
    return 4.0 * EPS * max(abs(lo), abs(hi), 1.0)


def check_contract(f, lo, hi, tol, sign_changes=None, monotone=False):
    """계약 (1)~(3) 을 한 번에 검사한다. sign_changes = 구성으로 아는 부호 바뀌는 점들(oracle (a)), None 이면 (b) 를 건너뛴다.
    반환 (x, cf)."""
    cf = Counted(f)
    x, f_lo, f_hi = bracket_root(cf, lo, hi, tol)
    exp_lo, exp_hi = f(lo), f(hi)
    # (1) 끝점 2회 먼저, 반환한 끝점 값은 그 평가 값 그대로
    assert set(cf.args[:2]) == {lo, hi}
    assert (f_lo, f_hi) == (exp_lo, exp_hi)
    # (3) 평가 수 상계
    assert cf.n <= 2 * kmax_ref(hi - lo, tol) + 6, (cf.n, kmax_ref(hi - lo, tol))
    if exp_lo != 0 and exp_hi != 0 and (exp_lo > 0) == (exp_hi > 0):
        assert x is None and cf.n == 2
        return x, cf
    if exp_lo == 0:
        assert x == lo
        return x, cf
    if exp_hi == 0:
        assert x == hi
        return x, cf
    assert x is not None and lo <= x <= hi
    # (2a) x 는 평가한 점이고, 평가한 점 중 부호가 반대(또는 0)인 c 가 tol/2 안에 있다
    assert x in cf.args
    fx = cf.vals[cf.args.index(x)]
    s = slack(lo, hi)
    assert fx == 0 or any(opposite(fx, v) and abs(c - x) <= tol / 2 + s for c, v in zip(cf.args, cf.vals)), \
        "평가한 점 중 tol/2 안의 부호 반대 점이 없다: x=%r f(x)=%r" % (x, fx)
    # (2b) 구성으로 아는 부호 바뀌는 점이 tol/2 안
    if sign_changes is not None:
        assert min(abs(x - r) for r in sign_changes) <= tol / 2 + s
    # (2c) 단조면 같은 tol 의 bisection 과 tol 이내
    if monotone:
        xb = ref_bisect(f, lo, hi, kmax_ref(hi - lo, tol))
        assert abs(x - xb) <= tol + s
    return x, cf


# ===========================================================================
# 0. 기준 구현 ref_bisect 자체의 검증(옛 test_bisect_root 에서 옮긴 손계산 -- 기준의 기준)
# ===========================================================================

def test_reference_bisection_hand_three_iterations():
    # [0,1] -> 0.5(+) -> [0,0.5] -> 0.25(−) -> [0.25,0.5] -> 0.375(+) -> [0.25,0.375] -> 가운데 0.3125 (손계산)
    assert ref_bisect(lambda t: t - 0.3, 0.0, 1.0, 3) == 0.3125


@pytest.mark.parametrize("n", [0, 1, 5, 20, 52])
@pytest.mark.parametrize("root", [0.123, 0.77, 1e-9])
def test_reference_bisection_error_bound(n, root):
    """마지막 구간 폭 2^-n 의 가운데 -> 근과 2^-(n+1) 이내(손으로 아는 근)."""
    x = ref_bisect(lambda t: math.tanh(t - root), 0.0, 1.0, n)
    assert abs(x - root) <= 0.5 ** (n + 1) + 1e-15


def test_reference_bisection_endpoints_and_same_sign():
    assert ref_bisect(lambda t: t, 0.0, 1.0, 10) == 0.0
    assert ref_bisect(lambda t: t - 1.0, 0.0, 1.0, 10) == 1.0
    assert ref_bisect(lambda t: t - 0.5, 0.0, 1.0, 10) == 0.5          # 가운데 값 0 이면 그 점
    assert ref_bisect(lambda t: t + 1.0, 0.0, 1.0, 10) is None


# ===========================================================================
# 1. 손 사례 (oracle (a): 근을 정한 합성 입력)
# ===========================================================================

@pytest.mark.parametrize("tol", [2.0 ** -10, 1e-3, 1e-7, 1e-12])
def test_linear_root(tol):
    x, _ = check_contract(lambda t: t - 0.3, 0.0, 1.0, tol, sign_changes=(0.3,), monotone=True)
    assert abs(x - 0.3) <= tol / 2 + slack(0.0, 1.0)


@pytest.mark.parametrize("tol", [1e-2, 1e-6, 1e-10])
def test_decreasing_function(tol):
    _, cf = check_contract(lambda t: 0.4 - t, 0.0, 1.0, tol, sign_changes=(0.4,), monotone=True)
    assert cf.vals[cf.args.index(0.0)] > 0 > cf.vals[cf.args.index(1.0)]


def test_endpoint_lo_exact_zero_returns_lo():
    x, cf = check_contract(lambda t: t, 0.0, 1.0, 1e-6)
    assert x == 0.0


def test_endpoint_hi_exact_zero_returns_hi():
    x, cf = check_contract(lambda t: t - 1.0, 0.0, 1.0, 1e-6)
    assert x == 1.0


@pytest.mark.parametrize("f,lo,hi,exp", [
    (lambda t: t + 1.0, 0.0, 1.0, (1.0, 2.0)),                  # 둘 다 양
    (lambda t: -t - 1.0, 0.0, 1.0, (-1.0, -2.0)),               # 둘 다 음
    (lambda t: math.inf, 0.0, 1.0, (math.inf, math.inf)),       # 둘 다 +inf
    (lambda t: -math.inf, -3.0, 2.0, (-math.inf, -math.inf)),   # 둘 다 −inf
    (lambda t: (t - 0.5) ** 2 + 1e-3, 0.0, 1.0, (0.251, 0.251)),  # 안쪽에 근 없음(극소 > 0)
    (lambda t: (t - 0.3) * (t - 0.7), 0.0, 1.0, (0.21, 0.21)),  # 안쪽에 근 둘(끝 부호 같음 -> 근 없음으로 보고)
])
def test_same_sign_endpoints_none_and_two_calls(f, lo, hi, exp):
    cf = Counted(f)
    x, f_lo, f_hi = bracket_root(cf, lo, hi, 1e-9)
    assert x is None
    assert f_lo == pytest.approx(exp[0], rel=1e-12) and f_hi == pytest.approx(exp[1], rel=1e-12)
    assert cf.n == 2 and set(cf.args) == {lo, hi}                 # 끝점마다 정확히 1회


def test_infinite_endpoints_finite_interior():
    """g 가 정의역 밖이면 ±inf 로 부호만 준다(CONTRACT 5.4) -- 끝이 −inf/+inf 여도 유한한 안쪽 근 0.6 을 찾는다."""
    def f(t):
        if t < 0.2:
            return -math.inf
        if t > 0.9:
            return math.inf
        return t - 0.6
    for tol in (1e-3, 1e-9):
        x, _ = check_contract(f, 0.0, 1.0, tol, sign_changes=(0.6,), monotone=True)
        assert abs(x - 0.6) <= tol / 2 + slack(0.0, 1.0)


@pytest.mark.parametrize("d", [0.6, 0.123456789, 0.999])
def test_interior_infinite_jump_sign_change(d):
    """안쪽에서 −유한 -> +inf 로 부호가 바뀌는 불연속(근 대신 정의역 경계): 부호 바뀌는 점 d 와 tol/2 이내."""
    def f(t):
        return math.inf if t > d else -0.5
    check_contract(f, 0.0, 1.0, 1e-8, sign_changes=(d,), monotone=True)


@pytest.mark.parametrize("d", [0.25, 0.7071])
def test_pure_inf_step(d):
    """값이 ±inf 뿐인 계단(보간 불가 -> 이분만): 부호 바뀌는 점 d 와 tol/2 이내, 평가 수 상계."""
    def f(t):
        return math.inf if t >= d else -math.inf
    check_contract(f, 0.0, 1.0, 1e-9, sign_changes=(d,), monotone=True)


def test_root_hugging_endpoint():
    """근이 끝점에 tol 보다 훨씬 가깝다(보간 걸음이 tol/4 보다 작아지는 경우 -- 계약 '반대편 확인')."""
    for r, tol in ((1e-9, 1e-3), (1.0 - 1e-9, 1e-3), (1e-15, 1e-6)):
        check_contract(lambda t, r=r: t - r, 0.0, 1.0, tol, sign_changes=(r,), monotone=True)


@pytest.mark.parametrize("p", [3, 5, 9])
def test_multiple_root_slow_for_interpolation(p):
    """홀수 중근 (x − r)^p: 보간이 느린 경우에도 평가 수 상계(보간이 k_max 를 넘으면 이분)."""
    r = 0.37
    check_contract(lambda t: (t - r) ** p, 0.0, 1.0, 1e-10, sign_changes=(r,), monotone=True)


def test_width_not_larger_than_tol():
    """hi − lo ≤ tol 이면 k_max = 1 -> 평가 수 ≤ 8, 근과 tol/2 이내."""
    check_contract(lambda t: t - 3e-5, 0.0, 1e-4, 1e-3, sign_changes=(3e-5,), monotone=True)
    check_contract(lambda t: t - 3e-5, 0.0, 1e-4, 1e-4, sign_changes=(3e-5,), monotone=True)


@pytest.mark.parametrize("lo,hi,r,tol", [(-1e3, 1e3, 12.5, 1e-9), (-0.45, 1.8, -0.2, 8.5e-4), (0.0375, 1.8, 1.79, 9e-4)])
def test_wide_and_offset_intervals(lo, hi, r, tol):
    check_contract(lambda t: math.tanh(3.0 * (t - r)), lo, hi, tol, sign_changes=(r,), monotone=True)


# ===========================================================================
# 2. 무작위 성질 test (oracle (a) 구성 근 + (b) 독립 bisection·fine_root)
# ===========================================================================

def _monotone(rng):
    """엄격 증가(또는 음수 배로 감소) 합성 함수 -- 근 위치는 구성으로 정하지 않고 fine_root 로(oracle (b))."""
    a0 = rng.choice((0.0, rng.uniform(0.01, 3.0)))
    terms = [(rng.uniform(0.1, 5.0), 10 ** rng.uniform(-1, 3), rng.uniform(-0.5, 1.5)) for _ in range(rng.randint(1, 4))]
    shift = rng.uniform(-1.0, 1.0)
    sgn = rng.choice((1.0, -1.0))

    def f(t):
        return sgn * (a0 * t + sum(a * math.tanh(b * (t - c)) for a, b, c in terms) - shift)
    return f


def _with_inf(rng, f, lo, hi, root):
    """근 바깥 양쪽을 ±inf(f 의 부호 그대로)로 덮는다 -- 정의역 밖 부호 값(CONTRACT 5.4)."""
    d1 = rng.uniform(lo, root)
    d2 = rng.uniform(root, hi)
    s_lo, s_hi = math.copysign(1.0, f(lo)), math.copysign(1.0, f(hi))

    def g(t):
        if t < d1:
            return s_lo * math.inf
        if t > d2:
            return s_hi * math.inf
        return f(t)
    return g


def _tol(rng, width):
    return width * 10 ** rng.uniform(-13, -0.5)


def test_property_monotone_random():
    rng = random.Random(20261008)
    n_root = 0
    for i in range(600):
        f = _monotone(rng)
        lo = rng.uniform(-1.0, 0.5)
        hi = lo + 10 ** rng.uniform(-3, 1)
        tol = _tol(rng, hi - lo)
        flo, fhi = f(lo), f(hi)
        if (flo > 0) == (fhi > 0):
            check_contract(f, lo, hi, tol)                         # 근 없음 -> None·2회
            continue
        n_root += 1
        r = fine_root(f, lo, hi)
        if i % 3 == 0:
            f = _with_inf(rng, f, lo, hi, r)
        check_contract(f, lo, hi, tol, sign_changes=(r,), monotone=True)
    assert n_root >= 100                                           # 전제(생성기 성질, seed 고정 실측 129): 근이 있는 사례가 충분히 섞였다


def test_property_polynomial_known_roots():
    """근을 정한 다항식 곱 s·Π(x − r_i)·(1 + x²)(비단조, 근 여러 개) -- 끝 부호가 다르면 tol/2 안에 구성 근 하나."""
    rng = random.Random(1008)
    n_root = 0
    for _ in range(600):
        lo = rng.uniform(-2.0, 0.0)
        hi = lo + rng.uniform(0.1, 4.0)
        roots = [rng.uniform(lo - 0.5, hi + 0.5) for _ in range(rng.randint(1, 6))]
        s = rng.choice((1.0, -1.0)) * 10 ** rng.uniform(-3, 3)

        def f(t, roots=roots, s=s):
            v = s * (1.0 + t * t)
            for r in roots:
                v *= (t - r)
            return v
        tol = _tol(rng, hi - lo)
        inside = [r for r in roots if lo <= r <= hi]
        x, _ = check_contract(f, lo, hi, tol, sign_changes=inside or None)
        n_root += x is not None
    assert n_root >= 200


def test_property_sine_known_roots():
    """sin(w·x + φ) -- 근 = (kπ − φ)/w(구성), 끝 부호가 다르면 tol/2 안에 그중 하나."""
    rng = random.Random(77)
    n_root = 0
    for _ in range(400):
        w = rng.uniform(0.5, 40.0)
        phi = rng.uniform(-math.pi, math.pi)
        lo = rng.uniform(-1.0, 1.0)
        hi = lo + rng.uniform(0.05, 3.0)
        ks = range(math.floor((w * lo + phi) / math.pi) - 1, math.ceil((w * hi + phi) / math.pi) + 2)
        roots = [(k * math.pi - phi) / w for k in ks]
        tol = _tol(rng, hi - lo)
        x, _ = check_contract(lambda t, w=w, phi=phi: math.sin(w * t + phi), lo, hi, tol,
                              sign_changes=[r for r in roots if lo - tol <= r <= hi + tol])
        n_root += x is not None
    assert n_root >= 100


def test_property_steps_and_inf_jumps():
    """부호 있는 불연속(유한 계단·±inf 계단, 여러 번 바뀜) -- 바뀌는 점을 구성으로 안다."""
    rng = random.Random(4242)
    for _ in range(300):
        lo, hi = 0.0, 1.0
        cuts = sorted(rng.uniform(0.0, 1.0) for _ in range(rng.choice((1, 1, 3))))
        mag = rng.choice((1.0, math.inf, 1e-300))
        s0 = rng.choice((1.0, -1.0))

        def f(t, cuts=cuts, mag=mag, s0=s0):
            k = sum(t >= c for c in cuts)
            return s0 * mag * (1.0 if k % 2 == 0 else -1.0)
        check_contract(f, lo, hi, _tol(rng, 1.0), sign_changes=cuts)


def test_agreement_with_reference_bisection_within_tol():
    """계약 '두 방법의 답은 서로 tol 이내' -- 근을 정한 단조 함수들(oracle (a)+(b))."""
    rng = random.Random(9)
    for _ in range(200):
        r = rng.uniform(0.0, 1.8)
        b = 10 ** rng.uniform(-1, 2)
        f = (lambda t, r=r, b=b: math.atan(b * (t - r)) + 0.1 * (t - r))
        tol = 10 ** rng.uniform(-9, -2)
        x, _, _ = bracket_root(f, 0.0, 1.8, tol)
        xb = ref_bisect(f, 0.0, 1.8, kmax_ref(1.8, tol))
        assert abs(x - xb) <= tol + slack(0.0, 1.8)
        assert abs(x - r) <= tol / 2 + slack(0.0, 1.8) and abs(xb - r) <= tol / 2 + slack(0.0, 1.8)


def test_evaluation_count_far_below_bisection_for_smooth_root():
    """성능 항목 1 의 근거(계약 10.7: 매끈한 1변수 근에서 평가 수가 bisection 보다 적다) -- 상계 외에 매끈한 단근에서는 bisection
    (끝점 2 + k_max)보다 적게 부르는지 본다. 계약은 상계만 약속하므로 이 test 는 매끈한 단근 한 종류에 한정한다."""
    tol = 1e-9
    f = Counted(lambda t: math.exp(t) - 2.0)                     # 근 ln 2, 도함수 ≥ 1
    x, _, _ = bracket_root(f, 0.0, 1.8, tol)
    assert abs(x - math.log(2.0)) <= tol / 2 + slack(0.0, 1.8)
    assert f.n < 2 + kmax_ref(1.8, tol)
