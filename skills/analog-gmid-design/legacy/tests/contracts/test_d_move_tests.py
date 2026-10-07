"""Phase 2 P6 계약: 참조가 test뿐인 등급 D 정의의 test 도구 이관(20260930-d-move-tests).

spec card `docs/02-design/specs/20260930-d-move-tests.spec.md` 계약 1·3·4를 판정한다. 정본 명세는 design
`gain-budget-gmid-sizing.20-dead-code-dup` v1.2 §2.1·§2.2-2·§8 P6.
계약 2(E-AST)·6(E-LIB·E-INST)·7(전체 스위트)은 auditor가 base와 병합본을 비교한다 -- 여기서 기대 해시·기대 출력을 박지 않는다.

이관 대상 5개(spec card 대상 표 그대로)와 새 위치:

* `A/tests/tools/regression_runner.py` -- `RegressionVerdict`(클래스), `_run_optimize_multistage_case`, `_REGRESSION_ENGINES`(모듈 dict),
  `run_regression_case`
* `A/tests/tools/interleave_splits.py` -- `find_interleaved_symmetric_splits`

이 파일 자체가 계약 4의 `A/tests/**` 범위 안이므로 이관 이름은 **문자열로만** 적는다(AST 참조를 만들지 않는다).

판정 넷:

* 계약 4 (GONE, 엔진): 5개 이름의 AST 참조(정의 def·class, 대입 대상 포함 Name, Attribute, import 별칭)가 `A/*.py`·
  `workspaces/run_harness.py`에서 0. 주석·문자열은 참조가 아니다. base에서는 정의가 있어 red.
* 계약 1 (이관): 새 모듈 두 파일이 있고, 각 이름이 **모듈 최상위**에 정의돼 있다(클래스는 class, dict는 대입, 나머지는 def).
  `regression_runner.py`는 `sizing_recipe`를 import하고, 두 새 모듈 어디에도 엔진 모듈(`A/*.py`) 최상위에 정의된 이름을
  다시 정의하지 않는다(엔진 코드 사본 금지 -- 계약 1 '엔진 이름을 sizing_recipe에서 import'). base에서는 파일이 없어 red.
  새 파일 이름은 기존 계약 test 파일 패턴(`probe_*.py`, `test_probe_*.py`, `*.topology.json`)과 겹치지 않는다.
* 계약 3·4 (소비자): `A/tests/**`에서 이관 이름을 import하는 곳은 그 이름의 새 모듈만 가리키고(엔진 모듈 등 다른 모듈에서 import 0),
  `import <엔진> as m` 뒤 `m.<이관 이름>` 모양의 한정 참조도 0이며, 새 모듈 밖에서 그 이름을 다시 정의하지 않는다.

oracle 대조(계획 N3.12.3):

* test_moved_names_gone_from_engine -- (a) 저장소 엔진 트리의 현재 AST가 입력, 기대값은 '참조 0'(spec card 계약 4 문장).
* test_new_tool_modules_define_moved_names -- (a) 새 모듈 파일의 AST가 입력, 기대값은 spec card 대상 표의 이름·종류(클래스/dict/함수).
* test_new_tool_modules_do_not_copy_engine_definitions -- (a) 엔진 최상위 정의 이름 집합(저장소 트리)과 새 모듈 정의의 교집합이
  공(空)이고 `regression_runner`가 `sizing_recipe`를 import한다(spec card 계약 1 문장).
* test_new_tool_file_names_do_not_match_contract_patterns -- (a) 계약 1이 나열한 패턴 셋과 새 파일 이름(대상 표)의 대조.
* test_tests_reference_moved_names_via_new_modules -- (a) `A/tests/**`의 현재 AST가 입력, 기대값은 '새 모듈 밖 참조 0'(계약 3·4).
* test_*_check_rejects_* / accepts_* -- (a) 합성 소스: 참조·정의·사본을 넣도록(또는 넣지 않도록) 손으로 만들었으므로 정답이 구성으로
  정해진다. 판정이 실제로 거부하는지(그리고 과하지 않은지) 본다.

판정하지 않은 것: `importlib.import_module("sizing_recipe")` 뒤 `getattr(m, "<이름>")` 같은 문자열 경유 참조(AST 참조가 아니다 --
spec card 계약 4가 'AST 참조'로 정했다). 옮긴 본문이 원본과 같은지는 E-AST(auditor).
"""
import ast
import fnmatch
import pathlib

