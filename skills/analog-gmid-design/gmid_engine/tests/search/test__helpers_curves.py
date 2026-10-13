"""search/_helpers_curves.py -- `curve_value`(gm/ID 축 보간)·`hull`(수준 집합의 gm/ID 폭) (설계 41 §6, §4.1 해법 매핑).

[U17 ①-b] 옛 공개 `at_gm_id` 는 `_at_gm_id`(비공개)가 되고 공개 읽기는 `curve_value(bundle, quantity, g)` 다(40 §2.4.7 CurveBook 행 v1.9.1 D10).
같은 성질을 `curve_value` 로 본다: 선형 양 = intrinsic_gain, log 양 = idu(곡선 묶음은 test 쪽 SimpleNamespace -- gm_id·values 칸).

oracle (a) 손계산: 마디 gm/ID 는 분지에서 내려가는 순서(lut 4.5 `GmIdAxisCurve`). 선형 보간은 두 마디 사이 직선, log 보간은 기하 평균,
정의역 밖은 끝 값. hull 은 {g : v(g) ≤ level}(below) 의 (최소, 최대) -- 마디 사이 선형 교차점, 비단조 곡선은 모든 칸을 센다, 비면 None.
"""
import math

import pytest

from types import SimpleNamespace

from gmid_engine.search._helpers_curves import QUANTITY_GAIN, QUANTITY_IDU, curve_value, hull


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
