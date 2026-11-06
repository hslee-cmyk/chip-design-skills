"""WB-1 F-3 -- `is_slice_gap`, `SLICE_GAP_REASONS` (interface card §2). oracle (식): card 가 열거한 사유 표."""
import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.lut import SLICE_GAP_REASONS, is_slice_gap

GAP = ("lut_axis_out_of_range", "lut_l_not_anchor", "lut_l_outside_model_bins", "lut_l_bin_unbracketed",
       "lut_l_cross_bin")


def test_slice_gap_reasons_tuple_exact():
    assert tuple(SLICE_GAP_REASONS) == GAP


@pytest.mark.parametrize("r", GAP)
def test_slice_gap_true_for_listed(r):
    assert is_slice_gap(SealViolationError(detail={"reason": r})) is True


@pytest.mark.parametrize("r", ["lut_column_unavailable", "lut_curve_undefined", "lut_query_failed"])
def test_slice_gap_false_for_others(r):
    assert is_slice_gap(SealViolationError(detail={"reason": r})) is False


def test_slice_gap_false_for_empty_detail():
    assert is_slice_gap(SealViolationError()) is False
