"""Phase 2 P5b 계약: 파일럿 전용 telescopic CMRR·PSRR 사슬 삭제(20260923-d-delete-telescopic).

spec card `docs/02-design/specs/20260923-d-delete-telescopic.spec.md` 계약 1·2·3·4·7을 판정한다. 정본 명세는 design
`gain-budget-gmid-sizing.20-dead-code-dup` v1.1 §3(GONE·NEW-TOPO)·§6.4(G-3 (b)·G-4)·§8 P5b.
계약 5·6(E-LIB·E-INST·NEW-TOPO (i) 전후 동일)은 auditor가 base와 병합본을 실행해 비교한다 -- 여기서 기대 해시를 박지 않는다.
계약 4의 '삭제 전에 실재했음' 기록도 auditor의 base 측정 몫이다 -- 이 파일은 삭제 뒤 부재만 단언한다.

삭제 대상(spec card 계약 1 표 그대로, 2026-09-29 개정): `sizing_recipe` 모듈 함수 9개, 사슬 전용 모듈 상수
`_TELESCOPIC_FIXED_BASE`, 사슬 전용 필드 `SizingContext._open_loop_gains_cache` -- GONE 11개. 그리고 레지스트리 키 4개
(`_CMRR_ESTIMATOR_REGISTRY`·`_PSRR_ESTIMATOR_REGISTRY` 각각의 `telescopic_class_ab`·`telescopic_class_ab_cmfb`).

판정:

* 계약 1(레지스트리 키): 실행 중 모듈의 두 레지스트리에 삭제한 family 키가 없고, 값에 삭제 대상 이름의 callable이 없다.
* 계약 2 (G-4): 삭제한 두 family와 등록 목록에 없는 임의 family를 선언한 `cmrr_estimate`·`psrr_estimate` spec을
  평가하면 `ValueError`이고 메시지에 그 레지스트리의 등록 family가 전부 들어간다(조용한 무동작·기본값·0 반환 없음).
  입력은 라이브러리 밖 이름·넷의 합성 topology다(NEW-TOPO (ii)). base에서는 앞 두 family가 등록돼 있어 red.
* 계약 3 (NEW-TOPO (iii)): 같은 합성 topology에 일반 경로 `smallsignal_ratio_db`(CMRR형·PSRR형)를 선언하면 유한한 값이
  나온다. 크기는 판정하지 않는다(피검 식 재서술 금지).
* 계약 4 (G-3 (b)): `A/*.py`에 파일럿 topology 경로 리터럴(`current_reuse_telescopic_ota.topology.json`을 담거나 줄기
  `current_reuse_telescopic_ota`만인 문자열 상수, docstring·문자열 문장·산문 언급 제외)이 0건. base에서는
  `_load_telescopic_topology_cached`가 그 경로를 열므로 red.
* 계약 7 (GONE): 11개의 AST 참조가 `A/*.py`·`workspaces/run_harness.py`·`A/tests/**`에서 0. 함수 9개와 상수는
  정의(def)·Name(대입 대상 포함 모든 ctx)·Attribute·import를 센다. 필드는 `SizingContext` 클래스 본문의 선언(대입 대상)과
  Attribute(`ctx._open_loop_gains_cache`)를 센다. 주석·문자열은 참조가 아니다. base에서는 정의가 있어 red.

oracle 대조(계획 N3.12.3):

* test_registries_drop_deleted_families -- (a) 실행 중 모듈의 등록 딕셔너리 자체가 입력, 기대값은 '삭제 키·callable 0'
  (spec card 계약 1 표의 도달 경로 열). 피검 함수 호출 없음.
* test_deleted_family_is_rejected_on_new_topology -- (a) 합성 선언(삭제한 family·임의 family)과 합성 topology.
  거부(`ValueError`)와 메시지의 등록 목록은 spec card 계약 2·design §6.4 G-4가 정한 행동이다. 메시지에 들어가야 할
  목록은 피검 함수 출력이 아니라 선언 레지스트리의 키에서 읽는다.
* test_general_path_yields_value_on_new_topology -- (a) 합성 topology에 일반 경로 선언 -> 값(spec card 계약 3·design §3
  NEW-TOPO (iii)). 기대값은 '유한한 float'뿐이다.
* test_rejection_check_* -- (a) 합성 계산기(조용히 0을 내는 것·목록 없는 메시지로 거부하는 것)로 판정기의 거부를 본다.
* test_pilot_topology_path_literal_absent -- (a) 저장소의 현재 엔진 소스가 입력, 기대값은 '경로 리터럴 0건'(계약 4).
  파일 이름 줄기는 interface card의 `_load_telescopic_topology_cached` docstring("`current_reuse_telescopic_ota.topology.json`의
  connectivity를 캐시해서 돌려준다")에서 왔다.
* test_path_literal_check_* -- (a) 합성 소스(경로 리터럴 있음/docstring·주석·다른 회로만 있음).
* test_deleted_names_have_no_ast_references -- (a) 저장소 트리의 현재 AST가 입력, 기대값은 '참조 0'(계약 7).
* test_reference_check_* -- (a) 합성 소스(참조 있음/주석·문자열·접두 일치·동명 지역변수·다른 클래스 필드만 있음).
"""
import ast
import importlib
import json
import math
import pathlib
import sys

