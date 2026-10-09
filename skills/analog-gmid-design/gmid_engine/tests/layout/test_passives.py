"""CONTRACT 4.10 수동소자 블록 입력 -- `passives.passives_from_decl(area_decl, values) -> tuple[LayoutPassive]` (U12 D-LY4 / R22,
사용자 결정 11·Q9, 2026-10-08 '측정 부하 전체(CL, CL1, CL2, RL) 면적 제외').

면적 = `metrics.PassiveArea.area_m2`(값 x PDK 선언 단위 면적 + 머리 면적) 하나 -- 탐색 축 `area_search` 와 같은 정본.
측정 부하(`excluded`)·단위 면적 미선언 소자·값 없는 소자는 만들지 않는다. 이름순 tuple.

oracle: (a) 합성 선언(밀도·시트 저항 값은 test 가 정한 합성 수, PDK 실값 주장 아님) 위 손계산 면적 +
          단일 정본 대조(같은 선언을 탐색 축 `area_search` 에 넣은 면적 합 == 레이아웃 수동소자 면적 합 == 손계산 합).
"""
from __future__ import annotations

import pytest

from gmid_engine.layout.contract_input import LayoutPassive
from gmid_engine.layout.floorplan import floorplan_of
from gmid_engine.layout.passives import passives_from_decl
from gmid_engine.metrics import PassiveArea, PassiveAreaDecl, area_search

from .conftest import toy_pdk
from .test_floorplan import row

# 합성 선언(손계산):
#   MIM 밀도 2e-3 F/m² (= 2 fF/µm²) -> 단위 면적 500 m²/F. Cc = 2e-12 F -> 1e-9 m² (1000 µm²)
#   poly 저항 W_min 0.35 µm, R□ 2000 Ω -> 단위 면적 W²/R□ = 1.225e-13/2000 = 6.125e-17 m²/Ω, 머리 1e-12 m².
#   R1 = 1e4 Ω -> 6.125e-13 + 1e-12 = 1.6125e-12 m²
#   CL(측정 부하, excluded) 5e-12 F, RL(측정 부하) 2.5e4 Ω -> 만들지 않음. Rx(단위 면적 미선언) -> 만들지 않음.
MIM_UNIT = 1 / 2e-3
RES_UNIT = (0.35e-6) ** 2 / 2000.0
RES_HEAD = 1e-12
CC_AREA = 1e-9
R1_AREA = 1.6125e-12


def decl():
    return PassiveAreaDecl(unit_area=(("Cc", MIM_UNIT), ("R1", RES_UNIT)), excluded=("CL", "RL"), head_area=(("R1", RES_HEAD),))


VALUES = {"R1": 1e4, "Cc": 2e-12, "CL": 5e-12, "RL": 2.5e4, "Rx": 1e3}


def test_hand_areas_sorted_and_exclusions():
    out = passives_from_decl(decl(), VALUES)
    assert isinstance(out, tuple) and all(isinstance(p, LayoutPassive) for p in out)
    assert [p.name for p in out] == ["Cc", "R1"]                             # 이름순, 측정 부하·미선언 소자 없음
    a = {p.name: p.area_m2 for p in out}
    assert a["Cc"] == pytest.approx(CC_AREA, rel=1e-12)
    assert a["R1"] == pytest.approx(R1_AREA, rel=1e-12)


def test_measurement_load_excluded_even_if_valued():
    # 결정 11 + 2026-10-08 확인: 측정 부하(CL·RL)는 값이 있어도 면적에서 뺀다
    out = passives_from_decl(decl(), {"CL": 5e-12, "RL": 2.5e4})
    assert out == ()


def test_declared_but_no_value_not_created():
    out = passives_from_decl(decl(), {"Cc": 2e-12})
    assert [p.name for p in out] == ["Cc"]


def test_single_source_with_search_area():
    # 같은 선언·값을 탐색 축 area_search 에 넣은 수동소자 면적 == 레이아웃 수동소자 면적 합 == 손계산 합(1e-9 + 1.6125e-12)
    out = passives_from_decl(decl(), VALUES)
    unit, head = dict(decl().unit_area), dict(decl().head_area)
    search = area_search((), tuple(PassiveArea(n, VALUES[n], unit.get(n), head.get(n, 0.0))
                                   for n in sorted(VALUES) if n not in decl().excluded))
    layout_total = sum(p.area_m2 for p in out)
    assert layout_total == pytest.approx(CC_AREA + R1_AREA, rel=1e-12)
    assert search.area_search_m2 == pytest.approx(CC_AREA + R1_AREA, rel=1e-12)
    assert layout_total == search.area_search_m2                             # 같은 식 하나(정본) -> 정확히 같다


def test_floorplan_passive_area_at_least_declared_area(toy_lut):
    # 선언 -> LayoutPassive -> floorplan 블록: passive_area_m2 >= 식 면적 합, 블록마다 격자 올림 한 칸 줄 이내
    # (폭 w = ceil(sqrt(N)), 높이 ceil(N/w) 칸 -> 초과분 < w 칸 = 한 줄; g = 1e-8).
    ps = passives_from_decl(decl(), VALUES)
    fp = floorplan_of((row("r/w100", "r", 3e-6),), {"r": "sub"}, toy_pdk(toy_lut, gap=0.47e-6, well=1.63e-6), ps)
    assert fp.passive_area_m2 >= CC_AREA + R1_AREA
    P = {p[0]: p for p in fp.placements}
    for p in ps:
        _, _, _, w, h = P["passive:" + p.name]
        assert w * h >= p.area_m2 * (1 - 1e-12)
        assert w * h - p.area_m2 <= w * 1e-8 * (1 + 1e-9)                   # 한 줄(폭 x 격자 한 칸) 이내
    # Cc 1e-9 m² = 1e7 칸 -> 폭 ceil(3162.28) = 3163, 높이 ceil(1e7/3163 = 3161.56) = 3162 -> 10 001 406 칸
    assert (P["passive:Cc"][3], P["passive:Cc"][4]) == pytest.approx((3163e-8, 3162e-8), rel=1e-9)
    assert fp.passive_area_m2 >= sum(p.area_m2 for p in ps)
