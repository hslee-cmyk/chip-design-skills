"""블록 국소 gain 모델 (설계 41 §2.1·§2.3·§2.5, 체크리스트 D-BM, 계획 P N3.8 '블록 국소 모델').

진입점: `block_local_gain(ss, block, drive=None, others=(), exclude=(), extra=(), ground=()) -> BlockGain`.

정의 = ω → 0 극한 KCL(§2.5). 미지수 집합은 행 모드(`block_gain_model.block_gain_model_of`)와 같은 규칙이고 스탬프 조립도 같은 함수(`block_gain_rows.block_stamp_matrix`)다 --
값 출처만 다르다(여기는 봉인 `ss` 의 gm·gmb·gds).
* **고정 집합 F** = 교류접지(`ss.ground_nets` ∪ `ground`(그 뷰 교류접지)) ∪ 여기 넷(입력 넷·`drive` 키) ∪ 남의 블록 넷(`others` − 자기 `block.nodes`). F 의 전압은 `drive` 값 또는 0 이다.
* **미지수 집합 U_b** = (블록 노드 ∪ 블록 소자(`block.members`)·`extra` 소자의 d·s·저항 단자 ∪ 저항 폐포 ∪ 용량 전용 넷) − F. 폐포: U_b 에 단자가 닿는 저항(`exclude` 제외)을
  스탬프하고 다른 단자가 F 밖이면 U_b 에 넣는다(되풀이). 비멤버 MOS 는 U_b 를 넓히지 않는다.
* **스탬프 소자**: d 또는 s 가 U_b 에 닿는 MOS(멤버든 비멤버든 -- 다른 단자는 고정 전압, 분기 없는 단자 스탬프), U_b 에 닿는 저항, `extra` 소자. `exclude`(S1v 가 주경로에서 뺀 feedforward
  묶음 소자)는 스탬프하지 않고 `extra`(merge 블록의 FF 묶음)가 우선한다. 막다른 가지(U_b 안, 출력 아님, 저항 단자 정확히 하나, 스탬프 MOS 의 d·s·g·b 가 안 닿는 넷, 용량으로 전하 넷과 이어진 넷 아님)는 그 넷과 저항을 뺀다(되풀이).
* **용량 전용 넷**: 전회로에 d·s·저항 단자가 없고 F 밖이며 스탬프 MOS 의 g·b 가 읽는 넷, 그 넷과 용량으로 이어진 같은 종류의 넷. 이 넷은 0 V 로 채우지 않고 전하 보존 행(전회로 C)으로 푼다
  (`_helpers_nodal.nodal_factor`). 전하 넷이 있을 때만 전회로 C 를 조립한다. 전하 넷이 있는데 값 없는 수동소자(`ss.missing`)가 있으면 C 가 불완전해 `singular_dc`.
* **산출**: `gain` = V(out)/V(in)(입력 둘이면 차, 출력 둘이면 차 -- 차동은 ±½ 이라 입력 1 V), `zout_ohm` = 입력 접지·출력 단위 전류(출력 둘이면 +1/−1)의 출력 전압(차),
  `node_v`(U_b ∪ 구동 넷, 사슬 입력), 복합 블록(`kind == composite`, 입력 둘 이상)은 경로별 기여 `contributions`((입력 넷, 기여), 다른 입력 넷에 gate 가 있는 소자의 gm·gmb 를 0 으로 둔 같은 모델의 해,
  부호 포함)를 내고 `gain` 은 None(`composite_paths` -- 한 이득 값이 아니다), `decomposed_only` = 스탬프 저항이 U_b 와 입력 또는 남의 블록 넷을 잇는가(블록을 가로지르는 되먹임 수동소자 --
  41 §2.2 '분해값'), 상대 풀이 잔차.
* 정의 불가(값으로): 출력이 없거나 셋 이상(`unsupported_outputs`), 입력이 없거나 셋 이상(`unsupported_inputs`), 입력 차 0(`input_zero`), 계 특이(`singular_dc`).
"""
import collections
import math

import numpy

from gmid_engine.core import AMPLITUDE_DB_PER_DECADE
from gmid_engine.graph import BLOCK_COMPOSITE

