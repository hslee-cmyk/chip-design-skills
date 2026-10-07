"""주파수 metric 한 번 계산 -- gain·UGF·GBW·PM (설계 design_mod1_lut_mod5_mna 3.4, 계획 N3.8 gain·PM 항).

진입점: `analyze_loop`.

인수 묶음 T = Π Factor 하나에서 모든 주파수 metric 을 한 번에 계산해 `LoopAnalysis` 로 보관한다(같은 응답을 metric 이
공유 -- UGF 이분을 PM 이 다시 하지 않는다).

* `gain_ss_db` = 20·log10|T(0)|.
* `ugf_ss_hz`: |T| = 1 첫 교차(`find_crossing`), Hz = ω/2π.
* `gbw_ss_hz` = |T(0)|·f_3dB, f_3dB = |T| = |T(0)|/√2 첫 교차. `gbw_ugf_gap_hz` = gbw − ugf.
* `pm_ss_deg` = 180° − (T(0) 대비 UGF 까지 누적 위상 지연). **PM 정의(계획 N3.8, U-48 사용자 확정)**: 선언된 되먹임
  수동소자가 있으면 그 β 루프의 루프 이득 T = A·β, 없으면 β = 1 루프 T = A. 이 함수는 T 를 인수 곱으로 받으므로
  β = 1 은 인수 하나(A), β 루프는 인수 둘(A, β)이다. 기준이 T(0) 위상이라 되먹임 부호 관례(반전·비반전 관측)와 무관하다.
값이 정의되지 않으면 None 과 (metric, 사유) 를 `undefined` 에 남긴다(읽을 때 `metric_value` 가 구조화 실패로 낸다).
"""
import math

import numpy

from gmid_engine.core import AMPLITUDE_DB_PER_DECADE

from .crossing import find_crossing
from .mna_types import Crossing, Factor, LoopAnalysis
from .phase_lag import phase_lag


def _product_samples(factors):
    if not isinstance(factors, tuple) or not factors:
        raise TypeError("analyze_loop 는 비어 있지 않은 Factor tuple 을 받는다")
    for f in factors:
        if not isinstance(f, Factor):
            raise TypeError("analyze_loop: 원소는 Factor 여야 한다: %r" % (f,))
    omegas = factors[0].response.omegas
    values = numpy.ones(omegas.shape, dtype=complex)
    for f in factors:
        if not numpy.array_equal(f.response.omegas, omegas):
            raise ValueError("루프 인수들의 ω 격자가 다르다 -- 한 번의 solve_responses 로 함께 풀어야 한다")
        values = values * f.response.values[:, f.column]
    return omegas, values


def analyze_loop(factors):
    """Factor tuple(같은 solve_responses 결과) -> `LoopAnalysis`."""
    omegas, values = _product_samples(factors)
    dc_value = float(values[0].real)
    magnitude = abs(dc_value)
    undefined = []
    gain_db = None
    if magnitude > 0:
        gain_db = AMPLITUDE_DB_PER_DECADE * math.log10(magnitude)
    else:
        undefined.append(("gain_ss_db", "dc_zero"))
    ugf = find_crossing(factors, omegas, values, 1.0)
    ugf_hz = lag = pm_deg = None
    if ugf.omega is None:
        undefined.append(("ugf_ss_hz", ugf.reason))
        undefined.append(("pm_ss_deg", ugf.reason))
    else:
        ugf_hz = ugf.omega / (2 * math.pi)
        lag = phase_lag(factors, omegas, values, ugf.omega, ugf.value)
        pm_deg = math.degrees(math.pi - lag)
    gbw_hz = gap_hz = None
    if magnitude > 0:
        f3db = find_crossing(factors, omegas, values, magnitude / math.hypot(1, 1))
    else:
        f3db = Crossing(level=0.0, reason="dc_zero")
    if f3db.omega is None:
        undefined.append(("gbw_ss_hz", f3db.reason))
    else:
        gbw_hz = magnitude * f3db.omega / (2 * math.pi)
        if ugf_hz is not None:
            gap_hz = gbw_hz - ugf_hz
    return LoopAnalysis(
        dc_value=dc_value,
        gain_ss_db=gain_db,
        ugf=ugf,
        f3db=f3db,
        ugf_ss_hz=ugf_hz,
        gbw_ss_hz=gbw_hz,
        gbw_ugf_gap_hz=gap_hz,
        phase_lag_rad=lag,
        pm_ss_deg=pm_deg,
        undefined=tuple(undefined),
    )
