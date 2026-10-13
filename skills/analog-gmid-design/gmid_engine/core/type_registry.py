"""실행 시 타입 등록부 -- S0 수준 스냅샷 코덱이 받을 수 있는 graph 필드 값 형식 목록 (설계 40 §2.4.3 '타입 등록부', §2.4.10 ②).

진입점: `type_registry() -> TypeRegistry`(프로세스에 하나).

* 등록은 아래에서 위로 한다(import 계층 P N3.10): 각 패키지의 `__init__` 이 자기 graph 필드 값 형식(frozen dataclass)을
  `type_registry().register(cls)` 로 올린다. core 는 상위 패키지를 import 하지 않는다 -- `pipeline` 이 모든 패키지를 import 해
  등록부를 채운 뒤 코덱(`snapshot_codec.S0SnapshotStore`)을 부른다.
* 이름 = `<모듈>.<클래스 qualname>`(코덱의 `__type__` 값). 같은 클래스를 다시 올리면 무동작, 같은 이름의 다른 클래스는 `ValueError`.
  frozen dataclass 가 아니면 `TypeError`(코덱이 필드로 다시 만들 수 있는 값 형식만 받는다).
* `lookup(name)`: 등록된 클래스, 없으면 `KeyError`(디코더는 목록 밖 타입을 거부한다). `names()`: 등록 이름의 정렬된 tuple
  (구조 test §2.4.10 ② 가 읽기만 한다).
* 이 모듈은 설계 40 §2.4.10 ① 허용 모듈 목록의 core graph 모듈이다(등록부 상태를 갖는다). 값 캐시가 아니다 -- 클래스 목록만 담는다.
"""
import dataclasses


def _type_name(cls):
    return cls.__module__ + "." + cls.__qualname__


class _TypeRegistry:
    """등록부 하나. `type_registry()` 로만 얻는다."""

    def __init__(self):
        self._types = {}

    def register(self, cls):
        """`cls`(frozen dataclass 클래스)를 올리고 그대로 돌려준다."""
        params = getattr(cls, "__dataclass_params__", None)
        if not isinstance(cls, type) or not dataclasses.is_dataclass(cls) or params is None or not params.frozen:
            raise TypeError("type_registry.register: frozen dataclass 클래스만 올린다 -- " + repr(cls))
        name = _type_name(cls)
        known = self._types.get(name)
        if known is not None and known is not cls:
            raise ValueError("type_registry.register: 같은 이름의 다른 클래스 " + name)
        self._types[name] = cls
        return cls

    def lookup(self, name):
        """등록된 클래스. 목록 밖이면 `KeyError`."""
        cls = self._types.get(name)
        if cls is None:
            raise KeyError("type_registry: 등록부 밖 타입 " + repr(name))
        return cls

    def name_of(self, cls):
        """등록된 `cls` 의 이름. 목록 밖이면 `KeyError`."""
        name = _type_name(cls)
        if self._types.get(name) is not cls:
            raise KeyError("type_registry: 등록부 밖 타입 " + name)
        return name

    def names(self):
        """등록 이름의 정렬된 tuple."""
        return tuple(sorted(self._types))


_REGISTRY = _TypeRegistry()


def type_registry():
    """프로세스의 타입 등록부."""
    return _REGISTRY
