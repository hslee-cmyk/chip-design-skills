"""off 소자 전류 효과 관문 G2-a (EO-1 범위 4, 설계 41 §4.8-9, 계획 O-222, A-1·A-2, A-49).

진입점: `off_region_gate(snapshot, lut) -> None` -- 필드를 쓰지 않는다. 거부 = `SealViolationError`(reason `off_gate`, detail `s_prime` = ((소자, s′), ...), s′ 정의 불능이면 None).
읽는 것: `device.{dc_op, dc_sat_v, region_decl, kind, pins, bulk}`, `graph.ss_off_delta`(1차 ΔV, `node_dv` 에 없는 넷은 0). 기준 VDSAT(·`vdsat(X)`) = 필드 `device.dc_sat_v` 의 `vdsat_v`(LUT 재호출 0),
보정점 vdsat(X + ΔX) = `lut.sat_threshold`(card HC-S 정본 -- 직접 `vdsat` 호출 0). 부르는 자리 = `ss_evaluate`(`ss_off_delta` 바로 뒤, 나머지 소비자 앞).

대상 = `device.dc_op` 의 MOS(선언 없음 + `triode`; `off` 소자는 dc_op 에 없다). 소자마다:
* ΔVGS, ΔVDS, ΔVSB = `terminal_voltages(kind, ΔV_d, ΔV_g, ΔV_s, ΔV_b)`(LUT 부호 규약 -- 식은 선형이라 같은 정의). VDS′ = VDS + ΔVDS.
* VDSAT′ = VDSAT + Σ_X [vdsat(X + ΔX, 나머지 그대로) − vdsat(X)] (X ∈ VGS·VDS·VSB, ΔX = 0 이면 그 항 조회 0; vdsat(X) = 필드 값). 보정점이 축·L 위치 밖이거나 역방향 VDS(<0)이면 `OUT_OF_DOMAIN`.
* VDS < 0 인 소자(`triode` 만 봉인을 통과해 온다, 필드 사유 `reverse_vds`): 기준·보정 조회 0, vdsat 입력 = `OUT_OF_DOMAIN`. VDS′ < 0 이면 표 행 4 통과, VDS′ ≥ 0 이면 행 5 거부.
* 판정 = 공용 `judge_region(소자, 선언, op.current, VDS′, VDSAT′)` + `region_mismatch`. 수치 문턱 없음(tol 미사용) -- s′ = VDS′ − VDSAT′ = 0 정확히는 포화다.
* 닫힌 식(VDSAT = a0 + a1·VGS + a2·VDS + a3·VSB 격자 안): s′ = s + (1 − a2)·ΔVDS − a1·ΔVGS − a3·ΔVSB, s = VDS − VDSAT.
oracle 왕복이 아니다 -- 봉인점 뒤 off 전류 효과가 선언 없는 소자의 포화 판정(과 `triode` 소자의 선형 판정)을 뒤집는지 본다.
"""
from gmid_engine.core import SealViolationError
from gmid_engine.graph import MOS_TERMINAL_NAMES
from gmid_engine.lut import REASON_LUT_DOMAIN, REASON_OFF_DECLARED, REASON_REVERSE_VDS, REASON_VDSAT_COLUMN_UNAVAILABLE, sat_threshold
from gmid_engine.sizing import METRICS_KEY, OUT_OF_DOMAIN, judge_region, region_mismatch, terminal_voltages

REASON_OFF_GATE = "off_gate"


def _input(bound):
    """판정 함수의 vdsat 입력 -- `SatBound` 에서: 수 -> 그 수, 열 없음 `None`, 정의역 밖·역방향 VDS `OUT_OF_DOMAIN`. 모르는 사유는 fail-closed."""
    if bound.reason is None:
        return bound.vdsat_v
    if bound.reason in (REASON_VDSAT_COLUMN_UNAVAILABLE, REASON_OFF_DECLARED):      # `off` 선언은 판정 함수가 값을 안 본다(표 행 1)
        return None
    if bound.reason in (REASON_LUT_DOMAIN, REASON_REVERSE_VDS):
        return OUT_OF_DOMAIN
    raise ValueError("dc_sat_v: 모르는 사유 " + repr(bound.reason))


def _shifted(lut, op, base, shift):
    """VDSAT′ (수) 또는 None(열 없음)/`OUT_OF_DOMAIN`. shift = (ΔVGS, ΔVDS, ΔVSB), base = 필드의 기준 VDSAT(수). ΔX ≠ 0 인 항마다 `sat_threshold` 1회."""
    total = base
    point = (op.vgs, op.vds, op.vsb)
    for axis, step in enumerate(shift):
        if step == 0:
            continue
        moved = _input(sat_threshold(lut.memo, op.kind, op.w_key, op.L, *(x + step if i == axis else x for i, x in enumerate(point))))
        if moved is None or moved == OUT_OF_DOMAIN:
            return moved
        total += moved - base
    return total


def off_region_gate(snapshot, lut):
    delta = dict(snapshot.value("graph", METRICS_KEY, "ss_off_delta").node_dv)
    pins = dict(snapshot.column("device", "pins"))
    bulk = {m: b.net for m, b in snapshot.column("device", "bulk")}
    declared = {m: r.region for m, r in snapshot.column("device", "region_decl")}
    bounds = dict(snapshot.column("device", "dc_sat_v"))
    rejected = []
    for m, op in sorted(snapshot.column("device", "dc_op")):
        d, g, s = (dict(pins[m])[t] for t in MOS_TERMINAL_NAMES)
        shift = terminal_voltages(op.kind, delta.get(d, 0.0), delta.get(g, 0.0), delta.get(s, 0.0), delta.get(bulk[m], 0.0))
        vds = op.vds + shift[1]
        base = _input(bounds[m])
        if op.vds < 0:
            sat = OUT_OF_DOMAIN
        elif base is None or base == OUT_OF_DOMAIN:
            sat = base
        else:
            sat = _shifted(lut, op, base, shift)
        verdict = judge_region(m, declared.get(m), op.current, vds, sat)
        if region_mismatch(verdict):
            rejected.append((m, vds - sat if isinstance(sat, float) else None))
    if rejected:
        raise SealViolationError(devices=tuple(m for m, _s in rejected),
                                 detail={"reason": REASON_OFF_GATE, "s_prime": tuple(rejected)})
