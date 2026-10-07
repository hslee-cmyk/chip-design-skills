"""CONTRACT 4.3 `w_tolerance(gm_id, tol_v, finger_w_m, grid_m) -> WTolerance` (LY1, Q4 (iv)) -- 손계산 + 실효 = max(상한, 하한)."""
from __future__ import annotations

import pytest

from gmid_engine.layout.contract_output import WTolerance
from gmid_engine.layout.w_tolerance import w_tolerance


@pytest.mark.parametrize("args, expected", [
    ((10.0, 0.01, 1e-6, 5e-9), (0.0025, 0.1, 0.1, False)),       # 계약 손계산 1: 상한 지배
    ((10.0, 0.0, 1e-6, 1e-8), (0.005, 0.0, 0.005, True)),         # 계약 손계산 2: 격자 지배
])
def test_hand_values(args, expected):
    t = w_tolerance(*args)
    assert isinstance(t, WTolerance)
    lower, upper, effective, grid_dominated = expected
    assert t.lower == pytest.approx(lower, rel=1e-12)
    assert t.upper == pytest.approx(upper, rel=1e-12)
    assert t.effective == pytest.approx(effective, rel=1e-12)
    assert t.grid_dominated is grid_dominated


@pytest.mark.parametrize("gm_id, tol_v, fw, grid", [
    (15.0, 0.031, 5e-6, 5e-9), (16.0, 0.0046, 5e-6, 5e-9), (8.0, 0.0, 3.6e-7, 5e-9), (20.0, 1e-4, 2.61e-6, 5e-9),
])
def test_effective_is_max_and_flag_is_strict(gm_id, tol_v, fw, grid):
    t = w_tolerance(gm_id, tol_v, fw, grid)
    upper = tol_v * gm_id
    lower = grid / (2 * fw)
    assert t.upper == pytest.approx(upper, rel=1e-12, abs=0.0)
    assert t.lower == pytest.approx(lower, rel=1e-12)
    assert t.effective == max(t.upper, t.lower)
    assert t.grid_dominated is (t.lower > t.upper)


def test_equal_bounds_not_grid_dominated():
    # lower == upper 이면 grid_dominated 는 False(`lower > upper` 엄격 비교)
    t = w_tolerance(10.0, 0.0005, 1e-6, 1e-8)       # upper 0.005, lower 0.005
    assert t.upper == pytest.approx(t.lower, rel=1e-12)
    if t.lower == t.upper:
        assert t.grid_dominated is False
    assert t.effective == max(t.upper, t.lower)
