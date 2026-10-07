"""⑤ W·소자 동작점 계산 블록 (설계 3.2 4, DEC-88: W = ID·L/IDu, gm_id 는 파생 보고).

진입점: `dc_widths`(`@compute_block`) -- `dc_widths(snapshot, lut)`.

* MOS 마다 VGS·VDS·VSB = 노드전압 차(크기, 저장 필드가 아니라 파생 -- `set_device_vds` 같은 쓰기 경로는 없다, N3.4),
  ID = `dc_current`, ln IDu = `dc_ln_idu`(쓰기 소자는 θ, 종속 소자는 순방향), W = ID·L/exp(ln IDu)(역산 없음),
  gm_id = 노드 전압 점의 순방향 LUT gm/ID(DEC-88 파생 보고), idu_forward = 같은 점의 순방향 IDu(봉인 2·3·8 입력 -- 순방향
  조회를 여기서 한 번만 한다).
* writes `device.dc_op`(DeviceOp). W_request 로 W 가 고정된 소자(MOD8 루프, 설계 3.2 4 의 반대 방향)는 이 범위 밖이다.
"""
import math

from gmid_engine.core import compute_block
from gmid_engine.graph import MOS_TERMINAL_NAMES

from ._helpers_lut import forward_point, terminal_voltages, w_key_of
from .s2_values import DC_WIDTHS_WRITER, DeviceOp

READS = (
    ("node", "dc_v"), ("node", "dc_rail_v"), ("device", "dc_current"), ("device", "dc_L"), ("device", "dc_ln_idu"),
    ("device", "pins"), ("device", "kind"), ("device", "bulk"),
)
WRITES = (("device", "dc_op"),)


@compute_block(DC_WIDTHS_WRITER, reads=READS, writes=WRITES)
def dc_widths(projection):
    (lut,) = projection.extras
    values = dict(projection.column("node", "dc_rail_v"))
    values.update(projection.column("node", "dc_v"))
    pins = dict(projection.column("device", "pins"))
    kinds = dict(projection.column("device", "kind"))
    bulk = dict(projection.column("device", "bulk"))
    lengths = dict(projection.column("device", "dc_L"))
    currents = dict(projection.column("device", "dc_current"))
    ops = {}
    for m, ln_idu in projection.column("device", "dc_ln_idu"):
        d, g, s = (dict(pins[m])[t] for t in MOS_TERMINAL_NAMES)
        kind = kinds[m]
        vgs, vds, vsb = terminal_voltages(kind, values[d], values[g], values[s], values[bulk[m].net])
        point = forward_point(lut, m, kind, lengths[m], vgs, vds, vsb)
        width = currents[m] * lengths[m] / math.exp(ln_idu)
        ops[m] = DeviceOp(kind, currents[m], ln_idu, point.gm_over_id, lengths[m], width, vgs, vds, vsb, w_key_of(lut, kind),
                          point.IDu)
    return {("device", "dc_op"): ops}
