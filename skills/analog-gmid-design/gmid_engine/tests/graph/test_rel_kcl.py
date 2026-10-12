"""graph/rel_kcl.py -- `s1_rel_kcl`: segment 2개 이상인 가지마다 kcl_group(계약 4.5, 7.5).

기대값 = oracle 가지(독립 구현)에서 직접 만든 kcl_group 과 계약 7.5 표.
"""
from __future__ import annotations

import pytest

from gmid_engine.core import ComputeBlock, GraphSnapshot
from gmid_engine.graph import S1_REL_KCL_WRITER, S1_WRITERS, build_s1, s1_rel_kcl

SIX = (
    "common_gate_amplifier", "current_reuse_telescopic_ota", "ngcc_3stage_ff",
    "pushpull_follower_buffer", "sf_pushpull_output_opamp", "two_stage_ota_sf",
)
NINE = tuple(sorted(SIX + ("folded_cascode", "nmcnr_amplifier", "two_stage_ota")))
TABLE = {"common_gate_amplifier": 1, "current_reuse_telescopic_ota": 18, "folded_cascode": 3, "ngcc_3stage_ff": 6,
         "nmcnr_amplifier": 4, "pushpull_follower_buffer": 3, "sf_pushpull_output_opamp": 8, "two_stage_ota": 3,
         "two_stage_ota_sf": 4}


def _s1(gh, name):
    return build_s1(gh.load_lib(name), gh.supplies_for(name))


@pytest.mark.parametrize("name", NINE)
def test_kcl_groups(gh, name):
    o = gh.oracle(gh.raw(name))
    s1 = _s1(gh, name)
    rels = gh.gval(s1, "rel_kcl_group")
    got = sorted((r.type, r.domain, r.members, r.status, r.evidence.nets, r.evidence.basis) for r in rels)
    assert got == sorted(o.kcl_group)
    assert len(rels) == TABLE[name] == len(o.kcl_group)
    # members 는 가지의 segment 원소 tuple 을 걷는 순서 그대로
    walks = {tuple(s.elements for s in b.segments) for b in gh.gval(s1, "branches") if len(b.segments) >= 2}
    assert {r.members for r in rels} == walks


def test_block_declaration():
    assert isinstance(s1_rel_kcl, ComputeBlock)
    assert s1_rel_kcl.name == S1_REL_KCL_WRITER
    assert tuple(s1_rel_kcl.reads) == (("graph", "branches"),)
    assert tuple(s1_rel_kcl.writes) == (("graph", "rel_kcl_group"),)


def test_direct_call_without_branches_key_error():
    with pytest.raises(KeyError):
        s1_rel_kcl(GraphSnapshot.empty(S1_WRITERS))
