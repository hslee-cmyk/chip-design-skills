"""graph/polarity.py -- 루프 극성(계약 10.2 '극성 = CS gate->drain 반전 곱, 커패시터 경유 0', 계획 N3.2-7).

oracle (a) 손 유도: 셀·소자 부호의 곱(CS 반전 -1, CG·CD·pass·저항 +1), 커패시터를 지나면 0(미정의).
- CMFB: M5 CS(-1) · M3/M4 CS(-1) · R1/R2(+1) = +1 (이 손 회로는 일부러 양의 되먹임으로 연결했다 -- cm 이 오르면 M5 전류가 늘어
  cmfb 가 내려가고 PMOS M3 전류가 늘어 om 이 오른다).
- RFB: M1 CS(-1) · Rf(+1) = -1.  XCOUP: M4·M3 CS = +1.  BIASSCC: Mp2·Mp1 CS = +1.  MILLER: Cc 경유 -> 0.
"""
from __future__ import annotations

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
