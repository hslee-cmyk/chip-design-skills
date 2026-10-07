"""한 계·한 ω 의 관측값과 LUT 파라미터·ω 에 대한 1차 민감도 -- 수반(adjoint) 풀이 (계획 NFR-5, metrics CONTRACT 9.2).

진입점: `response_sensitivity(system, parameters, omega) -> ResponseSensitivity`.

* 행렬: ω > 0 은 A = G + jωC, 우변 b = BG + jω·BC(`solve_point` 와 같은 식). ω = 0 은 극한 식(용량 전용 노드 행 = 전하 보존,
  `_helpers_dc.dc_limit_parts` -- `solve_dc_limit` 과 같은 행렬). LU 분해 **1회**로 정방향 x = A⁻¹b(모든 열), 반복 개선 1회
  (사후 오차 = |S·dx|, `solve_point` 와 같은 정의), 수반 y = A⁻ᵀSᵀ(관측 행마다) -- 파라미터마다 다시 조립·분해하지 않는다.
* 파라미터 p 의 ∂V/∂p = −yᵀ·(∂A_full/∂p)·x_full: ∂A_full/∂p = 단위 스탬프 항목(`ParameterSet`), x_full = 미지수 해 + 고정 노드
  전압(그 열의 전압 구동 진폭, 교류접지 0) -- 구동 노드로 가는 스탬프(우변 쪽 −A_uf·u)도 이 한 식에 든다. 항목 행이 고정 노드면
  식이 아니라 뺀다. ω > 0 은 C 항목에 jω 를 곱하고, ω = 0 은 용량 전용 노드 행에서 C 항목만·나머지 행에서 G 항목만 쓴다(극한 식의
  미분). 모든 항목을 한 번의 numpy 축약으로 더한다(파라미터 수만큼 풀이하지 않는다).
* ∂V/∂ω(ω > 0) = yᵀ·j(BC − C·x).
* 구조 결함·특이(영 피벗)는 예외 없이 `undefined`(`singular_mna` -- ω > 0, `singular_dc_limit` -- ω = 0). ω = 0 의 전하 주입 열
  (`dc_charge_injection`)은 그 열의 값·민감도가 NaN(`solve_dc_limit` 과 같음).
* 파라미터 항목의 노드가 이 계의 미지수·고정 노드가 아니면 ValueError(다른 회로의 `ParameterSet` -- 배선 결함).
"""
import numpy
import scipy.linalg

from ._helpers_dc import dc_limit_parts
from .mna_types import MnaSystem, ParameterSet, ResponseSensitivity, Undefined


def _check(system, parameters, omega):
    if not isinstance(system, MnaSystem):
        raise TypeError("response_sensitivity 는 MnaSystem 을 받는다")
    if not isinstance(parameters, ParameterSet):
        raise TypeError("response_sensitivity: parameters 는 ParameterSet 이어야 한다")
    omega = float(omega)
    if not numpy.isfinite(omega) or omega < 0:
        raise ValueError("response_sensitivity: ω 는 0 이상 유한해야 한다: %r" % omega)
    return omega


def _full_index(system, parameters):
    """항목 (행 미지수 번호 또는 −1, 열 전체 번호) -- 전체 번호 = 미지수 다음 고정 노드(`build_mna` 의 순서)."""
    order = {node: i for i, node in enumerate(system.nodes + system.fixed_nodes)}
    n = len(system.nodes)
    missing = sorted({int(v) for v in numpy.concatenate((parameters.rows, parameters.cols)) if int(v) not in order})
    if missing:
        raise ValueError("response_sensitivity: 파라미터 스탬프 노드 %r 가 이 계에 없다(다른 회로의 ParameterSet)" % (missing,))
    rows = numpy.array([order[int(v)] if order[int(v)] < n else -1 for v in parameters.rows], dtype=int)
    cols = numpy.array([order[int(v)] for v in parameters.cols], dtype=int)
    return rows, cols


def _drive(system):
    drive = numpy.zeros((len(system.fixed_nodes), len(system.excitations)))
    at = {node: k for k, node in enumerate(system.fixed_nodes)}
    for j, excitation in enumerate(system.excitations):
        for node, amp in excitation.voltages:
            drive[at[node], j] = amp
    return drive


def response_sensitivity(system, parameters, omega):
    """`MnaSystem`, `ParameterSet`(그 계를 만든 회로의 MOS), ω(rad/s, 0 이상) -> `ResponseSensitivity`."""
    omega = _check(system, parameters, omega)
    if system.defects:
        return ResponseSensitivity(omega=omega, undefined=system.defects)
    rows, cols = _full_index(system, parameters)
    n = len(system.nodes)
    r, m = system.sense_direct.shape
    count = len(parameters.params)
    direct = system.sense_direct.astype(complex)
    if n == 0:
        return ResponseSensitivity(omega=omega, values=direct, errors=numpy.zeros((r, m)),
                                   d_param=numpy.zeros((count, r, m), dtype=complex),
                                   d_omega=None if omega == 0 else numpy.zeros((r, m), dtype=complex))
    injected = ()
    if omega > 0:
        a = system.G + complex(0, omega) * system.C
        b = system.BG + complex(0, omega) * system.BC
    else:
        a, b, injected = dc_limit_parts(system)
    lu, piv = scipy.linalg.lu_factor(a)
    if not numpy.diag(lu).all():
        code = "singular_mna" if omega > 0 else "singular_dc_limit"
        category = "numeric" if omega > 0 else "structural"
        return ResponseSensitivity(omega=omega, undefined=(Undefined("response", code, category, (("omega", omega),)),))
    x = scipy.linalg.lu_solve((lu, piv), b)
    dx = scipy.linalg.lu_solve((lu, piv), b - a @ x)
    y = scipy.linalg.lu_solve((lu, piv), system.sense_rows.T.astype(a.dtype), trans=1)
    values = (system.sense_rows @ x + direct).astype(complex)
    errors = numpy.abs(system.sense_rows @ dx)
    full = numpy.vstack((x.astype(complex), _drive(system).astype(complex)))
    if omega > 0:
        coeff = parameters.values * numpy.where(parameters.capacitive, complex(0, omega), 1.0)
    else:
        charge_row = numpy.isin(rows, numpy.array(system.charge_nodes, dtype=int))
        coeff = parameters.values * (parameters.capacitive == charge_row)
    keep = rows >= 0
    contrib = -(coeff[keep][:, None, None] * y[rows[keep]][:, :, None] * full[cols[keep]][:, None, :])
    d_param = numpy.zeros((count, r, m), dtype=complex)
    numpy.add.at(d_param, parameters.owner[keep], contrib)
    d_omega = None
    if omega > 0:
        d_omega = y.T @ (complex(0, 1) * (system.BC - system.C @ x))
    undefined = []
    for j, nodes in injected:
        values[:, j] = numpy.nan
        d_param[:, :, j] = numpy.nan
        undefined.append(Undefined("response", "dc_charge_injection", "definitional", (("column", j), ("nodes", nodes))))
    return ResponseSensitivity(omega=omega, values=values, errors=errors, d_param=d_param, d_omega=d_omega,
                               undefined=tuple(undefined))
