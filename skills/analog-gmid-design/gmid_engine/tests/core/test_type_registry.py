"""core/type_registry.py -- S0 수준 스냅샷 코덱의 실행 시 타입 등록부 (design 40 v1.6 §2.4.3 '타입 등록부', §2.4.10 ②).

근거(design 문장):
* "디코더는 실행 시 타입 등록부(`core/type_registry.py`)에 있는 타입만 받는다. 목록 밖 타입은 거부한다."
* "각 패키지의 `__init__`이 자기 필드 값 형식을 `register(cls)`로 올린다. `pipeline`이 모든 패키지를 import해 등록부를
  채운 뒤 코덱을 부른다. core는 상위 패키지(`graph`·`metrics`·`search` 등)를 import하지 않는다."
* 형식 행: frozen dataclass = `{"__type__": "<모듈>.<클래스>", ...}` -- 디코더는 이 이름 하나로 타입을 찾으므로 같은 이름에
  다른 클래스 둘이 올라가면 디코딩이 모호하다(중복 등록 거부의 근거).
* §2.4.2: search `start_values.py`의 `StartRow`·`StartConflict`·`MacroResult`·`StartRung`을 필드 값으로 그대로 쓴다
  (`Placement`는 as-built 위치가 `convergence/convergence_values.py`라 design 문장과 어긋나 여기서 단언하지 않는다 -- 보고 항목).

이름(통합 단계에서 구현 공개 API 로 맞춤, design 은 `register(cls)` 만 정한다): 등록부는 `core.type_registry` 모듈의
`type_registry()` 가 돌려주는 프로세스 하나의 객체이고, 그 메서드 `register`·`lookup`(이름 -> 클래스)·`names`(등록 이름 목록)를
`_API` 표 한 곳에 적었다. 판정 의미(무엇을 받고 무엇을 거부하는가)는 red-first 그대로다. 예외 클래스는 design 이 정하지 않아
(TypeError, ValueError, KeyError) 중 하나를 받는다. 주의: 패키지 `gmid_engine.core` 의 `type_registry` 속성은 같은 이름의 함수라
(`core/__init__` 재수출) 모듈은 `from gmid_engine.core.type_registry import type_registry` 로 가져온다.

기대값은 피검 코드를 부르지 않고 design 문장과 파이썬 클래스 이름 규칙(`__module__` + `.` + `__qualname__`)에서 정했다.
"""
import dataclasses
import os
import subprocess
import sys
import uuid

import pytest

# 개념 -> 등록부 객체(`type_registry()`)의 메서드 이름(구현 공개 API).
_API = {
    "resolve": "lookup",                     # "<모듈>.<클래스>" -> 등록된 cls, 없으면 거부
    "registered_names": "names",             # 등록된 "<모듈>.<클래스>" 이름 목록(§2.4.10 ② 가 읽는 목록)
}
# 하위 프로세스에서 등록부 객체를 얻는 문장(모듈 경로는 design §2.4.3·§2.4.10 이 정한 것)
_GET_REGISTRY = "from gmid_engine.core.type_registry import type_registry as _type_registry\nr = _type_registry()\n"
_REJECT = (TypeError, ValueError, KeyError)   # 예외 클래스 이름 미정

_SKILL_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _registry():
    from gmid_engine.core.type_registry import type_registry   # 모듈 경로는 design §2.4.3·§2.4.10 이 정한 것
    return type_registry()


def _api(concept):
    reg = _registry()
    name = _API[concept]
    fn = getattr(reg, name, None)
    if fn is None:
        pytest.fail("core.type_registry 등록부에 '%s' 개념의 메서드 %r 가 없다" % (concept, name))
    return fn


def _qualified(cls):
    return cls.__module__ + "." + cls.__qualname__


def _fresh_class(class_name, module_name):
    """같은 (모듈, 클래스) 이름을 갖는 서로 다른 frozen dataclass 를 만들 수 있게 이름을 주입한다."""
    cls = dataclasses.make_dataclass(class_name, [("a", float)], frozen=True)
    cls.__module__ = module_name
    cls.__qualname__ = class_name
    return cls


def _unique_module():
    return "gmid_engine_test_probe_" + uuid.uuid4().hex


# ---------- 등록 ----------

def test_register_function_exists_in_core_type_registry():
    assert callable(getattr(_registry(), "register", None)), "design §2.4.3: core/type_registry.py 의 register(cls)"


def test_registered_class_is_resolved_by_qualified_name():
    cls = _fresh_class("Probe", _unique_module())
    _registry().register(cls)
    assert _api("resolve")(_qualified(cls)) is cls


def test_registered_name_appears_in_name_list():
    cls = _fresh_class("Listed", _unique_module())
    _registry().register(cls)
    assert _qualified(cls) in tuple(_api("registered_names")())


# ---------- 중복 등록 거부 ----------

