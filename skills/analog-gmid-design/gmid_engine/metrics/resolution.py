"""metric 분해능 -- LUT 조회 불확실성의 1차 전파와 MNA 사후 오차 (계획 NFR-5 '격자 분해능', search S-19, metrics CONTRACT 9.3).

진입점: `metric_resolutions(analysis, source, parameters, memo=None) -> tuple[Resolution]`.

* `analysis` = `LoopAnalysis`(source = 그 분석의 인수 tuple), `OutputResistance`·`ResponseRatio`(source = 그 `SystemResponse`).
  결과 = 값이 있는 레지스트리 필드마다 `Resolution(quantity, value, lut, numeric)` -- LoopAnalysis: gain_db·ugf_hz·gbw_hz·
  phase_margin_deg, OutputResistance: rout_ohm, ResponseRatio: ratio_db. 값이 None 인 필드는 내지 않는다(분해능 없음).
* **LUT 몫(최악 선형 결합)**: lut = Σ_p |∂q/∂p|·Δp(Δp = ε_d·|p|, `ParameterSet`) -- 파라미터마다 부호를 모르므로 절댓값 합.
  ∂q/∂p 는 `response_sensitivity`(수반, ω 마다 LU 1회)가 낸 ∂V/∂p 를 metric 정의의 1차 미분으로 옮긴 것:
  - gain_db = 20·log10|T(0)| -> (20/ln10)·Re(∂T0/T0).
  - ugf: |T(ω_u)| = level 의 음함수 미분 ∂ω_u/∂p = −(∂|T|/∂p)/(∂|T|/∂ω), Hz = /2π.
  - phase_margin_deg = 180° − (T(0) 대비 지연) -> ∂PM/∂p = Im(∂T/∂p / T) + Im(∂T/∂ω / T)·∂ω_u/∂p(T(0) 은 실수라 위상 미분 0), 도.
  - gbw = |T0|·ω_3/2π, |T(ω_3)| = ρ·|T0|(ρ = 교차 level/|T0|) -> ∂ω_3 = −(∂|T3| − ρ·∂|T0|)/(∂|T3|/∂ω).
  - rout = V0/I -> rout·Re(∂V0)/V0. ratio_db -> (20/ln10)·(Re(∂Vn/Vn) − Re(∂Vd/Vd)).
  - T = 인수 곱: ∂T = Σ_i ∂F_i·Π_{k≠i}F_k. `ProbeFactor` 인수는 `_helpers_probe.probe_value` 의 ∂T/∂V(Middlebrook 식의 해석 미분).
* **수치 몫**: 같은 분해의 반복 개선 사후 오차 e(`solve_point`·`find_crossing` 이 쓰는 오차와 같은 정의)를 같은 1차 식으로 옮긴다
  -- DC 양은 e/|V|, 교차 양은 (| |T| − level | + e)/|∂|T|/∂ω|(이분이 멈춘 점의 잔여 + 풀이 오차를 ω 로).
* `value` = max(lut, numeric). LUT 불확실성이 미정인 MOS 가 있거나(`undetermined`) 미분이 정의되지 않으면(풀이 특이, 교차에서
  ∂|T|/∂ω = 0, 값 0 으로 나눔) 그 필드의 value·lut 는 None(미정을 0 으로 두지 않는다).
* `memo` = 부르는 쪽이 한 계산 블록 안에서 넘기는 dict(키 (id(계), ω) -> `ResponseSensitivity`) -- 같은 계·같은 ω 를 여러 metric 이
  쓰면 LU 를 한 번만 한다(DC 극한을 gain·rout·ratio 가 공유). None 이면 호출 안에서만 공유.
"""
import math

import numpy

from gmid_engine.core import AMPLITUDE_DB_PER_DECADE

from ._helpers_probe import probe_value
from .mna_types import (Factor, LoopAnalysis, OutputResistance, ParameterSet, ProbeFactor, Resolution, ResponseRatio,
                        SystemResponse)
from .sensitivity import response_sensitivity

_DB_PER_NEPER = AMPLITUDE_DB_PER_DECADE * math.log10(math.e)      # d(20·log10|x|)/d ln|x| = 20·log10(e) = 20/ln10


def _sens(memo, system, parameters, omega):
    key = (id(system), float(omega))
    if key not in memo:
        memo[key] = response_sensitivity(system, parameters, omega)
    return memo[key]


