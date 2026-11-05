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
import sys
import time

import numpy as np
import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.sizing import DC_KEY, size_and_seal
from gmid_engine.sizing.input_window import saturation_window

from .conftest import (R4_L, build_ctx, detail, free_currents, mos, node_voltages, r4_ln_idu,
                       r4_vdsat_at, r4_vgs_of, seal_item, topo, two)
from types import SimpleNamespace

from .conftest import run_blocks
from .conftest import kschema  # [U17 ①-b] graph/kernel 필드 읽기(설계 40 v1.9.1 §2.4.7 KernelContext 행)

# ===========================================================================
# 단위: saturation_window(unknown, root, values, gradient, rows, *, slope=None) -> (dlo, dhi, slope) | None
# [IT-2b 갱신] 반환 창은 x0 = 0 기준 **이동량** [dlo, dhi](옛 절대 창 x0 + 이동량), `root` 는 x 로 움직이는 넷 하나(쌍·묶음 없음, [IT-2c 갱신] interface 20261104-it2c-icm-config 'saturation_window 계약'),
# 행은 5원소 (a, b, sign, slack, kind) -- 창 끝 정의(행마다 slack + sign·(s_a − s_b)·Δ ≥ 0 의 교집합)는 kind 를 쓰지 않는다. (design 41 4.7-3 2·4.7-7)
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
    assert saturation_window(unk, "x", vals, grad, ())[:2] == (-math.inf, math.inf)
    dlo, dhi, slope = saturation_window(unk, "x", vals, grad, (("a", "gnd", 1.0, 0.2, "sat"), ("vdd", "a", 1.0, 0.3, "sat"),
                                                                   ("vdd", "gnd", 1.0, 0.1, "sat")))
    assert abs(dlo - (-0.35)) <= 1e-12 and abs(dhi - 0.525) <= 1e-12                 # 옛 절대 창 [0.65, 1.525] − x0(1.0)
    # 반환 slope = {넷: dV/dx}: 손계산 s_a = 4/7, s_b = 2/7, 뿌리 s_x = 1 (oracle 대조: (손) 위 연립)
    assert abs(slope["a"] - 4 / 7) <= 1e-12 and abs(slope["b"] - 2 / 7) <= 1e-12 and slope["x"] == 1.0
    # 부호 −1 (pmos 방향): VDS = −(V(a) − V(gnd)) 율 −4/7 -> 위쪽 경계 Δ ≤ 0.2·7/4
    dlo, dhi, _ = saturation_window(unk, "x", vals, grad, (("a", "gnd", -1.0, 0.2, "sat"),))
    assert dlo == -math.inf and abs(dhi - 0.35) <= 1e-12
    # 이미 위반인 행(slack < 0): 경계가 0 을 넘어간다(출발점이 창 밖)
    dlo, _, _ = saturation_window(unk, "x", vals, grad, (("a", "gnd", 1.0, -0.1, "sat"),))
    assert abs(dlo - (0.1 * 7 / 4)) <= 1e-12


def test_it2b_sw_kind_is_not_used_for_window_end():
    """oracle 대조: (식) design 41 4.7-7 -- `saturation_window` 는 행의 kind(5번째 원소)를 창 계산에 쓰지 않는다: 같은 (a, b, sign, slack) 에
    kind 만 "sat"/"triode" 로 바꿔도 반환(dlo, dhi, slope)이 같다. 같은 연립은 test_hand_linear_system 의 손계산(s_a = 4/7)."""
    grad = _linear_gradient({"a": {"x": 0.5, "b": 0.25}, "b": {"a": 0.5}}, {"a": 0.0, "b": 0.0})
    vals = {"x": 1.0, "a": 4 / 7, "b": 2 / 7, "gnd": 0.0, "vdd": 1.8}
    unk = ("a", "b", "x")
    sat = saturation_window(unk, "x", vals, grad, (("a", "gnd", 1.0, 0.2, "sat"), ("vdd", "a", 1.0, 0.3, "sat")))
    tri = saturation_window(unk, "x", vals, grad, (("a", "gnd", 1.0, 0.2, "triode"), ("vdd", "a", 1.0, 0.3, "triode")))
    assert sat is not None and tri == sat
    assert abs(sat[0] - (-0.35)) <= 1e-12 and abs(sat[1] - 0.525) <= 1e-12


