"""불변 graph 스냅샷 -- Circuit State Graph 의 유일 정본 저장 구조 (확정 사항 1·2, 계획 N3.3·N3.4·SC-a·SC-b).

진입점: `GraphSnapshot`.

* 스냅샷은 불변이다. 쓰기는 `write` 하나(graph setter)로만 하고, 바뀐 레코드만 새로 만든 새 스냅샷을 돌려준다
  -- 바뀌지 않은 레코드 객체는 이전 스냅샷과 공유한다(구조 공유). 제자리 수정·되돌리기 API 는 없다.
* 모든 쓰기는 `WriterTable` 이 그 (kind, field) 에 배정한 writer 로만 한다(필드마다 writer 하나).
* 필드마다 값과 함께 writer·입력 버전·쓰기 횟수를 기록한다(`FieldValue`) -- 필드가 곧 캐시다.
* writer 별 마지막 입력 버전(`block_version`)을 기록한다 -- 계산 블록이 '입력 버전이 같으면 재사용'을 판정하는 근거.
"""
import dataclasses
import types
from collections.abc import Mapping

from .determinism import sorted_items
from .field_value import FieldValue
from .fingerprint import fp_of
from .graph_record import GraphRecord
from .writer_error import WriterPermissionError
from .writer_table import WriterTable


def _touch(pending, base, key):
    """이번 write 에서 처음 바뀌는 레코드의 필드 사본(레코드는 write 끝에서 한 번만 새로 만든다)."""
    fields = pending.get(key)
    if fields is None:
        record = base.get(key)
        fields = {} if record is None else dict(record.fields)
        pending[key] = fields
    return fields


