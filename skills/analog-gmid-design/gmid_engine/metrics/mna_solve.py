"""주파수 응답 풀이 (설계 design_mod1_lut_mod5_mna 3.3 '풀이(`mna_solve.py`)').

진입점: `solve_responses`.

* 계마다 극점·영점(`pencil_roots`)을 한 번 구하고, 모든 계의 근으로 공유 ω 격자(`omega_grid`)를 만든다
  (루프 인수들이 같은 격자 위에서 곱해진다 -- 루프 절단 계와 포트 전달 계도 한 번에 함께 푼다, 7a design 2.4 '격자').
* ω = 0: `solve_dc_limit` -- LU 1회로 모든 여기 열(구동 열 + 전류 주입 열 + 전하 주입 열), 용량 전용 노드는 전하 보존 극한.
* ω > 0: 격자 전체를 (k, n, n) 묶음 `G + jωC` 로 만들어 `numpy.linalg.solve` 한 번에 푼다(재스탬프 없음).
  묶음 풀이가 특이면 점마다 `solve_point` 로 다시 풀어 특이한 ω 만 NaN + 사유로 남긴다.
* 응답 모양 (k, r, m) = (ω, 관측 행, 여기 열).
* 예외를 던지지 않는다: 구조 결함·특이·극한 발산은 값 NaN + `undefined`.
"""
import numpy

from .dc_limit import solve_dc_limit
from .mna_types import MnaSystem, SystemResponse
from .omega_grid import omega_grid
from .pencil_roots import pencil_roots
from .point_solve import solve_point


def _ac_values(system, omegas):
    n = system.G.shape[0]
    shape = system.sense_direct.shape
    if not omegas.size:
        return numpy.zeros((0,) + shape, dtype=complex), ()
    if system.defects:
        return numpy.full((omegas.size,) + shape, numpy.nan, dtype=complex), ()
    if n == 0:
        return numpy.broadcast_to(system.sense_direct.astype(complex), (omegas.size,) + shape).copy(), ()
    jw = omegas[:, None, None] * complex(0, 1)
    a = system.G[None, :, :] + jw * system.C[None, :, :]
    b = system.BG[None, :, :] + jw * system.BC[None, :, :]
    try:
        x = numpy.linalg.solve(a, b)
    except numpy.linalg.LinAlgError:
        points = tuple(solve_point(system, omega) for omega in omegas)
        return numpy.stack([p.values for p in points]), tuple(u for p in points for u in p.undefined)
    return numpy.einsum("rn,knm->krm", system.sense_rows, x) + system.sense_direct[None, :, :], ()


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
        limit = solve_dc_limit(system)
        ac, ac_undefined = _ac_values(system, grid[1:])
        values = numpy.concatenate((limit.values.astype(complex)[None, :, :], ac))
        out.append(SystemResponse(
            system=system, roots=r, omegas=grid, values=values, undefined=limit.undefined + ac_undefined,
        ))
    return tuple(out)
