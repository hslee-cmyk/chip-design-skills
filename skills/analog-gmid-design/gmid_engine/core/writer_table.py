"""writer 권한표 -- graph 필드 (kind, field) 마다 writer 하나 (계획 N3.4, SC-a; 확정 사항 1 '필드마다 writer 1개').

진입점: `WriterTable`.

graph 의 모든 쓰기는 이 표가 그 (kind, field) 에 배정한 writer 이름으로만 할 수 있다(`GraphSnapshot.write`).
같은 (kind, field) 에 다른 writer 를 둘 선언하면 표를 만들 때 `WriterPermissionError`.
"""
import dataclasses
import types

from .writer_error import WriterPermissionError

# graph 레코드 종류: 노드·소자·관계 엣지, 그리고 스냅샷 전체 필드(θ·metric·레이아웃 결과 등)를 담는 graph.
ENTITY_KINDS = ("device", "edge", "graph", "node")


def _check_name(what, value):
    if not isinstance(value, str) or not value:
        raise ValueError("WriterTable: " + what + " 은 비어 있지 않은 문자열이어야 한다")


@dataclasses.dataclass(frozen=True)
class WriterTable:
    """(kind, field, writer) 선언 모음. `entries` 는 정렬된 ((kind, field), writer) tuple 로 정규화된다."""

    entries: tuple = ()
    _index: object = dataclasses.field(init=False, repr=False, compare=False)

    def __post_init__(self):
        index = {}
        for entry in self.entries:
            if isinstance(entry, str):
                raise ValueError("WriterTable: 항목은 (kind, field, writer) 세 값이어야 한다")
            kind, field, writer = tuple(entry)  # 개수가 다르면 언패킹 ValueError
            if kind not in ENTITY_KINDS:
                raise ValueError("WriterTable: 모르는 kind " + repr(kind) + " (허용 " + repr(ENTITY_KINDS) + ")")
            _check_name("field", field)
            _check_name("writer", writer)
            previous = index.get((kind, field))
            if previous is not None and previous != writer:
                raise WriterPermissionError(
                    "필드 " + repr((kind, field)) + " 에 writer 둘: " + repr(previous) + ", " + repr(writer)
                )
            index[(kind, field)] = writer
        object.__setattr__(self, "entries", tuple(sorted(index.items())))
        object.__setattr__(self, "_index", types.MappingProxyType(index))

    def __canonical__(self):
        return self.entries

    def writer_of(self, kind, field):
        """(kind, field) 에 배정된 writer 이름, 선언이 없으면 None."""
        return self._index.get((kind, field))

    def fields_of(self, writer):
        """`writer` 에 배정된 (kind, field) 의 정렬된 tuple."""
        return tuple(key for key, owner in self.entries if owner == writer)

    def require(self, writer, kind, field):
        """`writer` 가 (kind, field) 의 배정 writer 가 아니면(선언 없음 포함) `WriterPermissionError`."""
        owner = self._index.get((kind, field))
        if owner is None:
            raise WriterPermissionError("권한표에 없는 필드 " + repr((kind, field)) + " (writer " + repr(writer) + ")")
        if owner != writer:
            raise WriterPermissionError(
                "필드 " + repr((kind, field)) + " 의 writer 는 " + repr(owner) + " -- " + repr(writer) + " 는 쓸 수 없다"
            )
