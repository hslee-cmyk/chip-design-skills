"""봉인 DC 점 -> MOS 소신호 값 계산 블록 (설계 design_mod1_lut_mod5_mna 3.2 `ss_linearize`, 7a design 4.5 단계 5,
계획 N3.8 gmb·DF-28, DEC-91).

진입점: `ss_dev`(`@compute_block`) -- `ss_dev(snapshot, lut, junction)`.

* reads `device.dc_op`(GB7 `DeviceOp` -- kind·ID·gm/ID·L·W·VGS·VDS·VSB 크기·폭 키), extras `(lut, junction)`(sizing `LutAccess`,
  metrics `JunctionSource` -- 접합 파라미터·LUT 생성 규칙 선언·온도·PDK 선언 sha256 이 블록 입력 버전에 든다), [NFR-5]
  `device.dc_tol_v`(sizing `dc_tolerances` 가 쓴 그 소자의 tol_V(id_equivalent) 셀 -- 봉인 2 와 같은 값, LUT 다시 조회 안 함),
  `device.dc_gm`(같은 블록이 쓴 자기 동작점 gm = ID × LUT gm/ID -- ss 의 gm 은 이 필드 하나, 설계 40 §3.7-3).
  writes `device.ss_dev` = `SsDevice`(MOS 마다).
* [NFR-5] `lut_rel_tol` = `dc_op.gm_id · dc_tol_v`(무차원, metrics CONTRACT 9.1) -- tol_V(id_equivalent) = |Δln ID| / (gm/ID) 의 정의를
  되돌린 LUT 전류의 상대 불확실성. `dc_tol_v` 가 None 이거나 없으면 None(분해능 미정).
* 소자마다 같은 동작점의 LUT 조회 세 가지(모두 LUT memo point 영역 -- `op_point` 는 `dc_widths` 가 같은 키로 이미 불러
  적중이다): gm = `dc_gm`(dc 단계 필드를 읽는다 -- 다시 계산하지 않는다), gds = `op_point(...).gds_per_w`·W, gmb = lut `gmb(...)`·W/w_m,
  용량 = lut `caps(..., W)`(cgg·cgd·cgs·cgb·모형). [lut r6] `gmb` 는 GMBS 열이 있으면 열 정의(정본, lut CONTRACT 4.4), 없으면
  r5 VS 칸 할선 -- 어느 쪽인지 `gmb_model` 에 적는다(열 출처 규칙 4.3 과 같은 판정: 그 폭 슬라이스 열, 아니면 같은 폭 키의
  기준 LUT 열). 용량은 LUT v2 의 CGS·CGB 열(모형 `lut_cgs_cgb`, 부호 보존 값 그대로).
* 접합 용량 cdb·csb(DEC-91): PDK 접합 파라미터(`junction.params_of(kind)`) + 봉인점 역바이어스(v_db = VDS + VSB, v_sb = VSB)
  + 확산 기하로 `junction_caps`(metrics CONTRACT 8절). S2 에는 아직 레이아웃 기하(MOD7 `ly.diffusion`)가 없으므로 기하는 레이아웃 전
  첫 사이징점 규칙 = LUT 생성 규칙(finger_w = 폭 슬라이스 w_m, m = W / w_m) -- `junction_model` = `JUNCTION_LUT_RULE`(metric 묶음의
  `approximations` 로 매 결과에 실린다). [U14] 레이아웃 뒤(MOD8 재검증)에는 추가 extra `diffusion` = ((MOS, `DiffusionGeometry`), ...)(MOD7
  `ly.diffusion` 실현 기하: finger_w·ad·as·pd·ps·m = n_fingers)가 그 소자의 규칙 기하를 대체하고 `junction_model` = `JUNCTION_LAYOUT_DIFFUSION`.
  extra 가 없거나 비면 입력 버전이 종래와 같다.
* **`off` 선언 소자**(EO-1 범위 4, A-2): 추가 인자 `off_items` = ((소자, kind, `OffOp`, `RegionDecl`), ...) (`ss_evaluate` 가 `device.off_op`·`device.kind`·`device.region_decl` 필드에서 꺼내 넘긴다 --
  없으면 생략, 입력 버전 불변)로 그 소자의 `SsDevice` 도 낸다: gm·gmb·gds·용량 모두 `off_op` 점의 LUT 값(다른 MOS 와 같은 열 규칙, `w_m` = 소자 폭 W·`l_m` = 길이 L 환산).
  DC 전류는 0 모형이라 `dc_op`·`dc_gm` 필드가 없고 gm = (gm/ID)·`off_current`(ΔI_off = IDu·W/L, `ss_off_delta` 가 부르는 같은 함수). `lut_rel_tol` 은 None(tol_V 셀이 없다).
  extras 순서: `(lut, junction[, diffusion[, off_items]])` -- off 소자가 있으면 `diffusion` 자리를 (비었어도) 채운다.
* `gmb_model` = `GMB_COLUMN`(GMBS 열) 또는 `GMB_VS_CELL_SECANT`(열 없는 옛 LUT -- 임시 근사, 설계 2.8).
* 접합 용량 정본이 PDK 파라미터라 LUT v2 의 CDD·CSS 열(`Caps.cdd`·`css`)은 쓰지 않는다(DEC-91 '대조 test 전용').
* LUT 실패(용량 VS 축 0~0.8 V 밖 등)는 소자 이름을 붙인 `SealViolationError`(reason `lut_query_failed`, `lut_reason` = 원래
  사유, `device_query`) -- 근사·클램프하지 않는다(설계 2.4 '실패로 기록').
"""
import types