def test_it2b_sw_given_slope_skips_the_sensitivity_system():
    """oracle 대조: (식) `slope` 를 주면 안의 감도 연립을 풀지 않고 그 감도로 끝만 낸다(KVL 고정 구조). 반환 slope = 받은 값, `gradient` 는 불리지 않는다
    (부르면 AssertionError). 손계산: 행 (a, gnd, +1, 0.2) 율 0.5 - 0 = 0.5 -> Δ ≥ −0.4, 행 (vdd, a, +1, 0.3) 율 −0.5 -> Δ ≤ 0.6."""
    def never(net, V):
        raise AssertionError("slope 를 줬는데 gradient 가 불렸다")
    given = {"x": 1.0, "a": 0.5, "gnd": 0.0, "vdd": 0.0}
    vals = {"x": 1.0, "a": 0.5, "gnd": 0.0, "vdd": 1.8}
    rows = (("a", "gnd", 1.0, 0.2, "sat"), ("vdd", "a", 1.0, 0.3, "sat"))
    dlo, dhi, slope = saturation_window(("a", "x"), "x", vals, never, rows, slope=given)
    assert abs(dlo - (-0.4)) <= 1e-12 and abs(dhi - 0.6) <= 1e-12
    assert slope == given


def test_it2c_sw_root_is_a_single_net():
    """oracle 대조: (손) [IT-2c T-P] `root` 는 넷 하나. g_a = 0.5·V(x) + 0.25·V(b), g_b = 0.5·V(a) -> s_a = 4/7, s_b = 2/7(위 test_hand_linear_system
    의 연립), 반환 slope[root] = 1. 행 (a, gnd, +1, 0.2): Δ ≥ −0.35, 행 (vdd, a, +1, 0.3): Δ ≤ 0.525 (손: 0.2·7/4, 0.3·7/4)."""
    grad = _linear_gradient({"a": {"x": 0.5, "b": 0.25}, "b": {"a": 0.5}}, {"a": 0.0, "b": 0.0})
    vals = {"x": 1.0, "a": 4 / 7, "b": 2 / 7, "gnd": 0.0, "vdd": 1.8}
    dlo, dhi, slope = saturation_window(("a", "b", "x"), "x", vals, grad,
                                        (("a", "gnd", 1.0, 0.2, "sat"), ("vdd", "a", 1.0, 0.3, "sat")))
    assert abs(dlo + 0.35) <= 1e-12 and abs(dhi - 0.525) <= 1e-12 and slope["x"] == 1.0


def test_it2c_sw_pair_root_is_not_accepted():
    """oracle 대조: (식) [IT-2c T-P] interface 'root = 넷 하나(쌍·묶음 없음)': 쌍 root 는 넷 이름이 아니므로 받지 않는다(예외 종류는 계약이 정하지 않아
    TypeError·ValueError·KeyError 허용). 옛 쌍 호출 형식이 그대로 창을 돌려주면 red."""
    grad = _linear_gradient({"a": {"b": 0.5, "r": 0.25}, "b": {"a": 0.5}, "r": {"a": 0.3}}, {"a": 0.0, "b": 0.0, "r": 0.0})
    vals = {"a": 1.0, "b": 0.5, "r": 3.0, "gnd": 0.0, "vdd": 1.8}
    with pytest.raises((TypeError, ValueError, KeyError)):
        saturation_window(("a", "b", "r"), (("r", "a"),), vals, grad, (("a", "gnd", 1.0, 0.2, "sat"),))


def _never(net, V):
    raise AssertionError("slope 를 줬는데 gradient 가 불렸다")


@pytest.mark.parametrize("tiny", [0.0, 1.0e-17, -1.0e-17, 2.0e-16])
def test_it2c_sw_rows_with_slope_at_or_below_float_eps_are_skipped(tiny):
    """oracle 대조: (식) [IT-2c T-P] interface: 행 기울기 |sign·(s_a − s_b)| 가 sys.float_info.epsilon(2.220446049250313e-16) 이하이면 행을 건너뛴다(V/V 행
    분해능). 주어진 감도 s_a = tiny(|tiny| <= eps), 나머지 0 -> 행 (a, gnd, +1, 0.2) 의 기울기 = tiny -> 제약 아님 -> (−inf, +inf)."""
    vals = {"x": 1.0, "a": 0.5, "gnd": 0.0, "vdd": 1.8}
    given = {"x": 1.0, "a": tiny, "gnd": 0.0, "vdd": 0.0}
    dlo, dhi, slope = saturation_window(("a", "x"), "x", vals, _never, (("a", "gnd", 1.0, 0.2, "sat"),), slope=given)
    assert (dlo, dhi) == (-math.inf, math.inf) and slope == given


