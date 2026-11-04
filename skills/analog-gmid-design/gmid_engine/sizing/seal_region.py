"""봉인 7·9 영역 판정 계산 블록 -- 소자마다 공용 영역 판정 한 번 (EO-1 범위 4, 설계 41 §4.8-2, 계획 N3.6 표 7·9행, O-202·O-204·O-205).

진입점: `dc_seal_region`(`@compute_block`) -- `dc_seal_region(snapshot, lut)`. reads `device.dc_op`, `device.region_decl`. writes `graph.dc_seal_7`, `graph.dc_seal_9`.

`device.dc_op` 의 MOS 마다 `judge_region(device, declared, current, vds, vdsat)` 을 **한 번** 부르고(선언 = `device.region_decl` 의 region, 없으면 None) 그 결과 하나에서
두 항목의 status 를 정한다. 수치 문턱이 없다 -- 전도 = ID > 0, 포화 = VDS ≥ VDSAT(경계 0 V·등호).
* vdsat 입력: VDS < 0 이면 LUT 조회 없이 `None`(표 행 3·4 는 vdsat 값을 안 본다), 아니면 그 점 LUT VDSAT(`vdsat`). 열 없음(`lut_column_unavailable`) = `None`,
  축·L 위치 밖(lut 사유 `lut_axis_out_of_range`·`lut_l_*`) = `OUT_OF_DOMAIN`, 그 밖 LUT 실패는 소자 이름을 붙인 `SealViolationError`(fail-closed).
* 봉인 9: `cutoff` ≥ 1 이면 fail(devices = 그 소자), 아니고 `out_of_domain` ≥ 1 이면 undefined(devices = 그 소자, reason `out_of_domain`), 아니면 pass.
* 봉인 7: 표 행 3·8·10(거부 판정 `region_mismatch` 중 triode/saturation 쪽) ≥ 1 이면 fail, 아니고 행 6(`unresolved`, VDSAT 열 없음) ≥ 1 이면 undefined(reason
  `lut_vdsat_column_missing`), 아니면 pass.
* **출력 전용 기록**(판정을 바꾸지 않는다): 봉인 7 detail `slack_v`(vdsat 이 수인 소자 중 최소 VDS − vdsat)·`reverse_vds`(행 3 소자)·`indistinct`(|VDS − vdsat| < tol_VDsat 인
  ((소자, VDS − vdsat), ...), tol = `tol_vdsat_table(...).at(L, vds)`)·`indistinct_undefined`(tol 미정·조회 실패 소자); 봉인 9 detail `domain_edge`(LUT 표본 끝에 닿은 ((소자, 축), ...)).
* 항목의 `magnitude`·`tol`·`margin` 은 None(판정 여유 없음).
"""
from gmid_engine.core import SealViolationError, compute_block
from gmid_engine.lut import lut_axis_bounds, tol_vdsat_table, vdsat

from ._helpers_lut import with_device
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

READS = (("device", "dc_op"), ("device", "region_decl"))
WRITES = (("graph", "dc_seal_7"), ("graph", "dc_seal_9"))
_COLUMN_UNAVAILABLE = "lut_column_unavailable"     # lut CONTRACT 4.3 열 출처 규칙 3
_DOMAIN_REASONS = ("lut_axis_out_of_range", "lut_l_not_anchor", "lut_l_outside_model_bins", "lut_l_bin_unbracketed", "lut_l_cross_bin")      # lut CONTRACT 4.0 축·L 위치 밖
_OP_AXES = (("L", "L"), ("VGS", "vgs"), ("VDS", "vds"), ("VS", "vsb"))      # (LUT 축 이름, dc_op 칸)


def _vdsat_input(lut, device, op):
    """판정 함수의 vdsat 입력: VDS < 0 이면 조회 없이 None, 열 없음 None, 축·L 위치 밖 `OUT_OF_DOMAIN`, 아니면 수. 그 밖 LUT 실패는 소자 이름을 붙여 낸다(fail-closed)."""
    if op.vds < 0:
        return None
    try:
        return vdsat(lut.memo, op.kind, op.w_key, op.L, op.vgs, op.vds, op.vsb)
    except SealViolationError as exc:
        reason = dict(exc.record.detail).get("reason")
        if reason == _COLUMN_UNAVAILABLE:
            return None
        if reason in _DOMAIN_REASONS:
            return OUT_OF_DOMAIN
        raise with_device(exc, device, "vdsat") from exc


def _band(lut, op):
    """tol_VDsat 셀 (없으면 None) -- 조회 실패도 None(띠 기록만 미정이고 판정은 바뀌지 않는다)."""
    try:
        return tol_vdsat_table(lut.memo, op.kind, op.w_key).at(op.L, op.vds)
    except SealViolationError:
        return None


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
    cutoff, outside, unresolved, bad7, reverse = [], [], [], [], []
    slack, band, band_undefined, edges = [], [], [], []
    bounds = {}
    for m, op in sorted(projection.column("device", "dc_op")):
        sat = _vdsat_input(lut, m, op)
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
            tol = _band(lut, op)
            if tol is None:
                band_undefined.append(m)
            elif abs(op.vds - sat) < tol:
                band.append((m, op.vds - sat))
        edges.extend(_edges(lut, m, op, bounds))
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
