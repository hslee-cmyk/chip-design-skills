"""graph/s1_values.py -- 값 형식·어휘·필드 권한표 (계약 0절·3절·4절·5절).

기대값은 계약 문장(표의 글자)에서 옮겼다. 피검 모듈의 값으로 기대값을 만들지 않는다.
"""
from __future__ import annotations

import dataclasses

import pytest

import gmid_engine.graph as graph_pkg
from gmid_engine.core import WriterTable, fp_of, require_immutable
from gmid_engine.graph import (
    AC_GROUND_GATE_ONLY,
    AC_GROUND_RAIL,
    BRANCH_COLUMN_BUDGET,
    BRANCH_DC_ISOLATED_LOOP,
    BRANCH_DC_SELF_LOOP,
    BRANCH_GVGS_SELF_EDGE,
    BRANCH_MOS_KIND,
    BRANCH_MULTI_DOMAIN,
    BRANCH_POTENTIAL_TIE,
    BULK_DECLARED,
    BULK_DEFAULT_RULE,
    BULK_NEEDS_SUPPLIES,
    BULK_UNDETERMINED,
    BULK_UNSUPPORTED_KIND,
    COLUMN_RULE,
    CYCLE_V2_RAIL,
    CYCLE_V2_ZERO,
    DOMAIN_DC,
    DOMAIN_DC_TO_SS,
    DOMAIN_GEOM,
    ELEMENT_MOS,
    ELEMENT_PASSIVE,
    ELEMENT_SOURCE,
    GRAPH_KEY,
    J_ALL_VIEW_GROUND,
    J_DIFF_PAIR,
    J_GVGS_READING,
    J_IDEAL_SOURCE,
    J_L_CLASS,
    J_PARALLEL_MERGE,
    J_PRUNE_ORDER,
    J_RAIL_PAIRS,
    J_UNRESOLVED_GROUP,
    MOS_TERMINAL_NAMES,
    NO_SUPPLIES_FP,
    REL_EQUAL_VGS,
    REL_KCL_GROUP,
    REL_KVL_BRANCH,
    REL_L_CLASS,
    REL_MATCHING_OFFSET,
    REL_MATCHING_RATIO,
    REL_PORT_DIFF,
    REL_VDS_EQ_VGS,
    REL_VDS_SATURATION,
    ROLE_BIAS,
    ROLE_DIODE,
    ROLE_SIGNAL,
    S1_BRANCHES_WRITER,
    S1_BULK_WRITER,
    S1_COLUMNS_WRITER,
    S1_DC_CONDUCTION_WRITER,
    S1_DC_ROLES_WRITER,
    S1_GS_GROUPS_WRITER,
    S1_GVGS_WRITER,
    S1_REL_KCL_WRITER,
    S1_REL_MATCHING_WRITER,
    S1_REL_VGS_WRITER,
    S1_RULE_FILES,
    S1_STRUCTURE_WRITER,
    S1_WRITERS,
    STATUS_DERIVED,
    STATUS_PROPOSED,
    STATUS_REVIEW_NEEDED,
    UNSUPPORTED_BRANCHES,
    UNSUPPORTED_RULE_BRANCH,
    Branch,
    BulkResult,
    Column,
    ColumnOrphan,
    DcRole,
    Evidence,
    FieldNotComputed,
    GsGroup,
    GvgsSummary,
    RelEdge,
    S1Key,
    Segment,
)