import pytest

# contracts -> tests -> assets(A) -> analog-gmid-design -> skills -> 저장소 루트
_TESTS_DIR = pathlib.Path(__file__).resolve().parents[1]
_ASSETS_DIR = _TESTS_DIR.parent
_REPO_ROOT = _ASSETS_DIR.parents[2]
_TOOLS_DIR = _TESTS_DIR / "tools"
_RUN_HARNESS = _REPO_ROOT / "workspaces" / "run_harness.py"

# spec card 대상 표: 새 모듈 이름 -> {이관 이름: 정의 종류}. 종류: "class" | "def" | "assign"(모듈 dict 대입).
_MOVES = {
    "regression_runner": {
        "RegressionVerdict": "class",
        "_run_optimize_multistage_case": "def",
        "_REGRESSION_ENGINES": "assign",
        "run_regression_case": "def",
    },
    "interleave_splits": {
        "find_interleaved_symmetric_splits": "def",
    },
}
# 이관 이름 -> 새 모듈 이름
_HOME = {name: module for module, names in _MOVES.items() for name in names}
_MOVED = frozenset(_HOME)
# spec card 계약 1: 새 모듈이 엔진 이름을 import해야 하는 쪽(regression_runner -> sizing_recipe).
_REQUIRED_ENGINE_IMPORT = {"regression_runner": "sizing_recipe"}
# spec card 계약 1이 나열한 기존 계약 test 파일 패턴
_CONTRACT_FILE_PATTERNS = ("probe_*.py", "test_probe_*.py", "*.topology.json")
# 판정 범위가 공허하지 않다는 근거: 대상 표의 원 정의 파일
_REQUIRED_ENGINE_FILES = ("sizing_recipe.py", "stick_diagram.py")


def _engine_files() -> list:
    """계약 4의 엔진 범위: `A/*.py`(하위 디렉터리 제외) + `workspaces/run_harness.py`."""
    return sorted(_ASSETS_DIR.glob("*.py")) + [_RUN_HARNESS]


def _engine_module_names() -> frozenset:
    return frozenset(p.stem for p in _engine_files())


def _test_files() -> list:
    """계약 3·4의 test 범위: `A/tests/**`의 .py 전부."""
    return sorted(_TESTS_DIR.rglob("*.py"))


def _tool_path(module: str) -> pathlib.Path:
    return _TOOLS_DIR / f"{module}.py"


def _rel(path: pathlib.Path) -> str:
    return path.resolve().relative_to(_REPO_ROOT).as_posix()


def _read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def assert_engine_scope_present(files: list) -> None:
    """판정 범위가 공허하지 않다: 대상 표의 정의 파일과 run_harness가 범위 안에 실재한다."""
    names = {p.name for p in files if p.exists()}
    missing = [n for n in _REQUIRED_ENGINE_FILES + (_RUN_HARNESS.name,) if n not in names]
    assert missing == [], f"판정 범위에 있어야 할 엔진 파일이 없다: {missing}"


# --------------------------------------------------------------------------------------
# 계약 4 (GONE, 엔진): AST 참조 0
# --------------------------------------------------------------------------------------
def engine_references(source: str) -> list:
    """이관 이름 5개의 AST 참조(줄, 종류, 이름) -- 정렬. 주석·문자열·키워드 인자 이름은 참조가 아니다."""
    hits = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name in _MOVED:
            hits.add((node.lineno, "def", node.name))
        elif isinstance(node, ast.Name) and node.id in _MOVED:
            hits.add((node.lineno, "name", node.id))
        elif isinstance(node, ast.Attribute) and node.attr in _MOVED:
            hits.add((node.lineno, "attr", node.attr))
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                if alias.name.split(".")[-1] in _MOVED or (alias.asname or "") in _MOVED:
                    hits.add((node.lineno, "import", alias.name))
    return sorted(hits)


