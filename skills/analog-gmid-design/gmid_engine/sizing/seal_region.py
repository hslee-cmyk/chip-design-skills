"""봉인 7·9 영역 판정 계산 블록 -- 소자마다 공용 영역 판정 한 번 (EO-1 범위 4, 설계 41 §4.8-2, 계획 N3.6 표 7·9행, O-202·O-204·O-205).

진입점: `dc_seal_region`(`@compute_block`) -- `dc_seal_region(snapshot, lut)`. reads `device.dc_op`, `device.dc_sat_v`, `device.region_decl`. writes `graph.dc_seal_7`, `graph.dc_seal_9`.

`device.dc_op` 의 MOS 마다 `judge_region(device, declared, current, vds, vdsat)` 을 **한 번** 부르고(선언 = `device.region_decl` 의 region, 없으면 None) 그 결과 하나에서
두 항목의 status 를 정한다. 수치 문턱이 없다 -- 전도 = ID > 0, 포화 = VDS ≥ VDSAT(경계 0 V·등호).
* vdsat 입력 = 필드 `device.dc_sat_v`(`lut.SatBound`, writer `dc_widths`)에서 읽는다 -- **LUT VDSAT·tol 조회 0**(둘째 생산자 없음): 수 -> 그 수, 사유 `reverse_vds`·`vdsat_column_unavailable`·
  `off_declared` -> `None`(표 행 3·4 는 vdsat 값을 안 보고 `reverse_vds` 는 VDS < 0 행이며, 열 없음 = 행 6 `unresolved`), 사유 `lut_domain` -> `OUT_OF_DOMAIN`.
* 봉인 9: `cutoff` ≥ 1 이면 fail(devices = 그 소자), 아니고 `out_of_domain` ≥ 1 이면 undefined(devices = 그 소자, reason `out_of_domain`), 아니면 pass.
* 봉인 7: 표 행 3·8·10(거부 판정 `region_mismatch` 중 triode/saturation 쪽) ≥ 1 이면 fail, 아니고 행 6(`unresolved`, VDSAT 열 없음) ≥ 1 이면 undefined(reason
  `lut_vdsat_column_missing`), 아니면 pass.
* **출력 전용 기록**(판정을 바꾸지 않는다): 봉인 7 detail `slack_v`(vdsat 이 수인 소자 중 최소 VDS − vdsat)·`reverse_vds`(행 3 소자)·`indistinct`(|VDS − vdsat| < tol_VDsat 인
  ((소자, VDS − vdsat), ...), tol = 필드 `SatBound.tol_v` -- 기록 전용)·`indistinct_undefined`(tol 미정 소자); 봉인 9 detail `domain_edge`(LUT 표본 끝에 닿은 ((소자, 축), ...)).
* 항목의 `magnitude`·`tol`·`margin` 은 None(판정 여유 없음).
"""
from gmid_engine.core import compute_block
from gmid_engine.lut import (
    REASON_LUT_DOMAIN,
    REASON_OFF_DECLARED,
    REASON_REVERSE_VDS,
    REASON_VDSAT_COLUMN_UNAVAILABLE,
    lut_axis_bounds,
)

from .region_judge import (
    ACTUAL_CUTOFF,
    ACTUAL_OUT_OF_DOMAIN,
    ACTUAL_SATURATION,
    ACTUAL_TRIODE,
    ACTUAL_UNRESOLVED,
    OUT_OF_DOMAIN,
    judge_region,
)
from .region_mismatch import region_mismatch
from .s2_values import (
    DC_KEY,
    DC_SEAL_REGION_WRITER,
    REASON_VDSAT_MISSING,
    SEAL_CONDUCTION,
    SEAL_FAIL,
    SEAL_PASS,
    SEAL_SATURATION,
    SEAL_UNDEFINED,
    SealItem,
)

READS = (("device", "dc_op"), ("device", "dc_sat_v"), ("device", "region_decl"))
WRITES = (("graph", "dc_seal_7"), ("graph", "dc_seal_9"))
_OP_AXES = (("L", "L"), ("VGS", "vgs"), ("VDS", "vds"), ("VS", "vsb"))      # (LUT 축 이름, dc_op 칸)


