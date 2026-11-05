"""off 소자 전류 효과 관문 G2-a (EO-1 범위 4, 설계 41 §4.8-9, 계획 O-222, A-1·A-2, A-49).

진입점: `off_region_gate(snapshot, lut) -> None` -- 필드를 쓰지 않는다. 거부 = `SealViolationError`(reason `off_gate`, detail `s_prime` = ((소자, s′), ...), s′ 정의 불능이면 None).
읽는 것: `device.{dc_op, region_decl, kind, pins, bulk}`, `graph.ss_off_delta`(1차 ΔV, `node_dv` 에 없는 넷은 0), LUT VDSAT 열(`vdsat`). 부르는 자리 = `ss_evaluate`(`ss_off_delta` 바로 뒤, 나머지 소비자 앞).

대상 = `device.dc_op` 의 MOS(선언 없음 + `triode`; `off` 소자는 dc_op 에 없다). 소자마다:
* ΔVGS, ΔVDS, ΔVSB = `terminal_voltages(kind, ΔV_d, ΔV_g, ΔV_s, ΔV_b)`(LUT 부호 규약 -- 식은 선형이라 같은 정의). VDS′ = VDS + ΔVDS.
* VDSAT′ = VDSAT + Σ_X [vdsat(X + ΔX, 나머지 그대로) − vdsat(X)] (X ∈ VGS·VDS·VSB, ΔX = 0 이면 그 항 조회 0). 조회가 축·L 위치 밖이면 `OUT_OF_DOMAIN`.
* VDS < 0 인 소자(`triode` 만 봉인을 통과해 온다): 기준 VDSAT 조회 0·보정 조회 0, vdsat 입력 = `OUT_OF_DOMAIN`. VDS′ < 0 이면 표 행 4 통과, VDS′ ≥ 0 이면 행 5 거부.
* 판정 = 공용 `judge_region(소자, 선언, op.current, VDS′, VDSAT′)` + `region_mismatch`. 수치 문턱 없음(tol 미사용) -- s′ = VDS′ − VDSAT′ = 0 정확히는 포화다.
* 닫힌 식(VDSAT = a0 + a1·VGS + a2·VDS + a3·VSB 격자 안): s′ = s + (1 − a2)·ΔVDS − a1·ΔVGS − a3·ΔVSB, s = VDS − VDSAT.
oracle 왕복이 아니다 -- 봉인점 뒤 off 전류 효과가 선언 없는 소자의 포화 판정(과 `triode` 소자의 선형 판정)을 뒤집는지 본다.
"""
from gmid_engine.core import SealViolationError
from gmid_engine.graph import MOS_TERMINAL_NAMES
from gmid_engine.lut import vdsat
from gmid_engine.sizing import METRICS_KEY, OUT_OF_DOMAIN, judge_region, region_mismatch, terminal_voltages

REASON_OFF_GATE = "off_gate"
_COLUMN_UNAVAILABLE = "lut_column_unavailable"


def _lookup(lut, op, vgs, vds, vsb):
    """그 점의 VDSAT: 열 없음 None, 축·L 위치 밖 `OUT_OF_DOMAIN`, 아니면 수."""
    try:
        return vdsat(lut.memo, op.kind, op.w_key, op.L, vgs, vds, vsb)
    except SealViolationError as exc:
        return None if dict(exc.record.detail).get("reason") == _COLUMN_UNAVAILABLE else OUT_OF_DOMAIN


def _shifted(lut, op, shift):
    """VDSAT′ (수) 또는 None(열 없음)/`OUT_OF_DOMAIN`. shift = (ΔVGS, ΔVDS, ΔVSB). 기준 조회 1회 + ΔX ≠ 0 인 항마다 1회."""
    base = _lookup(lut, op, op.vgs, op.vds, op.vsb)
    if base is None or base == OUT_OF_DOMAIN:
        return base
    total = base
    point = (op.vgs, op.vds, op.vsb)
    for axis, step in enumerate(shift):
        if step == 0:
            continue
        moved = _lookup(lut, op, *(x + step if i == axis else x for i, x in enumerate(point)))
        if moved is None or moved == OUT_OF_DOMAIN:
            return moved
        total += moved - base
    return total


def off_region_gate(snapshot, lut):
    delta = dict(snapshot.value("graph", METRICS_KEY, "ss_off_delta").node_dv)
    pins = dict(snapshot.column("device", "pins"))
    bulk = {m: b.net for m, b in snapshot.column("device", "bulk")}
    declared = {m: r.region for m, r in snapshot.column("device", "region_decl")}
    rejected = []
    for m, op in sorted(snapshot.column("device", "dc_op")):
        d, g, s = (dict(pins[m])[t] for t in MOS_TERMINAL_NAMES)
        shift = terminal_voltages(op.kind, delta.get(d, 0.0), delta.get(g, 0.0), delta.get(s, 0.0), delta.get(bulk[m], 0.0))
        vds = op.vds + shift[1]
        sat = OUT_OF_DOMAIN if op.vds < 0 else _shifted(lut, op, shift)
        verdict = judge_region(m, declared.get(m), op.current, vds, sat)
        if region_mismatch(verdict):
            rejected.append((m, vds - sat if isinstance(sat, float) else None))
    if rejected:
        raise SealViolationError(devices=tuple(m for m, _s in rejected),
                                 detail={"reason": REASON_OFF_GATE, "s_prime": tuple(rejected)})
