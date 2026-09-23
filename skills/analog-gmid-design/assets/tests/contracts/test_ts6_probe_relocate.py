"""TS6 P2 계약: 승격하지 않는 probe 32개가 `A/tests/probes/`에 있고, 이동 깊이 보정 뒤 경로가 이동 전과 같은 곳을 가리킨다.

spec card `docs/02-design/specs/20260923-probe-relocate.spec.md` 계약 1·3·4·6을 판정한다.
정본 명세는 design `gain-budget-gmid-sizing.20-dead-code-dup` v1.1 §5·§8 P2, 실측 원자료는
`docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/probe_inventory.json`(probe 42개 전수).

판정 여섯 가지:

* (a) `A/tests/` 직속에 남은 `probe_*.py`는 승격 후보 7개뿐이다(계획 N3.11 TS6 승격 목록 =
  실측 `plan_ts6_promote_expected`). 이 7개는 P3 이후가 다루고 이 card는 건드리지 않는다.
* (b) `A/tests/probes/`에 32개가 있다. 기대 집합은 실측 42개에서 DF-21 삭제 3개(P1)와 승격 후보 7개를
  뺀 나머지로 **구성**한다 -- 디렉터리를 읽어 자기 자신을 기대값으로 삼지 않는다.
* (c) `A/tests/probes/**`의 어떤 파일에도 Windows 절대 경로 리터럴이 없다(계약 4). 판정식은 spec card의
  `^[A-Za-z]:[\\/]`를 **문자열 리터럴의 값**에 적용한다(줄 단위 정규식이 아니라 AST의 `ast.Constant`):
  `INST = (r"C:\\...\\workspaces" r"\\...json")` 처럼 암묵 연결로 두 줄에 걸친 리터럴도 값 하나로 본다.
* (d) 합성 소스로 그 판정식이 **실제로 거부**하는지 본다(통과만 보이는 게이트를 두지 않는다).
* (e) 계약 3(이동 깊이 보정): 각 probe의 `ASSETS`·`sys.path` 삽입·`library/**`·LUT npz 경로를 **파일을
  실행하지 않고** 경로식만 평가해서(아래 `resolve_path_names`) 얻고, 그 값이 이동 전 원본이 가리키던 곳과
  같은 실제 경로인지 본다. 기대값은 이동 전 형태(spec card 계약 3이 적은 `os.path.dirname(
  os.path.dirname(os.path.abspath(__file__)))`)를 **옛 자리** `A/tests/<이름>.py`에 적용해 만든다 --
  옮긴 파일의 식을 베끼지 않는다.
* (f) 계약 6(수집 불변)의 전제: `probes/` 아래에 pytest가 수집하는 이름(`test_*.py`·`*_test.py`)이 0개다.
  수집 집합 자체가 base와 같은지는 `--collect-only` 대조로 본다(이 파일 밖).

oracle 대조(계획 N3.12.3):

* test_only_promotion_candidates_remain_in_tests_root,
  test_relocated_probes_are_in_probes_dir -- (a) 구성으로 정답이 정해진 입력: 기대 이름 집합을 실측
  `probe_inventory.json`의 전수 목록에서 공표된 두 목록(삭제 3·승격 7)을 빼서 만든다. 피검 출력 없음.
* test_inventory_lists_are_the_published_ones -- (a) 실측 파일이 그 두 목록을 실제로 담고 있고 수가
  42 = 3 + 7 + 32로 맞는지(위 두 판정이 공허해지지 않게 하는 전제).
* test_probes_dir_has_no_windows_abs_path_literal -- (a) 저장소의 현재 리터럴 유무가 곧 기대값이다
  (spec card 계약 4의 목표값 0).
* test_probes_dir_has_no_collected_test_module -- (a) 파일 이름 규칙이 곧 기대값이다(계약 6의 전제).
* test_abs_path_judge_rejects_*, test_abs_path_judge_accepts_* -- (a) 합성 소스에 절대 경로를 손으로
  넣거나 뺐으므로 정답이 구성으로 정해진다.
* test_path_resolver_reads_synthetic_prologue, test_path_resolver_skips_unresolvable -- (a) 합성
  소스의 정답을 손으로 정했다(경로식 평가기 자체가 맞는지 -- 아래 (e) 판정이 공허해지지 않게).
* test_every_probe_derives_assets_from_its_own_location -- (a) 기대값 `A`를 **test 파일 자신의 위치**에서
  독립적으로 구성한다(`contracts` -> `tests` -> `assets`). dirname 중첩 수의 기대값도 `A`에서 probe까지의
  경로 성분 수로 구성한다(`tests/probes/<이름>.py` = 3).
* test_every_probe_assets_equals_pre_move_target -- (c) 기준선 대조: 이동 전 형태를 옛 자리에 적용한 값이
  기대값이다. 이동 전 형태는 spec card 계약 3에서 옮겨 적었고, 옛 자리는 계약 1이 적은 `A/tests/<이름>.py`다.
* test_assets_dir_holds_engine_entry_points -- (a) `A`의 정의(design §5의 A = assets)가 곧 기대값이다:
  그 안에 `sizing_recipe.py`와 `library/`가 있어야 `A`다.
* test_every_probe_syspath_insert_targets_exist,
  test_every_probe_library_and_lut_paths_exist -- (c) 이동 전 probe가 실제로 읽던 파일이 기대값이다
  (`A/library/**`·`A/sky130_nfet_pfet_lut_sample.npz`). 이동 후 같은 실제 경로로 해석되는지 본다.
* test_instance_paths_equal_pre_move_literal -- (c) 이동 전 리터럴이 가리키던 곳이 기대값이다
  (`<저장소 루트>/workspaces/current-reuse-telescopic-ota-report/current_reuse_telescopic_ota.instance.json`).
  그 리터럴은 base 트리의 probe에 있던 것을 옮겨 적었다.
"""
import ast
import json
import os
import pathlib
import re

