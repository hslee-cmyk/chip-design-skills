"""graph/l_classes.py -- L 동치류와 주인(계약 10.2 'L 동치류', 불변량 2 예외, 계획 DEC-17·LR1, 설계 40 3.2 보완 1).

oracle (a)·(d) 손 유도:
- 멤버 = S1 `rel_l_class` 묶음(같은 kind·gate·source, gate 비레일) 그대로 -- S1v 는 주인과 status 만 정한다.
- 주인(DEC-17): tail(DC 역할 바이어스 전류원이 둘 이상 소자의 공통 source 노드 전류를 공급) -> 여럿이면 첫 전달 뷰 최전단 stage 의
  tail -> 없으면 다른 멤버 전류를 정하는 전류 출처 멤버(diode 기준) -> 없으면 이름 정렬 첫 멤버.
- status: 멤버 DC 역할 미확정(S1 gs 묶음 review_needed)이면 review_needed, 그 밖 derived. S1 `rel_l_class` 는 proposed 그대로.

[U1b 2026-10-09] 설계 41 1.12.5(J-F): 주인 순서 3번째에 `main_path_signal`(gain 제약 전달 뷰, 없으면 첫 전달 뷰의 주경로 stage 시작
셀; FF 묶음 멤버보다 우선, 여럿이면 가장 앞 stage)을 넣고, 4번째 `name_order` 는 남은 동률만이며 `review_needed`
(`l_owner_name_order`)로 올린다. master edb5ee0 예외: 동률 후보가 모두 한 자기동형 궤도(U2 `automorphism_orbits`)면 review 를 올리지
않는다. 그래서 FOLDED {M3, M4}·LCREV {M2, M4, M6} 은 이제 review_needed 다(단일 종단 회로라 궤도가 갈린다).
"""
from __future__ import annotations

import pytest

from gmid_engine.graph import GRAPH_KEY, STATUS_DERIVED, STATUS_PROPOSED, STATUS_REVIEW_NEEDED

import jrules_hand as J
import s1v_hand as H


def _classes(s1v):
    return {lc.members: (lc.owner, lc.status) for lc in s1v.l_classes}


def test_diode_reference_owns_mirror_class(tmp_path):
    _, s1v = H.build(tmp_path, H.OTA5)
    # {M3, M4}: tail 없음, M3(diode)이 M4 전류를 정하는 전류 출처 멤버
    assert _classes(s1v) == {("M3", "M4"): ("M3", STATUS_DERIVED)}


def test_tail_owns_its_class(tmp_path):
    _, s1v = H.build(tmp_path, H.MILLER)
    # {M5, M7}(gate vb): M5 가 차동쌍 공통 source(tail) 전류를 공급하는 tail -> 주인 M5
    assert _classes(s1v) == {("M3", "M4"): ("M3", STATUS_DERIVED), ("M5", "M7"): ("M5", STATUS_DERIVED)}


def test_first_gain_stage_tail_wins_between_tails(tmp_path):
    _, s1v = H.build(tmp_path, H.CMFB)
    # {M0, M7}: 둘 다 tail(M0 -> M1/M2 공통 source, M7 -> M5/M6 공통 source t2) -> 첫 전달 뷰 최전단 stage(M1/M2 블록)의 tail M0.
    # {M3, M4, M8}: diode M8 이 전류 출처
    assert _classes(s1v) == {("M0", "M7"): ("M0", STATUS_DERIVED), ("M3", "M4", "M8"): ("M8", STATUS_DERIVED)}


def test_name_order_fallback(tmp_path):
    _, s1v = H.build(tmp_path, H.FOLDED)
    # {M3, M4}(gate vbp): tail 아님(drain fx·fy 는 각각 한 소자 source), diode 없음, stage 시작 셀 아님 -> 이름 첫 멤버 M3.
    # [U1b] 41 1.12.5-4: name_order 는 review_needed(l_owner_name_order). M3·M4 는 단일 종단 미러(M7 diode / M8 출력) 때문에 한
    # 자기동형 궤도가 아니라 edb5ee0 예외에 들지 않는다. {M7, M8}: diode M7
    assert _classes(s1v) == {("M3", "M4"): ("M3", STATUS_REVIEW_NEEDED), ("M7", "M8"): ("M7", STATUS_DERIVED)}
    hits = [f for f in s1v.findings if f.code == "l_owner_name_order"]
    assert [(h.severity, h.subject) for h in hits] == [("review_needed", ("M3", "M4"))]
    assert {lc.members: lc.owner_rule for lc in s1v.l_classes}[("M3", "M4")] == "name_order"


def test_unresolved_dc_role_group_is_review_needed(tmp_path):
    _, s1v = H.build(tmp_path, H.LCREV)
    # {M3, M5}: gate a 가 신호 넷(G 밖)이고 diode 멤버 없음 -> DC 역할 review_needed -> 동치류도 review_needed.
    # [U1b] 주인 = 주경로 2단 stage 시작 셀 M3(main_path_signal, 41 1.12.5-3; M5 는 막다른 가지).
    # {M2, M4, M6}: gate vbp ∈ G -> 바이어스 전류원(DC 역할 확정)이지만 tail·diode 기준·stage 시작 셀이 없어 name_order 동률 ->
    # [U1b] 41 1.12.5-4 로 review_needed(세 소자는 서로 다른 노드 a·out·z 의 부하라 한 궤도가 아니다)
    c = _classes(s1v)
    assert c[("M3", "M5")] == ("M3", STATUS_REVIEW_NEEDED)
    assert c[("M2", "M4", "M6")] == ("M2", STATUS_REVIEW_NEEDED)
    rules = {lc.members: lc.owner_rule for lc in s1v.l_classes}
    assert rules[("M3", "M5")] == "main_path_signal" and rules[("M2", "M4", "M6")] == "name_order"