from gmid_engine.core import SealViolationError, compute_block
from gmid_engine.lut import caps, gmb, op_point
from gmid_engine.sizing import REASON_LUT_QUERY, SS_DEV_WRITER

from .junction_cap import junction_caps
from .ss_types import SsDevice

READS = (("device", "dc_op"), ("device", "dc_tol_v"), ("device", "dc_gm"))
WRITES = (("device", "ss_dev"),)
GMB_COLUMN = "lut_gmbs_column"                        # lut gmb: GMBS 열(정본, lut CONTRACT r6 4.4)
GMB_VS_CELL_SECANT = "lut_vs_cell_secant"              # lut gmb: VS 선형 칸 할선(GMBS 열 없는 옛 LUT, 설계 MOD1 2.8 임시)
GMBS_COLUMN = "GMBS_PER_ID"                            # lut DERIVED_COLUMNS 의 gmb 열 이름(4.4 가 읽는 열)
JUNCTION_LUT_RULE = "pdk_bsim4_lut_rule_diffusion"     # DEC-91 접합 용량: PDK BSIM4 파라미터 + LUT 생성 규칙 확산 기하(레이아웃 전)
JUNCTION_LAYOUT_DIFFUSION = "pdk_bsim4_layout_diffusion"   # [U14] DEC-91 (2)·LY8: PDK BSIM4 파라미터 + MOD7 `ly.diffusion` 실현 확산 기하(레이아웃 뒤)


def _query(device, name, call):
    try:
        return call()
    except SealViolationError as exc:
        detail = dict(exc.record.detail)
        detail.update({"device_query": name, "lut_reason": detail.get("reason"), "reason": REASON_LUT_QUERY})
        raise SealViolationError(devices=(device,), margin=exc.record.margin, detail=detail) from exc


def _gmb_model(table, kind, w_key):
    if GMBS_COLUMN in table.slice_map[(kind, w_key)].columns:
        return GMB_COLUMN
    cap = table.cap_map.get(kind)
    return GMB_COLUMN if cap is not None and cap.w_key == w_key and GMBS_COLUMN in cap.columns else GMB_VS_CELL_SECANT


def off_current(point, width, length):
    """`off` 소자의 ΔI_off = IDu·W/L(A) -- `OpPoint` 하나와 소자 폭 W·길이 L(선언 `w_m`·`l_m`)에서. `ss_dev`(gm)와 `ss_off_delta`(주입)가 부르는 식 하나."""
    return point.IDu * width / length


def _linearize(lut, junction, device, op, gm, rel_tol, realized):
    """op = kind·w_key·L·W·vgs·vds·vsb 를 가진 점(`DeviceOp` 또는 off 소자의 읽기 전용 view). gm None 이면 off 소자: (gm/ID)·ΔI_off."""
    memo = lut.memo
    w_m = memo.lut.slice_map[(op.kind, op.w_key)].w_m
    args = (op.L, op.vgs, op.vds, op.vsb)
    point = _query(device, "op_point", lambda: op_point(memo, op.kind, op.w_key, *args))
    body = _query(device, "gmb", lambda: gmb(memo, op.kind, op.w_key, *args))
    cap = _query(device, "caps", lambda: caps(memo, op.kind, *args, op.W))
    geometry = junction.pre_layout_geometry(w_m, op.W / w_m) if realized is None else realized
    jc = junction_caps(junction.params_of(op.kind), geometry, op.vds + op.vsb, op.vsb, junction.temp_c)
    if gm is None:
        gm = point.gm_over_id * off_current(point, op.W, op.L)
    return SsDevice(
        gm=gm, gmb=body * op.W / w_m, gds=point.gds_per_w * op.W,
        cgg=cap.cgg, cgs=cap.cgs, cgd=cap.cgd, cgb=cap.cgb, cdb=jc.cdb, csb=jc.csb,
        cap_model=cap.model, gmb_model=_gmb_model(memo.lut, op.kind, op.w_key), junction_model=JUNCTION_LUT_RULE if realized is None else JUNCTION_LAYOUT_DIFFUSION,
        lut_rel_tol=rel_tol,
    )


@compute_block(SS_DEV_WRITER, reads=READS, writes=WRITES)
def ss_dev(projection):
    lut, junction, *rest = projection.extras
    tols = dict(projection.column("device", "dc_tol_v"))
    gm = dict(projection.column("device", "dc_gm"))
    realized = dict(rest[0]) if rest else {}                 # [U14] 실현 확산 기하 ((MOS, DiffusionGeometry), ...) -- 없으면 LUT 생성 규칙 기하
    out = {m: _linearize(lut, junction, m, op, gm[m], None if tols.get(m) is None else op.gm_id * tols[m], realized.get(m))
           for m, op in projection.column("device", "dc_op")}
    off_items = rest[1] if len(rest) > 1 else ()
    for m, kind, point, decl in off_items:      # `off` 선언 소자 -- 점 = `off_op`, 폭·길이 = 선언 (tol_V 셀 없음 -> lut_rel_tol None)
        view = types.SimpleNamespace(kind=kind, w_key=point.w_key, L=decl.l_m, W=decl.w_m, vgs=point.vgs, vds=point.vds, vsb=point.vsb)
        out[m] = _linearize(lut, junction, m, view, None, None, realized.get(m))
    return {("device", "ss_dev"): out}