def assert_no_engine_reference(source: str, where: str) -> None:
    """판정: 엔진 소스 `source`에 이관 이름의 AST 참조가 없다."""
    hits = engine_references(source)
    assert hits == [], f"{where}: 이관 이름이 엔진에 남아 있다(줄, 종류, 이름) {hits}"


def test_moved_names_gone_from_engine():
    # oracle (a): 저장소 엔진 트리의 현재 AST가 입력, 기대값은 '참조 0'(spec card 계약 4). base에서는 정의가 있어 red.
    files = _engine_files()
    assert_engine_scope_present(files)
    offenders = {}
    for path in files:
        hits = engine_references(_read(path))
        if hits:
            offenders[_rel(path)] = hits
    assert offenders == {}, f"GONE 위반 -- 엔진에 이관 이름 참조: {offenders}"


@pytest.mark.parametrize(
    ("source", "expected_name"),
    [
        ("class RegressionVerdict:\n    ok: bool\n", "RegressionVerdict"),                          # 클래스 정의
        ("def _run_optimize_multistage_case(case, luts):\n    return {}\n", "_run_optimize_multistage_case"),
        ("_REGRESSION_ENGINES = {'optimize_multistage': None}\n", "_REGRESSION_ENGINES"),          # 모듈 dict 대입
        ("_REGRESSION_ENGINES: dict = {}\n", "_REGRESSION_ENGINES"),                                # 주석 달린 대입
        ("def run_regression_case(p, k, rel_tol=0.01):\n    pass\n", "run_regression_case"),
        ("def find_interleaved_symmetric_splits(a, b):\n    return []\n", "find_interleaved_symmetric_splits"),
        ("from regression_runner import run_regression_case\n", "run_regression_case"),            # 역 import(재수출)
        ("import interleave_splits as m\ns = m.find_interleaved_symmetric_splits(3, 3)\n",
         "find_interleaved_symmetric_splits"),                                                      # 한정 호출
        ("from x import y as RegressionVerdict\n", "y"),                                            # 별칭으로 이름 되살리기
        ("v = _REGRESSION_ENGINES['k']\n", "_REGRESSION_ENGINES"),                                  # 읽기
    ],
)
def test_engine_reference_check_rejects_synthetic_reference(source, expected_name):
    # oracle (a): 이관 이름 참조를 하나 넣어 손으로 만든 합성 엔진 소스 -> 판정이 실패해야 한다.
    with pytest.raises(AssertionError):
        assert_no_engine_reference(source, "합성 엔진 소스")
    assert expected_name in {name.split(".")[-1] for _, _, name in engine_references(source)}


@pytest.mark.parametrize(
    "source",
    [
        "# run_regression_case 는 tests/tools/regression_runner.py 로 옮겼다\nx = 1\n",   # 주석
        "doc = 'find_interleaved_symmetric_splits(3, 3) 참조'\n",                          # 문자열
        "r = make(run_regression_case=None)\n",                                            # 키워드 인자 이름
        "def optimize_multistage(topology_fn, luts):\n    return None\n",                  # 이관 대상 아닌 이름
        "RegressionVerdictLike = 1\n",                                                     # 접두만 같은 이름
    ],
)
def test_engine_reference_check_accepts_sources_without_reference(source):
    # oracle (a): 참조가 없도록 구성한 합성 소스 -> 통과해야 한다(판정이 과하지 않다).
    assert_no_engine_reference(source, "합성 엔진 소스")
    assert engine_references(source) == []


# --------------------------------------------------------------------------------------
# 계약 1 (이관): 새 모듈에 최상위 정의가 있다 / 엔진 정의 사본이 없다 / 파일 이름 패턴
# --------------------------------------------------------------------------------------
def top_level_definitions(source: str) -> dict:
    """모듈 최상위 정의 이름 -> 종류("class" | "def" | "assign")."""
    found = {}
    for node in ast.parse(source).body:
        if isinstance(node, ast.ClassDef):
            found[node.name] = "class"
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            found[node.name] = "def"
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    found[target.id] = "assign"
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value is not None:
            found[node.target.id] = "assign"
    return found


