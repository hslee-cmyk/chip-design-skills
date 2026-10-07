"""CONTRACT 4.9 `box_verdict(rows, folds) -> BoxVerdict` (Q8 (vi) -- 기록만, 하드 게이트 없음)."""
from __future__ import annotations

import dataclasses
import itertools

import pytest

from gmid_engine.layout.box_shape import box_verdict
from gmid_engine.layout.contract_output import BoxVerdict


def test_hand_values_no_ties():
    rows = (("a", 4e-6, 1e-6), ("b", 2e-6, 1e-6), ("c", 3e-6, 2e-6))
    v = box_verdict(rows, [("x", 2)])
    assert isinstance(v, BoxVerdict)
    assert v.width_ratio == pytest.approx(2.0)
    assert v.total_width_m == pytest.approx(4e-6)
    assert v.total_height_m == pytest.approx(4e-6)
    assert v.elongation == pytest.approx(1.0)
    assert v.widest_row == "a" and v.narrowest_row == "b"
    assert v.folds == (("x", 2),) and isinstance(v.folds, tuple)


def test_elongation_is_max_over_min_of_two_sides():
    v = box_verdict((("a", 6e-6, 2e-6),), ())
    assert v.width_ratio == pytest.approx(1.0)
    assert v.elongation == pytest.approx(3.0)
    assert v.widest_row == v.narrowest_row == "a"
    assert v.folds == ()


def test_no_ok_field_no_threshold():
    # 하드 box 게이트 폐지(Q8 (vi)): 판정 필드·허용치가 없다
    names = [f.name for f in dataclasses.fields(BoxVerdict)]
    assert names == ["width_ratio", "elongation", "total_width_m", "total_height_m", "widest_row", "narrowest_row", "folds"]
    v = box_verdict((("a", 100e-6, 1e-6), ("b", 1e-6, 1e-6)), ())    # 비율 100 이어도 그대로 기록
    assert v.width_ratio == pytest.approx(100.0)
    assert not hasattr(v, "ok")


def test_ties_resolved_independent_of_input_order():
    # 동률 규칙 '동률은 id 순으로 정렬해' -- 어느 쪽 끝을 고르는지 문구가 모호(보고). 여기서는 입력 순서 무관 + 동률 집합 안만 본다.
    rows = [("r2", 3e-6, 1e-6), ("r1", 3e-6, 1e-6), ("r3", 1e-6, 1e-6), ("r0", 1e-6, 1e-6)]
    results = {(box_verdict(tuple(p), ()).widest_row, box_verdict(tuple(p), ()).narrowest_row)
               for p in itertools.permutations(rows)}
    assert len(results) == 1
    widest, narrowest = results.pop()
    assert widest in ("r1", "r2") and narrowest in ("r0", "r3")
