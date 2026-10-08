"""graph/declared_compare.py -- declared stage 대조(계약 10.2 'declared 대조', 설계 41 1.10, 계획 N3.2-8, U-50).

oracle (a) 손 유도(MILLER): 유도 stage 1 = 입력 M1·M2(+ 미러 M3/M4·tail M5), stage 2 = 입력 M6(+ 부하 M7).
- 선언 ((M1, M2), (M6,)) -> 입력 멤버십 일치 -> 불일치 기록 없음.
- 선언 ((M1, M2, M3, M4, M5), (M6, M7)) -> 부하·tail 을 함께 적어도 일치(대조는 input·cascode·tail 멤버십).
- 선언 ((M1, M6), (M2,)) -> 한 선언 stage 의 소자가 서로 다른 유도 stage 에 있다 -> `declared_stage_mismatch`(review_needed).
declared 는 유도의 입력이 아니다(U-50) -- 선언을 바꿔도 블록은 같다.
"""
from __future__ import annotations

import s1v_hand as H

MATCH = (("comp", (("M1", "M2"), ("M6",))),)
MATCH_WITH_LOADS = (("comp", (("M1", "M2", "M3", "M4", "M5"), ("M6", "M7"))),)
MISMATCH = (("comp", (("M1", "M6"), ("M2",))),)


def _mismatch(s1v):
    return [f for f in s1v.all_findings if f.code == "declared_stage_mismatch"] if hasattr(s1v, "all_findings") else \
        [f for f in s1v.findings if f.code == "declared_stage_mismatch"]


def test_no_declared_means_no_comparison(tmp_path):
    _, s1v = H.build(tmp_path, H.MILLER)
    assert s1v.declared == ()
    assert _mismatch(s1v) == []


def test_matching_declaration(tmp_path):
    for dec in (MATCH, MATCH_WITH_LOADS):
        _, s1v = H.build(tmp_path, H.MILLER, declared=dec)
        assert _mismatch(s1v) == []
        assert s1v.declared != ()                                   # 대조를 했다(요약이 남는다)


def test_mismatching_declaration_is_review_needed(tmp_path):
    _, s1v = H.build(tmp_path, H.MILLER, declared=MISMATCH)
    hits = _mismatch(s1v)
    assert hits and all(h.severity == "review_needed" for h in hits)
    assert any({"M1", "M6"} <= set(h.subject) for h in hits)
    assert set(hits) <= set(s1v.review_needed)


def test_mismatch_does_not_stop_build(tmp_path):
    _, s1v = H.build(tmp_path, H.MILLER, declared=MISMATCH, stop_on_unsupported=True)
    assert s1v.unsupported == ()


def test_declared_is_not_a_derivation_input(tmp_path):
    _, plain = H.build(tmp_path, H.MILLER)
    _, dec = H.build(tmp_path, H.MILLER, declared=MISMATCH)
    assert [(b.key, b.stage, b.roles) for b in H.view(plain).blocks] == [(b.key, b.stage, b.roles) for b in H.view(dec).blocks]
    assert plain.key != dec.key                                     # declared 지문은 S1v 키에 든다


def test_odd_declaration_never_stops(tmp_path):
    # tail 하나만 적은 선언도 기록(review_needed)일 뿐 정지 분기가 아니다 -- 기본 모드에서 반환
    _, s1v = H.build(tmp_path, H.OTA5, declared=(("x", (("M5",),)),), stop_on_unsupported=True)
    assert s1v.unsupported == ()
