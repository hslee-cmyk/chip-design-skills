"""graph/rel_vgs.py -- `s1_rel_vgs`: equal_vgs(gs 묶음마다)·vds_eq_vgs(diode 마다) 관계 엣지(계약 4.5, 7.5).

기대값 = JSON 직접 집계(oracle: gs 묶음·diode = gate==drain)와 계약 7.5 표. 계약이 정하지 않은 evidence 칸(group·basis 등)은
비교하지 않는다. 순서는 계약에 없어 정렬해 비교한다.
"""
from __future__ import annotations

import pytest

from gmid_engine.core import ComputeBlock
from gmid_engine.graph import S1_REL_VGS_WRITER, RelEdge, build_s1, s1_rel_vgs

SIX = (
    "common_gate_amplifier", "current_reuse_telescopic_ota", "ngcc_3stage_ff",
    "pushpull_follower_buffer", "sf_pushpull_output_opamp", "two_stage_ota_sf",
)
NINE = tuple(sorted(SIX + ("folded_cascode", "nmcnr_amplifier", "two_stage_ota")))
# 계약 7.5 표: (equal_vgs, vds_eq_vgs)
TABLE = {"common_gate_amplifier": (0, 0), "current_reuse_telescopic_ota": (3, 16), "folded_cascode": (3, 4),
         "ngcc_3stage_ff": (5, 3), "nmcnr_amplifier": (3, 2), "pushpull_follower_buffer": (0, 0),
         "sf_pushpull_output_opamp": (4, 1), "two_stage_ota": (2, 1), "two_stage_ota_sf": (2, 1)}


def _s1(gh, name):
    return build_s1(gh.load_lib(name), gh.supplies_for(name))


@pytest.mark.parametrize("name", NINE)
def test_equal_vgs(gh, name):
    o = gh.oracle(gh.raw(name))
    rels = gh.gval(_s1(gh, name), "rel_equal_vgs")
    assert all(isinstance(r, RelEdge) for r in rels)
    got = sorted((r.type, r.domain, r.members, r.status, r.evidence.nets) for r in rels)
    assert got == sorted(o.equal_vgs)
    assert all(r.evidence.rule == "equal_vgs" for r in rels)
    assert len(rels) == TABLE[name][0]


@pytest.mark.parametrize("name", NINE)
def test_vds_eq_vgs(gh, name):
    o = gh.oracle(gh.raw(name))
    agg = gh.agg(gh.raw(name))
    rels = gh.gval(_s1(gh, name), "rel_vds_eq_vgs")
    got = sorted((r.type, r.domain, r.members, r.status, r.evidence.nets) for r in rels)
    assert got == sorted(o.vds_eq_vgs)
    assert sorted(r.members[0] for r in rels) == list(agg.diodes)
    assert len(rels) == TABLE[name][1]


def test_block_declaration():
    assert isinstance(s1_rel_vgs, ComputeBlock)
    assert s1_rel_vgs.name == S1_REL_VGS_WRITER
    assert set(s1_rel_vgs.reads) == {("graph", "gs_groups"), ("device", "is_diode"), ("device", "pins")}
    assert set(s1_rel_vgs.writes) == {("graph", "rel_equal_vgs"), ("graph", "rel_vds_eq_vgs")}
