"""graph/dc_conduction.py -- `s1_dc_conduction`: 정지 검사·잎 가지치기·병렬 합침 segment (계약 4.3 U2, 4.6, 7.3, 7.6).

기대값 = test 쪽 독립 oracle(graph_u2_oracle.U2Oracle: JSON 에서 DC 엣지·가지치기·합침을 다시 구현)과 계약 7.3 표.
"""
from __future__ import annotations

import pytest

from gmid_engine.core import ComputeBlock
from gmid_engine.graph import S1_DC_CONDUCTION_WRITER, Segment, build_s1, s1_dc_conduction

SIX = (
    "common_gate_amplifier", "current_reuse_telescopic_ota", "ngcc_3stage_ff",
    "pushpull_follower_buffer", "sf_pushpull_output_opamp", "two_stage_ota_sf",
)
NINE = tuple(sorted(SIX + ("folded_cascode", "nmcnr_amplifier", "two_stage_ota")))
# 계약 7.3 표: dc_pruned, segment 수, 병렬 segment(원소 tuple)
TABLE = {
    "common_gate_amplifier": ((), 3, ()),
    "current_reuse_telescopic_ota": ((("Rz1", 1), ("Rz2", 1)), 51, (("M18a", "M18b"), ("M6", "M7"), ("M9a", "M9b"))),
    "folded_cascode": ((), 14, ()),
    "ngcc_3stage_ff": ((), 13, (("M13", "M14", "M7"), ("M6A", "M6B"))),
    "nmcnr_amplifier": ((("Rm", 1),), 15, (("M301", "RL"),)),
    "pushpull_follower_buffer": ((), 6, ()),
    "sf_pushpull_output_opamp": ((), 26, ()),
    "two_stage_ota": ((("Rz", 1),), 7, ()),
    "two_stage_ota_sf": ((), 9, ()),
}


def _s1(gh, name):
    return build_s1(gh.load_lib(name), gh.supplies_for(name))


@pytest.mark.parametrize("name", NINE)
def test_oracle_matches_contract_table(gh, name):
    o = gh.oracle(gh.raw(name))
    pruned, nseg, par = TABLE[name]
    assert o.dc_pruned == pruned
    assert len(o.segments) == nseg
    assert tuple(sorted(e for _, e in o.segments if len(e) > 1)) == par


@pytest.mark.parametrize("name", NINE)
def test_pruned_and_segments_match_oracle(gh, name):
    o = gh.oracle(gh.raw(name))
    s1 = _s1(gh, name)
    assert gh.gval(s1, "dc_pruned") == o.dc_pruned
    segs = gh.gval(s1, "dc_segments")
    assert all(isinstance(s, Segment) for s in segs)
    assert tuple(gh.seg_plain(s) for s in segs) == o.segments
    # 형식: nets 정렬 2-tuple, elements 이름순, nets 순
    assert [s.nets for s in segs] == sorted(s.nets for s in segs)
    for s in segs:
        assert s.nets == tuple(sorted(s.nets)) and s.nets[0] != s.nets[1]
        assert list(s.elements) == sorted(s.elements)
    # 남은 원소 + 가지친 원소 = DC 엣지 원소 전부(커패시터 제외), 중복 없음
    seg_els = [el for s in segs for el in s.elements]
    assert len(seg_els) == len(set(seg_els))
    dc_elements = {k for k, v in s1.column("device", "dc_nets") if v is not None}
    assert set(seg_els) | {el for el, _ in o.dc_pruned} == dc_elements


def _base(gh):
    raw = gh.raw("two_stage_ota_sf")
    return raw, gh.agg(raw)