def assert_defines(source: str, expected: dict, where: str) -> None:
    """판정: `source` 최상위에 `expected`(이름 -> 종류)의 정의가 모두 그 종류로 있다."""
    found = top_level_definitions(source)
    wrong = {name: (kind, found.get(name)) for name, kind in expected.items() if found.get(name) != kind}
    assert wrong == {}, f"{where}: 최상위 정의가 없거나 종류가 다르다 (이름: (기대, 실제)) {wrong}"


def test_new_tool_modules_define_moved_names():
    # oracle (a): 새 모듈 파일 AST가 입력, 기대값은 spec card 대상 표의 이름·종류. base에서는 파일이 없어 red.
    missing = [_rel(_tool_path(m)) for m in _MOVES if not _tool_path(m).is_file()]
    assert missing == [], f"이관 위치 파일이 없다: {missing}"
    for module, expected in _MOVES.items():
        assert_defines(_read(_tool_path(module)), expected, _rel(_tool_path(module)))


def imported_modules(source: str) -> set:
    """`import X`·`from X import ...`의 X(마지막 구성 요소)."""
    mods = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            mods.update(alias.name.split(".")[-1] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods.add(node.module.split(".")[-1])
    return mods


def assert_no_engine_copy(source: str, engine_defined: set, required_import, where: str) -> None:
    """판정: `source` 최상위가 엔진 최상위 정의 이름을 다시 정의하지 않고, `required_import`(있으면)를 import한다."""
    copies = sorted(set(top_level_definitions(source)) & engine_defined)
    assert copies == [], f"{where}: 엔진 정의 이름을 다시 정의했다(사본) {copies}"
    if required_import is not None:
        assert required_import in imported_modules(source), f"{where}: {required_import} 를 import하지 않는다"


def test_new_tool_modules_do_not_copy_engine_definitions():
    # oracle (a): 엔진 최상위 정의 집합(저장소 트리)과 새 모듈 정의의 교집합이 공이고 regression_runner가
    # sizing_recipe를 import한다(spec card 계약 1). base에서는 파일이 없어 red.
    files = _engine_files()
    assert_engine_scope_present(files)
    engine_defined = set()
    for path in files:
        engine_defined |= set(top_level_definitions(_read(path)))
    assert engine_defined, "엔진 최상위 정의 집합이 비었다(판정 범위 공허)"
    for module in _MOVES:
        path = _tool_path(module)
        assert path.is_file(), f"이관 위치 파일이 없다: {_rel(path)}"
        assert_no_engine_copy(_read(path), engine_defined, _REQUIRED_ENGINE_IMPORT.get(module), _rel(path))


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        # 클래스 하나가 빠졌다
        ("def _run_optimize_multistage_case(c, l):\n    pass\n_REGRESSION_ENGINES = {}\n"
         "def run_regression_case(p, k):\n    pass\n", _MOVES["regression_runner"]),
        # dict가 함수로 바뀌었다(종류 불일치)
        ("class RegressionVerdict:\n    pass\ndef _run_optimize_multistage_case(c, l):\n    pass\n"
         "def _REGRESSION_ENGINES():\n    return {}\ndef run_regression_case(p, k):\n    pass\n", _MOVES["regression_runner"]),
        # 최상위가 아니라 함수 안에 정의(모듈 속성이 아니다)
        ("def wrapper():\n    def find_interleaved_symmetric_splits(a, b):\n        return []\n",
         _MOVES["interleave_splits"]),
        # 빈 파일
        ("", _MOVES["interleave_splits"]),
    ],
)
def test_definition_check_rejects_incomplete_module(source, expected):
    # oracle (a): 대상 표의 정의 하나를 빼거나 종류·위치를 바꾸도록 손으로 만든 합성 모듈 -> 판정이 실패해야 한다.
    with pytest.raises(AssertionError):
        assert_defines(source, expected, "합성 모듈")


def test_definition_check_accepts_complete_module():
    # oracle (a): 대상 표의 정의를 모두 그 종류로 둔 합성 모듈 -> 통과.
    source = ("from sizing_recipe import optimize_multistage\n"
              "class RegressionVerdict:\n    ok: bool = False\n"
              "def _run_optimize_multistage_case(case, luts_by_kind):\n    return {}\n"
              "_REGRESSION_ENGINES: dict = {'optimize_multistage': _run_optimize_multistage_case}\n"
              "def run_regression_case(reference_json_path, case_key, rel_tol=0.01):\n    return None\n")
    assert_defines(source, _MOVES["regression_runner"], "합성 모듈")


