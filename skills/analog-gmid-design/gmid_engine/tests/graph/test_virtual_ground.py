"""graph/virtual_ground.py -- 기모드 여기의 회로 자기동형과 자기대응 넷(계약 10.2 '교류접지' 둘째 문장, 계획 N3.2-3 '대칭 축약').

oracle (a) 손 유도(자기동형 = 입력 p↔n 을 맞바꾸는 원소·넷 전단사로 connectivity 를 보존하는 것):
- XCOUP: M1↔M2, M3↔M4, om↔op, inp↔inn, 자기대응 = M0 과 넷 tail -> 가상접지 (tail,).
- CMFB: M1↔M2, M3↔M4, R1↔R2, om↔op, 자기대응 소자 M0·M5~M9 -> 그 소자들의 비접지 넷 cm·cmfb·t2·tail·x6.
- REPLICA: M1↔M2, M5↔M6, M3↔M4, c1↔c2, om↔op, 자기대응 M0·Mr·Mi -> 넷 b·tail.
- OTA5: inp↔inn 이면 M1↔M2, x↔out 이어야 하는데 M3(gate x)↔M4(gate x)는 gate 가 x↔out 으로 대응하지 않는다 -> 자기동형 없음 -> ().
- 단일 여기(CS, REPLICA_SE)는 기모드가 아니다 -> ().
축약 뷰에서 자기대응 넷은 접지라 차동쌍 공통 source 는 degeneration 이 아니다(XCOUP M1/M2), 자기동형이 없으면 degeneration(OTA5).
"""
from __future__ import annotations

import s1v_hand as H


def test_cross_coupled_pair_tail_is_virtual_ground(tmp_path):
    _, s1v = H.build(tmp_path, H.XCOUP)
    assert H.view(s1v).virtual_ground == ("tail",)


def test_cmfb_self_corresponding_nets(tmp_path):
    _, s1v = H.build(tmp_path, H.CMFB)
    assert H.view(s1v).virtual_ground == ("cm", "cmfb", "t2", "tail", "x6")


def test_replica_self_corresponding_nets(tmp_path):
    _, s1v = H.build(tmp_path, H.REPLICA)
    assert H.view(s1v).virtual_ground == ("b", "tail")


def test_asymmetric_mirror_load_has_no_automorphism(tmp_path):
    _, s1v = H.build(tmp_path, H.OTA5)
    assert H.view(s1v).virtual_ground == ()


def test_single_excitation_has_no_virtual_ground(tmp_path):
    for doc in (H.CS, H.REPLICA_SE, H.FOLLOWER):
        _, s1v = H.build(tmp_path, doc)
        assert all(v.virtual_ground == () for v in s1v.views), doc["topology_name"]


def test_virtual_ground_removes_degeneration_of_the_pair(tmp_path):
    _, sym = H.build(tmp_path, H.XCOUP)
    _, asym = H.build(tmp_path, H.OTA5)
    deg_sym = {c.dev: c.degeneration for c in H.view(sym).cells}
    deg_asym = {c.dev: c.degeneration for c in H.view(asym).cells}
    # 축약 뷰에서 tail 이 접지 -> source 접지 CS(degeneration 아님) / 축약 없음 -> 두 노드 모두 비접지 CS(degeneration)
    assert (deg_sym["M1"], deg_sym["M2"]) == (False, False)
    assert (deg_asym["M1"], deg_asym["M2"]) == (True, True)


def test_virtual_ground_nets_are_not_signal_nets_of_reduced_view(tmp_path):
    _, s1v = H.build(tmp_path, H.CMFB)
    v = H.view(s1v)
    # 축약 뷰의 신호 넷(ViewS1v docstring)은 가상접지 넷을 담지 않는다 -> 차동 경로 넷만
    assert v.signal_nets == ("inn", "inp", "om", "op")
    assert not set(v.virtual_ground) & set(v.signal_nets)
