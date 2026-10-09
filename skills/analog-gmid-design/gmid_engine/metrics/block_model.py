"""블록 국소 gain 모델 (설계 41 §2.1·§2.3, 체크리스트 D-BM, 계획 P N3.8 '블록 국소 모델').

진입점: `block_local_gain(ss, block, drive, others=(), exclude=(), extra=()) -> BlockGain`.

* **미지수** = 블록 소유 노드(블록 노드 − 입력 넷). **입력 넷**은 `drive`({넷: V})로 구동한다 -- 생략하면 단위 구동(입력 하나 = 1 V, 둘 = ±1/2 V
  입력 넷 이름순, 차동 ±1/|D|)이고 사슬(`block_residual`)은 앞 블록의 국소 해 전압을 준다. 블록 밖 노드는 교류접지(`others` = 다른 블록 노드)로 둔다.
* **스탬프 소자** = 소유 노드(또는 아래 폐포로 늘어난 미지수 노드)에 채널·저항 단자가 닿는 MOS·저항 -- 스탬프 값은 봉인 `ss`(`ss_dev` 의 gm·gmb·gds)에서 온다.
  S1v 의 `roles` 가 아니라 netlist 인접으로 정한다: 버퍼 블록은 S1v 에서 follower 소자만 멤버이고 출력노드에 닿는 부하 소자·수동소자를 붙이지 않지만(U10
  관찰), DC 이득·출력 임피던스는 그 소자들에 달렸다. 인접 규칙이면 이득 블록과 같은 규칙이 된다. 용량(CL, Cc)은 ω → 0 극한에서 열린 회로라 스탬프하지 않는다 --
  출력 CL 을 붙이지 않아도 DC 이득·Z_out 에 영향이 없다(주파수 의존 양을 넣으면 그때 같이 붙인다).
* 폐포: 소유도 접지도 다른 블록 노드도 아닌 넷(예: 직렬 Rz–Cc 의 중간 넷, feedforward 묶음 내부 넷)은 그 블록 소자가 닿으면 미지수로 넣고 그 넷에 닿는 소자도
  끌어온다(DC 에 뜬 노드가 접지로 잘못 눌리지 않게). `exclude`(S1v 가 주경로에서 뺀 feedforward 묶음 소자)는 어느 경우에도 스탬프하지 않고, `extra`(merge 블록의
  FF 묶음)는 항상 스탬프한다.
* **산출**: `gain` = V(out)/V(in)(입력 둘이면 차, 출력 둘이면 차 -- 차동은 ±½ 이라 입력 1 V), `zout_ohm` = 입력 접지·출력 단위 전류(출력 둘이면 +1/−1)의 출력 전압(차),
  `node_v`(사슬 입력), 복합 블록(`kind == composite`, 입력 둘 이상)은 경로별 기여 `contributions`((입력 넷, 기여), 다른 경로 입력 소자의 gm·gmb 를 0 으로 둔 국소 해, 부호 포함)를
  내고 `gain` 은 None(`composite_paths` -- 한 이득 값이 아니다), `decomposed_only` = 소유 노드와 블록 밖 노드(입력 넷·다른 블록 노드)를 잇는 저항(블록을 가로지르는 되먹임 수동소자)이 있는가 -- 저항이 닿는 블록 모두에 표시(41 §2.2 '분해값'), 상대 풀이 잔차.
* 정의 불가(값으로): 출력이 없거나 셋 이상(`unsupported_outputs`), 입력이 없거나 셋 이상(`unsupported_inputs`), 입력 차 0(`input_zero`), 계 특이(`singular_dc`).
"""
import dataclasses
import math

import numpy

from gmid_engine.core import AMPLITUDE_DB_PER_DECADE
from gmid_engine.graph import BLOCK_COMPOSITE

from ._helpers_nodal import conductance_matrix, nodal_adjoint, nodal_factor, nodal_solve
from .aux_types import BlockGain
from .mna_types import Undefined
from .records import SmallSignalCircuit

QUANTITY = "block_gain"
SINGLE = 1
PAIR = 1 + 1                                    # 차동 = 넷 둘(±1/|D|, |D| = 2)


def _undefined(code, detail=()):
    return (Undefined(QUANTITY, code, "definitional", detail),)


def _unit_drive(inputs):
    """블록 입력 넷 tuple -> 단위 구동 {넷: V} (하나 = 1 V, 둘 = 이름순 +½/−½). 그 밖 개수는 빈 dict."""
    nets = tuple(sorted(inputs))
    if len(nets) == SINGLE:
        return {nets[0]: 1.0}
    if len(nets) == PAIR:
        return {nets[0]: 1.0 / len(nets), nets[1]: -1.0 / len(nets)}
    return {}


def _difference(volts, nets):
    """넷 하나 = 그 전압, 둘 = 첫째 − 둘째(이름순), 그 밖 None."""
    ordered = tuple(sorted(nets))
    if len(ordered) == SINGLE:
        return volts[ordered[0]]
    if len(ordered) == PAIR:
        return volts[ordered[0]] - volts[ordered[1]]
    return None


