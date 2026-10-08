"""대신호 필드 -- 슬루 등가 용량과 방향별 최대 전류 (설계 40 §3.8-3, 계획 N3.5 '출력 구동 규칙'·DEC-58·DEC-65, 체크리스트 D-GB8a).

진입점: `ls_fields(ss, vstruct, ops, volts, bounds, lut, rel_tols=None, driving=None, outputs=()) -> LsFields`.

극점 노드 k(gain 제약 전달 뷰의 `pole_nets` 중 S1v `output_direction` 에 공급 셀 목록이 있는 것)마다:
* **`c_slew_farad`** = 봉인점 노드 용량 + 그 노드에 걸린 보상 커패시터(Miller 커패시터는 반대 노드가 따라 움직이므로 전체 값) + 출력 포트 노드이면 부하 요소 값. 구현은 노드 k 에
  한 단자가 닿은 모든 용량의 크기 합이다: MOS 단자 용량(cgs·cgd·cgb·cdb·csb -- 부호가 있는 BSIM4 용량이라 크기로 합산, 보수적) + 회로의 용량 소자(보상·부하는 이 소자로 이미
  들어 있다). 극점 계산용 `ss.node_c_farad`(Miller 효과로 곱한 값)와 다른 필드다.
* **방향별 최대 전류**(DEC-65): 충전/방전 방향마다 노드에 전류를 공급하는 셀(S1v `output_direction`의 charge·discharge 목록)의 합. 셀 종류에 따라
  - β(바이어스 셀): 봉인점 ID,
  - σ(신호 셀): LUT ID(VGS_max) -- VGS_max = 게이트 넷의 경로 합 구간(`bounds`, `ls_swing`)의 끝(NMOS hi, PMOS lo)과 그 소자 source 의 DC 전압 차, 같은 VDS·VSB 에서 LUT
    `op_point` 의 IDu·W/L. 봉인점 VGS 보다 작게 나오면 봉인점 ID 를 쓴다(공급 셀은 현재 전류 이상을 낼 수 있다),
  - κ(측면 주입 셀): 상한 미상(None -- J3·J12 결론).
  하나라도 미상이거나 공급 셀이 없으면 그 방향 전류는 None. 슬루율 = 전류 / `c_slew_farad`.
* 분해능: 방향 전류의 분해능 = Σ 공급 셀 (그 소자 `rel_tols` = (gm/ID)·tol_V 의 상대 오차 × 전류); β 셀은 θ 전류라 오차 0(부동소수 해상도), 모든 셀이 허용오차를 가져야 정한다.
* `driving`(spec `DrivingDecl`)에 `load_peak_amp` 가 있으면 `outputs` 의 방향 전류 최솟값 − 피크 전류를 `load_peak_margin_a` 로 낸다(미상이면 None). 슬루율 선언은 제약 행으로
  `search.ss_constraints` 가 이 필드로 만든다.
"""
import sys

from gmid_engine.core import SealViolationError
from gmid_engine.graph import DIR_BETA, DIR_SIGMA, NMOS
from gmid_engine.lut import op_point

from .aux_types import LsFields, LsNode

CHARGE = "charge"
DISCHARGE = "discharge"


def _node_capacitance(ss):
    """{넷: 그 넷에 닿은 용량 크기 합 (F)}."""
    names = ss.nodes
    total = {n: 0.0 for n in names}
    for m in ss.circuit.mos:
        for a, b, value in ((m.g, m.s, m.cgs), (m.g, m.d, m.cgd), (m.g, m.b, m.cgb), (m.d, m.b, m.cdb), (m.s, m.b, m.csb)):
            for node in (a, b):
                total[names[node]] += abs(value)
    for c in ss.circuit.capacitors:
        for node in (c.a, c.b):
            total[names[node]] += c.farad
    return total


def _signal_current(label, pins, ops, volts, bounds, lut):
    """σ 셀 한 소자의 ID(VGS_max) [A] 또는 None(LUT 가 정의하지 못함)."""
    op = ops[label]
    _drain, gate, source = pins[label]
    lo, hi = bounds[gate]
    source_v = volts[source]
    vgs_max = (hi - source_v) if op.kind == NMOS else (source_v - lo)
    if not vgs_max > op.vgs:
        return op.current
    try:
        point = op_point(lut.memo, op.kind, op.w_key, op.L, vgs_max, op.vds, op.vsb)
    except SealViolationError:
        return None
    return max(op.current, point.IDu * op.W / op.L)


def _cell_current(label, cls, pins, ops, volts, bounds, lut):
    if cls == DIR_BETA:
        return ops[label].current
    if cls == DIR_SIGMA:
        return _signal_current(label, pins, ops, volts, bounds, lut)
    return None                                                       # κ(측면 주입 셀): 상한 미상


def _direction(cells, direction, pins, ops, volts, bounds, lut, rel_tols):
    rows = tuple((direction, label, cls, _cell_current(label, cls, pins, ops, volts, bounds, lut)) for label, cls in cells)
    if not rows or any(r[3] is None for r in rows):
        return rows, None, None
    total = sum(r[3] for r in rows)
    res = 0.0
    for _d, label, cls, current in rows:
        eps = 0.0 if cls == DIR_BETA else (rel_tols or {}).get(label)
        if eps is None:
            return rows, total, None
        res += max(eps * current, sys.float_info.epsilon * current)
    return rows, total, res


def ls_fields(ss, vstruct, ops, volts, bounds, lut, rel_tols=None, driving=None, outputs=()):
    cap = _node_capacitance(ss)
    pins = {m.label: (ss.nodes[m.d], ss.nodes[m.g], ss.nodes[m.s]) for m in ss.circuit.mos}
    bound = {n: (lo, hi) for n, lo, hi in bounds}
    by_net = {d[0]: d for d in vstruct.directions}
    nodes = []
    for net in vstruct.pole_nets:
        if net not in by_net:
            continue                                   # 전류를 공급하는 셀 목록(S1v output_direction)이 없는 노드(꼬리·입력 넷 등)는 슬루 대상이 아니다
        _net, _topology, charge, discharge = by_net[net]
        c_rows, c_total, c_res = _direction(charge, CHARGE, pins, ops, volts, bound, lut, rel_tols)
        d_rows, d_total, d_res = _direction(discharge, DISCHARGE, pins, ops, volts, bound, lut, rel_tols)
        c = cap[net]
        nodes.append(LsNode(net, c, c_total, d_total, None if c_total is None or not c > 0 else c_total / c,
                            None if d_total is None or not c > 0 else d_total / c, c_rows + d_rows, c_res, d_res))
    margin = None
    if driving is not None and driving.load_peak_amp is not None:
        found = [min(n.i_charge_a, n.i_discharge_a) - driving.load_peak_amp for n in nodes
                 if n.net in outputs and n.i_charge_a is not None and n.i_discharge_a is not None]
        margin = min(found) if found else None
    return LsFields(tuple(nodes), margin)