@dataclasses.dataclass(frozen=True, eq=False)
class GraphSnapshot:
    """불변 스냅샷. 직접 만들지 말고 `GraphSnapshot.empty(writers)` 와 `write` 를 쓴다.

    * `writers`: WriterTable.
    * `tables`: kind -> (key -> GraphRecord) 읽기 전용 매핑. 필드가 하나도 없는 레코드는 두지 않는다.
    * `block_versions`: writer -> 마지막 쓰기의 입력 버전 읽기 전용 매핑.
    * `fp`: 값 내용 지문 = fp_of(정렬된 (kind, ((key, record.fp), ...)) 중 레코드가 있는 kind) --
      writer·입력 버전·block_versions 는 넣지 않는다(같은 값 = 같은 fp). 스냅샷이 불변이라 처음 읽을 때 한 번 계산해 보관한다.
    """

    writers: WriterTable
    tables: object = None
    block_versions: object = None
    fp: str = dataclasses.field(init=False)
    _order_cache: object = dataclasses.field(init=False, repr=False, compare=False)
    _column_cache: object = dataclasses.field(init=False, repr=False, compare=False)

    def __post_init__(self):
        if not isinstance(self.writers, WriterTable):
            raise TypeError("GraphSnapshot.writers 는 WriterTable 이어야 한다")
        tables = {}
        for kind, records in sorted_items(self.tables or {}):
            if records:
                tables[kind] = types.MappingProxyType(dict(records))
        versions = types.MappingProxyType(dict(self.block_versions or {}))
        object.__setattr__(self, "tables", types.MappingProxyType(tables))
        object.__setattr__(self, "block_versions", versions)
        object.__setattr__(self, "_order_cache", {})
        object.__setattr__(self, "_column_cache", {})

    def __getattr__(self, name):
        """`fp` 만 지연 계산: 첫 읽기에 계산해 보관한다(읽지 않는 중간 스냅샷은 직렬화하지 않는다)."""
        if name != "fp":
            raise AttributeError(name)
        content = tuple(
            (kind, tuple((key, record.fp) for key, record in self._ordered(kind)))
            for kind in self.kinds()
        )
        object.__setattr__(self, "fp", fp_of(content))
        return self.fp

    def _ordered(self, kind):
        """`kind` 레코드의 key 정렬된 ((key, record), ...) -- 스냅샷이 불변이라 kind 마다 한 번만 정렬한다."""
        ordered = self._order_cache.get(kind)
        if ordered is None:
            ordered = sorted_items(self.tables.get(kind, {}))
            self._order_cache[kind] = ordered
        return ordered

    @classmethod
    def empty(cls, writers):
        """레코드가 없는 첫 스냅샷."""
        return cls(writers)

    def kinds(self):
        """레코드가 있는 kind 의 정렬된 tuple."""
        return tuple(kind for kind, _ in sorted_items(self.tables))

    def keys(self, kind):
        """`kind` 레코드 key 의 정렬된 tuple(없으면 빈 tuple)."""
        return tuple(key for key, _ in sorted_items(self.tables.get(kind, {})))

    def record(self, kind, key):
        """GraphRecord, 없으면 None."""
        return self.tables.get(kind, {}).get(key)

    def field(self, kind, key, field):
        """FieldValue, 없으면 None."""
        record = self.record(kind, key)
        return None if record is None else record.get(field)

    def value(self, kind, key, field):
        """필드 값. 없으면 `KeyError`."""
        field_value = self.field(kind, key, field)
        if field_value is None:
            raise KeyError((kind, key, field))
        return field_value.value

    def column(self, kind, field):
        """`kind` 레코드 중 `field` 가 있는 것의 ((key, value), ...) -- key 정렬."""
        return tuple((key, field_value.value) for key, field_value in self.column_fields(kind, field))

    def column_fields(self, kind, field):
        """`column` 과 같은 순서의 ((key, FieldValue), ...) -- 값과 함께 value_fp·writer·입력 버전을 읽을 때(투영 지문)."""
        cache_key = (kind, field)
        pairs = self._column_cache.get(cache_key)
        if pairs is None:
            pairs = tuple((key, record.get(field)) for key, record in self._ordered(kind) if record.get(field) is not None)
            self._column_cache[cache_key] = pairs
        return pairs

    def extend_writers(self, writers):
        """같은 레코드·block_version 을 더 넓은 권한표 `writers` 아래로 옮긴 새 스냅샷(sizing O7, 2026-10-08 사용자 승인).

        * `writers` 는 이 스냅샷 권한표의 모든 ((kind, field), writer) 를 같은 writer 로 포함해야 한다 -- 빠진 항목이나 다른
          writer 는 `WriterPermissionError`(이미 쓴 필드의 출처가 표와 어긋나게 되므로). WriterTable 아니면 `TypeError`.
        * 레코드 객체는 그대로 공유한다(`is`, 구조 공유), `fp`·값·필드 메타·`block_version` 이 이 스냅샷과 같다.
        * 이 스냅샷은 바뀌지 않는다. 표가 같으면 `self` 그대로.
        """
        if not isinstance(writers, WriterTable):
            raise TypeError("extend_writers: writers 는 WriterTable 이어야 한다")
        if writers == self.writers:
            return self
        for (kind, field), writer in self.writers.entries:
            if writers.writer_of(kind, field) != writer:
                raise WriterPermissionError(
                    "extend_writers: 새 권한표가 " + repr((kind, field)) + " 의 writer " + repr(writer) + " 를 유지하지 않는다"
                )
        return GraphSnapshot(writers, self.tables, self.block_versions)

    def widen(self, writers):
        """권한표를 이 표와 `writers` 의 합(`WriterTable.union`)으로 넓힌 스냅샷(`extend_writers`). 이미 덮으면 `self` 그대로.
        S0 수준 층(설계 40 §2.4.1)은 층마다 자기 필드 표를 더하며 한 스냅샷 위에 산다."""
        return self.extend_writers(self.writers.union(writers))

    def derive_child(self, keep_writers):
        """writer 가 `keep_writers` 안인 필드와 그 writer 의 `block_version` 만 남긴 새 스냅샷(계획 N3.3 스냅샷 파생 규칙, O-61 P1).

        * 평가 커널이 parent 스냅샷에서 출발할 때 쓴다 -- 커널 밖 writer 의 낡은 필드는 '없음'이 '낡은 값'보다 안전하므로 eager 로 뺀다.
        * 권한표는 그대로, 남기는 레코드의 필드 `FieldValue` 는 객체째 공유한다(구조 공유). 필드가 다 빠진 레코드는 두지 않는다.
        * `keep_writers` 에 이 스냅샷이 모르는 이름이 있어도 거부하지 않는다(교집합). 이 스냅샷은 바뀌지 않는다.
        """
        keep = frozenset(keep_writers)
        tables = {}
        for kind, records in self.tables.items():
            kept = {}
            for key, record in records.items():
                fields = tuple((name, fv) for name, fv in record.fields if fv.writer in keep)
                if len(fields) == len(record.fields):
                    kept[key] = record
                elif fields:
                    kept[key] = GraphRecord(kind, key, fields)
            tables[kind] = kept
        versions = {writer: version for writer, version in self.block_versions.items() if writer in keep}
        return GraphSnapshot(self.writers, tables, versions)

    def block_version(self, writer):
        """`writer` 의 마지막 쓰기 입력 버전, 쓴 적 없으면 None."""
        return self.block_versions.get(writer)

    def write(self, writer, input_version, columns):
        """graph setter. `columns`: {(kind, field): {key: value}} -- 각 (kind, field) 열을 통째로 바꾼다.

        * (kind, field) 마다 `writers.require(writer, kind, field)` -- 위반이면 `WriterPermissionError`.
        * 열에 없는 key 의 그 필드는 지운다(필드가 다 빠진 레코드는 없어진다). 없는 레코드는 만든다.
        * 값·입력 버전이 모두 같은 필드는 기존 FieldValue 를 그대로 둔다(쓰기 횟수 불변).
          다르면 새 FieldValue(쓰기 횟수 = 이전 + 1, 처음이면 1).
        * 값은 불변이어야 한다(`TypeError`). key 는 문자열(`TypeError`).
        * `block_version(writer)` = `input_version` 이 된다.
        * 아무것도 바뀌지 않으면(레코드·block_version 모두) `self` 를 그대로 돌려준다.
        """
        if not isinstance(input_version, str) or not input_version:
            raise ValueError("write: input_version 은 비어 있지 않은 문자열이어야 한다")
        if not isinstance(columns, Mapping):
            raise TypeError("write: columns 는 {(kind, field): {key: value}} 매핑이어야 한다")
        pending = {}
        changed = False
        for (kind, field), values in sorted_items(columns):
            self.writers.require(writer, kind, field)
            if not isinstance(values, Mapping):
                raise TypeError("write: 열 " + repr((kind, field)) + " 은 {key: value} 매핑이어야 한다")
            for key in values:
                if not isinstance(key, str):
                    raise TypeError("write: key 는 문자열이어야 한다")
            base = self.tables.get(kind, {})
            kind_pending = pending.setdefault(kind, {})
            for key, _ in self.column_fields(kind, field):
                if key not in values:
                    del _touch(kind_pending, base, key)[field]
                    changed = True
            for key, value in sorted_items(values):
                record = base.get(key)
                old = None if record is None else record.get(field)
                count = 1 if old is None else old.write_count + 1
                new = FieldValue(value, writer, input_version, count)
                if old is not None and old.value_fp == new.value_fp and old.input_version == input_version:
                    continue
                _touch(kind_pending, base, key)[field] = new
                changed = True
        tables = dict(self.tables)
        for kind, kind_pending in pending.items():
            records = dict(tables.get(kind, {}))
            for key, fields in kind_pending.items():
                if fields:
                    records[key] = GraphRecord(kind, key, tuple(fields.items()))
                else:
                    records.pop(key, None)
            tables[kind] = records
        if not changed and self.block_versions.get(writer) == input_version:
            return self
        versions = dict(self.block_versions)
        versions[writer] = input_version
        return GraphSnapshot(self.writers, tables, versions)