import pytest

# contracts -> tests -> assets(A) -> analog-gmid-design -> skills -> 저장소 루트
_TESTS_DIR = pathlib.Path(__file__).resolve().parents[1]
_ASSETS_DIR = _TESTS_DIR.parent
_REPO_ROOT = _ASSETS_DIR.parents[2]
_PROBES_DIR = _TESTS_DIR / "probes"

_INVENTORY = (_REPO_ROOT / "docs" / "03-analysis" / "gain-budget-gmid-sizing-20-dead-code-dup"
              / "probe_inventory.json")

# spec card 계약 4의 판정식(문자열 리터럴 값의 맨 앞에 드라이브 문자).
_ABS_PATH_RE = re.compile(r"^[A-Za-z]:[\\/]")
# pytest 기본 수집 이름 규칙(계약 6의 전제).
_COLLECTED_NAME_RE = re.compile(r"^test_.*\.py$|^.*_test\.py$")

# 이동 전 probe가 `assets`를 유도하던 형태(spec card 계약 3에서 옮겨 적음). 옛 자리 `A/tests/<이름>.py`에
# 적용하면 `A`가 나온다 -- 이동 후 값과 대조할 기준선이다.
_PRE_MOVE_ASSETS_FORM = "os.path.dirname(os.path.dirname(os.path.abspath(__file__)))"
# 이동 전 probe가 쓰던 instance json 절대 경로 리터럴이 가리키던 곳(base 트리에서 옮겨 적음).
_PRE_MOVE_INSTANCE_TAIL = ("workspaces", "current-reuse-telescopic-ota-report",
                           "current_reuse_telescopic_ota.instance.json")


# --------------------------------------------------------------------------------------
# 판정 보조 1: 절대 경로 리터럴(계약 4)
# --------------------------------------------------------------------------------------
def abs_path_literals(source: str):
    """`source` 안의 문자열 리터럴 중 Windows 절대 경로로 시작하는 것: (줄 번호, 값) 목록."""
    hits = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if _ABS_PATH_RE.match(node.value):
                hits.append((node.lineno, node.value))
    return hits


def assert_no_abs_path_literal(source: str, where: str) -> None:
    """`source`에 Windows 절대 경로 리터럴이 하나도 없다."""
    hits = abs_path_literals(source)
    assert hits == [], f"{where}: Windows 절대 경로 리터럴 {hits}"


# --------------------------------------------------------------------------------------
# 판정 보조 2: 경로식 평가(계약 3) -- probe를 **실행하지 않고** 경로 줄만 해석한다
# --------------------------------------------------------------------------------------
class _Unresolvable(Exception):
    """경로식이 아니거나(계산·자료 구조) 이 평가기가 모르는 이름이다 -- 판정 대상이 아니다."""


_PATH_FUNCS = {
    ("os", "path", "dirname"): os.path.dirname,
    ("os", "path", "abspath"): os.path.abspath,
    ("os", "path", "realpath"): os.path.realpath,
    ("os", "path", "normpath"): os.path.normpath,
    ("os", "path", "join"): os.path.join,
}