def test_leaf_resistor_chain_pruned_in_rounds(gh, tmp_path):
    raw, agg = _base(gh)
    inner = next(n for n in sorted(agg.terminals) if n not in agg.rails and n not in agg.ports)
    raw["passive_elements"] += [
        {"name": "Rq1", "kind": "resistor", "terminals": [inner, "nq1"], "value_ohm": 1e3},
        {"name": "Rq2", "kind": "resistor", "terminals": ["nq1", "nq2"], "value_ohm": 1e3},
        {"name": "Cq", "kind": "capacitor", "terminals": ["nq2", "gnd"], "value_farad": 1e-12},   # 차수에 안 든다
    ]
    o = gh.oracle(raw)
    assert o.dc_pruned == (("Rq2", 1), ("Rq1", 2))
    s1 = build_s1(gh.load_raw(tmp_path, raw), {"vdd": 1.8, "gnd": 0.0})
    assert gh.gval(s1, "dc_pruned") == (("Rq2", 1), ("Rq1", 2))
    assert tuple(gh.seg_plain(s) for s in gh.gval(s1, "dc_segments")) == o.segments
    assert not {"Rq1", "Rq2"} & {el for s in gh.gval(s1, "dc_segments") for el in s.elements}


def test_resistor_on_port_or_rail_is_kept_and_mos_leaf_not_pruned(gh, tmp_path):
    raw, agg = _base(gh)
    out = next(k for k, v in agg.ports.items() if v["direction"] == "output")
    raw["passive_elements"].append({"name": "Rload", "kind": "resistor", "terminals": [out, "gnd"], "value_ohm": 1e4})
    gate = raw["netlist"][0]["gate"]
    raw["netlist"].append({"name": "Mleaf", "kind": "nmos", "drain": "dleaf", "gate": gate, "source": "gnd"})
    s1 = build_s1(gh.load_raw(tmp_path, raw), {"vdd": 1.8, "gnd": 0.0})
    assert gh.gval(s1, "dc_pruned") == ()
    els = {el for s in gh.gval(s1, "dc_segments") for el in s.elements}
    assert {"Rload", "Mleaf"} <= els
    assert tuple(gh.seg_plain(s) for s in gh.gval(s1, "dc_segments")) == gh.oracle(raw).segments


def test_parallel_merge_ignores_kind(gh, tmp_path):
    # J13-a 기본안: MOS 와 저항이 같은 넷 쌍이면 한 segment (nmcnr M301∥RL 과 같은 꼴을 합성)
    raw, _ = _base(gh)
    m = raw["netlist"][0]
    raw["passive_elements"].append({"name": "Rpar", "kind": "resistor", "terminals": [m["source"], m["drain"]],
                                    "value_ohm": 1e5})
    s1 = build_s1(gh.load_raw(tmp_path, raw), {"vdd": 1.8, "gnd": 0.0})
    seg = next(s for s in gh.gval(s1, "dc_segments") if m["name"] in s.elements)
    assert seg.elements == tuple(sorted((m["name"], "Rpar")))
    assert seg.nets == tuple(sorted((m["drain"], m["source"])))


# ------------------------------------------------------------------ 정지 (4.6, 7.6 변형 재현)


def _ota(gh):
    return gh.raw("two_stage_ota")


def test_stop_inductor(gh, tmp_path):
    raw = _ota(gh)
    raw["passive_elements"].append({"name": "Lx", "kind": "inductor", "terminals": ["OUT", "gnd"]})
    d, devices = gh.stop(lambda: build_s1(gh.load_raw(tmp_path, raw), {"vdd": 1.8, "gnd": 0.0}))
    assert (d["rule_branch"], d["nets"], devices) == ("passive_kind_unsupported", (), ("Lx",))


def test_stop_ideal_voltage_source(gh, tmp_path):
    raw = _ota(gh)
    raw["ideal_sources"] = [{"name": "Vx", "kind": "voltage_source", "terminals": ["vdd", "OUT"], "value_volt": 0.3}]
    d, devices = gh.stop(lambda: build_s1(gh.load_raw(tmp_path, raw), {"vdd": 1.8, "gnd": 0.0}))
    assert (d["rule_branch"], d["nets"], devices) == ("source_kind_unsupported", (), ("Vx",))


