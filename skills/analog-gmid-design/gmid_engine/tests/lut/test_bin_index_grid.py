"""WB-1 B-1 -- `bin_index(intervals, x, grid_m, rule)` (interface card §1). oracle (손): 격자 정수 비교.

값을 round(값/grid_m) 정수로 바꿔 닫힌 구간끼리 비교한다. 경계 공유 시 rule lower = 앞 구간, upper = 뒤 구간.
손 유도: g = 5e-9 -> 5e-6 = 1000, 4.9999999999999996e-06 도 round 하면 1000. 1 ulp 가 아니라 32 eps 어긋나도 같은 정수.
"""
import pytest

from gmid_engine.lut._helpers_bins import bin_index

EPS = 2.0 ** -52
TWO = ((3e-6, 5e-6), (5e-6, 7e-6))


@pytest.mark.parametrize("g, intervals, x, rule, want", [
    (5e-9, TWO, 4.9999999999999996e-06, "lower", 0),
    (5e-9, TWO, 4.9999999999999996e-06, "upper", 1),         # base: 옛 규칙은 경계 공유를 못 가려 red
    (5e-9, TWO, 7.5e-6, "lower", None),
    (1e-8, ((1e-6, 2e-6),), 1e-6 * (1 - 32 * EPS), "lower", 0),   # base: 1 ulp 밖 None
    (1e-8, ((1e-6, 2e-6),), 2e-6 * (1 + 32 * EPS), "lower", 0),
])
def test_bin_index_card_table(g, intervals, x, rule, want):
    assert bin_index(intervals, x, g, rule) == want


@pytest.mark.parametrize("rule", ["lower", "upper"])
def test_bin_index_interior_points_ignore_rule(rule):
    # 손: 4e-6 은 첫 구간만, 6e-6 은 둘째만 (경계가 아니면 rule 무관)
    assert bin_index(TWO, 4e-6, 5e-9, rule) == 0
    assert bin_index(TWO, 6e-6, 5e-9, rule) == 1
    assert bin_index(TWO, 2e-6, 5e-9, rule) is None
