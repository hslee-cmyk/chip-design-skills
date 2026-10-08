"""`sizing/input_window.py` (U4) -- 입력 공통모드 y_icm 의 포화 창 (사용자 결정 J-E 2026-10-08, 설계 41 §4.6 '입력 DC 정책' SP-2 (c),
40 §11 'J 추가 범위' U4, 확인 행 D-J5, CONTRACT 14.6).

설계 문구: 입력 DC 가 대기인 회로는 입력 공통모드를 W4 자유 변수 y_icm 으로 두고, 범위는 입력 창 [Vin,min, Vin,max] ∩ [rail_lo,
rail_hi], 경계는 봉인 시점 값이며 tol 을 포함한다. 입력 DC 가 선언된 회로는 그 값을 쓴다.

oracle:
- (a) `saturation_window` 단위: 선형 writer 식(g_n = Σ c·V + 상수)이면 노드가 x 를 따라 움직이는 율 s = dV/dx 는 선형 연립의 해이고
  VDS 가 x 의 1차 함수라 창이 정확하다 -- 기대값은 numpy.linalg.solve(다른 방법 (b))와 닫힌 식 x ≥ x0 − slack/a.
- (a)+(b) 커널 통합: 순환 follower toy(MA nmos (y, x, gnd) 가 x 를, MB nmos (x, in, y, b = y) 가 y 를 쓴다; in = 입력 DC 대기 포트)를
  r4 닫힌 식으로 **독립 풀이**(bisection)해 V(in) 마다 두 소자의 포화 여유 VDS − VDSAT − tol_VDsat 을 재고, 여유 = 0 인 V(in) 을
  다시 bisection 으로 찾은 정확한 창 [lo*, hi*] 와 대조한다. VDSAT·tol_VDsat 은 conftest `r4_vdsat_at`·`r4_tol_vdsat`(npz 열 직접).
- 피검 함수로 기대값을 만들지 않는다.
"""
import math
import random
import time

import numpy as np
import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.sizing import DC_KEY, INPUT_GROUP_KEY, size_and_seal
from gmid_engine.sizing.input_window import saturation_window

from .conftest import (R4_L, build_ctx, detail, free_currents, mos, node_voltages, r4_ln_idu, r4_tol_vdsat,
                       r4_vdsat_at, r4_vgs_of, topo, two)

# ===========================================================================
# 단위: saturation_window(unknown, root, values, gradient, rows) -> (lo, hi) | None
# ===========================================================================


def _linear_gradient(coef, const):
    """coef = {노드: {의존 노드: 계수}}, g_n = Σ coef·V + const[n]."""
    def gradient(net, V):
        c = coef[net]
        return sum(k * V[j] for j, k in c.items()) + const[net], dict(c)
    return gradient


def test_hand_linear_system():
    """g_a = 0.5·V(x) + 0.25·V(b), g_b = 0.5·V(a) -> s_a = 4/7, s_b = 2/7(손계산). 행 (a, gnd, +1, 0.2): VDS = V(a) 율 +4/7 ->
    x ≥ 1 − 0.2·7/4 = 0.65. 행 (vdd, a, +1, 0.3): 율 −4/7 -> x ≤ 1 + 0.3·7/4 = 1.525. 행 (vdd, gnd): 율 0 -> 제약 아님."""
    grad = _linear_gradient({"a": {"x": 0.5, "b": 0.25}, "b": {"a": 0.5}}, {"a": 0.0, "b": 0.0})
    vals = {"x": 1.0, "a": 4 / 7, "b": 2 / 7, "gnd": 0.0, "vdd": 1.8}
    unk = ("a", "b", "x")
    assert saturation_window(unk, "x", vals, grad, ()) == (-math.inf, math.inf)
    lo, hi = saturation_window(unk, "x", vals, grad, (("a", "gnd", 1.0, 0.2), ("vdd", "a", 1.0, 0.3),
                                                      ("vdd", "gnd", 1.0, 0.1)))
    assert abs(lo - 0.65) <= 1e-12 and abs(hi - 1.525) <= 1e-12
    # 부호 −1 (pmos 방향): VDS = −(V(a) − V(gnd)) 율 −4/7 -> 위쪽 경계 x ≤ 1 + 0.2·7/4
    lo, hi = saturation_window(unk, "x", vals, grad, (("a", "gnd", -1.0, 0.2),))
    assert lo == -math.inf and abs(hi - 1.35) <= 1e-12
    # 이미 위반인 행(slack < 0): 경계가 x0 를 넘어간다(x0 가 창 밖)
    lo, _ = saturation_window(unk, "x", vals, grad, (("a", "gnd", 1.0, -0.1),))
    assert abs(lo - (1.0 + 0.1 * 7 / 4)) <= 1e-12


