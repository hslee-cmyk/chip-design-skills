"""루프 이득 T = 인수 곱의 격자 밖 한 점 평가 공용 helper (사용처: `crossing.py`, `phase_lag.py`).

공개 함수: `product_at(factors, omega)` -- ω 한 점의 T 와 |T| 사후 오차와 정의 불가 사유. 같은 계를 쓰는 인수가 여럿이면 그 계는 한 번만 푼다.
"""
import numpy

from .mna_types import Factor
from .point_solve import solve_point


def _check(factors):
    if not isinstance(factors, tuple) or not factors:
        raise TypeError("루프 인수는 비어 있지 않은 Factor tuple 이어야 한다")
    for f in factors:
        if not isinstance(f, Factor):
            raise TypeError("루프 인수 원소는 Factor 여야 한다: %r" % (f,))
        if not 0 <= f.column < len(f.response.system.excitations):
            raise ValueError("Factor.column %r 이 열 범위 밖이다" % (f.column,))
    first = factors[0].response.omegas
    for f in factors[1:]:
        if not numpy.array_equal(f.response.omegas, first):
            raise ValueError("루프 인수들의 ω 격자가 다르다 -- 한 번의 solve_responses 로 함께 풀어야 한다")


def product_at(factors, omega):
    """Factor tuple, ω -> (T(jω), |T| 사후 오차, 사유 tuple). 오차 = |T|·Σ e_i/|F_i|(인수 하나가 0 이면 그 인수 오차 ×
    나머지 곱). 어느 인수 계가 그 ω 에서 정의되지 않으면(특이·결함) T 는 NaN 이고 사유 tuple 이 비어 있지 않다."""
    _check(factors)
    solved = []
    values = []
    errors = []
    undefined = []
    for f in factors:
        system = f.response.system
        point = next((p for s, p in solved if s is system), None)
        if point is None:
            point = solve_point(system, omega)
            solved.append((system, point))
            undefined.extend(point.undefined)
        values.append(complex(point.values[f.column]))
        errors.append(float(point.errors[f.column]))
    total = complex(numpy.prod(values))
    bound = 0.0
    for i, err in enumerate(errors):
        others = numpy.prod([abs(v) for k, v in enumerate(values) if k != i])
        bound += err * others
    return total, float(bound), tuple(undefined)
