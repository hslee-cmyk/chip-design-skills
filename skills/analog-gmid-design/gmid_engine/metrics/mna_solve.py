"""주파수 응답 풀이 (설계 design_mod1_lut_mod5_mna 3.3 '풀이(`mna_solve.py`)').

진입점: `solve_responses`.

* 계마다 극점·영점(`pencil_roots`)을 한 번 구하고, 모든 계의 근으로 공유 ω 격자(`omega_grid`)를 만든다
  (루프 인수들이 같은 격자 위에서 곱해진다).
* ω = 0: G 를 LU 분해 1회 해서 모든 여기 열(구동 열 + 전류 주입 열)을 한 번에 푼다(실수 해).
* ω > 0: 격자 전체를 (k, n, n) 묶음 `G + jωC` 로 만들어 `numpy.linalg.solve` 한 번에 푼다(재스탬프 없음).
* 특이: DC 경로 없는 노드(`dc_floating`)는 DC 풀이 전에 거부, ω 묶음 풀이가 특이면 그 ω 를 찾아 함께 거부.
"""
import numpy
import scipy.linalg

from gmid_engine.core import StructureUnresolvedError

from .mna_types import MnaSystem, SystemResponse
from .omega_grid import omega_grid
from .pencil_roots import pencil_roots
from .point_solve import solve_point


def _dc_values(system):
    n = system.G.shape[0]
    if n == 0:
        return system.sense_direct.astype(float)
    if system.dc_floating:
        raise StructureUnresolvedError(
            detail={"reason": "dc_floating_node", "nodes": system.dc_floating, "omega": 0.0}
        )
    lu, piv = scipy.linalg.lu_factor(system.G)
    if not numpy.diag(lu).all():
        raise StructureUnresolvedError(detail={"reason": "singular_mna", "omega": 0.0})
    x = scipy.linalg.lu_solve((lu, piv), system.BG)
    return system.sense_row @ x + system.sense_direct


def _ac_values(system, omegas):
    n = system.G.shape[0]
    m = len(system.excitations)
    if not omegas.size:
        return numpy.zeros((0, m), dtype=complex)
    if n == 0:
        return numpy.broadcast_to(system.sense_direct.astype(complex), (omegas.size, m)).copy()
    jw = omegas[:, None, None] * complex(0, 1)
    a = system.G[None, :, :] + jw * system.C[None, :, :]
    b = system.BG[None, :, :] + jw * system.BC[None, :, :]
    try:
        x = numpy.linalg.solve(a, b)
    except numpy.linalg.LinAlgError:
        for omega in omegas:
            solve_point(system, omega)
        raise
    return numpy.einsum("n,knm->km", system.sense_row, x) + system.sense_direct[None, :]


def solve_responses(systems):
    """`MnaSystem` tuple -> 같은 순서의 `SystemResponse` tuple(공유 ω 격자, 첫 행 ω = 0)."""
    if not isinstance(systems, tuple) or not systems:
        raise TypeError("solve_responses 는 비어 있지 않은 MnaSystem tuple 을 받는다")
    for s in systems:
        if not isinstance(s, MnaSystem):
            raise TypeError("solve_responses: 원소는 MnaSystem 이어야 한다: %r" % (s,))
    roots = tuple(pencil_roots(s) for s in systems)
    grid = numpy.array(omega_grid(roots))
    out = []
    for system, r in zip(systems, roots):
        dc = _dc_values(system)
        ac = _ac_values(system, grid[1:])
        values = numpy.vstack((dc.astype(complex)[None, :], ac))
        out.append(SystemResponse(system=system, roots=r, omegas=grid, values=values))
    return tuple(out)
