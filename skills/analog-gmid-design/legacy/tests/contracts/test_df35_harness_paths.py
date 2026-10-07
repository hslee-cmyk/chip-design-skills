"""Phase 2 DF-35 계약: 하네스 `workspaces/run_harness.py`의 경로를 `__file__`에서 유도한다(20260930-df35-harness-paths).

spec card `docs/02-design/specs/20260930-df35-harness-paths.spec.md` 계약 1~4를 판정한다. 계약 5(E-INST 동작 보존·전체
스위트)는 auditor가 base와 병합본을 실행해 비교한다 -- 여기서 기대 해시를 박지 않는다.

* 계약 1: `run_harness.py`의 AST 문자열 상수(docstring 제외) 중 Windows 절대 경로(`^[A-Za-z]:[\\\\/]`)와 POSIX 절대 경로
  (`/`로 시작하고 경로 구획이 둘 이상)가 0개. 주석은 AST에 없으므로 대상이 아니다.
* 계약 2: `WORKSPACES_DIR` = 그 `run_harness.py`가 있는 디렉터리, `ASSETS_DIR` = 저장소 루트 아래 `skills/analog-gmid-design/assets`.
* 계약 3: `run_harness` import가 `sys.path`에 넣은 assets 경로 = 계약 2의 `ASSETS_DIR`(다른 체크아웃 경로가 들어가지 않는다).
* 계약 4: `LIBRARY_DIR`·`LUTFILE`은 계약 2의 `ASSETS_DIR` 아래.

피검 모듈은 **이 체크아웃의** `workspaces/run_harness.py` 파일을 `importlib.util.spec_from_file_location`으로 새 이름에 로드한다 --
같은 pytest 세션의 다른 test가 `run_harness`(또는 다른 체크아웃의 엔진 모듈)를 먼저 import했어도 이 판정은 그 캐시와 무관하다.
이 파일은 피검 로드 전에 엔진 모듈을 import하지 않는다. 로드가 새로 들인 엔진·하네스 모듈(`sys.modules`)과 `sys.path`는 fixture
끝에 되돌려 같은 세션의 다른 test를 흐리지 않는다.

base에서 계약 1은 어디서나 red, 계약 2~4는 메인 체크아웃이 아닌 체크아웃(test worktree·격리 복제본)에서 red이고 병합본에서 green이다.

oracle 대조(계획 N3.12.3):

* test_harness_source_has_no_absolute_path_constants -- (a) 저장소의 현재 `run_harness.py` AST가 입력이고 기대값은 '0건'(계약 1).
* test_absolute_path_check_rejects_* / accepts_* -- (a) 합성 소스(spec card '거부해야 할 입력'): 절대 경로 상수는 발견, 상대 경로·
  `os.path.join` 식·주석·docstring 예시는 발견 아님.
* test_harness_paths_* / test_harness_sys_path_* -- (a) 구성: 기대 경로는 이 test 파일 자신의 위치(`__file__`)에서 저장소 루트를
  구해 만든다. 피검 모듈의 상수를 기대값으로 쓰지 않는다(spec card 'oracle 종류와 출처').
"""
import ast
import collections
import importlib.util
import os
import pathlib
import re
import sys

import pytest

# contracts(0) -> tests(1) -> legacy(2) -> analog-gmid-design(3) -> skills(4) -> 저장소 루트(5)
# 2026-10-07 legacy 이동: 엔진 소스·하네스는 legacy/, 공용 입력(library·LUT)은 assets/ (LEGACY.md).
_THIS_FILE = pathlib.Path(__file__).resolve()
_REPO_ROOT = _THIS_FILE.parents[5]
_EXPECTED_ASSETS = _REPO_ROOT / "skills" / "analog-gmid-design" / "assets"
_EXPECTED_ENGINE = _REPO_ROOT / "skills" / "analog-gmid-design" / "legacy"
_EXPECTED_WORKSPACES = _EXPECTED_ENGINE / "workspaces"
_HARNESS_FILE = _EXPECTED_WORKSPACES / "run_harness.py"
_LOADED_NAME = "_df35_run_harness_under_test"

