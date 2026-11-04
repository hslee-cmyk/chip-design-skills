"""탐색 예산 -- 탐색(층 0·시작점·외층·ε·L-b)이 쓸 수 있는 커널 평가 수와 유도 전이 한 자리 (설계 40 §2.4.14 C 행, 사용자 결정 X-8·X-15~X-17).

진입점: `search_ceiling(sctx, *, final=False) -> int | None` (탐색 예산, 유도 전이 전이면 None).

* 선언 실행(`sctx.eval_budget_source == "declared"`): 탐색 예산 = E_B(`sctx.eval_budget`) 그대로. 작은 E_B 도 거부하지 않는다(X-17).
* 유도 실행(`settings.eval_budget` None): D = ⌊front_budget_s / 평가 시간 중앙값⌋(`EvalBudget.limit()`), 탐색 예산 = D − R(R = `gate_reserve`).
  유도 전이는 평가 시간이 n_θ + 1개 이상일 때 **첫 n_θ + 1개**로 D 를 한 번 내서 `sctx.eval_budget`·`eval_budget_source` 에 기록한다(`kernel.evaluate` 는 쓰지 않는다).
  전이 호출에서 `kernel_calls` ≥ D − R 이면 `ValueError`(`time_budget_below_search_reserve` -- 탐색 예산이 이미 소진, 게이트 예약 R 을 지킬 수 없다).
* `final=True`(`find_front` 가 게이트 전에 한 번): 평가 시간이 1개 이상이면 그 전부로 유도한다. `kernel_calls` > D − R 이면 `ValueError`.
* 전이 뒤 호출에서 `kernel_calls` > 탐색 예산이면 `RuntimeError`(탐색이 정지 확인 없이 평가했다 -- 결함). 선언 실행은 이 검사가 없다(`search_stop` 이 사유로 읽는다).
* 숫자의 유일한 계산 자리다. 소비자: `search_stop`, `layer0_center`, `slsqp_outer`, `eps_sweep`, `residual_probe`, `find_front`.
"""
from ._helpers_ceiling import gate_reserve
from .eval_budget import EvalBudget


def _derive(sctx, final):
    times = sctx.eval_times
    n = len(sctx.domain.variables)
    if len(times) < (1 if final else n + 1):
        return None
    used = list(times) if final else list(times[:n + 1])
    d = EvalBudget(sctx.settings.front_budget_s, used).limit()
    if d is None:
        return None
    room = d - gate_reserve(sctx)
    calls = sctx.counters["kernel_calls"]
    if calls > room if final else calls >= room:
        raise ValueError("time_budget_below_search_reserve: kernel_calls=" + str(calls) + " 가 탐색 예산 D − R = " + str(room)
                         + " 에 이미 닿았다(D=" + str(d) + ", R=" + str(gate_reserve(sctx)) + ")")
    sctx.eval_budget = d
    sctx.eval_budget_source = "derived_once:floor(B/median_t_eval)@n_evals=" + str(len(times))
    return room


def search_ceiling(sctx, *, final=False):
    if sctx.eval_budget is None:
        return _derive(sctx, final)
    if sctx.eval_budget_source == "declared":
        return sctx.eval_budget
    room = sctx.eval_budget - gate_reserve(sctx)
    if sctx.counters["kernel_calls"] > room:
        raise RuntimeError("search_ceiling: kernel_calls=" + str(sctx.counters["kernel_calls"]) + " 가 탐색 예산 " + str(room) + " 을 넘었다")
    return room
