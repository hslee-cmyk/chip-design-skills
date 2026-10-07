"""TS6 P2 계약: 승격하지 않는 probe 32개가 `A/tests/probes/`에 있고, 이동 깊이 보정 뒤 경로가 이동 전과 같은 곳을 가리킨다.

spec card `docs/02-design/specs/20260923-probe-relocate.spec.md` 계약 1·2·3·4·5·6을 판정한다.
정본 명세는 design `gain-budget-gmid-sizing.20-dead-code-dup` v1.1 §5·§8 P2, 실측 원자료는
`docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/probe_inventory.json`(probe 42개 전수).

판정 여섯 가지:

* (a) `A/tests/` 직속에 남은 `probe_*.py`는 승격 후보(계획 N3.11 TS6 승격 목록 = 실측
  `plan_ts6_promote_expected`) 중 **아직 승격되지 않은 것**뿐이다. 승격 여부는 spec card
  `20260923-probe-promote-clean` 계약 1의 이름 규칙(`A/tests/unit/test_<probe 이름>.py`가 있다)이 정한다 --
  P2는 이 7개를 건드리지 않았고, P3부터 하나씩 승격본으로 바뀐다. 승격한 수·이름을 이 파일에 박지 않으므로
  남은 승격이 진행돼도 판정은 그대로다. 규칙만 보면 '원본도 승격본도 없음'이나 '둘 다 있음'을 통과시킬 수
  있어 **양방향**(후보마다 정확히 하나만 존재)과 '후보 밖 이름의 승격본 없음'을 함께 건다.
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
* (g) 계약 2(경로 줄을 뺀 나머지가 그대로)와 계약 5(운영 도구 이동): base 커밋의 blob을 기준선으로 읽어
  **바뀐 줄이 전부 경로 줄인지** 본다. 경로 줄의 정의는 spec card 계약 2에서 옮겨 적었다 --
  `os.path.*`·`sys.path.insert`를 담은 문장과 절대 경로 리터럴을 담은 문장(여러 줄에 걸치면 그 줄 전부).

oracle 대조(계획 N3.12.3):

* test_only_promotion_candidates_remain_in_tests_root,
  test_relocated_probes_are_in_probes_dir -- (a) 구성으로 정답이 정해진 입력: 기대 이름 집합을 실측
  `probe_inventory.json`의 전수 목록에서 공표된 두 목록(삭제 3·승격 7)을 빼서 만들고, 승격분은 계약 1의
  이름 규칙으로 더 뺀다(규칙에서 유도 -- 디렉터리를 읽어 자기 자신을 기대값으로 삼지 않는다). 피검 출력 없음.
* test_promotion_judgment_rejects_half_moved_and_stray_promotions -- (a) 합성 디렉터리: 원본·승격본을 손으로
  만들었으므로 정답이 구성으로 정해진다. 세 결함(둘 다 있음·둘 다 없음·후보 밖 승격본)을 실제로 거부하는지 본다.
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
* test_path_statement_marker_*, test_only_path_lines_judge_rejects_* -- (a) 합성 소스에서 어느 줄이
  경로 줄인지 손으로 정했고, 경로 줄이 아닌 변경을 넣어 판정이 **실제로 거부**하는지 본다.
* test_base_blob_reader_reads_the_base_tree -- (a) base 커밋에 그 경로가 있다는 사실이 기대값이다
  (아래 기준선 대조가 빈 문자열로 공허하게 통과하지 않게 하는 전제).
* test_moved_tool_matches_base_except_path_lines --(c) 기준선 = base 커밋의 blob 그 자체(계약 2·5의
  '경로 줄을 뺀 나머지가 바이트 그대로'). 새 기대값을 만들지 않는다.
* test_moved_tool_is_in_tools_dir, test_moved_tool_paths_equal_pre_move_targets -- (a)/(c) 계약 5의
  새 자리와, 이동 전 형태를 옛 자리에 적용한 경로가 기대값이다(계약 3과 같은 방식).
"""
import ast
import difflib
import json
import os
import pathlib
import re
import subprocess

