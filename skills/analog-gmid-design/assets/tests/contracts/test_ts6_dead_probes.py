"""TS6 P1 계약: DF-21 probe 3개가 지워졌고 그 삭제 근거가 저장소 상태로 남아 있다(20260923-probe-dead-delete).

spec card `docs/02-design/specs/20260923-probe-dead-delete.spec.md` 계약 3의 (a)~(d)를 판정한다.
정본 명세는 design `gain-budget-gmid-sizing.20-dead-code-dup` v1.1 §5·§8 P1, 실측 원자료는
`docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/probe_inventory.json`(probe 42개 전수).

판정 네 가지(각각 '근거가 사라지면 이 test가 먼저 깨진다'는 뜻이다):

* (a) `A/tests/probe_mirror_common_L_wiring.py`·`probe_node_voltage_audit.py`·`probe_vs_semantics.py`가 없다.
* (b) `A/sizing_recipe.py`가 `_L_ROLE_MULTIPLIERS`를 더 이상 바인딩하지 않는다(= 지운 probe의 66·142행이
  import 즉시 `AttributeError`였다).
* (c) `audit_vsb_consistency`가 `A/sizing_recipe.py`의 운영 함수 안에서 호출된다(AST). 호출부가 0이라던 지운
  probe의 존재 이유가 사실과 다르다는 근거다. 이 파일은 `sizing_recipe`의 구현을 보지 않고 **호출 유무만** 센다.
* (d) 지운 `probe_vs_semantics`가 읽던 파일럿 산출물
  `workspaces/current-reuse-telescopic-ota-report/current_reuse_telescopic_ota.instance.json`의 `sizing` 레코드가
  `vs` 없이 `vsb`만 가진다(= `"vs" not in e` 로 건너뛰는 probe가 전 소자 skip = 무동작이었다).
  판정 범위를 이 파일럿 하나로 잡은 이유: 지운 probe가 이 경로를 소스에 박아 읽었다(probe_inventory.json의
  `hardcoded_abs_paths` 22행). 다른 workspace의 옛 `.instance.json`은 아직 `vs`를 가지므로 대상이 아니다.

oracle 대조(계획 N3.12.3):

* test_dead_probe_files_are_absent -- (a) 구성으로 정답이 정해진 입력: 삭제 목록은 spec card 계약 1의 세 경로 그대로,
  남는 수 39는 실측 probe_inventory.json의 42에서 DF-21 3을 뺀 값(계약 4). 피검 출력 없음.
* test_sizing_recipe_source_has_no_l_role_multipliers,
  test_sizing_recipe_module_has_no_l_role_multipliers_attribute -- (a) 저장소의 현재 심볼 유무가 곧 기대값이다.
* test_audit_vsb_consistency_has_operational_caller -- (a) 저장소의 현재 호출 관계가 곧 기대값이다(spec card 계약 2의
  `sizing_recipe.py:9481` 기록과 같은 사실). 호출부 '있음/없음'만 보고 계산식은 읽지 않는다.
* test_pilot_instance_sizing_declares_vsb_not_vs -- (a) 파일럿 산출물의 키 집합이 곧 기대값이다.
* test_*_rejects_* -- (a) 합성 입력(합성 디렉터리·합성 소스 문자열·합성 dict): 반대 경우를 손으로 만들었으므로
  정답이 구성으로 정해진다. 판정기가 실제로 거부하는지를 본다.
"""
import ast
import importlib
import pathlib
import sys

import pytest

# contracts -> tests -> assets(A) -> analog-gmid-design -> skills -> 저장소 루트
_TESTS_DIR = pathlib.Path(__file__).resolve().parents[1]
_ASSETS_DIR = _TESTS_DIR.parent
_REPO_ROOT = _ASSETS_DIR.parents[2]

# spec card 계약 1의 세 경로(저장소 루트 기준).
_DELETED_PROBES = (
    "skills/analog-gmid-design/assets/tests/probe_mirror_common_L_wiring.py",
    "skills/analog-gmid-design/assets/tests/probe_node_voltage_audit.py",
    "skills/analog-gmid-design/assets/tests/probe_vs_semantics.py",
)
# 실측 probe_inventory.json: n_probes = 42, plan_df21_delete_expected = 위 3개 -> 남는 수(계약 4).
_PROBE_TOTAL_BEFORE = 42
_REMAINING_PROBES = _PROBE_TOTAL_BEFORE - len(_DELETED_PROBES)

