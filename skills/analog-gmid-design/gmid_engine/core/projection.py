"""계산 블록 입력 투영 -- 블록이 선언한 (kind, field) 열과 추가 인자만 담은 불변 객체 (설계 요건 1.1 (2), 계획 SC-e).

진입점: `Projection`.

블록 함수는 GraphSnapshot 이 아니라 이 투영만 받는다. 선언하지 않은 열은 투영에 없어 읽을 수 없다
(`KeyError`) -- 그래서 '선언 = 실제 read' 가 구성상 참이고, 입력 버전(투영 지문)이 블록이 읽는 상태 전부를 덮는다.
"""
import dataclasses

from .fingerprint import fp_of
from .immutability import require_immutable


@dataclasses.dataclass(frozen=True)
class Projection:
    """`columns` = 정렬된 (((kind, field), ((key, value), ...)), ...), `extras` = 추가 인자 tuple, `fp` = 둘의 지문."""

    columns: tuple = ()
    extras: tuple = ()
    fp: str = dataclasses.field(init=False)

    def __post_init__(self):
        require_immutable(self.extras)
        object.__setattr__(self, "columns", tuple(sorted(self.columns, key=lambda pair: pair[0])))
        object.__setattr__(self, "fp", fp_of((self.columns, self.extras)))

    @classmethod
    def from_snapshot(cls, snapshot, reads, extras=()):
        """`snapshot` 에서 `reads`((kind, field) 들)의 열만 뽑은 투영. 열이 비어 있어도 선언한 열은 들어간다."""
        columns = tuple((kind_field, snapshot.column(*kind_field)) for kind_field in reads)
        return cls(columns, tuple(extras))

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