def test_it2c_sw_row_just_above_float_eps_is_kept():
    """oracle 대조: (식) 위 test 의 대조 -- 기울기 4.5e-16(> eps 2.22e-16) 행은 선다: slack + 4.5e-16·Δ ≥ 0 -> dlo = −0.2/4.5e-16 (손)."""
    vals = {"x": 1.0, "a": 0.5, "gnd": 0.0, "vdd": 1.8}
    given = {"x": 1.0, "a": 4.5e-16, "gnd": 0.0, "vdd": 0.0}
    dlo, dhi, _ = saturation_window(("a", "x"), "x", vals, _never, (("a", "gnd", 1.0, 0.2, "sat"),), slope=given)
    assert dhi == math.inf and abs(dlo - (-0.2 / 4.5e-16)) <= 1e-9 * abs(0.2 / 4.5e-16)


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
        rows.append((d, src, rng.choice((1.0, -1.0)), rng.uniform(0.0, 0.3), "sat"))
    lo_e, hi_e = -math.inf, math.inf
    for d, src, sg, slack, _kind in rows:
        a = sg * (s[d] - s[src])
        if abs(a) <= sys.float_info.epsilon:
            continue
        if a > 0:
            lo_e = max(lo_e, -slack / a)                 # [IT-2b 갱신] 이동량 창: 옛 절대 창에서 x0 를 뺀 값
        else:
            hi_e = min(hi_e, slack / -a)
    lo, hi, slope = saturation_window(tuple(sorted(nodes + ["x"])), "x", vals, _linear_gradient(coef, const), tuple(rows))
    for n in nodes:
        assert abs(slope[n] - s[n]) <= 1e-9 * max(1.0, abs(s[n])), (n, slope[n], s[n])      # 반환 slope = numpy 해
    for got, exp in ((lo, lo_e), (hi, hi_e)):
        assert (math.isinf(got) and got == exp) or abs(got - exp) <= 1e-9 * max(1.0, abs(exp)), (got, exp)


def test_singular_system_is_none():
    """V(a) = V(b), V(b) = V(a) -> (I − G) 특이 -> None(CONTRACT 14.6 '(1)이 풀리지 않으면 종래 사상')."""
    grad = _linear_gradient({"a": {"b": 1.0}, "b": {"a": 1.0}}, {"a": 0.0, "b": 0.0})
    vals = {"x": 1.0, "a": 0.5, "b": 0.5, "gnd": 0.0}
    assert saturation_window(("a", "b", "x"), "x", vals, grad, (("a", "gnd", 1.0, 0.2, "sat"),)) is None


def test_gradient_outside_domain_is_none():
    def grad(net, V):
        raise SealViolationError(devices=(), margin=None, detail={"reason": "lut_query_failed"})
    vals = {"x": 1.0, "a": 0.5, "gnd": 0.0}
    assert saturation_window(("a", "x"), "x", vals, grad, (("a", "gnd", 1.0, 0.2, "sat"),)) is None


# ===========================================================================
# 커널 통합: 순환 follower toy (입력 DC 대기)
# ===========================================================================

def _doc():
    net = [mos("MA", "nmos", "y", "x", "gnd", "gnd"), mos("MB", "nmos", "x", "in", "y", "y")]
    src = [two("IX", "current_source", "vdd", "x"), two("IY", "current_source", "vdd", "y")]
    return topo("u4_icm_follower", net, {"in": ("input", "x"), "y": ("output", "y")}, sources=src)


@pytest.fixture          # [XRUN-F1 card B 규칙 M M-d] KernelContext(실행 두 객체를 칸으로 쥠)는 function 범위
def pend(tmp_path_factory, r4_access):
    ctx = build_ctx(tmp_path_factory.mktemp("icm_pend"), _doc(), r4_access)[2]
    w = dict(ctx.base.column("node", "dc_writer"))["in"]
    assert w.relation == "free_window" and w.y_key == "in"            # 전제: in = 입력 포트 W4 뿌리 (y 키 = 그 넷, IT-1)
    return ctx


