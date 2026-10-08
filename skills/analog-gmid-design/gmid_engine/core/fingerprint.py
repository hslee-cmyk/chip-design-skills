"""내용 지문 -- 값의 정준 직렬화 바이트와 그 sha256 (계획 NFR-2, SC-d).

진입점: `fp_of(obj) -> str`.

정준 직렬화 규칙(같은 내용 = 같은 바이트, 다른 내용 = 다른 바이트):
* 원소마다 `태그 + 길이 + ':' + 내용`(스칼라) 또는 `태그 + 원소 수 + ':' + 원소들`(컨테이너) -- 자기 구분적이라
  이어 붙여도 모호하지 않다.
* float 은 `float.hex`(반올림 없는 정확한 표현), bool 은 int 와 다른 태그, dict 계열은 키의 정준 바이트로 정렬,
  set 계열은 원소의 정준 바이트로 정렬(순회 순서·PYTHONHASHSEED 무관, NFR-4).
* `__canonical__()` 메서드가 있는 객체는 그 반환값을, dataclass 는 (모듈.클래스 이름, 선언 순서 필드)를 직렬화한다.
* 그 밖의 타입은 `TypeError`(`id()`·`repr()` 로 대신하지 않는다 -- DF-13).
"""
import dataclasses
import hashlib
from collections.abc import Mapping, Set

_SEP = b":"


def _frame(tag, count, payload):
    return tag + str(count).encode("ascii") + _SEP + payload


def _type_name(obj):
    cls = type(obj)
    return _encode(cls.__module__ + "." + cls.__qualname__)


def _encode(obj):
    kind = type(obj)
    if kind is str:                      # 정확히 내장 타입이면 __canonical__ 가 없으므로 아래 일반 분기와 같은 바이트를 바로 만든다
        payload = obj.encode("utf-8")
        return _frame(b"S", len(payload), payload)
    if kind is tuple:
        parts = [_encode(item) for item in obj]
        return _frame(b"T", len(parts), b"".join(parts))
    if kind is float:
        payload = float.hex(obj).encode("ascii")
        return _frame(b"F", len(payload), payload)
    if kind is int:
        payload = str(obj).encode("ascii")
        return _frame(b"I", len(payload), payload)
    canonical = getattr(kind, "__canonical__", None)
    if canonical is not None:
        inner = _type_name(obj) + _encode(canonical(obj))
        return _frame(b"C", len(inner), inner)
    if obj is None:
        return _frame(b"N", 0, b"")
    if isinstance(obj, bool):
        payload = b"T" if obj else b"F"
        return _frame(b"B", len(payload), payload)
    if isinstance(obj, int):
        payload = str(obj).encode("ascii")
        return _frame(b"I", len(payload), payload)
    if isinstance(obj, float):
        payload = float.hex(obj).encode("ascii")
        return _frame(b"F", len(payload), payload)
    if isinstance(obj, str):
        payload = obj.encode("utf-8")
        return _frame(b"S", len(payload), payload)
    if isinstance(obj, (bytes, bytearray)):
        payload = bytes(obj)
        return _frame(b"Y", len(payload), payload)
    if isinstance(obj, (tuple, list)):
        parts = [_encode(item) for item in obj]
        return _frame(b"T", len(parts), b"".join(parts))
    if isinstance(obj, Mapping):
        pairs = sorted((_encode(k), _encode(v)) for k, v in obj.items())
        return _frame(b"M", len(pairs), b"".join(k + v for k, v in pairs))
    if isinstance(obj, Set):
        parts = sorted(_encode(item) for item in obj)
        return _frame(b"Z", len(parts), b"".join(parts))
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        fields = [
            _encode(f.name) + _encode(getattr(obj, f.name))
            for f in dataclasses.fields(obj)
        ]
        inner = _type_name(obj) + b"".join(fields)
        return _frame(b"D", len(fields), inner)
    raise TypeError(
        "fp_of: 지문을 만들 수 없는 타입 " + type(obj).__qualname__
        + " (정준 직렬화 규칙 밖 -- __canonical__ 을 정의하거나 지원 타입으로 바꿀 것)"
    )


def fp_of(obj):
    """`obj` 의 정준 직렬화 바이트의 sha256 hex 문자열(64자)을 돌려준다."""
    return hashlib.sha256(_encode(obj)).hexdigest()
