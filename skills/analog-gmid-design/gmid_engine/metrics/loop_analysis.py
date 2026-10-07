"""주파수 양 한 번 계산 -- gain·UGF·GBW·위상 여유 (설계 design_mod1_lut_mod5_mna 3.4, 계획 N3.8 gain·PM 항).

진입점: `analyze_loop`.

인수 묶음 T = Π 인수(`Factor`·`ProbeFactor`, 공통 규약 -- mna_types docstring) 하나에서 모든 주파수 양을 한 번에 계산해
`LoopAnalysis` 로 보관한다(같은 응답을 metric 이 공유 -- UGF 이분을 위상 여유가 다시 하지 않는다). 레지스트리가 이 필드를
metric 이름에 잇는다: `gain_ss_db`·`ugf_ss_hz`·`gbw_ss_hz`·`parasitic_pm_ss_deg` = 선언 전달 뷰 인수, `pm_ss_deg` = 루프 뷰 인수.

* `gain_db` = 20·log10|T(0)|(T(0) = ω → 0 극한).
* `ugf_hz`: |T| = 1 첫 교차(`find_crossing`), Hz = ω/2π.
* `gbw_hz` = |T(0)|·f_3dB, f_3dB = |T| = |T(0)|/√2 첫 교차. `gbw_ugf_gap_hz` = gbw − ugf.
* `phase_margin_deg` = 180° − (T(0) 대비 UGF 까지 누적 위상 지연). **PM 정의(계획 N3.8, U-48 사용자 확정, 7a design 2.4·2.5)**:
  spec `feedback` 이 비어 있지 않으면 절단 회로 계의 `ProbeFactor` 하나(오라클 Middlebrook 과 같은 식 T = (Tv·Ti − 1)/(Tv + Ti + 2)),
  빈 list 면 β = 1 -- 포트 전달 뷰 `Factor` 하나(T = A). A·β 를 따로 푼 인수 2개의 곱은 β 망이 증폭기를 싣는 부하를 빼므로
  `pm_ss_deg` 의 정의가 아니다(인수 곱 기계 자체는 그대로 지원한다 -- 7a design 2.7). 기준이 T(0) 위상이라 되먹임 부호
  관례(반전·비반전 관측)와 무관하다. 같은 계산을 전달 뷰 인수에 하면 `parasitic_pm_ss_deg`(DM 3.4)다.
예외를 던지지 않는다: 정의되지 않은 양은 None 이고 `undefined` 에 `Undefined(quantity = 필드 이름, …)`.
"""
import math

import numpy

from gmid_engine.core import AMPLITUDE_DB_PER_DECADE

from ._helpers_product import check_factors
from .crossing import find_crossing
from .mna_types import LoopAnalysis, Undefined
from .phase_lag import phase_lag

_QUANTITIES = ("gain_db", "ugf_hz", "gbw_hz", "gbw_ugf_gap_hz", "phase_lag_rad", "phase_margin_deg")


def _product_samples(factors):
    omegas = check_factors(factors)
    values = numpy.ones(omegas.shape, dtype=complex)
    for f in factors:
        values = values * f.samples
    return omegas, values


def _all_undefined(factors, values):
    causes = tuple(u for f in factors for u in f.undefined) or (Undefined("response", "response_not_finite", "numeric"),)
    first = causes[0]
    undefined = tuple(Undefined(q, first.code, first.category, first.detail) for q in _QUANTITIES)
    dc = values[0].real
    return LoopAnalysis(
        dc_value=None if math.isnan(dc) else float(dc), gain_db=None, ugf=None, f3db=None, ugf_hz=None,
        gbw_hz=None, gbw_ugf_gap_hz=None, phase_lag_rad=None, phase_margin_deg=None, undefined=undefined,
    )


def _retag(undefined, quantity):
    return Undefined(quantity, undefined.code, undefined.category, undefined.detail)


def analyze_loop(factors):
    """인수 tuple(`Factor`·`ProbeFactor`, 같은 solve_responses 결과) -> `LoopAnalysis`."""
    omegas, values = _product_samples(factors)
    if not numpy.isfinite(values).all():
        return _all_undefined(factors, values)
    dc_value = float(values[0].real)
    magnitude = abs(dc_value)
    undefined = []
    gain_db = None
    if magnitude > 0:
        gain_db = AMPLITUDE_DB_PER_DECADE * math.log10(magnitude)
    else:
        undefined.append(Undefined("gain_db", "dc_zero", "definitional"))
    ugf = find_crossing(factors, omegas, values, 1.0, "ugf_hz")
    ugf_hz = lag = pm_deg = None
    if ugf.omega is None:
        undefined.append(ugf.undefined)
        undefined.append(_retag(ugf.undefined, "phase_lag_rad"))
        undefined.append(_retag(ugf.undefined, "phase_margin_deg"))
    else:
        ugf_hz = ugf.omega / (2 * math.pi)
        lag, why = phase_lag(factors, omegas, values, ugf.omega, ugf.value, "phase_lag_rad")
        if why is None:
            pm_deg = math.degrees(math.pi - lag)
        else:
            undefined.append(why)
            undefined.append(_retag(why, "phase_margin_deg"))
    gbw_hz = gap_hz = f3db = None
    if magnitude > 0:
        f3db = find_crossing(factors, omegas, values, magnitude / math.hypot(1, 1), "gbw_hz")
        if f3db.omega is None:
            undefined.append(f3db.undefined)
        else:
            gbw_hz = magnitude * f3db.omega / (2 * math.pi)
    else:
        undefined.append(Undefined("gbw_hz", "dc_zero", "definitional"))
    if gbw_hz is not None and ugf_hz is not None:
        gap_hz = gbw_hz - ugf_hz
    else:
        undefined.append(Undefined("gbw_ugf_gap_hz", "operand_undefined", "definitional"))
    return LoopAnalysis(
        dc_value=dc_value,
        gain_db=gain_db,
        ugf=ugf,
        f3db=f3db,
        ugf_hz=ugf_hz,
        gbw_hz=gbw_hz,
        gbw_ugf_gap_hz=gap_hz,
        phase_lag_rad=lag,
        phase_margin_deg=pm_deg,
        undefined=tuple(undefined),
    )
