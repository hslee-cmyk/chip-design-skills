"""IC11 계약 test 뼈대(20260922-ts7-ic-xfail, 계획 N3.11 TS7, `00-common` CC-3).

표식 (4, "rail2"), (6a, "rail3"), (6a, "reject"): oracle (d) 계획서 N4.1 IC11 행 -- 담당 Phase = `read_plan_tables(...).ic_parts["IC11"]`,
함수 이름 = `ic_test["IC11"]`, 케이스 이름은 design `10-test-separation` §6.5 선언 목록.
본문은 담당 Phase card가 채울 때까지 `pytest.fail()` 한 줄이다(§6.5 뼈대 본문 규칙). xfail은 conftest가 만든다.
"""
import pytest


@pytest.mark.parametrize("case", [
    pytest.param("rail2", marks=pytest.mark.gmid_ic("IC11", phase="4", case="rail2")),
    pytest.param("rail3", marks=pytest.mark.gmid_ic("IC11", phase="6a", case="rail3")),
    pytest.param("reject", marks=pytest.mark.gmid_ic("IC11", phase="6a", case="reject")),
])
def test_rail_origin_shift_invariance(case):
    pytest.fail()
