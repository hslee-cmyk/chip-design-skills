"""graph/polarity.py -- 루프 극성(계약 10.2 '극성 = CS gate->drain 반전 곱, 커패시터 경유 0', 계획 N3.2-7).

oracle (a) 손 유도: 셀·소자 부호의 곱(CS 반전 -1, CG·CD·pass·저항 +1), 커패시터를 지나면 0(미정의).
- CMFB: M5 CS(-1) · M3/M4 CS(-1) · R1/R2(+1) = +1 (이 손 회로는 일부러 양의 되먹임으로 연결했다 -- cm 이 오르면 M5 전류가 늘어
  cmfb 가 내려가고 PMOS M3 전류가 늘어 om 이 오른다).
- RFB: M1 CS(-1) · Rf(+1) = -1.  XCOUP: M4·M3 CS = +1.  BIASSCC: Mp2·Mp1 CS = +1.  MILLER: Cc 경유 -> 0.

[U1b 2026-10-09] 설계 41 1.12.4(J-F)가 N3.2-7 의 '커패시터만 거치면 review_needed' 를 대체한다: 커패시터를 지나는 사이클은 극성
`ac_only`(info `loop_polarity_ac_only`, 그 수동소자는 GB5 보상 후보), 루프 뷰 극성 = 그 뷰에 속한 DC 사이클 극성(모두 같으면 그 값,
갈리면 `loop_polarity_conflict` review_needed, DC 사이클이 없으면 `loop_polarity_undefined`). 계약 불변량 (d): ac_only 이면 극성 0.
"""
from __future__ import annotations

import jrules_hand as J
import s1v_hand as H


def _pol(tmp_path, doc, vid="transfer:0"):
    _, s1v = H.build(tmp_path, doc)
    return sorted(lp.polarity for lp in H.view(s1v, vid).loops)


def test_two_inverting_cells_and_resistor_is_positive(tmp_path):
    assert _pol(tmp_path, H.CMFB) == [1, 1]
    assert _pol(tmp_path, H.CMFB, "loop:M5:cm") == [1, 1]


def test_single_inverting_cell_with_resistor_is_negative(tmp_path):
    assert _pol(tmp_path, H.RFB) == [-1]


def test_cross_coupled_pair_is_positive(tmp_path):
    assert _pol(tmp_path, H.XCOUP) == [1]
    assert _pol(tmp_path, H.BIASSCC) == [1]


def test_capacitor_path_is_undefined(tmp_path):
    assert _pol(tmp_path, H.MILLER) == [0]


def test_polarity_vocabulary(tmp_path):
    for doc in (H.CMFB, H.RFB, H.XCOUP, H.MILLER, H.BIASSCC):
        _, s1v = H.build(tmp_path, doc)
        assert {lp.polarity for v in s1v.views for lp in v.loops} <= {-1, 0, 1}


# ---------------------------------------------------------------- [U1b] 41 1.12.4 사이클·루프 뷰 극성
def _loop_view(tmp_path, doc, vid="loop:M5:cm"):
    _, s1v = H.build(tmp_path, doc)
    return H.view(s1v, vid)


def test_capacitor_cycle_is_ac_only(tmp_path):
    # MILLER 의 o1 -> out -Cc-> o1: 커패시터 경유 -> ac_only, 극성 0(계약 불변량 (d))
    _, s1v = H.build(tmp_path, H.MILLER)
    assert [(lp.ac_only, lp.polarity) for lp in H.view(s1v).loops] == [(True, 0)]


def test_loop_view_polarity_is_dc_cycle_polarity(tmp_path):
    # CMFB 루프 뷰: DC 사이클 둘(R1·R2 경유) 모두 +1 -> 뷰 극성 +1
    assert _loop_view(tmp_path, H.CMFB).polarity == 1


def test_dc_and_capacitor_cycles_in_one_loop_view(tmp_path):
    # POL_AC(jrules_hand): cm -M5-> cmfb -M3-> om -R1-> cm (+1), cm -> cmfb -M4-> op -R2-> cm (+1), cm -> cmfb -> om -Cx-> cm (ac_only).
    # 뷰 극성 = DC 사이클 극성 +1, info loop_polarity_ac_only(대상 = 커패시터 Cx, GB5 보상 후보), 갈림·미정의 기록 없음
    v = _loop_view(tmp_path, J.POL_AC)
    cyc = {(frozenset(lp.devices), lp.ac_only, lp.polarity) for lp in v.loops if lp.cut == ("M5", "cm")}
    assert cyc == {(frozenset({"M5", "M3", "R1"}), False, 1), (frozenset({"M5", "M4", "R2"}), False, 1),
                   (frozenset({"M5", "M3", "Cx"}), True, 0)}
    assert v.polarity == 1
    hits = [f for f in v.findings if f.code == "loop_polarity_ac_only"]
    assert [(h.severity, h.subject) for h in hits] == [("info", ("Cx",))]
    assert "Cx" in v.compensation_candidates
    assert not {"loop_polarity_conflict", "loop_polarity_undefined"} & set(H.codes(v))


def test_dc_cycles_with_different_signs_conflict(tmp_path):
    # POL_CONFLICT: cm -M5(CS -1)-> cmfb -Mf(CD +1)-> f -Rg-> cm = -1, R1·R2 사이클 = +1 -> loop_polarity_conflict(review_needed)
    v = _loop_view(tmp_path, J.POL_CONFLICT)
    signs = sorted(lp.polarity for lp in v.loops if lp.cut == ("M5", "cm") and not lp.ac_only)
    assert signs == [-1, 1, 1]
    hits = [f for f in v.findings if f.code == "loop_polarity_conflict"]
    assert [h.severity for h in hits] == ["review_needed"]


def test_pilot_cm_loop_view_polarity():
    # oracle (a) 손 유도 + (d) 41 1.13 극성 행: 파일럿 루프 뷰 loop:M37a:Voc 의 DC 사이클 4개
    #   N1a2a -M2a(CG +)-> Vom1 -M26(CS -)-> Vop -R2-> Voc -M37a(CS -)-> Vcmfb -M7(CS -)-> Vx -M1a(CG +)-> N1a2a = -1
    #   ... Vom1 -(M18a/M18b pass +)-> Vg25 -M25(CS -)-> Vop ... = -1, b 쪽 대칭 둘도 -1
    # Cc–Rz 우회 사이클 2개(Rz2·Cc2 / Rz1·Cc1 경유)는 ac_only -> 뷰 극성 -1
    _, s1v = H.build_lib("current_reuse_telescopic_ota")
    v = H.view(s1v, "loop:M37a:Voc")
    mine = [lp for lp in v.loops if lp.cut == ("M37a", "Voc")]
    assert sorted(lp.polarity for lp in mine if not lp.ac_only) == [-1, -1, -1, -1]
    assert len([lp for lp in mine if lp.ac_only]) == 2
    assert v.polarity == -1
    assert "loop_polarity_undefined" not in H.codes(v) and "loop_polarity_conflict" not in H.codes(v)
