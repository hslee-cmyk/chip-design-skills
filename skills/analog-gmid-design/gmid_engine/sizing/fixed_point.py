"""순환 블록 Gauss-Seidel 고정점과 수렴·비수렴 판정 (계획 N3.6, SC-c, 설계 3.4).

진입점: `gauss_seidel(nodes, values, update, tolerance, width, devices=()) -> (values, (k, deltas, tol, K_max))`.

* `nodes`: 갱신 순서(쓰기 계획 순서). `values`: {노드: V} 시작값(바깥 노드 포함, 이 함수가 복사해 쓴다).
* `update(node, values) -> V`: 그 노드 writer 식(최신 값을 읽는다 -- Gauss-Seidel).
* `tolerance(values) -> tol`: 현재 반복값에서의 허용오차(V, 양수). `width`: 상한 계산 구간 폭(V).
* 매 반복 Δk = max |변화|. Δk ≤ tol 이면 수렴. k ≥ 3 부터 q = Δk/Δk−1: q < 1 이면
  q^(K_max − k)·Δk/(1 − q) > tol 일 때(남은 상한 안 도달 불가 확정), 그리고 q 와 무관하게 k ≥ K_max 일 때 `NonconvergentError`
  (margin = Δk/tol). K_max 는 매 반복의 tol 로 다시 잰다(`k_max`). 창 크기·연속 횟수 상수 없음.
"""
from gmid_engine.core import NonconvergentError

from .k_max import k_max

_MIN_RATIO_ITERATIONS = 2 + 1                          # q 추정에 필요한 최소 반복 수 3(N3.6)


def gauss_seidel(nodes, values, update, tolerance, width, devices=()):
    current = dict(values)
    deltas = []
    k = 0
    while True:
        k += 1
        delta = 0.0
        for node in nodes:
            new = update(node, current)
            delta = max(delta, abs(new - current[node]))
            current[node] = new
        deltas.append(delta)
        tol = tolerance(current)
        limit = k_max(width, tol)
        if delta <= tol:
            return current, (k, tuple(deltas), tol, limit)
        stop = k >= limit
        if k >= _MIN_RATIO_ITERATIONS and deltas[-2] > 0:
            q = delta / deltas[-2]
            if q < 1:
                stop = stop or (q ** max(limit - k, 0)) * delta / (1 - q) > tol
        if stop:
            raise NonconvergentError(devices=tuple(devices), margin=delta / tol,
                                     detail={"nodes": tuple(nodes), "iterations": k, "deltas": tuple(deltas),
                                             "tol": tol, "k_max": limit})
