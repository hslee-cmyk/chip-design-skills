"""front 점 이웃 시험 -- L 칸(bin)과 w_f 칸을 같은 바퀴로 한 칸씩 이동하는 국소 탐색 (설계 design_mod6_search_front 4.3, 계획 LR10 (L-b)·(W-b)·LR5, 설계 40 §3.7-B 7).

진입점: `polish_cells(sctx, solved, origin, wf_cost=None) -> (tuple[SolveResult], str)`(수락된 새 풀이, 정지 사유). `wf_cost` = 호출자가 주는 출력 전용 합산 dict `{"evals": n, "wall_s": s}`(w_f 이동 시험 평가 수와
그 벽시계 -- 결과 JSON `perf` 의 이웃 시험 칸, 없으면 세지 않는다).

* `solved` = front 에 남은 SolveResult(best 가 있는 것). 한 바퀴 순서: ⓐ L 칸 -- MOS 를 이름순으로 칸 index ±1(L 칸 표 안), ⓑ w_f 칸 -- 칸 순서로 칸마다 그 kind 후보(`widths`) 오름차순 목록에서 지금 키의
  바로 아래·바로 위 이웃(목록 끝이면 그쪽 건너뜀). 시험은 탐색 평가 1회(연속 W):
  ① L 이동 = 같은 연속 값, L = 새 칸에서 지금 L 에 가장 가까운 끝(위로 가면 lo, 아래로 가면 hi) / w_f 이동 = 같은 θ·L 칸, 평가 입력 `wf'`(`keys` 한 원소만 이웃 키)
  ② 받아들일 상태이고 (목적이 줄거나 음의 제약 합이 줄면) 그 칸 벡터·그 `wf'` 로 SLSQP 재시작(같은 최소화 축·같은 ε)
  ③ 재시작 해의 목적 개선이 그 축 분해능 한 칸(정규화 1) 이상이면 수락하고 그 점에서 다음 바퀴를 돈다. 수락·종료 규칙은 L 이동과 w_f 이동이 같은 하나다(둘째 수락 규칙 0).
  한 바퀴에 수락이 없으면 끝(유한 칸 표·유한 후보 목록·비증가 -- 종료 보장). 모델 오차 미측정이라 수락은 격자 분해능만으로 판정한 '추정'이다.
* 점의 평가 입력 `wf` 는 그 점 평가 스냅샷에서 읽는다(`point_wf` -- 결과 객체에 사본 칸을 두지 않는다).
* 분해능: 면적 = b_A, 전력 = 기준점(그 바퀴의 base)의 b_P. 탐색 예산(`search_stop` -- `search_ceiling` 의 `kernel_calls` 한도)·벽시계(`sctx.deadline`)에 닿으면 끝(평가 전에 확인).
* 수락한 새 점은 부르는 쪽이 같은 비지배 필터에 다시 넣는다.
* **정지 사유**(설계 40 §2.4.13 (5) 'L-b 정지 사유 기록', NFR-4 card 2): 반환 직전에 예산 확인을 **한 번 더** 한다 -- 커널 호출 수 >= 탐색 예산이면 `eval_budget`, 아니고 마감이
  지났으면 `wall_budget`, 아니면 `converged`. 끝난 길(while 조건·칸 이동 건너뜀·수락 없는 바퀴)과 무관하게 이 마지막 확인 하나가 사유를 정한다(커널 호출 수는 줄지 않고 벽시계는 단조 증가하므로
  바퀴 안 어느 `solve_eps`·칸 이동이 예산에 걸렸으면 끝의 확인도 걸린다). 버려진 `solve_eps` 결과의 정지는 따로 기록하지 않는다.
"""
import time

from gmid_engine.lut import widths
from gmid_engine.sizing import THETA_L, WfInput

from .kernel import evaluate
from .point_wf import point_wf
from .search_stop import search_stop
from .search_values import ACCEPTED_STATUSES, AXIS_POWER, STAGE_L_SEARCH, StartPoint
from .slsqp_outer import solve_eps


def _objective(sctx, result, axis, ref):
    if axis == AXIS_POWER:
        return result.objectives.power_w / ref.objectives.power_resolution_w
    return result.objectives.area_m2 / sctx.domain.area_resolution_m2


def _violation(result):
    return sum(min(r.c, 0.0) for r in result.constraints)


def _trials(sctx, base, wf):
    """한 바퀴의 시험 순서 -- (식별 문자열, 출처 태그 꼬리, θ, L 칸 벡터, 평가 입력, 이동 종류) 열: L 칸 이동 전부, 그다음 w_f 칸 이동(칸 순서, 아래 -> 위)."""
    cells = dict(zip((m for m, _c in sctx.domain.l_cells), base.key.cells))
    for mos, table in sctx.domain.l_cells:
        for move in (-1, 1):
            j = cells[mos] + move
            if not 0 <= j < len(table):
                continue
            vector = tuple({**cells, mos: j}[m] for m, _t in sctx.domain.l_cells)
            lo, hi = table[j]
            theta = dict(base.theta)
            theta[(THETA_L, mos)] = lo if move > 0 else hi
            yield mos + ":" + str(move), (("device", mos), ("move", move)), theta, vector, wf, False
    lut = sctx.dc.lut.memo.lut
    kinds = dict(sctx.dc.base.column("device", "kind"))
    for index, (cell, key) in enumerate(zip(wf.cells_ref, wf.keys)):
        candidates = widths(lut, kinds[cell.members[0]])
        at = candidates.index(key)
        for move in (-1, 1):
            if not 0 <= at + move < len(candidates):
                continue
            moved = WfInput(wf.cells_ref, wf.keys[:index] + (candidates[at + move],) + wf.keys[index + 1:])
            yield "wf" + str(index) + ":" + str(move), (("wf_cell", index), ("move", move)), dict(base.theta), tuple(base.key.cells), moved, True


def polish_cells(sctx, solved, origin, wf_cost=None):
    accepted = []
    current = solved
    improved = True
    while improved and search_stop(sctx) is None:
        improved = False
        base = current.best
        f_base = _objective(sctx, base, current.minimize, base)
        for name, tail, theta, vector, wf, is_wf_move in _trials(sctx, base, point_wf(base.evaluation.snapshot)):
            if search_stop(sctx) is not None:
                continue
            tag = origin + (("stage", STAGE_L_SEARCH),) + tail
            started = time.perf_counter()
            probe = evaluate(sctx, theta, vector, wf, parent=base, origin=tag)
            if is_wf_move and wf_cost is not None:
                wf_cost["evals"] += 1
                wf_cost["wall_s"] += time.perf_counter() - started
            if probe.status not in ACCEPTED_STATUSES:
                continue
            if not (_objective(sctx, probe, current.minimize, base) < f_base or _violation(probe) > _violation(base)):
                continue
            start = StartPoint("lb:" + name, probe.theta, vector, wf, "l_search")
            result = solve_eps(sctx, start, current.minimize, current.eps, tag)
            if result.best is None:
                continue
            if f_base - _objective(sctx, result.best, current.minimize, base) >= 1:
                accepted.append(result)
                current = result
                improved = True
                break
    return tuple(accepted), search_stop(sctx) or "converged"
