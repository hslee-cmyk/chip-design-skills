"""규칙 H: gmid_engine/<pkg>/<file>.py 마다 tests/<pkg>/test_<file>.py, 고아 test 0.

xfail 이 아니라 누락·고아 목록을 출력하고 FAIL 한다. core 골격 단계에서는 누락이 많을 것이라
마커 structure_test_mapping 으로 기본 실행에서 뺀다(conftest.py, README 'H').
실행: pytest <이 폴더> -m structure_test_mapping
검사기 자체가 누락·고아를 거부하는지는 test_structure_rules_reject_fixtures.py 의 H 픽스처 test(기본 실행)가 본다.
"""
from __future__ import annotations

import pytest


@pytest.mark.structure_test_mapping
def test_rule_h_tests_mirror_sources(checks, engine_root, report):
    n, v = checks.check_h(engine_root)
    report(n, len(v))
    assert not v, "규칙 H 위반 %d건(원본 %d개):\n%s" % (len(v), n, "\n".join(str(x) for x in v))
