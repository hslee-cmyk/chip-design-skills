"""graph/gvgs_cycles.py -- `s1_gvgs`: G_vgs 순환수·kvl_branch·v1(port_diff)·VDS-1(vds_saturation)·fixed_vgs(계약 4.5, 4.6, 7.5).

기대값 = 독립 oracle: G = MOS 마다 (gate, source) 무향 엣지(모든 레일 = 고정 노드 F), 평행 엣지는 이름순 첫 소자,
c(H) = |E| − |V| + 성분 수로 개수를 직접 계산, 비다리 엣지는 '빼면 c 가 1 줄어드는 엣지'로 판정, VDS-1 은 BFS 최단 거리.
사이클 대표 소자는 이름 tie-break 이라(7.5) 개수·사이클 유효성·불변량으로 비교한다.
"""
from __future__ import annotations

import collections

import pytest

from gmid_engine.core import ComputeBlock
from gmid_engine.graph import S1_GVGS_WRITER, GvgsSummary, build_s1, s1_gvgs


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
# 계약 7.5 표: (cyclomatic, v2_port0, v2_port1, v1, fixed_vgs, VDS-1)
TABLE = {
    "common_gate_amplifier": (0, 0, 0, 0, 0, 0),
    "current_reuse_telescopic_ota": (5, 4, 0, 1, 0, 22),
    "folded_cascode": (0, 0, 0, 0, 0, 1),
    "ngcc_3stage_ff": (0, 0, 0, 0, 0, 6),
    "nmcnr_amplifier": (0, 0, 0, 0, 0, 4),
    "pushpull_follower_buffer": (1, 0, 1, 0, 0, 0),
    "sf_pushpull_output_opamp": (1, 1, 0, 0, 0, 0),
    "two_stage_ota": (0, 0, 0, 0, 0, 1),
    "two_stage_ota_sf": (0, 0, 0, 0, 0, 1),
}
F = "\x00F"


def _s1(gh, name):
    return _build(gh.load_lib(name), gh.supplies_for(name))


def _summary(gh, s1):
    s = gh.gval(s1, "gvgs_summary")
    assert isinstance(s, GvgsSummary)
    return s


@pytest.mark.parametrize("name", NINE)
def test_oracle_matches_contract_table(gh, name):
    o = gh.oracle(gh.raw(name))
    assert (o.cyclomatic, o.v2_port0, o.v2_port1, o.v1, len(o.fixed_vgs), len(o.vds1)) == TABLE[name]


@pytest.mark.parametrize("name", NINE)
def test_counts_match_oracle(gh, name):
    o = gh.oracle(gh.raw(name))
    s = _summary(gh, _s1(gh, name))
    assert (s.cyclomatic, s.v2_port0, s.v2_port1, s.v1) == (o.cyclomatic, o.v2_port0, o.v2_port1, o.v1)
    assert s.cyclomatic == s.v2_port0 + s.v2_port1 + s.v1
    assert tuple(sorted(s.fixed_vgs)) == o.fixed_vgs


def _cycle_nodes(o, members):
    """대표 소자 멤버가 G_vgs 의 단순 사이클 하나를 이루는지 확인하고 노드 집합을 돌려준다."""
    assert len(set(members)) == len(members)
    edges = [o.gs_edges[m] for m in members]                 # 대표 소자가 아니면 KeyError
    deg = collections.Counter(n for e in edges for n in e)
    assert set(deg.values()) == {2}
    assert len(deg) == len(edges)                            # 단순 사이클: 노드 수 = 엣지 수
    # 연결성
    adj = collections.defaultdict(set)
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    start = next(iter(adj))
    seen, stack = {start}, [start]
    while stack:
        x = stack.pop()
        for y in adj[x] - seen:
            seen.add(y)
            stack.append(y)
    assert seen == set(deg)
    return set(deg)


@pytest.mark.parametrize("name", NINE)
def test_kvl_branch_cycles(gh, name):
    o = gh.oracle(gh.raw(name))
    s1 = _s1(gh, name)
    kvl = gh.gval(s1, "rel_kvl_branch")
    assert len(kvl) == o.v2_port0 + o.v2_port1
    ports = set(o.input_ports)
    by_ports = collections.Counter()
    for r in kvl:
        assert (r.type, r.domain, r.status, r.evidence.basis) == ("kvl_branch", "dc", "derived", ("J12-c",))
        assert list(r.members) == sorted(r.members)
        nodes = _cycle_nodes(o, r.members)
        assert r.evidence.rule == ("v2_rail" if F in nodes else "v2_zero")
        assert r.evidence.nets == tuple(sorted(nodes - {F}))
        by_ports[len(nodes & ports)] += 1
    assert by_ports[0] == o.v2_port0                         # 0 단계: 포트 없는 사이클
    assert by_ports[1] == o.v2_port1                         # p 단계: 포트 하나를 지나는 사이클
    assert set(by_ports) <= {0, 1}


@pytest.mark.parametrize("name", NINE)
def test_port_diff_cycles(gh, name):
    o = gh.oracle(gh.raw(name))
    s = _summary(gh, _s1(gh, name))
    assert len(s.port_diff) == o.v1
    for r in s.port_diff:
        assert (r.type, r.domain, r.status, r.evidence.basis) == ("port_diff", "dc", "derived", ("J12-c",))
        nodes = _cycle_nodes(o, r.members)
        assert len(nodes & set(o.input_ports)) >= 2


