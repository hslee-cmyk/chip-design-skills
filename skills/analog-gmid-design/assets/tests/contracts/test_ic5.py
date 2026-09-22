"""IC5 계약 test 뼈대(20260922-ts7-ic-xfail, 계획 N3.11 TS7, `00-common` CC-3).

표식 (1, ""): oracle (d) 계획서 N4.1 IC5 행 -- 담당 Phase = `read_plan_tables(...).ic_parts["IC5"]`,
함수 이름 = `ic_test["IC5"]`, 케이스 이름은 design `10-test-separation` §6.5 선언 목록.
본문은 담당 Phase card가 채울 때까지 `pytest.fail()` 한 줄이다(§6.5 뼈대 본문 규칙). xfail은 conftest가 만든다.
"""
import pytest


@pytest.mark.gmid_ic("IC5", phase="1", case="")
def test_gate_docstring_declares_blind_spots():
    pytest.fail()