def test_engine_copy_check_rejects_and_accepts_synthetic_modules():
    # oracle (a): 합성 엔진 정의 집합 {optimize_multistage, _COMPENSATION_REGISTRY}. 그 이름을 새 모듈에서 다시 정의하면
    # 사본으로 거부, sizing_recipe import가 없으면 거부, import만 하면 통과 -- 구성으로 정답이 정해진다.
    engine_defined = {"optimize_multistage", "_COMPENSATION_REGISTRY"}
    copied_def = "from sizing_recipe import _COMPENSATION_REGISTRY\ndef optimize_multistage(f, l):\n    return None\n"
    copied_dict = "import sizing_recipe\n_COMPENSATION_REGISTRY = {}\n"
    no_import = "import json\ndef run_regression_case(p, k):\n    return json.loads(p)\n"
    good_from = "from sizing_recipe import optimize_multistage, _COMPENSATION_REGISTRY\ndef run_regression_case(p, k):\n    pass\n"
    good_mod = "import sizing_recipe as sr\ndef run_regression_case(p, k):\n    return sr.optimize_multistage\n"
    for bad in (copied_def, copied_dict, no_import):
        with pytest.raises(AssertionError):
            assert_no_engine_copy(bad, engine_defined, "sizing_recipe", "합성 모듈")
    for good in (good_from, good_mod):
        assert_no_engine_copy(good, engine_defined, "sizing_recipe", "합성 모듈")
    # import 요구가 없는 모듈(interleave_splits 쪽)은 사본만 본다
    assert_no_engine_copy("def find_interleaved_symmetric_splits(a, b):\n    return []\n", engine_defined, None, "합성 모듈")


def assert_file_name_outside_patterns(file_name: str, patterns: tuple) -> None:
    """판정: `file_name`이 어느 패턴과도 겹치지 않는다."""
    matched = [p for p in patterns if fnmatch.fnmatch(file_name, p)]
    assert matched == [], f"{file_name}: 기존 계약 test 파일 패턴과 겹친다 {matched}"


def test_new_tool_file_names_do_not_match_contract_patterns():
    # oracle (a): spec card 계약 1이 나열한 패턴 셋과 대상 표의 새 파일 이름 대조.
    for module in _MOVES:
        assert_file_name_outside_patterns(f"{module}.py", _CONTRACT_FILE_PATTERNS)
    # 판정이 공허하지 않다: 패턴에 걸리는 합성 이름은 거부된다.
    for bad in ("probe_regression_runner.py", "test_probe_interleave.py", "x.topology.json"):
        with pytest.raises(AssertionError):
            assert_file_name_outside_patterns(bad, _CONTRACT_FILE_PATTERNS)


# --------------------------------------------------------------------------------------
# 계약 3·4 (소비자): A/tests/** 의 참조는 새 모듈을 가리킨다
# --------------------------------------------------------------------------------------
def misdirected_test_references(source: str, own_module) -> list:
    """test 소스에서 이관 이름을 새 모듈 밖으로 가리키는 참조(줄, 종류, 이름) -- 정렬.

    `own_module`: 이 소스가 새 모듈 자체이면 그 모듈 이름(자기 정의는 허용), 아니면 None.
    센다: 새 모듈이 아닌 모듈에서의 `from X import <이름>`(상대 import 포함), `import X as m` 뒤 `m.<이름>`에서 X가 그 이름의
    새 모듈이 아닌 경우, 새 모듈 밖의 재정의(def·class·최상위 대입).
    """
    tree = ast.parse(source)
    hits = set()
    module_alias = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_alias[alias.asname or alias.name.split(".")[0]] = alias.name.split(".")[-1]
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            source_module = (node.module or "").split(".")[-1]
            for alias in node.names:
                if alias.name in _MOVED and source_module != _HOME[alias.name]:
                    hits.add((node.lineno, "import-from", f"{node.module}.{alias.name}"))
        elif isinstance(node, ast.Attribute) and node.attr in _MOVED:
            if isinstance(node.value, ast.Name) and node.value.id in module_alias:
                if module_alias[node.value.id] != _HOME[node.attr]:
                    hits.add((node.lineno, "attr", f"{module_alias[node.value.id]}.{node.attr}"))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name in _MOVED:
            if own_module != _HOME[node.name]:
                hits.add((node.lineno, "def", node.name))
    for name in set(top_level_definitions(source)) & _MOVED:
        if own_module != _HOME[name]:
            hits.add((0, "assign", name))
    return sorted(hits)


