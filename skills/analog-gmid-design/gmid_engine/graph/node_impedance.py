"""노드 임피던스 등급 (설계 41 §1.7-4, 계획 N3.2-6).

진입점: `node_impedance(model, ground, pass_devices) -> dict`  ({넷: 등급}, 등급 ∈ IMP_LOW·IMP_HIGH·IMP_VALUE).

* 낮음: gm 차수 컨덕턴스를 주는 단자가 붙은 노드 -- MOS 의 source 단자(gate 가 교류접지이든 앞단이 구동하든 무관 -- 출력 임피던스는 입력
  신호를 0 으로 놓고 보므로 source 를 들여다보면 1/gm 차수다, follower 출력 포함. 2026-10-08 정정), 또는 diode 연결 소자(gate == drain)의 drain+gate.
* 값 의존: 낮음 단자가 없고 DC 를 통하는 수동소자(저항)가 붙은 노드.
* 높음: 그 밖(drain·gate·커패시터 단자만 붙음).
* pass 묶음 소자(`pass_devices`)의 단자는 등급에 기여하지 않는다 -- 두 노드를 잇는 통로라 끝 노드는 반대편 노드의 종류를 상속한다(41 §1.6-5).
블록 출력노드 등급(`blocks`·`buffer_bundles` 의 Block.impedance)과 극점 노드 목록(`pole_nodes`)이 같은 표를 쓴다(개념당 정의 하나, 등급이 둘이면 결함). 교류접지 넷은 표에 없다.
"""
from gmid_engine.authoring import DC_CONDUCTING_PASSIVE_KINDS

from .s1v_values import IMP_HIGH, IMP_LOW, IMP_VALUE


def node_impedance(model, ground, pass_devices=frozenset()):
    low = set()
    for m in model.mos:
        if m.name in pass_devices:
            continue
        if m.g == m.d:
            low.add(m.d)
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
