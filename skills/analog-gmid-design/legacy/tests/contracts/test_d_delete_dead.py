"""Phase 2 P5 계약: 레지스트리 등급 D 중 도달 경로 없는 8개 정의의 삭제(20260923-d-delete-dead).

spec card `docs/02-design/specs/20260923-d-delete-dead.spec.md` 계약 2·3·4를 판정한다. 정본 명세는 design
`gain-budget-gmid-sizing.20-dead-code-dup` v1.1 §3(GONE·NEW-TOPO)·§6.4(G-1~G-4)·§8 P5.
계약 5~7(E-LIB·E-INST·NEW-TOPO 전후 동일)은 auditor가 base와 병합본을 실행해 비교한다 -- 여기서 기대 해시를 박지 않는다.

삭제 대상 6개(spec card 계약 1 표의 8개 중 복원된 둘을 뺀 것):

* 모듈 함수 -- `sizing_recipe.converge_with_parasitics`·`slew_rate`,
  `stick_diagram.suggest_headroom_stack_groups`·`render_stick_diagram`
* 메서드 -- `SemiEmpiricalGmIdLUT.fT`, `GmIdLUT.junction_cap`

`sizing_recipe.lut_conditions_from_npz`·`workspaces/run_harness.derived_spec`은 계획서가 소비자·경로로 지정한 함수라
20260930-restore-plan-functions(spec card 계약 4, V5 승인 R1)가 되살렸으므로 판정 대상에서 뺐다. 두 이름을 쓰던 판정기
자기 점검 합성 케이스는 남은 삭제 이름으로 바꿨다(판정 강도 유지).

판정 셋:

* 계약 2 (G-1): 6개 중 어느 것도 엔진 모듈(`A/*.py`·`workspaces/run_harness.py`)의 딕셔너리에 **값으로** 나타나지 않는다
  (AST: 딕셔너리 리터럴·dict 컴프리헨션·`dict(...)` 키워드·`d[k] = v` 대입의 값 쪽). 함수 이름을 문자열 값으로 두는 경우
  (`getattr` 분기 가능성)도 등록으로 센다. 실행 중 모듈의 네 레지스트리(`_METRICS_REGISTRY`·`_CMRR_ESTIMATOR_REGISTRY`·
  `_PSRR_ESTIMATOR_REGISTRY`·`_COMPENSATION_REGISTRY`)의 값에 그 이름의 callable이 없는지도 따로 본다.
* 계약 3 (G-4): `_METRICS_REGISTRY`에 없는 metric type을 선언하면 `compute_metric`이 `ValueError`로 거부한다
  (조용한 무동작·기본값 대입이 아니다). 입력은 라이브러리에 없는 소자 이름의 합성 사이징 결과다.
* 계약 4 (GONE): 6개 이름의 AST 참조(정의·Name·Attribute·import)가 `A/*.py`·`workspaces/run_harness.py`·`A/tests/**`에서 0.
  주석·문자열은 참조가 아니다. 메서드 이름 `fT`는 같은 이름의 지역변수·데이터 필드가 있으므로(spec card 계약 1 표 주석)
  **정의(그 클래스 안의 def)·메서드 호출(`x.fT(...)`)·클래스 한정 참조(`SemiEmpiricalGmIdLUT.fT`)**만 센다. `junction_cap`도 같은 규칙.
  이 test는 base에서 red(정의가 아직 있다)이고 삭제 뒤 green이다.

oracle 대조(계획 N3.12.3):

* test_deleted_names_are_not_registered_as_dict_values, test_runtime_registries_hold_no_deleted_callable --
  (a) 저장소의 현재 등록 딕셔너리가 곧 입력이고 기대값은 '0건'이다(spec card 'oracle 종류와 출처' G-1). 피검 함수 호출 없음.
* test_registration_check_rejects_* / accepts_* -- (a) 합성 소스: 이름을 값으로 등록하도록(또는 하지 않도록) 손으로 만들었으므로
  정답이 구성으로 정해진다. 판정이 실제로 거부하는지 본다.
* test_unregistered_metric_type_is_rejected -- (a) 합성 선언: type 이름은 `_METRICS_REGISTRY` 키에 없도록 골랐고(전제를 같은
  test에서 확인), 거부는 spec card 계약 3·design §6.4 G-4가 정한 행동이다. 기대값을 피검 출력으로 만들지 않는다.
* test_registered_metric_type_on_same_context_yields_value -- (a) 대조군: 같은 합성 컨텍스트에서 등록된 type은 값이 나온다
  (design §3 NEW-TOPO (iii) '일반 경로 선언은 값 산출'). 값의 크기는 판정하지 않는다(피검 식 재서술 금지) -- 유한한 수인지만.
* test_deleted_names_have_no_ast_references -- (a) 저장소 트리의 현재 AST가 곧 입력이고 기대값은 '참조 0'이다(spec card 계약 4).
* test_reference_check_rejects_* / accepts_* -- (a) 합성 소스(참조 있음/주석·문자열·동명 지역변수만 있음)로 판정의 거부·통과를 본다.
"""
import ast
import importlib
import math
import pathlib
import sys

