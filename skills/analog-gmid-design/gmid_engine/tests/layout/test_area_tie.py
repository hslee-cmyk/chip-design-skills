"""CONTRACT 4.10 ΔA_tie -- `area_tie.area_tie_m2(a, b) = grid x max(a.bbox_width_m, a.bbox_height_m, b.bbox_width_m, b.bbox_height_m)`
(U12 D-LY1 / R20, 계획 DEC-79·DEC-95 (2): MANUFACTURINGGRID x max(두 점 bbox 의 변 4개)). 두 점 격자가 다르면 ValueError.

oracle: (d) 계획 식(DEC-95 (2))의 손계산 -- 변 길이를 손으로 정한 FloorplanSummary 두 개, 기대값은 손으로 곱한 수.
          (a) 구성: 대칭(a, b 교환), 자기 자신과도 0 이 아님, 옛 grid² 보다 큼(외곽 변 > 격자 한 칸일 때).
"""
from __future__ import annotations

import pytest

from gmid_engine.layout.area_tie import area_tie_m2
from gmid_engine.layout.contract_output import FloorplanSummary
from gmid_engine.layout.floorplan import floorplan_of

from .conftest import toy_pdk
from .test_floorplan import row


def fp(w, h, grid=1e-8):
    return FloorplanSummary(bbox_width_m=w, bbox_height_m=h, outline_area_m2=w * h, grid_m=grid, aspect_ratio=max(w, h) / min(w, h),
                            packing_density=1.0, placements=(), included=())


def test_hand_value_largest_of_four_sides():
    # 손계산: a 3 x 1 µm, b 2 x 5 µm, g 10 nm -> 변 4개 최대 5 µm -> 1e-8 x 5e-6 = 5e-14 m²
    assert area_tie_m2(fp(3e-6, 1e-6), fp(2e-6, 5e-6)) == pytest.approx(5e-14, rel=1e-12)
    # 최대 변이 a 의 폭일 때: a 40 x 7 µm, b 9 x 12 µm, g 5 nm -> 5e-9 x 40e-6 = 2e-13 m²
    assert area_tie_m2(fp(40e-6, 7e-6, 5e-9), fp(9e-6, 12e-6, 5e-9)) == pytest.approx(2e-13, rel=1e-12)


def test_symmetric():
    a, b = fp(3e-6, 1e-6), fp(2e-6, 5e-6)
    assert area_tie_m2(a, b) == area_tie_m2(b, a)


def test_same_point_is_not_zero_and_exceeds_old_grid_squared():
    a = fp(3e-6, 1e-6)
    tie = area_tie_m2(a, a)
    assert tie == pytest.approx(1e-8 * 3e-6, rel=1e-12)                    # 손계산 3e-14 m²
    assert tie > 1e-8 ** 2                                                  # 옛 grid² (1e-16) 보다 훨씬 크다(R20 결함)


@pytest.mark.parametrize("ga, gb", [(1e-8, 5e-9), (5e-9, 1e-8), (1e-8, 1.0000000001e-8)])
def test_grid_mismatch_rejected(ga, gb):
    with pytest.raises(ValueError):
        area_tie_m2(fp(3e-6, 1e-6, ga), fp(2e-6, 5e-6, gb))


def test_floorplan_of_output_is_consumed(toy_lut):
    # floorplan_of 의 실제 출력 두 개: 단일 행 3 µm + 2 x 0.2 µm dummy + tap 0.3 µm = 3.7 µm 폭, 높이 1 µm (test_floorplan 손계산)
    # / 같은 행 + 높이 2 µm(finger_w 2e-6) -> 3.7 x 2 µm. 최대 변 3.7 µm -> 1e-8 x 3.7e-6 = 3.7e-14 m²
    pdk = toy_pdk(toy_lut, dummy=0.2e-6, tap=0.3e-6)
    a = floorplan_of((row("r/w100", "r", 3e-6),), {"r": "sub"}, pdk)
    b = floorplan_of((row("r/w200", "r", 3e-6, fw=2e-6, key=200),), {"r": "sub"}, pdk)
    assert area_tie_m2(a, b) == pytest.approx(3.7e-14, rel=1e-9)