@pytest.mark.parametrize("doc", [H.OTA5, H.MILLER, H.CMFB, H.FOLDED, H.LCREV, H.BIASSCC, H.REPLICA, H.TAP],
                         ids=lambda d: d["topology_name"])
def test_members_follow_s1_rel_l_class_and_s1_stays_proposed(tmp_path, doc):
    s1, s1v = H.build(tmp_path, doc)
    rel = s1.value("graph", GRAPH_KEY, "rel_l_class")
    assert sorted(r.members for r in rel) == sorted(lc.members for lc in s1v.l_classes)
    assert {r.status for r in rel} <= {STATUS_PROPOSED}
    for lc in s1v.l_classes:
        assert lc.owner in lc.members
        assert lc.status in (STATUS_DERIVED, STATUS_REVIEW_NEEDED)
        assert isinstance(lc.owner_rule, str) and lc.owner_rule


# ---------------------------------------------------------------- [U1b] 41 1.12.5 주인 규칙 main_path_signal·name_order
def test_main_path_cell_owns_class_shared_with_ff_cell(tmp_path):
    # 손 유도(jrules_hand FF3): {M2, M4}(nmos, gate a, gnd) 에서 M2 = 주경로 2단 stage 시작 셀, M4 = FF 묶음 셀 -> 주인 M2.
    # {M1, M5}(gate in) 에서 M1 = 1단 stage 시작 셀(M5 는 FF 묶음) -> 주인 M1. 두 묶음 모두 기준 없는 J-U3-c 묶음이라 status
    # review_needed(DC 역할 미확정)이고 S1v 에 `dc_role_unresolved_group` 이 붙는다(40 3.2-3 dc_role 사실 대상, 41 1.11 ③).
    _, s1v = H.build(tmp_path, J.FF3)
    got = {lc.members: (lc.owner, lc.owner_rule, lc.status) for lc in s1v.l_classes}
    assert got[("M2", "M4")] == ("M2", "main_path_signal", STATUS_REVIEW_NEEDED)
    assert got[("M1", "M5")] == ("M1", "main_path_signal", STATUS_REVIEW_NEEDED)
    groups = sorted(f.subject for f in s1v.findings if f.code == "dc_role_unresolved_group")
    assert groups == [("M1", "M5"), ("M2", "M4")]


def test_ngcc_owner_is_main_path_signal():
    # oracle (d) 41 1.13 L 주인 행: ngcc {M8, M14} -> M8(main_path_signal). M14 는 FF 묶음
    _, s1v = H.build_lib("ngcc_3stage_ff")
    got = {lc.members: (lc.owner, lc.owner_rule) for lc in s1v.l_classes}
    assert got[("M14", "M8")] == ("M8", "main_path_signal")


def test_sf_owners_are_composite_references():
    # oracle (d) 41 1.13: sf 3동치류 -> M6·M8·M14(current_source_member, 복합 diode 기준)
    _, s1v = H.build_lib("sf_pushpull_output_opamp")
    got = {lc.members: (lc.owner, lc.owner_rule, lc.status) for lc in s1v.l_classes}
    assert got[("M17", "M6", "M9")] == ("M6", "current_source_member", STATUS_DERIVED)
    assert got[("M11", "M8")] == ("M8", "current_source_member", STATUS_DERIVED)
    assert got[("M14", "M16", "M20")] == ("M14", "current_source_member", STATUS_DERIVED)


def test_name_order_tie_inside_one_orbit_raises_no_review(tmp_path):
    # master edb5ee0(41 1.12.5-4 예외): FDIFF 는 M1<->M2, M3<->M4, om<->op 교환에 대칭인 완전 차동 회로라 동률 후보 {M3, M4} 가 한
    # 자기동형 궤도다 -> 주인은 이름 순 M3 이지만 review 를 올리지 않는다(status derived, l_owner_name_order 없음)
    _, s1v = H.build(tmp_path, J.FDIFF)
    got = {lc.members: (lc.owner, lc.owner_rule, lc.status) for lc in s1v.l_classes}
    assert got[("M3", "M4")] == ("M3", "name_order", STATUS_DERIVED)
    assert "l_owner_name_order" not in J.finding_codes(s1v)
    assert s1v.review_needed == ()


def test_name_order_tie_across_orbits_stays_review(tmp_path):
    # 같은 부하 쌍이라도 단일 종단(미러 부하) 회로면 궤도가 갈린다 -> review 유지. nmcnr {M104, M105} 도 단일 종단 미러(M108 diode /
    # M109 출력) 때문에 두 소자가 서로 다른 궤도라(엔진 automorphism_orbits 로 확인한 값이 아니라 test_automorphism_orbits 의
    # '단일 종단 = 다른 궤도' 손 유도) 예외에 들지 않는다
    _, s1v = H.build(tmp_path, H.FOLDED)
    assert "l_owner_name_order" in J.finding_codes(s1v)
    _, lib = H.build_lib("nmcnr_amplifier")
    got = {lc.members: (lc.owner_rule, lc.status) for lc in lib.l_classes}
    assert got[("M104", "M105")] == ("name_order", STATUS_REVIEW_NEEDED)