import pytest

# contracts -> tests -> assets(A) -> analog-gmid-design -> skills -> 저장소 루트
_TESTS_DIR = pathlib.Path(__file__).resolve().parents[1]
_ASSETS_DIR = _TESTS_DIR.parent
_REPO_ROOT = _ASSETS_DIR.parents[2]
_RUN_HARNESS = _ASSETS_DIR / "workspaces" / "run_harness.py"  # 2026-10-07 legacy 이동

# spec card 계약 1 표의 8개 중 복원된 둘(20260930-restore-plan-functions)을 뺀 6개. 모듈 함수는 이름 자체가 식별자다.
_DELETED_FUNCTIONS = frozenset({
    "converge_with_parasitics",
    "slew_rate",
    "suggest_headroom_stack_groups",
    "render_stick_diagram",
})
# 20260930-restore-plan-functions가 되살린 두 이름. GONE·G-1 판정 대상이 아니다. 계약 3(G-4)의 미등록 metric type
# 입력으로만 남긴다(metric type으로 선언되면 거부돼야 하는 것은 복원과 무관하다 -- 판정 입력을 줄이지 않는다).
_RESTORED_NAMES = ("derived_spec", "lut_conditions_from_npz")
# 메서드는 (이름 -> 소유 클래스). 같은 이름의 지역변수·데이터 필드와 구분하려고 소유 클래스로 한정한다.
_DELETED_METHODS = {
    "fT": "SemiEmpiricalGmIdLUT",
    "junction_cap": "GmIdLUT",
}
_ALL_DELETED = _DELETED_FUNCTIONS | frozenset(_DELETED_METHODS)
# 판정 대상이 공허하지 않다는 근거: 계약 1 표의 정의 위치 파일(이 셋이 없으면 판정 자체가 무의미하다).
_REQUIRED_ENGINE_FILES = ("sizing_recipe.py", "stick_diagram.py")
# spec card 계약 2가 이름을 댄 레지스트리 넷(sizing_recipe 모듈 속성).
_NAMED_REGISTRIES = ("_METRICS_REGISTRY", "_CMRR_ESTIMATOR_REGISTRY", "_PSRR_ESTIMATOR_REGISTRY",
                     "_COMPENSATION_REGISTRY")


def _engine_files() -> list:
    """계약 2·4의 엔진 범위: `A/*.py`(하위 디렉터리 제외) + `workspaces/run_harness.py`."""
    return sorted(_ASSETS_DIR.glob("*.py")) + [_RUN_HARNESS]


def _test_files() -> list:
    """계약 4의 test 범위: `A/tests/**`의 .py 전부."""
    return sorted(_TESTS_DIR.rglob("*.py"))


def _rel(path: pathlib.Path) -> str:
    return path.resolve().relative_to(_REPO_ROOT).as_posix()


def _read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def _import_sizing_recipe():
    if str(_ASSETS_DIR) not in sys.path:
        sys.path.insert(0, str(_ASSETS_DIR))
    return importlib.import_module("sizing_recipe")


# --------------------------------------------------------------------------------------
# 계약 2 (G-1): 딕셔너리 값으로 등록돼 있지 않다
# --------------------------------------------------------------------------------------
def _value_refs(node: ast.AST) -> list:
    """딕셔너리 값 쪽 부분 트리에서 삭제 대상 이름을 가리키는 것(줄, 이름) 목록.

    센다: 함수 이름의 Name·Attribute(`slew_rate`, `sr.slew_rate`), 메서드 이름의 Attribute(`lut.fT`,
    `GmIdLUT.junction_cap` -- 값 자리에 놓인 메서드는 등록이다), 함수 이름과 **정확히 같은** 문자열 상수(`getattr` 분기).
    """
    hits = []
    for sub in ast.walk(node):
        if isinstance(sub, ast.Name) and sub.id in _DELETED_FUNCTIONS:
            hits.append((sub.lineno, sub.id))
        elif isinstance(sub, ast.Attribute) and sub.attr in _ALL_DELETED:
            hits.append((sub.lineno, sub.attr))
        elif isinstance(sub, ast.Constant) and isinstance(sub.value, str) and sub.value in _DELETED_FUNCTIONS:
            hits.append((sub.lineno, sub.value))
    return hits


