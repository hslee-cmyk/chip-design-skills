"""off 소자 전류 효과의 1차 노드 전압 변화 계산 블록 (EO-1 범위 4, 설계 41 §4.8-8, 계획 O-221·O-222, A-2).

진입점: `ss_off_delta`(`@compute_block`, writer `ss_off_delta`) -- `ss_off_delta(snapshot, lut, *, donors, counters)`. off 선언이 없으면 부르지 않는다(`ss_evaluate`).
reads `device.{off_op, region_decl, kind, pins}`, `graph.{ss_circuit, ss_nodal}`; writes `graph.ss_off_delta`(key `METRICS_KEY`) = `OffDelta(node_dv, sources)`.

* ΔI_off(소자) = `off_current(op_point(kind, w_key, L = l_m, off_op 점), w_m, l_m)` = IDu·w_m/l_m. 주입(노드로 들어가는 전류, p = nmos +1 / pmos −1): drain −p·ΔI, source +p·ΔI.
  고정 넷(교류접지 ∪ 입력) 주입은 ΔV 를 만들지 않는다(그 노드는 전압 고정).
* **G·ΔV = 주입**: G = `graph.ss_nodal` 의 컨덕턴스(off 소자 스탬프 포함 -- `ss_dev` 가 `off_op` 점 LUT 값으로 넣었다)이고 풀이는 그 인수분해 위의 `nodal_solve` 한 번이다. 조립·인수분해를
  다시 하지 않는다. `node_dv` = 풀린 노드(미지수)의 ((넷, ΔV), ...) 넷 이름순.
* 정지 `off_delta_undefined`(E-0, `SealViolationError`): `graph.ss_nodal` 이 `Undefined`, 인수분해가 특이(`lu` None), 또는 주입 넷이 고정 아닌 floating 노드.
"""
from gmid_engine.core import SealViolationError, compute_block
from gmid_engine.graph import MOS_TERMINAL_NAMES
from gmid_engine.lut import op_point
from gmid_engine.sizing import METRICS_KEY, SS_OFF_DELTA_WRITER, terminal_voltages

from ._helpers_nodal import nodal_solve
from .mna_types import Undefined
from .ss_linearize import off_current
from .ss_types import OffDelta

READS = (("device", "off_op"), ("device", "region_decl"), ("device", "kind"), ("device", "pins"),
         ("graph", "ss_circuit"), ("graph", "ss_nodal"))
WRITES = (("graph", "ss_off_delta"),)
REASON_UNDEFINED = "off_delta_undefined"


def _undefined(devices, why):
    return SealViolationError(devices=tuple(sorted(devices)), detail={"reason": REASON_UNDEFINED, "why": why})


@compute_block(SS_OFF_DELTA_WRITER, reads=READS, writes=WRITES)
def ss_off_delta(projection):
    (lut,) = projection.extras
    nodal = projection.value("graph", METRICS_KEY, "ss_nodal")
    kinds = dict(projection.column("device", "kind"))
    pins = dict(projection.column("device", "pins"))
    decl = dict(projection.column("device", "region_decl"))
    ops = dict(projection.column("device", "off_op"))
    names = tuple(sorted(ops))
    if isinstance(nodal, Undefined):
        raise _undefined(names, "ss_nodal_undefined")
    index = {net: i for i, net in enumerate(nodal.nodes)}
    injection, sources = {}, {}
    for m in names:
        op = ops[m]
        point = op_point(lut.memo, kinds[m], op.w_key, decl[m].l_m, op.vgs, op.vds, op.vsb)
        delta = off_current(point, decl[m].w_m, decl[m].l_m)
        sign = terminal_voltages(kinds[m], 0.0, 1.0, 0.0, 0.0)[0]                # nmos +1, pmos −1 (부호 정의 하나)
        drain, _gate, source = (dict(pins[m])[t] for t in MOS_TERMINAL_NAMES)
        injection[index[drain]] = injection.get(index[drain], 0.0) - sign * delta
        injection[index[source]] = injection.get(index[source], 0.0) + sign * delta
        sources[m] = delta
    unknown, lu, _piv, _coupling, floating, charge = nodal.factor
    if unknown.size and lu is None:
        raise _undefined(names, "singular")
    stuck = sorted(nodal.nodes[i] for i in injection if i in floating or i in charge)      # 전도 경로 없는 용량 전용 노드(전하 노드 포함)에는 직류 전류가 쌓여 극한이 없다
    if stuck:
        raise _undefined(names, "floating_injection_net:" + ",".join(stuck))
    volt, _residual = nodal_solve(nodal.factor, len(nodal.nodes), None, injection)
    node_dv = tuple(sorted((nodal.nodes[int(i)], float(volt[int(i)])) for i in unknown))
    return {("graph", "ss_off_delta"): {METRICS_KEY: OffDelta(node_dv, tuple((m, sources[m]) for m in names))}}
