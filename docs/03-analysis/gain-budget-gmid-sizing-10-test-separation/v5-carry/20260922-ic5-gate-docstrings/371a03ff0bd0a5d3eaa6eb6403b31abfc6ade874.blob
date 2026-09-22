"""IC5 계약 test: 게이트 함수 docstring이 '검사하지 않는 것' 절과 `영역:` 한 줄을 선언한다(20260922-ic5-gate-docstrings).

계획 N4.1 IC5, `00-common` §5(+`10-test-separation` C1 개정 `없음(배치)`), design `10-test-separation` §5.6·§6.6.
표식 (1, ""): oracle (d) 계획서 N4.1 IC5 행(C6 `20260922-ts7-ic-xfail`이 단 그대로, 대조 test 대상).

대상 = 소스 분류 파일(`A/*.py`, `<저장소 루트>/workspaces/run_harness.py`)에서 이름이
`^(check_|verify_|validate_|audit_|reject_|require_)` 또는 `^load_.*_checked$`인 함수·메서드 전부(모든 깊이).
test가 실행 때 `ast.parse`로 모은다(목록을 박지 않는다). A = `skills/analog-gmid-design/assets`.

oracle 대조:
* test_gate_docstring_declares_blind_spots -- (d) 형식 규칙과 정규식은 design §5.6 원문, 영역 값 표 21행은
  design §5.6 영역 표(승인 `20260922-10-test-separation-design`), 허용 영역 문자열은 `00-common` §4
  `domain` 값 집합과 §5 게이트 함수 행(`없음(스키마)`·`없음(배치)`).
* test_format_checker_* -- (a) 구성으로 정답이 정해진 합성 docstring: 각 문자열에 규칙 위반을 넣었는지가 곧
  기대값이다(design §5.6 문장을 손으로 적용, 피검 코드 없음).
* test_target_collector_finds_all_depths -- (a) 구성으로 정답이 정해진 합성 소스: 어떤 이름의 함수를 어느
  깊이에 넣었는지가 곧 기대 대상 집합이다(design §5.6 대상 규칙을 손으로 적용).
* test_domain_table_uses_allowed_values -- (d) `00-common` §4·§5: 옮겨 적은 표의 값이 허용 문자열 안에 있다.
"""
import ast
import inspect
import pathlib
import re

import pytest

_ASSETS_DIR = pathlib.Path(__file__).resolve().parents[2]
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[5]
_HARNESS = _REPO_ROOT / "workspaces" / "run_harness.py"

# oracle (d) design §5.6 대상 이름 규칙(원문).
_TARGET_NAME_RES = (re.compile(r"^(check_|verify_|validate_|audit_|reject_|require_)"),
                    re.compile(r"^load_.*_checked$"))

# oracle (d) design §5.6 형식 규칙(원문).
_BLIND_HEAD = "검사하지 않는 것:"
_DOMAIN_HEAD = "영역:"
_DOMAIN_RE = re.compile(r"^영역:\s*(없음\((스키마|배치)\)|(dc|ac_struct|ss|ls)(\s*,\s*(dc|ac_struct|ss|ls))*)\s*(\.|$)")

# oracle (d) `00-common` §4 영역 `domain` 값 집합과 §5 게이트 함수 행의 두 '없음' 값.
_DOMAINS = frozenset({"dc", "ac_struct", "ss", "ls"})
_NONE_SCHEMA = "없음(스키마)"
_NONE_LAYOUT = "없음(배치)"
_ALLOWED = _DOMAINS | {_NONE_SCHEMA, _NONE_LAYOUT}

# oracle (d) design §5.6 영역 표(현존 21개). 키 = (파일 이름, 함수 이름), 값 = 영역 값 집합.
_DOMAIN_TABLE = {
    ("audit_current_forced.py", "audit_topology"): {_NONE_SCHEMA},
    ("sizing_recipe.py", "check_quasi_static"): {"ss"},
    ("sizing_recipe.py", "audit_l_sharing_consistency"): {"dc"},
    ("sizing_recipe.py", "audit_vsb_consistency"): {"dc"},
    ("sizing_recipe.py", "validate_no_legacy_vs_key"): {_NONE_SCHEMA},
    ("sizing_recipe.py", "validate_metric_units"): {_NONE_SCHEMA},
    ("sizing_recipe.py", "validate_theta_declaration_order"): {_NONE_SCHEMA},
    ("sizing_recipe.py", "require_declared_spec_source"): {_NONE_SCHEMA},
    ("stick_diagram.py", "check_mirror_symmetry"): {_NONE_LAYOUT},
    ("stick_diagram.py", "check_symmetry_dispositions"): {_NONE_LAYOUT},
    ("stick_diagram.py", "check_multi_leaf_hub_parity"): {_NONE_LAYOUT},
    ("stick_diagram.py", "audit_vertical_stack_id_vs_kcl"): {"dc"},
    ("stick_diagram.py", "audit_theta_root_direction"): {"dc", "ac_struct"},
    ("stick_diagram.py", "require_device_roles_reviewed"): {_NONE_SCHEMA},
    ("stick_diagram.py", "audit_vertical_stack_id_euler_feasibility"): {_NONE_LAYOUT},
    ("stick_diagram.py", "check_finger_width_compatibility"): {_NONE_LAYOUT},
    ("stick_diagram.py", "check_euler_condition"): {_NONE_LAYOUT},
    ("stick_diagram.py", "check_box_shape"): {_NONE_LAYOUT},
    ("stick_diagram.py", "check_walk_sequence"): {_NONE_LAYOUT},
    ("stick_diagram.py", "check_stick_diagram_coverage"): {_NONE_LAYOUT},
    ("stick_diagram.py", "audit_row_split"): {_NONE_LAYOUT},
}