def _dict_value_nodes(tree: ast.AST):
    """딕셔너리에 값으로 들어가는 식 노드 전부."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            yield from node.values
        elif isinstance(node, ast.DictComp):
            yield node.value
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "dict":
            for kw in node.keywords:
                yield kw.value
        elif isinstance(node, ast.Assign) and any(isinstance(t, ast.Subscript) for t in node.targets):
            yield node.value


def dict_value_registrations(source: str) -> list:
    """소스 안에서 삭제 대상 이름이 딕셔너리 값으로 나타나는 곳(줄, 이름) -- 정렬."""
    hits = []
    for value in _dict_value_nodes(ast.parse(source)):
        hits.extend(_value_refs(value))
    return sorted(set(hits))


def assert_no_dict_value_registration(source: str, where: str) -> None:
    """판정: `source`의 어떤 딕셔너리에도 삭제 대상 이름이 값으로 등록돼 있지 않다."""
    hits = dict_value_registrations(source)
    assert hits == [], f"{where}: 삭제 대상이 딕셔너리 값으로 등록돼 있다(줄, 이름) {hits}"


def assert_engine_scope_present(files: list) -> None:
    """판정 범위가 공허하지 않다: 계약 1 표의 정의 파일과 run_harness가 범위 안에 실재한다."""
    names = {p.name for p in files if p.exists()}
    missing = [n for n in _REQUIRED_ENGINE_FILES + (_RUN_HARNESS.name,) if n not in names]
    assert missing == [], f"판정 범위에 있어야 할 엔진 파일이 없다: {missing}"


def test_deleted_names_are_not_registered_as_dict_values():
    # oracle (a): 저장소의 현재 엔진 소스가 입력이고 기대값은 '등록 0건'(spec card 계약 2).
    files = _engine_files()
    assert_engine_scope_present(files)
    offenders = {}
    for path in files:
        hits = dict_value_registrations(_read(path))
        if hits:
            offenders[_rel(path)] = hits
    assert offenders == {}, f"G-1 위반 -- 선언으로 도달 가능한 등록이 있다: {offenders}"


def _callable_names(obj, depth: int = 0) -> set:
    """레지스트리 값(중첩 dict·list·tuple 포함)에 들어 있는 callable의 `__name__` 집합."""
    names = set()
    if depth > 4:
        return names
    if isinstance(obj, dict):
        for v in obj.values():
            names |= _callable_names(v, depth + 1)
    elif isinstance(obj, (list, tuple, set, frozenset)):
        for v in obj:
            names |= _callable_names(v, depth + 1)
    elif callable(obj):
        name = getattr(obj, "__name__", None)
        if name is None and hasattr(obj, "func"):  # functools.partial
            name = getattr(obj.func, "__name__", None)
        if name is not None:
            names.add(name)
    return names


def assert_registry_holds_no_deleted_callable(registry: dict, where: str) -> None:
    """판정: 레지스트리 값의 callable 중 삭제 대상 이름을 가진 것이 없다(+ 레지스트리가 비어 있지 않다)."""
    assert isinstance(registry, dict) and registry, f"{where}: 판정할 레지스트리가 비었거나 dict가 아니다"
    found = sorted(_callable_names(registry) & _ALL_DELETED)
    assert found == [], f"{where}: 삭제 대상 callable이 값으로 등록돼 있다 {found}"


@pytest.mark.parametrize("registry_name", _NAMED_REGISTRIES)
def test_runtime_registries_hold_no_deleted_callable(registry_name):
    # oracle (a): 실행 중 모듈의 등록 딕셔너리 자체가 입력, 기대값은 '삭제 대상 이름의 callable 0'.
    module = _import_sizing_recipe()
    assert hasattr(module, registry_name), f"sizing_recipe 에 spec card 계약 2의 {registry_name} 이 없다"
    assert_registry_holds_no_deleted_callable(getattr(module, registry_name), registry_name)


@pytest.mark.parametrize(
    ("source", "expected_name"),
    [
        ('_METRICS_REGISTRY = {"slew": slew_rate}\n', "slew_rate"),                        # 모듈 함수 Name
        ('REG = {"conv": sr.converge_with_parasitics}\n', "converge_with_parasitics"),      # 모듈 한정 Attribute
        ('REG = {"ft": SemiEmpiricalGmIdLUT.fT}\n', "fT"),                                   # 클래스 한정 메서드
        ('REG = {"cj": lut.junction_cap}\n', "junction_cap"),                                # 바운드 메서드
        ('REG = {"render": ("stick", render_stick_diagram)}\n', "render_stick_diagram"),     # 튜플 안
        ('REG = {"sr": lambda i, c: slew_rate(i, c)}\n', "slew_rate"),                     # 람다 감싸기
        ('REG = dict(stick=render_stick_diagram)\n', "render_stick_diagram"),                # dict(...) 키워드
        ('REG = {}\nREG["hs"] = suggest_headroom_stack_groups\n', "suggest_headroom_stack_groups"),  # 첨자 대입
        ('REG = {k: slew_rate for k in ("a", "b")}\n', "slew_rate"),                         # dict 컴프리헨션
        ('REG = {"fn": "converge_with_parasitics"}\n', "converge_with_parasitics"),          # 문자열 값(getattr 분기)
    ],
)
def test_registration_check_rejects_synthetic_registry(source, expected_name):
    # oracle (a): 이름을 문자열 키에 묶인 값으로 등록하도록 손으로 만든 합성 소스 -> 판정이 실패해야 한다.
    with pytest.raises(AssertionError):
        assert_no_dict_value_registration(source, "합성 소스")
    assert expected_name in {name for _, name in dict_value_registrations(source)}


@pytest.mark.parametrize(
    "source",
    [
        '# REG = {"slew": slew_rate}\nREG = {"gain": gain_fn}\n',   # 주석 안
        'REG = {"slew_rate": gain_fn}\n',                            # 키로만 쓴 이름(값 아님)
        'fT = 1.0e9\nrow = {"fT_hz": 2.0}\nslew = slew_rate(1e-6, 1e-12)\n',  # 딕셔너리 밖 호출·동명 지역변수
        'row = {"fT": fT}\n',                                        # 메서드와 동명인 지역변수 값
        'REG = {"note": "uses slew_rate formula"}\n',                # 이름을 포함할 뿐인 문자열
    ],
)
def test_registration_check_accepts_sources_without_registration(source):
    # oracle (a): 등록이 없도록 구성한 합성 소스 -> 통과해야 한다(판정이 과하지 않다).
    assert_no_dict_value_registration(source, "합성 소스")
    assert dict_value_registrations(source) == []


def test_runtime_registry_check_rejects_synthetic_registry():
    # oracle (a): 삭제 대상과 같은 이름의 callable을 값으로 넣은 합성 레지스트리 -> 거부.
    # 이 파일이 계약 4(GONE)의 범위 안이므로 삭제 대상 이름으로 def 하지 않고 `__name__`만 붙인다.
    def synthetic_deleted(ID, C):  # noqa: ARG001 -- 이름만 쓰는 합성 callable
        return None
    synthetic_deleted.__name__ = "slew_rate"

    def some_metric(ctx):  # noqa: ARG001
        return None

    with pytest.raises(AssertionError):
        assert_registry_holds_no_deleted_callable({"ok": some_metric, "slew": synthetic_deleted}, "합성 레지스트리")
    with pytest.raises(AssertionError):
        assert_registry_holds_no_deleted_callable({"nested": {"slew": (synthetic_deleted,)}}, "합성 레지스트리")
    with pytest.raises(AssertionError):
        assert_registry_holds_no_deleted_callable({}, "빈 합성 레지스트리")  # 공허한 통과 방지
    assert_registry_holds_no_deleted_callable({"ok": some_metric}, "합성 레지스트리")


# --------------------------------------------------------------------------------------
# 계약 3 (G-4): 미등록 metric type은 ValueError로 거부된다
# --------------------------------------------------------------------------------------
# 라이브러리에 없는 합성 소자 이름(NEW-TOPO 취지 -- 새 이름·다른 소자 수). 수치는 판정하지 않는 입력일 뿐이다.
_SYNTHETIC_SIZED = {
    "Qnew_in": {"ID": 7e-6, "W": 4e-6, "L": 0.3e-6, "gm": 90e-6, "gds": 0.9e-6},
    "Qnew_ld": {"ID": 7e-6, "W": 6e-6, "L": 0.6e-6, "gm": 60e-6, "gds": 0.4e-6},
    "Qnew_tl": {"ID": 14e-6, "W": 9e-6, "L": 1.0e-6, "gm": 110e-6, "gds": 0.2e-6},
}
# 삭제 대상 이름 그대로(미래 topology가 그 이름을 metric type으로 적는 경우) + 어떤 레지스트리에도 없을 새 이름.
_UNREGISTERED_TYPES = sorted(_ALL_DELETED | frozenset(_RESTORED_NAMES)) + ["new_topology_future_metric"]


def assert_metric_type_rejected(compute_metric, registry: dict, spec: dict, ctx) -> None:
    """판정: `spec["type"]`이 레지스트리 키에 없고, 그 선언을 계산하면 `ValueError`로 거부된다."""
    assert spec["type"] not in registry, f"전제 위반: {spec['type']!r} 는 이미 _METRICS_REGISTRY 키다"
    with pytest.raises(ValueError):
        compute_metric(spec, ctx)


@pytest.mark.parametrize("metric_type", _UNREGISTERED_TYPES)
def test_unregistered_metric_type_is_rejected(metric_type):
    # oracle (a): 합성 선언(미등록 type) -> spec card 계약 3·design §6.4 G-4가 정한 거부(ValueError).
    sr = _import_sizing_recipe()
    ctx = sr.SizingContext(sized={k: dict(v) for k, v in _SYNTHETIC_SIZED.items()})
    assert_metric_type_rejected(sr.compute_metric, sr._METRICS_REGISTRY,
                                {"type": metric_type, "devices": sorted(_SYNTHETIC_SIZED)}, ctx)


def test_registered_metric_type_on_same_context_yields_value():
    # oracle (a) 대조군: 같은 합성 컨텍스트에서 등록된 type(`sum_current`, 기존 test s008이 쓰는 공개 선언)은
    # 거부 없이 값을 낸다 -- 위 거부가 컨텍스트 결함이 아니라 type 때문임을 보인다. 크기는 판정하지 않는다.
    sr = _import_sizing_recipe()
    assert "sum_current" in sr._METRICS_REGISTRY
    ctx = sr.SizingContext(sized={k: dict(v) for k, v in _SYNTHETIC_SIZED.items()})
    value = sr.compute_metric({"type": "sum_current", "devices": sorted(_SYNTHETIC_SIZED)}, ctx)
    assert isinstance(value, float) and math.isfinite(value), value


def test_rejection_check_fails_when_type_is_registered():
    # oracle (a): 합성 레지스트리에 type을 넣으면 전제 단언이 실패해야 한다(판정이 공허하게 통과하지 않는다).
    def compute_metric(spec, ctx):  # noqa: ARG001 -- 합성 계산기: 항상 값을 낸다(조용한 통과)
        return 0.0

    with pytest.raises(AssertionError):
        assert_metric_type_rejected(compute_metric, {"x": object()}, {"type": "x"}, None)
    # 미등록인데 조용히 값을 내는 합성 계산기 -> ValueError가 나지 않았으므로 판정이 실패해야 한다.
    with pytest.raises(pytest.fail.Exception):
        assert_metric_type_rejected(compute_metric, {}, {"type": "x"}, None)


# --------------------------------------------------------------------------------------
# 계약 4 (GONE): AST 참조 0
# --------------------------------------------------------------------------------------
def ast_references(source: str) -> list:
    """삭제 대상 6개의 AST 참조(줄, 종류, 이름) -- 정렬.

    함수 이름: 정의(def·class), Name(모든 ctx), Attribute, `from x import 이름`.
    메서드 이름: 소유 클래스 안의 def, 메서드 호출 `x.이름(...)`, 클래스 한정 `소유클래스.이름`, `from x import 이름`.
    주석·문자열·키워드 인자 이름은 참조가 아니다.
    """
    tree = ast.parse(source)
    hits = set()
    call_funcs = {id(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name in _DELETED_FUNCTIONS:
                hits.add((node.lineno, "def", node.name))
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if (isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                            and _DELETED_METHODS.get(item.name) == node.name):
                        hits.add((item.lineno, "def", item.name))
        elif isinstance(node, ast.Name) and node.id in _DELETED_FUNCTIONS:
            hits.add((node.lineno, "name", node.id))
        elif isinstance(node, ast.Attribute):
            if node.attr in _DELETED_FUNCTIONS:
                hits.add((node.lineno, "attr", node.attr))
            elif node.attr in _DELETED_METHODS:
                owner = _DELETED_METHODS[node.attr]
                qualified = isinstance(node.value, ast.Name) and node.value.id == owner
                if id(node) in call_funcs or qualified:
                    hits.add((node.lineno, "attr", node.attr))
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                if alias.name.split(".")[-1] in _ALL_DELETED:
                    hits.add((node.lineno, "import", alias.name))
    return sorted(hits)


def assert_no_ast_reference(source: str, where: str) -> None:
    """판정: `source`에 삭제 대상 6개의 AST 참조가 없다."""
    hits = ast_references(source)
    assert hits == [], f"{where}: 삭제 대상 참조가 남아 있다(줄, 종류, 이름) {hits}"


def test_deleted_names_have_no_ast_references():
    # oracle (a): 저장소 트리의 현재 AST가 입력, 기대값은 '참조 0'(spec card 계약 4). P5 base에서는 정의가 있어 red였다.
    engine = _engine_files()
    assert_engine_scope_present(engine)
    tests = _test_files()
    assert tests, "A/tests/** 에 .py 파일이 없다(판정 범위 공허)"
    offenders = {}
    for path in engine + tests:
        hits = ast_references(_read(path))
        if hits:
            offenders[_rel(path)] = hits
    assert offenders == {}, f"GONE 위반 -- 삭제 대상 참조: {offenders}"


@pytest.mark.parametrize(
    ("source", "expected_name"),
    [
        ("def slew_rate(ID, C):\n    return ID / C\n", "slew_rate"),                               # 정의
        ("class GmIdLUT:\n    def junction_cap(self, L, W):\n        return 0.0\n", "junction_cap"),  # 메서드 정의
        ("class SemiEmpiricalGmIdLUT:\n    def fT(self, g, L, v):\n        return 1.0\n", "fT"),   # 메서드 정의
        ("from sizing_recipe import converge_with_parasitics\n", "converge_with_parasitics"),       # import
        ("import stick_diagram as sd\ng = sd.suggest_headroom_stack_groups({})\n", "suggest_headroom_stack_groups"),  # 모듈 한정 호출
        ("x = lut.fT(12.0, 1e-6, 0.6)\n", "fT"),                                                     # 메서드 호출
        ("f = SemiEmpiricalGmIdLUT.fT\n", "fT"),                                                     # 클래스 한정 참조
        ("cj = lut.junction_cap(1e-6, 2e-6)\n", "junction_cap"),                                     # 메서드 호출
        ("fn = render_stick_diagram\n", "render_stick_diagram"),                                     # Name 대입
        ("def f(n):\n    return suggest_headroom_stack_groups(n)\n", "suggest_headroom_stack_groups"),
        ("import sizing_recipe as sr\nd = sr.slew_rate(1e-6, 1e-12)\n", "slew_rate"),
    ],
)
def test_reference_check_rejects_synthetic_reference(source, expected_name):
    # oracle (a): 참조를 하나 넣어 손으로 만든 합성 소스 -> 판정이 실패해야 한다.
    with pytest.raises(AssertionError):
        assert_no_ast_reference(source, "합성 소스")
    assert expected_name in {name.split(".")[-1] for _, _, name in ast_references(source)}


@pytest.mark.parametrize(
    "source",
    [
        "# converge_with_parasitics(...) 는 지웠다\nx = 1\n",           # 주석
        "doc = 'sd.render_stick_diagram(n) 로 바꾼다'\n",               # 문자열
        "fT = gm / (2 * 3.14159 * cgg)\nrow = {'fT': fT}\n",             # 메서드와 동명인 지역변수
        "def fT(gm, cgg):\n    return gm / cgg\n",                       # 소유 클래스 밖의 동명 함수
        "class Other:\n    def fT(self):\n        return 0.0\n",         # 다른 클래스의 동명 메서드
        "value = result.fT\n",                                           # 데이터 필드 읽기(호출 아님)
        "r = make(fT=1e9, junction_cap=None)\n",                         # 키워드 인자 이름
    ],
)
def test_reference_check_accepts_sources_without_reference(source):
    # oracle (a): 참조가 없도록 구성한 합성 소스 -> 통과해야 한다(판정이 과하지 않다).
    assert_no_ast_reference(source, "합성 소스")
    assert ast_references(source) == []
