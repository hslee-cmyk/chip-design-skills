"""극점·영점 -- 일반화 고유값 (설계 design_mod1_lut_mod5_mna 3.3 'ω 격자': (G, −C) 고유값과 증강 pencil 영점, 7a design 4.1 3.4 행).

진입점: `pencil_roots`.

* 극점: det(G + sC) = 0 의 유한 근 = pencil (G, −C) 고유값.
* 관측 행 r · 열 j 의 영점: [[G + sC, −(bg + s·bc)], [c_r, d_rj]] 가 특이한 유한 s = pencil (A, −E) 고유값,
  A = [[G, −bg], [c_r, d_rj]], E = [[C, −bc], [0, 0]].
* 순수 전하 열(전압·전류 진폭 없이 전하만 주입)은 영점을 계산하지 않는다(빈 tuple): 그 전달함수는 같은 노드 전류 열의
  s 배라 영점 = 전류 열 영점 ∪ {0} 이고, 원점은 격자에서 빠진다 -- 더할 꺾임점이 없다. 그런 열은 `Factor` 로 쓰지 않는다.
* 유한·원점 판정은 `_helpers_pencil.finite_eigs`(QZ 동차 좌표, 상수 없음).
* 이 값은 **격자 배치와 상단 괄호에만** 쓴다. metric 값(교차·위상)은 실제 풀이로 잰다(옛 SR:4104 docstring 의
  관측·제어 불가 모드 문제를 피한다).
"""
import numpy

from ._helpers_pencil import finite_eigs
from .mna_types import MnaSystem, Roots


def _charge_only(excitation):
    return not excitation.voltages and not excitation.currents


def pencil_roots(system):
    """`MnaSystem` -> `Roots`(유한 극점, 관측 행 × 열마다 유한 영점). 정렬은 (크기, 실부, 허부) -- 결정론."""
    if not isinstance(system, MnaSystem):
        raise TypeError("pencil_roots 는 MnaSystem 을 받는다")
    rows = len(system.senses)
    if system.defects:
        return Roots(poles=(), zeros=tuple(tuple(() for _ in system.excitations) for _ in range(rows)))
    g, c = system.G, system.C
    n = g.shape[0]
    poles = finite_eigs(g, c)
    zeros = []
    for r in range(rows):
        row_zeros = []
        for j, excitation in enumerate(system.excitations):
            if _charge_only(excitation):
                row_zeros.append(())
                continue
            a = numpy.zeros((n + 1, n + 1))
            e = numpy.zeros((n + 1, n + 1))
            a[:n, :n] = g
            a[:n, n] = -system.BG[:, j]
            a[n, :n] = system.sense_rows[r]
            a[n, n] = system.sense_direct[r, j]
            e[:n, :n] = c
            e[:n, n] = -system.BC[:, j]
            row_zeros.append(finite_eigs(a, e))
        zeros.append(tuple(row_zeros))
    return Roots(poles=poles, zeros=tuple(zeros))