def test_second_class_with_same_qualified_name_is_rejected():
    module = _unique_module()
    first = _fresh_class("Twin", module)
    second = _fresh_class("Twin", module)
    assert first is not second and _qualified(first) == _qualified(second)
    _registry().register(first)
    with pytest.raises(_REJECT):
        _registry().register(second)
    # 거부 뒤에도 먼저 올린 것이 그대로 남는다(등록부가 바뀌지 않는다).
    assert _api("resolve")(_qualified(first)) is first


# ---------- 미등록 거부 ----------

def test_unregistered_name_is_rejected():
    cls = _fresh_class("NeverRegistered", _unique_module())
    with pytest.raises(_REJECT):
        _api("resolve")(_qualified(cls))


def test_unregistered_name_not_in_name_list():
    cls = _fresh_class("NotListed", _unique_module())
    assert _qualified(cls) not in tuple(_api("registered_names")())


def test_importable_but_unregistered_engine_class_is_rejected():
    # import 할 수 있는 실제 클래스라도 등록부에 없으면 거부한다("목록 밖 타입은 거부") -- 이름으로 import 해서 받으면 안 된다.
    # BoundedLRU 는 graph 필드 값 형식이 아니다(캐시 객체, §2.4.10 허용 모듈) -- 등록될 이유가 없다.
    with pytest.raises(_REJECT):
        _api("resolve")("gmid_engine.core.bounded_lru.BoundedLRU")


# ---------- import 계층(§2.4.3: core 는 상위 패키지를 import 하지 않는다) ----------

def _imported_engine_packages(statement):
    code = (
        "import sys\n"
        + statement + "\n"
        "mods = sorted({m.split('.')[1] for m in sys.modules if m.startswith('gmid_engine.') and m.count('.') >= 1})\n"
        "print(','.join(mods))\n"
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = _SKILL_DIR + os.pathsep + env.get("PYTHONPATH", "")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, cwd=_SKILL_DIR)
    assert out.returncode == 0, out.stderr
    return set(filter(None, out.stdout.strip().split(",")))


def test_type_registry_imports_no_upper_package():
    pkgs = _imported_engine_packages("from gmid_engine.core.type_registry import type_registry")
    assert pkgs <= {"core"}, "core.type_registry 가 상위 패키지를 import 했다: %s" % sorted(pkgs - {"core"})


def test_importing_core_alone_registers_no_upper_package_type():
    code = (
        _GET_REGISTRY
        + "names = [n for n in r.%s() if n.startswith('gmid_engine.') and not n.startswith('gmid_engine.core.')]\n"
        "print(len(names))\n" % _API["registered_names"]
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = _SKILL_DIR + os.pathsep + env.get("PYTHONPATH", "")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, cwd=_SKILL_DIR)
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "0", "core 만 import 했는데 상위 패키지 타입이 등록돼 있다(등록은 아래에서 위로, 각 패키지 __init__)"


# ---------- pipeline import 가 등록부를 채운다(§2.4.3) ----------

_SEARCH_START_VALUE_TYPES = (
    "gmid_engine.search.start_values.StartRow",
    "gmid_engine.search.start_values.StartConflict",
    "gmid_engine.search.start_values.MacroResult",
    "gmid_engine.search.start_values.StartRung",
)


def test_pipeline_import_registers_search_start_value_types():
    code = (
        "import gmid_engine.pipeline\n"
        + _GET_REGISTRY
        + "names = set(r.%s())\n"
        "print('|'.join(sorted(n for n in %r if n not in names)))\n" % (_API["registered_names"], _SEARCH_START_VALUE_TYPES)
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = _SKILL_DIR + os.pathsep + env.get("PYTHONPATH", "")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, cwd=_SKILL_DIR)
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "", "pipeline import 뒤 등록되지 않은 필드 값 형식: %s" % out.stdout.strip()


def _reachable_dataclass_types(roots, skip=()):
    """값들에서 닿는 dataclass 인스턴스의 타입 집합(필드 값·tuple·list·frozenset·dict 값을 따라 내려간다). `skip` 타입은 세지 않고 안으로만 간다."""
    import dataclasses as _dc
    seen, found, stack = set(), set(), list(roots)
    while stack:
        v = stack.pop()
        if id(v) in seen:
            continue
        seen.add(id(v))
        if _dc.is_dataclass(v) and not isinstance(v, type):
            if type(v) not in skip:
                found.add(type(v))
            stack.extend(getattr(v, f.name) for f in _dc.fields(v))
        elif isinstance(v, (tuple, list, frozenset, set)):
            stack.extend(v)
        elif hasattr(v, "items") and hasattr(v, "keys"):
            stack.extend(v.values())
            stack.extend(v.keys())
    return found


