"""결합 잔차 측정 요약 r̂, r̂_spread (설계 41 §2.4 단계 B1, 체크리스트 D-BM).

진입점: `coupled_residual(residuals_db) -> CoupledResidual`.

표본 = 봉인을 통과한 준난수 θ 점마다 `block_residual` 이 낸 `gain_residual_db`(dB)다(점을 평가하는 일은 `search.residual_probe`). 산출: r̂ = 중앙값,
r̂_spread = 최대 − 최소. 쓰임은 층 0 조합 순서뿐이다 -- 상한이 보장되지 않으므로 판정에는 쓰지 않는다(M2). 정의 안 된 잔차(None)와 비유한 값은 표본에서 뺀다.
"""
import math
import statistics

from .aux_types import CoupledResidual


def coupled_residual(residuals_db):
    values = [float(r) for r in residuals_db if r is not None and math.isfinite(r)]
    if not values:
        return CoupledResidual(None, None, 0)
    return CoupledResidual(statistics.median(values), max(values) - min(values), len(values))