# 계약 1의 절대 경로 모양(spec card 계약 1 문장). POSIX는 `/`로 시작하고 구획이 둘 이상인 것(`/s`·`/` 같은 단위·구분 문자열 제외).
_WINDOWS_ABS = re.compile(r"^[A-Za-z]:[\\/]")
_POSIX_ABS = re.compile(r"^/[^/\s]+/[^\s]*")


def _norm(path) -> str:
    return os.path.normcase(os.path.realpath(str(path)))


def _is_under(path, root) -> bool:
    p, r = _norm(path), _norm(root)
    try:
        return os.path.commonpath([p, r]) == r
    except ValueError:  # 드라이브가 다르다
        return False


# --------------------------------------------------------------------------------------
# 계약 1: 문자열 상수에 절대 경로 없음
# --------------------------------------------------------------------------------------
def _docstring_nodes(tree: ast.AST) -> set:
    """모듈·클래스·함수 docstring 상수 노드의 id 집합(계약 1 대상 아님)."""
    ids = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                ids.add(id(body[0].value))
    return ids


def absolute_path_constants(source: str) -> list:
    """소스의 문자열 상수(docstring 제외) 중 절대 경로 모양인 것의 줄 번호 목록 -- 정렬."""
    tree = ast.parse(source)
    skip = _docstring_nodes(tree)
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in skip:
            if _WINDOWS_ABS.match(node.value) or _POSIX_ABS.match(node.value):
                hits.append(node.lineno)
    return sorted(hits)


def assert_no_absolute_path_constant(source: str, where: str) -> None:
    """판정: `source`의 문자열 상수에 절대 경로가 없다."""
    hits = absolute_path_constants(source)
    assert hits == [], f"{where}: 절대 경로 문자열 상수가 있다(줄) {hits}"


def test_harness_source_has_no_absolute_path_constants():
    # oracle (a): 저장소의 현재 run_harness.py가 입력, 기대값은 '절대 경로 상수 0'(계약 1).
    assert _HARNESS_FILE.is_file(), f"판정 대상이 없다: {_HARNESS_FILE}"
    assert_no_absolute_path_constant(_HARNESS_FILE.read_text(encoding="utf-8"), "workspaces/run_harness.py")


@pytest.mark.parametrize(
    "source",
    [
        'sys.path.insert(0, r"C:\\x\\y")\n',                  # Windows 역슬래시(raw)
        'ASSETS_DIR = "D:/a"\n',                              # Windows 슬래시
        'ROOT = "/home/u/repo"\n',                            # POSIX
        'p = os.path.join("C:\\\\Users\\\\u", "assets")\n',   # join 인자 안의 절대 경로도 상수다
        'def f():\n    return "/opt/repo/workspaces"\n',      # 함수 안
        'x = f"C:/Users/{name}/repo"\n',                      # f-string 상수 부분
    ],
)
def test_absolute_path_check_rejects_synthetic_source(source):
    # oracle (a): 절대 경로 상수를 넣어 손으로 만든 합성 소스 -> 발견(판정 실패)해야 한다.
    with pytest.raises(AssertionError):
        assert_no_absolute_path_constant(source, "합성 소스")
    assert absolute_path_constants(source) != []


@pytest.mark.parametrize(
    "source",
    [
        'LIB = "library"\nLUT = "sky130_nfet_pfet_lut_sample.npz"\n',                          # 상대 경로
        'A = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "skills")\n',      # join 식
        '# sys.path.insert(0, r"C:\\x\\y")\nx = 1\n',                                          # 주석
        '"""예: C:\\\\Users\\\\u\\\\repo 또는 /home/u/repo 에서 실행"""\nx = 1\n',              # 모듈 docstring
        'def f():\n    """C:/Users/u/repo 예시"""\n    return 1\n',                            # 함수 docstring
        'msg = "see C:/x for details"\nunit = "/s"\nsep = "/"\n',                              # 앞이 경로가 아님·단위 문자열
    ],
)
def test_absolute_path_check_accepts_sources_without_absolute_path(source):
    # oracle (a): 절대 경로 상수가 없도록 구성한 합성 소스 -> 통과해야 한다(판정이 과하지 않다).
    assert_no_absolute_path_constant(source, "합성 소스")
    assert absolute_path_constants(source) == []


