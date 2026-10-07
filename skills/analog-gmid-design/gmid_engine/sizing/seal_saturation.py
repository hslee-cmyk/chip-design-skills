"""봉인 7 포화 여유 계산 블록 (계획 N3.6 항목 7, DEC-88 (ii) (C), 설계 3.6).

진입점: `dc_seal_saturation`(`@compute_block`) -- `dc_seal_saturation(snapshot, linear_devices)`.

판정식: ID > 0 인 MOS(`intended_region: linear` 선언 소자 제외)에서 VDS − VDsat ≥ +tol_VDsat. VDsat = LUT `VDSAT` 열 보간,
tol_VDsat = VDSAT 열 leave-one-out 셀값(DEC-88). **master lut(r3)에는 VDSAT 열·`vdsat` 조회가 없다**(lut CONTRACT 8절,
U-27 재생성 대기) -> 계획대로 이 항목을 '정의 미확정'(undefined, reason `lut_vdsat_column_missing`)으로 기록하고
2/(gm/ID) 로 대신하지 않는다. 대상 소자 목록은 남긴다(열이 생기면 같은 대상에 판정식을 건다).
"""
from gmid_engine.core import compute_block

from .s2_values import DC_KEY, DC_SEAL_SATURATION_WRITER, REASON_VDSAT_MISSING, SEAL_SATURATION, SEAL_UNDEFINED, SealItem

READS = (("device", "dc_op"),)
WRITES = (("graph", "dc_seal_7"),)


@compute_block(DC_SEAL_SATURATION_WRITER, reads=READS, writes=WRITES)
def dc_seal_saturation(projection):
    (linear_devices,) = projection.extras
    targets = tuple(sorted(m for m, op in projection.column("device", "dc_op")
                           if op.current > 0 and m not in linear_devices))
    item = SealItem(SEAL_SATURATION, SEAL_UNDEFINED, None, None, None, targets, (),
                    (("n_checked", len(targets)), ("reason", REASON_VDSAT_MISSING)))
    return {("graph", "dc_seal_7"): {DC_KEY: item}}
