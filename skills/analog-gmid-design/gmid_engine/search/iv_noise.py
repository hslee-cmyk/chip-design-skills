"""잡음 경로 출발 구간 -- 열잡음 가드 부하 gm/ID 상한과 폐루프 잡음 경계의 활성 여부 (설계 41 §7.5, §6.4-3; D-NZ5, D-SIf).

진입점: `noise_bounds(ctx, currents, lengths, gm_id_lo) -> NoiseBounds`.

* **`noise_excess_th <= E` 가드**(41 §7.5): noise_excess_th = 1 + (부하 열잡음 기여 / 입력 열잡음 기여) 이므로 부하 합 ≤ (E − 1)·입력 합이다. 소자 기여 = S_vg·gm²
  (게이트 환산 열잡음 밀도 × gm², 입력 환산 비로 gm_in² 가 약분된다) -- S_vg 는 U3 `noise_params` 의 평탄값 B(기준 폭 w_ref 에서 잰 값, 폭 W 소자는 B·w_ref/W: 같은 전류밀도에서 폭에 반비례),
  gm = (gm/ID)·I(매크로 1회차 전류). 합 가드를 소자별 gm/ID 상한으로 바꾸는 규약은 `guard_bounds`(41 §6.2 와 같은 '나머지는 최소로').
  입력·부하 소자는 gain 제약 전달 뷰의 첫 이득 블록 역할로 정한다. 41 §7.5 는 γ_k·gm_k 비 형태로 쓰지만 B = 4kTγ/gm 이라 같은 비다.
* **파일럿 `noise_out_int_vrms`**: 41 §7.5·§6.4-3 의 열잡음 C_eff 하한(`2·γ_avg·kT/(β·C_eff)`)과 1/f L 하한(`Σ_in K/(W·L)·∫ f^−EF |폐루프 이득|² df`)은 (1) 적분 대역 [f_lo, f_hi] 의
  유도 규칙(U8 `noise_integral`: f_lo = LUT 실측 최저 잡음 주파수, 꼬리 상계 f·S(f) <= 분해능²)과 kT(U8 은 `scipy.constants.k` × (`JunctionSource.temp_c` + 273.15))은 병합돼 있다. 그러나 출발 구간 입력에는
  (1) 되먹임율 β -- 1/f 하한 `∫ f^−EF |폐루프 이득|² df` 의 폐루프 이득(`feedback_factor_beta_unavailable`), (2) C_eff 를 받을 출발 어휘 -- `Bound` 는 소자 gm/ID·L 뿐이고 수동소자 값 경계와
  보상 C 소자 지정이 입력 묶음에 없다(`c_eff_not_a_start_bound`)가 없다. 없는 입력을 임의로 정하지 않고 위 정확한 사유로 비활성 보고한다(`depends_on_unmerged_unit` 은 U8 병합으로 거짓이 돼 제거). LUT 잡음
  데이터가 없으면 `lut_noise_unavailable`. 판정은 U8 전회로 `noise_out_int_vrms`(봉인 스냅샷)가 한다.
* LUT 잡음 데이터가 없으면(`lut_noise_unavailable`) 계산하지 않고 그 사유를 비활성으로 남긴다(`noise_lut_missing` 정지는 로드 단계의 몫). 출발값 전용(EP-7).
"""
import dataclasses

from gmid_engine.core import SchemaRejectedError, SealViolationError
from gmid_engine.lut import noise_params

from ._helpers_curves import QUANTITY_IDU, QUANTITY_VGS, curve_bundle_of, curve_value
from ._helpers_guard import Tolerant, guard_bounds, guard_devices, guard_input_gm_id
from .start_values import (
    SRC_NOISE_FLICKER_L,
    SRC_NOISE_GUARD,
    SRC_NOISE_THERMAL_C,
    WHY_NO_CURRENT,
    WHY_NO_LUT,
    WHY_NO_TARGET,
)