_SIZING_RECIPE = _ASSETS_DIR / "sizing_recipe.py"
_PILOT_INSTANCE = (_REPO_ROOT / "workspaces" / "current-reuse-telescopic-ota-report"
                   / "current_reuse_telescopic_ota.instance.json")
_MISSING_SYMBOL = "_L_ROLE_MULTIPLIERS"
_AUDIT_FUNC = "audit_vsb_consistency"
# 운영 함수가 아닌 것으로 세지 않을 이름 앞머리(진단·자가검사·pytest 함수).
_NON_OPERATIONAL_PREFIXES = ("test_", "probe_", "selftest", "_selftest", "main")


# --------------------------------------------------------------------------------------
# 판정 보조(이름은 전부 assert 로 시작한다 -- 판정 문장이 이 안에 있다)
# --------------------------------------------------------------------------------------
def assert_paths_absent(root: pathlib.Path, rel_paths) -> None:
    """`root` 아래에 `rel_paths` 중 어느 것도 남아 있지 않다."""
    present = [rel for rel in rel_paths if (root / rel).exists()]
    assert present == [], f"지워져야 할 파일이 남아 있다: {present}"


def _bound_names(source: str) -> set:
    """모듈 소스가 바인딩하는 이름(대입·정의·import·for·with·attribute 대입 대상)."""
    names = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            names.add(node.id)
        elif isinstance(node, ast.Attribute) and isinstance(node.ctx, (ast.Store, ast.Del)):
            names.add(node.attr)
    return names


def assert_source_binds_no_symbol(source: str, symbol: str, where: str) -> None:
    """`source`(모듈 소스)가 `symbol` 이라는 이름을 어디에서도 바인딩하지 않는다."""
    bound = _bound_names(source)
    assert symbol not in bound, f"{where}: 없어야 할 심볼 {symbol} 이 여전히 바인딩된다"


def _is_main_guard(node: ast.AST) -> bool:
    if not isinstance(node, ast.If) or not isinstance(node.test, ast.Compare):
        return False
    left = node.test.left
    comparators = node.test.comparators
    return (isinstance(left, ast.Name) and left.id == "__name__" and len(comparators) == 1
            and isinstance(comparators[0], ast.Constant) and comparators[0].value == "__main__")


def _called_func_name(func: ast.AST):
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _operational_callers(source: str, symbol: str) -> set:
    """`symbol` 을 호출하는 **운영 함수** 이름 집합.

    센다: 함수 정의 안(가장 안쪽 정의에 귀속)의 호출.
    안 센다: 모듈 최상위 호출, `if __name__ == "__main__":` 안의 호출, 자기 자신(재귀),
            test·probe·selftest·main 앞머리 함수.
    """
    callers = set()

    def walk(node, stack):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                walk(child, stack + [child.name])
                continue
            if _is_main_guard(child):
                continue
            if isinstance(child, ast.Call) and _called_func_name(child.func) == symbol and stack:
                inner = stack[-1]
                if inner != symbol and not inner.startswith(_NON_OPERATIONAL_PREFIXES):
                    callers.add(inner)
            walk(child, stack)

    walk(ast.parse(source), [])
    return callers


def assert_symbol_has_operational_caller(source: str, symbol: str, where: str) -> set:
    callers = _operational_callers(source, symbol)
    assert callers, f"{where}: {symbol} 을 호출하는 운영 함수가 없다"
    return callers


def assert_records_declare_vsb_not_vs(records: dict, where: str) -> None:
    """소자 레코드 전부가 `vsb` 를 가지고 `vs` 는 없다(+ 레코드가 하나라도 있다)."""
    assert records, f"{where}: 판정할 소자 레코드가 없다"
    with_vs = sorted(name for name, rec in records.items() if "vs" in rec)
    without_vsb = sorted(name for name, rec in records.items() if "vsb" not in rec)
    assert with_vs == [], f"{where}: 낡은 키 vs 를 가진 소자 {with_vs}"
    assert without_vsb == [], f"{where}: vsb 가 없는 소자 {without_vsb}"


def _load_pilot_sizing() -> dict:
    import json
    with open(_PILOT_INSTANCE, encoding="utf-8") as fh:
        return json.load(fh)["sizing"]


