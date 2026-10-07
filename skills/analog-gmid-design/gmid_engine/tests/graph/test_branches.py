"""graph/branches.py -- `s1_branches`: 분기 노드·가지(계약 4.3 U2, 4.6 dc_isolated_loop, 7.3).

기대값 = 독립 oracle(segment 그래프에서 닻·극대 직렬 사슬을 다시 걸음)과 계약 7.3 표(합침/따로).
'따로' = 병렬 원소를 원소별 엣지로 풀어 같은 정의로 센 값(oracle merge=False).
"""
from __future__ import annotations

import pytest

from gmid_engine.core import ComputeBlock, GraphSnapshot
from gmid_engine.graph import S1_BRANCHES_WRITER, S1_WRITERS, Branch, build_s1, s1_branches

SIX = (
    "common_gate_amplifier", "current_reuse_telescopic_ota", "ngcc_3stage_ff",
    "pushpull_follower_buffer", "sf_pushpull_output_opamp", "two_stage_ota_sf",
)
NINE = tuple(sorted(SIX + ("folded_cascode", "nmcnr_amplifier", "two_stage_ota")))
# 계약 7.3 표: (분기 노드 합침, 따로, 가지 합침, 따로, 이상원 가지)
TABLE = {
    "common_gate_amplifier": (0, 0, 1, 1, 0),
    "current_reuse_telescopic_ota": (7, 9, 27, 32, 1),
    "folded_cascode": (3, 3, 8, 8, 1),
    "ngcc_3stage_ff": (1, 3, 7, 12, 0),
    "nmcnr_amplifier": (3, 4, 10, 12, 0),
    "pushpull_follower_buffer": (0, 0, 3, 3, 0),
    "sf_pushpull_output_opamp": (1, 1, 9, 9, 1),
    "two_stage_ota": (1, 1, 4, 4, 0),
    "two_stage_ota_sf": (1, 1, 5, 5, 0),
}


def _s1(gh, name):
    return build_s1(gh.load_lib(name), gh.supplies_for(name))


@pytest.mark.parametrize("name", NINE)
def test_oracle_matches_contract_table(gh, name):
    raw = gh.raw(name)
    merged, split = gh.oracle(raw), gh.oracle(raw, merge=False)
    bn_m, bn_s, br_m, br_s, src = TABLE[name]
    assert (len(merged.branch_nodes), len(split.branch_nodes)) == (bn_m, bn_s)
    assert (len(merged.branches), len(split.branches)) == (br_m, br_s)
    assert sum(1 for b in merged.branches if b[3]) == src


@pytest.mark.parametrize("name", NINE)
def test_branches_match_oracle(gh, name):
    o = gh.oracle(gh.raw(name))
    s1 = _s1(gh, name)
    brs = gh.gval(s1, "branches")
    assert all(isinstance(b, Branch) for b in brs)
    assert tuple(gh.branch_plain(b) for b in brs) == o.branches
    assert [b.id for b in brs] == list(range(len(brs)))


@pytest.mark.parametrize("name", NINE)
def test_branch_node_field_on_every_node(gh, name):
    o = gh.oracle(gh.raw(name))
    agg = gh.agg(gh.raw(name))
    s1 = _s1(gh, name)
    col = dict(s1.column("node", "dc_branch_node"))
    assert tuple(col) == agg.nodes
    assert all(isinstance(v, bool) for v in col.values())
    assert {k for k, v in col.items() if v} == set(o.branch_nodes)
    assert not any(col[r] for r in agg.rails)


