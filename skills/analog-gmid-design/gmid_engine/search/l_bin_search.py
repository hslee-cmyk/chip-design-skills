"""L-b: front 점에서 L 칸(bin) 한 칸 이동 국소 탐색 (설계 design_mod6_search_front 4.3, 계획 LR10 (L-b)·LR5).

진입점: `polish_l_cells(sctx, solved, deadline, origin) -> tuple[SolveResult]`(수락된 새 풀이).

* `solved` = front 에 남은 SolveResult(best 가 있는 것). MOS 를 이름순으로 돌며 칸 index ±1(L 칸 표 안)을 시험한다:
  ① 같은 연속 값, L = 새 칸에서 지금 L 에 가장 가까운 끝(위로 가면 lo, 아래로 가면 hi)으로 커널 1회
  ② 받아들일 상태이고 (목적이 줄거나 음의 제약 합이 줄면) 그 칸 벡터로 SLSQP 재시작(같은 최소화 축·같은 ε)
  ③ 재시작 해의 목적 개선이 그 축 분해능 한 칸(정규화 1) 이상이면 수락하고 그 점에서 다음 바퀴를 돈다.
  한 바퀴에 수락이 없으면 끝(유한 칸 표·비증가 -- 종료 보장). 모델 오차 미측정이라 수락은 격자 분해능만으로 판정한 '추정'이다.
* 수락한 새 점은 부르는 쪽이 같은 비지배 필터에 다시 넣는다.
"""
import time

from gmid_engine.sizing import THETA_L

from .kernel import evaluate
from .search_values import ACCEPTED_STATUSES, AXIS_POWER, STAGE_L_SEARCH, StartPoint
from .slsqp_outer import solve_eps


def _objective(sctx, result, axis):
    if axis == AXIS_POWER:
        return result.objectives.power_w / sctx.domain.power_resolution_w
    return result.objectives.area_m2 / sctx.domain.area_resolution_m2


def _violation(result):
    return sum(min(r.c, 0.0) for r in result.constraints)


def polish_l_cells(sctx, solved, deadline, origin):
    accepted = []
    current = solved
    improved = True
    while improved:
        improved = False
        base = current.best
        if time.perf_counter() > deadline:
            break
        cells = dict(zip((m for m, _c in sctx.domain.l_cells), base.key.cells))
        f_base = _objective(sctx, base, current.minimize)
        for mos, table in sctx.domain.l_cells:
            for move in (-1, 1):
                j = cells[mos] + move
                if not 0 <= j < len(table):
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
                if not (_objective(sctx, probe, current.minimize) < f_base or _violation(probe) > _violation(base)):
                    continue
                start = StartPoint("lb:" + mos + ":" + str(move), probe.theta, vector, "l_search")
                result = solve_eps(sctx, start, current.minimize, current.eps, deadline, tag)
                if result.best is None:
                    continue
                if f_base - _objective(sctx, result.best, current.minimize) >= 1:
                    accepted.append(result)
                    current = result
                    improved = True
                    break
            if improved:
                break
    return tuple(accepted)