import pytest

# contracts -> tests -> assets(A) -> analog-gmid-design -> skills -> 저장소 루트
_TESTS_DIR = pathlib.Path(__file__).resolve().parents[1]
_ASSETS_DIR = _TESTS_DIR.parent
_REPO_ROOT = _ASSETS_DIR.parents[2]
_RUN_HARNESS = _REPO_ROOT / "workspaces" / "run_harness.py"

# spec card 계약 1 표의 함수 9개(전부 sizing_recipe 모듈 함수 -- 이름 자체가 식별자다).
_DELETED_NAMES = frozenset({
    "_cmrr_telescopic_class_ab",
    "_cmrr_telescopic_class_ab_cmfb",
    "_psrr_telescopic_class_ab",
    "_psrr_telescopic_class_ab_cmfb",
    "_cmfb_amp_gain_diode_load",
    "_load_telescopic_topology_cached",
    "_telescopic_class_ab_open_loop_response",
    "_telescopic_open_loop_device_names",
    "_telescopic_class_ab_open_loop_gains",
})
# spec card 계약 1 표(2026-09-29 추가)의 사슬 전용 모듈 상수 -- 모듈 이름이라 함수와 같은 규칙으로 센다.
_DELETED_CONSTANTS = frozenset({"_TELESCOPIC_FIXED_BASE"})
_GONE_MODULE_NAMES = _DELETED_NAMES | _DELETED_CONSTANTS
# spec card 계약 1 표(2026-09-29 추가)의 사슬 전용 필드: (필드 이름 -> 소유 클래스).
# 같은 이름의 지역변수와 구분하려고 선언은 소유 클래스 본문에서만 센다. Attribute는 어디서나 센다.
_DELETED_FIELDS = {"_open_loop_gains_cache": "SizingContext"}
# spec card 계약 1 표 '도달 경로' 열의 레지스트리 키(두 레지스트리 각각에서 빠진다).
_DELETED_FAMILIES = ("telescopic_class_ab", "telescopic_class_ab_cmfb")
# 어떤 레지스트리에도 없을 새 family(미래 topology가 오타·새 이름을 적는 경우 -- spec card '거부해야 할 입력').
_UNREGISTERED_FAMILY = "new_topology_future_family"
# metric type -> 그 type이 family를 고르는 레지스트리(spec card 계약 1 표).
_FAMILY_REGISTRIES = {
    "cmrr_estimate": "_CMRR_ESTIMATOR_REGISTRY",
    "psrr_estimate": "_PSRR_ESTIMATOR_REGISTRY",
}
# 계약 4: `_load_telescopic_topology_cached`가 열던 파일럿 topology 파일 이름 줄기(interface card docstring).
_PILOT_TOPOLOGY_STEM = "current_reuse_telescopic_ota"


def _engine_files() -> list:
    """계약 4·7의 엔진 범위: `A/*.py`(하위 디렉터리 제외)."""
    return sorted(_ASSETS_DIR.glob("*.py"))


def _test_files() -> list:
    """계약 7의 test 범위: `A/tests/**`의 .py 전부."""
    return sorted(_TESTS_DIR.rglob("*.py"))


def _rel(path: pathlib.Path) -> str:
    return path.resolve().relative_to(_REPO_ROOT).as_posix()


def _read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def _import_sizing_recipe():
    if str(_ASSETS_DIR) not in sys.path:
        sys.path.insert(0, str(_ASSETS_DIR))
    return importlib.import_module("sizing_recipe")