# --------------------------------------------------------------------------------------
# 계약 2~4: 이 체크아웃의 run_harness를 새 이름으로 로드
# --------------------------------------------------------------------------------------
def _is_engine_module(module) -> bool:
    """이 로드가 새로 들인 모듈 중 되돌릴 것: 파일이 어느 체크아웃의 assets·workspaces 디렉터리에 있는 것."""
    path = getattr(module, "__file__", None)
    if not path:
        return False
    parts = pathlib.PurePath(os.path.abspath(path)).parts
    lowered = [p.lower() for p in parts]
    in_assets = any(lowered[i:i + 2] in (["analog-gmid-design", "assets"], ["analog-gmid-design", "legacy"])
                    for i in range(len(lowered) - 1))
    return in_assets or "workspaces" in lowered


@pytest.fixture(scope="module")
def loaded_harness():
    """이 체크아웃의 run_harness.py를 새 이름으로 로드한다. 반환: (모듈, 로드가 sys.path에 더한 항목 목록).

    로드 전에 기대 ASSETS_DIR를 sys.path에서 잠시 빼 둔다 -- 조건부 삽입(`if ... not in sys.path`)이어도 로드가
    무엇을 넣는지가 드러나게 한다. 끝나면 sys.path와 새로 들인 엔진·하네스 모듈을 되돌린다.
    """
    assert _HARNESS_FILE.is_file(), f"피검 파일이 없다: {_HARNESS_FILE}"
    saved_path = list(sys.path)
    saved_modules = set(sys.modules)
    expected_dirs = {_norm(_EXPECTED_ASSETS), _norm(_EXPECTED_ENGINE)}
    sys.path[:] = [p for p in sys.path if not (p and _norm(p) in expected_dirs)]
    before = collections.Counter(sys.path)
    spec = importlib.util.spec_from_file_location(_LOADED_NAME, str(_HARNESS_FILE))
    module = importlib.util.module_from_spec(spec)
    sys.modules[_LOADED_NAME] = module
    try:
        spec.loader.exec_module(module)
        added = list((collections.Counter(sys.path) - before).elements())
        yield module, added
    finally:
        sys.path[:] = saved_path
        for name in set(sys.modules) - saved_modules:
            if name == _LOADED_NAME or _is_engine_module(sys.modules[name]):
                del sys.modules[name]


def assert_same_directory(actual, expected, what: str) -> None:
    """판정: `actual`이 `expected`와 같은 실제 디렉터리다."""
    assert isinstance(actual, (str, os.PathLike)), f"{what}: 경로가 아니다 {actual!r}"
    assert os.path.isdir(actual), f"{what}: 디렉터리가 아니다(다른 체크아웃 또는 없는 경로) {actual!r}"
    assert os.path.samefile(actual, expected), f"{what}: {actual!r} != 기대 {str(expected)!r}"


def assert_path_under(actual, root, what: str) -> None:
    """판정: `actual`이 `root` 아래 경로다(정규화 비교)."""
    assert isinstance(actual, (str, os.PathLike)), f"{what}: 경로가 아니다 {actual!r}"
    assert _is_under(actual, root), f"{what}: {actual!r} 가 기대 {str(root)!r} 아래가 아니다"


def assert_added_assets_paths_are(added: list, expected_assets) -> None:
    """판정: 로드가 sys.path에 더한 `expected_assets`와 끝 세 구획이 같은 경로(예 `.../analog-gmid-design/legacy`)가
    있고, 전부 기대 경로다."""
    tail = [s.lower() for s in pathlib.PurePath(os.path.normpath(str(expected_assets))).parts[-3:]]
    assets_like = [p for p in added
                   if pathlib.PurePath(os.path.normpath(p)).parts[-3:] and
                   [s.lower() for s in pathlib.PurePath(os.path.normpath(p)).parts[-3:]]
                   == tail]
    assert assets_like, f"로드가 sys.path에 assets 경로를 넣지 않았다(더한 항목 {added})"
    wrong = [p for p in assets_like if _norm(p) != _norm(expected_assets)]
    assert wrong == [], f"다른 체크아웃의 assets 경로가 sys.path에 들어갔다 {wrong} (기대 {str(expected_assets)!r})"