def _is_target_name(name: str) -> bool:
    return any(r.search(name) for r in _TARGET_NAME_RES)


def _collect_targets(source: str, file_name: str) -> list[tuple[str, str, int, str | None]]:
    """(파일 이름, 함수 이름, 줄 번호, 원 docstring 또는 None) -- 모든 깊이의 함수·메서드."""
    out = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and _is_target_name(node.name):
            out.append((file_name, node.name, node.lineno, ast.get_docstring(node, clean=False)))
    return out


def _source_files() -> list[pathlib.Path]:
    return sorted(_ASSETS_DIR.glob("*.py")) + [_HARNESS]


def _stripped_lines(doc: str) -> list[str]:
    return [line.strip() for line in inspect.cleandoc(doc).splitlines()]


def _format_violations(doc: str | None) -> list[str]:
    """design §5.6 형식 위반 목록(빈 목록 = 형식 만족)."""
    if doc is None:
        return ["docstring 없음"]
    lines = _stripped_lines(doc)
    problems = []
    blind_idx = [i for i, line in enumerate(lines) if line.startswith(_BLIND_HEAD)]
    if not blind_idx:
        problems.append(f"'{_BLIND_HEAD}' 줄 없음")
    for i in blind_idx:
        after_colon = lines[i][len(_BLIND_HEAD):].strip()
        next_nonempty = next((line for line in lines[i + 1:] if line), "")
        if not after_colon and not next_nonempty:
            problems.append(f"'{_BLIND_HEAD}' 줄 {i + 1}에 내용 없음")
    domain_lines = [line for line in lines if line.startswith(_DOMAIN_HEAD)]
    if len(domain_lines) != 1:
        problems.append(f"'{_DOMAIN_HEAD}' 줄 {len(domain_lines)}개(정확히 1개여야 함)")
    for line in domain_lines:
        if not _DOMAIN_RE.match(line):
            problems.append(f"'{_DOMAIN_HEAD}' 줄이 §5.6 정규식에 맞지 않음: {line!r}")
    return problems


def _domain_values(doc: str) -> set[str]:
    """형식을 만족한 docstring의 `영역:` 값 집합(쉼표 순서 무관)."""
    line = next(line for line in _stripped_lines(doc) if line.startswith(_DOMAIN_HEAD))
    group = _DOMAIN_RE.match(line).group(1)
    if group.startswith("없음"):
        return {group}
    return {part.strip() for part in group.split(",")}


@pytest.mark.gmid_ic("IC5", phase="1", case="")
def test_gate_docstring_declares_blind_spots():
    # oracle (d): 계획 N4.1 IC5, `00-common` §5(+C1), design §5.6 형식·영역 표(spec card 계약 1~3).
    assert _HARNESS.is_file(), f"design §5.6 소스 분류 파일이 없다: {_HARNESS}"
    targets = []
    for path in _source_files():
        targets.extend(_collect_targets(path.read_text(encoding="utf-8"), path.name))

    # (1) 공허한 통과 방지.
    assert len(targets) >= 1, "IC5 대상 함수가 0개다"

    # 표의 21개가 대상 집합 안에 있어야 (3)이 공허하지 않다.
    found_keys = {(f, n) for f, n, _, _ in targets}
    missing = sorted(set(_DOMAIN_TABLE) - found_keys)
    assert not missing, f"design §5.6 영역 표의 함수가 대상에 없다({len(missing)}개): {missing}"

    # (2) 모든 대상이 §5.6 형식.
    format_bad = []
    for f, n, lineno, doc in targets:
        problems = _format_violations(doc)
        if problems:
            format_bad.append(f"{f}:{lineno} {n}: {'; '.join(problems)}")
    assert not format_bad, (f"§5.6 docstring 형식 위반 {len(format_bad)}개 / 대상 {len(targets)}개:\n"
                            + "\n".join(format_bad))

    # (3) 표의 21개는 영역 값 집합이 표와 같다. 표 밖 대상은 형식만((2)에서 끝).
    domain_bad = []
    for f, n, lineno, doc in targets:
        values = _domain_values(doc)
        expected = _DOMAIN_TABLE.get((f, n))
        if expected is not None and values != expected:
            domain_bad.append(f"{f}:{lineno} {n}: 영역 {sorted(values)} != 표 {sorted(expected)}")
    assert not domain_bad, f"§5.6 영역 표와 다른 값 {len(domain_bad)}개:\n" + "\n".join(domain_bad)