@pytest.mark.parametrize("seed", range(6))
def test_random_linear_systems_against_numpy(seed):
    """무작위 선형 writer 식(대각 우세라 연립 정칙) n = 2..6 노드, 무작위 행: 기대 s = (I − G)⁻¹ G_x(numpy.linalg.solve),
    기대 창 = 닫힌 식. 상대 1e-9."""
    rng = random.Random(seed)
    n = rng.randint(2, 6)
    nodes = ["n%d" % i for i in range(n)]
    coef, const = {}, {}
    for a in nodes:
        row = {b: rng.uniform(-0.4, 0.4) / n for b in nodes if b != a and rng.random() < 0.7}
        row["x"] = rng.uniform(-1.0, 1.0)
        coef[a], const[a] = row, rng.uniform(-0.2, 0.2)
    G = np.array([[coef[a].get(b, 0.0) for b in nodes] for a in nodes])
    gx = np.array([coef[a]["x"] for a in nodes])
    s = dict(zip(nodes, np.linalg.solve(np.eye(n) - G, gx)))
    s["x"], s["gnd"] = 1.0, 0.0
    x0 = 0.7
    vals = {"gnd": 0.0, "x": x0}
    vals.update(zip(nodes, np.linalg.solve(np.eye(n) - G, gx * x0 + np.array([const[a] for a in nodes]))))
    rows = []
    for _ in range(rng.randint(1, 6)):
        d, src = rng.sample(nodes + ["gnd", "x"], 2)
        rows.append((d, src, rng.choice((1.0, -1.0)), rng.uniform(0.0, 0.3)))
    lo_e, hi_e = -math.inf, math.inf
    for d, src, sg, slack in rows:
        a = sg * (s[d] - s[src])
        if abs(a) <= 1e-12:
            continue
        if a > 0:
            lo_e = max(lo_e, x0 - slack / a)
        else:
            hi_e = min(hi_e, x0 + slack / -a)
    lo, hi = saturation_window(tuple(sorted(nodes + ["x"])), "x", vals, _linear_gradient(coef, const), tuple(rows))
    for got, exp in ((lo, lo_e), (hi, hi_e)):
        assert (math.isinf(got) and got == exp) or abs(got - exp) <= 1e-9 * max(1.0, abs(exp)), (got, exp)


def test_singular_system_is_none():
    """V(a) = V(b), V(b) = V(a) -> (I − G) 특이 -> None(CONTRACT 14.6 '(1)이 풀리지 않으면 종래 사상')."""
    grad = _linear_gradient({"a": {"b": 1.0}, "b": {"a": 1.0}}, {"a": 0.0, "b": 0.0})
    vals = {"x": 1.0, "a": 0.5, "b": 0.5, "gnd": 0.0}
    assert saturation_window(("a", "b", "x"), "x", vals, grad, (("a", "gnd", 1.0, 0.2),)) is None


def test_gradient_outside_domain_is_none():
    def grad(net, V):
        raise SealViolationError(devices=(), margin=None, detail={"reason": "lut_query_failed"})
    vals = {"x": 1.0, "a": 0.5, "gnd": 0.0}
    assert saturation_window(("a", "x"), "x", vals, grad, (("a", "gnd", 1.0, 0.2),)) is None


# ===========================================================================
# 커널 통합: 순환 follower toy (입력 DC 대기)
# ===========================================================================

TOL = r4_tol_vdsat("nmos")


def _doc():
    net = [mos("MA", "nmos", "y", "x", "gnd", "gnd"), mos("MB", "nmos", "x", "in", "y", "y")]
    src = [two("IX", "current_source", "vdd", "x"), two("IY", "current_source", "vdd", "y")]
    return topo("u4_icm_follower", net, {"in": ("input", "x"), "y": ("output", "y")}, sources=src)