WHY_NO_LUT_NOISE = "lut_noise_unavailable"                 # LUT 잡음 r1 데이터 없음(`noise_params` 가 던지는 사유와 같은 이름)
WHY_NO_BETA = "feedback_factor_beta_unavailable"            # 1/f L 하한의 폐루프 이득 |H_cl|² 에 쓸 되먹임율 β -- 출발 입력 묶음(StartContext)에 되먹임 선언·그 전달이 없다
WHY_NO_C_EFF = "c_eff_not_a_start_bound"                    # 열잡음 C_eff 하한은 수동소자(보상 C) 값 경계 -- 출발 어휘(Bound)는 소자 gm/ID·L 뿐이고 C_eff 소자 지정도 입력 묶음에 없다
_METRIC_GUARD = "noise_excess_th"
_METRIC_INTEGRATED = "noise_out_int_vrms"
_LUT_ERRORS = (SealViolationError, SchemaRejectedError)


@dataclasses.dataclass(frozen=True)
class NoiseBounds:
    """`bounds` = {소자: (Bound, ...)}(부하 gm/ID 상한), `conflicts`, `inactive` = ((경계 식, 사유), ...)."""

    bounds: object
    conflicts: tuple
    inactive: tuple


class _WhiteLevelUnknown(Exception):
    """B 가 미상(`b_status`)인 점 -- 이 파일 밖으로 나가지 않는다."""


def _white_density(ctx, name, g, L, current):
    """소자의 게이트 환산 열잡음 밀도 S_vg(V²/Hz) -- 기준 폭의 B 를 W 로 환산."""
    d = ctx.by_name[name]
    bundle = curve_bundle_of(ctx, d.name, d.kind, L)
    curve = bundle[QUANTITY_IDU]
    params = noise_params(ctx.memo, d.kind, d.w_key, L, curve_value(bundle, QUANTITY_VGS, g), curve.vds, curve.vsb)
    if params.B is None:
        raise _WhiteLevelUnknown(params.b_status)
    w = max(current * L / curve_value(bundle, QUANTITY_IDU, g), ctx.w_min_m)          # 실현 폭은 PDK 최소 finger 폭 이상
    return params.B * params.w_m / w


def noise_bounds(ctx, currents, lengths, gm_id_lo, gm_id_cap=None):
    inactive = []
    if any(m == _METRIC_INTEGRATED for m, _op, _v in ctx.constraints):
        no_lut = {d.kind for d in ctx.devices} - set(ctx.memo.lut.noise)
        inactive += [(SRC_NOISE_FLICKER_L, WHY_NO_LUT_NOISE if no_lut else WHY_NO_BETA),
                     (SRC_NOISE_THERMAL_C, WHY_NO_LUT_NOISE if no_lut else WHY_NO_C_EFF)]
    else:
        inactive += [(SRC_NOISE_FLICKER_L, WHY_NO_TARGET), (SRC_NOISE_THERMAL_C, WHY_NO_TARGET)]
    guard = [v for m, op, v in ctx.constraints if m == _METRIC_GUARD and op == "<="]
    if not guard:
        return NoiseBounds({}, (), tuple(inactive) + ((SRC_NOISE_GUARD, WHY_NO_TARGET),))
    inputs, loads = guard_devices(ctx)
    if not inputs or any(currents.get(n) is None for n in inputs + loads):
        return NoiseBounds({}, (), tuple(inactive) + ((SRC_NOISE_GUARD, WHY_NO_CURRENT),))

    def term(name, g):
        return _white_density(ctx, name, g, lengths[name], currents[name]) * (g * currents[name]) ** 2

    term = Tolerant(term)
    try:
        bounds, conflicts = guard_bounds(ctx, inputs, loads, term, min(guard) - 1, lengths, gm_id_lo,
                                         guard_input_gm_id(ctx, term, inputs, lengths, gm_id_lo, gm_id_cap), SRC_NOISE_GUARD)
    except _LUT_ERRORS as exc:
        return NoiseBounds({}, (), tuple(inactive) + ((SRC_NOISE_GUARD, dict(exc.record.detail).get("reason", WHY_NO_LUT)),))
    except _WhiteLevelUnknown as exc:
        return NoiseBounds({}, (), tuple(inactive) + ((SRC_NOISE_GUARD, str(exc)),))
    return NoiseBounds(bounds, conflicts, tuple(inactive))