def test_expected_paths_exist():
    # 판정 범위가 공허하지 않다: test 파일 위치에서 구한 기대 경로가 실재한다.
    assert _EXPECTED_ASSETS.is_dir(), _EXPECTED_ASSETS
    assert _EXPECTED_WORKSPACES.is_dir(), _EXPECTED_WORKSPACES
    assert _HARNESS_FILE.is_file(), _HARNESS_FILE
    assert (_EXPECTED_ENGINE / "sizing_recipe.py").is_file(), "기대 엔진 디렉터리(legacy)에 엔진이 없다"


def test_harness_paths_workspaces_dir(loaded_harness):
    # oracle (a) 구성: 기대 = 이 test 파일 위치에서 구한 <루트>/workspaces (= 로드한 run_harness.py의 디렉터리). 계약 2.
    module, _ = loaded_harness
    assert_same_directory(module.WORKSPACES_DIR, _EXPECTED_WORKSPACES, "WORKSPACES_DIR")
    assert_same_directory(module.WORKSPACES_DIR, _HARNESS_FILE.parent, "WORKSPACES_DIR")


def test_harness_paths_assets_dir(loaded_harness):
    # oracle (a) 구성: 기대 = <루트>/skills/analog-gmid-design/assets. 계약 2.
    module, _ = loaded_harness
    assert_same_directory(module.ASSETS_DIR, _EXPECTED_ASSETS, "ASSETS_DIR")


def test_harness_sys_path_assets_entry(loaded_harness):
    # oracle (a) 구성: 로드가 sys.path에 넣은 엔진 경로 = 기대 legacy 디렉터리(메인 체크아웃 경로 아님). 계약 3.
    # 2026-10-07 legacy 이동: 엔진 소스가 assets/ 에서 legacy/ 로 옮겨 sys.path 항목도 legacy 다.
    _, added = loaded_harness
    assert_added_assets_paths_are(added, _EXPECTED_ENGINE)


@pytest.mark.parametrize("name", ["LIBRARY_DIR", "LUTFILE"])
def test_harness_paths_derived_under_assets(loaded_harness, name):
    # oracle (a) 구성: 파생 경로는 기대 ASSETS_DIR 아래이고 실재한다. 계약 4.
    module, _ = loaded_harness
    value = getattr(module, name)
    assert_path_under(value, _EXPECTED_ASSETS, name)
    assert os.path.exists(value), f"{name}: 없는 경로 {value!r}"


def test_path_checks_reject_wrong_paths(tmp_path):
    # oracle (a): 판정 보조 함수 자기 점검 -- 다른 디렉터리·다른 체크아웃 모양 경로를 거부한다.
    other = tmp_path / "other_checkout" / "skills" / "analog-gmid-design" / "assets"
    other.mkdir(parents=True)
    with pytest.raises(AssertionError):
        assert_same_directory(str(other), _EXPECTED_ASSETS, "합성")
    with pytest.raises(AssertionError):
        assert_same_directory(str(tmp_path / "missing"), _EXPECTED_ASSETS, "합성")
    assert_same_directory(str(_EXPECTED_ASSETS), _EXPECTED_ASSETS, "합성")
    with pytest.raises(AssertionError):
        assert_path_under(str(other / "library"), _EXPECTED_ASSETS, "합성")
    assert_path_under(str(_EXPECTED_ASSETS / "library"), _EXPECTED_ASSETS, "합성")
    with pytest.raises(AssertionError):  # 다른 체크아웃 assets가 들어감
        assert_added_assets_paths_are([str(other)], _EXPECTED_ASSETS)
    with pytest.raises(AssertionError):  # 기대와 다른 것이 함께 들어감
        assert_added_assets_paths_are([str(_EXPECTED_ASSETS), str(other)], _EXPECTED_ASSETS)
    with pytest.raises(AssertionError):  # assets 경로를 넣지 않음
        assert_added_assets_paths_are([str(tmp_path)], _EXPECTED_ASSETS)
    assert_added_assets_paths_are([str(_EXPECTED_ASSETS), str(tmp_path)], _EXPECTED_ASSETS)