# --------------------------------------------------------------------------------------
# (a) 세 경로가 없다
# --------------------------------------------------------------------------------------
def test_dead_probe_files_are_absent():
    # oracle (a): 삭제 목록은 spec card 계약 1이 이름을 댄 세 경로 그대로다.
    assert_paths_absent(_REPO_ROOT, _DELETED_PROBES)
    # 공허한 판정 방지(계약 4): 지운 셋 말고 39개는 그대로 있다 -- 실측 42 - 3.
    remaining = sorted(p.name for p in _TESTS_DIR.rglob("probe_*.py"))
    assert len(remaining) == _REMAINING_PROBES, f"남은 probe 수 {len(remaining)}: {remaining}"


def test_path_absence_check_rejects_surviving_file(tmp_path):
    # oracle (a): 합성 디렉터리에 같은 이름을 하나 만들어 두면 판정이 실패해야 한다.
    victim = _DELETED_PROBES[0]
    (tmp_path / victim).parent.mkdir(parents=True)
    (tmp_path / victim).write_text("# 합성 파일(지워졌어야 할 probe 자리)\n", encoding="utf-8")
    with pytest.raises(AssertionError):
        assert_paths_absent(tmp_path, _DELETED_PROBES)
    assert (tmp_path / victim).exists()


# --------------------------------------------------------------------------------------
# (b) `_L_ROLE_MULTIPLIERS` 가 없다
# --------------------------------------------------------------------------------------
def test_sizing_recipe_source_has_no_l_role_multipliers():
    # oracle (a): 엔진 소스의 현재 심볼 유무가 곧 기대값이다(지운 probe의 66·142행이 읽던 이름).
    source = _SIZING_RECIPE.read_text(encoding="utf-8")
    assert_source_binds_no_symbol(source, _MISSING_SYMBOL, _SIZING_RECIPE.name)


def test_sizing_recipe_module_has_no_l_role_multipliers_attribute():
    # oracle (a): import 한 모듈에 그 이름이 없다 = 지운 probe의 `sr._L_ROLE_MULTIPLIERS` 는 AttributeError 였다.
    if str(_ASSETS_DIR) not in sys.path:
        sys.path.insert(0, str(_ASSETS_DIR))
    module = importlib.import_module("sizing_recipe")
    assert not hasattr(module, _MISSING_SYMBOL), f"sizing_recipe 에 {_MISSING_SYMBOL} 이 아직 있다"


@pytest.mark.parametrize(
    "source",
    [
        '_L_ROLE_MULTIPLIERS = {"tail": 1.0}\n',                      # 모듈 상수로 정의
        'def f():\n    _L_ROLE_MULTIPLIERS = 1\n    return _L_ROLE_MULTIPLIERS\n',  # 함수 안 대입
        'import os as _L_ROLE_MULTIPLIERS\n',                          # import 별칭
        'class C:\n    pass\nC._L_ROLE_MULTIPLIERS = 2\n',             # attribute 대입
    ],
)
def test_symbol_absence_check_rejects_source_that_binds_it(source):
    # oracle (a): 합성 소스가 그 이름을 바인딩하도록 손으로 만들었다 -> 판정이 실패해야 한다.
    with pytest.raises(AssertionError):
        assert_source_binds_no_symbol(source, _MISSING_SYMBOL, "합성 소스")
    assert _MISSING_SYMBOL in _bound_names(source)


def test_symbol_absence_check_accepts_source_without_binding():
    # oracle (a): 이름을 쓰기만 하고 바인딩하지 않는 합성 소스는 통과해야 한다(판정이 과하지 않다).
    source = "import sizing_recipe as sr\nvalue = sr._L_ROLE_MULTIPLIERS\n"
    assert_source_binds_no_symbol(source, _MISSING_SYMBOL, "합성 소스")
    assert _MISSING_SYMBOL not in _bound_names(source)


# --------------------------------------------------------------------------------------
# (c) `audit_vsb_consistency` 가 운영 경로에서 호출된다
# --------------------------------------------------------------------------------------
def test_audit_vsb_consistency_has_operational_caller():
    # oracle (a): 저장소의 현재 호출 관계가 기대값이다 -- 호출 유무만 세고 구현은 보지 않는다.
    source = _SIZING_RECIPE.read_text(encoding="utf-8")
    callers = assert_symbol_has_operational_caller(source, _AUDIT_FUNC, _SIZING_RECIPE.name)
    assert all(not name.startswith(_NON_OPERATIONAL_PREFIXES) for name in callers), callers


