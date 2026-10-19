"""graph/s1_structure.py -- writer `s1_structure` 의 node·device 구조 필드(계약 4.1) + 블록 직접 호출(6절).

기대값 = topology JSON 직접 집계(conftest JsonAgg). 계약 7.1 표 숫자로 집계를 교차 확인한다.
"""
from __future__ import annotations

import pytest

from gmid_engine.core import ComputeBlock, GraphSnapshot, StructureUnresolvedError
from gmid_engine.graph import (
    AC_GROUND_GATE_ONLY,
    ELEMENT_MOS,
    ELEMENT_PASSIVE,
    ELEMENT_SOURCE,
    S1_STRUCTURE_WRITER,
    S1_WRITERS,
    build_s1,
    s1_structure,
)

SIX = (
    "common_gate_amplifier", "current_reuse_telescopic_ota", "ngcc_3stage_ff",
    "pushpull_follower_buffer", "sf_pushpull_output_opamp", "two_stage_ota_sf",
)

# 9회로 전부(2026-10-07 topology 정정 b9c7042 뒤 모두 load 통과) -- JSON 직접 집계 대조용
NINE = tuple(sorted(SIX + ("folded_cascode", "nmcnr_amplifier", "two_stage_ota")))
# 계약 7.1 표: (node 수, 레일, n, p, 수동, 이상원, is_diode 참, in, out)
TABLE = {
    "common_gate_amplifier": (7, ("gnd", "vdd"), 2, 1, 0, 0, (), 1, 1),
    "current_reuse_telescopic_ota": (37, ("gnd", "vdd"), 24, 27, 12, 1, (
        "M11a", "M11b", "M14a", "M14b", "M18_bg", "M20a", "M20b", "M23a", "M24b", "M36a", "M36b", "M39",
        "M40", "M57", "M64", "M66"), 2, 2),
    "ngcc_3stage_ff": (13, ("gnd", "vdd"), 9, 7, 3, 0, ("M3", "M6A", "M9"), 2, 1),
    "pushpull_follower_buffer": (9, ("agnd", "vdd", "vss"), 3, 3, 1, 0, (), 1, 1),
    "sf_pushpull_output_opamp": (23, ("agnd", "vdd", "vss"), 11, 11, 5, 1, ("M4",), 2, 1),
    "two_stage_ota_sf": (10, ("gnd", "vdd"), 6, 3, 2, 0, ("M3",), 2, 1),
}
NODE_FIELDS = ("ac_ground_class", "is_rail", "port_direction", "port_role", "terminals")


def _build(*args, **kw):
    """`build_s1(..., donors=, counters=)` -- [XRUN-F1 card B C0·C6] 부를 때마다 새 실행 하나(새 open_run() 쌍)."""
    from gmid_engine.search import open_run
    donors, counters = open_run()
    return build_s1(*args, donors=donors, counters=counters, **kw)


def _s1(gh, name):
    return _build(gh.load_lib(name), gh.supplies_for(name))


@pytest.mark.parametrize("name", SIX)
def test_json_aggregate_matches_contract_table(gh, name):
    agg = gh.agg(gh.raw(name))
    nodes, rails, n, p, npas, nsrc, diodes, nin, nout = TABLE[name]
    assert (len(agg.nodes), tuple(sorted(agg.rails)), agg.n_kind, agg.p_kind) == (nodes, rails, n, p)
    assert (len(agg.passives), len(agg.sources), agg.diodes, agg.n_in, agg.n_out) == (npas, nsrc, diodes, nin, nout)


@pytest.mark.parametrize("name", NINE)
def test_node_fields(gh, name):
    agg = gh.agg(gh.raw(name))
    s1 = _s1(gh, name)
    snap = s1.snapshot
    assert snap.keys("node") == agg.nodes
    for f in NODE_FIELDS:
        col = s1.column("node", f)
        assert tuple(k for k, _ in col) == agg.nodes, f       # 모든 node 에 5필드
        fv = snap.field("node", agg.nodes[0], f)
        assert fv.writer == S1_STRUCTURE_WRITER
    for net in agg.nodes:
        assert s1.value("node", net, "terminals") == agg.terminals.get(net, ())
        assert s1.value("node", net, "is_rail") is (net in agg.rails)
        port = agg.ports.get(net)
        assert s1.value("node", net, "port_direction") == (port["direction"] if port else None)
        assert s1.value("node", net, "port_role") == (port["role"] if port else None)
        assert s1.value("node", net, "ac_ground_class") == agg.ac_class(net)
    gate_only = tuple(k for k, v in s1.column("node", "ac_ground_class") if v == AC_GROUND_GATE_ONLY)
    assert gate_only == agg.gate_only