def _theta(ctx, vgs_a, vgs_b, y=None):
    th = {("L", "MA"): 1e-6, ("L", "MB"): 1e-6, ("ln_idu", "MA"): r4_ln_idu("nmos", vgs_a, 0.3, 0.0),
          ("ln_idu", "MB"): r4_ln_idu("nmos", vgs_b, 0.3, 0.0)}
    if y is not None:
        th[("y", "in")] = y
    th.update(free_currents(ctx, {"MA": 1e-5, "MB": 1e-5, "IX": 1e-5, "IY": 1e-5}))
    assert set(th) == set(kschema(ctx).components)
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
        # [IT-2c 갱신, 승인 동작 변경 O-204] 창 끝 행의 판정 여유 0: slack = VDS - VDSAT (tol_VDsat 항 없음). 봉인 7 쪽 oracle 은 +tol 그대로.
        slack_a = y - r4_vdsat_at("nmos", R4_L[0], x, 0.0)
        slack_b = (x - y) - r4_vdsat_at("nmos", R4_L[0], vgb, 0.0)
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


# [WB-1 3a E-13 이행] 커널 `node.dc_window[뿌리]` 는 **KVL 순서 창**(뿌리 넷에 채널이 닿는 전도 MOS 의 V_DS ≥ 0 교집합, VDSAT·tol 읽기 0)이다.
# 이 toy 의 뿌리 `in` 은 게이트만 닿으므로 창 = 레일 범위(`test_block_dc.py::test_window_w4_gate_only_root_is_rail_range_without_constraints`)이고
# V(in) = lo + y·(hi − lo) 는 포화 창 [lo*, hi*] 와 무관하다. 옛 test 들의 '창 안 y 는 모두 봉인, 창 끝 y=0·1 도 포화 여유 ≥ 0, 비면 empty_window' 전제
# (커널이 포화 여유로 창을 좁히고 y 를 그 안에 사상)는 사라졌다 -> RETIRED_TESTS_wb1.md. 살아 있는 물리 단언은 아래 새 test 로 옮긴다:
#   (1) 정확한 포화 창(Follower 독립 풀이) 안으로 사상되는 y 는 봉인 7 pass + 독립 여유 ≥ 0,
#   (2) 창 밖으로 사상되는 y 는 어떤 경우에도 봉인되지 않고 SealViolationError(봉인 7 `slack_v` 가 독립 여유 이하),
#   (3) 정확한 포화 창이 빈 구성은 모든 y 가 거부,
#   (4) 기록된 순서 창은 포화 창보다 넓다(커널이 포화 여유로 좁히지 않는다 -- E-13).
# oracle: (a) 물리 불변식(포화 여유 VDS − VDSAT ≥ 0) + (b) Follower 독립 풀이(r4 닫힌 식 bisection). 피검 함수로 기대값을 만들지 않는다.
_CONFIGS = {"mid": (0.9, 0.3, 0.9), "below": (0.6, 0.3, 0.67), "above": (1.1, 0.3, 1.08)}      # (VGS_A, VGS_B, 창 안 추측 V(in))


def _oracle_slacks(ev):
    """O-204 정의 포화 여유 VDS − VDSAT (문턱 없음)을 엔진이 낸 노드전압에서 독립으로 잰다(MA: VDS = V(y), VGS = V(x);
    MB: VDS = V(x) − V(y), VGS = V(in) − V(y), VSB 0). VDSAT·tol = conftest npz 열 직접."""
    V = node_voltages(ev.snapshot)
    sa = V["y"] - r4_vdsat_at("nmos", R4_L[0], V["x"], 0.0)
    sb = (V["x"] - V["y"]) - r4_vdsat_at("nmos", R4_L[0], V["in"] - V["y"], 0.0)
    return sa, sb


def _recorded_window(pend, va=None, vb=None):
    """커널이 기록한 입력 창(순서 창). 게이트만 닿는 뿌리라 창은 y·소자 좌표와 무관한 레일 범위이므로 기준 구성(VGS 0.9/0.3, y 0.5)의 열 평가에서 읽는다
    (va·vb 는 받기만 한다: 포화 아닌 구성은 열 평가에서 VDS < 0 LUT 정의역 밖으로 거부될 수 있어 구성별로 못 읽는다). 다른 구성의 봉인 test 는 자기 평가의
    창이 이것과 같음을 따로 단언한다."""
    return dict(run_blocks(pend, _theta(pend, 0.9, 0.3, 0.5), upto="columns").column("node", "dc_window"))["in"]


def _y_for(w, vin):
    """기록된 창 [lo, hi] 에서 V(in) = lo + y·(hi − lo) 가 되는 y (사상 정의의 역)."""
    return (vin - w.lo) / (w.hi - w.lo)