def test_stop_unsupported_mos_kind(gh, tmp_path):
    raw = _ota(gh)
    name = raw["netlist"][2]["name"]
    raw["netlist"][2]["kind"] = "njfet"
    d, devices = gh.stop(lambda: build_s1(gh.load_raw(tmp_path, raw), None))
    assert (d["rule_branch"], d["nets"], devices) == ("mos_kind_unsupported", (), (name,))


def test_stop_reports_first_name_branch_and_all_its_elements(gh, tmp_path):
    # 이름순 첫 원소(Aind)의 분기 = passive, devices = 같은 분기 원소 전부(Aind, Zind) -- MOS njfet(M*)은 안 들어감
    raw = _ota(gh)
    raw["netlist"][0]["kind"] = "njfet"
    raw["passive_elements"] += [{"name": "Zind", "kind": "inductor", "terminals": ["OUT", "gnd"]},
                                {"name": "Aind", "kind": "inductor", "terminals": ["OUT", "vdd"]}]
    o_err = pytest.raises(gh.StopExpected, gh.oracle, raw).value
    d, devices = gh.stop(lambda: build_s1(gh.load_raw(tmp_path, raw), None))
    assert d["rule_branch"] == o_err.branch == "passive_kind_unsupported"
    assert devices == o_err.devices == ("Aind", "Zind")


def test_stop_dc_self_loop(gh, tmp_path):
    raw = _ota(gh)
    m = raw["netlist"][3]
    m["drain"] = m["source"]
    if m["gate"] == m["source"]:
        pytest.fail("픽스처: gate 가 source 와 같으면 다른 소자를 골라야 한다")
    d, devices = gh.stop(lambda: build_s1(gh.load_raw(tmp_path, raw), {"vdd": 1.8, "gnd": 0.0}))
    assert d["rule_branch"] == "dc_self_loop"
    assert devices == (m["name"],)
    assert d["nets"] == (m["source"],)


def test_unsupported_checked_before_self_loop(gh, tmp_path):
    raw = _ota(gh)
    raw["netlist"][3]["drain"] = raw["netlist"][3]["source"]
    raw["passive_elements"].append({"name": "Lx", "kind": "inductor", "terminals": ["OUT", "gnd"]})
    d, _ = gh.stop(lambda: build_s1(gh.load_raw(tmp_path, raw), None))
    assert d["rule_branch"] == "passive_kind_unsupported"


def test_stop_is_not_cached(gh, tmp_path):
    # 정지는 예외라 캐시되지 않는다(1절): 같은 입력으로 다시 불러도 다시 정지
    raw = _ota(gh)
    raw["passive_elements"].append({"name": "Lx", "kind": "inductor", "terminals": ["OUT", "gnd"]})
    doc = gh.load_raw(tmp_path, raw)
    for _ in range(2):
        d, _ = gh.stop(lambda: build_s1(doc, None))
        assert d["rule_branch"] == "passive_kind_unsupported"


# ------------------------------------------------------------------ 블록


def test_block_declaration():
    assert isinstance(s1_dc_conduction, ComputeBlock)
    assert s1_dc_conduction.name == S1_DC_CONDUCTION_WRITER
    assert set(s1_dc_conduction.reads) == {("device", "dc_nets"), ("device", "element_class"), ("device", "kind"),
                                           ("device", "unsupported"), ("node", "is_rail"), ("node", "port_direction")}
    assert set(s1_dc_conduction.writes) == {("graph", "dc_pruned"), ("graph", "dc_segments")}
    assert ("device", "bulk") not in s1_dc_conduction.reads


def test_direct_call_reuses_on_same_snapshot(gh):
    s1 = _s1(gh, "two_stage_ota")
    before = s1_dc_conduction.stats()
    assert s1_dc_conduction(s1.snapshot) is s1.snapshot
    after = s1_dc_conduction.stats()
    assert (after.reuses - before.reuses, after.computes - before.computes) == (1, 0)