# ---- 판정기가 실제로 거부함(합성 docstring, oracle (a)) ----

_VALID_DOC = '''첫 단락.

    검사하지 않는 것: 소자 수가 0인 입력.
    영역: dc, ac_struct
    '''


def test_format_checker_accepts_valid_control():
    # oracle (a): 두 절을 규칙대로 넣은 합성 docstring -- 위반 0, 값 {dc, ac_struct}(쉼표 순서 무관).
    assert _format_violations(_VALID_DOC) == []
    assert _domain_values(_VALID_DOC) == {"dc", "ac_struct"}
    layout_doc = "검사하지 않는 것:\n  배치 밖 소자.\n영역: 없음(배치)."
    assert _format_violations(layout_doc) == []
    assert _domain_values(layout_doc) == {_NONE_LAYOUT}


def test_format_checker_rejects_missing_blind_spot_section():
    # oracle (a): '검사하지 않는 것' 절을 넣지 않은 합성 docstring -- 절 없음 위반.
    problems = _format_violations("첫 단락.\n\n영역: dc\n")
    assert f"'{_BLIND_HEAD}' 줄 없음" in problems, problems


def test_format_checker_rejects_empty_blind_spot_section():
    # oracle (a): 절 머리만 있고 콜론 뒤·다음 줄 모두 비어 있는 합성 docstring.
    problems = _format_violations("첫 단락.\n영역: ss\n검사하지 않는 것:\n")
    assert f"'{_BLIND_HEAD}' 줄 3에 내용 없음" in problems, problems


def test_format_checker_rejects_two_domain_lines():
    # oracle (a): 각각은 유효한 `영역:` 줄을 두 개 넣은 합성 docstring -- '정확히 1개' 위반 하나만.
    problems = _format_violations("첫 단락.\n검사하지 않는 것: 음수 폭.\n영역: dc\n영역: ss\n")
    assert problems == [f"'{_DOMAIN_HEAD}' 줄 2개(정확히 1개여야 함)"], problems


def test_format_checker_rejects_unknown_domain_value():
    # oracle (a): 허용 밖 값 `dc_ac`(`00-common` §4 값 집합에 없음)를 넣은 합성 docstring -- 정규식 위반 하나만.
    problems = _format_violations("첫 단락.\n검사하지 않는 것: 음수 폭.\n영역: dc_ac\n")
    assert problems == [f"'{_DOMAIN_HEAD}' 줄이 §5.6 정규식에 맞지 않음: '영역: dc_ac'"], problems


def test_format_checker_rejects_missing_docstring():
    # oracle (a): docstring이 없는 함수(get_docstring = None).
    assert _format_violations(None) == ["docstring 없음"]


# ---- 대상 수집기가 규칙대로 모음(합성 소스, oracle (a)) ----

_SYNTH_SOURCE = '''
def check_a():
    """doc a"""

def checker():
    pass

def load_topology():
    pass

def load_topology_checked():
    pass

class K:
    def validate_b(self):
        pass

    def helper(self):
        def audit_inner():
            pass

async def reject_c():
    pass

def my_verify_x():
    pass
'''


def test_target_collector_finds_all_depths():
    # oracle (a): 합성 소스에 대상 이름 규칙에 맞는 함수 5개(모듈·메서드·중첩·async·load_*_checked)와
    # 맞지 않는 4개(checker, load_topology, helper, my_verify_x)를 넣었다.
    collected = _collect_targets(_SYNTH_SOURCE, "synth.py")
    assert {name for _, name, _, _ in collected} == {
        "check_a", "load_topology_checked", "validate_b", "audit_inner", "reject_c"}
    docs = {name: doc for _, name, _, doc in collected}
    assert docs["check_a"] == "doc a"
    assert docs["validate_b"] is None


def test_domain_table_uses_allowed_values():
    # oracle (d): `00-common` §4·§5 -- 옮겨 적은 design §5.6 표 21행의 값이 허용 문자열 안에 있다.
    assert len(_DOMAIN_TABLE) == 21
    for key, values in _DOMAIN_TABLE.items():
        assert values and values <= _ALLOWED, (key, values)
