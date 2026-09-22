"""IC8 계약 test 뼈대(20260922-ts7-ic-xfail, 계획 N3.11 TS7, `00-common` CC-3).

표식 (6c, ""): oracle (d) 계획서 N4.1 IC8 행 -- 담당 Phase = `read_plan_tables(...).ic_parts["IC8"]`,
함수 이름 = `ic_test["IC8"]`, 케이스 이름은 design `10-test-separation` §6.5 선언 목록.
본문은 담당 Phase card가 채울 때까지 `pytest.fail()` 한 줄이다(§6.5 뼈대 본문 규칙). xfail은 conftest가 만든다.
"""
import pytest


@pytest.mark.gmid_ic("IC8", phase="6c", case="")
def test_unevidenced_derivation_stops_before_search():
    pytest.fail()