def assert_engine_scope_present(files: list) -> None:
    """판정 범위가 공허하지 않다: 계약 1 표의 정의 파일 `sizing_recipe.py`가 범위 안에 실재한다."""
    names = {p.name for p in files if p.exists()}
    assert "sizing_recipe.py" in names, f"판정 범위에 sizing_recipe.py 가 없다: {sorted(names)}"


# --------------------------------------------------------------------------------------
# 계약 1 (레지스트리 키): 두 레지스트리에서 삭제한 family 키와 callable이 빠진다
# --------------------------------------------------------------------------------------
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


def assert_registry_drops_families(registry: dict, where: str) -> None:
    """판정: 레지스트리가 비어 있지 않고, 삭제한 family 키도 삭제 대상 이름의 callable 값도 없다."""
    assert isinstance(registry, dict) and registry, f"{where}: 판정할 레지스트리가 비었거나 dict가 아니다"
    keys = sorted(set(_DELETED_FAMILIES) & set(registry))
    assert keys == [], f"{where}: 삭제한 family 키가 남아 있다 {keys}"
    found = sorted(_callable_names(registry) & _DELETED_NAMES)
    assert found == [], f"{where}: 삭제 대상 callable이 값으로 등록돼 있다 {found}"


@pytest.mark.parametrize("registry_name", sorted(set(_FAMILY_REGISTRIES.values())))
def test_registries_drop_deleted_families(registry_name):
    # oracle (a): 실행 중 모듈의 등록 딕셔너리가 입력, 기대값은 '삭제 키·callable 0'(spec card 계약 1). base에서 red.
    module = _import_sizing_recipe()
    assert hasattr(module, registry_name), f"sizing_recipe 에 spec card 계약 1의 {registry_name} 이 없다"
    assert_registry_drops_families(getattr(module, registry_name), registry_name)


def test_registry_check_rejects_synthetic_registry():
    # oracle (a): 삭제한 family 키를 가진 합성 레지스트리·삭제 대상 이름의 callable을 가진 합성 레지스트리 -> 거부.
    # 이 파일이 계약 7(GONE)의 범위 안이므로 삭제 대상 이름으로 def 하지 않고 `__name__`만 붙인다.
    def synthetic_estimator(metric_spec, ctx):  # noqa: ARG001 -- 이름만 쓰는 합성 callable
        return 0.0
    synthetic_estimator.__name__ = "_cmrr_telescopic_class_ab"

    def other_estimator(metric_spec, ctx):  # noqa: ARG001
        return 0.0

    with pytest.raises(AssertionError):
        assert_registry_drops_families({"telescopic_class_ab": other_estimator}, "합성 레지스트리")
    with pytest.raises(AssertionError):
        assert_registry_drops_families({"renamed_family": synthetic_estimator}, "합성 레지스트리")
    with pytest.raises(AssertionError):
        assert_registry_drops_families({}, "빈 합성 레지스트리")  # 공허한 통과 방지
    assert_registry_drops_families({"some_family": other_estimator}, "합성 레지스트리")


