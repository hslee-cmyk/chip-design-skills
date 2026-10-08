"""graph/signal_reach.py -- 도달성(최소 고정점)과 순방향 집합(설계 41 1.3, 계획 N3.2-3 '순방향 경로 정의', 불변량 3).

oracle (a) 손 유도. 규칙: 여기 포트에서 시작해 (a) 신호 넷을 gate 로 받는 소자의 drain·source (b) 신호 넷을 source 로 받는 소자의
drain (c) 신호 넷에 붙은 2단자 수동소자의 반대쪽 단자를 더한다(교류접지 넷은 넣지 않는다). 순방향 = 여기에서 도달하고 출력
포트로 역도달하는 넷.
"""
from __future__ import annotations

import pytest

import s1v_hand as H


def test_five_transistor_ota(tmp_path):
    _, s1v = H.build(tmp_path, H.OTA5)
    v = H.view(s1v)
    # inp,inn -(a)-> x,out,tail ; tail -(b)-> x,out ; x -(a)-> out(M4), vdd 는 접지. 모두 out 으로 역도달
    assert v.signal_nets == ("inn", "inp", "out", "tail", "x")
    assert v.forward_nets == ("inn", "inp", "out", "tail", "x")


def test_folded_cascode(tmp_path):
    _, s1v = H.build(tmp_path, H.FOLDED)
    v = H.view(s1v)
    # inp->fx,tail ; inn->fy,tail ; tail-(b)->fx,fy ; fx-(b)->ox(M5) ; fy-(b)->out(M6) ; ox-(a)->out(M8)
    assert v.signal_nets == ("fx", "fy", "inn", "inp", "out", "ox", "tail")
    assert v.forward_nets == v.signal_nets


def test_dead_end_drain_is_signal_but_not_forward(tmp_path):
    _, s1v = H.build(tmp_path, H.AMB)
    v = H.view(s1v)
    # in -(a)-> x(drain), s1(source). x 에서 더 나가는 단자가 없어 출력 s1 로 역도달하지 않는다
    assert v.signal_nets == ("in", "s1", "x")
    assert v.forward_nets == ("in", "s1")


def test_dead_end_gate_branch(tmp_path):
    _, s1v = H.build(tmp_path, H.TAP)
    v = H.view(s1v)
    # fx -(a)-> t(Mt drain): t 는 막다른 가지
    assert v.signal_nets == ("fx", "in", "out", "t")
    assert v.forward_nets == ("fx", "in", "out")


def test_side_latch_is_signal_not_forward(tmp_path):
    _, s1v = H.build(tmp_path, H.BIASSCC)
    v = H.view(s1v)
    assert v.signal_nets == ("in", "out", "p", "q")
    assert v.forward_nets == ("in", "out")


def test_passive_reach_rule_c(tmp_path):
    _, s1v = H.build(tmp_path, H.RSER)
    v = H.view(s1v)
    # a -(c) R1-> out. CL 의 반대 단자 gnd 는 접지라 넣지 않는다
    assert v.signal_nets == ("a", "in", "out")
    assert v.forward_nets == ("a", "in", "out")


def test_unexcited_input_is_not_reached(tmp_path):
    _, s1v = H.build(tmp_path, H.REPLICA_SE)
    assert "in2" not in H.view(s1v, "transfer:0").signal_nets
    assert "in1" not in H.view(s1v, "transfer:1").signal_nets


@pytest.mark.parametrize("doc", [H.OTA5, H.MILLER, H.FOLDED, H.CMFB, H.REPLICA, H.REPLICA_SE, H.TAP, H.AMB, H.PASS,
                                 H.BIASSCC, H.RFB, H.FF, H.XCOUP], ids=lambda d: d["topology_name"])
def test_invariant3_forward_subset_of_signal_and_disjoint_from_ground(tmp_path, doc):
    _, s1v = H.build(tmp_path, doc)
    for v in s1v.views:
        assert set(v.forward_nets) <= set(v.signal_nets), v.id
        assert not set(v.signal_nets) & set(v.ac_ground), v.id
        assert {n for n, _ in v.excite} <= set(v.signal_nets), v.id
