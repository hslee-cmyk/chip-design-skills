"""순환 블록 Gauss-Seidel 고정점과 수렴·비수렴 판정 (계획 N3.6, SC-c, 설계 3.4).

진입점: `gauss_seidel(nodes, values, update, tolerance, width, devices=()) -> (values, (k, deltas, tol, K_max))`.

* `nodes`: 갱신 순서(쓰기 계획 순서). `values`: {노드: V} 시작값(바깥 노드 포함, 이 함수가 복사해 쓴다).
* `update(node, values) -> V`: 그 노드 writer 식(최신 값을 읽는다 -- Gauss-Seidel).
* `tolerance(values) -> tol`: 현재 반복값에서의 허용오차(V, 양수). `width`: 상한 계산 구간 폭(V).
* 매 반복 Δk = max |변화|. 수렴 = 노드전압 오차 상계 ≤ tol(r7, 노드전압이 정본이라 Δ 만으로 받지 않는다): Δk = 0(정확한
  고정점)이거나, k ≥ 3 부터 q = Δk/Δk−1 < 1 이고 m = max(1, q/(1 − q))·Δk ≤ tol(사후 상계 q/(1−q)·Δk 와 마지막 걸음 Δk
  둘 다 tol 안 -- q < 1/2 이면 r6 의 Δk ≤ tol 과 같다). q ≥ 1 이면 Δk 가 작아도 받지 않는다. q < 1 이고 K_max 에서의 같은 양
  q^(K_max − k)·m > tol 이면(남은 상한 안 도달 불가 확정), 그리고 q 와 무관하게 k ≥ K_max
  이면 `NonconvergentError`(margin = Δk/tol). K_max 는 매 반복의 tol 로 다시 잰다(`k_max`). 창 크기·연속 횟수 상수 없음.
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
        if delta == 0:                                 # 정확한 고정점 -- 오차 상계 0
            return current, (k, tuple(deltas), tol, limit)
        stop = k >= limit
        if k >= _MIN_RATIO_ITERATIONS and deltas[-2] > 0:
            q = delta / deltas[-2]
            if q < 1:
                # 사후 오차 상계 ‖V_k − V*‖∞ ≤ q/(1−q)·Δk 와 마지막 걸음 Δk(봉인 1·2 가 tol 로 재는 잔차 쪽) 둘 다 tol 안
                measure = max(1, q / (1 - q)) * delta
                if measure <= tol:
                    return current, (k, tuple(deltas), tol, limit)
                # K_max 반복에서의 같은 양 q^(K_max−k)·measure 도 tol 을 넘으면 남은 상한 안 도달 불가 확정
                stop = stop or (q ** max(limit - k, 0)) * measure > tol
        if stop:
            raise NonconvergentError(devices=tuple(devices), margin=delta / tol,
                                     detail={"nodes": tuple(nodes), "iterations": k, "deltas": tuple(deltas),
                                             "tol": tol, "k_max": limit})
