"""⑤ W·소자 동작점 계산 블록 (설계 3.2 4, DEC-88: W = ID·L/IDu, gm_id 는 파생 보고).

진입점: `dc_widths`(`@compute_block`) -- `dc_widths(snapshot, lut, w_request=())`.

* MOS 마다 VGS·VDS·VSB = 노드전압 차(크기, 저장 필드가 아니라 파생 -- `set_device_vds` 같은 쓰기 경로는 없다, N3.4),
  ID = `dc_current`, ln IDu = `dc_ln_idu`(쓰기 소자는 θ, 종속 소자는 순방향), W = ID·L/exp(ln IDu)(역산 없음),
  gm_id = 노드 전압 점의 순방향 LUT gm/ID(DEC-88 파생 보고), idu_forward = 같은 점의 순방향 IDu(봉인 2·3·8 입력 -- 순방향
  조회를 여기서 한 번만 한다).
* writes `device.dc_op`(DeviceOp).
* **W_request**(MOD8 루프, 계획 N3.17 LY3, 설계 40 §3.7): `w_request` = ((MOS, W(m)), ...) -- 그 소자의 W 는 계산 결과가 아니라 **고정 입력**이다
  (`DeviceOp.W` = 요청값). 쓰기 소자는 `size_and_seal` 이 좌표 ln IDu 를 ln(ID·L/W) 로 바꿔 `dc_columns` 에 넘기므로 여기서도
  ID·L/exp(ln IDu) = W 가 같은 양이다. 종속 소자(노드 VGS 순방향 좌표)는 KCL 전류가 정한 ID 와 요청 W 가 어긋날 수 있고 그 어긋남은
  봉인 3(순방향 IDu × W/L 로 다시 센 KCL 잔차)이 판정한다 -- 요청 폭에서의 전기 재검증이 이 경로의 목적이다(LY7).
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
    lut, *rest = projection.extras
    requested = dict(rest[0]) if rest else {}
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
        width = requested[m] if m in requested else currents[m] * lengths[m] / math.exp(ln_idu)
        ops[m] = DeviceOp(kind, currents[m], ln_idu, point.gm_over_id, lengths[m], width, vgs, vds, vsb, w_key_of(lut, kind),
                          point.IDu)
    return {("device", "dc_op"): ops}