@pytest.mark.parametrize("name", NINE)
def test_union_of_cycle_members_is_non_bridge_edges(gh, name):
    o = gh.oracle(gh.raw(name))
    s1 = _s1(gh, name)
    members = {m for r in gh.gval(s1, "rel_kvl_branch") for m in r.members}
    members |= {m for r in _summary(gh, s1).port_diff for m in r.members}
    assert members == set(o.non_bridge)


@pytest.mark.parametrize("name", NINE)
def test_vds_saturation(gh, name):
    o = gh.oracle(gh.raw(name))
    s = _summary(gh, _s1(gh, name))
    assert sorted(r.members[0] for r in s.vds_saturation) == sorted(o.vds1)
    for r in s.vds_saturation:
        assert (r.type, r.domain, r.status, r.evidence.basis) == ("vds_saturation", "dc", "derived", ("J12-c",))
        dev = o.mos[r.members[0]]
        cur = o._node(dev["drain"])
        for m in r.members[1:]:                               # drain 쪽부터 Gs 경로
            a, b = o.gs_edges[m]
            assert cur in (a, b)
            cur = b if a == cur else a
        assert cur == o._node(dev["source"])
        assert len(r.members) - 1 == o.vds1[r.members[0]]     # 최단 경로


def test_pilot_values(gh):
    s1 = _s1(gh, "current_reuse_telescopic_ota")
    s = _summary(gh, s1)
    assert (s.cyclomatic, s.v2_port0, s.v2_port1, s.v1) == (5, 4, 0, 1)
    assert all(r.evidence.rule == "v2_rail" for r in gh.gval(s1, "rel_kvl_branch"))
    assert len(s.vds_saturation) == 22


def test_fixed_vgs(gh, tmp_path):
    # gate·source 둘 다 레일 -> fixed_vgs 에만(G 엣지 아님)
    raw = gh.raw("two_stage_ota")
    raw["netlist"].append({"name": "Mfix", "kind": "nmos", "drain": "OUT", "gate": "vdd", "source": "gnd"})
    o = gh.oracle(raw)
    raw.pop("source_manifest", None)    # 변형 문서: 소자 수가 출처 그림과 달라졌다 -- 출처 개수 선언을 뗀다(authoring 10절, 키 없으면 검사 안 함)
    s = _summary(gh, _build(gh.load_raw(tmp_path, raw), {"vdd": 1.8, "gnd": 0.0}))
    assert tuple(sorted(s.fixed_vgs)) == o.fixed_vgs == ("Mfix",)
    assert s.cyclomatic == o.cyclomatic


def test_parallel_vgs_edges_counted_once(gh, tmp_path):
    # 같은 (gate, source) 엣지 둘 = 단순 그래프에서 하나(v0 = equal_vgs) -> 순환수 변화 없음
    raw = gh.raw("two_stage_ota_sf")
    base = gh.oracle(raw).cyclomatic
    m = next(e for e in raw["netlist"] if e["source"] not in raw["supply_nets"])
    raw["netlist"].append({"name": "Zdup", "kind": m["kind"], "drain": m["drain"], "gate": m["gate"], "source": m["source"]})
    raw.pop("source_manifest", None)    # 변형 문서: 소자 수가 출처 그림과 달라졌다 -- 출처 개수 선언을 뗀다(authoring 10절, 키 없으면 검사 안 함)
    s = _summary(gh, _build(gh.load_raw(tmp_path, raw), {"vdd": 1.8, "gnd": 0.0}))
    assert s.cyclomatic == base == gh.oracle(raw).cyclomatic


def test_gate_equals_source_stops(gh, tmp_path):
    # 7.6: gate == source(비레일 tail 넷) MOS 추가 -> gvgs_self_edge
    raw = gh.raw("two_stage_ota")
    tail = next(e["source"] for e in raw["netlist"] if e["source"] not in raw["supply_nets"])
    raw["netlist"].append({"name": "Mgs", "kind": "nmos", "drain": "OUT", "gate": tail, "source": tail})
    o_err = pytest.raises(gh.StopExpected, gh.oracle, raw).value
    raw.pop("source_manifest", None)    # 변형 문서: 소자 수가 출처 그림과 달라졌다 -- 출처 개수 선언을 뗀다(authoring 10절, 키 없으면 검사 안 함)
    d, devices = gh.stop(lambda: _build(gh.load_raw(tmp_path, raw), {"vdd": 1.8, "gnd": 0.0}))
    assert d["rule_branch"] == o_err.branch == "gvgs_self_edge"
    assert devices == ("Mgs",)
    assert d["nets"] == (tail,)


def test_gate_equals_source_on_rail_is_fixed_not_stop(gh, tmp_path):
    raw = gh.raw("two_stage_ota")
    raw["netlist"].append({"name": "Moff", "kind": "nmos", "drain": "OUT", "gate": "gnd", "source": "gnd"})
    raw.pop("source_manifest", None)    # 변형 문서: 소자 수가 출처 그림과 달라졌다 -- 출처 개수 선언을 뗀다(authoring 10절, 키 없으면 검사 안 함)
    s = _summary(gh, _build(gh.load_raw(tmp_path, raw), {"vdd": 1.8, "gnd": 0.0}))
    assert "Moff" in s.fixed_vgs


def test_block_declaration():
    assert isinstance(s1_gvgs, ComputeBlock)
    assert s1_gvgs.name == S1_GVGS_WRITER
    assert set(s1_gvgs.reads) == {("device", "element_class"), ("device", "is_diode"), ("device", "kind"),
                                  ("device", "pins"), ("node", "is_rail"), ("node", "port_direction")}
    assert set(s1_gvgs.writes) == {("graph", "gvgs_summary"), ("graph", "rel_kvl_branch")}
