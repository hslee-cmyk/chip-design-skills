"""노드 임피던스 등급 (설계 41 §1.7-4, 계획 N3.2-6).

진입점: `node_impedance(model, ground) -> dict`  ({넷: 등급}, 등급 ∈ IMP_LOW·IMP_HIGH·IMP_VALUE).

* 낮음: gm 차수 컨덕턴스를 주는 단자가 붙은 노드 -- gate 가 이 뷰의 교류접지인 MOS 의 source 단자, 또는 diode 연결 소자(gate == drain)의
  drain+gate.
* 값 의존: 낮음 단자가 없고 DC 를 통하는 수동소자(저항)가 붙은 노드.
* 높음: 그 밖(drain·gate·커패시터 단자만 붙음).
블록 출력노드 판정(`blocks`)과 극점 노드 목록(`pole_nodes`)이 같은 표를 쓴다(개념당 정의 하나). 교류접지 넷은 표에 없다.
"""
from gmid_engine.authoring import DC_CONDUCTING_PASSIVE_KINDS

from .s1v_values import IMP_HIGH, IMP_LOW, IMP_VALUE


def node_impedance(model, ground):
    low = set()
    for m in model.mos:
        if m.g == m.d:
            low.add(m.d)
        if m.g in ground:
            low.add(m.s)
    resistive = set()
    for p in model.passives:
        if p.kind in DC_CONDUCTING_PASSIVE_KINDS:
            resistive.update((p.a, p.b))
    table = {}
    for net in model.nets:
        if net in ground:
            continue
        table[net] = IMP_LOW if net in low else IMP_VALUE if net in resistive else IMP_HIGH
    return table