@pytest.mark.parametrize("name", NINE)
def test_device_fields(gh, name):
    agg = gh.agg(gh.raw(name))
    s1 = _s1(gh, name)
    all_names = tuple(sorted(set(agg.mos) | set(agg.passives) | set(agg.sources)))
    assert s1.snapshot.keys("device") == all_names
    cls = dict(s1.column("device", "element_class"))
    assert sorted(k for k, v in cls.items() if v == ELEMENT_MOS) == sorted(agg.mos)
    assert sorted(k for k, v in cls.items() if v == ELEMENT_PASSIVE) == sorted(agg.passives)
    assert sorted(k for k, v in cls.items() if v == ELEMENT_SOURCE) == sorted(agg.sources)
    kinds = dict(s1.column("device", "kind"))
    for n, e in {**agg.mos, **agg.passives, **agg.sources}.items():
        assert kinds[n] == e["kind"]
    for n, e in agg.mos.items():
        assert s1.value("device", n, "pins") == (("d", e["drain"]), ("g", e["gate"]), ("s", e["source"]))
        assert s1.value("device", n, "bulk_declared") == e.get("bulk")
        assert s1.value("device", n, "is_diode") is (e["gate"] == e["drain"])
    for n, e in {**agg.passives, **agg.sources}.items():
        assert s1.value("device", n, "pins") == (("t0", e["terminals"][0]), ("t1", e["terminals"][1]))
        vkeys = [k for k in e if k.startswith("value_") and k != "value_from_spec"]
        assert s1.value("device", n, "value_key") == (vkeys[0] if vkeys else None)
        assert s1.value("device", n, "value") == (e[vkeys[0]] if vkeys else None)
    # 필드 대상 범위: MOS 전용 / 2단자 전용
    assert tuple(k for k, _ in s1.column("device", "is_diode")) == tuple(sorted(agg.mos))
    assert tuple(k for k, _ in s1.column("device", "bulk_declared")) == tuple(sorted(agg.mos))
    assert tuple(k for k, _ in s1.column("device", "value_key")) == tuple(sorted(set(agg.passives) | set(agg.sources)))
    assert tuple(k for k, v in s1.column("device", "is_diode") if v) == agg.diodes
    assert s1.column("device", "unsupported") == ()           # 6회로 모두 지원 kind


@pytest.mark.parametrize("name", NINE)
def test_dc_nets_field_c1(gh, name):
    # C1: 모든 원소에 dc_nets -- MOS (d, s) 정렬, 저항·이상원 terminals 정렬, 커패시터 None
    agg = gh.agg(gh.raw(name))
    s1 = _s1(gh, name)
    col = dict(s1.column("device", "dc_nets"))
    assert set(col) == set(agg.mos) | set(agg.passives) | set(agg.sources)
    for n, e in agg.mos.items():
        assert col[n] == tuple(sorted((e["drain"], e["source"])))
    for n, e in agg.passives.items():
        assert col[n] == (tuple(sorted(e["terminals"])) if e["kind"] == "resistor" else None)
    for n, e in agg.sources.items():
        assert col[n] == tuple(sorted(e["terminals"]))


def test_bulk_only_net_is_node_without_terminals(gh, tmp_path):
    raw = gh.raw("common_gate_amplifier")
    raw["supply_nets"] = ["vdd", "gnd", "vsub"]                 # bulk 로만 닿는 레일
    for e in raw["netlist"]:
        e["bulk"] = "VB_well" if e["kind"] == "pmos" else "vsub"
    agg = gh.agg(raw)
    s1 = _build(gh.load_raw(tmp_path, raw), {"vdd": 1.8, "gnd": 0.0, "vsub": 0.0})
    assert s1.snapshot.keys("node") == agg.nodes
    for net in ("VB_well", "vsub"):
        assert s1.value("node", net, "terminals") == ()
    assert s1.value("node", "VB_well", "ac_ground_class") is None   # 단자 없는 넷 -> None
    assert s1.value("node", "VB_well", "is_rail") is False
    assert s1.value("node", "vsub", "is_rail") is True
    assert s1.value("device", "M3", "bulk_declared") == "VB_well"
    assert s1.value("device", "M1", "bulk_declared") == "vsub"