from ._helpers_nodal import capacitance_matrix, nodal_adjoint, nodal_factor, nodal_solve
from .aux_types import BlockGain
from .block_gain_rows import block_stamp_matrix
from .mna_types import Undefined

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


def _structure(ss, block, drive, others, exclude, extra, ground):
    """미지수 집합·스탬프 소자(모듈 문서). -> (고정 집합 F, 미지수 U_b(전하 넷 제외), 전하 넷, 스탬프 MOS 라벨 집합, 스탬프 저항 라벨 집합) -- 넷은 노드 index."""
    index = {net: i for i, net in enumerate(ss.nodes)}
    mos = {m.label: m for m in ss.circuit.mos}
    res = {r.label: r for r in ss.circuit.resistors}
    outside = set(others) - set(block.nodes)
    fixed = {index[n] for n in set(ss.ground_nets) | set(ground) | set(drive) | set(block.inputs) | outside if n in index}
    barred = set(exclude) - set(extra)
    owners = (set(block.members) | set(extra)) - barred
    unknown = {index[n] for n in block.nodes if n in index}
    for name in owners:
        if name in mos:
            unknown |= {mos[name].d, mos[name].s}
        elif name in res:
            unknown |= {res[name].a, res[name].b}
    unknown -= fixed
    changed = True
    while changed:                                                             # 저항 폐포: U_b 에 닿는 저항의 다른 끝(F 밖)을 넣는다
        changed = False
        for label, r in res.items():
            if label not in barred and (r.a in unknown or r.b in unknown):
                new = {t for t in (r.a, r.b) if t not in fixed and t not in unknown}
                if new:
                    unknown |= new
                    changed = True
    outputs = {index[n] for n in block.outputs if n in index}
    conducting = {t for m in mos.values() for t in (m.d, m.s)} | {t for r in res.values() for t in (r.a, r.b)}
    cap_only = set(range(len(ss.nodes))) - conducting - fixed
    capacitors = [(k.a, k.b) for k in ss.circuit.capacitors if k.a in cap_only and k.b in cap_only]
    dropped = set()
    while True:
        stamped_mos = {l for l, m in mos.items() if l not in barred and (m.d in unknown or m.s in unknown)} | (set(extra) & set(mos))
        touched = {t for l in stamped_mos for t in (mos[l].d, mos[l].g, mos[l].s, mos[l].b)}
        live = {l: r for l, r in res.items() if l not in dropped and l not in barred and (r.a in unknown or r.b in unknown or l in extra)}
        count = collections.Counter(t for r in live.values() for t in (r.a, r.b))
        charge = {t for l in stamped_mos for t in (mos[l].g, mos[l].b)} & cap_only | (unknown & cap_only)
        grown = True
        while grown:                                                           # 용량으로 이어진 같은 종류(용량 전용)의 넷
            grown = False
            for a, b in capacitors:
                if (a in charge) != (b in charge):
                    charge |= {a, b}
                    grown = True
        read = {t for k in ss.circuit.capacitors for t, o in ((k.a, k.b), (k.b, k.a)) if o in charge}   # 블록 안 C 독자: 전하 넷과 용량으로 이어진 넷
        dead = {n for n in unknown if n not in outputs and n not in touched and n not in read and count[n] == 1}
        if not dead:
            break
        unknown -= dead                                                        # 막다른 가지: 넷과 그 저항을 뺀다(되풀이)
        dropped |= {l for l, r in live.items() if r.a in dead or r.b in dead}
    return fixed, unknown - charge, charge, stamped_mos, set(live)


def _stamp(ss, mos_labels, res_labels, zeroed=()):
    """스탬프 소자 라벨 집합 -> `block_stamp_matrix` 입력. `zeroed` = gate 넷 이름 집합(그 gate 의 gm·gmb 를 0 으로 둔다 -- 복합 블록 경로 기여)."""
    names = ss.nodes
    mos = tuple((names[m.d], names[m.g], names[m.s], names[m.b], 0.0 if names[m.g] in zeroed else m.gm, m.gds, 0.0 if names[m.g] in zeroed else m.gmb)
                for m in ss.circuit.mos if m.label in mos_labels)
    res = tuple((names[r.a], names[r.b], 1.0 / r.ohm) for r in ss.circuit.resistors if r.label in res_labels)
    return mos, res


