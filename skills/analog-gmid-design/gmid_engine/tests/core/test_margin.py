"""CONTRACT §4.6 normalized_margin(magnitude, tol) -- tol None/0 -> None, 그 밖 float(magnitude)/float(tol), 부호 보존."""
import pytest

from gmid_engine.core import normalized_margin


@pytest.mark.parametrize("tol", [None, 0, 0.0])
def test_none_or_zero_tol_gives_none(tol):
    assert normalized_margin(5.0, tol) is None
    assert normalized_margin(0, tol) is None


@pytest.mark.parametrize(
    "magnitude, tol, expected",
    [
        (3.0, 2.0, 1.5),
        (-3.0, 2.0, -1.5),
        (3.0, -2.0, -1.5),
        (1, 4, 0.25),
        (0, 7, 0.0),
        (0.5, 0.25, 2.0),
    ],
)
def test_ratio_hand_computed(magnitude, tol, expected):
    out = normalized_margin(magnitude, tol)
    assert type(out) is float
    assert out == expected


def test_int_inputs_return_float():
    out = normalized_margin(4, 2)
    assert type(out) is float and out == 2.0
