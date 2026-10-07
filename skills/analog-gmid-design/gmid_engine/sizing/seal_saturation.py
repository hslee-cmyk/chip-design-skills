"""봉인 7 포화 여유 계산 블록 (계획 N3.6 항목 7, DEC-88 (ii) (C), 설계 3.6, sizing CONTRACT 6절·12절 O1).

진입점: `dc_seal_saturation`(`@compute_block`) -- `dc_seal_saturation(snapshot, linear_devices, lut)`.

판정식: ID > 0 인 MOS(`intended_region: linear` 선언 소자 제외)마다 VDS − VDsat ≥ +tol_VDsat.
* VDsat = lut `vdsat(memo, kind, w_key, L, vgs, vds, vsb)`(LUT `VDSAT` 열 보간 -- 오라클 `@m[vdsat]` 과 같은 양, lut CONTRACT
  4.3), 조회점 = 그 소자 `dc_op` 의 (L, vgs, vds, vsb)(노드전압 차의 크기), w_key = `dc_op.w_key`.
* tol_VDsat = lut `tol_vdsat_table(memo, kind, w_key).at(L, vds)`(VDSAT 열 같은 방법 LOO 셀값, lut CONTRACT 5.2) -- None 이면
  그 행은 판정 불가(undefined, 통과로 바꾸지 않는다).
* 행 크기(N3.14 정규화 '위반 크기 / 허용오차', 클수록 나쁨·> 1 이면 위반): magnitude = VDsat − VDS + 2·tol_VDsat, tol =
  tol_VDsat -> margin = magnitude/tol = 1 − (VDS − VDsat − tol_VDsat)/tol_VDsat. 계획 N3.6 의 margin
  (VDS − VDsat − tol_VDsat)/tol_VDsat(양수 = 여유)은 1 − margin 이다(같은 식, 방향만 N3.14 에 맞춤). margin > 1 ⇔
  VDS − VDsat < tol_VDsat ⇔ 위반. detail `slack_v` = 대표 행의 VDS − VDsat − tol_VDsat(V).
* **VDSAT 열이 없는 LUT 세트**(옛 12-L 세트 등 -- lut `lut_column_unavailable`): 그 소자 행은 tol None(undefined)이고 detail
  reason = `lut_vdsat_column_missing` -- 2/(gm/ID) 로 대신하지 않는다(DEC-88). 열이 있으면 이 reason 은 나오지 않는다.
* 그 밖 LUT 실패(축 밖·L 위치)는 소자 이름을 붙인 `SealViolationError`(reason `lut_query_failed`, device_query `vdsat`·
  `tol_vdsat_cell`) -- 판정을 계속하지 않는다.
"""
import dataclasses

from gmid_engine.core import SealViolationError, compute_block
from gmid_engine.lut import tol_vdsat_table, vdsat

from ._helpers_lut import with_device
from ._helpers_seal import judge
from .s2_values import DC_KEY, DC_SEAL_SATURATION_WRITER, REASON_VDSAT_MISSING, SEAL_SATURATION

READS = (("device", "dc_op"),)
WRITES = (("graph", "dc_seal_7"),)
_COLUMN_UNAVAILABLE = "lut_column_unavailable"     # lut CONTRACT 4.3 열 출처 규칙 3


def _row(lut, device, op):
    """(대상, 크기, tol 또는 None, devices, nodes, 열 없음 여부)."""
    try:
        sat = vdsat(lut.memo, op.kind, op.w_key, op.L, op.vgs, op.vds, op.vsb)
    except SealViolationError as exc:
        if dict(exc.record.detail).get("reason") == _COLUMN_UNAVAILABLE:
            return (device, None, None, (device,), ()), True
        raise with_device(exc, device, "vdsat") from exc
    try:
        tol = tol_vdsat_table(lut.memo, op.kind, op.w_key).at(op.L, op.vds)
    except SealViolationError as exc:
        raise with_device(exc, device, "tol_vdsat_cell") from exc
    if tol is None:
        return (device, sat - op.vds, None, (device,), ()), False
    return (device, sat - op.vds + 2.0 * tol, tol, (device,), ()), False


@compute_block(DC_SEAL_SATURATION_WRITER, reads=READS, writes=WRITES)
def dc_seal_saturation(projection):
    linear_devices, lut = projection.extras
    rows = []
    missing = False
    for m, op in sorted(projection.column("device", "dc_op")):
        if op.current > 0 and m not in linear_devices:
            row, absent = _row(lut, m, op)
            rows.append(row)
            missing = missing or absent
    detail = (("reason", REASON_VDSAT_MISSING),) if missing else ()
    item = judge(SEAL_SATURATION, rows, detail)
    if item.tol is not None:
        item = dataclasses.replace(item, detail=tuple(sorted(item.detail + (("slack_v", 2.0 * item.tol - item.magnitude),))))
    return {("graph", "dc_seal_7"): {DC_KEY: item}}