def _path_gains(ss, block, index, c, fixed_all, mos_labels, res_labels, outputs):
    """복합 블록(41 §2.1): 입력 넷(경로)마다 '다른 경로 입력 소자의 gm 을 0 으로 둔 같은 모델의 해' -- 그 입력 1 V·나머지 0 V 구동의 출력(차) = 경로 기여(부호 포함).
    다른 경로 입력 소자 = gate 가 다른 입력 넷인 MOS(gm·gmb 를 0 으로, gds 는 둔다). -> ((입력 넷, 기여), ...) 입력 넷순."""
    out = []
    for net in sorted(block.inputs):
        mos, res = _stamp(ss, mos_labels, res_labels, zeroed={n for n in block.inputs if n != net})
        g = block_stamp_matrix(ss.nodes, mos, res)[0]
        volt, _residual = nodal_solve(nodal_factor(g, fixed_all, c=c), len(ss.nodes), {index[net]: 1.0})
        if volt is None:
            return ()
        out.append((net, float(_difference({n: volt[index[n]] for n in outputs}, outputs))))
    return tuple(out)


def block_local_gain(ss, block, drive=None, others=(), exclude=(), extra=(), ground=()):
    drive = _unit_drive(block.inputs) if drive is None else drive
    index = {net: i for i, net in enumerate(ss.nodes)}
    size = len(ss.nodes)
    fixed, unknown, charge, mos_labels, res_labels = _structure(ss, block, drive, others, exclude, extra, ground)
    members = tuple(sorted(mos_labels | res_labels))
    if charge and ss.missing:                                                  # 전하 보존 행은 그 넷에 닿는 모든 용량이 필요하다 -- 값 없는 수동소자가 있으면 C 가 불완전
        return BlockGain(block.key, None, None, None, undefined=_undefined("singular_dc"), members=members)
    mos, res = _stamp(ss, mos_labels, res_labels)
    g = block_stamp_matrix(ss.nodes, mos, res)[0]
    c = capacitance_matrix(ss.circuit, size) if charge else numpy.zeros((size, size))
    fixed_all = set(range(size)) - unknown - charge
    factor = nodal_factor(g, fixed_all, c=c)
    volt, residual = nodal_solve(factor, size, {index[n]: v for n, v in drive.items()})
    if volt is None:
        return BlockGain(block.key, None, None, None, undefined=_undefined("singular_dc"), members=members)
    names = {i: n for n, i in index.items()}
    driven = {index[n] for n in drive if n in index}
    node_v = tuple(sorted((names[i], float(volt[i])) for i in unknown | charge | driven))
    by_net = dict(node_v)
    outputs = tuple(n for n in block.outputs)
    across = {index[n] for n in set(block.inputs) | (set(others) - set(block.nodes)) if n in index}      # 블록 경계 밖 노드(입력 넷 + 남의 블록 넷)
    resistors = {r.label: r for r in ss.circuit.resistors}
    decomposed = any((resistors[l].a in across and resistors[l].b in unknown) or (resistors[l].b in across and resistors[l].a in unknown) for l in res_labels)
    if len(outputs) not in (SINGLE, PAIR) or any(n not in by_net for n in outputs):
        return BlockGain(block.key, None, None, None, (), decomposed, residual, node_v, members, _undefined("unsupported_outputs"))
    if block.kind == BLOCK_COMPOSITE and len(block.inputs) > SINGLE:
        paths = _path_gains(ss, block, index, c, fixed_all, mos_labels, res_labels, outputs)
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
    zout = None if z is None else float(sum(z[i] * unit[i] for i in numpy.flatnonzero(unit)))       # 전하 넷의 NaN 은 단위 벡터 0 과 곱하지 않는다
    if not abs(vin) > 0:
        return BlockGain(block.key, None, None, zout, (), decomposed, residual, node_v, members, _undefined("input_zero"))
    gain = _difference(by_net, outputs) / vin
    gain_db = AMPLITUDE_DB_PER_DECADE * math.log10(abs(gain)) if gain != 0 else None
    return BlockGain(block.key, float(gain), gain_db, zout, (), decomposed, residual, node_v, members)