def _finite(*arrays):
    return all(a is not None and numpy.isfinite(a).all() for a in arrays)


def _factor_terms(factor, sens):
    """인수 하나 -> (F, ∂F/∂p (P,), ∂F/∂ω 또는 None, 사후 오차) 또는 None(정의 안 됨)."""
    if sens.values is None:
        return None
    if isinstance(factor, ProbeFactor):
        value, err, _why, grad = probe_value(factor, sens.omega, sens.values, sens.errors, sens.undefined)
        if grad is None:
            return None
        used = grad != 0                                    # 고른 열·관측 칸만(안 고른 전하 주입 열의 NaN 을 섞지 않는다)
        d_param = sens.d_param[:, used] @ grad[used]
        d_omega = None if sens.d_omega is None else complex(sens.d_omega[used] @ grad[used])
    else:
        value = complex(sens.values[factor.row, factor.column])
        err = float(sens.errors[factor.row, factor.column])
        d_param = sens.d_param[:, factor.row, factor.column]
        d_omega = None if sens.d_omega is None else complex(sens.d_omega[factor.row, factor.column])
    if not _finite(numpy.array([value]), d_param, numpy.array([err])):
        return None
    return complex(value), d_param, d_omega, float(err)


def _loop_terms(factors, parameters, omega, memo):
    """T = Π 인수의 (T, ∂T/∂p, ∂T/∂ω, |T| 사후 오차) 또는 None."""
    terms = []
    for f in factors:
        t = _factor_terms(f, _sens(memo, f.response.system, parameters, omega))
        if t is None:
            return None
        terms.append(t)
    values = [t[0] for t in terms]
    total = complex(numpy.prod(values))
    d_param = numpy.zeros(len(parameters.params), dtype=complex)
    d_omega = None if omega == 0 else complex(0)
    err = 0.0
    for i, (_v, dp, dw, e) in enumerate(terms):
        others = complex(numpy.prod([v for k, v in enumerate(values) if k != i]))
        d_param = d_param + dp * others
        if d_omega is not None:
            d_omega += dw * others
        err += e * abs(others)
    return total, d_param, d_omega, err


def _lut(parameters, derivative):
    if parameters.undetermined or not _finite(derivative):
        return None
    return float(numpy.sum(numpy.abs(derivative) * parameters.delta))


def _resolution(quantity, lut, numeric):
    lut = None if lut is None else float(lut)
    numeric = None if numeric is None else float(numeric)
    value = None if lut is None or numeric is None else max(lut, numeric)
    return Resolution(quantity, value, lut, numeric)


def _magnitude_slopes(t, d_param, d_omega):
    mag = abs(t)
    return mag, (numpy.conj(t) * d_param).real / mag, (numpy.conj(t) * d_omega).real / mag


def _loop(analysis, factors, parameters, memo):
    db = _DB_PER_NEPER
    out = []
    dc = _loop_terms(factors, parameters, 0.0, memo)
    if dc is not None and not dc[0]:
        dc = None                                           # T(0) = 0: 로그·비로 나눌 수 없다(값도 정의 불가인 경우)
    if analysis.gain_db is not None:
        if dc is None:
            out.append(Resolution("gain_db", None))
        else:
            t0, d0, _w, e0 = dc
            out.append(_resolution("gain_db", _lut(parameters, db * (d0 / t0).real), db * e0 / abs(t0)))
    if analysis.ugf_hz is not None:
        out.extend(_crossing_terms(analysis, factors, parameters, memo))
    if analysis.gbw_hz is not None:
        out.append(Resolution("gbw_hz", None) if dc is None else _gbw(analysis, factors, parameters, memo, dc))
    return tuple(out)


def _crossing_terms(analysis, factors, parameters, memo):
    crossing = analysis.ugf
    terms = _loop_terms(factors, parameters, crossing.omega, memo)
    quantities = ("ugf_hz",) + (("phase_margin_deg",) if analysis.phase_margin_deg is not None else ())
    if terms is None:
        return tuple(Resolution(q, None) for q in quantities)
    t, d_param, d_omega, err = terms
    mag, d_mag, d_mag_w = _magnitude_slopes(t, d_param, d_omega)
    if d_mag_w == 0:
        return tuple(Resolution(q, None) for q in quantities)
    d_w = -d_mag / d_mag_w
    w_num = (abs(mag - crossing.level) + err) / abs(d_mag_w)
    lut_w = _lut(parameters, d_w)
    out = [_resolution("ugf_hz", None if lut_w is None else lut_w / (2 * math.pi), w_num / (2 * math.pi))]
    if analysis.phase_margin_deg is not None:
        phase_w = (d_omega / t).imag
        d_pm = (d_param / t).imag + phase_w * d_w
        lut = _lut(parameters, d_pm)
        out.append(_resolution("phase_margin_deg", None if lut is None else math.degrees(lut),
                               math.degrees(err / mag + abs(phase_w) * w_num)))
    return tuple(out)


