"""memo 키 정준화 -- 불변 값을 '같은 내용이면 ==·hash 가 같고 다른 내용이면 다른' hashable 값으로 바꾼다 (계획 NFR-2, DF-13, 사용자 승인 2026-10-08).

진입점: `canonical_key(obj)`.

`fp_of` 의 동치 관계(CONTRACT 1절)를 직렬화·sha256 없이 dict 키로 그대로 옮긴다: `canonical_key(a) == canonical_key(b)` 는
`fp_of(a) == fp_of(b)` 와 같다(sha256 충돌 제외). 파이썬의 `==` 가 뭉개는 구분을 태그로 되살린다.
* `bool` / `int` / `float` / `str` / `bytes` 는 서로 다른 값: `True` != `1` != `1.0` != `"1"`.
* float 은 비트 패턴(`struct.pack`)이라 `0.0` 과 `-0.0` 이 다른 키이고, NaN 은 모두 같은 키다(`float.hex` 가 모두 'nan').
* tuple 은 원소를 정준화한 tuple, frozenset 은 정준화한 원소의 frozenset, dataclass 는 (타입 이름, 선언 순서 필드),
  `__canonical__` 객체는 (타입 이름, 정준화한 반환값). 타입 이름은 `fp_of` 와 같은 `모듈.qualname`.
* 가변·지원 밖 값은 `require_immutable` 과 같은 `TypeError`(검사와 정준화가 한 번의 순회다).
태그는 이 파일 전용 sentinel 이라 사용자 값이 태그 tuple 과 같아질 수 없다. 결과는 프로세스 안에서만 쓰는 dict 키이며
저장·기록하지 않는다(저장·기록되는 지문은 `fp_of`).
"""
import dataclasses
import struct

_FLOAT_BITS = struct.Struct("<d")
_NAN_BITS = _FLOAT_BITS.pack(float("nan"))
_BOOL = object()
_BYTES = object()
_SET = object()
_DATACLASS = object()
_CANONICAL = object()
_TRUE = (_BOOL, True)
_FALSE = (_BOOL, False)


def _type_name(obj):
    cls = type(obj)
    return cls.__module__ + "." + cls.__qualname__


def _reject(obj):
    raise TypeError(
        "canonical_key: 불변 값이 아님 -- " + type(obj).__qualname__
        + " (tuple·frozenset·frozen dataclass·스칼라 또는 __canonical__ 객체만 허용)"
    )


def _float_key(value):
    return _FLOAT_BITS.pack(value) if value == value else _NAN_BITS


def canonical_key(obj):
    """`obj`(불변 값)의 정준 hashable 키. 불변이 아니면 `TypeError`."""
    kind = type(obj)
    if kind is str or kind is int or obj is None:
        return obj
    if kind is tuple:
        parts = []
        for item in obj:
            item_kind = type(item)
            if item_kind is str or item_kind is int or item is None:
                parts.append(item)
            elif item_kind is float:
                parts.append(_float_key(item))
            else:
                parts.append(canonical_key(item))
        return tuple(parts)
    if kind is float:
        return _float_key(obj)
    canonical = getattr(kind, "__canonical__", None)
    if canonical is not None:
        return (_CANONICAL, _type_name(obj), canonical_key(canonical(obj)))
    if isinstance(obj, bool):
        return _TRUE if obj else _FALSE
    if isinstance(obj, int):
        return int(obj)
    if isinstance(obj, float):
        return _float_key(obj)
    if isinstance(obj, str):
        return str.__str__(obj)
    if isinstance(obj, bytes):
        return (_BYTES, bytes(obj))
    if isinstance(obj, tuple):
        return canonical_key(tuple(obj))
    if isinstance(obj, frozenset):
        return (_SET, frozenset([canonical_key(item) for item in obj]))
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        params = getattr(kind, "__dataclass_params__", None)
        if params is not None and params.frozen:
            fields = tuple((f.name, canonical_key(getattr(obj, f.name))) for f in dataclasses.fields(obj))
            return (_DATACLASS, _type_name(obj), fields)
    return _reject(obj)
