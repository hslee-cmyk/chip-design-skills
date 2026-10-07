"""graph/s1_values.py -- 값 형식·어휘·필드 권한표 (계약 0절·3절·4절·5절).

기대값은 계약 문장(표의 글자)에서 옮겼다. 피검 모듈의 값으로 기대값을 만들지 않는다.
"""
from __future__ import annotations

import dataclasses

import pytest

from gmid_engine.core import WriterTable, fp_of, require_immutable
from gmid_engine.graph import (
    AC_GROUND_GATE_ONLY,
    AC_GROUND_RAIL,
    BRANCH_MULTI_DOMAIN,
    BRANCH_POTENTIAL_TIE,
    BULK_DECLARED,
    BULK_DEFAULT_RULE,
    BULK_NEEDS_SUPPLIES,
    BULK_UNDETERMINED,
    BULK_UNSUPPORTED_KIND,
    ELEMENT_MOS,
    ELEMENT_PASSIVE,
    ELEMENT_SOURCE,
    MOS_TERMINAL_NAMES,
    NO_SUPPLIES_FP,
    RESERVED_FIELDS,
    S1_BULK_WRITER,
    S1_RULE_FILES,
    S1_STRUCTURE_WRITER,
    S1_WRITERS,
    UNSUPPORTED_BRANCHES,
    UNSUPPORTED_RULE_BRANCH,
    BulkResult,
    FieldNotComputed,
    S1Key,
)

# 계약 4.1 표 (writer s1_structure)
STRUCTURE_FIELDS = (
    ("node", "terminals"), ("node", "is_rail"), ("node", "port_direction"), ("node", "port_role"),
    ("node", "ac_ground_class"),
    ("device", "element_class"), ("device", "kind"), ("device", "pins"), ("device", "bulk_declared"),
    ("device", "is_diode"), ("device", "value_key"), ("device", "value"), ("device", "unsupported"),
)
# 계약 4.3 표
RESERVED = (
    ("device", "dc_role", "dc_roles"),
    ("edge", "relation", "relations"),
    ("graph", "branches", "dc_conduction"),
    ("graph", "columns", "columns"),
)


def test_vocabulary_strings_match_contract():
    assert S1_STRUCTURE_WRITER == "s1_structure"
    assert S1_BULK_WRITER == "s1_bulk"
    assert AC_GROUND_RAIL == "rail"
    assert AC_GROUND_GATE_ONLY == "gate_only_undriven"
    assert (ELEMENT_MOS, ELEMENT_PASSIVE, ELEMENT_SOURCE) == ("mos", "passive", "ideal_source")
    assert MOS_TERMINAL_NAMES == ("d", "g", "s")
    assert NO_SUPPLIES_FP == "none"
    assert (BULK_DECLARED, BULK_DEFAULT_RULE, BULK_UNDETERMINED) == ("declared", "default_rule", "undetermined")
    assert (BULK_NEEDS_SUPPLIES, BULK_UNSUPPORTED_KIND) == ("needs_supplies_v", "unsupported_kind")
    assert BRANCH_MULTI_DOMAIN == "bulk_multi_domain"
    assert BRANCH_POTENTIAL_TIE == "bulk_rail_potential_tie"
    assert UNSUPPORTED_RULE_BRANCH == "unsupported_rule_branch"


def test_unsupported_branches_per_element_class():
    # 계약 4.1 `unsupported` 행: 원소 분류마다 분기 이름 하나
    assert dict(UNSUPPORTED_BRANCHES) == {
        "mos": "mos_kind_unsupported",
        "passive": "passive_kind_unsupported",
        "ideal_source": "source_kind_unsupported",
    }


def test_rule_files_are_contract_list():
    # 계약 3절: S1_RULE_FILES = (ac_ground_static, bulk_default, s1_build, s1_index, s1_structure, s1_values, supplies).py
    assert tuple(S1_RULE_FILES) == (
        "ac_ground_static.py", "bulk_default.py", "s1_build.py", "s1_index.py",
        "s1_structure.py", "s1_values.py", "supplies.py",
    )
    assert "s1_key.py" not in S1_RULE_FILES and "s1_model.py" not in S1_RULE_FILES


def test_writer_table_is_exactly_contract_fields():
    assert isinstance(S1_WRITERS, WriterTable)
    expected = {(k, f): S1_STRUCTURE_WRITER for k, f in STRUCTURE_FIELDS}
    expected[("device", "bulk")] = S1_BULK_WRITER
    for k, f, w in RESERVED:
        expected[(k, f)] = w
    assert dict(S1_WRITERS.entries) == expected
    assert len(S1_WRITERS.entries) == len(STRUCTURE_FIELDS) + 1 + len(RESERVED)
    assert S1_WRITERS.fields_of(S1_BULK_WRITER) == (("device", "bulk"),)
    assert S1_WRITERS.fields_of(S1_STRUCTURE_WRITER) == tuple(sorted(STRUCTURE_FIELDS))


def test_reserved_fields_table():
    assert tuple(RESERVED_FIELDS) == RESERVED
    for k, f, w in RESERVED_FIELDS:
        assert S1_WRITERS.writer_of(k, f) == w


def test_s1key_frozen_and_equality_by_three_values():
    a = S1Key("t" * 64, "r" * 64, "none")
    b = S1Key("t" * 64, "r" * 64, "none")
    assert dataclasses.is_dataclass(S1Key)
    assert [f.name for f in dataclasses.fields(S1Key)] == ["topology_fp", "rule_fp", "supplies_v_fp"]
    assert a == b and a is not b
    assert a != S1Key("t" * 64, "r" * 64, "x" * 64)
    assert a != S1Key("t" * 64, "q" * 64, "none")
    assert a != S1Key("u" * 64, "r" * 64, "none")
    with pytest.raises(dataclasses.FrozenInstanceError):
        a.rule_fp = "x"  # type: ignore[misc]
    require_immutable(a)
    assert fp_of(a) == fp_of(b)


def test_bulk_result_fields_and_immutability():
    assert [f.name for f in dataclasses.fields(BulkResult)] == ["net", "origin", "reason"]
    r = BulkResult("vdd", "default_rule", None)
    require_immutable(r)
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.net = "gnd"  # type: ignore[misc]
    assert r == BulkResult("vdd", "default_rule", None)
    assert fp_of(r) != fp_of(BulkResult("gnd", "default_rule", None))


def test_field_not_computed_is_lookup_error():
    assert issubclass(FieldNotComputed, LookupError)
    assert not issubclass(LookupError, FieldNotComputed)