@pytest.mark.parametrize("name", NINE)
def test_branch_invariants(gh, name):
    # 가지마다: segment 가 걷는 순서로 이어지고(인접 segment 가 넷 공유), 양 끝은 닻, 내부 넷은 닻이 아니다.
    s1 = _s1(gh, name)
    agg = gh.agg(gh.raw(name))
    segs = gh.gval(s1, "dc_segments")
    deg = {}
    for s in segs:
        for n in s.nets:
            deg[n] = deg.get(n, 0) + 1
    anchors = set(agg.rails) | {n for n, d in deg.items() if d == 1 or (d >= 3 and n not in agg.rails)}
    used = []
    for b in gh.gval(s1, "branches"):
        cur = b.ends[0]
        assert cur in anchors
        for i, s in enumerate(b.segments):
            assert cur in s.nets
            cur = s.nets[1] if s.nets[0] == cur else s.nets[0]
            if i < len(b.segments) - 1:
                assert cur not in anchors
        assert cur == b.ends[1] and cur in anchors
        used += [gh.seg_plain(s) for s in b.segments]
        srcs = {el for s in b.segments for el in s.elements} & set(agg.sources)
        assert b.has_ideal_source is bool(srcs)
    # 모든 segment 가 정확히 한 가지에
    assert sorted(used) == sorted(gh.seg_plain(s) for s in segs)


def test_isolated_loop_stops(gh, tmp_path):
    # 7.6 변형: 새 넷 la·lb·lc 위 MOS 3개 고리(gate = 첫 netlist 소자의 gate) -> dc_isolated_loop
    raw = gh.raw("two_stage_ota")
    gate = raw["netlist"][0]["gate"]
    raw["netlist"] += [
        {"name": "Mla", "kind": "nmos", "drain": "la", "gate": gate, "source": "lb"},
        {"name": "Mlb", "kind": "nmos", "drain": "lb", "gate": gate, "source": "lc"},
        {"name": "Mlc", "kind": "nmos", "drain": "lc", "gate": gate, "source": "la"},
    ]
    o_err = pytest.raises(gh.StopExpected, gh.oracle, raw).value
    d, devices = gh.stop(lambda: build_s1(gh.load_raw(tmp_path, raw), {"vdd": 1.8, "gnd": 0.0}))
    assert d["rule_branch"] == o_err.branch == "dc_isolated_loop"
    assert devices == o_err.devices == ("Mla", "Mlb", "Mlc")
    assert d["nets"] == o_err.detail["nets"] == ("la", "lb", "lc")


def test_loop_through_anchor_is_a_branch_not_a_stop(gh, tmp_path):
    # 레일에 닿는 고리는 닻이 있어 정지하지 않는다(ends 가 같은 닻인 가지 하나)
    raw = gh.raw("two_stage_ota")
    gate = raw["netlist"][0]["gate"]
    raw["netlist"] += [                         # gnd - ra - rb - gnd (ra·rb 는 차수 2, 닻 아님)
        {"name": "Mra", "kind": "nmos", "drain": "ra", "gate": gate, "source": "gnd"},
        {"name": "Mrb", "kind": "nmos", "drain": "rb", "gate": gate, "source": "ra"},
        {"name": "Mrc", "kind": "nmos", "drain": "gnd", "gate": gate, "source": "rb"},
    ]
    o = gh.oracle(raw)
    s1 = build_s1(gh.load_raw(tmp_path, raw), {"vdd": 1.8, "gnd": 0.0})
    assert tuple(gh.branch_plain(b) for b in gh.gval(s1, "branches")) == o.branches
    loops = [b for b in gh.gval(s1, "branches") if b.ends[0] == b.ends[1]]
    assert [b.ends for b in loops] == [("gnd", "gnd")]


def test_block_declaration():
    assert isinstance(s1_branches, ComputeBlock)
    assert s1_branches.name == S1_BRANCHES_WRITER
    assert set(s1_branches.reads) == {("graph", "dc_segments"), ("device", "element_class"), ("node", "is_rail")}
    assert set(s1_branches.writes) == {("graph", "branches"), ("node", "dc_branch_node")}


def test_direct_call_without_predecessor_key_error():
    # 계약 6절: 선행 블록 필드가 없으면 projection 의 graph 값 조회가 KeyError
    with pytest.raises(KeyError):
        s1_branches(GraphSnapshot.empty(S1_WRITERS))