def assert_test_references_point_to_new_modules(source: str, own_module, where: str) -> None:
    """판정: test 소스의 이관 이름 참조가 모두 그 이름의 새 모듈을 가리킨다."""
    hits = misdirected_test_references(source, own_module)
    assert hits == [], f"{where}: 이관 이름을 새 모듈 밖에서 가져오거나 다시 정의한다(줄, 종류, 이름) {hits}"


def test_tests_reference_moved_names_via_new_modules():
    # oracle (a): A/tests/** 의 현재 AST가 입력, 기대값은 '새 모듈 밖 참조 0'(spec card 계약 3·4).
    files = _test_files()
    assert files, "A/tests/** 에 .py 파일이 없다(판정 범위 공허)"
    tool_modules = {_tool_path(m).resolve(): m for m in _MOVES}
    offenders = {}
    for path in files:
        hits = misdirected_test_references(_read(path), tool_modules.get(path.resolve()))
        if hits:
            offenders[_rel(path)] = hits
    assert offenders == {}, f"소비자 위반 -- 이관 이름이 새 모듈을 가리키지 않는다: {offenders}"


@pytest.mark.parametrize(
    "source",
    [
        "from sizing_recipe import (optimize_multistage, run_regression_case)\n",           # 엔진에서 import
        "from stick_diagram import find_interleaved_symmetric_splits\n",                    # 엔진에서 import
        "from sizing_recipe import RegressionVerdict as RV\n",                              # 별칭 import
        "import sizing_recipe as sr\nv = sr.run_regression_case('p', 'k')\n",               # 엔진 모듈 한정 참조
        "import stick_diagram\ns = stick_diagram.find_interleaved_symmetric_splits(3, 3)\n",
        "from regression_runner import find_interleaved_symmetric_splits\n",                # 다른 새 모듈(잘못된 집)
        "from .sizing_recipe import _REGRESSION_ENGINES\n",                                 # 상대 import
        "def run_regression_case(p, k):\n    return None\n",                                 # 새 모듈 밖 재정의
        "_REGRESSION_ENGINES = {}\n",                                                       # 새 모듈 밖 dict 재정의
    ],
)
def test_test_reference_check_rejects_misdirected_reference(source):
    # oracle (a): 이관 이름을 새 모듈 밖에서 가져오도록 손으로 만든 합성 test 소스 -> 판정이 실패해야 한다.
    with pytest.raises(AssertionError):
        assert_test_references_point_to_new_modules(source, None, "합성 test 소스")


@pytest.mark.parametrize(
    ("source", "own_module"),
    [
        ("from regression_runner import run_regression_case\nv = run_regression_case('p', 'k')\n", None),
        ("from interleave_splits import find_interleaved_symmetric_splits\n", None),
        ("import regression_runner as rr\nv = rr.RegressionVerdict\n", None),
        ("from sizing_recipe import optimize_multistage\nx = _verdict.ok\n", None),          # 이관 이름 없음
        ("# from sizing_recipe import run_regression_case\ns = 'run_regression_case'\n", None),  # 주석·문자열
        ("from sizing_recipe import optimize_multistage\n_REGRESSION_ENGINES = {}\n"
         "def run_regression_case(p, k):\n    return None\n", "regression_runner"),          # 새 모듈 자기 정의
    ],
)
def test_test_reference_check_accepts_new_module_references(source, own_module):
    # oracle (a): 새 모듈만 가리키도록 구성한 합성 소스 -> 통과해야 한다(판정이 과하지 않다).
    assert_test_references_point_to_new_modules(source, own_module, "합성 test 소스")
    assert misdirected_test_references(source, own_module) == []
