"""봉인 DC 점 -> MOS 소신호 값 계산 블록 (설계 design_mod1_lut_mod5_mna 3.2 `ss_linearize`, 7a design 4.5 단계 5,
계획 N3.8 gmb·DF-28, DEC-91).

진입점: `ss_dev`(`@compute_block`) -- `ss_dev(snapshot, lut)`.

* reads `device.dc_op`(GB7 `DeviceOp` -- kind·ID·gm/ID·L·W·VGS·VDS·VSB 크기·폭 키), extras `(lut,)`(sizing `LutAccess`).
  writes `device.ss_dev` = `SsDevice`(MOS 마다).
* 소자마다 같은 동작점의 LUT 조회 세 가지(모두 LUT memo point 영역 -- `op_point` 는 `dc_widths` 가 같은 키로 이미 불러
  적중이다): gm = ID·(gm/ID)(`DeviceOp.gm_id`, dc 정의값), gds = `op_point(...).gds_per_w`·W, gmb = lut `gmb(...)`·W/w_m,
  용량 = lut `caps(..., W)`(cgg·cgd·cgs·cgb·모형).
* 접합 용량 cdb·csb(DEC-91): 정본은 PDK 접합 파라미터(CJ·CJSW·MJ·MJSW·PB) + 봉인점 역바이어스 + 확산 기하다. PDK 선언
  (`core.read_pdk_decl`)에 그 양이 없고 lut r5 에 CDD·CSS 열도 없어 **값 0 + `junction_model` = `JUNCTION_PENDING`** 으로
  적는다(값을 지어내지 않는다 -- metric 묶음의 `approximations` 로 매 결과에 실린다).
* gmb 는 lut r5 의 VS 칸 할선(GMBS 열 전 임시, 설계 2.8) -- `gmb_model` = `GMB_VS_CELL_SECANT`.
* LUT 실패(용량 VS 축 0~0.8 V 밖 등)는 소자 이름을 붙인 `SealViolationError`(reason `lut_query_failed`, `lut_reason` = 원래
  사유, `device_query`) -- 근사·클램프하지 않는다(설계 2.4 '실패로 기록').
"""
from gmid_engine.core import SealViolationError, compute_block
from gmid_engine.lut import caps, gmb, op_point
from gmid_engine.sizing import REASON_LUT_QUERY, SS_DEV_WRITER

from .ss_types import SsDevice

READS = (("device", "dc_op"),)
WRITES = (("device", "ss_dev"),)
GMB_VS_CELL_SECANT = "lut_vs_cell_secant"              # lut gmb: VS 선형 칸 할선(GMBS 열 전 임시, 설계 MOD1 2.8)
JUNCTION_PENDING = "pending_pdk_junction_params"       # DEC-91 접합 용량: PDK 접합 파라미터 선언 대기 -> cdb = csb = 0


def _query(device, name, call):
    try:
        return call()
    except SealViolationError as exc:
        detail = dict(exc.record.detail)
        detail.update({"device_query": name, "lut_reason": detail.get("reason"), "reason": REASON_LUT_QUERY})
        raise SealViolationError(devices=(device,), margin=exc.record.margin, detail=detail) from exc


def _linearize(lut, device, op):
    memo = lut.memo
    w_m = memo.lut.slice_map[(op.kind, op.w_key)].w_m
    args = (op.L, op.vgs, op.vds, op.vsb)
    point = _query(device, "op_point", lambda: op_point(memo, op.kind, op.w_key, *args))
    body = _query(device, "gmb", lambda: gmb(memo, op.kind, op.w_key, *args))
    cap = _query(device, "caps", lambda: caps(memo, op.kind, *args, op.W))
    return SsDevice(
        gm=op.gm_id * op.current, gmb=body * op.W / w_m, gds=point.gds_per_w * op.W,
        cgg=cap.cgg, cgs=cap.cgs, cgd=cap.cgd, cgb=cap.cgb, cdb=0.0, csb=0.0,
        cap_model=cap.model, gmb_model=GMB_VS_CELL_SECANT, junction_model=JUNCTION_PENDING,
    )


@compute_block(SS_DEV_WRITER, reads=READS, writes=WRITES)
def ss_dev(projection):
    (lut,) = projection.extras
    return {("device", "ss_dev"): {m: _linearize(lut, m, op) for m, op in projection.column("device", "dc_op")}}
