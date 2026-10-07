"""graph/ac_ground_static.py -- `static_ac_ground(index, rails, input_nets)` (계약 4.1 `ac_ground_class`, 6절).

규칙: 레일 -> "rail"; 레일 아님·입력 포트 아님·단자가 전부 g -> "gate_only_undriven"; 그 밖 None.
index 넷 순서 그대로 ((넷, 분류|None), ...). 기대값 = JSON 직접 집계 + 계약 7.1 표.
"""
from __future__ import annotations

import pytest

from gmid_engine.graph import AC_GROUND_GATE_ONLY, AC_GROUND_RAIL, static_ac_ground, terminal_index

SIX = (
    "common_gate_amplifier", "current_reuse_telescopic_ota", "ngcc_3stage_ff",
    "pushpull_follower_buffer", "sf_pushpull_output_opamp", "two_stage_ota_sf",
)
# 계약 7.1 표 gate_only_undriven 열
TABLE_GATE_ONLY = {
    "common_gate_amplifier": ("VNBias1", "VNBias2", "VPBias1"),
    "current_reuse_telescopic_ota": (),
    "ngcc_3stage_ff": ("VBN", "VBP"),
    "pushpull_follower_buffer": ("VNB1", "VPB1"),
    "sf_pushpull_output_opamp": (),
    "two_stage_ota_sf": ("bias",),
}


def _run(doc, agg):
    idx = terminal_index(doc.devices, doc.passives, doc.sources)
    return idx, static_ac_ground(idx, tuple(sorted(doc.rails)), tuple(sorted(agg.input_nets)))


@pytest.mark.parametrize("name", SIX)
def test_library_classes_match_json(gh, name):
    agg = gh.agg(gh.raw(name))
    assert agg.gate_only == TABLE_GATE_ONLY[name]           # 집계 자체를 계약 표와 교차 확인
    doc = gh.load_lib(name)
    idx, out = _run(doc, agg)
    assert [n for n, _ in out] == [n for n, _ in idx]       # index 순서 그대로
    got = dict(out)
    for net in agg.terminals:
        assert got[net] == agg.ac_class(net), net
    assert tuple(sorted(n for n, c in out if c == AC_GROUND_GATE_ONLY)) == TABLE_GATE_ONLY[name]
    assert {n for n, c in out if c == AC_GROUND_RAIL} == set(agg.rails)


def test_input_port_gate_only_net_is_not_ac_ground(gh):
    # two_stage_ota_sf 입력 vin_p·vin_n 은 gate 에만 닿지만 입력 포트라 None
    agg = gh.agg(gh.raw("two_stage_ota_sf"))
    doc = gh.load_lib("two_stage_ota_sf")
    _, out = _run(doc, agg)
    got = dict(out)
    for net in agg.input_nets:
        assert set(t for _, t in agg.terminals[net]) == {"g"}
        assert got[net] is None
    # 같은 index 에 입력 넷을 비우면 gate_only 로 바뀐다(규칙이 input_nets 인자를 실제로 쓴다)
    idx = terminal_index(doc.devices, doc.passives, doc.sources)
    got2 = dict(static_ac_ground(idx, tuple(sorted(doc.rails)), ()))
    for net in agg.input_nets:
        assert got2[net] == AC_GROUND_GATE_ONLY


def test_rail_wins_and_mixed_terminals_none():
    idx = (
        ("a", (("C1", "t0"), ("M1", "g"))),     # g + 2단자 -> None
        ("b", (("M1", "g"), ("M2", "g"))),      # 전부 g -> gate_only
        ("c", (("M1", "d"),)),                  # d -> None
        ("r", (("M2", "g"),)),                  # 레일 -> rail (전부 g 여도)
    )
    assert static_ac_ground(idx, ("r",), ()) == (
        ("a", None), ("b", AC_GROUND_GATE_ONLY), ("c", None), ("r", AC_GROUND_RAIL))


def test_output_port_gate_only_still_classified():
    # 규칙은 '입력 포트 아님' 만 본다 -- input_nets 에 없는 넷은 gate 전용이면 gate_only
    idx = (("o", (("M1", "g"),)),)
    assert static_ac_ground(idx, (), ()) == (("o", AC_GROUND_GATE_ONLY),)
    assert static_ac_ground(idx, (), ("o",)) == (("o", None),)


def test_empty_index():
    assert static_ac_ground((), ("vdd",), ()) == ()
