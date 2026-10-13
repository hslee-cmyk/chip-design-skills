"""search/_helpers_curves.py -- `curve_value`(gm/ID 축 보간)·`hull`(수준 집합의 gm/ID 폭)·`curve_bundle`(같은 (L, VDS, VSB) 곡선 묶음)
(설계 41 §6, §4.1 해법 매핑).

[U17 ①-b] 옛 공개 `at_gm_id` 는 `_at_gm_id`(비공개)가 되고 공개 읽기는 `curve_value(bundle, quantity, g)` 다(40 §2.4.7 CurveBook 행 v1.9.1 D10).
같은 성질을 `curve_value` 로 본다: 선형 양 = intrinsic_gain, log 양 = idu(곡선 묶음은 test 쪽 SimpleNamespace -- gm_id·values 칸).

oracle (a) 손계산: 마디 gm/ID 는 분지에서 내려가는 순서(lut 4.5 `GmIdAxisCurve`). 선형 보간은 두 마디 사이 직선, log 보간은 기하 평균,
정의역 밖은 끝 값. hull 은 {g : v(g) ≤ level}(below) 의 (최소, 최대) -- 마디 사이 선형 교차점, 비단조 곡선은 모든 칸을 센다, 비면 None.
"""
import math

import pytest

from types import SimpleNamespace

from gmid_engine.search._helpers_curves import (QUANTITY_FT, QUANTITY_GAIN, QUANTITY_IDU, QUANTITY_VDSAT, QUANTITY_VGS, curve_bundle,
                                                curve_value, hull)

from .u13_hand import A, B, C, CGG_REF, I0, LAM, W_M, cs_chain, start_view_of, toy_case


def at_gm_id(gm_id, values, g, log=False):
    """test 쪽 입력 포장: 곡선 마디를 묶음 하나로 싸서 공개 `curve_value` 로 읽는다(log = log 보간 양 idu, 아니면 선형 양 intrinsic_gain)."""
    quantity = QUANTITY_IDU if log else QUANTITY_GAIN
    return curve_value({quantity: SimpleNamespace(gm_id=gm_id, values=values)}, quantity, g)

G = (20.0, 16.0, 12.0, 8.0)          # 내려가는 gm/ID 마디
V = (1.0, 2.0, 4.0, 8.0)


def test_linear_interpolation_between_nodes():
    assert at_gm_id(G, V, 14.0) == pytest.approx(3.0, abs=1e-15)      # (2 + 4)/2
    assert at_gm_id(G, V, 16.0) == pytest.approx(2.0, abs=1e-15)


def test_log_interpolation_is_geometric_mean():
    assert at_gm_id(G, V, 14.0, log=True) == pytest.approx(math.sqrt(2.0 * 4.0), rel=1e-12)


def test_outside_domain_clamps_to_end_values():
    assert at_gm_id(G, V, 25.0) == 1.0
    assert at_gm_id(G, V, 5.0) == 8.0


def test_hull_below_level_with_linear_crossing():
    # v ≤ 3: 마디 20(1)·16(2) 와 16–12 칸의 교차점 v = 3 -> g = 14
    assert hull(G, V, 3.0) == pytest.approx((14.0, 20.0))
    # v ≥ 3: 교차점 14 와 마디 12·8
    assert hull(G, V, 3.0, below=False) == pytest.approx((8.0, 14.0))


def test_hull_counts_all_cells_of_non_monotone_curve():
    v = (1.0, 5.0, 1.0, 5.0)            # 두 번 내려왔다 올라간다
    lo, hi = hull(G, v, 3.0)
    assert (lo, hi) == pytest.approx((10.0, 20.0))        # 교차 18·14·10, 마디 20·12 -> 전체 (10, 20)


def test_hull_empty_is_none():
    assert hull(G, V, 0.5) is None