# --------------------------------------------------------------------------------------
# 합성 topology(NEW-TOPO): 라이브러리 밖 회로 이름·넷 이름·소자 이름
# --------------------------------------------------------------------------------------
# 차동 입력쌍 + 게이트 바이어스 부하 2개 + 꼬리 전류원(5소자). 넷 이름은 라이브러리 어디에도 없는 것을 골랐고
# 레일도 `supply_nets` 선언으로만 정한다(계획 DEC-60 -- 넷 이름 집합으로 레일을 정하지 않는다).
# 수치는 판정하지 않는 입력일 뿐이다(값의 크기를 단언하지 않는다).
_SYN_RAILS = ["rail_hi", "rail_lo"]
_SYN_NETLIST = [
    {"name": "Qnew_inp", "kind": "nmos", "source": "node_tail", "drain": "node_outn", "gate": "sig_inp"},
    {"name": "Qnew_inn", "kind": "nmos", "source": "node_tail", "drain": "node_outp", "gate": "sig_inn"},
    {"name": "Qnew_ldp", "kind": "pmos", "source": "rail_hi", "drain": "node_outn", "gate": "bias_ld"},
    {"name": "Qnew_ldn", "kind": "pmos", "source": "rail_hi", "drain": "node_outp", "gate": "bias_ld"},
    {"name": "Qnew_tail", "kind": "nmos", "source": "rail_lo", "drain": "node_tail", "gate": "bias_tl"},
]
_SYN_SIZED = {
    "Qnew_inp": {"ID": 8e-6, "W": 4e-6, "L": 0.4e-6, "gm": 95e-6, "gds": 0.8e-6},
    "Qnew_inn": {"ID": 8e-6, "W": 4e-6, "L": 0.4e-6, "gm": 95e-6, "gds": 0.8e-6},
    "Qnew_ldp": {"ID": 8e-6, "W": 7e-6, "L": 0.7e-6, "gm": 55e-6, "gds": 0.5e-6},
    "Qnew_ldn": {"ID": 8e-6, "W": 7e-6, "L": 0.7e-6, "gm": 55e-6, "gds": 0.5e-6},
    "Qnew_tail": {"ID": 16e-6, "W": 9e-6, "L": 1.1e-6, "gm": 120e-6, "gds": 0.3e-6},
}
# 외부에서 구동되는 넷(입력·바이어스·레일). 여기에 없는 넷은 회로 내부 노드다.
_SYN_DRIVEN = ("sig_inp", "sig_inn", "bias_ld", "bias_tl", "rail_hi", "rail_lo")


def _excite(**weights) -> dict:
    """외부 구동 넷 전부를 선언하고(값 0 = AC 접지) 주어진 넷만 여기한다 -- 라이브러리 two_stage_ota 선언과 같은 방식."""
    out = {net: 0.0 for net in _SYN_DRIVEN}
    out.update(weights)
    return out


def _write_synthetic_topology(directory: pathlib.Path) -> pathlib.Path:
    topo = {
        "schema_version": "2.0",
        "topology_name": "synthetic_new_topology_p5b",
        "supply_nets": list(_SYN_RAILS),
        "ports": {
            "sig_inp": {"role": "differential_input_p", "direction": "input"},
            "sig_inn": {"role": "differential_input_n", "direction": "input"},
            "node_outp": {"role": "differential_output_p", "direction": "output"},
            "node_outn": {"role": "differential_output_n", "direction": "output"},
        },
        "netlist": [dict(d) for d in _SYN_NETLIST],
        "symmetry": {"matching_pairs": []},
        "sizing_roles": {"theta": [], "metrics": {}, "objective": {}, "constraints": []},
    }
    path = directory / "synthetic_new_topology_p5b.topology.json"
    path.write_text(json.dumps(topo, indent=2), encoding="utf-8")
    return path


@pytest.fixture
def synthetic_ctx(tmp_path):
    sr = _import_sizing_recipe()
    path = _write_synthetic_topology(tmp_path)
    return sr, sr.SizingContext(sized={k: dict(v) for k, v in _SYN_SIZED.items()}, topology_path=str(path))


def _family_spec(metric_type: str, family: str) -> dict:
    """삭제한 사슬이 받던 모양의 역할 배정(합성 소자 이름)에 family만 바꿔 단 선언."""
    return {"type": metric_type, "circuit_family": family,
            "input_p": "Qnew_inp", "input_p_b": "Qnew_inn", "input_n": "Qnew_inp", "input_n_b": "Qnew_inn",
            "cascode_p": "Qnew_ldp", "cascode_p_b": "Qnew_ldn", "cascode_n": "Qnew_ldp", "cascode_n_b": "Qnew_ldn",
            "tail_p_devices": ["Qnew_tail"], "tail_n_device": "Qnew_tail", "tail_device": "Qnew_tail"}


# --------------------------------------------------------------------------------------
# 계약 2 (G-4): 등록 목록에 없는 family는 ValueError, 메시지에 등록 family 목록
# --------------------------------------------------------------------------------------
def assert_family_rejected_with_listing(compute_metric, registry: dict, spec: dict, ctx) -> None:
    """판정: `spec["circuit_family"]`는 레지스트리 키가 아니고, 그 선언을 계산하면 `ValueError`로 거부되며
    메시지에 레지스트리의 등록 family가 전부 들어간다."""
    family = spec["circuit_family"]
    assert registry, "전제 위반: 등록 family가 하나도 없는 레지스트리로는 '목록 안내'를 판정할 수 없다"
    assert family not in registry, f"전제 위반: {family!r} 는 아직 등록된 family다(삭제되지 않았다)"
    with pytest.raises(ValueError) as excinfo:
        compute_metric(spec, ctx)
    message = str(excinfo.value)
    missing = sorted(k for k in registry if str(k) not in message)
    assert missing == [], f"거부 메시지에 등록 family 목록이 없다(빠진 것 {missing}): {message!r}"


