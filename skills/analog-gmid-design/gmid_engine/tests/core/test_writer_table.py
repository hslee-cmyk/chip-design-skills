"""CONTRACT §5.1·5.3 ENTITY_KINDS, WriterTable -- 정규화(정렬·중복 제거), 조회, require 권한, 잘못된 선언 거부."""
import dataclasses

import pytest

from gmid_engine.core import ENTITY_KINDS, WriterPermissionError, WriterTable, fp_of


def test_entity_kinds_exact():
    assert ENTITY_KINDS == ("device", "edge", "graph", "node")


ENTRIES = [
    ("node", "v", "bias"),
    ("device", "w", "sizer"),
    ("device", "l", "sizer"),
    ("graph", "theta", "search"),
]


def test_frozen_dataclass():
    t = WriterTable(ENTRIES)
    assert dataclasses.is_dataclass(t)
    with pytest.raises(dataclasses.FrozenInstanceError):
        t.entries = ()


def test_entries_normalized_sorted():
    t = WriterTable(ENTRIES)
    assert t.entries == (
        (("device", "l"), "sizer"),
        (("device", "w"), "sizer"),
        (("graph", "theta"), "search"),
        (("node", "v"), "bias"),
    )


def test_duplicates_collapse_and_order_irrelevant():
    t1 = WriterTable(ENTRIES)
    t2 = WriterTable(list(reversed(ENTRIES)) + [("node", "v", "bias"), ("device", "w", "sizer")])
    assert t1 == t2
    assert t1.entries == t2.entries
    assert fp_of(t1) == fp_of(t2)


def test_different_tables_differ():
    t1 = WriterTable(ENTRIES)
    t2 = WriterTable(ENTRIES[:-1])
    assert t1 != t2
    assert fp_of(t1) != fp_of(t2)


def test_writer_of():
    t = WriterTable(ENTRIES)
    assert t.writer_of("device", "w") == "sizer"
    assert t.writer_of("node", "v") == "bias"
    assert t.writer_of("node", "w") is None
    assert t.writer_of("edge", "v") is None


def test_fields_of():
    t = WriterTable(ENTRIES)
    assert t.fields_of("sizer") == (("device", "l"), ("device", "w"))
    assert t.fields_of("search") == (("graph", "theta"),)
    assert t.fields_of("nobody") == ()


def test_require_assigned_ok():
    t = WriterTable(ENTRIES)
    assert t.require("sizer", "device", "w") is None


def test_require_other_writer_rejected():
    t = WriterTable(ENTRIES)
    with pytest.raises(WriterPermissionError):
        t.require("bias", "device", "w")


def test_require_undeclared_rejected():
    t = WriterTable(ENTRIES)
    with pytest.raises(WriterPermissionError):
        t.require("sizer", "device", "undeclared")


def test_two_writers_same_field_rejected():
    with pytest.raises(WriterPermissionError):
        WriterTable([("node", "v", "a"), ("node", "v", "b")])


def test_empty_table_ok():
    t = WriterTable([])
    assert t.entries == ()
    assert t.writer_of("node", "v") is None
    with pytest.raises(WriterPermissionError):
        t.require("a", "node", "v")


@pytest.mark.parametrize(
    "entry",
    [
        ("vertex", "v", "w"),          # kind 밖
        ("Node", "v", "w"),            # kind 대소문자 다름
        ("node", "", "w"),             # field 빈
        ("node", 3, "w"),              # field 비문자열
        ("node", "v", ""),             # writer 빈
        ("node", "v", None),           # writer 비문자열
        "abc",                         # 항목이 str (길이 3이라도)
        ("node", "v"),                 # 원소 2개
        ("node", "v", "w", "x"),       # 원소 4개
    ],
    ids=["kind_unknown", "kind_case", "field_empty", "field_nonstr", "writer_empty", "writer_none",
         "entry_str", "entry_len2", "entry_len4"],
)
def test_bad_entry_value_error(entry):
    with pytest.raises(ValueError):
        WriterTable([("device", "w", "sizer"), entry])