# 계약 4.1 표 (writer s1_structure, C1 dc_nets 포함)
STRUCTURE_FIELDS = (
    ("node", "terminals"), ("node", "is_rail"), ("node", "port_direction"), ("node", "port_role"),
    ("node", "ac_ground_class"),
    ("device", "element_class"), ("device", "kind"), ("device", "pins"), ("device", "dc_nets"),
    ("device", "bulk_declared"), ("device", "is_diode"), ("device", "value_key"), ("device", "value"),
    ("device", "unsupported"),
)
# 계약 4.2~4.5 writes (writer 이름 = 블록 이름)
U_FIELDS = {
    "s1_bulk": (("device", "bulk"),),
    "s1_dc_conduction": (("graph", "dc_pruned"), ("graph", "dc_segments")),
    "s1_branches": (("graph", "branches"), ("node", "dc_branch_node")),
    "s1_columns": (("graph", "columns"), ("graph", "column_pairs"), ("graph", "column_orphans")),
    "s1_gs_groups": (("graph", "gs_groups"),),
    "s1_dc_roles": (("device", "dc_role"),),
    "s1_rel_vgs": (("graph", "rel_equal_vgs"), ("graph", "rel_vds_eq_vgs")),
    "s1_rel_kcl": (("graph", "rel_kcl_group"),),
    "s1_rel_matching": (("graph", "rel_matching_ratio"), ("graph", "rel_l_class")),
    "s1_matching_groups": (("graph", "rel_matching_offset"), ("graph", "matching_groups"),
                           ("graph", "matching_dispositions")),
    "s1_gvgs": (("graph", "rel_kvl_branch"), ("graph", "gvgs_summary")),
}


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


def test_u2_u4_vocabulary_matches_contract():
    # 계약 4절 머리·4.3~4.6 의 글자
    assert GRAPH_KEY == "s1"
    assert (STATUS_DERIVED, STATUS_PROPOSED, STATUS_REVIEW_NEEDED) == ("derived", "proposed", "review_needed")
    assert (DOMAIN_DC, DOMAIN_DC_TO_SS, DOMAIN_GEOM) == ("dc", "dc_to_ss", "geom")
    assert (BRANCH_DC_SELF_LOOP, BRANCH_DC_ISOLATED_LOOP) == ("dc_self_loop", "dc_isolated_loop")
    assert BRANCH_COLUMN_BUDGET == "column_enumeration_over_budget"
    assert BRANCH_GVGS_SELF_EDGE == "gvgs_self_edge"
    assert BRANCH_MOS_KIND == "mos_kind_unsupported"
    assert COLUMN_RULE == "rail_pair_simple_path"
    assert (CYCLE_V2_RAIL, CYCLE_V2_ZERO) == ("v2_rail", "v2_zero")
    assert (ROLE_DIODE, ROLE_BIAS, ROLE_SIGNAL) == ("diode_reference", "bias_current_source", "signal")
    assert (REL_EQUAL_VGS, REL_VDS_EQ_VGS, REL_KCL_GROUP, REL_MATCHING_RATIO, REL_L_CLASS, REL_MATCHING_OFFSET,
            REL_KVL_BRANCH, REL_PORT_DIFF, REL_VDS_SATURATION) == (
        "equal_vgs", "vds_eq_vgs", "kcl_group", "matching_ratio", "l_class", "matching_offset",
        "kvl_branch", "port_diff", "vds_saturation")
    # J 항목 ID(계약 4절 Evidence 문단 + 4.3~4.5 에서 각 ID 가 붙는 자리)
    assert (J_PARALLEL_MERGE, J_PRUNE_ORDER, J_RAIL_PAIRS, J_IDEAL_SOURCE) == ("J13-a", "J13-b", "J13-c", "J13-d")
    assert (J_ALL_VIEW_GROUND, J_UNRESOLVED_GROUP) == ("J-U3-a", "J-U3-c")
    assert (J_L_CLASS, J_DIFF_PAIR, J_GVGS_READING) == ("J-U4-a", "J-U4-b", "J12-c")


def test_writer_constants_are_block_names():
    assert (S1_DC_CONDUCTION_WRITER, S1_BRANCHES_WRITER, S1_COLUMNS_WRITER, S1_GS_GROUPS_WRITER, S1_DC_ROLES_WRITER,
            S1_REL_VGS_WRITER, S1_REL_KCL_WRITER, S1_REL_MATCHING_WRITER, S1_GVGS_WRITER) == (
        "s1_dc_conduction", "s1_branches", "s1_columns", "s1_gs_groups", "s1_dc_roles",
        "s1_rel_vgs", "s1_rel_kcl", "s1_rel_matching", "s1_gvgs")