@pytest.mark.parametrize("family", list(_DELETED_FAMILIES) + [_UNREGISTERED_FAMILY])
@pytest.mark.parametrize("metric_type", sorted(_FAMILY_REGISTRIES))
def test_deleted_family_is_rejected_on_new_topology(synthetic_ctx, metric_type, family):
    # oracle (a): 합성 topology에 삭제한(또는 없는) family를 선언 -> spec card 계약 2·design §6.4 G-4의 거부.
    # 메시지에 들어가야 할 목록은 선언 레지스트리의 키다(피검 함수 출력이 아니다). 삭제한 두 family는 base에서 red.
    sr, ctx = synthetic_ctx
    registry = getattr(sr, _FAMILY_REGISTRIES[metric_type])
    assert_family_rejected_with_listing(sr.compute_metric, registry, _family_spec(metric_type, family), ctx)


def test_rejection_check_fails_on_silent_or_unlisted_refusal():
    # oracle (a): 판정기가 공허하게 통과하지 않는지 합성 계산기로 본다.
    registry = {"family_a": object(), "family_b": object()}
    spec = {"type": "cmrr_estimate", "circuit_family": "family_gone"}

    def silent_zero(metric_spec, ctx):  # noqa: ARG001 -- 조용히 0을 낸다(기본값 대입)
        return 0.0

    def refuses_without_listing(metric_spec, ctx):  # noqa: ARG001 -- 거부는 하지만 등록 목록을 안 알린다
        raise ValueError("unknown circuit_family")

    def refuses_with_listing(metric_spec, ctx):  # noqa: ARG001
        raise ValueError("unknown circuit_family 'family_gone'; registered: ['family_a', 'family_b']")

    with pytest.raises(pytest.fail.Exception):
        assert_family_rejected_with_listing(silent_zero, registry, spec, None)
    with pytest.raises(AssertionError):
        assert_family_rejected_with_listing(refuses_without_listing, registry, spec, None)
    with pytest.raises(AssertionError):  # family가 아직 등록돼 있으면 전제 위반
        assert_family_rejected_with_listing(refuses_with_listing, {"family_gone": object()}, spec, None)
    assert_family_rejected_with_listing(refuses_with_listing, registry, spec, None)


# --------------------------------------------------------------------------------------
# 계약 3 (NEW-TOPO (iii)): 같은 판정을 일반 경로 선언으로 하면 값이 나온다
# --------------------------------------------------------------------------------------
_GENERAL_PATH_SPECS = {
    # CMRR형: 차동 여기/차동 감지 대 동상 여기/동상 감지(파일럿 cmrr_estimate_db 선언과 같은 모양, 넷만 합성).
    "cmrr_like": {"type": "smallsignal_ratio_db",
                  "excite_num": _excite(sig_inp=0.5, sig_inn=-0.5), "sense_num": "diff",
                  "excite_den": _excite(sig_inp=1.0, sig_inn=1.0), "sense_den": "common",
                  "sense_p": "node_outp", "sense_n": "node_outn"},
    # PSRR형: 차동 여기/차동 감지 대 상단 레일 여기/동상 감지.
    "psrr_like": {"type": "smallsignal_ratio_db",
                  "excite_num": _excite(sig_inp=0.5, sig_inn=-0.5), "sense_num": "diff",
                  "excite_den": _excite(rail_hi=1.0), "sense_den": "common",
                  "sense_p": "node_outp", "sense_n": "node_outn"},
}


def assert_finite_value(value, where: str) -> None:
    """판정: 값이 나왔다(유한한 실수). 크기는 판정하지 않는다."""
    assert isinstance(value, float) and math.isfinite(value), f"{where}: 유한한 값이 아니다 {value!r}"


