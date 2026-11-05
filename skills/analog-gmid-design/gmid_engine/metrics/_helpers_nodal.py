"""ω → 0 노달 풀이 공용 helper -- 용량 행렬 조립, LU 1회, 정방향·수반 풀이 (사용처: `offset_analysis`, `block_model`, `block_residual`).

공개 함수: `capacitance_matrix`, `nodal_factor`, `nodal_solve`, `nodal_adjoint`.

* `conductance_matrix`(G 조립)는 `ss_nodal.py` 에 있다(G·g_bound 의 조립 자리는 `ss_nodal` 한 곳).
* 정의 = ω → 0 극한 KCL(설계 41 §2.5, 40 §3.8). 전도 경로가 있는 노드는 컨덕턴스 행 `G·v = i`, 용량 전용 노드(전도 단자가 없고 용량만 닿는 노드)는 전하 보존 행
  `C·v = q`(`_helpers_dc.limit_matrix` 가 G 사본의 그 행을 C 행으로 바꾼다 -- `solve_dc_limit` 과 같은 식이다). 용량 전용 노드를 0 V 로 채우지 않는다.
* `capacitance_matrix(circuit, size)` -> (size, size) 실수 C -- `capacitors` 와 MOS 다섯 용량(cgs·cgd·cgb·cdb·csb, 단자 쌍 스탬프).
* `nodal_factor(g, fixed, *, c)` -> 튜플 `(unknown, lu, piv, coupling, floating, charge)`: `c` 는 반드시 준다(생략 = TypeError -- 용량을 조용히 빼지 않는다).
  - `charge` = 비고정 노드 중 G 행이 0 이고 C 행이 0 이 아닌 것(전하 보존 행으로 푸는 미지수).
  - `floating` = G 행·C 행이 모두 0 이고 비고정 행의 어떤 G 열·C 열 항목도 없는 비고정 노드(0 V 가 값에 영향 없음).
  - `unknown` = 고정도 floating 도 아닌 노드(charge 포함) 정수 배열. G 행·C 행이 모두 0 인데 다른 비고정 행이 그 노드를 읽으면(예: gate 만 닿은 노드) 행이 0 이라 미지수에 남아 `lu` 가 None(특이).
  - `coupling` = `limit_matrix` 행렬의 [unknown, 전체] 블록(고정 노드 구동 항).
* `nodal_solve(factor, size, drive, injection)` -> (전압 벡터 (size,), 상대 잔차). 고정 노드 전압 = `drive`({노드: V}, 없으면 0),
  `injection` = {노드: 들어가는 전류 A} -- 전하 노드에 주입하면 직류 전류가 쌓여 극한이 없다: (None, None). 잔차 = ‖G_uu·x − b‖₂ / max(‖b‖₂, 부동소수 최소량) -- LU 의 수치 정밀도 진단(감도 게이트의 ε).
* `nodal_adjoint(factor, size, sense)` -> (z (size,)): `sense` = 관측 벡터(출력 y = sense·v). 노드 n 에 단위 전류를 넣었을 때의 y = z[n]. 고정 노드는 0, 전하 노드는 NaN(전류 주입이 정의되지 않는다).
  한 번의 LU 로 모든 주입 노드의 y 를 얻는다.
"""
import sys

import numpy
import scipy.linalg

from ._helpers_dc import limit_matrix
from .stamp_mos import mos_stamps
from .stamp_two_terminal import two_terminal_stamps


def _assemble(stamp_sets, key, size):
    out = numpy.zeros((size, size))
    for stamp in stamp_sets:
        for row, col, value in getattr(stamp, key):
            out[row, col] += value
    return out


def capacitance_matrix(circuit, size):
    """`SmallSignalCircuit`(정수 노드 < size) -> (size, size) 실수 C -- `capacitors` 와 MOS 다섯 용량."""
    return _assemble(tuple(two_terminal_stamps(k) for k in circuit.capacitors) + tuple(mos_stamps(m) for m in circuit.mos), "c", size)


def nodal_factor(g, fixed, *, c):
    """G (n, n), 고정 노드 집합, C (n, n) -> `(unknown, lu, piv, coupling, floating, charge)`(모듈 문서)."""
    size = g.shape[0]
    c = numpy.asarray(c)
    fixed_set = frozenset(int(f) for f in fixed)
    free = [i for i in range(size) if i not in fixed_set]
    g_row, c_row = g.any(axis=1), c.any(axis=1)
    read = g[free, :].any(axis=0) | c[free, :].any(axis=0)                     # 비고정 행이 이 노드(열)를 읽는다
    floating = tuple(i for i in free if not (g_row[i] or c_row[i] or read[i]))
    charge = tuple(i for i in free if not g_row[i] and c_row[i])
    unknown = numpy.array([i for i in free if i not in floating], dtype=int)
    matrix = limit_matrix(g, c, charge)
    coupling = matrix[unknown, :]
    if unknown.size == 0:
        return unknown, None, None, coupling, floating, charge
    lu, piv = scipy.linalg.lu_factor(matrix[numpy.ix_(unknown, unknown)])
    if not numpy.diag(lu).all():
        lu = None
    return unknown, lu, piv, coupling, floating, charge


def nodal_solve(factor, size, drive=None, injection=None):
    """정방향 풀이. -> (전압 (size,), 상대 잔차) -- 특이하거나 전하 노드에 전류를 주입하면 (None, None)."""
    unknown, lu, piv, coupling, _floating, charge = factor
    volt = numpy.zeros(size)
    for node, amount in (drive or {}).items():
        volt[node] = amount
    if any(node in charge for node in (injection or {})):
        return None, None
    if unknown.size == 0:
        return volt, 0.0
    if lu is None:
        return None, None
    inject = numpy.zeros(size)
    for node, amount in (injection or {}).items():
        inject[node] = amount
    rhs = inject[unknown] - coupling @ volt                # 고정 노드 전압 항(미지수 열은 아직 0)
    x = scipy.linalg.lu_solve((lu, piv), rhs)
    volt[unknown] = x
    norm = numpy.linalg.norm(rhs)
    matrix = coupling[:, unknown]
    return volt, float(numpy.linalg.norm(matrix @ x - rhs) / max(norm, sys.float_info.min))


def nodal_adjoint(factor, size, sense):
    """수반 풀이. -> z (size,) 또는 특이하면 None. 고정 노드 0, 전하 노드 NaN."""
    unknown, lu, piv, _coupling, _floating, charge = factor
    z = numpy.zeros(size)
    if unknown.size == 0:
        return z
    if lu is None:
        return None
    z[unknown] = scipy.linalg.lu_solve((lu, piv), numpy.asarray(sense, dtype=float)[unknown], trans=1)
    z[list(charge)] = numpy.nan
    return z