def test_unsupported_branches_per_element_class():
    # 계약 4.1 `unsupported` 행: 원소 분류마다 분기 이름 하나
    assert dict(UNSUPPORTED_BRANCHES) == {
        "mos": "mos_kind_unsupported",
        "passive": "passive_kind_unsupported",
        "ideal_source": "source_kind_unsupported",
    }


def test_rule_files_are_contract_list():
    # 계약 3절: graph 파일 17개(s1_key.py·s1_model.py 제외)
    assert tuple(S1_RULE_FILES) == (
        "ac_ground_static.py", "branches.py", "bulk_default.py", "columns.py", "dc_conduction.py", "dc_roles.py",
        "gs_groups.py", "gvgs_cycles.py", "matching_groups.py", "rel_kcl.py", "rel_matching.py", "rel_vgs.py",
        "s1_build.py",
        "s1_index.py", "s1_structure.py", "s1_values.py", "supplies.py",
    )
    assert "s1_key.py" not in S1_RULE_FILES and "s1_model.py" not in S1_RULE_FILES


def test_writer_table_is_exactly_contract_fields():
    assert isinstance(S1_WRITERS, WriterTable)
    expected = {(k, f): S1_STRUCTURE_WRITER for k, f in STRUCTURE_FIELDS}
    for w, fields in U_FIELDS.items():
        for kf in fields:
            expected[kf] = w
    assert dict(S1_WRITERS.entries) == expected
    assert len(S1_WRITERS.entries) == len(STRUCTURE_FIELDS) + sum(len(v) for v in U_FIELDS.values())
    assert S1_WRITERS.fields_of(S1_STRUCTURE_WRITER) == tuple(sorted(STRUCTURE_FIELDS))
    for w, fields in U_FIELDS.items():
        assert S1_WRITERS.fields_of(w) == tuple(sorted(fields))
    # C2: edge kind 필드 없음, 예약 상수 없음
    assert not any(k == "edge" for (k, _), _w in S1_WRITERS.entries)
    assert not hasattr(graph_pkg, "RESERVED_FIELDS") and "RESERVED_FIELDS" not in graph_pkg.__all__


@pytest.mark.parametrize("cls,fields", [
    (Evidence, ["rule", "nets", "group", "basis"]),
    (Segment, ["nets", "elements"]),
    (Branch, ["id", "ends", "segments", "has_ideal_source"]),
    (Column, ["id", "rails", "branch_order", "parallel_expansion", "status", "evidence"]),
    (GsGroup, ["kind", "gate", "source", "members"]),
    (DcRole, ["role", "status", "evidence"]),
    (RelEdge, ["type", "domain", "members", "status", "evidence"]),
    (GvgsSummary, ["cyclomatic", "v2_port0", "v2_port1", "v1", "fixed_vgs", "port_diff", "vds_saturation"]),
])
def test_value_types_are_frozen_dataclasses(cls, fields):
    assert dataclasses.is_dataclass(cls)
    assert [f.name for f in dataclasses.fields(cls)] == fields
    assert cls.__dataclass_params__.frozen


def test_evidence_defaults_and_immutability():
    e = Evidence("r")
    assert (e.nets, e.group, e.basis) == ((), (), ())
    require_immutable(e)
    require_immutable(Evidence("r", ("a",), ("M1",), (J_PARALLEL_MERGE,)))
    with pytest.raises(dataclasses.FrozenInstanceError):
        e.rule = "x"  # type: ignore[misc]


def test_column_orphan_is_frozen():
    assert dataclasses.is_dataclass(ColumnOrphan) and ColumnOrphan.__dataclass_params__.frozen
    assert len(dataclasses.fields(ColumnOrphan)) == 2


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
