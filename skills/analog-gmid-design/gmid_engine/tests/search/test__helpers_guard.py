"""search/_helpers_guard.py -- `guard_devices(ctx)`(입력·부하 소자, 구조 역할)와 `guard_bounds(...)`(부하 합 가드 -> 소자별 gm/ID 상한)
(설계 41 §6.4-2a offset 가드, §7.5 열잡음 가드).

oracle:
- (a) 구조: CS 사슬의 첫 이득 블록 = MN1(입력, gate 가 입력 포트) + MP1(전류원 부하).
- (a) 손계산: 합 가드 Σ_loads term_k ≤ ratio·Σ_inputs term_in(g_in) 를 '나머지는 최소(gm/ID 하한)로 두고 k 가 가질 수 있는 최대'(41 §6.2 규약)로 쓰면
  level_k = ratio·Σ term_in − Σ_{j≠k} term_j(g_lo,j), 상한 = term_k(g) ≤ level_k 인 g 의 최댓값. term(g) = g(선형, test 가 고른 구성)이면 상한 = level_k
  (toy 곡선 gm/ID 마디 5.6..20 안일 때). level ≤ 0 이거나 어느 g 도 만족하지 않으면 자르지 않고 충돌 레코드(41 §6.6).
"""
import pytest

from gmid_engine.search._helpers_guard import guard_bounds, guard_devices, guard_input_gm_id
from .u13_hand import cs_chain, start_view_of, toy_case

ELS = (("C1", "capacitor", 1e-12), ("C2", "capacitor", 1e-12))


@pytest.fixture(scope="module")
def ctx():
    c = toy_case(cs_chain(2), elements=ELS, constraints=(("gbw_ss_hz", ">=", 1e6), ("pm_ss_deg", ">=", 60.0)))
    return start_view_of(c)


def test_guard_devices_first_gain_block(ctx):
    inputs, loads = guard_devices(ctx)
    assert tuple(inputs) == ("MN1",)
    assert tuple(loads) == ("MP1",)


def _term(name, g):
    return g


def test_guard_bounds_levels_hand_computed(ctx):
    lengths = {"MP1": 1e-6, "MP2": 1e-6}
    lo = {"MP1": 6.0, "MP2": 7.0}
    bounds, conflicts = guard_bounds(ctx, ("MN1",), ("MP1", "MP2"), _term, 2.0, lengths, lo, 10.0, "src_t")
    assert conflicts == ()
    # level_MP1 = 2·10 − 7 = 13, level_MP2 = 2·10 − 6 = 14
    (b1,) = bounds["MP1"]
    (b2,) = bounds["MP2"]
    assert (b1.quantity, b1.side, b1.source) == ("gm_id", "hi", "src_t")
    assert b1.value == pytest.approx(13.0, abs=1e-9)
    assert b2.value == pytest.approx(14.0, abs=1e-9)


def test_guard_bounds_unsatisfiable_is_conflict_not_cut(ctx):
    lengths = {"MP1": 1e-6, "MP2": 1e-6}
    lo = {"MP1": 6.0, "MP2": 7.0}
    # level_MP1 = 1·10 − 7 = 3 < 곡선 최솟값 5.6 -> 상한 없음 -> 충돌(어긋남 = 5.6 − 3)
    bounds, conflicts = guard_bounds(ctx, ("MN1",), ("MP1", "MP2"), _term, 1.0, lengths, lo, 10.0, "src_t")
    assert "MP1" not in bounds
    hit = [c for c in conflicts if c.device == "MP1"]
    assert len(hit) == 1 and hit[0].quantity == "gm_id"
    assert hit[0].gap == pytest.approx(5.6 - 3.0, abs=1e-9)


def _hump(name, g):
    """입력 기여: g = 12.1 근처에서 최대인 혹(toy 곡선 마디 20 − 0.8k 중 최대 마디 = 12.0). 부하 기여: g(선형)."""
    return 30.0 - (g - 12.1) ** 2 if name == "MN1" else g


def test_guard_input_measured_at_max_contribution_node(ctx):
    # CONTRACT U13 가드: 입력 쪽 기여는 입력 소자가 가질 수 있는 최대(하한 ~ 가드가 아닌 상한 안에서 기여가 최대인 곡선 마디)
    got = guard_input_gm_id(ctx, _hump, ("MN1",), {"MN1": 1e-6}, {"MN1": 6.4}, {"MN1": 16.0})
    assert got["MN1"] == pytest.approx(12.0, abs=1e-9)
    # 상한이 혹 아래면 그 안의 최대 마디 = 상한 쪽 마디 10.4
    got = guard_input_gm_id(ctx, _hump, ("MN1",), {"MN1": 1e-6}, {"MN1": 6.4}, {"MN1": 10.4 + 1e-9})
    assert got["MN1"] == pytest.approx(10.4, abs=1e-9)


def test_guard_input_skips_undefined_nodes(ctx):
    # LUT 가 정의하지 못하는 마디(None)는 뺀다: 12.0 이 None 이면 다음으로 큰 기여 12.8(−0.49) > 11.2(−0.81)
    def term(name, g):
        return None if abs(g - 12.0) < 1e-6 else _hump(name, g)
    got = guard_input_gm_id(ctx, term, ("MN1",), {"MN1": 1e-6}, {"MN1": 6.4}, {"MN1": 16.0})
    assert got["MN1"] == pytest.approx(12.8, abs=1e-9)


def test_guard_levels_use_input_max_and_loads_min(ctx):
    # 손계산(41 §6.2 규약 '나머지는 최소'): 입력 기여 = 혹 최대 30 − 0.01 = 29.99 (g_in = 12.0), ratio 0.5 -> 우변 14.995.
    # level_MP1 = 14.995 − term(MP2, lo 7) = 7.995, level_MP2 = 14.995 − 6 = 8.995; 부하 term = g 이므로 상한 = level.
    # 입력을 하한 6.4 에서 쟀다면 우변 = 0.5·(30 − 32.49) < 0 -> 모두 충돌(대조: 가장 느슨한 경우라 거짓 충돌이 없다).
    g_in = guard_input_gm_id(ctx, _hump, ("MN1",), {"MN1": 1e-6}, {"MN1": 6.4}, {"MN1": 16.0})
    lengths = {"MN1": 1e-6, "MP1": 1e-6, "MP2": 1e-6}
    bounds, conflicts = guard_bounds(ctx, ("MN1",), ("MP1", "MP2"), _hump, 0.5, lengths, {"MP1": 6.0, "MP2": 7.0}, g_in, "src_t")
    assert conflicts == ()
    rhs = 0.5 * (30.0 - (12.0 - 12.1) ** 2)
    (b1,) = bounds["MP1"]
    (b2,) = bounds["MP2"]
    assert b1.value == pytest.approx(rhs - 7.0, abs=1e-6)
    assert b2.value == pytest.approx(rhs - 6.0, abs=1e-6)
