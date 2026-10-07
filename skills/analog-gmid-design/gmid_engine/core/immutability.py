"""불변 값 검사 -- graph 필드 값·계산 블록 추가 인자·memo 키는 불변이어야 한다 (계획 SC-a·SC-b, 설계 요건 1.1 (2)).

진입점: `require_immutable(value) -> None`.

허용: None, bool, int, float, str, bytes, `tuple`·`frozenset`(원소가 모두 허용 값), frozen dataclass(필드 값이
모두 허용 값), `__canonical__()` 메서드가 있는 객체(그 반환값이 허용 값). 그 밖(dict·list·set·bytearray·
일반 객체·ndarray 등)은 `TypeError` -- 제자리 변경이 가능한 값을 graph 나 캐시 키에 넣으면 지문이 낡는다(IC10).
"""
import dataclasses

_SCALARS = (type(None), bool, int, float, str, bytes)


def _children(value):
    canonical = getattr(type(value), "__canonical__", None)
    if canonical is not None:
        return (canonical(value),)
    if isinstance(value, _SCALARS):
        return ()
    if isinstance(value, (tuple, frozenset)):
        return tuple(value)
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        params = getattr(type(value), "__dataclass_params__", None)
        if params is not None and params.frozen:
            return tuple(getattr(value, f.name) for f in dataclasses.fields(value))
    raise TypeError(
        "require_immutable: 불변 값이 아님 -- " + type(value).__qualname__
        + " (tuple·frozenset·frozen dataclass·스칼라 또는 __canonical__ 객체만 허용)"
    )


def require_immutable(value):
    """`value` 와 그 하위 원소가 모두 불변 허용 타입이면 None, 아니면 `TypeError`."""
    pending = [value]
    while pending:
        pending.extend(_children(pending.pop()))
