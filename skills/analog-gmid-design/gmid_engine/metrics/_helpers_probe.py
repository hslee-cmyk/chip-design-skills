"""Middlebrook 이중 주입 루프 이득 T 한 점 평가 공용 helper (사용처: `probe_loop.py` 격자 표본, `_helpers_product.py` 격자 밖 한 점,
`resolution.py` 분해능의 ∂T/∂V).

공개 함수: `probe_value(probe, omega, values, errors, causes)` -- 절단 회로 계의 관측값 (r, m) 한 점에서 T, |T| 사후 오차, 사유,
∂T/∂V((r, m) 복소 -- 고른 열·관측 칸만 0 아님, 정의 안 되면 None).

식(7a design 2.4, 오라클 `loop_gain` 과 같은 식·같은 부호 규약 -- 근사 없음): 프로브를 지운 절단 회로의 Z(2k×2k, 행 = 관측
V(n_1..n_k), V(x_1..x_k), 열 = 같은 노드 순서의 단위 주입)에서 P = [I; −I], M = Pᵀ·Z·P(프로브에서 본 직렬 임피던스 행렬),
s = [w; 0].
* 1회(전압 주입 V(n) − V(x) = w): i = M⁻¹w, V = Z·P·i, Tv = −wᵀV_x / wᵀV_n.
* 2회(전류 w 를 n 으로 주입, 프로브 0 V): n → x 프로브 전류 I = M⁻¹·Pᵀ·Z·s, Ti = wᵀI / wᵀ(w − I).
* T = (Tv·Ti − 1)/(Tv + Ti + 2).
ω 열 선택: ω > 0 은 전류 열. ω = 0 은 전류 열 중 `dc_charge_injection`(그 노드가 용량 전용)이 없으면 전류 열, 전부면 전하 열
(Tv·Ti 는 Z 의 0차 동차식이라 열마다 같은 배율 s 는 값을 바꾸지 않는다). 섞이면(전도 노드 + 용량 전용 노드 -- 예: gate 쪽 n 과
저항 쪽 x 로 끊은 공통 모드 루프) 열마다 1/s 차수가 달라 Z 의 0차 동차식으로는 극한을 못 낸다: T(0) 은 증강 pencil 의 s = 0 값
(`_helpers_probe._mixed_dc_value` -- 용량 전용 행을 s 로 나누고 프로브 결합을 s 쪽에 둔 식이 선두 차수를 정확히 푼다)으로 낸다.
이 값에는 사후 오차·∂T/∂V 가 없다(오차 0 -- ω = 0 극한 규약, ∂T/∂V None). 극한이 없으면(T(0) 이 원점 극점) 정의 불가
`loop_cut_mixed_charge`.
[CM] 같은 경로가 절단 계의 ω = 0 DC 극한이 특이(`singular_dc_limit` -- 출력 포트 절단처럼 소비자 쪽 전도 섬이 절단 뒤 DC 경로 없이 떠 있음)일 때도 쓰인다:
증강 pencil 은 프로브 전압원 제약이 그 섬을 묶어 s = 0 에서 정칙이다.
M 이 특이(영 피벗)면 `loop_probe_singular`(numeric), Tv·Ti·T 분모 0 은 `den_zero`(definitional).
사후 오차: Z 원소 오차 e(관측 반복 개선 보정량 / 주입 크기)의 1차 전파 Σ|∂T/∂Z|·e. ∂T/∂Z 는 항등식 1/(1 + T) = Q,
Q·wᵀw = wᵀV_n + wᵀ(w − I) 의 해석 미분(dM⁻¹ = −M⁻¹·dM·M⁻¹)이다 -- 상수 없음.
"""
import math

import numpy
import scipy.linalg

from ._helpers_pencil import probe_pencil
from .mna_types import Undefined

_INJECTION_CODE = "dc_charge_injection"
_SINGULAR_CODE = "singular_dc_limit"


def _column_of(cause):
    return dict(cause.detail).get("column")


def _relevant(causes, omega, columns):
    out = []
    for cause in causes:
        detail = dict(cause.detail)
        if detail.get("omega", omega) != omega:
            continue
        if "column" in detail and detail["column"] not in columns:
            continue
        out.append(cause)
    return tuple(out)


def _undefined(code, category, omega, **detail):
    return Undefined("response", code, category, (("omega", omega),) + tuple(sorted(detail.items())))


def _columns(probe, omega, causes):
    """(열 번호 tuple, 주입 크기 tuple) 또는 섞인 절단 표지 (None, 용량 전용 열 tuple)."""
    if omega > 0:
        return probe.current_columns, probe.current_scales
    if any(c.code == _SINGULAR_CODE for c in causes):       # 절단 계의 DC 극한이 특이(절단 뒤 떠 있는 전도 섬 등) -- 증강 pencil 값으로
        return None, ()
    injected = {_column_of(c) for c in causes if c.code == _INJECTION_CODE}
    flags = tuple(j in injected for j in probe.current_columns)
    if not any(flags):
        return probe.current_columns, probe.current_scales
    if all(flags):
        return probe.charge_columns, probe.charge_scales
    return None, tuple(c for c, f in zip(probe.current_columns, flags) if f)


