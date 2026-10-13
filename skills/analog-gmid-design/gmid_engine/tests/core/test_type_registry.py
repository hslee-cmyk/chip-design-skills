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