@pytest.fixture(scope="module")
def pend(tmp_path_factory, r4_access):
    ctx = build_ctx(tmp_path_factory.mktemp("icm_pend"), _doc(), r4_access)[2]
    w = dict(ctx.base.column("node", "dc_writer"))["in"]
    assert w.relation == "free_window" and w.y_key == INPUT_GROUP_KEY            # 전제: in = 입력 묶음 W4 뿌리
    return ctx


def _theta(ctx, vgs_a, vgs_b, y=None):
    th = {("L", "MA"): 1e-6, ("L", "MB"): 1e-6, ("ln_idu", "MA"): r4_ln_idu("nmos", vgs_a, 0.3, 0.0),
          ("ln_idu", "MB"): r4_ln_idu("nmos", vgs_b, 0.3, 0.0)}
    if y is not None:
        th[("y", INPUT_GROUP_KEY)] = y
    th.update(free_currents(ctx, {"MA": 1e-5, "MB": 1e-5, "IX": 1e-5, "IY": 1e-5}))
    assert set(th) == set(ctx.schema.components)
    return th


def _bisect(f, lo, hi, n=200):
    flo = f(lo)
    assert (flo > 0) != (f(hi) > 0), "근을 끼지 않은 구간"
    for _ in range(n):
        mid = 0.5 * (lo + hi)
        fm = f(mid)
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return 0.5 * (lo + hi)


class Follower:
    """독립 풀이: V(x) = VGS_A(좌표 Ta, VDS = V(y)), V(y) = V(in) − VGS_B(좌표 Tb, VDS = V(x) − V(y), VSB 0)."""

    def __init__(self, vgs_a, vgs_b):
        self.ta = r4_ln_idu("nmos", vgs_a, 0.3, 0.0)
        self.tb = r4_ln_idu("nmos", vgs_b, 0.3, 0.0)

    def solve(self, vin):
        def g(y):
            x = r4_vgs_of("nmos", self.ta, y, 0.0)
            return vin - r4_vgs_of("nmos", self.tb, x - y, 0.0) - y
        y = _bisect(g, 1e-9, 1.2)
        x = r4_vgs_of("nmos", self.ta, y, 0.0)
        vgb = r4_vgs_of("nmos", self.tb, x - y, 0.0)
        slack_a = y - r4_vdsat_at("nmos", R4_L[0], x, 0.0) - TOL
        slack_b = (x - y) - r4_vdsat_at("nmos", R4_L[0], vgb, 0.0) - TOL
        return x, y, slack_a, slack_b

    def window(self, guess):
        """정확한 창: slack_A(vin) = 0 (아래 끝), slack_B(vin) = 0 (위 끝). guess = 창 안의 V(in)."""
        assert min(self.solve(guess)[2:]) > 0
        lo = _bisect(lambda v: self.solve(v)[2], guess - 0.3, guess)
        hi = _bisect(lambda v: self.solve(v)[3], guess, guess + 0.3)
        return lo, hi


def _window(ev):
    return dict(ev.snapshot.column("node", "dc_window"))["in"]


def _tol_v(ev):
    return max(v for _, v in ev.snapshot.column("device", "dc_tol_v"))


def test_follower_oracle_window():
    """전제(피검 아님): VGS 0.9/0.3 구성의 정확한 창 ≈ [0.790, 1.035] -- 레일 중앙 0.9 V 를 포함하고, 옛 사상(V(in) = y·1.8)의
    y = 0.1(0.18 V)·0.9(1.62 V)는 창 밖."""
    lo, hi = Follower(0.9, 0.3).window(0.9)
    assert 0.78 < lo < 0.80 and 1.03 < hi < 1.04
    assert not lo <= 0.18 <= hi and not lo <= 1.62 <= hi


@pytest.mark.parametrize("y", [0.02, 0.25, 0.5, 0.75, 0.98])
def test_interior_y_maps_into_saturation_window(pend, y):
    """J-E: 창 안 y -> 봉인(모든 MOS 포화). V(in) = lo + y·(hi − lo)(기록된 창), V(in) 은 정확한 창 안. 기록된 창의 끝은 정확한
    창 끝과 tol_V 안에서 같다(경계는 봉인 시점 값 -- 해상도 = 그 점의 tol_V)."""
    f = Follower(0.9, 0.3)
    lo_e, hi_e = f.window(0.9)
    ev = size_and_seal(pend, _theta(pend, 0.9, 0.3, y))
    assert ev.sealed is not None
    w = _window(ev)
    vin = node_voltages(ev.snapshot)["in"]
    assert abs(vin - (w.lo + y * (w.hi - w.lo))) <= 1e-12
    assert lo_e <= vin <= hi_e
    tv = _tol_v(ev)
    assert abs(w.lo - lo_e) <= tv and abs(w.hi - hi_e) <= tv


