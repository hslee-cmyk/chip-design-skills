"""graph/composite_blocks.py -- 복합 블록(계약 10.2 '블록'·10.4, 설계 41 1.9, 계획 DEC-81).

oracle (a) 손 유도(FF): 1단 CS M1(in -> a)·2단 CS M3(a -> out)과 병렬 경로 CS M4(in -> out). 합류 노드 out 을 서로 다른 stage 블록이
공유 -> 복합 블록. 경로 부호 = 셀 부호의 곱(CS = -1): a -> out(M3) = -1, in -> out(M4) = -1. 묶인 MOS 셀 = M3·M4 = 2.
묶은 뒤 DAG(블록 a -> 복합 블록)는 사슬. 묶음 경계는 J12 ratify 전이라 status review_needed + `composite_block_pending_ratify`
(계약 10.4).
oracle (d): DEC-81 -- ngcc_3stage_ff 의 M7·M13·M14 drain 이 모두 Vout 에 붙는 것이 발동 회로 기본안(계획서 본문).

[U1b 2026-10-09] 설계 41 1.9 '복합 블록 판정 전에 FF 묶음을 주경로 블록 구성에서 뺀다. FF 합류는 복합 블록으로 묶지 않는다'와
1.12.2-3 'FF 합류에는 복합 블록 조건(DEC-81)을 적용하지 않는다'가 위 FF 손 회로와 ngcc 를 바꾼다: M4 는 1단 블록 a 를 우회하는
feedforward 묶음(test_feedforward_cells 손 유도)이라 복합 블록이 0 이다. 41 1.13 ngcc 행 '복합 블록 0'.
review_needed 만 있는 회로는 FOLDED({M3, M4} L 동치류 주인이 이름 순 -> `l_owner_name_order`, 41 1.12.5-4; 두 소자는 단일 종단
미러 부하 때문에 한 자기동형 궤도가 아니다 -- test_automorphism_orbits '단일 종단 = 다른 궤도')로 바꿨다.
"""
from __future__ import annotations

import s1v_hand as H


def test_feedforward_merge_is_not_composite(tmp_path):
    # [U1b] 41 1.9·1.12.2-3: FF 합류(out)는 복합 블록이 아니다 -- 주경로 블록 사슬 a(stage 1) -> out(stage 2), 복합 블록 0,
    # composite_block_pending_ratify 없음. M4 는 FF 묶음(탭 in, merge out)이다.
    _, s1v = H.build(tmp_path, H.FF)
    v = H.view(s1v)
    assert v.composites == ()
    assert "composite_block_pending_ratify" not in H.all_codes(s1v)
    assert {b.key: b.stage for b in v.blocks} == {("a",): 1, ("out",): 2}
    assert [(c.tap, c.merge, c.cells) for c in v.feedforward] == [("in", "out", ("M4",))]


def test_chain_without_merge_has_no_composite(tmp_path):
    for doc in (H.MILLER, H.OTA5, H.FOLDED, H.LCREV):
        _, s1v = H.build(tmp_path, doc)
        assert H.view(s1v).composites == (), doc["topology_name"]
        assert "composite_block_pending_ratify" not in H.all_codes(s1v)


def test_review_needed_alone_does_not_stop(tmp_path):
    # review_needed 는 정지가 아니라 기록(계약 10.2 끝 문장) -- 기본 모드에서도 반환하고 S1v.review_needed 에 모인다.
    # [U1b] review_needed 만 내는 손 회로 = FOLDED(41 1.12.5-4 name_order 동률 {M3, M4}, 한 궤도 아님)
    _, s1v = H.build(tmp_path, H.FOLDED, stop_on_unsupported=True)
    assert [f.code for f in s1v.review_needed] == ["l_owner_name_order"]
    assert s1v.unsupported == ()


def test_ngcc_vout_merge_is_not_composite():
    # [U1b] 41 1.13 ngcc 행: 주경로 V1 -> V2 -> Vout + feedforward 2묶음, 복합 블록 0(옛 DEC-81 발동 기본안을 J-A 가 대체)
    _, s1v = H.build_lib("ngcc_3stage_ff")
    v = H.view(s1v)
    assert v.composites == ()
    assert {c.merge for c in v.feedforward} == {"Vout"}
