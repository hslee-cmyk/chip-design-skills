"""봉인 허용오차 계산 블록 -- 소자별 tol_V 셀과 첫 평가 gm 상계 (계획 N3.6 허용오차 식, DEC-32·DEC-87·DEC-88, 설계 3.5).

진입점: `dc_tolerances`(`@compute_block`) -- `dc_tolerances(snapshot, lut)`.

* `device.dc_tol_v` = (kind, w_key, L 앵커, VDS) 셀의 id_equivalent tol_V(V) 또는 None(셀 미정의) -- 봉인 1·2·3·6·8 이 쓴다
  (봉인 2·3·SCC 수렴 = ID 환산 지표, DEC-88. 봉인 1·6·8 의 지표 배정은 N3.6 기본안 '그 전압을 만든 LUT 조회 종류' --
  노드전압을 만든 것이 ln IDu 좌표 역산이므로 같은 id_equivalent).
* `device.dc_gm_bound` = 그 소자 (L, VDS, VSB) 곡선 VGS 격자 위 gm 최댓값 × W/w_m -- tol_I 의 gm(N3.6: 첫 평가는 LUT 격자
  최댓값. 직전 봉인 스냅샷의 `ss` gm 은 `ss` 블록이 생기면 바꾼다).
"""
from gmid_engine.core import SealViolationError, compute_block
from gmid_engine.lut import gm_id_curve

from ._helpers_lut import tol_v_cell, w_key_of, with_device
from .s2_values import DC_TOLERANCES_WRITER

READS = (("device", "dc_op"),)
WRITES = (("device", "dc_tol_v"), ("device", "dc_gm_bound"))


def _gm_grid_max(lut, device, op):
    """(L, VDS, VSB) 곡선의 VGS 격자 위 gm 최댓값을 소자 폭 W 로 환산(S)."""
    w_key = w_key_of(lut, op.kind)
    w_m = lut.memo.lut.slice_map[(op.kind, w_key)].w_m
    try:
        curve = gm_id_curve(lut.memo, op.kind, w_key, op.L, op.vds, op.vsb)
    except SealViolationError as exc:
        raise with_device(exc, device, "gm_grid_max") from exc
    return float((curve.id_vals * curve.gm_id_vals).max()) * op.W / w_m


@compute_block(DC_TOLERANCES_WRITER, reads=READS, writes=WRITES)
def dc_tolerances(projection):
    (lut,) = projection.extras
    tols = {}
    bounds = {}
    for m, op in projection.column("device", "dc_op"):
        tols[m] = tol_v_cell(lut, m, op.kind, op.L, op.vds)
        bounds[m] = _gm_grid_max(lut, m, op)
    return {("device", "dc_tol_v"): tols, ("device", "dc_gm_bound"): bounds}
