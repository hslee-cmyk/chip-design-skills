"""봉인 9 전도 여유 계산 블록 (오케스트레이터 결정 2026-10-08 '봉인한 동작점은 모델이 분해하는 점이어야 한다', sizing CONTRACT
6절 [r8]).

진입점: `dc_seal_conduction`(`@compute_block`) -- `dc_seal_conduction(snapshot, lut)`.

판정식: ID > 0 인 모든 MOS(전도 -- `intended_region` 과 무관)마다 I_off ≤ ε·ID.
* I_off = 그 소자 VGS = 0 누설 = lut `op_point(memo, kind, w_key, L, 0, vds, vsb).IDu · W/L`(그 소자 `dc_op` 의 L·VDS·VSB·W·
  w_key) -- SPICE 오라클 `off_current_A`(C23, pipeline `oracle_input` 이 내는 값)와 같은 양.
* ε = (gm/ID)·tol_V -- `dc_op.gm_id` 와 `device.dc_tol_v`(id_equivalent tol_V 셀). metrics 9절 ε_d(`lut_rel_tol`)와 같은 소자 자기
  전류 분해능(상대). tol_V 가 None 이면 그 행은 판정 불가(undefined).
* 행(N3.14 '위반 크기 / 허용오차', > 1 이면 위반): magnitude = I_off, tol = ε·ID -> margin = I_off/(ε·ID).
* writes `device.dc_off_current`(전도 MOS 마다 I_off, A) · `device.dc_conduction_floor`(전도 MOS 마다 ID 하한 I_off/ε, A, tol_V
  None 이면 None) -- search 가 θ 전류 상자·제약을 같은 식으로 조일 때 읽는 소자별 하한. ID ≤ 0 MOS 는 두 필드에 없다.
* VGS = 0 조회 실패는 소자 이름을 붙인 `SealViolationError`(reason `lut_query_failed`, device_query `off_current`).
"""
from gmid_engine.core import SealViolationError, compute_block
from gmid_engine.lut import op_point

from ._helpers_lut import with_device
from ._helpers_seal import judge
from .s2_values import DC_KEY, DC_SEAL_CONDUCTION_WRITER, SEAL_CONDUCTION

READS = (("device", "dc_op"), ("device", "dc_tol_v"))
WRITES = (("graph", "dc_seal_9"), ("device", "dc_off_current"), ("device", "dc_conduction_floor"))


def _off_current(lut, device, op):
    try:
        point = op_point(lut.memo, op.kind, op.w_key, op.L, 0.0, op.vds, op.vsb)
    except SealViolationError as exc:
        raise with_device(exc, device, "off_current") from exc
    return point.IDu * op.W / op.L


@compute_block(DC_SEAL_CONDUCTION_WRITER, reads=READS, writes=WRITES)
def dc_seal_conduction(projection):
    (lut,) = projection.extras
    tol_v = dict(projection.column("device", "dc_tol_v"))
    rows, offs, floors = [], {}, {}
    for m, op in sorted(projection.column("device", "dc_op")):
        if not op.current > 0:
            continue
        off = _off_current(lut, m, op)
        eps = None if tol_v.get(m) is None else op.gm_id * tol_v[m]
        offs[m] = off
        floors[m] = None if eps is None else off / eps
        rows.append((m, off, None if eps is None else eps * op.current, (m,), ()))
    return {("graph", "dc_seal_9"): {DC_KEY: judge(SEAL_CONDUCTION, rows)},
            ("device", "dc_off_current"): offs, ("device", "dc_conduction_floor"): floors}
