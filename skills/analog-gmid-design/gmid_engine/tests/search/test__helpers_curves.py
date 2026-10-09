"""search/_helpers_curves.py -- `at_gm_id`(gm/ID 축 보간)·`hull`(수준 집합의 gm/ID 폭) (설계 41 §6, §4.1 해법 매핑).

oracle (a) 손계산: 마디 gm/ID 는 분지에서 내려가는 순서(lut 4.5 `GmIdAxisCurve`). 선형 보간은 두 마디 사이 직선, log 보간은 기하 평균,
정의역 밖은 끝 값. hull 은 {g : v(g) ≤ level}(below) 의 (최소, 최대) -- 마디 사이 선형 교차점, 비단조 곡선은 모든 칸을 센다, 비면 None.
"""
import math

import pytest

from gmid_engine.search._helpers_curves import at_gm_id, hull

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
