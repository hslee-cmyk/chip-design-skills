"""tests/structure 공용 설정.

- fixtures/ 는 위반 픽스처(가짜 소스 트리)라 수집·import 하지 않는다.
- 마커 structure_test_mapping(규칙 H)은 기본 실행에서 뺀다(-m 을 주면 그 식을 따른다). 이유: README 'H'.
- 각 test 가 기록한 '검사 대상 수'를 실행 끝 요약에 출력한다(대상 0개라도 숫자로 보고).
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ENGINE_ROOT = HERE.parents[1]                                   # .../gmid_engine
LIBRARY_DIR = ENGINE_ROOT.parent / "assets" / "library"         # library 13회로 topology
FIXTURES = HERE / "fixtures"
MAPPING_MARKER = "structure_test_mapping"

collect_ignore_glob = ["fixtures/*"]

_REPORT_KEY = pytest.StashKey[list]()


def _load_checks():
    name = "gmid_structure_checks"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, HERE / "structure_checks.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        MAPPING_MARKER + ": 규칙 H(원본 파일마다 tests/<pkg>/test_<file>.py) -- 골격 단계라 기본 실행에서 제외, "
        "-m " + MAPPING_MARKER + " 로 실행",
    )
    config.stash[_REPORT_KEY] = []


def pytest_collection_modifyitems(config, items):
    if config.option.markexpr:
        return
    keep, drop = [], []
    for it in items:
        (drop if it.get_closest_marker(MAPPING_MARKER) else keep).append(it)
    if drop:
        config.hook.pytest_deselected(items=drop)
        items[:] = keep


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    lines = config.stash.get(_REPORT_KEY, [])
    if not lines:
        return
    terminalreporter.section("gmid_engine 구조 규칙 -- 검사 대상 수")
    terminalreporter.write_line("엔진 루트: %s" % ENGINE_ROOT)
    for line in lines:
        terminalreporter.write_line(line)


@pytest.fixture(scope="session")
def checks():
    return _load_checks()


@pytest.fixture(scope="session")
def engine_root():
    return ENGINE_ROOT


@pytest.fixture(scope="session")
def library():
    """(회로 목록, 이름 -> 출처) -- 9회로 topology 에서 수집."""
    return _load_checks().library_names(LIBRARY_DIR)


@pytest.fixture(scope="session")
def fixture_tree():
    def get(rule: str, kind: str) -> Path:
        p = FIXTURES / rule / kind / "gmid_engine"
        assert p.is_dir(), "픽스처 트리 없음: %s" % p
        return p
    return get


@pytest.fixture
def report(request):
    def rec(n_targets: int, n_violations: int) -> None:
        request.config.stash[_REPORT_KEY].append(
            "%-40s 대상 %3d개, 위반 %d건" % (request.node.name, n_targets, n_violations))
    return rec