def test_at_gm_id_non_monotone_curve_reads_strong_inversion_cell():
    # CONTRACT U13 '곡선 읽기(at_gm_id)는 gm/ID 를 품은 칸이 여럿이면(pmos 중반전 상승) 가장 오른쪽(강반전) 칸에서 읽는다'.
    # 손 toy 곡선(VGS 오름차순 마디): gm/ID 20 -> 14 로 내려갔다가 16 으로 다시 오른 뒤(혹) 10 으로 내려간다.
    g = (20.0, 14.0, 16.0, 10.0)
    v = (1.0, 2.0, 3.0, 4.0)
    # g = 15 는 세 칸 [20,14]·[14,16]·[16,10] 에 든다 -> 가장 오른쪽 칸 [16,10]: 3 + (16 − 15)/(16 − 10)·(4 − 3)
    assert at_gm_id(g, v, 15.0) == pytest.approx(3.0 + 1.0 / 6.0, rel=1e-12)
    # 한 칸에만 드는 값은 그 칸에서: g = 17 -> [20,14]: 1 + 3/6, g = 12 -> [16,10]: 3 + 4/6
    assert at_gm_id(g, v, 17.0) == pytest.approx(1.5, rel=1e-12)
    assert at_gm_id(g, v, 12.0) == pytest.approx(3.0 + 4.0 / 6.0, rel=1e-12)
    # log 보간도 같은 칸: 3^(5/6)·4^(1/6)
    assert at_gm_id(g, v, 15.0, log=True) == pytest.approx(3.0 ** (5.0 / 6.0) * 4.0 ** (1.0 / 6.0), rel=1e-12)


# ---------------------------------------------------------------- [U17 ①-b 판정 후] 옛 CurveBook oracle 2건을 `curve_bundle` 로 되살림
# 옛 tests/search/test_iv_curves.py(base 9255a22)의 test_values_at_nodes_match_construction·test_ft_decreases_with_gm_id 는 CurveBook 이
# 없어지며(설계 40 v1.9.1 §2.4.7 CurveBook 행·D10) 대체 없이 삭제됐다(audit 6절 '기준 약화'). 곡선 묶음 읽기는 이제 `curve_bundle(v, kind, L,
# vds, vsb)` + `curve_value` 다(v = 출발 구간 블록 안 읽기 묶음 StartView). 기대값은 toy LUT 구성 식에서만 만든다(피검 함수 미사용):
# oracle (a) toy LUT 해석식(u13_hand 머리) -- VGS 격자 마디에서 정확:
#   gm/ID = B − C·VGS, VDSAT = 2/(gm/ID), 진성 이득 = (gm/ID)/LAM, IDu = I0·exp(f(VGS) + LAM·VDS − A·VS²), f = B·VGS − C/2·VGS²,
#   f_T = (gm/ID)·IDu·W_ref/(2π·CGG_ref·L)  (lut 4.5: gm/(2π·Cgg), Cgg 는 폭에 비례하므로 폭 무관).
# 점 (L, VDS, VSB) = (1 µm, 0.9 V, 0.45 V) 와 VGS 0.3·1.0·1.5 V 는 모두 toy 격자점이다(u13_hand L_GRID·VDS_GRID·VS_GRID·VGS_GRID).

def _f(v):
    return B * v - 0.5 * C * v * v


@pytest.fixture(scope="module")
def view():
    c = toy_case(cs_chain(2), elements=(("C1", "capacitor", 1e-12), ("C2", "capacitor", 3e-12)),
                 constraints=(("gbw_ss_hz", ">=", 1e6), ("pm_ss_deg", ">=", 60.0)))
    return start_view_of(c)


@pytest.mark.parametrize("kind", ["nmos", "pmos"])
@pytest.mark.parametrize("vgs", [0.3, 1.0, 1.5])
def test_values_at_nodes_match_construction(view, kind, vgs):
    L, vds, vsb = 1e-6, 0.9, 0.45
    bundle = curve_bundle(view, kind, L, vds, vsb)
    assert bundle is not None
    g = B - C * vgs
    assert curve_value(bundle, QUANTITY_VDSAT, g) == pytest.approx(2.0 / g, rel=1e-9)
    assert curve_value(bundle, QUANTITY_GAIN, g) == pytest.approx(g / LAM, rel=1e-9)
    idu = I0[kind] * math.exp(_f(vgs) + LAM * vds - A * vsb * vsb)
    assert curve_value(bundle, QUANTITY_IDU, g) == pytest.approx(idu, rel=1e-9)
    ft = g * idu * W_M / (2 * math.pi * CGG_REF * L)
    assert curve_value(bundle, QUANTITY_FT, g) == pytest.approx(ft, rel=1e-9)
    assert curve_value(bundle, QUANTITY_VGS, g) == pytest.approx(vgs, abs=1e-12)


def test_ft_decreases_with_gm_id(view):
    # (a) 물리 단조: 같은 (L, VDS, VS) 에서 약반전(gm/ID 큼)일수록 f_T 가 낮다
    bundle = curve_bundle(view, "nmos", 1e-6, 0.9, 0.0)
    assert bundle is not None
    gs = [B - C * v for v in (1.7, 1.2, 0.7, 0.2)]
    fts = [curve_value(bundle, QUANTITY_FT, g) for g in gs]
    assert all(a > b for a, b in zip(fts, fts[1:]))
