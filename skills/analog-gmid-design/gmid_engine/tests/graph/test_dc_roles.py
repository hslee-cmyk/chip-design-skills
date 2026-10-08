"""graph/dc_roles.py -- `s1_dc_roles`: MOS 소자 DC 역할(계약 4.4 표 (1)~(5), 4.6, 7.4).

기대값 = 독립 oracle(교류접지 G = 레일 ∪ gate 전용 미구동 넷을 JSON 에서 다시 구하고 표 순서대로 적용)과 계약 7.4 표.
"""
from __future__ import annotations

import collections

import pytest

from gmid_engine.core import ComputeBlock
from gmid_engine.graph import (
    S1_DC_ROLES_WRITER,
    DcRole,
    build_s1,
    s1_dc_roles,
    s1_gs_groups,
)

SIX = (
    "common_gate_amplifier", "current_reuse_telescopic_ota", "ngcc_3stage_ff",
    "pushpull_follower_buffer", "sf_pushpull_output_opamp", "two_stage_ota_sf",
)
NINE = tuple(sorted(SIX + ("folded_cascode", "nmcnr_amplifier", "two_stage_ota")))
# 계약 7.4 표: (diode, bias, signal, review_needed 묶음)
TABLE = {
    "common_gate_amplifier": (0, 2, 1, ()),
    "current_reuse_telescopic_ota": (16, 15, 20, ()),
    "folded_cascode": (4, 4, 5, ()),
    "ngcc_3stage_ff": (3, 8, 5, (("M14", "M8"),)),
    "nmcnr_amplifier": (2, 7, 6, ()),
    "pushpull_follower_buffer": (0, 2, 4, ()),
    "sf_pushpull_output_opamp": (1, 1, 20, (("M11", "M8"), ("M14", "M16", "M20"), ("M17", "M6", "M9"))),
    "two_stage_ota": (1, 3, 3, ()),
    "two_stage_ota_sf": (1, 4, 4, ()),
}


def _s1(gh, name):
    return build_s1(gh.load_lib(name), gh.supplies_for(name))


def _counts(roles):
    c = collections.Counter(r[0] for r in roles.values())
    review = tuple(sorted({r[2][2] for r in roles.values() if r[1] == "review_needed"}))
    return c["diode_reference"], c["bias_current_source"], c["signal"], review


@pytest.mark.parametrize("name", NINE)
def test_oracle_matches_contract_table(gh, name):
    assert _counts(gh.oracle(gh.raw(name)).dc_roles) == TABLE[name]


def test_table_totals():
    tot = [sum(v[i] for v in TABLE.values()) for i in range(3)]
    assert tot == [28, 46, 68]
    groups = [g for v in TABLE.values() for g in v[3]]
    assert len(groups) == 4 and sum(len(g) for g in groups) == 10


@pytest.mark.parametrize("name", NINE)
def test_roles_match_oracle(gh, name):
    raw = gh.raw(name)
    o = gh.oracle(raw)
    s1 = _s1(gh, name)
    col = s1.column("device", "dc_role")
    assert tuple(k for k, _ in col) == tuple(sorted(o.mos))         # MOS 레코드에만
    assert all(isinstance(v, DcRole) for _, v in col)
    assert {k: gh.role_plain(v) for k, v in col} == o.dc_roles
    for n in list(o.passives) + list(o.sources):
        with pytest.raises(KeyError):
            s1.value("device", n, "dc_role")


@pytest.mark.parametrize("name", NINE)
def test_diode_always_role_1(gh, name):
    agg = gh.agg(gh.raw(name))
    s1 = _s1(gh, name)
    for n in agg.diodes:
        r = s1.value("device", n, "dc_role")
        assert (r.role, r.status, r.evidence.rule) == ("diode_reference", "derived", "1")


def test_review_needed_group_is_signal_not_stop(gh):
    s1 = _s1(gh, "ngcc_3stage_ff")
    for n in ("M14", "M8"):
        r = s1.value("device", n, "dc_role")
        assert (r.role, r.status, r.evidence.rule, r.evidence.group, r.evidence.basis) == (
            "signal", "review_needed", "2", ("M14", "M8"), ("J-U3-c",))


def test_gate_ground_group_rule(gh, tmp_path):
    # (2) 둘째 행: diode 멤버 없는 묶음의 gate 가 gate 전용 미구동 넷 -> 멤버 전부 bias, basis J-U3-a
    raw = gh.raw("pushpull_follower_buffer")
    raw["netlist"] += [{"name": "Mq1", "kind": "nmos", "drain": "A", "gate": "VNB1", "source": "vss"},
                       {"name": "Mq2", "kind": "nmos", "drain": "B", "gate": "VNB1", "source": "vss"}]
    o = gh.oracle(raw)
    raw.pop("source_manifest", None)    # 변형 문서: 소자 수가 출처 그림과 달라졌다 -- 출처 개수 선언을 뗀다(authoring 10절, 키 없으면 검사 안 함)
    s1 = build_s1(gh.load_raw(tmp_path, raw), gh.supplies_for("pushpull_follower_buffer"))
    # 원본 M6(nmos, gate VNB1, source vss)도 같은 묶음이 된다(JSON 확인)
    m6 = next(e for e in raw["netlist"] if e["name"] == "M6")
    assert (m6["kind"], m6["gate"], m6["source"]) == ("nmos", "VNB1", "vss")
    for n in ("M6", "Mq1", "Mq2"):
        assert gh.role_plain(s1.value("device", n, "dc_role")) == o.dc_roles[n] == (
            "bias_current_source", "derived", ("2", ("VNB1", "vss"), ("M6", "Mq1", "Mq2"), ("J-U3-a",)))


def test_block_declaration():
    assert isinstance(s1_dc_roles, ComputeBlock)
    assert s1_dc_roles.name == S1_DC_ROLES_WRITER
    assert set(s1_dc_roles.reads) == {("device", "element_class"), ("device", "is_diode"), ("device", "kind"),
                                      ("device", "pins"), ("node", "ac_ground_class"), ("node", "is_rail"),
                                      ("graph", "gs_groups")}
    assert tuple(s1_dc_roles.writes) == (("device", "dc_role"),)


def test_direct_call_unsupported_mos_stops(gh, tmp_path):
    # 블록 단독 호출에서는 s1_dc_roles 자신이 mos_kind_unsupported 로 정지(4.6)
    raw = gh.raw("two_stage_ota")
    name = raw["netlist"][1]["name"]
    raw["netlist"][1]["kind"] = "njfet"
    doc = gh.load_raw(tmp_path, raw)
    snap = s1_gs_groups(gh.structure_and_bulk(doc, None))
    d, devices = gh.stop(lambda: s1_dc_roles(snap))
    assert d["rule_branch"] == "mos_kind_unsupported"
    assert devices == (name,)
