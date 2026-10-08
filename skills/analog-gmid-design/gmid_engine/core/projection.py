"""계산 블록 입력 투영 -- 블록이 선언한 (kind, field) 열과 추가 인자만 담은 불변 객체 (설계 요건 1.1 (2), 계획 SC-e).

진입점: `Projection`.

블록 함수는 GraphSnapshot 이 아니라 이 투영만 받는다. 선언하지 않은 열은 투영에 없어 읽을 수 없다
(`KeyError`) -- 그래서 '선언 = 실제 read' 가 구성상 참이고, 입력 버전(투영 지문)이 블록이 읽는 상태 전부를 덮는다.

투영 지문(2026-10-08 사용자 승인 '값 지문 합성', sizing O9): `fp = fp_of(((((kind, field), 열 지문), ...), extras))`, 열 지문 = sha256(자기 구분 인코딩된 ((key, fp_of(value)), ...))` -- 값 자리에 값 대신 값 지문을 넣는다. `from_snapshot` 은 스냅샷 필드가 이미 든 `FieldValue.value_fp`(= fp_of(value),
쓸 때 한 번 계산)를 그대로 쓰므로 블록 호출마다 값을 다시 직렬화하지 않는다. 모든 값을 똑같이 지문으로 바꾸므로 같은 열 값·
extras -> 같은 fp, 어느 값 하나라도 다르면 다른 fp(sha256 충돌을 빼면 값 직렬화 지문과 같은 동치 관계). 직접 생성도 같은 식이라
같은 내용이면 `from_snapshot` 과 fp 가 같다.
"""
import dataclasses
import hashlib

from .fingerprint import fp_of
from .immutability import require_immutable


def _by_kind_field(item):
    return item[0]


def _column_fp(pairs):
    """열 하나의 ((key, 값 지문), ...) 의 지문 -- 자기 구분적(`길이:key` + 고정 길이 64자 값 지문)이라 fp_of 의 재귀 직렬화 없이
    sha256 한 번. key 가 str 이 아니면 그 key 만 fp_of 로 정준화한다."""
    parts = []
    for key, value_fp in pairs:
        text = key if type(key) is str else fp_of(key)
        parts.append(str(len(text)) + ":" + text + value_fp)
    return hashlib.sha256("".join(parts).encode("utf-8")).hexdigest()


def _projection_fp(rows, extras):
    """rows = 정렬된 ((kind, field), ((key, 값 지문), ...)) 들."""
    return fp_of((tuple((kind_field, _column_fp(pairs)) for kind_field, pairs in rows), extras))


@dataclasses.dataclass(frozen=True)
class Projection:
    """`columns` = 정렬된 (((kind, field), ((key, value), ...)), ...), `extras` = 추가 인자 tuple,
    `fp` = (열마다 ((key, 값 지문), ...), extras) 의 지문."""

    columns: tuple = ()
    extras: tuple = ()
    fp: str = dataclasses.field(init=False)

    def __post_init__(self):
        require_immutable(self.extras)
        columns = tuple(sorted(self.columns, key=_by_kind_field))
        value_fps = tuple((kind_field, tuple((key, fp_of(value)) for key, value in values))
                          for kind_field, values in columns)
        object.__setattr__(self, "columns", columns)
        object.__setattr__(self, "fp", _projection_fp(value_fps, self.extras))

    @classmethod
    def from_snapshot(cls, snapshot, reads, extras=()):
        """`snapshot` 에서 `reads`((kind, field) 들)의 열만 뽑은 투영. 열이 비어 있어도 선언한 열은 들어간다.
        값 지문은 스냅샷 필드의 `value_fp` 를 그대로 쓴다(값을 다시 직렬화하지 않는다)."""
        extras = tuple(extras)
        require_immutable(extras)
        rows = sorted(((kind_field, snapshot.column_fields(*kind_field)) for kind_field in reads), key=_by_kind_field)
        columns = tuple((kind_field, tuple((key, fv.value) for key, fv in pairs)) for kind_field, pairs in rows)
        value_fps = tuple((kind_field, tuple((key, fv.value_fp) for key, fv in pairs)) for kind_field, pairs in rows)
        projection = object.__new__(cls)
        object.__setattr__(projection, "columns", columns)
        object.__setattr__(projection, "extras", extras)
        object.__setattr__(projection, "fp", _projection_fp(value_fps, extras))
        return projection

    def column(self, kind, field):
        """선언한 열의 ((key, value), ...). 선언 밖이면 `KeyError`."""
        for kind_field, values in self.columns:
            if kind_field == (kind, field):
                return values
        raise KeyError("투영에 없는 열(블록 reads 선언 밖): " + repr((kind, field)))

    def value(self, kind, key, field):
        """선언한 열의 한 값. 열이 선언 밖이거나 key 에 값이 없으면 `KeyError`."""
        for row_key, value in self.column(kind, field):
            if row_key == key:
                return value
        raise KeyError((kind, key, field))
