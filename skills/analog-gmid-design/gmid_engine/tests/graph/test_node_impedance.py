"""graph/node_impedance.py -- 블록 출력노드 임피던스 등급(계약 10.2 '블록', 설계 41 1.7 (4), 계획 N3.2-6·9 (c)).

oracle (a) 손 유도. 등급 정의(41 1.7 (4)): 낮음 = gate 가 그 뷰에서 교류접지인 source 단자 또는 diode 가 붙은 노드, 높음 = drain·gate·
커패시터 단자만, 값 의존 = 낮음 단자 없이 저항이 붙은 노드. `Block.impedance` = (출력노드, 등급) 이름순.
"""
from __future__ import annotations

import s1v_hand as H


def _imp(tmp_path, doc, key):
    _, s1v = H.build(tmp_path, doc)
    return H.blocks(H.view(s1v))[key].impedance


def test_drain_only_output_is_high(tmp_path):
    assert _imp(tmp_path, H.CS, ("out",)) == (("out", "high"),)
    assert _imp(tmp_path, H.OTA5, ("out",)) == (("out", "high"),)
    assert _imp(tmp_path, H.FOLDED, ("out",)) == (("out", "high"),)


def test_miller_capacitor_terminal_keeps_high(tmp_path):
    # o1: drain(M2·M4) + gate(M6) + 커패시터 Cc / out: drain(M6·M7) + Cc
    _, s1v = H.build(tmp_path, H.MILLER)
    bl = H.blocks(H.view(s1v))
    assert (bl[("o1",)].impedance, bl[("out",)].impedance) == ((("o1", "high"),), (("out", "high"),))


def test_resistor_without_low_terminal_is_value_dependent(tmp_path):
    # om·op: drain(M1/M2, M3/M4) + 감지 저항 R1/R2, 낮음 단자 없음
    assert _imp(tmp_path, H.CMFB, ("om", "op")) == (("om", "value_dependent"), ("op", "value_dependent"))


def test_diode_on_output_is_low(tmp_path):
    assert _imp(tmp_path, H.CSDIODE, ("out",)) == (("out", "low"),)