def _dotted(node):
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        raise _Unresolvable("호출 대상이 이름이 아니다")
    parts.append(node.id)
    return tuple(reversed(parts))


def _eval_path(node, env):
    """`os.path.*`·문자열 리터럴·이미 아는 이름으로만 이루어진 식을 값으로 만든다. 그 밖은 거부."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in env:
            return env[node.id]
        raise _Unresolvable(f"모르는 이름 {node.id}")
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _eval_path(node.left, env) + _eval_path(node.right, env)
    if isinstance(node, ast.Call):
        fn = _PATH_FUNCS.get(_dotted(node.func))
        if fn is None or node.keywords:
            raise _Unresolvable("경로 함수가 아니다")
        return fn(*[_eval_path(a, env) for a in node.args])
    raise _Unresolvable(type(node).__name__)


def resolve_path_names(source: str, file_path: str):
    """`source`를 `file_path`에 놓았을 때 경로 줄이 만드는 값들.

    반환 `(names, syspath_inserts)`: `names`는 이름 -> 경로 문자열(모듈 최상위에서 정한 것과, 그 이름으로
    풀리는 중첩 대입), `syspath_inserts`는 `sys.path.insert(...)`에 들어간 경로 문자열 목록.
    경로식이 아닌 대입(계산·자료 구조)은 조용히 건너뛴다 -- 이 함수는 경로 줄만 본다.
    """
    tree = ast.parse(source)
    env = {"__file__": file_path}
    names, inserts = {}, []

    def _record_assign(stmt):
        if not (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1
                and isinstance(stmt.targets[0], ast.Name)):
            return
        try:
            value = _eval_path(stmt.value, env)
        except _Unresolvable:
            return
        env[stmt.targets[0].id] = value
        names[stmt.targets[0].id] = value

    for stmt in tree.body:                      # 1차: 모듈 최상위(여기서 ASSETS가 정해진다)
        _record_assign(stmt)
    for stmt in ast.walk(tree):                 # 2차: 함수 안 등 나머지(최상위 이름으로 풀리는 것만)
        _record_assign(stmt)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and not node.keywords:
            try:
                dotted = _dotted(node.func)
            except _Unresolvable:
                continue
            if dotted == ("sys", "path", "insert") and len(node.args) == 2:
                try:
                    inserts.append(_eval_path(node.args[1], env))
                except _Unresolvable:
                    continue
    return names, inserts


def dirname_depth(source: str, name: str) -> int:
    """모듈 최상위 `name = ...` 식에 중첩된 `os.path.dirname` 호출 수."""
    for stmt in ast.parse(source).body:
        if (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1
                and isinstance(stmt.targets[0], ast.Name) and stmt.targets[0].id == name):
            return sum(1 for n in ast.walk(stmt.value)
                       if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                       and n.func.attr == "dirname")
    raise AssertionError(f"모듈 최상위에 {name} 대입이 없다")


def _same_path(a, b) -> bool:
    return os.path.normcase(os.path.realpath(a)) == os.path.normcase(os.path.realpath(b))


def _inventory() -> dict:
    with open(_INVENTORY, encoding="utf-8") as fh:
        return json.load(fh)


def _published_lists():
    """실측 inventory에서 (전수 이름, 삭제 3, 승격 7)을 읽는다 -- 세 목록 모두 공표된 것이다."""
    data = _inventory()
    all_names = {p["name"] for p in data["probes"]}
    deleted = set(data["plan_df21_delete_expected"])
    promoted = set(data["plan_ts6_promote_expected"])
    return data, all_names, deleted, promoted


def _relocated_names():
    """옮긴 32개의 이름(구성: 전수 42 - 삭제 3 - 승격 7)."""
    _, all_names, deleted, promoted = _published_lists()
    return sorted(all_names - deleted - promoted)


def _py_names(directory: pathlib.Path, pattern: str) -> set:
    return {p.name for p in directory.glob(pattern)}


def _probe_sources():
    """옮긴 32개의 (이름, 새 경로, 소스) -- 기대 이름 집합으로 훑는다(디렉터리를 베끼지 않는다)."""
    for name in _relocated_names():
        path = _PROBES_DIR / f"{name}.py"
        yield name, path, path.read_text(encoding="utf-8")


# --------------------------------------------------------------------------------------
# 전제: 실측 목록이 공표된 그 목록이다(위 판정이 공허해지지 않게)
# --------------------------------------------------------------------------------------
def test_inventory_lists_are_the_published_ones():
    # oracle (a): 계획 N3.11 TS6·design §5가 이름을 댄 두 목록 그대로이고, 42 = 3 + 7 + 32로 갈린다.
    data, all_names, deleted, promoted = _published_lists()
    assert data["n_probes"] == len(all_names) == 42, data["n_probes"]
    assert len(deleted) == 3 and deleted <= all_names, sorted(deleted)
    assert len(promoted) == 7 and promoted <= all_names, sorted(promoted)
    assert deleted.isdisjoint(promoted)
    assert len(all_names - deleted - promoted) == 32


# --------------------------------------------------------------------------------------
# (a) tests/ 직속에는 승격 후보 7개만 남는다
# --------------------------------------------------------------------------------------
def test_only_promotion_candidates_remain_in_tests_root():
    # oracle (a): 기대 집합 = 실측 승격 목록 7개(이 card가 건드리지 않는 것) 그대로.
    _, _, _, promoted = _published_lists()
    expected = {f"{name}.py" for name in promoted}
    assert _py_names(_TESTS_DIR, "probe_*.py") == expected


# --------------------------------------------------------------------------------------
# (b) probes/ 에 32개가 있다
# --------------------------------------------------------------------------------------
def test_relocated_probes_are_in_probes_dir():
    # oracle (a): 기대 집합 = 실측 전수 42 - 삭제 3 - 승격 7 = 32개를 구성한 것(디렉터리를 베끼지 않는다).
    expected = {f"{name}.py" for name in _relocated_names()}
    assert len(expected) == 32
    assert _py_names(_PROBES_DIR, "probe_*.py") == expected
    # 하위 디렉터리에 숨지 않았다(계약 1: `A/tests/probes/<같은 이름>.py`).
    assert {p.name for p in _PROBES_DIR.rglob("probe_*.py")} == expected


def test_relocated_probes_are_gone_from_tests_root():
    # oracle (a): 같은 32개가 옛 자리(`A/tests/` 직속)에는 없다(계약 1의 '`A/tests/`에는 없다').
    still_there = sorted(f"{n}.py" for n in _relocated_names() if (_TESTS_DIR / f"{n}.py").exists())
    assert still_there == [], still_there


# --------------------------------------------------------------------------------------
# (c) probes/ 에 Windows 절대 경로 리터럴이 0개(계약 4)
# --------------------------------------------------------------------------------------
def test_probes_dir_has_no_windows_abs_path_literal():
    # oracle (a): spec card 계약 4의 목표값 0 -- 저장소의 현재 리터럴 유무가 곧 기대값이다.
    scanned = sorted(_PROBES_DIR.rglob("*.py"))
    assert len(scanned) == 32, [p.name for p in scanned]   # 공허한 통과 방지
    offenders = {}
    for path in scanned:
        hits = abs_path_literals(path.read_text(encoding="utf-8"))
        if hits:
            offenders[path.name] = hits
    assert offenders == {}, offenders


def test_probes_dir_has_no_collected_test_module():
    # oracle (a): pytest 기본 수집 이름 규칙이 곧 기대값이다(계약 6 '`probes/`는 수집 대상이 아니다'의 전제).
    collected = sorted(p.name for p in _PROBES_DIR.rglob("*.py") if _COLLECTED_NAME_RE.match(p.name))
    assert collected == [], collected


# --------------------------------------------------------------------------------------
# (d) 판정식이 실제로 거부한다
# --------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("source", "expected"),
    [
        # oracle (a): 합성 소스에 절대 경로 리터럴을 몇 개 넣었는지가 곧 기대값이다.
        ('ASSETS = r"C:\\Users\\HSLEE\\skills\\analog-gmid-design\\assets"\n', 1),   # 원본 probe가 쓰던 형태
        ('INST = "C:/Users/HSLEE/workspaces/x.instance.json"\n', 1),                 # 슬래시 표기
        ('P = "d:\\\\temp\\\\x.json"\n', 1),                                          # 소문자 드라이브
        ('A = r"C:\\a"\nB = r"D:/b"\n', 2),                                           # 두 개
        # 암묵 연결(두 줄에 걸친 리터럴 하나) -- 줄 단위 정규식이 놓치는 형태를 값 하나로 잡는다.
        ('INST = (r"C:\\Users\\HSLEE\\workspaces"\n        r"\\report\\x.instance.json")\n', 1),
    ],
)
def test_abs_path_judge_rejects_synthetic_absolute_paths(source, expected):
    assert len(abs_path_literals(source)) == expected
    with pytest.raises(AssertionError):
        assert_no_abs_path_literal(source, "합성 소스")


@pytest.mark.parametrize(
    "source",
    [
        # oracle (a): 절대 경로가 아닌 것을 손으로 골랐다 -> 판정이 통과해야 한다(과하지 않다).
        'ASSETS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\n',
        'P = os.path.join(ASSETS, "library", "x.topology.json")\n',
        'MSG = "C: 드라이브 얘기를 하는 문장"\n',      # 드라이브 문자 뒤에 구분자가 없다
        'P = "../workspaces/x.json"\n',                # 상대 경로
        'P = "/usr/local/share/x.json"\n',             # POSIX 절대 경로(이 판정식의 대상이 아니다)
        '"""문서 문자열 안의 C 얘기."""\n',
    ],
)
def test_abs_path_judge_accepts_relative_sources(source):
    assert abs_path_literals(source) == []
    assert_no_abs_path_literal(source, "합성 소스")


# --------------------------------------------------------------------------------------
# (e) 경로식 평가기 자체가 맞는가(아래 계약 3 판정이 공허해지지 않게)
# --------------------------------------------------------------------------------------
def test_path_resolver_reads_synthetic_prologue():
    # oracle (a): 합성 소스를 가상의 위치에 놓았을 때의 정답을 손으로 정했다.
    src = ('import os, sys\n'
           'ASSETS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\n'
           'sys.path.insert(0, ASSETS)\n'
           'sys.path.insert(0, os.path.join(ASSETS, "..", "..", "..", "workspaces"))\n'
           'TOPO = os.path.join(ASSETS, "library", "x.topology.json")\n')
    here = os.path.join("root", "skills", "s", "assets", "tests", "probes", "p.py")
    names, inserts = resolve_path_names(src, os.path.abspath(here))
    assets = os.path.abspath(os.path.join("root", "skills", "s", "assets"))
    assert names["ASSETS"] == assets
    assert names["TOPO"] == os.path.join(assets, "library", "x.topology.json")
    assert inserts[0] == assets
    assert _same_path(inserts[1], os.path.abspath(os.path.join("root", "workspaces")))
    assert dirname_depth(src, "ASSETS") == 3


def test_path_resolver_skips_unresolvable():
    # oracle (a): 경로식이 아닌 줄을 손으로 골랐다 -> 평가기가 값으로 만들지 않아야 한다(경로 줄만 본다).
    src = ('import os, tempfile\n'
           'GAIN_DB = 20.0 * 3\n'
           'TMP = os.path.join(tempfile.gettempdir(), "x.json")\n'
           'CFG = os.path.join(ASSETS, "library", cfg["topology_file"])\n')
    names, inserts = resolve_path_names(src, os.path.abspath("p.py"))
    assert names == {} and inserts == []


# --------------------------------------------------------------------------------------
# (e) 계약 3: 이동 깊이 보정 -- 옮긴 probe의 경로가 이동 전과 같은 곳을 가리킨다
# --------------------------------------------------------------------------------------
def test_assets_dir_holds_engine_entry_points():
    # oracle (a): `A`의 정의(design §5: A = `skills/analog-gmid-design/assets`)가 곧 기대값이다.
    # 아래 판정이 "아무 디렉터리"를 `A`로 인정하지 않게 하는 전제다.
    assert _ASSETS_DIR.name == "assets" and _ASSETS_DIR.parent.name == "analog-gmid-design"
    assert (_ASSETS_DIR / "sizing_recipe.py").is_file()
    assert (_ASSETS_DIR / "library").is_dir()
    assert (_ASSETS_DIR / "sky130_nfet_pfet_lut_sample.npz").is_file()


def test_every_probe_derives_assets_from_its_own_location():
    # oracle (a): 기대값을 test 파일 자신의 위치에서 독립적으로 구성한다(contracts -> tests -> assets).
    # dirname 중첩 수의 기대값도 구성이다: `A`에서 probe까지의 경로 성분 수(tests/probes/<이름>.py = 3).
    expected_depth = len(pathlib.PurePath("tests", "probes", "x.py").parts)
    assert expected_depth == 3
    checked = 0
    for name, path, src in _probe_sources():
        names, _ = resolve_path_names(src, str(path))
        assert "ASSETS" in names, f"{name}: ASSETS를 경로식으로 유도하지 않는다"
        assert _same_path(names["ASSETS"], _ASSETS_DIR), f"{name}: ASSETS={names['ASSETS']}"
        assert dirname_depth(src, "ASSETS") == expected_depth, name
        checked += 1
    assert checked == 32, checked


def test_every_probe_assets_equals_pre_move_target():
    # oracle (c): 기준선 = 이동 전 형태(spec card 계약 3에서 옮겨 적은 `_PRE_MOVE_ASSETS_FORM`)를
    # **옛 자리** `A/tests/<이름>.py`에 적용한 값. 옮긴 파일의 식을 베끼지 않는다.
    pre_src = f"import os\nASSETS = {_PRE_MOVE_ASSETS_FORM}\n"
    assert dirname_depth(pre_src, "ASSETS") == 2          # 이동 전에는 중첩이 둘이었다
    checked = 0
    for name, path, src in _probe_sources():
        old_file = str(_TESTS_DIR / f"{name}.py")          # 이동 전 자리(계약 1)
        pre_names, _ = resolve_path_names(pre_src, old_file)
        new_names, _ = resolve_path_names(src, str(path))
        assert _same_path(new_names["ASSETS"], pre_names["ASSETS"]), (
            f"{name}: 이동 전 {pre_names['ASSETS']} != 이동 후 {new_names['ASSETS']}")
        checked += 1
    assert checked == 32, checked


def test_every_probe_syspath_insert_targets_exist():
    # oracle (c): 이동 전 probe가 import를 위해 넣던 디렉터리가 기대값이다 -- 첫 삽입은 `A`(엔진 모듈 자리),
    # 나머지도 실재하는 디렉터리여야 이동이 probe를 깨뜨리지 않은 것이다.
    checked = 0
    for name, path, src in _probe_sources():
        _, inserts = resolve_path_names(src, str(path))
        assert inserts, f"{name}: sys.path 삽입을 해석하지 못했다"
        assert _same_path(inserts[0], _ASSETS_DIR), f"{name}: 첫 삽입 {inserts[0]}"
        for entry in inserts:
            assert os.path.isdir(entry), f"{name}: sys.path 삽입 대상이 없다 {entry}"
        checked += 1
    assert checked == 32, checked


def test_every_probe_library_and_lut_paths_exist():
    # oracle (c): 이동 전 probe가 실제로 읽던 파일이 기대값이다(`A/library/**`, `A/*.npz`, `A/tests/**`).
    # 보정이 빠지면 이 경로들이 `A/tests` 아래를 가리켜 존재하지 않게 된다 -- 그때 이 판정이 깨진다.
    inside_assets, missing = [], []
    for name, path, src in _probe_sources():
        names, _ = resolve_path_names(src, str(path))
        for var, value in sorted(names.items()):
            if var == "ASSETS" or not os.path.isabs(value):
                continue
            rel = os.path.relpath(os.path.realpath(value), os.path.realpath(_ASSETS_DIR))
            if rel.startswith(os.pardir):
                continue                                   # `A` 밖(저장소 루트·workspaces 등)은 여기서 안 본다
            inside_assets.append((name, var, value, rel))
            if not os.path.exists(value):
                missing.append(f"{name}:{var}={value}")
    assert missing == [], missing
    # 공허한 통과 방지: 계약 3이 이름을 댄 두 갈래(`library/**`와 LUT npz)가 실제로 판정에 들어왔다.
    assert any(rel.split(os.sep)[0] == "library" for _, _, _, rel in inside_assets), inside_assets
    assert any(value.endswith(".npz") for _, _, value, _ in inside_assets), inside_assets


def test_instance_paths_equal_pre_move_literal():
    # oracle (c): 이동 전 절대 경로 리터럴이 가리키던 곳이 기대값이다(base 트리에서 옮겨 적은 꼬리 경로).
    # 그 파일은 산출물이라 없는 복제본도 있으므로 존재가 아니라 **가리키는 곳**을 대조한다.
    expected = os.path.join(str(_REPO_ROOT), *_PRE_MOVE_INSTANCE_TAIL)
    found = {}
    for name, path, src in _probe_sources():
        names, _ = resolve_path_names(src, str(path))
        if "INST" in names:
            found[name] = names["INST"]
    assert found, "INST를 쓰는 probe를 하나도 해석하지 못했다"
    wrong = {n: v for n, v in found.items() if not _same_path(v, expected)}
    assert wrong == {}, (wrong, expected)
