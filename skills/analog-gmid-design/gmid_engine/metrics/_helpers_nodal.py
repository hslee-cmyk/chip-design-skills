"""ω → 0 노달 풀이 공용 helper -- 컨덕턴스 행렬 조립, LU 1회, 정방향·수반 풀이 (사용처: `offset_analysis`, `block_model`, `ff_gm_ratio`, `block_residual`).

공개 함수: `conductance_matrix`, `nodal_factor`, `nodal_solve`, `nodal_adjoint`.

* 소신호 DC 극한(용량은 열린 회로)의 노달 식 `G·v = i` 만 푼다. `build_mna` 의 `solve_dc_limit` 은 용량 전용 노드를 전하 보존 식으로
  바꾸는 일반형이고, 여기는 **전도 경로가 있는 노드**의 실수 연립만 필요한 곳(소자 전달 임피던스·블록 국소 해·FF 단락 전류)에 쓴다.
  컨덕턴스가 하나도 안 닿은 노드(KCL 식이 없는 노드)는 미지수에서 빼고 전압 0 으로 둔다(`floating`) -- 값이 정의되지 않는 노드를
  임의로 채우지 않고, 부르는 쪽이 `floating` 으로 영향 여부를 본다.
* `nodal_factor(g, fixed)` -> `NodalFactor` 대신 튜플 `(unknown, lu, piv, coupling, floating)`: `unknown` = 미지수 노드(고정 아닌 노드 중 G 행이 0
  이 아닌 것) 정수 배열, `lu`·`piv` = 그 부분행렬의 LU(특이하면 `lu` 가 None), `coupling` = G[unknown, fixed 전체] 블록(고정 노드 구동 항),
  `floating` = 제외한 노드 tuple.
* `nodal_solve(factor, size, drive, injection)` -> (전압 벡터 (size,), 상대 잔차). 고정 노드 전압 = `drive`({노드: V}, 없으면 0),
  `injection` = {노드: 들어가는 전류 A}. 잔차 = ‖G_uu·x − b‖₂ / max(‖b‖₂, 부동소수 최소량) -- LU 의 수치 정밀도 진단(감도 게이트의 ε).
* `nodal_adjoint(factor, size, sense)` -> (z (size,)): `sense` = 관측 벡터(출력 y = sense·v). 노드 n 에 단위 전류를 넣었을 때의 y = z[n].
  고정 노드는 0. 한 번의 LU 로 모든 주입 노드의 y 를 얻는다.
"""
import sys

import numpy
import scipy.linalg

from .stamp_mos import mos_stamps
from .stamp_two_terminal import two_terminal_stamps


def _gamma(count, unit_roundoff):
    """γ_m = m·u / (1 − m·u) (m = 연산 수, γ_0 = 0) -- 부동소수 연산 m 번 누적 오차의 상대 상계(Higham 식 γ_m)."""
    return count * unit_roundoff / (1 - count * unit_roundoff)


def conductance_matrix(circuit, size, *, bound=False):
    """`SmallSignalCircuit`(정수 노드 < size) -> (size, size) 실수 G -- MOS(gm·gmb·gds)와 저항. 용량은 DC 극한에서 열린 회로라 넣지 않는다.

    `bound=True` 면 `(G, g_bound)`: g_bound 는 G 조립 오차의 항목별 상계 E_ij = γ_{max(k_ij−1, 0)}·S_ij + C_ij + γ_{n+1}·|Ĝ_ij|
    (S_ij = Σ|ĝ_s|, k_ij = 항목의 스탬프 항 수, C_ij = Σ γ_{c_s}·|ĝ_s|, c_s = 스탬프 항의 연산 수 `StampSet.g_ops`, n = size, Ĝ = 계산된 G, u = ε/2;
    값 0 항목은 스탬프에서 빠지므로 세지 않는다). 스탬프가 없는 항목은 0. 기본 `False` 면 G 하나(옛 소비자 값 불변)."""
    g = numpy.zeros((size, size))
    stamps = tuple(mos_stamps(m) for m in circuit.mos) + tuple(two_terminal_stamps(r) for r in circuit.resistors)
    terms = {}
    for stamp in stamps:
        for (row, col, value), ops in zip(stamp.g, stamp.g_ops):
            g[row, col] += value
            terms.setdefault((row, col), []).append((value, ops))
    if not bound:
        return g
    unit_roundoff = sys.float_info.epsilon / 2
    g_bound = numpy.zeros((size, size))
    for (row, col), items in terms.items():
        magnitude = sum(abs(value) for value, _ops in items)
        stamp_error = sum(_gamma(ops, unit_roundoff) * abs(value) for value, ops in items)
        g_bound[row, col] = (_gamma(max(len(items) - 1, 0), unit_roundoff) * magnitude + stamp_error
                             + _gamma(size + 1, unit_roundoff) * abs(g[row, col]))
    return g, g_bound


def nodal_factor(g, fixed):
    """G (n, n), 고정 노드 집합 -> `(unknown, lu, piv, coupling, floating)`(모듈 문서)."""
    size = g.shape[0]
    fixed_set = frozenset(int(f) for f in fixed)
    connected = g.any(axis=1)
    unknown = numpy.array([i for i in range(size) if i not in fixed_set and connected[i]], dtype=int)
    floating = tuple(i for i in range(size) if i not in fixed_set and not connected[i])
    coupling = g[unknown, :]
    if unknown.size == 0:
        return unknown, None, None, coupling, floating
    lu, piv = scipy.linalg.lu_factor(g[numpy.ix_(unknown, unknown)])
    if not numpy.diag(lu).all():
        lu = None
    return unknown, lu, piv, coupling, floating


def nodal_solve(factor, size, drive=None, injection=None):
    """정방향 풀이. -> (전압 (size,), 상대 잔차) -- 특이하면 (None, None)."""
    unknown, lu, piv, coupling, _floating = factor
    volt = numpy.zeros(size)
    for node, amount in (drive or {}).items():
        volt[node] = amount
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
    """수반 풀이. -> z (size,) 또는 특이하면 None."""
    unknown, lu, piv, _coupling, _floating = factor
    z = numpy.zeros(size)
    if unknown.size == 0:
        return z
    if lu is None:
        return None
    z[unknown] = scipy.linalg.lu_solve((lu, piv), numpy.asarray(sense, dtype=float)[unknown], trans=1)
    return z