# ---------- [U17 ①-a 통합] 등록 대상 = design §2.4.2 '값 형식'에서 독립 도출(구현 등록 목록을 베끼지 않는다) ----------
# design 40 §2.4.2: S0 수준 필드 값 = as-built frozen dataclass(graph/s1v_values.py, metrics/achievability_types.py, search/start_values.py 의
# StartRow·StartConflict·MacroResult·StartRung·Placement)를 그대로 쓰고, 묶음(S1v, Achievability, StartIntervals)은 필드로 풀어 사본을 두지 않는다.
# 그래서 (가) 실제 S1 필드 값과 (나) 묶음 S1v 를 필드로 풀었을 때 그 값에서 닿는 dataclass 는 모두 등록돼 있어야 하고(목록 밖이면 코덱이 거부),
# (다) 묶음 클래스 자체는 필드 값이 아니다. 대상 회로 = library 9개 전부(구조가 다른 회로마다 닿는 값 형식이 다르다).
# metrics·search 묶음(Achievability·StartIntervals)의 같은 검사는 실제 단계 B·출발 구간이 필요해 tests/search/test_start_intervals.py 에 있다.

_LIBRARY = os.path.join(_SKILL_DIR, "assets", "library")


def _library_names():
    return sorted(n[: -len(".topology.json")] for n in os.listdir(_LIBRARY) if n.endswith(".topology.json") and not n.startswith("_"))


def _library_s1_s1v(name):
    import json
    from gmid_engine.authoring import load_topology
    from gmid_engine.graph import build_s1, build_s1v
    raw = json.loads(open(os.path.join(_LIBRARY, name + ".topology.json"), encoding="utf-8").read())
    supplies = {k: v for k, v in raw["_declared_target_spec"]["supplies_v"].items() if not k.startswith("_")}
    s1 = build_s1(load_topology(os.path.join(_LIBRARY, name + ".topology.json")), supplies)
    return s1, build_s1v(s1, None, count_budget=10 ** 9, stop_on_unsupported=False)


def _field_values(snapshot):
    out = []
    for kind in snapshot.kinds():
        for key in snapshot.keys(kind):
            rec = snapshot.record(kind, key)
            out.extend(rec.get(n).value for n in rec.field_names())
    return out


def test_library_has_nine_circuits():
    assert len(_library_names()) == 9, _library_names()


@pytest.mark.parametrize("name", _library_names())
def test_s1_and_s1v_field_value_types_are_registered(name):
    import gmid_engine.pipeline  # noqa: F401  (design §2.4.3: pipeline 이 모든 패키지를 import 해 등록부를 채운다)
    # [U17 ①-b] build_s1v 는 S1Graph(필드 graph/s1v: views·l_classes·findings·declared·applied_facts, 40 v1.9.1 §2.4.8 D1) -- 묶음 없음.
    s1, g = _library_s1_s1v(name)
    s1_types = _reachable_dataclass_types(_field_values(s1.snapshot))
    rec = g.snapshot.record("graph", "s1v")
    assert rec is not None, "graph/s1v 레코드가 없다"
    s1v_types = _reachable_dataclass_types([rec.get(n).value for n in rec.field_names()])
    names = set(_api("registered_names")())
    missing = sorted(_qualified(t) for t in s1_types | s1v_types if _qualified(t) not in names)
    assert not missing, "S0 수준 필드 값 형식인데 등록부에 없다(코덱이 거부): %s" % missing
    assert s1v_types, "s1v 에서 닿는 값 형식이 0 -- 검사가 비었다"


def test_bundle_classes_are_not_registered():
    # §2.4.2: 묶음 객체는 필드 묶음으로 풀고 사본을 두지 않는다 -> 묶음 클래스 자체는 필드 값 형식이 아니다.
    code = (
        "import gmid_engine.pipeline\n"
        + _GET_REGISTRY
        + "names = set(r.%s())\n"
        "print('|'.join(sorted(n for n in %r if n in names)))\n"
        % (_API["registered_names"], ("gmid_engine.graph.s1v_values.S1v", "gmid_engine.metrics.achievability_types.Achievability",
                                      "gmid_engine.search.start_values.StartIntervals"))
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = _SKILL_DIR + os.pathsep + env.get("PYTHONPATH", "")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, cwd=_SKILL_DIR)
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "", "묶음 클래스가 등록돼 있다: %s" % out.stdout.strip()


def test_pipeline_import_registered_count_reported():
    # 보고용 계수: pipeline import 뒤 gmid_engine 값 형식 등록 수(판정은 위 도달 검사가 한다 -- 수 자체는 design 이 정하지 않는다).
    code = "import gmid_engine.pipeline\n" + _GET_REGISTRY + "print(len([n for n in r.%s() if n.startswith('gmid_engine.')]))\n" % _API["registered_names"]
    env = dict(os.environ)
    env["PYTHONPATH"] = _SKILL_DIR + os.pathsep + env.get("PYTHONPATH", "")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, cwd=_SKILL_DIR)
    assert out.returncode == 0, out.stderr
    print("registered gmid_engine value types after pipeline import:", out.stdout.strip())
    assert int(out.stdout.strip()) > 0
