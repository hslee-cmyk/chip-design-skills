"""graph/gs_groups.py -- `s1_gs_groups`: 같은 (kind, gate, source) MOS 2개 이상 묶음(계약 4.4, 7.4).

기대값 = JSON 직접 집계(oracle)와 계약 7.4 표 gs_groups 열.
"""
from __future__ import annotations

import pytest

from gmid_engine.core import ComputeBlock
from gmid_engine.graph import S1_GS_GROUPS_WRITER, GsGroup, build_s1, s1_gs_groups

SIX = (
    "common_gate_amplifier", "current_reuse_telescopic_ota", "ngcc_3stage_ff",
    "pushpull_follower_buffer", "sf_pushpull_output_opamp", "two_stage_ota_sf",
)
NINE = tuple(sorted(SIX + ("folded_cascode", "nmcnr_amplifier", "two_stage_ota")))
TABLE = {"common_gate_amplifier": 0, "current_reuse_telescopic_ota": 3, "folded_cascode": 3, "ngcc_3stage_ff": 5,
         "nmcnr_amplifier": 3, "pushpull_follower_buffer": 0, "sf_pushpull_output_opamp": 4, "two_stage_ota": 2,
         "two_stage_ota_sf": 2}


def _s1(gh, name):
    return build_s1(gh.load_lib(name), gh.supplies_for(name))


def _json_groups(raw):
    """oracle 와 별개로 한 번 더: (kind, gate, source) -> 이름 목록."""
    out = {}
    for e in raw["netlist"]:
        out.setdefault((e["kind"], e["gate"], e["source"]), []).append(e["name"])
    return {k: tuple(sorted(v)) for k, v in out.items() if len(v) >= 2}


@pytest.mark.parametrize("name", NINE)
def test_groups_match_json(gh, name):
    raw = gh.raw(name)
    groups = gh.gval(_s1(gh, name), "gs_groups")
    assert all(isinstance(g, GsGroup) for g in groups)
    plain = tuple(gh.gs_plain(g) for g in groups)
    assert plain == gh.oracle(raw).gs_groups
    assert {(k, g, s): m for k, g, s, m in plain} == _json_groups(raw)
    assert [p[:3] for p in plain] == sorted(p[:3] for p in plain)
    assert len(plain) == TABLE[name]
    assert sum(TABLE.values()) == 22                          # 7.4 합계


def test_rail_gate_group_included(gh, tmp_path):
    # 레일 gate 묶음도 원자료로 포함(4.4)
    raw = gh.raw("pushpull_follower_buffer")
    raw["netlist"] += [{"name": "Mg1", "kind": "nmos", "drain": "A", "gate": "vdd", "source": "vss"},
                       {"name": "Mg2", "kind": "nmos", "drain": "B", "gate": "vdd", "source": "vss"}]
    raw.pop("source_manifest", None)    # 변형 문서: 소자 수가 출처 그림과 달라졌다 -- 출처 개수 선언을 뗀다(authoring 10절, 키 없으면 검사 안 함)
    s1 = build_s1(gh.load_raw(tmp_path, raw), gh.supplies_for("pushpull_follower_buffer"))
    assert ("nmos", "vdd", "vss", ("Mg1", "Mg2")) in [gh.gs_plain(g) for g in gh.gval(s1, "gs_groups")]


def test_kind_separates_groups(gh, tmp_path):
    raw = gh.raw("pushpull_follower_buffer")
    raw["netlist"] += [{"name": "Mk1", "kind": "nmos", "drain": "A", "gate": "VNB1", "source": "B"},
                       {"name": "Mk2", "kind": "pmos", "drain": "vout", "gate": "VNB1", "source": "B"}]
    raw.pop("source_manifest", None)    # 변형 문서: 소자 수가 출처 그림과 달라졌다 -- 출처 개수 선언을 뗀다(authoring 10절, 키 없으면 검사 안 함)
    s1 = build_s1(gh.load_raw(tmp_path, raw), gh.supplies_for("pushpull_follower_buffer"))
    assert all({"Mk1", "Mk2"} - set(g.members) for g in gh.gval(s1, "gs_groups"))


def test_block_declaration():
    assert isinstance(s1_gs_groups, ComputeBlock)
    assert s1_gs_groups.name == S1_GS_GROUPS_WRITER
    assert set(s1_gs_groups.reads) == {("device", "element_class"), ("device", "kind"), ("device", "pins")}
    assert tuple(s1_gs_groups.writes) == (("graph", "gs_groups"),)
