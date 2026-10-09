"""`model_error_pairs` -- 설계 40 §3.8-6(오라클 대조 결과 `derived.model_error_<metric>`), DEC-72, 체크리스트 D-GB8c, 계약 10.0·10.7
(`build_search_context(model_error=)` 가 받는 ((metric, 크기), ...) 이름순, 레지스트리 밖 이름 KeyError, 비유한·비수 TypeError).

oracle (a): 입력 매핑에서 손으로 기대 tuple 을 적는다.
"""
from __future__ import annotations

import math

import pytest

from gmid_engine.metrics import model_error_pairs


def test_reads_prefixed_keys_sorted_magnitude():
    got = model_error_pairs({"model_error_gain_ss_db": -0.4, "model_error_icmr_v": 0.02, "other": 3, "offset_in_sigma_mv": 1.0})
    assert got == (("gain_ss_db", 0.4), ("icmr_v", 0.02))


def test_accepts_pairs():
    assert model_error_pairs((("model_error_swing_out_v", 1),)) == (("swing_out_v", 1.0),)


def test_unknown_metric_rejected():
    with pytest.raises(KeyError):
        model_error_pairs({"model_error_gain_db": 0.1})


@pytest.mark.parametrize("bad", [math.nan, math.inf, "0.1", True, None])
def test_bad_values_rejected(bad):
    with pytest.raises(TypeError):
        model_error_pairs({"model_error_gain_ss_db": bad})


def test_empty():
    assert model_error_pairs({}) == ()
