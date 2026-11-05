"""탐색 정지 사유 한 자리 (설계 40 §2.4.14 C 행; 층 0·외층·L-b·residual_probe·start_points 의 정지 정의 셋을 대체한다).

진입점: `search_stop(sctx) -> "eval_budget" | "wall_budget" | None`.

* `kernel_calls` ≥ 탐색 예산(`search_ceiling`) -> `"eval_budget"`. `sctx.deadline` 이 지났으면 `"wall_budget"`. 그 밖 None.
* 탐색 단계의 단일 평가는 평가 **전에** 이 함수를 본다(`kernel_calls` = 탐색 예산 − 1 이면 평가, = 탐색 예산이면 평가 안 함).
* 유도 전이 전에 불리면 `search_ceiling` 이 전이를 일으킬 수 있다(그때 `ValueError` 가 날 수 있다).
"""
import time

from .search_ceiling import search_ceiling


def search_stop(sctx):
    ceiling = search_ceiling(sctx)
    if ceiling is not None and sctx.counters["kernel_calls"] >= ceiling:
        return "eval_budget"
    if sctx.deadline is not None and time.perf_counter() > sctx.deadline:
        return "wall_budget"
    return None
