"""graph/l_classes.py -- L 동치류와 주인(계약 10.2 'L 동치류', 불변량 2 예외, 계획 DEC-17·LR1, 설계 40 3.2 보완 1).

oracle (a)·(d) 손 유도:
- 멤버 = S1 `rel_l_class` 묶음(같은 kind·gate·source, gate 비레일) 그대로 -- S1v 는 주인과 status 만 정한다.
- 주인(DEC-17): tail(DC 역할 바이어스 전류원이 둘 이상 소자의 공통 source 노드 전류를 공급) -> 여럿이면 첫 전달 뷰 최전단 stage 의
  tail -> 없으면 다른 멤버 전류를 정하는 전류 출처 멤버(diode 기준) -> 없으면 이름 정렬 첫 멤버.
- status: 멤버 DC 역할 미확정(S1 gs 묶음 review_needed)이면 review_needed, 그 밖 derived. S1 `rel_l_class` 는 proposed 그대로.
"""
from __future__ import annotations

import pytest

from gmid_engine.graph import GRAPH_KEY, STATUS_DERIVED, STATUS_PROPOSED, STATUS_REVIEW_NEEDED

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
    # {M3, M4}(gate vbp): tail 아님(drain fx·fy 는 각각 한 소자 source), diode 없음 -> 이름 첫 멤버 M3. {M7, M8}: diode M7
    assert _classes(s1v) == {("M3", "M4"): ("M3", STATUS_DERIVED), ("M7", "M8"): ("M7", STATUS_DERIVED)}


def test_unresolved_dc_role_group_is_review_needed(tmp_path):
    _, s1v = H.build(tmp_path, H.LCREV)
    # {M3, M5}: gate a 가 신호 넷(G 밖)이고 diode 멤버 없음 -> DC 역할 review_needed -> 동치류도 review_needed.
    # {M2, M4, M6}: gate vbp ∈ G -> 바이어스 전류원, derived
    c = _classes(s1v)
    assert c[("M3", "M5")][1] == STATUS_REVIEW_NEEDED
    assert c[("M2", "M4", "M6")][1] == STATUS_DERIVED


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