def _mixed_dc_value(system, pairs, weights):
    """T(s → 0) = −H(0)/(H(0) + wᵀw), H(0) = c·a⁻¹·b_g (`_helpers_pencil.probe_pencil` 의 s = 0 식) -- 극한이 없으면(a 특이: T 가 원점 극점을
    가짐, H + wᵀw = 0) None. 절단 노드가 섞여(전도 + 용량 전용) 열 선택으로 Z 의 0차 동차식을 쓸 수 없는 ω = 0 에서 `_helpers_probe`
    가 이 값을 쓴다. 구조 결함(`system.defects`)이 있으면 None."""
    if system.defects:
        return None
    a, _e, ww = probe_pencil(system, pairs, weights)
    full = a.shape[0] - 1
    try:
        lu, piv = scipy.linalg.lu_factor(a[:full, :full])
    except (ValueError, scipy.linalg.LinAlgError):
        return None
    if not numpy.isfinite(lu).all() or not numpy.diag(lu).all():
        return None
    h = float(a[full, :full] @ scipy.linalg.lu_solve((lu, piv), -a[:full, full]))
    return None if not math.isfinite(h) or h + ww == 0 else complex(-h / (h + ww))


def probe_value(probe, omega, values, errors, causes):
    """`probe`(`ProbeFactor` 의 행·열·크기·가중 필드), ω, 관측값 (r, m), 오차 (r, m), 그 점의 사유 tuple ->
    (T 복소 또는 NaN, |T| 사후 오차, 사유 tuple, ∂T/∂V (r, m) 복소 또는 None). 예외를 던지지 않는다.
    ∂T/∂V 는 ∂T/∂Z(아래 해석 미분)를 Z = V[행, 고른 열] / 주입 크기 로 되돌린 것이다(고른 칸 밖은 0)."""
    nan = complex(math.nan, math.nan)
    picked = _columns(probe, omega, causes)
    if picked[0] is None:               # 섞인 절단의 ω = 0: 증강 pencil 의 s = 0 값
        value = _mixed_dc_value(probe.response.system, probe.pairs, probe.weights)
        if value is None:
            return nan, math.nan, (_undefined("loop_cut_mixed_charge", "definitional", omega, charge_only_columns=picked[1]),), None
        return value, 0.0, (), None
    result = _standard_value(probe, omega, picked, errors, values, causes, nan)
    if omega == 0 and not numpy.isfinite(result[0]):
        # [CM] ω = 0 에서 열 선택 방식이 값을 못 내면(절단 뒤 DC 경로 없는 전도 섬 -> Z 특이로 den_zero 등) 증강 pencil 의 s = 0 값으로 대신한다.
        value = _mixed_dc_value(probe.response.system, probe.pairs, probe.weights)
        if value is not None:
            return value, 0.0, (), None
    return result


def _standard_value(probe, omega, picked, errors, values, causes, nan):
    columns, scales = picked
    scale = numpy.array(scales, dtype=float)
    z = numpy.asarray(values)[numpy.ix_(probe.rows, columns)] / scale[None, :]
    e = numpy.asarray(errors)[numpy.ix_(probe.rows, columns)] / numpy.abs(scale)[None, :]
    if not numpy.isfinite(z).all():
        why = _relevant(causes, omega, columns) or (_undefined("response_not_finite", "numeric", omega),)
        return nan, math.nan, why, None
    w = numpy.array(probe.weights, dtype=float)
    k = w.size
    p = numpy.vstack((numpy.eye(k), -numpy.eye(k)))
    s = numpy.concatenate((w, numpy.zeros(k)))
    lu, piv = scipy.linalg.lu_factor(p.T @ z @ p)
    if not numpy.diag(lu).all():
        return nan, math.nan, (_undefined("loop_probe_singular", "numeric", omega),), None
    i_v = scipy.linalg.lu_solve((lu, piv), w.astype(complex))
    v = z @ (p @ i_v)
    den_v = w @ v[:k]
    i_i = scipy.linalg.lu_solve((lu, piv), p.T @ (z @ s))
    g = w @ i_i
    den_i = w @ w - g
    if den_v == 0 or den_i == 0:
        return nan, math.nan, (_undefined("den_zero", "definitional", omega),), None
    t_v = -(w @ v[k:]) / den_v
    t_i = g / den_i
    total = t_v + t_i + 2
    if total == 0:
        return nan, math.nan, (_undefined("den_zero", "definitional", omega),), None
    t = (t_v * t_i - 1) / total
    lam = scipy.linalg.lu_solve((lu, piv), p.T @ (z.T @ s), trans=1)
    mu = scipy.linalg.lu_solve((lu, piv), w.astype(complex), trans=1)
    grad_v = numpy.outer(s - p @ lam, p @ i_v)
    grad_i = numpy.outer(p @ mu, s - p @ i_i)
    grad_t = -((1 + t) ** 2) * (grad_v - grad_i) / (w @ w)
    grad_full = numpy.zeros(numpy.shape(values), dtype=complex)
    grad_full[numpy.ix_(probe.rows, columns)] = grad_t / scale[None, :]
    return complex(t), float(numpy.sum(numpy.abs(grad_t) * e)), (), grad_full
