"""graph/rel_matching.py -- `s1_rel_matching`: matching_ratio·l_class(비레일 gate gs 묶음)(계약 4.5, 7.5).

기대값 = JSON 직접 집계(oracle)와 계약 7.5 표. matching_offset 은 2026-10-07 Q8 (iii) 로 writer 가
`s1_matching_groups`(matching_groups.py, 계약 4.5a)로 옮겨 이 파일에서 뺐다(그 test 는 test_matching_groups.py 몫).
"""
from __future__ import annotations

import pytest

from gmid_engine.core import ComputeBlock
from gmid_engine.graph import S1_REL_MATCHING_WRITER, build_s1, s1_rel_matching


def _build(*args, **kw):
    """`build_s1(..., donors=, counters=)` -- [XRUN-F1 card B C0·C6] 부를 때마다 새 실행 하나(새 open_run() 쌍)."""
    from gmid_engine.search import open_run
    donors, counters = open_run()
    return build_s1(*args, donors=donors, counters=counters, **kw)

SIX = (
    "common_gate_amplifier", "current_reuse_telescopic_ota", "ngcc_3stage_ff",
    "pushpull_follower_buffer", "sf_pushpull_output_opamp", "two_stage_ota_sf",
)
NINE = tuple(sorted(SIX + ("folded_cascode", "nmcnr_amplifier", "two_stage_ota")))
# 계약 7.5 표: matching_ratio = l_class 수
TABLE = {
    "common_gate_amplifier": 0,
    "current_reuse_telescopic_ota": 3,
    "folded_cascode": 3,
    "ngcc_3stage_ff": 5,
    "nmcnr_amplifier": 3,
    "pushpull_follower_buffer": 0,
    "sf_pushpull_output_opamp": 4,
    "two_stage_ota": 2,
    "two_stage_ota_sf": 2,
}


def _s1(gh, name):
    return _build(gh.load_lib(name), gh.supplies_for(name))


@pytest.mark.parametrize("name", NINE)
def test_oracle_matches_table(gh, name):
    o = gh.oracle(gh.raw(name))
    assert len(o.matching_ratio) == len(o.l_class) == TABLE[name]


@pytest.mark.parametrize("name", NINE)
def test_matching_ratio_and_l_class(gh, name):
    o = gh.oracle(gh.raw(name))
    s1 = _s1(gh, name)
    mr = gh.gval(s1, "rel_matching_ratio")
    assert sorted((r.type, r.domain, r.members, r.status, r.evidence.nets) for r in mr) == sorted(o.matching_ratio)
    lc = gh.gval(s1, "rel_l_class")
    assert sorted((r.type, r.domain, r.members, r.status, r.evidence.basis) for r in lc) == sorted(o.l_class)
    assert sorted(r.members for r in mr) == sorted(r.members for r in lc)


def test_rail_gate_group_is_not_mirror(gh, tmp_path):
    # gate 가 레일인 gs 묶음은 equal_vgs 는 있어도 matching_ratio·l_class 는 없다
    raw = gh.raw("pushpull_follower_buffer")
    raw["netlist"] += [{"name": "Mg1", "kind": "nmos", "drain": "A", "gate": "vdd", "source": "vss"},
                       {"name": "Mg2", "kind": "nmos", "drain": "B", "gate": "vdd", "source": "vss"}]
    raw.pop("source_manifest", None)    # 변형 문서: 소자 수가 출처 그림과 달라졌다 -- 출처 개수 선언을 뗀다(authoring 10절, 키 없으면 검사 안 함)
    s1 = _build(gh.load_raw(tmp_path, raw), gh.supplies_for("pushpull_follower_buffer"))
    assert ("Mg1", "Mg2") in [r.members for r in gh.gval(s1, "rel_equal_vgs")]
    assert gh.gval(s1, "rel_matching_ratio") == () and gh.gval(s1, "rel_l_class") == ()


def test_block_declaration():
    assert isinstance(s1_rel_matching, ComputeBlock)
    assert s1_rel_matching.name == S1_REL_MATCHING_WRITER
    assert set(s1_rel_matching.reads) == {("graph", "gs_groups"), ("node", "is_rail")}
    assert set(s1_rel_matching.writes) == {("graph", "rel_l_class"), ("graph", "rel_matching_ratio")}
