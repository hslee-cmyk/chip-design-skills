"""search/_helpers_guard.py -- `guard_devices(ctx)`(입력·부하 소자, 구조 역할)와 `guard_bounds(...)`(부하 합 가드 -> 소자별 gm/ID 상한)
(설계 41 §6.4-2a offset 가드, §7.5 열잡음 가드).

oracle:
- (a) 구조: CS 사슬의 첫 이득 블록 = MN1(입력, gate 가 입력 포트) + MP1(전류원 부하).
- (a) 손계산: 합 가드 Σ_loads term_k ≤ ratio·Σ_inputs term_in(g_in) 를 '나머지는 최소(gm/ID 하한)로 두고 k 가 가질 수 있는 최대'(41 §6.2 규약)로 쓰면
  level_k = ratio·Σ term_in − Σ_{j≠k} term_j(g_lo,j), 상한 = term_k(g) ≤ level_k 인 g 의 최댓값. term(g) = g(선형, test 가 고른 구성)이면 상한 = level_k
  (toy 곡선 gm/ID 마디 5.6..20 안일 때). level ≤ 0 이거나 어느 g 도 만족하지 않으면 자르지 않고 충돌 레코드(41 §6.6).
"""
import pytest

from gmid_engine.search._helpers_guard import guard_bounds, guard_devices
from gmid_engine.search.iv_context import build_start_context

from .u13_hand import cs_chain, toy_case

ELS = (("C1", "capacitor", 1e-12), ("C2", "capacitor", 1e-12))


@pytest.fixture(scope="module")
def ctx():
    c = toy_case(cs_chain(2), elements=ELS, constraints=(("gbw_ss_hz", ">=", 1e6), ("pm_ss_deg", ">=", 60.0)))
    return build_start_context(c.s1v, c.ach, c.kctx, c.spec, c.pdk, c.sctx.domain)


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
