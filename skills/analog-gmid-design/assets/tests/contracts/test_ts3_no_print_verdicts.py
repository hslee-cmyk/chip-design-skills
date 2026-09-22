"""TS3 contract: test 트리에서 print·logging 호출 인자로 PASS/FAIL 판정을 내지 않는다(20260922-ts3-assert-verdicts).

판정식 T(design `gain-budget-gmid-sizing.10-test-separation` §7)를 이 파일 안에서 독립 구현한다:

    T = Σ(호출 c) Σ(c의 위치·키워드 인자 안 문자열 `ast.Constant` 노드마다 한 번 -- f-string은 그 안의
        `Constant` 조각만 세고 `JoinedStr`를 따로 세지 않는다) len(re.findall(r"(?<![A-Za-z])(PASS|FAIL)(?![A-Za-z])", s))
    c = `print(...)` 또는 `<logging|logger|log|LOGGER|LOG>.<debug|info|warning|warn|error|critical|exception|log>(...)`

대상 = `A/tests/**/*.py` − `A/tests/probes/**` − `A/tests/tools/**` (A = `skills/analog-gmid-design/assets`).

oracle 대조:
* test_tree_has_no_print_verdicts -- (d) design §6.3·§7이 정한 목표값 T = 0(spec card 계약 2).
* test_verdict_counter_* -- (a) 구성으로 정답이 정해진 합성 소스: 각 소스 문자열에 토큰을 몇 개 넣었는지가
  곧 기대값이다(§7 문장을 손으로 적용한 값, 피검 코드 없음).
"""
import ast
import pathlib
import re

import pytest

_TESTS_DIR = pathlib.Path(__file__).resolve().parents[1]
_EXCLUDED_TOP_DIRS = ("probes", "tools")
_TOKEN_RE = re.compile(r"(?<![A-Za-z])(PASS|FAIL)(?![A-Za-z])")
_LOG_OBJECTS = frozenset({"logging", "logger", "log", "LOGGER", "LOG"})
_LOG_METHODS = frozenset({"debug", "info", "warning", "warn", "error", "critical", "exception", "log"})
_LEGACY_SCRIPTS = ("selftest_sizing_recipe.py", "selftest_stick_diagram.py",
                   "selftest_design_report.py", "selftest_topology_library.py")


def _is_verdict_call(node: ast.Call) -> bool:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id == "print"
    return (isinstance(func, ast.Attribute) and func.attr in _LOG_METHODS
            and isinstance(func.value, ast.Name) and func.value.id in _LOG_OBJECTS)


def _count_verdict_tokens(source: str) -> list[tuple[int, int]]:
    """(호출 줄 번호, 그 호출의 토큰 수) 목록 -- 토큰 수 0인 호출은 뺀다. 합이 T다."""
    hits = []
    for node in ast.walk(ast.parse(source)):
        if not (isinstance(node, ast.Call) and _is_verdict_call(node)):
            continue
        n = 0
        for arg in list(node.args) + [kw.value for kw in node.keywords]:
            for sub in ast.walk(arg):
                if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                    n += len(_TOKEN_RE.findall(sub.value))
        if n:
            hits.append((node.lineno, n))
    return hits


def _target_files() -> list[pathlib.Path]:
    out = []
    for path in sorted(_TESTS_DIR.rglob("*.py")):
        rel = path.relative_to(_TESTS_DIR)
        if rel.parts[0] in _EXCLUDED_TOP_DIRS:
            continue
        out.append(path)
    return out


def test_target_set_includes_legacy_scripts():
    # oracle (d): design §6.3 -- TS3 변환 대상 이관본 4개가 판정 대상에 들어 있어야 T = 0 단언이 공허하지 않다.
    rels = {p.relative_to(_TESTS_DIR).as_posix() for p in _target_files()}
    for name in _LEGACY_SCRIPTS:
        assert f"legacy/{name}" in rels, f"판정 대상에 legacy/{name}이 없다: {sorted(rels)[:20]}"


def test_tree_has_no_print_verdicts():
    # oracle (d): design §7 판정식 T의 목표값 0(spec card 계약 2).
    offenders = {}
    for path in _target_files():
        hits = _count_verdict_tokens(path.read_text(encoding="utf-8"))
        if hits:
            offenders[path.relative_to(_TESTS_DIR).as_posix()] = hits
    total = sum(n for hits in offenders.values() for _, n in hits)
    assert total == 0, f"print·logging 판정 토큰 T={total}: {offenders}"


def test_verdict_counter_rejects_single_token():
    # oracle (a): 합성 소스에 print 인자 토큰을 정확히 1개 넣었다 -> T = 1(판정기가 실제로 거부한다).
    source = 'x = 1\nprint("  [check] result PASS")\n'
    assert sum(n for _, n in _count_verdict_tokens(source)) == 1


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        # oracle (a): 각 줄의 기대값은 넣은 토큰 수 그대로(§7 규칙을 손으로 적용).
        ('v = 3\nprint(f"value={v} FAIL")\n', 1),                    # f-string 상수 조각 1개, JoinedStr 따로 안 셈
        ('ok = True\nprint(f"{\'PASS\' if ok else \'FAIL\'}")\n', 2),  # 조건식 안 상수 2개
        ('import logging\nlogging.info("FAIL here")\n', 1),           # logging 호출
        ('logger = None\nlogger.warning("x", extra="PASS")\n', 1),    # 키워드 인자
        ('print("PASSED FAILURE")\n', 0),                              # 글자 경계 -- 토큰 아님
        ('msg = "PASS"\nassert msg, "FAIL"\n', 0),                     # print·logging 호출이 아님
        ('print("OK", "SKIP")\n', 0),                                  # 다른 판정어는 T 대상 아님
    ],
)
def test_verdict_counter_rule_cases(source, expected):
    assert sum(n for _, n in _count_verdict_tokens(source)) == expected
