"""graph 레코드 -- 노드·소자·엣지·graph 전체 하나의 불변 필드 묶음 (계획 N3.3 S1·S2, 확정 사항 2).

진입점: `GraphRecord`.

레코드는 불변이다. 필드를 바꾸면 `GraphSnapshot.write` 가 새 레코드를 만들고, 바뀌지 않은 레코드는
새 스냅샷이 같은 객체를 공유한다(구조 공유).
"""
import dataclasses

from .field_value import FieldValue
from .fingerprint import fp_of


@dataclasses.dataclass(frozen=True)
class GraphRecord:
    """`kind`·`key`(입력에서 읽은 이름 문자열)와 정렬된 ((field, FieldValue), ...) tuple.

    `fp` = fp_of((kind, key, ((field, value_fp), ...))) -- 값 내용만의 지문(writer·입력 버전·쓰기 횟수 제외).
    레코드는 불변이라 `fp` 는 처음 읽을 때 한 번 계산해 레코드에 보관한다(스냅샷 지문을 읽지 않는 중간 레코드는 계산하지 않는다).
    """

    kind: str
    key: str
    fields: tuple = ()
    fp: str = dataclasses.field(init=False)

    def __post_init__(self):
        if not isinstance(self.key, str):
            raise TypeError("GraphRecord.key 는 문자열이어야 한다")
        names = []
        for name, field_value in self.fields:
            if not isinstance(name, str) or not name:
                raise ValueError("GraphRecord 필드 이름은 비어 있지 않은 문자열이어야 한다")
            if not isinstance(field_value, FieldValue):
                raise TypeError("GraphRecord 필드 값은 FieldValue 여야 한다")
            names.append(name)
        if len(set(names)) != len(names):
            raise ValueError("GraphRecord 필드 이름 중복")
        ordered = tuple(sorted(self.fields, key=lambda pair: pair[0]))
        object.__setattr__(self, "fields", ordered)

    def __getattr__(self, name):
        """`fp` 만 지연 계산: 첫 읽기에 계산해 인스턴스에 보관한다(이후는 일반 속성 조회)."""
        if name != "fp":
            raise AttributeError(name)
        content = (self.kind, self.key, tuple((field, fv.value_fp) for field, fv in self.fields))
        object.__setattr__(self, "fp", fp_of(content))
        return self.fp

    def get(self, field):
        """필드의 FieldValue, 없으면 None."""
        for name, field_value in self.fields:
            if name == field:
                return field_value
        return None

    def field_names(self):
        """필드 이름의 정렬된 tuple."""
        return tuple(name for name, _ in self.fields)