@pytest.mark.parametrize("label", sorted(_GENERAL_PATH_SPECS))
def test_general_path_yields_value_on_new_topology(synthetic_ctx, label):
    # oracle (a): 합성 topology + 일반 경로 선언 -> spec card 계약 3의 '값이 나온다'. 기대값은 유한성뿐이다.
    sr, ctx = synthetic_ctx
    spec = _GENERAL_PATH_SPECS[label]
    assert spec["type"] in sr._METRICS_REGISTRY, "전제 위반: 일반 경로 metric type이 등록돼 있지 않다"
    assert_finite_value(sr.compute_metric(dict(spec), ctx), label)


def test_finite_value_check_rejects_non_values():
    # oracle (a): 값이 아닌 것(무한·NaN·None)을 넣으면 판정이 실패해야 한다.
    for bad in (float("inf"), float("nan"), None):
        with pytest.raises(AssertionError):
            assert_finite_value(bad, "합성 값")
    assert_finite_value(12.5, "합성 값")


# --------------------------------------------------------------------------------------
# 계약 4 (G-3 (b)): 파일럿 topology 경로 리터럴 0건
# --------------------------------------------------------------------------------------
def _statement_string_ids(tree: ast.AST) -> set:
    """문장으로만 쓰인 문자열 상수(docstring 포함)의 id -- 경로로 쓰일 수 없으므로 리터럴로 세지 않는다."""
    ids = set()
    for node in ast.walk(tree):
        if (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)):
            ids.add(id(node.value))
    return ids


def _is_pilot_path_literal(value: str) -> bool:
    """경로 리터럴: 파일 이름 `<줄기>.topology.json`을 담거나, 줄기 자체만인 상수(경로 조립 부품).

    줄기를 산문으로 언급한 문자열(예: 회로 비교 설명 메시지)은 경로가 아니다 -- base 실측에서 `stick_diagram.py`의
    안내 메시지가 회로 이름을 산문으로 언급한다(경로를 열지 않는다).
    """
    return (_PILOT_TOPOLOGY_STEM + ".topology.json") in value or value.strip() == _PILOT_TOPOLOGY_STEM


def pilot_path_literals(source: str) -> list:
    """`source`의 문자열 상수 중 파일럿 topology 경로 리터럴(줄, 둘러싼 def, 값) -- 정렬.

    docstring·문자열 문장·주석은 세지 않는다. f-string의 고정 부분도 문자열 상수로 센다.
    """
    tree = ast.parse(source)
    skip = _statement_string_ids(tree)
    hits = set()

    def visit(node, owner):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            owner = node.name  # 가장 안쪽 def/class
        if (isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in skip
                and _is_pilot_path_literal(node.value)):
            hits.add((node.lineno, owner, node.value))
        for child in ast.iter_child_nodes(node):
            visit(child, owner)

    visit(tree, "<module>")
    return sorted(hits)


def assert_no_pilot_path_literal(source: str, where: str) -> None:
    """판정: `source`에 파일럿 topology 경로 리터럴이 없다."""
    hits = pilot_path_literals(source)
    assert hits == [], f"{where}: 파일럿 topology 경로 리터럴이 남아 있다(줄, 둘러싼 def, 값) {hits}"


def test_pilot_topology_path_literal_absent():
    # oracle (a): 저장소의 현재 엔진 소스가 입력, 기대값은 '경로 리터럴 0건'(spec card 계약 4). base에서 red.
    files = _engine_files()
    assert_engine_scope_present(files)
    offenders = {}
    for path in files:
        hits = pilot_path_literals(_read(path))
        if hits:
            offenders[_rel(path)] = hits
    assert offenders == {}, f"G-3 (b) -- 파일럿 topology 경로가 코드에 박혀 있다: {offenders}"


@pytest.mark.parametrize(
    "source",
    [
        'P = os.path.join(ASSETS, "library", "current_reuse_telescopic_ota.topology.json")\n',
        'def load():\n    return open(LIB / "current_reuse_telescopic_ota.topology.json")\n',
        'name = "current_reuse_telescopic_ota"\npath = f"{LIB}/{name}.topology.json"\n',
        'p = f"{LIB}/current_reuse_telescopic_ota.topology.json"\n',              # f-string 고정 부분
        'CACHE = {"topo": "library/current_reuse_telescopic_ota.topology.json"}\n',
    ],
)
def test_path_literal_check_rejects_synthetic_literal(source):
    # oracle (a): 경로 리터럴을 하나 넣어 손으로 만든 합성 소스 -> 판정이 실패해야 한다.
    with pytest.raises(AssertionError):
        assert_no_pilot_path_literal(source, "합성 소스")