@pytest.mark.parametrize(
    "source",
    [
        # 호출이 아예 없다(정의만) -- 지운 probe의 docstring이 주장한 '호출부 0' 상태.
        "def audit_vsb_consistency(by_name, sized, vdd):\n    return []\n",
        # 최상위 스크립트 호출만 있다(함수 밖).
        "def audit_vsb_consistency(by_name, sized, vdd):\n    return []\n"
        "rows = audit_vsb_consistency({}, {}, 1.8)\n",
        # `if __name__ == '__main__':` 안에서만 부른다.
        "def audit_vsb_consistency(by_name, sized, vdd):\n    return []\n"
        "if __name__ == '__main__':\n    audit_vsb_consistency({}, {}, 1.8)\n",
        # 자기 자신(재귀)만 -- 운영 호출부가 아니다.
        "def audit_vsb_consistency(by_name, sized, vdd):\n    return audit_vsb_consistency({}, {}, vdd)\n",
        # test 함수에서만 부른다.
        "def audit_vsb_consistency(by_name, sized, vdd):\n    return []\n"
        "def test_audit():\n    assert audit_vsb_consistency({}, {}, 1.8) == []\n",
    ],
)
def test_caller_check_rejects_sources_without_operational_call(source):
    # oracle (a): 합성 소스마다 운영 호출부를 0으로 구성했다 -> 판정이 실패해야 한다.
    with pytest.raises(AssertionError):
        assert_symbol_has_operational_caller(source, _AUDIT_FUNC, "합성 소스")
    assert _operational_callers(source, _AUDIT_FUNC) == set()


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        # oracle (a): 운영 함수 이름을 손으로 넣었으므로 기대 집합이 구성으로 정해진다.
        ("def run_pipeline(x):\n    return audit_vsb_consistency({}, {}, 1.8)\n", {"run_pipeline"}),
        ("def run_pipeline(x):\n    return sr.audit_vsb_consistency({}, {}, 1.8)\n", {"run_pipeline"}),
        ("def outer():\n    def inner():\n        audit_vsb_consistency({}, {}, 1.8)\n    return inner\n",
         {"inner"}),
        ("def a():\n    audit_vsb_consistency({}, {}, 1.8)\n"
         "def b():\n    audit_vsb_consistency({}, {}, 1.8)\n", {"a", "b"}),
    ],
)
def test_caller_check_finds_operational_call(source, expected):
    assert _operational_callers(source, _AUDIT_FUNC) == expected
    callers = assert_symbol_has_operational_caller(source, _AUDIT_FUNC, "합성 소스")
    assert callers == expected


# --------------------------------------------------------------------------------------
# (d) 파일럿 instance.json 은 `vs` 없이 `vsb` 를 쓴다
# --------------------------------------------------------------------------------------
def test_pilot_instance_sizing_declares_vsb_not_vs():
    # oracle (a): 파일럿 산출물의 키 집합이 곧 기대값이다 -- 지운 probe의 `"vs" not in e` skip이 전 소자에 걸린다.
    sizing = _load_pilot_sizing()
    assert_records_declare_vsb_not_vs(sizing, _PILOT_INSTANCE.name)
    skipped = [name for name, rec in sizing.items() if "vs" not in rec]
    assert len(skipped) == len(sizing), f"skip 소자 {len(skipped)} / 전체 {len(sizing)}"


@pytest.mark.parametrize(
    "records",
    [
        {"M1": {"vs": 0.4, "vsb": 0.4}},          # 낡은 키 vs 가 남아 있다
        {"M1": {"vsb": 0.4}, "M2": {"vs": 0.0}},  # 일부 소자만 낡은 키
        {"M1": {"vds": 0.3}},                     # vsb 가 없다
        {},                                        # 레코드 자체가 없다(공허한 통과 방지)
    ],
)
def test_vsb_schema_check_rejects_stale_records(records):
    # oracle (a): 합성 dict 에 반대 경우를 손으로 넣었다 -> 판정이 실패해야 한다.
    with pytest.raises(AssertionError):
        assert_records_declare_vsb_not_vs(records, "합성 instance")
    assert isinstance(records, dict)


def test_vsb_schema_check_accepts_clean_records():
    # oracle (a): vsb 만 가진 합성 dict 는 통과해야 한다(판정이 과하지 않다).
    records = {"M1": {"vsb": 0.4, "vds": 0.3}, "M2": {"vsb": 0.0}}
    assert_records_declare_vsb_not_vs(records, "합성 instance")
    assert all("vs" not in rec for rec in records.values())
