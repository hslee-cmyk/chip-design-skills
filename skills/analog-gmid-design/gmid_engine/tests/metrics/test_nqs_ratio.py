"""`nqs_ratio` -- 설계 40 §3.8-4 '`nqs_ratio` = `ugf_ss_hz` / 신호 경로 소자 최소 f_T, f_T = gm/(2π·cgg)', 체크리스트 D-GB8b, 계약 10.0.

oracle (a) 손계산: gm 1 mS·cgg 10 fF -> f_T = 1e-3/(2π·1e-14) = 15.915 GHz; gm 0.2 mS·cgg 5 fF -> 6.366 GHz(최소). ugf 100 MHz -> 0.0157.
"""
from __future__ import annotations

import math

import pytest

from gmid_engine.metrics import NqsRatio, nqs_ratio

from .conftest import codes


def test_ratio_uses_minimum_ft():
    got = nqs_ratio((("Ma", 1e-3, 1e-14), ("Mb", 2e-4, 5e-15)), 1e8)
    ft_b = 2e-4 / (2 * math.pi * 5e-15)
    assert isinstance(got, NqsRatio)
    assert got.min_ft_hz == pytest.approx(ft_b, rel=1e-14)
    assert got.ratio == pytest.approx(1e8 / ft_b, rel=1e-14)
    assert got.limiting_device == "Mb"


def test_nonpositive_cgg_or_gm_skipped():
    got = nqs_ratio((("Ma", 1e-3, 1e-14), ("Mz", 1e-3, 0.0), ("Mo", 0.0, 1e-14)), 1e8)
    assert got.limiting_device == "Ma"
    assert got.ratio == pytest.approx(1e8 * 2 * math.pi * 1e-14 / 1e-3, rel=1e-14)


def test_undefined():
    assert codes(nqs_ratio((("Ma", 1e-3, 1e-14),), None).undefined) == {"ugf_unavailable"}
    got = nqs_ratio((("Mz", 1e-3, 0.0),), 1e8)
    assert got.ratio is None and codes(got.undefined) == {"ft_undefined"}
    assert codes(nqs_ratio((), 1e8).undefined) == {"ft_undefined"}


def test_order_and_name_invariance():
    a = nqs_ratio((("Ma", 1e-3, 1e-14), ("Mb", 2e-4, 5e-15)), 1e8)
    b = nqs_ratio((("Q", 2e-4, 5e-15), ("P", 1e-3, 1e-14)), 1e8)
    assert a.ratio == b.ratio and b.limiting_device == "Q"
