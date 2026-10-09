"""`coupled_residual` -- 설계 41 §2.4 단계 B1: 산출 r̂ = 중앙값, r̂_spread = 최대 − 최소(봉인 표본의 잔차), 체크리스트 D-BM.

oracle (a) 손계산: [0.1, −0.3, 0.5, 0.2] -> 중앙값 (0.1 + 0.2)/2 = 0.15, spread 0.8. 정의 안 된 잔차(None)·비유한 값은 표본에서 뺀다(계약 10.0).
"""
from __future__ import annotations

import math

import pytest

from gmid_engine.metrics import CoupledResidual, coupled_residual


def test_median_and_spread():
    got = coupled_residual((0.1, -0.3, 0.5, 0.2))
    assert isinstance(got, CoupledResidual)
    assert got.median_db == pytest.approx(0.15, abs=1e-15)
    assert got.spread_db == pytest.approx(0.8, abs=1e-15)
    assert got.count == 4


def test_odd_count_median():
    got = coupled_residual((3.0, -1.0, 2.0))
    assert (got.median_db, got.spread_db, got.count) == (2.0, 4.0, 3)


def test_undefined_and_nonfinite_dropped():
    got = coupled_residual((None, 1.0, math.nan, math.inf, -2.0))
    assert (got.median_db, got.spread_db, got.count) == (-0.5, 3.0, 2)


def test_empty():
    assert coupled_residual(()) == CoupledResidual(None, None, 0)
    assert coupled_residual((None, math.nan)) == CoupledResidual(None, None, 0)


def test_order_invariant():
    assert coupled_residual((0.1, -0.3, 0.5, 0.2)) == coupled_residual((0.5, 0.2, -0.3, 0.1))
