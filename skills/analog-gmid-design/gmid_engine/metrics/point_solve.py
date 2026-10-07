"""ω 한 점 풀이와 사후 오차 (설계 design_mod1_lut_mod5_mna 3.3 '풀이', 3.4 `ugf_ss_hz` '종료 = MNA 상대 잔차로 구별 불가한 폭').

진입점: `solve_point`.

조립된 `MnaSystem` 을 다시 스탬프하지 않고 A(ω) = G + jωC 를 LU 분해 1회 해서 모든 여기 열을 푼다.
같은 분해로 반복 개선 1회(r = b − A·x, A·dx = r)를 해 관측 보정량 |c·dx| 를 열마다 오차 추정으로 낸다
(분해능 상수 없음 -- 이분 정지 판정이 이 값을 쓴다). ω = 0 은 `solve_dc_limit`(전하 보존 극한, 오차 0 으로 둔다 --
정확한 극한 식의 직접 해). 영 피벗·구조 결함이면 예외 없이 NaN + `undefined`.
"""
import numpy
import scipy.linalg

from .dc_limit import solve_dc_limit
from .mna_types import MnaSystem, PointSolution, Undefined


def solve_point(system, omega):
    """`MnaSystem`, ω(rad/s, 0 이상 유한) -> `PointSolution`(열마다 관측값·오차 추정)."""
    if not isinstance(system, MnaSystem):
        raise TypeError("solve_point 는 MnaSystem 을 받는다")
    omega = float(omega)
    if not numpy.isfinite(omega) or omega < 0:
        raise ValueError("solve_point: ω 는 0 이상 유한해야 한다: %r" % omega)
    m = len(system.excitations)
    nan = numpy.full(m, numpy.nan, dtype=complex)
    if system.defects:
        return PointSolution(omega=omega, values=nan, errors=nan.real, undefined=system.defects)
    if omega == 0:
        limit = solve_dc_limit(system)
        return PointSolution(
            omega=omega, values=limit.values.astype(complex), errors=numpy.zeros(m), undefined=limit.undefined,
        )
    n = system.G.shape[0]
    direct = system.sense_direct.astype(complex)
    if n == 0:
        return PointSolution(omega=omega, values=direct, errors=numpy.zeros(m))
    jw = complex(0, omega)
    a = system.G + jw * system.C
    b = system.BG + jw * system.BC
    lu, piv = scipy.linalg.lu_factor(a)
    if not numpy.diag(lu).all():
        return PointSolution(
            omega=omega, values=nan, errors=nan.real,
            undefined=(Undefined("response", "singular_mna", "numeric", (("omega", omega),)),),
        )
    x = scipy.linalg.lu_solve((lu, piv), b)
    dx = scipy.linalg.lu_solve((lu, piv), b - a @ x)
    values = system.sense_row @ x + direct
    errors = numpy.abs(system.sense_row @ dx)
    return PointSolution(omega=omega, values=values, errors=errors)