@pytest.mark.parametrize(
    "source",
    [
        '"""current_reuse_telescopic_ota.topology.json 의 connectivity를 읽던 곳(삭제)."""\nx = 1\n',  # 모듈 docstring
        'def f():\n    """current_reuse_telescopic_ota 파일럿 설명."""\n    return 0\n',               # 함수 docstring
        '# path = "current_reuse_telescopic_ota.topology.json"\nx = 1\n',                           # 주석
        'P = os.path.join(ASSETS, "library", "folded_cascode.topology.json")\n',                   # 다른 회로
        'def load(path):\n    return open(path)\n',                                                 # 선언에서 받은 경로
        'msg = ("matching이 맞다(`current_reuse_telescopic_ota` M13/M22 비교)")\n',               # 산문 언급(경로 아님)
    ],
)
def test_path_literal_check_accepts_sources_without_literal(source):
    # oracle (a): 경로 리터럴이 없도록 구성한 합성 소스 -> 통과해야 한다(판정이 과하지 않다).
    assert_no_pilot_path_literal(source, "합성 소스")


# --------------------------------------------------------------------------------------
# 계약 7 (GONE): AST 참조 0
# --------------------------------------------------------------------------------------
def _assigned_names(stmt: ast.AST) -> list:
    """클래스 본문 문장이 선언하는 이름(대입 대상 Name) 목록 -- `x: T = ...`, `x = ...`, `x: T`."""
    if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
        return [stmt.target]
    if isinstance(stmt, ast.Assign):
        return [t for t in stmt.targets if isinstance(t, ast.Name)]
    return []


def ast_references(source: str) -> list:
    """삭제 대상 11개의 AST 참조(줄, 종류, 이름) -- 정렬.

    함수 9개·상수 1개(모듈 이름): 정의(def·class), Name(대입 대상 포함 모든 ctx), Attribute, `import`·`from x import 이름`.
    필드 1개: 소유 클래스 본문의 선언(대입 대상), Attribute(`obj.이름` -- 읽기·쓰기 모두), import.
    주석·문자열·키워드 인자 이름은 참조가 아니다.
    """
    tree = ast.parse(source)
    hits = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name in _GONE_MODULE_NAMES:
                hits.add((node.lineno, "def", node.name))
            if isinstance(node, ast.ClassDef):
                for stmt in node.body:
                    for target in _assigned_names(stmt):
                        if _DELETED_FIELDS.get(target.id) == node.name:
                            hits.add((target.lineno, "field", target.id))
        elif isinstance(node, ast.Name) and node.id in _GONE_MODULE_NAMES:
            hits.add((node.lineno, "name", node.id))
        elif isinstance(node, ast.Attribute) and (node.attr in _GONE_MODULE_NAMES or node.attr in _DELETED_FIELDS):
            hits.add((node.lineno, "attr", node.attr))
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                last = alias.name.split(".")[-1]
                if last in _GONE_MODULE_NAMES or last in _DELETED_FIELDS:
                    hits.add((node.lineno, "import", alias.name))
    return sorted(hits)


def assert_no_ast_reference(source: str, where: str) -> None:
    """판정: `source`에 삭제 대상 11개의 AST 참조가 없다."""
    hits = ast_references(source)
    assert hits == [], f"{where}: 삭제 대상 참조가 남아 있다(줄, 종류, 이름) {hits}"


def test_deleted_names_have_no_ast_references():
    # oracle (a): 저장소 트리의 현재 AST가 입력, 기대값은 '참조 0'(spec card 계약 7). base에서는 정의가 있어 red.
    engine = _engine_files()
    assert_engine_scope_present(engine)
    assert _RUN_HARNESS.exists(), f"판정 범위의 {_RUN_HARNESS} 가 없다"
    tests = _test_files()
    assert tests, "A/tests/** 에 .py 파일이 없다(판정 범위 공허)"
    offenders = {}
    for path in engine + [_RUN_HARNESS] + tests:
        hits = ast_references(_read(path))
        if hits:
            offenders[_rel(path)] = hits
    assert offenders == {}, f"GONE 위반 -- 삭제 대상 참조: {offenders}"


