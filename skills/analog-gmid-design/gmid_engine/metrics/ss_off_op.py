"""`off` 선언 소자의 동작점 계산 블록 (EO-1 범위 4, 설계 41 §4.8-8·§4.8-10, 계획 O-221·O-222, A-47).

진입점: `ss_off_op`(`@compute_block`, writer `ss_off_op`) -- `ss_off_op(snapshot, lut, *, donors, counters)`. off 선언이 하나도 없으면 부르지 않는다(`ss_evaluate`).
reads `device.{region_decl, kind, pins, bulk}`, `node.{dc_v, dc_rail_v}`; writes `device.off_op` = `OffOp(vgs, vds, vsb, w_key)`(off 선언 소자만, kind·W·L 칸 없음).

* 식(p = +1 nmos, −1 pmos -- sizing `terminal_voltages` 의 부호 정의): vgs = p(Vg − Vs), vds = p(Vd − Vs), vsb = p(Vs − Vb). `w_key` = 선언 폭 `w_m` 이 가리키는 LUT 슬라이스 키(`lut.slice_of_finger`, WB-1 A-64 -- 선언 폭이 슬라이스 폭이어야 한다).
* 정지(E-0, 후보 실패 `SealViolationError`, 표 순서대로 첫 맞는 행, 해당 소자 전부 `exc.record.devices`):
  1. `off_vgs_negative`: vgs < 0 인 off 소자 하나 이상(꺼짐은 VGS ≥ 0 의 LUT 점이다).
  2. `off_bulk_forward`: `junction_forward(vds, vsb)` > 0(봉인 6 과 같은 식 하나, 경계 0 V, tol 입력 없음, LUT 조회 전).
  3. `slice_missing`: 선언 폭 `w_m` 이 슬라이스 폭이 아님(`slice_of_finger`, LUT 값 조회 0; 소자 = devices).
  4. `off_outside_lut`: 그 밖에 그 점이 LUT 밖(L = `l_m` 위치·축 밖; vds < 0 이고 vdb ≥ 0 인 점 포함). 클램프하지 않는다.
* 위 판정은 ΔI 를 계산하지 않는다(`ss_off_delta` 는 부르지 않는다).
"""
from gmid_engine.authoring import REGION_OFF
from gmid_engine.core import SealViolationError, compute_block
from gmid_engine.lut import lut_axis_bounds, op_point, slice_of_finger
from gmid_engine.graph import MOS_TERMINAL_NAMES
from gmid_engine.sizing import SS_OFF_OP_WRITER, junction_forward, terminal_voltages

from .ss_types import OffOp

READS = (("device", "region_decl"), ("device", "kind"), ("device", "pins"), ("device", "bulk"),
         ("node", "dc_v"), ("node", "dc_rail_v"))
WRITES = (("device", "off_op"),)
REASON_VGS_NEGATIVE = "off_vgs_negative"
REASON_BULK_FORWARD = "off_bulk_forward"
REASON_OUTSIDE_LUT = "off_outside_lut"


def _stop(reason, devices, **detail):
    return SealViolationError(devices=tuple(sorted(devices)), detail={"reason": reason, **detail})


@compute_block(SS_OFF_OP_WRITER, reads=READS, writes=WRITES)
def ss_off_op(projection):
    (lut,) = projection.extras
    kinds = dict(projection.column("device", "kind"))
    pins = dict(projection.column("device", "pins"))
    bulk = {m: b.net for m, b in projection.column("device", "bulk")}
    volts = dict(projection.column("node", "dc_rail_v"))
    volts.update(projection.column("node", "dc_v"))
    decl = dict(projection.column("device", "region_decl"))
    points = {}
    for m in sorted(m for m, r in decl.items() if r.region == REGION_OFF):
        d, g, s = (dict(pins[m])[t] for t in MOS_TERMINAL_NAMES)
        points[m] = terminal_voltages(kinds[m], volts[d], volts[g], volts[s], volts[bulk[m]])      # (vgs, vds, vsb)
    negative = [m for m, (vgs, _vds, _vsb) in points.items() if vgs < 0]
    if negative:
        raise _stop(REASON_VGS_NEGATIVE, negative, vgs=tuple((m, points[m][0]) for m in sorted(negative)))
    forward = {m: junction_forward(vds, vsb) for m, (_vgs, vds, vsb) in points.items()}      # 봉인 6 과 같은 식 하나
    if any(v > 0 for v in forward.values()):
        raise _stop(REASON_BULK_FORWARD, [m for m, v in forward.items() if v > 0], forward_v=tuple((m, v) for m, v in sorted(forward.items()) if v > 0))
    keys = {}
    for m in sorted(points):        # 3. 선언 폭이 슬라이스 폭이 아니면 slice_missing (LUT 값 조회 없음, 소자 이름을 채운다)
        try:
            keys[m] = slice_of_finger(lut.memo.lut, kinds[m], decl[m].l_m, decl[m].w_m)
        except SealViolationError as exc:
            raise SealViolationError(devices=(m,), margin=exc.record.margin, detail=dict(exc.record.detail)) from exc
    out = {}
    outside = []
    for m, (vgs, vds, vsb) in points.items():
        bounds = {name: (lo, hi) for name, lo, hi in lut_axis_bounds(lut.memo, kinds[m], keys[m])}      # 축 끝만 읽는다
        if any(not lo <= v <= hi for v, (lo, hi) in zip((vgs, vds, vsb), (bounds["VGS"], bounds["VDS"], bounds["VS"]))):
            outside.append(m)
            continue
        try:
            op_point(lut.memo, kinds[m], keys[m], decl[m].l_m, vgs, vds, vsb)          # L 위치까지 LUT 안 점인가 -- 안이면 memo 에 남아 `ss_dev`·`ss_off_delta` 가 적중한다
        except SealViolationError:
            outside.append(m)
            continue
        out[m] = OffOp(vgs, vds, vsb, keys[m])
    if outside:
        raise _stop(REASON_OUTSIDE_LUT, outside, point=tuple((m, points[m]) for m in sorted(outside)))
    return {("device", "off_op"): out}
