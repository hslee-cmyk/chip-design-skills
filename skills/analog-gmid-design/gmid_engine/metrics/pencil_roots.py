"""극점·영점 -- 일반화 고유값 (설계 design_mod1_lut_mod5_mna 3.3 'ω 격자': (G, −C) 고유값과 증강 pencil 영점).

진입점: `pencil_roots`.

* 극점: det(G + sC) = 0 의 유한 근 = pencil (G, −C) 고유값.
* 열 j 의 영점: [[G + sC, −(bg + s·bc)], [c, d]] 가 특이한 유한 s = pencil (A, −E) 고유값,
  A = [[G, −bg], [c, d]], E = [[C, −bc], [0, 0]].
* '유한' 판정은 상수가 아니라 QZ 동차 좌표 (α, β)로 한다: |β| ≤ 차원·기계 엡실론·‖E‖_F 이면 무한대(β 가 반올림
  오차 수준) -- 특이 pencil 의 불확정 고유값(α·β 모두 반올림 수준)도 같은 판정으로 빠진다.
* 이 값은 **격자 배치와 상단 괄호에만** 쓴다. metric 값(교차·위상)은 실제 풀이로 잰다(옛 SR:4104 docstring 의
  관측·제어 불가 모드 문제를 피한다).
"""
import numpy
import scipy.linalg

from .mna_types import MnaSystem, Roots


def _finite_eigs(a, e):
    size = a.shape[0]
    if size == 0:
        return ()
    alpha, beta = scipy.linalg.eig(a, -e, right=False, homogeneous_eigvals=True)
    eps = numpy.finfo(float).eps
    tol_beta = size * eps * numpy.linalg.norm(e)
    out = []
    for al, be in zip(alpha, beta):
        if abs(be) <= tol_beta:
            continue
        out.append(complex(al / be))
    return tuple(sorted(out, key=lambda z: (abs(z), z.real, z.imag)))


def pencil_roots(system):
    """`MnaSystem` -> `Roots`(유한 극점, 열마다 유한 영점). 정렬은 (크기, 실부, 허부) -- 결정론."""
    if not isinstance(system, MnaSystem):
        raise TypeError("pencil_roots 는 MnaSystem 을 받는다")
    if system.defects:
        return Roots(poles=(), zeros=tuple(() for _ in system.excitations))
    g, c = system.G, system.C
    n = g.shape[0]
    poles = _finite_eigs(g, c)
    zeros = []
    for j in range(len(system.excitations)):
        a = numpy.zeros((n + 1, n + 1))
        e = numpy.zeros((n + 1, n + 1))
        a[:n, :n] = g
        a[:n, n] = -system.BG[:, j]
        a[n, :n] = system.sense_row
        a[n, n] = system.sense_direct[j]
        e[:n, :n] = c
        e[:n, n] = -system.BC[:, j]
        zeros.append(_finite_eigs(a, e))
    return Roots(poles=poles, zeros=tuple(zeros))
