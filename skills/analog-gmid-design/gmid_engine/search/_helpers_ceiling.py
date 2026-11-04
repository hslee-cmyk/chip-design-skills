"""E_total·감도 게이트 예약 R 의 계산 자리 하나 (설계 40 §2.4.5 '상한'·§2.4.14 C 행, 사용자 결정 X-8·X-15~X-17).

진입점: `gate_reserve(sctx) -> int`, `e_total(sctx) -> int | None`. 이 모듈은 값을 계산할 뿐 어디에도 보관하지 않는다(graph 단일 정본: 사본·cache 없음).

* R = `gate_reserve` = 2 × 탐색 변수 수(감도 게이트의 FD 묶음 상계 -- 방향 2).
* E_total = `e_total` = 선언 실행(`sctx.eval_budget_source == "declared"`)이면 E_B + R, 유도 실행이면 D(= `sctx.eval_budget`), 예산이 아직 없으면 None.
  (N_T 항은 LA-1 범위 15 (g) `layer0_budget` 이 더한다 -- 이 card 에는 없다.)
* 소비자: `search_ceiling`(탐색 예산 = E_total − R 또는 E_B), `gate_run`(게이트 묶음 `ceiling`), `find_front`(색인 상한 `total_of`·`perf.block_index_bound`).
"""


def gate_reserve(sctx):
    return 2 * len(sctx.domain.variables)


def e_total(sctx):
    if sctx.eval_budget is None:
        return None
    if sctx.eval_budget_source == "declared":
        return sctx.eval_budget + gate_reserve(sctx)
    return sctx.eval_budget