def _select(ss, owned, fixed_out, exclude, extra):
    """스탬프 소자 선택(폐포). -> (MOS 라벨 집합, 저항 라벨 집합, 미지수 노드 집합)."""
    elements = tuple((m.label, (m.d, m.s)) for m in ss.circuit.mos) + tuple((r.label, (r.a, r.b)) for r in ss.circuit.resistors)
    terms_of = dict(elements)
    unknown = set(owned)
    selected = {label for label in extra if label in terms_of}
    for label in selected:
        unknown.update(t for t in terms_of[label] if t not in fixed_out)
    changed = True
    while changed:
        changed = False
        for label, terms in elements:
            if label in selected or label in exclude or not any(t in unknown for t in terms):
                continue
            selected.add(label)
            unknown.update(t for t in terms if t not in fixed_out)
            changed = True
    mos_labels = {m.label for m in ss.circuit.mos}
    return selected & mos_labels, selected - mos_labels, unknown


def _path_gains(ss, block, index, size, mos_labels, res_labels, unknown, outputs):
    """복합 블록(41 §2.1): 입력 넷(경로)마다 '다른 경로 입력 소자의 gm 을 0 으로 둔 국소 해' -- 그 입력 1 V·나머지 0 V 구동의 출력(차) = 경로 기여(부호 포함).
    다른 경로 입력 소자 = gate 가 다른 입력 넷인 MOS(gm·gmb 를 0 으로, gds 는 둔다). -> ((입력 넷, 기여), ...) 입력 넷순."""
    out = []
    for net in sorted(block.inputs):
        others = {n for n in block.inputs if n != net}
        zeroed = tuple(dataclasses.replace(m, gm=0.0, gmb=0.0) if ss.nodes[m.g] in others else m
                       for m in ss.circuit.mos if m.label in mos_labels)
        sub = SmallSignalCircuit(mos=zeroed, resistors=tuple(r for r in ss.circuit.resistors if r.label in res_labels))
        volt, _residual = nodal_solve(nodal_factor(conductance_matrix(sub, size), set(range(size)) - unknown), size, {index[net]: 1.0})
        if volt is None:
            return ()
        out.append((net, float(_difference({n: volt[index[n]] for n in outputs}, outputs))))
    return tuple(out)


def block_local_gain(ss, block, drive=None, others=(), exclude=(), extra=()):
    drive = _unit_drive(block.inputs) if drive is None else drive
    index = {net: i for i, net in enumerate(ss.nodes)}
    size = len(ss.nodes)
    ground = {index[n] for n in ss.ground_nets}
    inputs = {index[n] for n in block.inputs}
    driven = {index[n] for n in drive}
    owned = {index[n] for n in block.nodes} - inputs - driven - ground
    outside = {index[n] for n in others if n in index} - owned
    fixed_out = ground | driven | inputs | outside
    mos_labels, res_labels, unknown = _select(ss, owned, fixed_out, frozenset(exclude), frozenset(extra))
    sub = SmallSignalCircuit(mos=tuple(m for m in ss.circuit.mos if m.label in mos_labels),
                             resistors=tuple(r for r in ss.circuit.resistors if r.label in res_labels))
    members = tuple(sorted(mos_labels | res_labels))
    g = conductance_matrix(sub, size)
    factor = nodal_factor(g, set(range(size)) - unknown)
    volt, residual = nodal_solve(factor, size, {index[n]: v for n, v in drive.items()})
    if volt is None:
        return BlockGain(block.key, None, None, None, undefined=_undefined("singular_dc"), members=members)
    names = {i: n for n, i in index.items()}
    node_v = tuple(sorted((names[i], float(volt[i])) for i in unknown | driven))
    by_net = dict(node_v)
    outputs = tuple(n for n in block.outputs)
    across = inputs | outside                                      # 블록 경계 밖 노드(입력 넷 + 다른 블록 노드)
    decomposed = any((r.a in across and r.b in unknown) or (r.b in across and r.a in unknown)
                     for r in ss.circuit.resistors if r.label in res_labels)
    if len(outputs) not in (SINGLE, PAIR) or any(n not in by_net for n in outputs):
        return BlockGain(block.key, None, None, None, (), decomposed, residual, node_v, members, _undefined("unsupported_outputs"))
    if block.kind == BLOCK_COMPOSITE and len(block.inputs) > SINGLE:
        paths = _path_gains(ss, block, index, size, mos_labels, res_labels, unknown, outputs)
        return BlockGain(block.key, None, None, None, paths, decomposed, residual, node_v, members, _undefined("composite_paths"))
    inputs_v = {n: drive.get(n, 0.0) for n in block.inputs}
    vin = _difference(inputs_v, block.inputs) if len(block.inputs) in (SINGLE, PAIR) else None
    if vin is None:
        return BlockGain(block.key, None, None, None, (), decomposed, residual, node_v, members, _undefined("unsupported_inputs"))
    out_pair = tuple(sorted(outputs))
    unit = numpy.zeros(size)                                        # 출력 단위 전류 주입(둘이면 +1/−1) = 관측 벡터(상호성: Z_out = e·G⁻¹·e)
    unit[index[out_pair[0]]] = 1.0
    if len(out_pair) == PAIR:
        unit[index[out_pair[1]]] = -1.0
    z = nodal_adjoint(factor, size, unit)
    zout = None if z is None else float(z @ unit)
    if not abs(vin) > 0:
        return BlockGain(block.key, None, None, zout, (), decomposed, residual, node_v, members, _undefined("input_zero"))
    gain = _difference(by_net, outputs) / vin
    gain_db = AMPLITUDE_DB_PER_DECADE * math.log10(abs(gain)) if gain != 0 else None
    return BlockGain(block.key, float(gain), gain_db, zout, (), decomposed, residual, node_v, members)
