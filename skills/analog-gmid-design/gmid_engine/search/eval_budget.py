"""평가 예산 N_T (설계 41 §5.8 DEC-34 식, 40 §11 U13 `eval_budget.py`; 41 §8 `class EvalBudget`).

진입점: `EvalBudget(wall_s, times, reserve_evals=0)`.

N_T = floor((B − T_used − T_reserve) / t_eval)

* B = `wall_s`(`wall_clock_budget_s` / `front_budget_s`), `times` = 지금까지 잰 평가 시간 목록(호출자의 `eval_times` 를 그대로 참조 -- 이 객체는 복사하지 않는다), t_eval = 그 중앙값
  (첫 평가가 끝나기 전에는 정의되지 않는다 -> `limit()`·`remaining()` 이 None), T_used = Σ times, T_reserve = `reserve_evals` · t_eval(외층 최소 비용 = 끝점 2개 ×
  as-built `slsqp_outer` maxiter 식 Σ⌈log2(폭/h)⌉ 평가 수 -- 부르는 쪽이 센다. 외층 예약분은 **한 번만** 뺀다, N4).
* `limit()` = 총 평가 수 한도 = floor(B / t_eval) − reserve_evals(T_used 를 빼기 전의 같은 식 -- 이미 쓴 평가도 한도 안에 센다). `remaining()` = max(0, limit() − len(times)) = 지금부터의
  N_T(평가 시간이 균일할 때 정의 식과 같다). 두 값 모두 평가 수라 같은 입력이면 같은 정수다(결정론, 벽시계는 입력으로만 들어온다).
* as-built 소비자: `kernel.evaluate` 가 평가 한 sweep(n + 1) 뒤 한 번 `limit()` 로 E_B 를 정한다(reserve_evals = 0 -- 층 0 gain 예산 U15 가 들어오기 전). U15 `layer0_budget` 이 `remaining()` 을 읽는다.
"""
import statistics


class EvalBudget:
    def __init__(self, wall_s, times, reserve_evals=0):
        if not wall_s > 0:
            raise ValueError("EvalBudget: wall_s 는 양수여야 한다: " + repr(wall_s))
        if reserve_evals < 0:
            raise ValueError("EvalBudget: reserve_evals 는 음수일 수 없다: " + repr(reserve_evals))
        self.wall_s = wall_s
        self.times = times
        self.reserve_evals = int(reserve_evals)

    def t_eval(self):
        """평가 시간 중앙값(s). 평가가 하나도 없으면 None."""
        return statistics.median(self.times) if self.times else None

    def limit(self):
        t = self.t_eval()
        if t is None or not t > 0:
            return None
        return max(0, int(self.wall_s / t) - self.reserve_evals)

    def remaining(self):
        total = self.limit()
        return None if total is None else max(0, total - len(self.times))
