"""ω → 0 극한 해 -- 용량 전용 노드는 전하 보존으로 정확히 (설계 design_mod1_lut_mod5_mna 3.3 'ω = 0: G 를 LU 분해 1회',
coordinator 결정 2026-10-07 M2).

진입점: `solve_dc_limit`.

(G + sC)·x = BG + s·BC 에서 컨덕턴스가 하나도 닿지 않는 노드 집합 F(`charge_nodes`, 전체 G 행 = 0)의 행은
s·(C_F·x − BC_F) = BG_F 이다. BG_F 는 그 노드에 주입한 전류뿐(G 행이 0 이라 구동 노드 결합이 없다)이므로:
* BG_F = 0 인 열: 양변을 s 로 나눠 극한을 취하면 C_F·x = BC_F (전하 보존, 블록 C_cc·x_c = −C_cr·x_r 의 일반형)이
  정확한 식이다. 나머지 행 R 은 G_R·x = BG_R. 두 묶음을 쌓은 실수 행렬 M 을 LU 1회로 모든 열을 푼다
  (상수·작은 ω 근사 없음 -- 극한 식 자체를 푼다).
* BG_F ≠ 0 인 열: 직류 전류가 용량 노드에 쌓여 극한이 발산 -> 그 열 NaN + `dc_charge_injection`(definitional).
* M 이 특이(영 피벗)면 모든 열 NaN + `singular_dc_limit`(structural).
이 극한은 **소신호** 전달값이다. 용량 전용 노드의 DC 동작점 전압은 MOD5 몫이 아니다(GB7 / spec 선언).
"""
import numpy
import scipy.linalg

from ._helpers_dc import dc_limit_parts
from .mna_types import DcLimit, MnaSystem, Undefined


def solve_dc_limit(system):
    """`MnaSystem` -> `DcLimit`(관측 행 × 열마다 ω → 0 극한 관측값 (r, m), 정의 안 된 열은 NaN + 사유).
    전하 주입 열은 BG_F = 0 이라 F 행이 C_F·x = BC_F 로 그대로 들어간다(새 규칙 없음, `dc_charge_injection` 아님)."""
    if not isinstance(system, MnaSystem):
        raise TypeError("solve_dc_limit 은 MnaSystem 을 받는다")
    nan = numpy.full(system.sense_direct.shape, numpy.nan)
    if system.defects:
        return DcLimit(values=nan, undefined=system.defects)
    n = system.G.shape[0]
    if n == 0:
        return DcLimit(values=system.sense_direct.astype(float))
    matrix, rhs, injected = dc_limit_parts(system)
    lu, piv = scipy.linalg.lu_factor(matrix)
    if not numpy.diag(lu).all():
        nodes = tuple(system.nodes[i] for i in system.charge_nodes)
        return DcLimit(
            values=nan,
            undefined=(Undefined("response", "singular_dc_limit", "structural", (("charge_nodes", nodes),)),),
        )
    x = scipy.linalg.lu_solve((lu, piv), rhs)
    values = system.sense_rows @ x + system.sense_direct
    undefined = []
    for j, nodes in injected:
        values[:, j] = numpy.nan
        undefined.append(
            Undefined("response", "dc_charge_injection", "definitional", (("column", j), ("nodes", nodes)))
        )
    return DcLimit(values=values, undefined=tuple(undefined))
