"""graph/composite_blocks.py -- 복합 블록(계약 10.2 '블록'·10.4, 설계 41 1.9, 계획 DEC-81).

oracle (a) 손 유도(FF): 1단 CS M1(in -> a)·2단 CS M3(a -> out)과 병렬 경로 CS M4(in -> out). 합류 노드 out 을 서로 다른 stage 블록이
공유 -> 복합 블록. 경로 부호 = 셀 부호의 곱(CS = -1): a -> out(M3) = -1, in -> out(M4) = -1. 묶인 MOS 셀 = M3·M4 = 2.
묶은 뒤 DAG(블록 a -> 복합 블록)는 사슬. 묶음 경계는 J12 ratify 전이라 status review_needed + `composite_block_pending_ratify`
(계약 10.4).
oracle (d): DEC-81 -- ngcc_3stage_ff 의 M7·M13·M14 drain 이 모두 Vout 에 붙는 것이 발동 회로 기본안(계획서 본문).
"""
from __future__ import annotations

import s1v_hand as H


def test_feedforward_merge_is_composite(tmp_path):
    _, s1v = H.build(tmp_path, H.FF)
    v = H.view(s1v)
    assert len(v.composites) == 1
    c = v.composites[0]
    assert c.merge_nodes == ("out",)
    assert c.status == "review_needed"
    assert c.chain is True
    assert c.cells == 2
    assert sorted(c.paths) == [(("a", "out"), -1), (("in", "out"), -1)]
    hits = [f for f in v.findings if f.code == "composite_block_pending_ratify"]
    assert [(h.severity, h.subject) for h in hits] == [("review_needed", ("out",))]


def test_chain_without_merge_has_no_composite(tmp_path):
    for doc in (H.MILLER, H.OTA5, H.FOLDED, H.LCREV):
        _, s1v = H.build(tmp_path, doc)
        assert H.view(s1v).composites == (), doc["topology_name"]
        assert "composite_block_pending_ratify" not in H.all_codes(s1v)


def test_review_needed_alone_does_not_stop(tmp_path):
    # review_needed 는 정지가 아니라 기록(계약 10.2 끝 문장) -- 기본 모드에서도 반환하고 S1v.review_needed 에 모인다
    _, s1v = H.build(tmp_path, H.FF, stop_on_unsupported=True)
    assert [f.code for f in s1v.review_needed] == ["composite_block_pending_ratify"]
    assert s1v.unsupported == ()


def test_ngcc_vout_merge_is_composite():
    _, s1v = H.build_lib("ngcc_3stage_ff")
    v = H.view(s1v)
    assert any("Vout" in c.merge_nodes for c in v.composites)
