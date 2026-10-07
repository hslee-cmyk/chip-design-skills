"""레일별 공급 전류·전력 (설계 design_mod1_lut_mod5_mna 3.4 `supply_current_dc`·`power_dc_w`, 계획 DEC-78, DF-16).

진입점: `supply_currents`.

레일 k 에서 회로로 들어가는 전류 I_k = 레일 노드에 닿는 가지 전류의 합(레일 노드에서 나가는 방향):
* MOS 채널(`ChannelCurrent`, drain→source 전류 i): drain 이 k 면 +i, source 가 k 면 −i.
* 저항 a–b: a 가 k 면 (V_k − V_b)/R, b 가 k 면 (V_k − V_a)/R(노드 전압은 `rails` 와 `node_v`).
* 이상 전류원(`CurrentSource`, from→to 로 amp): from 이 k 면 +amp, to 가 k 면 −amp.
`supply_current_dc` = 선언된 합산 레일(`counted_rails`) 의 I_k 합(DEC-78 '선언된 레일 기준으로 합한다' -- 소자 전류 단순 합을
쓰지 않는다, DF-16). `power_dc_w` = Σ_k V_k·I_k(모든 레일). `kcl_residual_amp` = Σ_k I_k -- 레일 전위를 같이 Δ 옮기면
power 는 Δ·잔차만큼만 변한다(IC11). 레일 이름 기본값 없음(옛 ("vdd","VDD") 폐기) -- 레일은 노드 인덱스로만 받는다.
"""
from .mna_types import SupplyCurrents
from .records import DcOperatingPoint


def _voltages(op):
    volts = dict(op.node_v)
    for rail in op.rails:
        if rail.node in volts and volts[rail.node] != rail.volt:
            raise ValueError("레일 노드 %r 의 node_v 가 레일 전압과 다르다" % (rail.node,))
        volts[rail.node] = rail.volt
    return volts


def _rail_current(op, node, volts):
    total = 0.0
    for ch in op.channels:
        if ch.drain == node:
            total += ch.amp
        if ch.source == node:
            total -= ch.amp
    for r in op.resistors:
        if node in (r.a, r.b):
            other = r.b if r.a == node else r.a
            if other not in volts:
                raise ValueError("저항 %r 의 반대 노드 %r 전압이 node_v 에 없다" % (r.label, other))
            total += (volts[node] - volts[other]) / r.ohm
    for src in op.sources:
        if src.from_node == node:
            total += src.amp
        if src.to_node == node:
            total -= src.amp
    return total


def supply_currents(op, counted_rails):
    """`DcOperatingPoint`, 합산 레일 노드 tuple(선언) -> `SupplyCurrents`."""
    if not isinstance(op, DcOperatingPoint):
        raise TypeError("supply_currents 는 DcOperatingPoint 를 받는다")
    rail_nodes = tuple(sorted(r.node for r in op.rails))
    if not isinstance(counted_rails, tuple) or not counted_rails:
        raise ValueError("supply_currents: 합산 레일 선언(counted_rails)이 비었다 -- 기본값 없음")
    unknown = sorted(set(counted_rails) - set(rail_nodes))
    if unknown or len(set(counted_rails)) != len(counted_rails):
        raise ValueError("supply_currents: 합산 레일 %r 이 레일 선언 밖이거나 중복이다" % (counted_rails,))
    volts = _voltages(op)
    per_rail = tuple((node, _rail_current(op, node, volts)) for node in rail_nodes)
    currents = dict(per_rail)
    return SupplyCurrents(
        per_rail=per_rail,
        counted_rails=tuple(sorted(counted_rails)),
        supply_current_dc=sum(currents[k] for k in sorted(counted_rails)),
        power_dc_w=sum(volts[k] * i for k, i in per_rail),
        kcl_residual_amp=sum(i for _, i in per_rail),
    )
