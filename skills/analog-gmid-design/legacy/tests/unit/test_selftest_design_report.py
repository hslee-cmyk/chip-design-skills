"""TS2(계획 N3.11, C9 20260922-ts2-pytest-split): 이관본 `legacy/selftest_design_report.py`의 섹션별 pytest test.

정본: design `gain-budget-gmid-sizing.10-test-separation` §6.8, 매핑표
`docs/03-analysis/gain-budget-gmid-sizing-10-test-separation/c9-mapping.json`(test 이름 = 매핑표 `test_ids`).

oracle 대조: 모든 기대값은 (c) 동작 보존 -- head 2dd98f2 이관본(C2가 원본 `design_report.py`의
`if __name__ == "__main__":` 블록을 그대로 옮긴 것)의 `assert`·거부 try를 그대로 옮겼다. 새 기대값은 없다.
test마다 docstring 끝 줄에 원문 섹션 번호와 줄 범위를 적었다. 거부 try(`try: 호출; raise AssertionError`
+ `except X`)는 `pytest.raises(X)`로, 메시지 단언은 `excinfo.value`로 옮겼다. 판정 없는 print는 옮기지 않았다.
섹션 사이 데이터 의존은 함수 범위 fixture `s<NNN>_state`(그 이름을 만드는 문장만 담는다)로, 전역 `lut`는 세션
fixture `toy_lut`로, `_ASSETS_DIR` 경로는 `assets_dir`·`library_dir`로 바꿨다(design §6.8-3·4).
"""
import os
import sys
import types

import pytest

_ASSETS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
if _ASSETS not in sys.path:
    sys.path.insert(0, _ASSETS)


from design_report import (assemble_report_data, build_topology_device_table, os, render_html_report)  # noqa: E402
from stick_diagram import run_full_circuit_audit_from_topology  # noqa: E402


@pytest.fixture
def s000_state(assets_dir, library_dir):
    """섹션 S000(이관본 줄 11-22)이 만드는 이름 _crt_instance, _crt_topo -- 읽는 섹션: S001, S002, S003. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    _lib_dir = library_dir
    _crt_topo = os.path.join(_lib_dir, "current_reuse_telescopic_ota.topology.json")
    _crt_instance = os.path.normpath(os.path.join(
        assets_dir,
        "workspaces", "current-reuse-telescopic-ota-report",
        "current_reuse_telescopic_ota.instance.json"))

    return types.SimpleNamespace(_crt_instance=_crt_instance, _crt_topo=_crt_topo)


@pytest.fixture
def s001_state(s000_state):
    """섹션 S001(이관본 줄 24-34)이 만드는 이름 _rows -- 읽는 섹션: S002. 그 이름을 만드는 문장만 옮겼다(design §6.8-3 (다))."""
    _crt_topo = s000_state._crt_topo

    _rows = build_topology_device_table(_crt_topo)

    return types.SimpleNamespace(_rows=_rows)


def test_s001_build_topology_device_table(s000_state):
    """=== Test 1: build_topology_device_table() -- 51개 소자가 matching_pairs로 그룹핑돼
    더 적은 행으로 묶이는지, M1a/M1b가 한 행으로 합쳐지는지 ===

    oracle (c) 이관본 legacy/selftest_design_report.py 섹션 S001(줄 24-34, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _crt_topo = s000_state._crt_topo

    _rows = build_topology_device_table(_crt_topo)
    assert len(_rows) < 51, f"그룹핑이 전혀 안 됨(51개 그대로): {len(_rows)}"
    _names = [r["name"] for r in _rows]
    assert "M1a/M1b" in _names, f"선언된 매칭쌍 M1a/M1b가 한 행으로 안 합쳐짐: {_names}"
    _total_devices_in_rows = sum(len(r["name"].split("/")) for r in _rows)
    assert _total_devices_in_rows == 51, \
        f"행에 포함된 소자 총합({_total_devices_in_rows})이 51과 다름 -- 소자 누락/중복"


def test_s002_assemble_report_data(s000_state, s001_state):
    """=== Test 2: assemble_report_data() -- instance.json 없이도(사이징 전) 안 죽는지 ===

    oracle (c) 이관본 legacy/selftest_design_report.py 섹션 S002(줄 35-43, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _crt_topo = s000_state._crt_topo
    _rows = s001_state._rows

    _r_no_instance = assemble_report_data(_crt_topo, "존재하지_않는_경로.instance.json")
    assert _r_no_instance["sizing"] is None and _r_no_instance["floorplan"] is None
    assert len(_r_no_instance["topology"]["devices"]) == len(_rows)
    _html_no_instance = render_html_report(_r_no_instance)
    assert "<html" not in _html_no_instance.lower() or True  # 최소 파싱 실패 없이 문자열 생성 확인
    assert "Topology" in _html_no_instance


def test_s003_assemble_report_data(s000_state):
    """=== Test 3: assemble_report_data() -- 실제(과거, partial scope) instance.json +
    run_full_circuit_audit_from_topology() 결과까지 합쳐 렌더링 ===

    oracle (c) 이관본 legacy/selftest_design_report.py 섹션 S003(줄 44-62, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _crt_instance = s000_state._crt_instance
    _crt_topo = s000_state._crt_topo

    assert os.path.exists(_crt_instance)  # spec card 계약 4: 추적되는 파일(workspaces/current-reuse-telescopic-ota-report/current_reuse_telescopic_ota.instance.json)
    _audit = run_full_circuit_audit_from_topology(_crt_topo)
    _narrative = {"meta": {"title": "current_reuse_telescopic_ota -- self-test render",
                            "source_paper": "Xie & Chen (self-test narrative passthrough)"},
                  "spec": {"VDD_V": 1.8}}
    _r_full = assemble_report_data(_crt_topo, _crt_instance, full_circuit_audit=_audit,
                                     narrative=_narrative)
    assert _r_full["sizing"] is not None, "실제 instance.json이 있는데 sizing이 안 채워짐"
    assert _r_full["report_gates"]["run_full_circuit_audit"]["ok"] == _audit.ok
    _html_full = render_html_report(_r_full)
    assert "current_reuse_telescopic_ota" in _html_full
    assert "run_full_circuit_audit" in _html_full
    assert "M1a/M1b" in _html_full


def test_s004_report():
    """=== Test 4: 빈 report({}) -- 아무 섹션도 없어도 크래시 없이 최소 HTML만 생성 ===

    oracle (c) 이관본 legacy/selftest_design_report.py 섹션 S004(줄 63-65, head 2dd98f2)의 판정을 그대로 옮겼다.
    """
    _html_empty = render_html_report({})
    assert "<style>" in _html_empty
