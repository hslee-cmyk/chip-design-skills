"""`core/pdk_decl.py` 의 test 자리 (구조 규칙 H 1:1 -- 동작 test 는 독립 test 작성자가 core CONTRACT 9절로 쓴다).

작성자 ≠ 검증자(계획 14절): 코드 작성자는 동작 test·기대값을 쓰지 않는다. 이 파일은 그 test 가 들어올 자리다.
"""
import pytest


@pytest.mark.skip(reason="동작 test 미작성 -- 독립 test 작성자 몫(core CONTRACT 9절 read_pdk_decl)")
def test_read_pdk_decl_contract_pending():
    pass