def _vdsat_input(bound):
    """판정 함수의 vdsat 입력 -- 필드 `SatBound` 에서: 수 -> 그 수, 축·L 위치 밖 `OUT_OF_DOMAIN`, 그 밖 사유(역방향 VDS·열 없음·`off` 선언) `None`. 모르는 사유는 fail-closed."""
    if bound.reason is None:
        return bound.vdsat_v
    if bound.reason == REASON_LUT_DOMAIN:
        return OUT_OF_DOMAIN
    if bound.reason in (REASON_REVERSE_VDS, REASON_VDSAT_COLUMN_UNAVAILABLE, REASON_OFF_DECLARED):
        return None
    raise ValueError("dc_sat_v: 모르는 사유 " + repr(bound.reason))


def _edges(lut, name, op, bounds):
    """op 가 LUT 표본 끝에 닿은 축 -> ((소자, 축), ...). 축 끝 = `lut_axis_bounds`(슬라이스 격자, kind·w_key 마다 이 호출 안 지역 읽기)."""
    key = (op.kind, op.w_key)
    if key not in bounds:
        bounds[key] = lut_axis_bounds(lut.memo, op.kind, op.w_key)
    ends = {axis: (first, last) for axis, first, last in bounds[key]}
    return tuple((name, axis) for axis, field in _OP_AXES
                 if getattr(op, field) <= ends[axis][0] or getattr(op, field) >= ends[axis][1])


def _item(number, status, devices, detail):
    return SealItem(number, status, None, None, None, tuple(devices), (), tuple(sorted(detail)))


@compute_block(DC_SEAL_REGION_WRITER, reads=READS, writes=WRITES)
def dc_seal_region(projection):
    (lut,) = projection.extras
    declared = {m: r.region for m, r in projection.column("device", "region_decl")}
    bounds_of = dict(projection.column("device", "dc_sat_v"))
    cutoff, outside, unresolved, bad7, reverse = [], [], [], [], []
    slack, band, band_undefined, edges = [], [], [], []
    axis_ends = {}
    for m, op in sorted(projection.column("device", "dc_op")):
        bound = bounds_of[m]
        sat = _vdsat_input(bound)
        verdict = judge_region(m, declared.get(m), op.current, op.vds, sat)
        actual = verdict.actual
        if actual == ACTUAL_CUTOFF:
            cutoff.append(m)
        elif actual == ACTUAL_OUT_OF_DOMAIN:
            outside.append(m)
        elif actual == ACTUAL_UNRESOLVED:
            unresolved.append(m)
        if actual in (ACTUAL_TRIODE, ACTUAL_SATURATION) and region_mismatch(verdict):      # 표 행 3·8·10
            bad7.append(m)
        if op.current > 0 and op.vds < 0 and declared.get(m) is None:
            reverse.append(m)
        if isinstance(sat, float):
            slack.append(op.vds - sat)
            tol = bound.tol_v
            if tol is None:
                band_undefined.append(m)
            elif abs(op.vds - sat) < tol:
                band.append((m, op.vds - sat))
        edges.extend(_edges(lut, m, op, axis_ends))
    detail9 = ()
    if edges:
        detail9 += (("domain_edge", tuple(edges)),)
    if cutoff:
        item9 = _item(SEAL_CONDUCTION, SEAL_FAIL, cutoff, detail9)
    elif outside:
        item9 = _item(SEAL_CONDUCTION, SEAL_UNDEFINED, outside, detail9 + (("reason", ACTUAL_OUT_OF_DOMAIN),))
    else:
        item9 = _item(SEAL_CONDUCTION, SEAL_PASS, (), detail9)
    detail7 = ()
    for key, found in (("slack_v", min(slack) if slack else None), ("reverse_vds", tuple(reverse)), ("indistinct", tuple(band)),
                       ("indistinct_undefined", tuple(band_undefined))):
        if found is not None and found != ():
            detail7 += ((key, found),)
    if bad7:
        item7 = _item(SEAL_SATURATION, SEAL_FAIL, bad7, detail7)
    elif unresolved:
        item7 = _item(SEAL_SATURATION, SEAL_UNDEFINED, unresolved, detail7 + (("reason", REASON_VDSAT_MISSING),))
    else:
        item7 = _item(SEAL_SATURATION, SEAL_PASS, (), detail7)
    return {("graph", "dc_seal_7"): {DC_KEY: item7}, ("graph", "dc_seal_9"): {DC_KEY: item9}}
