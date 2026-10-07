"""`k_max(width, tol)` -- CONTRACT 5.6: ceil(log2(width/tol)), width ≤ tol 이면 1. 양의 유한 수가 아니면 ValueError."""
import math

import pytest

from gmid_engine.sizing import k_max


@pytest.mark.parametrize("width,tol,expected", [
    (8.0, 1.0, 3),            # log2 8 = 3 정확
    (4.0, 1.0, 2),
    (10.0, 1.0, 4),           # log2 10 = 3.32 -> 4
    (1.8, 1e-3, 11),          # log2 1800 = 10.81 -> 11
    (1.8, 0.0384, 6),         # log2 46.9 = 5.55 -> 6
    (1.0, 1.0, 1),            # width == tol -> 1
    (0.5, 1.0, 1),            # width < tol -> 1
    (2.0 + 1e-12, 1.0, 2),
])
def test_values(width, tol, expected):
    assert k_max(width, tol) == expected
    assert k_max(width, tol) == (1 if width <= tol else math.ceil(math.log2(width / tol)))


def test_returns_int():
    assert isinstance(k_max(10.0, 1.0), int)


@pytest.mark.parametrize("width,tol", [
    (0.0, 1.0), (-1.0, 1.0), (1.0, 0.0), (1.0, -1e-3),
    (math.inf, 1.0), (1.0, math.inf), (math.nan, 1.0), (1.0, math.nan),
])
def test_rejects_non_positive_or_non_finite(width, tol):
    with pytest.raises(ValueError):
        k_max(width, tol)