import pytest

# contracts -> tests -> assets(A) -> analog-gmid-design -> skills -> 저장소 루트
_TESTS_DIR = pathlib.Path(__file__).resolve().parents[1]
_ASSETS_DIR = _TESTS_DIR.parent
_REPO_ROOT = _ASSETS_DIR.parents[2]
_PROBES_DIR = _TESTS_DIR / "probes"
_TOOLS_DIR = _TESTS_DIR / "tools"
_UNIT_DIR = _TESTS_DIR / "unit"
# 승격본 자리의 이름 규칙(spec card `20260923-probe-promote-clean` 계약 1): probe `<이름>`의 승격본은
# `A/tests/unit/test_<이름>.py`다(계약 1의 `<주제>`는 이름에서 `probe_` 접두사를 뺀 것이므로 `test_` + 이름).
_PROMOTED_PREFIX = "test_"
_TESTS_REL = _TESTS_DIR.relative_to(_REPO_ROOT).as_posix()

# 계약 5의 운영 도구(spec card가 이름을 댄 것).
_TOOL_NAME = "derive_achievable_bounds.py"
# 이 change id의 base -- gate/master HEAD이자 spec card 개정 커밋(계약 2·5의 '원본 바이트'가 여기 있다).
_BASE_COMMIT = "939f926fe97ba27f9c8d5110a089253c5a4501e3"

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


# --------------------------------------------------------------------------------------
# 판정 보조 3: base 기준선 대조(계약 2·5) -- 기대값은 base 커밋의 blob 그 자체다
# --------------------------------------------------------------------------------------
def base_blob_text(rel_path: str) -> str:
    """base 커밋에 있던 `rel_path`의 내용(개행은 정규화해서 줄 목록 비교에 쓴다)."""
    proc = subprocess.run(["git", "-C", str(_REPO_ROOT), "show", f"{_BASE_COMMIT}:{rel_path}"],
                          capture_output=True)
    assert proc.returncode == 0, (
        f"base {_BASE_COMMIT[:7]}의 {rel_path}를 읽지 못했다: {proc.stderr.decode('utf-8', 'replace')}")
    text = proc.stdout.decode("utf-8")
    assert text.strip(), f"{rel_path}: base 내용이 비었다"
    return text


def path_statement_lines(source: str) -> set:
    """`source`에서 **경로 줄**의 줄 번호(spec card 계약 2의 정의를 옮긴 것).

    경로 줄 = `os.path.*`나 `sys.path.insert`를 담은 문장의 줄과, 절대 경로 리터럴을 담은 문장의 줄.
    문장이 여러 줄에 걸치면(암묵 연결 등) 그 문장이 차지한 줄을 모두 센다.
    """
    def _is_path_stmt(stmt) -> bool:
        for sub in ast.walk(stmt):
            if isinstance(sub, ast.Call):
                try:
                    dotted = _dotted(sub.func)
                except _Unresolvable:
                    continue
                if dotted[:2] == ("os", "path") or dotted == ("sys", "path", "insert"):
                    return True
            if (isinstance(sub, ast.Constant) and isinstance(sub.value, str)
                    and _ABS_PATH_RE.match(sub.value)):
                return True
        return False

    marked = set()
    for stmt in ast.walk(ast.parse(source)):
        if isinstance(stmt, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Expr)) and _is_path_stmt(stmt):
            marked.update(range(stmt.lineno, (stmt.end_lineno or stmt.lineno) + 1))
    return marked


