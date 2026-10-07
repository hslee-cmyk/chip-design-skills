"""graph/rel_matching.py -- `s1_rel_matching`: matching_ratio·l_class(비레일 gate gs 묶음)·matching_offset(계약 4.5, 7.5).

기대값 = JSON 직접 집계(oracle)와 계약 7.5 표(파일럿 matching_offset 3묶음 포함).
"""
from __future__ import annotations

import pytest

from gmid_engine.core import ComputeBlock
from gmid_engine.graph import S1_REL_MATCHING_WRITER, build_s1, s1_rel_matching

SIX = (
    "common_gate_amplifier", "current_reuse_telescopic_ota", "ngcc_3stage_ff",
    "pushpull_follower_buffer", "sf_pushpull_output_opamp", "two_stage_ota_sf",
)
NINE = tuple(sorted(SIX + ("folded_cascode", "nmcnr_amplifier", "two_stage_ota")))
# 계약 7.5 표: (matching_ratio = l_class 수, matching_offset {멤버: status})
TABLE = {
    "common_gate_amplifier": (0, {}),
    "current_reuse_telescopic_ota": (3, {("M37a", "M37b"): "derived", ("M4a", "M4b", "M63"): "review_needed",
                                         ("M1a", "M1b", "M58"): "review_needed"}),
    "folded_cascode": (3, {("M1", "M2"): "derived"}),
    "ngcc_3stage_ff": (5, {("M1", "M2"): "derived"}),
    "nmcnr_amplifier": (3, {("M102", "M103"): "derived"}),
    "pushpull_follower_buffer": (0, {}),
    "sf_pushpull_output_opamp": (4, {("M1", "M2"): "derived"}),
    "two_stage_ota": (2, {("M1", "M2"): "derived"}),
    "two_stage_ota_sf": (2, {("M1", "M2"): "derived"}),
}


def _s1(gh, name):
    return build_s1(gh.load_lib(name), gh.supplies_for(name))


@pytest.mark.parametrize("name", NINE)
def test_oracle_matches_table(gh, name):
    o = gh.oracle(gh.raw(name))
    n, off = TABLE[name]
    assert len(o.matching_ratio) == len(o.l_class) == n
    assert {x[2]: x[3] for x in o.matching_offset} == off


@pytest.mark.parametrize("name", NINE)
def test_matching_ratio_and_l_class(gh, name):
    o = gh.oracle(gh.raw(name))
    s1 = _s1(gh, name)
    mr = gh.gval(s1, "rel_matching_ratio")
    assert sorted((r.type, r.domain, r.members, r.status, r.evidence.nets) for r in mr) == sorted(o.matching_ratio)
    lc = gh.gval(s1, "rel_l_class")
    assert sorted((r.type, r.domain, r.members, r.status, r.evidence.basis) for r in lc) == sorted(o.l_class)
    assert sorted(r.members for r in mr) == sorted(r.members for r in lc)


@pytest.mark.parametrize("name", NINE)
def test_matching_offset(gh, name):
    o = gh.oracle(gh.raw(name))
    rels = gh.gval(_s1(gh, name), "rel_matching_offset")
    got = sorted((r.type, r.domain, r.members, r.status, r.evidence.nets, r.evidence.basis) for r in rels)
    assert got == sorted(o.matching_offset)
    for r in rels:
        assert list(r.members) == sorted(r.members)


def test_rail_gate_group_is_not_mirror(gh, tmp_path):
    # gate 가 레일인 gs 묶음은 equal_vgs 는 있어도 matching_ratio·l_class 는 없다
    raw = gh.raw("pushpull_follower_buffer")
    raw["netlist"] += [{"name": "Mg1", "kind": "nmos", "drain": "A", "gate": "vdd", "source": "vss"},
                       {"name": "Mg2", "kind": "nmos", "drain": "B", "gate": "vdd", "source": "vss"}]
    s1 = build_s1(gh.load_raw(tmp_path, raw), gh.supplies_for("pushpull_follower_buffer"))
    assert ("Mg1", "Mg2") in [r.members for r in gh.gval(s1, "rel_equal_vgs")]
    assert gh.gval(s1, "rel_matching_ratio") == () and gh.gval(s1, "rel_l_class") == ()


def test_block_declaration():
    assert isinstance(s1_rel_matching, ComputeBlock)
    assert s1_rel_matching.name == S1_REL_MATCHING_WRITER
    assert set(s1_rel_matching.reads) == {("graph", "gs_groups"), ("device", "element_class"), ("device", "kind"),
                                          ("device", "pins"), ("node", "is_rail")}
    assert set(s1_rel_matching.writes) == {("graph", "rel_l_class"), ("graph", "rel_matching_offset"),
                                           ("graph", "rel_matching_ratio")}
