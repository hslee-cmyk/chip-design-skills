"""graph/pole_nodes.py -- 극점 노드 목록(계약 10.2, 불변량 6, 설계 41 1.7 (5), 계획 N3.2-6 '극점 노드 목록').

oracle (a): 극점 노드 = 그 뷰의 교류접지가 아닌 모든 넷(중복 없음, 버퍼 출력노드 포함) -- topology JSON 넷 집합(직접 집계)에서
뷰의 ac_ground 를 뺀 것. 소속 블록 = 그 넷을 소유하는 블록(입력 경계 넷 제외 -> 여기 포트는 소속 없음).
임피던스 등급(41 1.7 (4)): 낮음 = gate 가 그 뷰에서 교류접지인 source 단자 또는 diode 가 붙음, 값 의존 = 낮음 단자 없이 저항이
붙음, 높음 = 그 밖(drain·gate·커패시터 단자만).
"""
from __future__ import annotations

import pytest

import s1v_hand as H

ALL = [H.OTA5, H.MILLER, H.FOLDED, H.FOLLOWER, H.PUSHPULL, H.CMFB, H.CS, H.CG, H.PASS, H.XCOUP, H.FF, H.REPLICA,
       H.REPLICA_SE, H.TAP, H.BMULTI, H.CSDIODE, H.BIASSCC, H.RFB, H.RSER, H.CAPROUND, H.LCREV]


@pytest.mark.parametrize("doc", ALL, ids=lambda d: d["topology_name"])
def test_invariant6_pole_nodes_are_all_non_ground_nets(tmp_path, doc):
    _, s1v = H.build(tmp_path, doc)
    nets = H.json_nets(doc)
    for v in s1v.views:
        listed = [p.net for p in v.pole_nodes]
        assert len(listed) == len(set(listed)), v.id
        assert set(listed) == nets - set(v.ac_ground), v.id


def test_buffer_output_is_a_pole_node(tmp_path):
    _, s1v = H.build(tmp_path, H.FOLLOWER)
    p = H.poles(H.view(s1v))
    assert p["out"].block == ("out",)


def test_block_membership(tmp_path):
    _, s1v = H.build(tmp_path, H.MILLER)
    p = H.poles(H.view(s1v))
    # 1단 블록(o1)이 x·tail·o1 을 소유, 2단 블록(out)이 out 을 소유(o1 은 2단의 입력 경계), 여기 포트는 소속 없음
    assert {n: p[n].block for n in ("x", "tail", "o1", "out", "inp", "inn")} == {
        "x": ("o1",), "tail": ("o1",), "o1": ("o1",), "out": ("out",), "inp": (), "inn": ()}


def test_impedance_grades(tmp_path):
    grades = {}
    for doc, net in ((H.OTA5, "x"), (H.CG, "in"), (H.FOLDED, "fx"), (H.REPLICA, "c1"), (H.CS, "out"),
                     (H.OTA5, "out"), (H.CMFB, "om")):
        _, s1v = H.build(tmp_path, doc)
        grades[(doc["topology_name"], net)] = H.poles(H.view(s1v))[net].impedance
    assert grades == {
        ("ota5", "x"): "low",                 # diode M3 drain+gate
        ("cg", "in"): "low",                  # M1 source, gate vb 교류접지
        ("folded", "fx"): "low",              # 캐스코드 M5 source, gate vbc 교류접지
        ("replica", "c1"): "low",             # 캐스코드 M5 source, gate b 가 (4)로 교류접지
        ("cs", "out"): "high",                # drain 만(M1·M2)
        ("ota5", "out"): "high",              # drain 만(M2·M4)
        ("cmfb", "om"): "value_dependent",    # drain(M1·M3) + 저항 R1, 낮음 단자 없음
    }


def test_drive_attribute_matches_view_drive_kind(tmp_path):
    _, s1v = H.build(tmp_path, H.FOLDED)
    v = H.view(s1v)
    d = H.drive(v)
    mismatched = [(p.net, p.drive, d[p.net]) for p in v.pole_nodes if p.net in d and p.drive != d[p.net]]
    assert mismatched == []
    assert {p.net for p in v.pole_nodes} >= set(d)