@pytest.mark.parametrize("y", [0.0, 1.0])
def test_window_ends_are_saturated(pend, y):
    """설계 41 §4.6: y_icm 범위 = 입력 창이고 '경계는 봉인 시점 값이며 tol 을 포함한다' -> θ 정의역의 끝 y = 0·1 도 창 안이라
    포화 여유 ≥ 0(봉인 7 pass). 정확한 창 끝에서의 독립 풀이 여유는 0(전제)."""
    f = Follower(0.9, 0.3)
    lo_e, hi_e = f.window(0.9)
    assert abs(f.solve(lo_e)[2]) <= 1e-9 and abs(f.solve(hi_e)[3]) <= 1e-9            # 전제
    ev = size_and_seal(pend, _theta(pend, 0.9, 0.3, y))
    assert ev.sealed is not None


def test_window_found_when_rail_midpoint_is_outside(pend):
    """VGS 0.6/0.3 구성: 정확한 창 ≈ [0.604, 0.738](독립 풀이, 비어 있지 않음)이고 레일 중앙 0.9 V 는 창 밖·풀이 불가(y 의 1변수
    구간에 근 없음). 설계는 '범위 = 입력 창' 이므로 y = 0.5 는 창 안 점으로 봉인되어야 한다(선언 입력 DC 0.67 V 로 같은 θ 가 봉인됨
    -- 아래 전제). CONTRACT 14.6 의 '(1)이 풀리지 않으면 종래 사상(레일 범위)' 은 이 경우 창을 찾지 못한다."""
    f = Follower(0.6, 0.3)
    lo_e, hi_e = f.window(0.67)
    assert 0.60 < lo_e < 0.61 and 0.73 < hi_e < 0.74
    ev = size_and_seal(pend, _theta(pend, 0.6, 0.3, 0.5))
    assert ev.sealed is not None
    assert lo_e <= node_voltages(ev.snapshot)["in"] <= hi_e


def test_declared_input_dc_same_theta_seals(tmp_path, r4_access):
    """위 test 의 전제: 같은 소자 좌표로 입력 DC 0.67 V 를 선언하면 봉인된다(창이 실재)."""
    ctx = build_ctx(tmp_path, _doc(), r4_access, input_dc_v=0.67)[2]
    assert dict(ctx.base.column("node", "dc_writer"))["in"].relation == "input_dc"
    ev = size_and_seal(ctx, _theta(ctx, 0.6, 0.3))
    assert ev.sealed is not None and node_voltages(ev.snapshot)["in"] == 0.67
    assert "in" not in dict(ev.snapshot.column("node", "dc_window"))           # 선언 입력 DC 는 창 사상이 없다


def test_empty_window_rejected(pend):
    """VGS 0.5/0.6: slack_A + slack_B = V(x) − VDSAT_A − VDSAT_B − 2·tol 은 V(in) 에 거의 무관(V(x) 는 VDS(MA) 의 LAM 항으로만
    움직임)하고 음수다(독립 풀이로 V(y) > 0 인 0.7..1.3 V 격자 확인, 손계산 ≈ 0.5 − 0.25 − 0.3025 − 0.002) -> 창이 비었다 ->
    SealViolationError(empty_window, 봉인 7 항목, 후보 실패)."""
    f = Follower(0.5, 0.6)
    assert all(sum(f.solve(0.7 + 0.03 * i)[2:]) < -0.05 for i in range(21))            # 전제
    for y in (0.0, 0.5, 1.0):
        with pytest.raises(SealViolationError) as ei:
            size_and_seal(pend, _theta(pend, 0.5, 0.6, y))
        d = detail(ei.value)
        assert d["reason"] == "empty_window" and d["item"] == 7 and d["node"] == "in"


def test_repeat_identical(pend):
    a = size_and_seal(pend, _theta(pend, 0.9, 0.3, 0.3))
    b = size_and_seal(pend, _theta(pend, 0.9, 0.3, 0.3))
    assert a.snapshot.fp == b.snapshot.fp and _window(a) == _window(b)