@pytest.mark.parametrize(
    ("source", "expected_name"),
    [
        ("def _cmrr_telescopic_class_ab(metric_spec, ctx):\n    return 0.0\n", "_cmrr_telescopic_class_ab"),
        ("from sizing_recipe import _cmfb_amp_gain_diode_load\n", "_cmfb_amp_gain_diode_load"),
        ("import sizing_recipe as sr\ng = sr._telescopic_class_ab_open_loop_gains(s, c)\n",
         "_telescopic_class_ab_open_loop_gains"),
        ("REG = {'telescopic_class_ab_cmfb': _psrr_telescopic_class_ab_cmfb}\n", "_psrr_telescopic_class_ab_cmfb"),
        ("fn = _load_telescopic_topology_cached\n", "_load_telescopic_topology_cached"),
        ("def f(s):\n    return _telescopic_open_loop_device_names(s)\n", "_telescopic_open_loop_device_names"),
        ("x = _telescopic_class_ab_open_loop_response(s, c, 1, 0, 0, 0)\n",
         "_telescopic_class_ab_open_loop_response"),
        ("REG = dict(telescopic_class_ab=_psrr_telescopic_class_ab)\n", "_psrr_telescopic_class_ab"),
        ("REG = {}\nREG['x'] = _cmrr_telescopic_class_ab_cmfb\n", "_cmrr_telescopic_class_ab_cmfb"),
        # 상수(2026-09-29 추가): 대입 대상·읽기·모듈 한정·import
        ("_TELESCOPIC_FIXED_BASE = {'Vbias1': 0.0}\n", "_TELESCOPIC_FIXED_BASE"),
        ("_TELESCOPIC_FIXED_BASE: dict = {}\n", "_TELESCOPIC_FIXED_BASE"),
        ("def f(extra):\n    return {**_TELESCOPIC_FIXED_BASE, **extra}\n", "_TELESCOPIC_FIXED_BASE"),
        ("import sizing_recipe as sr\nbase = sr._TELESCOPIC_FIXED_BASE\n", "_TELESCOPIC_FIXED_BASE"),
        ("from sizing_recipe import _TELESCOPIC_FIXED_BASE\n", "_TELESCOPIC_FIXED_BASE"),
        # 필드(2026-09-29 추가): 소유 클래스 본문의 선언·Attribute 읽기/쓰기
        ("class SizingContext:\n    _open_loop_gains_cache: dict = field(default_factory=dict)\n",
         "_open_loop_gains_cache"),
        ("class SizingContext:\n    _open_loop_gains_cache = None\n", "_open_loop_gains_cache"),
        ("hit = ctx._open_loop_gains_cache.get(key)\n", "_open_loop_gains_cache"),
        ("ctx._open_loop_gains_cache[key] = gains\n", "_open_loop_gains_cache"),
        ("self._open_loop_gains_cache = {}\n", "_open_loop_gains_cache"),
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
        "# _cmrr_telescopic_class_ab(...) 는 지웠다\nx = 1\n",                                  # 주석
        "doc = '_telescopic_class_ab_open_loop_gains() 대신 smallsignal_ratio_db'\n",           # 문자열
        "spec = {'circuit_family': 'telescopic_class_ab_cmfb'}\n",                              # family 문자열(이름 아님)
        "_cmrr_telescopic_class_ab_v2 = 1.0\n",                                                 # 접두만 같은 다른 이름
        "r = make(_cmfb_amp_gain_diode_load=None)\n",                                           # 키워드 인자 이름
        "# _TELESCOPIC_FIXED_BASE 는 파일럿 넷 이름이었다\nFIXED = {'bias': 0.0}\n",            # 상수: 주석
        "_TELESCOPIC_FIXED_BASE_V2 = {}\n",                                                     # 상수: 접두만 같은 이름
        "note = '_open_loop_gains_cache 는 지웠다'\n",                                          # 필드: 문자열
        "class OtherContext:\n    _open_loop_gains_cache = None\n",                             # 필드: 다른 클래스 선언
        "def f():\n    _open_loop_gains_cache = {}\n    return _open_loop_gains_cache\n",        # 필드: 동명 지역변수
    ],
)
def test_reference_check_accepts_sources_without_reference(source):
    # oracle (a): 참조가 없도록 구성한 합성 소스 -> 통과해야 한다(판정이 과하지 않다).
    assert_no_ast_reference(source, "합성 소스")
    assert ast_references(source) == []
