"""루프 절단 회로 -- 선언된 되먹임 수동소자 단자를 새 노드로 옮긴다 (7a design 2.2 L1~L4, 2.4 '계 구성', metrics CONTRACT 3.10).

진입점: `cut_circuit(circuit, cuts) -> CutCircuit`.

순수 함수다. `LoopCut(kind, index, terminal)` 마다 `circuit` 의 그 원소(저항·커패시터 index 번째)의 단자를 원래 노드 n 에서 새
노드 x 로 옮긴다. 같은 원래 노드에서 옮긴 단자는 모두 같은 x 로 간다(오라클 `lbx_<넷>` 하나와 같다). x 는 원래 회로의 최대
노드 인덱스 뒤에 n 오름차순으로 붙는다(재번호 불변, I-7 확장). 교류접지는 그대로다 -- 어느 노드를 고정할지(레일·gate 전용
미구동 넷·절단 안 된 입력 포트)는 선언에서 회로 레코드를 만드는 쪽(ss_linearize)이 정한다.
결과에는 프로브 여기 열 4k 개(단위 전류 I(n_j), I(x_j), 단위 전하 Q(n_j), Q(x_j))와 관측 2k 개(V(n_j), V(x_j))가 함께 든다 --
`build_mna(cut.circuit, cut.excitations, cut.senses)` 로 계 하나를 조립 1회 하면 `probe_factor` 가 그 응답에서 T 를 낸다.
입력 계약 위반(ValueError): cuts 가 비었다, index 가 원소 수 밖, 같은 원소를 두 번 끊음(두 단자 모두 -- 로더의
`feedback_cut_ambiguous` 와 같은 조건), 절단 노드가 교류접지(고정 노드는 끊을 수 없다).
"""
import dataclasses

from .mna_types import CutCircuit
from .records import LOOP_CUT_KINDS, LOOP_CUT_MOS, Excitation, LoopCut, Sense, SmallSignalCircuit

_UNIT = 1.0


def _nodes(circuit):
    out = set(circuit.ac_ground)
    for m in circuit.mos:
        out.update((m.d, m.g, m.s, m.b))
    for p in circuit.resistors + circuit.capacitors:
        out.update((p.a, p.b))
    return out


def _pools(circuit):
    # LoopCut.kind 어휘(records.LOOP_CUT_KINDS) -> 그 원소 tuple
    return dict(zip(LOOP_CUT_KINDS + (LOOP_CUT_MOS,), (circuit.resistors, circuit.capacitors, circuit.mos)))


def _check(circuit, cuts):
    if not isinstance(circuit, SmallSignalCircuit):
        raise TypeError("cut_circuit: circuit 는 SmallSignalCircuit 이어야 한다")
    if not isinstance(cuts, tuple) or not cuts:
        raise TypeError("cut_circuit: cuts 는 비어 있지 않은 LoopCut tuple 이어야 한다")
    seen = set()
    for cut in cuts:
        if not isinstance(cut, LoopCut):
            raise TypeError("cut_circuit: cuts 원소는 LoopCut 이어야 한다: %r" % (cut,))
        pool = _pools(circuit)[cut.kind]
        if cut.index >= len(pool):
            raise ValueError("cut_circuit: %s index %r 이 원소 수 %r 밖이다" % (cut.kind, cut.index, len(pool)))
        if (cut.kind, cut.index) in seen:
            raise ValueError("cut_circuit: 같은 원소 (%s, %r) 를 두 번 끊는다" % (cut.kind, cut.index))
        seen.add((cut.kind, cut.index))


def _probe_columns(pairs):
    nodes = tuple(n for n, _ in pairs) + tuple(x for _, x in pairs)
    currents = tuple(Excitation("probe_current_%d" % node, currents=((node, _UNIT),)) for node in nodes)
    charges = tuple(Excitation("probe_charge_%d" % node, charges=((node, _UNIT),)) for node in nodes)
    return currents + charges, tuple(Sense(node) for node in nodes)


def cut_circuit(circuit, cuts):
    """`SmallSignalCircuit`, `LoopCut` tuple -> `CutCircuit`."""
    _check(circuit, cuts)
    pools = {kind: list(elements) for kind, elements in _pools(circuit).items()}
    origin = []
    for cut in cuts:
        node = getattr(pools[cut.kind][cut.index], cut.terminal)
        if node in circuit.ac_ground:
            raise ValueError("cut_circuit: 절단 노드 %r 이 교류접지(고정 노드)다" % (node,))
        origin.append(node)
    cut_nodes = sorted(set(origin))
    top = max(_nodes(circuit))
    new_node = {n: top + 1 + rank for rank, n in enumerate(cut_nodes)}
    for cut, node in zip(cuts, origin):
        element = pools[cut.kind][cut.index]
        pools[cut.kind][cut.index] = dataclasses.replace(element, **{cut.terminal: new_node[node]})
    resistors, capacitors, mos = (tuple(pools[kind]) for kind in LOOP_CUT_KINDS + (LOOP_CUT_MOS,))
    cut = dataclasses.replace(circuit, resistors=resistors, capacitors=capacitors, mos=mos)
    pairs = tuple((n, new_node[n]) for n in cut_nodes)
    excitations, senses = _probe_columns(pairs)
    return CutCircuit(circuit=cut, cuts=cuts, pairs=pairs, excitations=excitations, senses=senses)
