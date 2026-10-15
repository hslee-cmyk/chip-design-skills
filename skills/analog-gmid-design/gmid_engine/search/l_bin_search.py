"""L-b: front 점에서 L 칸(bin) 한 칸 이동 국소 탐색 (설계 design_mod6_search_front 4.3, 계획 LR10 (L-b)·LR5).

진입점: `polish_l_cells(sctx, solved, origin) -> (tuple[SolveResult], str)`(수락된 새 풀이, 정지 사유).

* `solved` = front 에 남은 SolveResult(best 가 있는 것). MOS 를 이름순으로 돌며 칸 index ±1(L 칸 표 안)을 시험한다:
  ① 같은 연속 값, L = 새 칸에서 지금 L 에 가장 가까운 끝(위로 가면 lo, 아래로 가면 hi)으로 커널 1회
  ② 받아들일 상태이고 (목적이 줄거나 음의 제약 합이 줄면) 그 칸 벡터로 SLSQP 재시작(같은 최소화 축·같은 ε)
  ③ 재시작 해의 목적 개선이 그 축 분해능 한 칸(정규화 1) 이상이면 수락하고 그 점에서 다음 바퀴를 돈다.
  한 바퀴에 수락이 없으면 끝(유한 칸 표·비증가 -- 종료 보장). 모델 오차 미측정이라 수락은 격자 분해능만으로 판정한 '추정'이다.
* 분해능: 면적 = b_A, 전력 = 기준점(그 바퀴의 base)의 b_P. 평가 예산(`sctx.eval_budget`)·벽시계(`sctx.deadline`)에 닿으면 끝.
* 수락한 새 점은 부르는 쪽이 같은 비지배 필터에 다시 넣는다.
* **정지 사유**(설계 40 §2.4.13 (5) 'L-b 정지 사유 기록', NFR-4 card 2): 반환 직전에 예산 확인을 **한 번 더** 한다 -- 커널 호출 수 >= 평가 예산이면 `eval_budget`, 아니고 마감이
  지났으면 `wall_budget`, 아니면 `converged`. 끝난 길(while 조건·칸 이동 건너뜀·수락 없는 바퀴)과 무관하게 이 마지막 확인 하나가 사유를 정한다(커널 호출 수는 줄지 않고 벽시계는 단조 증가하므로
  L-b 안 어느 `solve_eps`·칸 이동이 예산에 걸렸으면 끝의 확인도 걸린다). 버려진 `solve_eps` 결과의 정지는 따로 기록하지 않는다.
"""
import time

from gmid_engine.sizing import THETA_L

from .kernel import evaluate
from .search_values import ACCEPTED_STATUSES, AXIS_POWER, STAGE_L_SEARCH, StartPoint
from .slsqp_outer import solve_eps


def _objective(sctx, result, axis, ref):
    if axis == AXIS_POWER:
        return result.objectives.power_w / ref.objectives.power_resolution_w
    return result.objectives.area_m2 / sctx.domain.area_resolution_m2


def _violation(result):
    return sum(min(r.c, 0.0) for r in result.constraints)


def _budget_stop(sctx):
    if sctx.eval_budget is not None and sctx.counters["kernel_calls"] >= sctx.eval_budget:
        return "eval_budget"
    if sctx.deadline is not None and time.perf_counter() > sctx.deadline:
        return "wall_budget"
    return None


def polish_l_cells(sctx, solved, origin):
    accepted = []
    current = solved
    improved = True
    while improved and _budget_stop(sctx) is None:
        improved = False
        base = current.best
        cells = dict(zip((m for m, _c in sctx.domain.l_cells), base.key.cells))
        f_base = _objective(sctx, base, current.minimize, base)
        for mos, table in sctx.domain.l_cells:
            for move in (-1, 1):
                j = cells[mos] + move
                if not 0 <= j < len(table) or _budget_stop(sctx) is not None:
                    continue
                trial_cells = {**cells, mos: j}
                vector = tuple(trial_cells[m] for m, _t in sctx.domain.l_cells)
                lo, hi = table[j]
                theta = dict(base.theta)
                theta[(THETA_L, mos)] = lo if move > 0 else hi
                tag = origin + (("stage", STAGE_L_SEARCH), ("device", mos), ("move", move))
                probe = evaluate(sctx, theta, vector, parent=base, origin=tag)
                if probe.status not in ACCEPTED_STATUSES:
                    continue
                if not (_objective(sctx, probe, current.minimize, base) < f_base or _violation(probe) > _violation(base)):
                    continue
                start = StartPoint("lb:" + mos + ":" + str(move), probe.theta, vector, "l_search")
                result = solve_eps(sctx, start, current.minimize, current.eps, tag)
                if result.best is None:
                    continue
                if f_base - _objective(sctx, result.best, current.minimize, base) >= 1:
                    accepted.append(result)
                    current = result
                    improved = True
                    break
            if improved:
                break
    return tuple(accepted), _budget_stop(sctx) or "converged"