def non_path_line_changes(base_source: str, new_source: str):
    """base -> new 에서 바뀐 줄 중 **경로 줄이 아닌** 것: (쪽, 줄 번호, 내용) 목록."""
    base_lines, new_lines = base_source.splitlines(), new_source.splitlines()
    base_ok, new_ok = path_statement_lines(base_source), path_statement_lines(new_source)
    offenders = []
    matcher = difflib.SequenceMatcher(None, base_lines, new_lines, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        for i in range(i1, i2):
            if (i + 1) not in base_ok:
                offenders.append(("base", i + 1, base_lines[i]))
        for j in range(j1, j2):
            if (j + 1) not in new_ok:
                offenders.append(("new", j + 1, new_lines[j]))
    return offenders


def assert_only_path_lines_changed(base_source: str, new_source: str, where: str) -> None:
    """계약 2·5: 바뀐 줄이 전부 경로 줄이고 그 밖의 줄은 모두 같다."""
    offenders = non_path_line_changes(base_source, new_source)
    assert offenders == [], f"{where}: 경로 줄이 아닌 변경 {offenders}"


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


def promoted_probe_names(unit_dir: pathlib.Path) -> set:
    """이름 규칙으로 읽은 **승격 완료** probe 이름(`unit/test_<이름>.py` -> `<이름>`)."""
    return {p.stem[len(_PROMOTED_PREFIX):] for p in unit_dir.glob(f"{_PROMOTED_PREFIX}probe_*.py")}


def assert_promotion_is_all_or_nothing(candidates, tests_root: pathlib.Path,
                                       unit_dir: pathlib.Path) -> None:
    """판정: 승격 후보마다 원본(`tests/<이름>.py`)과 승격본(`unit/test_<이름>.py`) 중 **정확히 하나**만 있다.

    둘 다 있으면 원본을 안 지운 것이고, 둘 다 없으면 판정 없이 사라진 것이다 -- 둘 다 '옮기다 만 상태'라
    통과시키지 않는다(이 판정의 값은 한쪽만 하고 멈춘 것을 잡는 데 있다).
    """
    state = {name: ((tests_root / f"{name}.py").exists(),
                    (unit_dir / f"{_PROMOTED_PREFIX}{name}.py").exists())
             for name in candidates}
    both = sorted(n for n, (orig, prom) in state.items() if orig and prom)
    neither = sorted(n for n, (orig, prom) in state.items() if not orig and not prom)
    assert both == [], f"원본과 승격본이 둘 다 있는 probe {both} -- 승격은 '원본 삭제'까지가 한 단위다"
    assert neither == [], f"원본도 승격본도 없는 probe {neither} -- 판정으로 옮기지 않고 사라졌다"


def assert_unit_promotions_are_candidates(unit_dir: pathlib.Path, candidates) -> None:
    """판정: `unit/`의 승격본은 전부 **공표된 승격 후보**의 것이다(후보 밖 이름이 끼어들지 않는다)."""
    stray = sorted(promoted_probe_names(unit_dir) - set(candidates))
    assert stray == [], f"승격 후보가 아닌 이름의 승격본 {stray} -- 승격 목록은 계획 N3.11 TS6이 정한다"


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
# (a) tests/ 직속에는 승격 후보 중 **아직 승격 안 된 것**만 남는다
# --------------------------------------------------------------------------------------
def test_only_promotion_candidates_remain_in_tests_root():
    # oracle (a): 기대 집합 = 공표된 승격 후보 7개 - **승격이 끝난 것**. 끝났는지는 spec card
    # `20260923-probe-promote-clean` 계약 1의 이름 규칙(`unit/test_<이름>.py`)이 정한다 -- 승격한 수나
    # 이름을 이 파일에 박지 않으므로 P3b 이후 승격이 더 일어나도 그대로 성립한다. 규칙만으로는 한쪽만
    # 한 상태를 통과시킬 수 있으므로 양방향 판정을 같이 건다(정확히 하나만 존재 + 후보 밖 승격본 없음).
    _, _, _, promoted = _published_lists()
    expected = {f"{name}.py" for name in promoted - promoted_probe_names(_UNIT_DIR)}
    assert _py_names(_TESTS_DIR, "probe_*.py") == expected
    assert_promotion_is_all_or_nothing(promoted, _TESTS_DIR, _UNIT_DIR)
    assert_unit_promotions_are_candidates(_UNIT_DIR, promoted)


def test_promotion_judgment_rejects_half_moved_and_stray_promotions(tmp_path):
    # oracle (a): 합성 디렉터리 -- 어떤 파일을 만들었는지가 곧 정답이다. 승격 후보 두 개를 가정하고
    # (a) 둘 다 있음 (b) 둘 다 없음 (c) 후보가 아닌 이름의 승격본 세 경우를 만들어 거부를 본다.
    candidates = {"probe_alpha", "probe_beta"}
    tests_root, unit_dir = tmp_path / "tests", tmp_path / "tests" / "unit"
    unit_dir.mkdir(parents=True)
    # 정상: alpha는 승격본만, beta는 원본만.
    (unit_dir / "test_probe_alpha.py").write_text("# 합성 승격본\n", encoding="utf-8")
    (tests_root / "probe_beta.py").write_text("# 합성 원본\n", encoding="utf-8")
    assert_promotion_is_all_or_nothing(candidates, tests_root, unit_dir)
    assert_unit_promotions_are_candidates(unit_dir, candidates)
    assert promoted_probe_names(unit_dir) == {"probe_alpha"}
    # (a) 둘 다 있음 -- 승격본을 만들고 원본을 안 지운 상태.
    (tests_root / "probe_alpha.py").write_text("# 합성 원본(안 지움)\n", encoding="utf-8")
    with pytest.raises(AssertionError):
        assert_promotion_is_all_or_nothing(candidates, tests_root, unit_dir)
    (tests_root / "probe_alpha.py").unlink()
    # (b) 둘 다 없음 -- 승격본 없이 원본만 사라진 상태.
    (tests_root / "probe_beta.py").unlink()
    with pytest.raises(AssertionError):
        assert_promotion_is_all_or_nothing(candidates, tests_root, unit_dir)
    (tests_root / "probe_beta.py").write_text("# 합성 원본\n", encoding="utf-8")
    # (c) 후보가 아닌 이름의 승격본.
    (unit_dir / "test_probe_gamma.py").write_text("# 합성 승격본(후보 아님)\n", encoding="utf-8")
    with pytest.raises(AssertionError):
        assert_unit_promotions_are_candidates(unit_dir, candidates)
    assert_promotion_is_all_or_nothing(candidates, tests_root, unit_dir)


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


# --------------------------------------------------------------------------------------
# (g) 경로 줄 표시와 기준선 대조 판정이 실제로 거부하는가
# --------------------------------------------------------------------------------------
def test_path_statement_marker_marks_path_lines_only():
    # oracle (a): 합성 소스에서 어느 줄이 경로 줄인지 손으로 정했다.
    src = ('import os, sys\n'                                            # 1 (경로 줄 아님)
           'ASSETS = os.path.dirname(os.path.abspath(__file__))\n'       # 2 경로 줄
           'sys.path.insert(0, ASSETS)\n'                                # 3 경로 줄
           'INST = (r"C:\\a\\b"\n'                                       # 4 경로 줄(절대 경로 리터럴)
           '        r"\\c.json")\n'                                      # 5 같은 문장의 이어지는 줄
           'GAIN_DB = 20.0 * 3\n')                                       # 6 계산 줄
    assert path_statement_lines(src) == {2, 3, 4, 5}


def test_only_path_lines_judge_rejects_a_calculation_change():
    # oracle (a): 계산 줄을 손으로 바꾼 합성 쌍 -> 판정이 거부해야 한다(경로 줄만 허용).
    base = 'import os\nASSETS = os.path.dirname(os.path.abspath(__file__))\nGAIN_DB = 20.0\n'
    new = 'import os\nASSETS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))\nGAIN_DB = 30.0\n'
    offenders = non_path_line_changes(base, new)
    assert [o[0] for o in offenders] == ["base", "new"], offenders
    with pytest.raises(AssertionError):
        assert_only_path_lines_changed(base, new, "합성 쌍")


def test_only_path_lines_judge_accepts_a_path_only_change():
    # oracle (a): 경로 줄만 바꾼 합성 쌍(줄 수가 바뀌는 암묵 연결 -> 한 줄 포함) -> 통과해야 한다.
    base = ('import os\n'
            'ASSETS = os.path.dirname(os.path.abspath(__file__))\n'
            'INST = (r"C:\\w\\x"\n'
            '        r"\\y.json")\n'
            'GAIN_DB = 20.0\n')
    new = ('import os\n'
           'ASSETS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))\n'
           'INST = os.path.join(ASSETS, "..", "y.json")\n'
           'GAIN_DB = 20.0\n')
    assert non_path_line_changes(base, new) == []
    assert_only_path_lines_changed(base, new, "합성 쌍")


def test_base_blob_reader_reads_the_base_tree():
    # oracle (a): base 커밋에 옛 자리가 있다는 사실이 기대값이다 -- 아래 기준선 대조가 공허해지지 않게.
    for name in _relocated_names():
        assert base_blob_text(f"{_TESTS_REL}/{name}.py").strip()
    assert base_blob_text(f"{_TESTS_REL}/{_TOOL_NAME}").strip()


# --------------------------------------------------------------------------------------
# 계약 5: 운영 도구가 `A/tests/tools/`로 옮겨졌다
# --------------------------------------------------------------------------------------
def test_moved_tool_is_in_tools_dir():
    # oracle (a): spec card 계약 5가 적은 새 자리와 옛 자리가 곧 기대값이다.
    assert (_TOOLS_DIR / _TOOL_NAME).is_file(), f"{_TOOLS_DIR / _TOOL_NAME} 가 없다"
    assert not (_TESTS_DIR / _TOOL_NAME).exists(), f"{_TESTS_DIR / _TOOL_NAME} 가 아직 있다"


def test_moved_tool_matches_base_except_path_lines():
    # oracle (c): 기준선 = base 커밋 blob 그 자체(계약 5의 '경로 계산 줄을 뺀 나머지가 원본과 같다').
    new_path = _TOOLS_DIR / _TOOL_NAME
    assert new_path.is_file(), f"{new_path} 가 없다"
    assert_only_path_lines_changed(base_blob_text(f"{_TESTS_REL}/{_TOOL_NAME}"),
                                   new_path.read_text(encoding="utf-8"), _TOOL_NAME)


def test_moved_tool_paths_equal_pre_move_targets():
    # oracle (c)/(a): 계약 3과 같은 방식 -- 이동 전 형태를 옛 자리 `A/tests/<도구>`에 적용한 값이 기대값이고,
    # dirname 중첩 기대값은 `A`에서 새 자리까지의 경로 성분 수(tests/tools/<도구> = 3)로 구성한다.
    new_path = _TOOLS_DIR / _TOOL_NAME
    assert new_path.is_file(), f"{new_path} 가 없다"
    src = new_path.read_text(encoding="utf-8")
    names, inserts = resolve_path_names(src, str(new_path))
    assert "ASSETS" in names, "도구가 ASSETS를 경로식으로 유도하지 않는다"
    assert dirname_depth(src, "ASSETS") == len(pathlib.PurePath("tests", "tools", "x.py").parts)

    pre_src = f"import os\nASSETS = {_PRE_MOVE_ASSETS_FORM}\n"
    pre_names, _ = resolve_path_names(pre_src, str(_TESTS_DIR / _TOOL_NAME))
    assert _same_path(names["ASSETS"], pre_names["ASSETS"]), (
        f"이동 전 {pre_names['ASSETS']} != 이동 후 {names['ASSETS']}")
    assert _same_path(names["ASSETS"], _ASSETS_DIR)

    assert inserts, "도구의 sys.path 삽입을 해석하지 못했다"
    assert _same_path(inserts[0], _ASSETS_DIR), inserts[0]
    for entry in inserts:
        assert os.path.isdir(entry), f"sys.path 삽입 대상이 없다 {entry}"