def test_recorded_window_is_order_window_wider_than_exact_saturation_window(pend):
    """E-13: 순서 창은 V_DS ≥ 0 만 쓰고 포화 여유를 쓰지 않는다 -> 기록된 창은 정확한 포화 창을 **포함하고 더 넓다**(옛: 포화 창 끝 ±tol_V 와 같음).
    oracle (b): Follower 독립 풀이의 정확한 포화 창."""
    for va, vb, guess in _CONFIGS.values():
        lo_e, hi_e = Follower(va, vb).window(guess)
        w = _recorded_window(pend, va, vb)
        assert w.lo < lo_e < hi_e < w.hi, (w.lo, w.hi, lo_e, hi_e)


@pytest.mark.parametrize("t", [0.3, 0.5, 0.7])
@pytest.mark.parametrize("key", sorted(_CONFIGS))
def test_y_mapped_inside_exact_saturation_window_seals(pend, key, t):
    """(1) 정확한 포화 창 [lo*, hi*] 의 t 분위 V(in) 로 사상되는 y(= 기록된 창의 역사상)는 봉인되고 봉인 7 pass, 엔진이 낸 노드전압에서 독립으로 잰
    포화 여유 VDS − VDSAT 은 두 소자 모두 ≥ 0, V(in) 은 사상 정의 lo + y·(hi − lo) 와 1e-12 안으로 같다. oracle (a)+(b)."""
    va, vb, guess = _CONFIGS[key]
    lo_e, hi_e = Follower(va, vb).window(guess)
    w = _recorded_window(pend, va, vb)
    target = lo_e + t * (hi_e - lo_e)
    ev = size_and_seal(pend, _theta(pend, va, vb, _y_for(w, target)))
    assert ev.sealed is not None
    assert seal_item(ev.snapshot, 7).status == "pass"
    assert _window(ev) == w                                                        # 창은 구성과 무관한 레일 범위
    vin = node_voltages(ev.snapshot)["in"]
    assert abs(vin - target) <= 1e-9
    assert lo_e <= vin <= hi_e
    assert min(_oracle_slacks(ev)) >= -1e-12


@pytest.mark.parametrize("d", [0.1, 0.3])
@pytest.mark.parametrize("side", ["below", "above"])
@pytest.mark.parametrize("key", sorted(_CONFIGS))
def test_y_mapped_outside_exact_saturation_window_is_never_sealed(pend, key, side, d):
    """(2) 정확한 포화 창에서 d 만큼 벗어난 V(in) 로 사상되는 y 는 봉인되지 않는다(SealViolationError: 포화 여유 음수 -> 봉인 7 또는 VDS < 0 LUT 정의역 밖).
    창 끝 쪽 레일 안에 드는 점만 쓴다(전제). 이 거부가 빠지면 포화 아닌 점이 봉인된다 -> fail-open. oracle (a)+(b)."""
    va, vb, guess = _CONFIGS[key]
    lo_e, hi_e = Follower(va, vb).window(guess)
    w = _recorded_window(pend, va, vb)
    vin = lo_e - d if side == "below" else hi_e + d
    assert w.lo < vin < w.hi                                                       # 전제: 레일 안
    with pytest.raises(SealViolationError):
        size_and_seal(pend, _theta(pend, va, vb, _y_for(w, vin)))


@pytest.mark.parametrize("y", [0.0, 1.0])
@pytest.mark.parametrize("key", sorted(_CONFIGS))
def test_rail_end_y_is_never_sealed(pend, key, y):
    """(2') 레일 범위 끝 y = 0·1 (V(in) = 레일 하·상단)은 모든 구성에서 정확한 포화 창 밖이라(전제) 봉인되지 않는다. 옛 test_window_ends_are_saturated 가
    '창 끝 y 도 포화'였던 전제는 E-13 으로 사라졌고 물리 결론(포화가 아니면 봉인 안 됨)만 남는다."""
    va, vb, guess = _CONFIGS[key]
    lo_e, hi_e = Follower(va, vb).window(guess)
    w = _recorded_window(pend, va, vb)
    assert not lo_e <= (w.lo if y == 0.0 else w.hi) <= hi_e                        # 전제
    with pytest.raises(SealViolationError):
        size_and_seal(pend, _theta(pend, va, vb, y))