def test_bulk_only_rail_is_ac_ground_rail(gh, tmp_path):
    """계약 4.1: `AC_GROUND_RAIL` = 레일. '그 밖(단자 없는 넷 포함) None' 은 레일이 아닌 넷의 경우다 --
    bulk 로만 닿아 단자가 없는 레일도 레일이므로 "rail"."""
    raw = gh.raw("common_gate_amplifier")
    raw["supply_nets"] = ["vdd", "gnd", "vsub"]
    for e in raw["netlist"]:                    # 전부 선언 -> 기본 규칙 대상 없음(vsub·gnd 동률이어도 정지 검사 미적용)
        e["bulk"] = "vsub" if e["kind"] == "nmos" else "vdd"
    s1 = _build(gh.load_raw(tmp_path, raw), {"vdd": 1.8, "gnd": 0.0, "vsub": 0.0})
    assert s1.value("node", "vsub", "terminals") == ()
    assert s1.value("node", "vsub", "is_rail") is True
    assert s1.value("node", "vsub", "ac_ground_class") == "rail"


@pytest.mark.parametrize("where,kind,branch", [
    ("netlist", "njfet", "mos_kind_unsupported"),
    ("passive_elements", "inductor", "passive_kind_unsupported"),
    ("ideal_sources", "voltage_source", "source_kind_unsupported"),
])
def test_unsupported_kind_recorded_then_stopped_by_u2(gh, tmp_path, where, kind, branch):
    """s1_structure 는 기록만 하고(4.1), 정지는 소비자 s1_dc_conduction 이 한다(4.3·4.6, 9절 10)."""
    raw = gh.raw("sf_pushpull_output_opamp")
    target = raw[where][0]
    name = target["name"]
    target["kind"] = kind
    if where == "ideal_sources":
        v = target.pop("value_amp", None)
        target["value_volt"] = v
    doc = gh.load_raw(tmp_path, raw)
    snap = gh.structure_and_bulk(doc, None)                        # 기록 단계는 정지하지 않는다
    assert snap.column("device", "unsupported") == ((name, branch),)
    assert snap.value("device", name, "kind") == kind
    with pytest.raises(StructureUnresolvedError) as ei:
        _build(doc, None)
    d = dict(ei.value.record.detail)
    assert (d["reason"], d["rule_branch"], d["nets"]) == ("unsupported_rule_branch", branch, ())
    assert ei.value.record.devices == (name,)


def test_supported_kinds_have_no_unsupported_field(gh):
    s1 = _s1(gh, "current_reuse_telescopic_ota")
    with pytest.raises(KeyError):
        s1.value("device", "M6", "unsupported")


def test_direct_block_call_matches_build(gh):
    name = "pushpull_follower_buffer"
    doc = gh.load_lib(name)
    assert isinstance(s1_structure, ComputeBlock) and s1_structure.name == S1_STRUCTURE_WRITER
    assert s1_structure.reads == ()
    run = gh.fresh_run()
    base = GraphSnapshot.empty(S1_WRITERS)
    snap = s1_structure(base, doc.devices, doc.passives, doc.sources, tuple(sorted(doc.rails)), doc.ports, **run)
    assert snap.block_version(S1_STRUCTURE_WRITER) is not None
    ref = _build(doc, None).snapshot
    for kind in ("node", "device"):
        assert snap.keys(kind) == ref.keys(kind)
        for f in ("terminals", "is_rail", "ac_ground_class") if kind == "node" else ("pins", "kind", "element_class"):
            assert snap.column(kind, f) == ref.column(kind, f)
    # 같은 입력으로 다시 부르면 재사용(같은 객체, 실행 계수(card B C1) reuses +1)
    before = gh.block_row(run["counters"], s1_structure.name)
    again = s1_structure(snap, doc.devices, doc.passives, doc.sources, tuple(sorted(doc.rails)), doc.ports, **run)
    after = gh.block_row(run["counters"], s1_structure.name)
    assert again is snap
    assert (after[1] - before[1], after[4] - before[4]) == (1, 0)


def test_direct_block_rejects_mutable_extras(gh):
    # card B C4: extras 불변 검사 TypeError 는 그 호출을 계수에 넣지 않는다
    doc = gh.load_lib("common_gate_amplifier")
    run = gh.fresh_run()
    with pytest.raises(TypeError):
        s1_structure(GraphSnapshot.empty(S1_WRITERS), list(doc.devices), doc.passives, doc.sources,
                     tuple(sorted(doc.rails)), doc.ports, **run)
    assert gh.block_row(run["counters"], s1_structure.name) == (0, 0, 0, 0, 0, 0)
