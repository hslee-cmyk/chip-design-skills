"""루프 이득 T = 인수 곱의 공용 helper (사용처: `crossing.py`, `phase_lag.py`, `loop_analysis.py`).

공개 함수:
* `check_factors(factors)` -- 인수 tuple 검사(형식 `Factor`·`ProbeFactor`, 행·열 범위, 순수 전하 열 금지, 같은 ω 격자).
* `product_at(factors, omega)` -- ω 한 점의 T 와 |T| 사후 오차와 정의 불가 사유. 같은 계를 쓰는 인수가 여럿이면 그 계는
  한 번만 푼다. 인수 공통 규약(metrics CONTRACT 3.8·3.9): `PointSolution` → (복소값, 사후 오차, 사유) --
  `Factor` 는 그 (행, 열) 원소, `ProbeFactor` 는 `_helpers_probe.probe_value`(Middlebrook 식).
"""
import numpy

from ._helpers_probe import probe_value
from .mna_types import Factor, ProbeFactor
from .point_solve import solve_point


def check_factors(factors):
    """인수 tuple 검사 -- 위반은 TypeError·ValueError(배선 결함). 통과하면 첫 인수의 공유 격자를 돌려준다."""
    if not isinstance(factors, tuple) or not factors:
        raise TypeError("루프 인수는 비어 있지 않은 Factor·ProbeFactor tuple 이어야 한다")
    for f in factors:
        if isinstance(f, ProbeFactor):
            continue
        if not isinstance(f, Factor):
            raise TypeError("루프 인수 원소는 Factor 또는 ProbeFactor 여야 한다: %r" % (f,))
        system = f.response.system
        if not 0 <= f.column < len(system.excitations):
            raise ValueError("Factor.column %r 이 열 범위 밖이다" % (f.column,))
        if not 0 <= f.row < len(system.senses):
            raise ValueError("Factor.row %r 이 관측 행 범위 밖이다" % (f.row,))
        excitation = system.excitations[f.column]
        if not excitation.voltages and not excitation.currents:
            raise ValueError("Factor 열 %r 은 순수 전하 열이다 -- 루프 인수로 쓰지 않는다(ProbeFactor 내부 전용)"
                             % (excitation.name,))
    first = factors[0].response.omegas
    for f in factors[1:]:
        if not numpy.array_equal(f.response.omegas, first):
            raise ValueError("루프 인수들의 ω 격자가 다르다 -- 한 번의 solve_responses 로 함께 풀어야 한다")
    return first


def product_at(factors, omega):
    """인수 tuple, ω -> (T(jω), |T| 사후 오차, 사유 tuple). 오차 = |T|·Σ e_i/|F_i|(인수 하나가 0 이면 그 인수 오차 ×
    나머지 곱). 어느 인수 계가 그 ω 에서 정의되지 않으면(특이·결함·프로브 사유) T 는 NaN 이고 사유 tuple 이 비어 있지 않다."""
    check_factors(factors)
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
        if isinstance(f, ProbeFactor):
            value, err, why = probe_value(f, float(omega), point.values, point.errors, point.undefined)
        else:
            value, err, why = point.values[f.row, f.column], point.errors[f.row, f.column], point.undefined
        undefined.extend(u for u in why if u not in undefined)
        values.append(complex(value))
        errors.append(float(err))
    total = complex(numpy.prod(values))
    bound = 0.0
    for i, err in enumerate(errors):
        others = numpy.prod([abs(v) for k, v in enumerate(values) if k != i])
        bound += err * others
    return total, float(bound), tuple(undefined)
