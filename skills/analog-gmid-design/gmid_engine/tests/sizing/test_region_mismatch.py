"""`region_mismatch(judgment) -> bool` -- interface card 20261104-eo1r4-sf1l §1 표 'mismatch' 칸(규칙 H: judge_region 를 거치지 않고 RegionJudgment 를 직접 만들어 넣는다).

oracle (식): 표 10행의 (declared, actual) -> mismatch 대응을 손으로 옮겼다. mismatch 는 declared·actual 만의 함수다.
"""
import pytest

from gmid_engine.sizing import RegionJudgment, region_mismatch

# (표 행, declared, actual, mismatch)
TABLE = [
    (1, "off", "not_judged", False),
    (2, None, "cutoff", True),
    (2, "triode", "cutoff", True),
    (3, None, "triode", True),          # 행 3·8
    (4, "triode", "triode", False),     # 행 4·9
    (5, None, "out_of_domain", True),
    (5, "triode", "out_of_domain", True),
    (6, None, "unresolved", False),
    (6, "triode", "unresolved", False),
    (7, None, "saturation", False),
    (10, "triode", "saturation", True),
]


@pytest.mark.parametrize("row,declared,actual,expected", TABLE, ids=["row%d-%s-%s" % (r[0], r[1], r[2]) for r in TABLE])
def test_region_mismatch_table(row, declared, actual, expected):
    got = region_mismatch(RegionJudgment("Mx", declared, actual))
    assert got is expected


def test_region_mismatch_ignores_device_name():
    assert region_mismatch(RegionJudgment("A", None, "cutoff")) is region_mismatch(RegionJudgment("B", None, "cutoff"))
    assert region_mismatch(RegionJudgment("A", None, "saturation")) is region_mismatch(RegionJudgment("Z9", None, "saturation"))


def test_region_mismatch_true_set_is_exactly_the_table_true_rows():
    """actual 6종 x declared 3종 전수에서 표가 정한 조합만 True."""
    true_set = {(None, "cutoff"), ("triode", "cutoff"), (None, "triode"), (None, "out_of_domain"),
                ("triode", "out_of_domain"), ("triode", "saturation")}
    actuals = ("saturation", "triode", "cutoff", "out_of_domain", "not_judged", "unresolved")
    valid = {(None, a) for a in actuals if a != "not_judged"} | {("triode", a) for a in actuals if a != "not_judged"} \
        | {("off", "not_judged")}
    for declared, actual in sorted(valid, key=repr):
        assert region_mismatch(RegionJudgment("Mx", declared, actual)) is ((declared, actual) in true_set), (declared, actual)