def _gbw(analysis, factors, parameters, memo, dc):
    t0, d0, _w, e0 = dc
    a = abs(t0)
    d_a = (numpy.conj(t0) * d0).real / a
    crossing = analysis.f3db
    rho = crossing.level / a
    terms = _loop_terms(factors, parameters, crossing.omega, memo)
    if terms is None:
        return Resolution("gbw_hz", None)
    t3, d3, d3_w, e3 = terms
    mag, d_mag, d_mag_w = _magnitude_slopes(t3, d3, d3_w)
    if d_mag_w == 0:
        return Resolution("gbw_hz", None)
    d_w3 = -(d_mag - rho * d_a) / d_mag_w
    d_gbw = (d_a * crossing.omega + a * d_w3) / (2 * math.pi)
    w_num = (abs(mag - crossing.level) + e3 + rho * e0) / abs(d_mag_w)
    return _resolution("gbw_hz", _lut(parameters, d_gbw), (e0 * crossing.omega + a * w_num) / (2 * math.pi))


def _port(analysis, response, parameters, memo):
    sens = _sens(memo, response.system, parameters, 0.0)
    if sens.values is None:
        quantity = "rout_ohm" if isinstance(analysis, OutputResistance) else "ratio_db"
        return (Resolution(quantity, None),)
    if isinstance(analysis, OutputResistance):
        v0 = sens.values[analysis.row, analysis.column].real
        e0 = sens.errors[analysis.row, analysis.column]
        if not v0:
            return (Resolution("rout_ohm", None),)
        derivative = analysis.rout_ohm * sens.d_param[:, analysis.row, analysis.column].real / v0
        return (_resolution("rout_ohm", _lut(parameters, derivative), analysis.rout_ohm * e0 / abs(v0)),)
    db = _DB_PER_NEPER
    row = analysis.row
    vn, vd = sens.values[row, analysis.num_column].real, sens.values[row, analysis.den_column].real
    if not vn or not vd:
        return (Resolution("ratio_db", None),)
    derivative = db * (sens.d_param[:, row, analysis.num_column].real / vn
                       - sens.d_param[:, row, analysis.den_column].real / vd)
    numeric = db * (sens.errors[row, analysis.num_column] / abs(vn) + sens.errors[row, analysis.den_column] / abs(vd))
    return (_resolution("ratio_db", _lut(parameters, derivative), float(numeric)),)


def metric_resolutions(analysis, source, parameters, memo=None):
    """분석 결과, 그 출처(LoopAnalysis -> 인수 tuple, OutputResistance·ResponseRatio -> SystemResponse), `ParameterSet` ->
    값이 있는 필드마다 `Resolution` tuple. 예외는 형식 위반(TypeError)뿐 -- 정의 불가는 value None."""
    if not isinstance(parameters, ParameterSet):
        raise TypeError("metric_resolutions: parameters 는 ParameterSet 이어야 한다")
    memo = {} if memo is None else memo
    if isinstance(analysis, LoopAnalysis):
        if not isinstance(source, tuple) or not source or not all(isinstance(f, (Factor, ProbeFactor)) for f in source):
            raise TypeError("metric_resolutions: LoopAnalysis 의 source 는 그 분석의 인수 tuple 이어야 한다")
        return _loop(analysis, source, parameters, memo)
    if isinstance(analysis, (OutputResistance, ResponseRatio)):
        if not isinstance(source, SystemResponse):
            raise TypeError("metric_resolutions: OutputResistance·ResponseRatio 의 source 는 SystemResponse 여야 한다")
        value = analysis.rout_ohm if isinstance(analysis, OutputResistance) else analysis.ratio_db
        return () if value is None else _port(analysis, source, parameters, memo)
    raise TypeError("metric_resolutions: 소신호 분석 결과(LoopAnalysis·OutputResistance·ResponseRatio)가 아니다: %r"
                    % (type(analysis).__name__,))
