"""MOD7 폭 슬라이스별 보존량 실현 -- W_need(fw) = ID / J_slice(fw) (계획 N3.17 LY1, 사용자 결정 2026-10-07 Q4 (i)(iv)).

진입점: `slice_density(memo, device, keys) -> tuple[SliceDensity]`.

보존량은 (ID, gm/ID, L)이다. PDK 특성화 폭 슬라이스(폭 키)마다 MOD1 `lut` 공개 API 로만 조회한다(LUT 조회를 다시 구현하지 않는다):
* `vgs_for_gm_id(memo, kind, 키, gm/ID, L, VDS, VSB)` -> 그 슬라이스에서 목표 gm/ID 의 강반전 분지 VGS,
* `op_point(memo, kind, 키, L, VGS, VDS, VSB).IDu` -> 정규화 전류 IDu = ID·L/w_m, 그래서 전류 밀도 J = ID/W = IDu / L,
* W_need = ID_A / J,
* `tol_v_table(memo, kind, 키).at(L, VDS, "id_equivalent")` -> 그 슬라이스 셀의 tol_V(N3.6 ID 환산 지표, W 보존 소비자).
조회 결과는 `LutMemo` 가 캐시한다(같은 키는 다시 계산하지 않는다).

그 폭에서 목표 동작점이 실현되지 않으면(`SealViolationError`: 분지 안 gm/ID 근 없음·축 밖·L 앵커 아님) 그 폭은 후보가
아니다 -- 숫자 대신 사유를 남긴다(조용히 빼지 않는다). tol_V 셀이 정의되지 않은 폭(`at` 이 None)도 사유
`tol_v_undefined` 로 뺀다(허용오차 없이 후보 순위를 매길 수 없다).
"""
from gmid_engine.core import SealViolationError
from gmid_engine.lut import op_point, tol_v_table, vgs_for_gm_id

from .contract_output import SliceDensity

_TOL_METRIC = "id_equivalent"
_TOL_UNDEFINED = "tol_v_undefined"


def _one(memo, device, key, finger_w_m):
    try:
        vgs = vgs_for_gm_id(memo, device.kind, key, device.gm_id, device.L_m, device.vds_V, device.vsb_V)
        op = op_point(memo, device.kind, key, device.L_m, vgs, device.vds_V, device.vsb_V)
        tol = tol_v_table(memo, device.kind, key).at(device.L_m, device.vds_V, _TOL_METRIC)
    except SealViolationError as exc:
        return SliceDensity(key, finger_w_m, None, None, None, None, dict(exc.record.detail)["reason"])
    if tol is None:
        return SliceDensity(key, finger_w_m, vgs, None, None, None, _TOL_UNDEFINED)
    density = op.IDu / device.L_m
    return SliceDensity(key, finger_w_m, vgs, density, device.ID_A / density, float(tol), "")


def slice_density(memo, device, keys):
    """`device`(`LayoutDevice`)의 보존량을 폭 키 `keys`(오름차순) 슬라이스마다 실현한 `SliceDensity` tuple(같은 순서).
    finger_w = 키 x LUT 제조 격자(`memo.lut.spec.manufacturing_grid_m`)."""
    grid = memo.lut.spec.manufacturing_grid_m
    return tuple(_one(memo, device, key, key * grid) for key in keys)
