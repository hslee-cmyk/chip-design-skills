"""결합 잔차 측정 (설계 41 §2.4 단계 B1, 체크리스트 D-BM) -- 준난수 θ 표본에서 블록 분해 잔차 r̂ 와 r̂_spread.

진입점: `residual_probe(sctx, count) -> ResidualProbe`.

* 표본: `count`(= spec `search.dof_rank_sample_count`)개의 Halton 점(소수 기저, index 1 부터, 스크램블 없음)을 θ 연속 변수 중 **전류가 아닌** 성분(L 칸 안 값·ln IDu·수동소자 값)의
  자연 좌표(bounds 위 선형, ln 변수는 ln 좌표) 전체 구간에 놓고, 전류 성분은 `centre_start` 의 KCL 원뿔 안 중심값에 둔다(전류까지 상자에서 뽑으면 원뿔 밖 점이 대부분이라 표본이
  봉인 점이 되지 못한다). 평가 커널(`evaluate`)을 돌리고 **봉인을 통과한 점**(`ACCEPTED_STATUSES`)에서 그 점의 `block_residual` 보고(`metrics_aux` 필드)의 `gain_residual_db` 를 잰다.
* 정지: 봉인 표본이 `count`개 모이거나, 평가 예산(`sctx.eval_budget` -- 커널 호출 수)에 닿거나, 예산이 선언되지 않았으면 시험 `count`번. 상자 전체 Halton 점은 대부분 봉인되지 않으므로
  (표본 수율은 회로에 달렸다) 예산이 정지 조건이고, 표본이 `count` 보다 적으면 `stop` 에 사유를 남긴다 -- 층 0 은 r̂ 가 없으면(`count` 0) 조합 순서를 잔차 없이 정한다.
* 산출 `ResidualProbe`: `summary`(metrics `coupled_residual` -- r̂ = 중앙값, r̂_spread = 최대 − 최소, 표본 수), `evaluated`(평가한 점 수), `values`(잔차 열). 
* 쓰임은 층 0 조합 순서뿐이다(41 §5.6) -- 상한이 보장되지 않아 판정에는 쓰지 않는다(M2). 구조 입력(`sctx.structure`)이 없거나 전달 뷰 제약이 없으면 보고가 없어 표본 0.
"""
import dataclasses
import math

from gmid_engine.metrics import REPORT_BLOCK_RESIDUAL, coupled_residual
from gmid_engine.sizing import METRICS_KEY, THETA_CURRENT

from .kernel import evaluate
from .layer0_center import centre_start
from .search_values import ACCEPTED_STATUSES

AUX_FIELD = "metrics_aux"
RESIDUAL_KEY = "gain_residual_db"


@dataclasses.dataclass(frozen=True)
class ResidualProbe:
    """`residual_probe` 결과. `summary` = metrics `CoupledResidual`, `evaluated` = 평가한 점 수, `values` = 잰 잔차 dB tuple, `stop` = 정지 사유(`enough`·`eval_budget`·`trials`)."""

    summary: object
    evaluated: int
    values: tuple
    stop: str


def _primes(count):
    found, k = [], 1
    while len(found) < count:
        k += 1
        if all(k % p for p in found):
            found.append(k)
    return found


def _radical_inverse(index, base):
    value, scale = 0.0, 1.0 / base
    while index:
        index, digit = divmod(index, base)
        value += digit * scale
        scale /= base
    return value


def _residual_of(result):
    """평가 결과의 블록 잔차 dB(보고 없음 -> None). 전달 뷰가 둘 이상이면 절댓값이 가장 큰 쪽(보수적)."""
    snapshot = result.evaluation.snapshot
    try:
        bundle = snapshot.value("graph", METRICS_KEY, AUX_FIELD)
    except KeyError:
        return None
    values = [dict(rep)[RESIDUAL_KEY] for name, rep in bundle.reports if name == REPORT_BLOCK_RESIDUAL and dict(rep)[RESIDUAL_KEY] is not None]
    return max(values, key=abs) if values else None


def residual_probe(sctx, count):
    variables, theta, cells, _centre_u = centre_start(sctx)
    free = [v for v in variables if v.component[0] != THETA_CURRENT]
    bases = _primes(len(free))
    values, evaluated, stop = [], 0, "enough"
    k = 0
    while len(values) < count:
        if sctx.eval_budget is not None and sctx.counters["kernel_calls"] >= sctx.eval_budget:
            stop = "eval_budget"
            break
        if sctx.eval_budget is None and k >= count:
            stop = "trials"
            break
        k += 1
        point = dict(theta)
        for var, base in zip(free, bases):
            value = var.lo + _radical_inverse(k, base) * (var.hi - var.lo)
            point[var.component] = math.exp(value) if var.log else value
        result = evaluate(sctx, point, cells)
        evaluated += 1
        if result.status in ACCEPTED_STATUSES and result.evaluation is not None:
            residual = _residual_of(result)
            if residual is not None:
                values.append(residual)
    return ResidualProbe(coupled_residual(values), evaluated, tuple(values), stop)