def test_seal7_slack_v_is_not_better_than_independent_slack(pend):
    """봉인 7 거부의 `slack_v`(엔진)는 같은 점에서 독립으로 잰 O-204 여유 VDS − VDSAT(문턱 없음) 이하다 -- 봉인 7 은 +tol_VDsat 를 더 요구하므로
    엔진 여유가 독립 여유보다 클 수 없다. V(in) 0.45 V(포화 창 [0.79, 1.04] 밖)에서 음수. oracle (a)+(b)."""
    va, vb, guess = _CONFIGS["mid"]
    w = _recorded_window(pend, va, vb)
    theta = _theta(pend, va, vb, _y_for(w, 0.45))
    with pytest.raises(SealViolationError) as ei:
        size_and_seal(pend, theta)
    d = detail(ei.value)
    assert d["item"] == 7
    slack_v = dict(d["item_detail"])["slack_v"]
    ind = min(_oracle_slacks(SimpleNamespace(snapshot=run_blocks(pend, theta, upto="columns"))))
    assert slack_v < 0 and slack_v <= ind + 1e-12, (slack_v, ind)


def test_declared_input_dc_same_theta_seals(tmp_path, r4_access):
    """위 test 의 전제: 같은 소자 좌표로 입력 DC 0.67 V 를 선언하면 봉인된다(창이 실재)."""
    ctx = build_ctx(tmp_path, _doc(), r4_access, input_dc_v=0.67)[2]
    assert dict(ctx.base.column("node", "dc_writer"))["in"].relation == "input_dc"
    ev = size_and_seal(ctx, _theta(ctx, 0.6, 0.3))
    assert ev.sealed is not None and node_voltages(ev.snapshot)["in"] == 0.67
    # [IT-2b 갱신 -- 승인된 동작 변경 design 41 4.7-3 3·4.7-8 (1): 입력 DC 선언 포트도 창 항목을 갖는다] 옛 단언 `"in" not in dc_window`
    # ('선언 입력 DC 는 창 사상이 없다')을 새 계약으로 바꾼다: 항목이 있고 측정된 창(input_status "measured", lo ≤ 0.67 ≤ hi)이다.
    # [IT-2c 갱신 -- A-83] 커널 `node.dc_window` 는 W4 뿌리 넷만 갖는다(interface 'node.dc_window(바뀜)') -> 선언 포트 `dc_window["in"]` 단언은 지운다.
    # cfg 로 옮기지 않는 사유: `node.dc_window_cfg` 의 writer 는 metrics 블록 `icm_config`(ss_evaluate 단계)라 `size_and_seal` 스냅샷에는 항목이 없고(KeyError 실측),
    # sizing 층 test 에서 metrics 층을 부르는 근거가 interface 에 없다. 선언 입력 DC 포트의 cfg `measured` 창 단언은 tests/metrics/test_icm_config*.py 가 맡는다.


def test_empty_exact_saturation_window_rejects_every_y(pend):
    """VGS 0.5/0.6: slack_A + slack_B = V(x) − VDSAT_A − VDSAT_B − 2·tol 은 V(in) 에 거의 무관(V(x) 는 VDS(MA) 의 LAM 항으로만
    움직임)하고 음수다(독립 풀이로 V(y) > 0 인 0.7..1.3 V 격자 확인, 손계산 ≈ 0.5 − 0.25 − 0.3025 − 0.002) -> 포화 창이 비었다 -> 어떤 y 도 봉인되지 않는다.
    [WB-1 E-13 이행] 옛 단언 `reason == "empty_window"`(커널이 포화 창을 좁혀 비면 그 사유로 거부)는 사라졌다: 순서 창은 포화 여유를 쓰지 않아
    창은 비지 않고 거부는 봉인 7(포화 여유 음수) 또는 VDS < 0 LUT 정의역 밖(`lut_query_failed`)이 낸다. 물리 결론(포화 점이 없으면 봉인 없음)은 유지. oracle (b)."""
    f = Follower(0.5, 0.6)
    assert all(sum(f.solve(0.7 + 0.03 * i)[2:]) < -0.05 for i in range(21))            # 전제
    for y in (0.0, 0.25, 0.5, 0.75, 1.0):
        with pytest.raises(SealViolationError):
            size_and_seal(pend, _theta(pend, 0.5, 0.6, y))


def test_repeat_identical(pend):
    """같은 θ(포화 창 안 y = 0.5 -> V(in) 0.9 V) 두 번 -> 같은 스냅샷 지문·같은 창. oracle (c): 결정성."""
    a = size_and_seal(pend, _theta(pend, 0.9, 0.3, 0.5))
    b = size_and_seal(pend, _theta(pend, 0.9, 0.3, 0.5))
    assert a.snapshot.fp == b.snapshot.fp and _window(a) == _window(b)
