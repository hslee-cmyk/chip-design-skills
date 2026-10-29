# interface card: 20260923-probe-promote-consistency

> **[대체 표지 2026-10-29 -- 검증 대기] 대체됨 -- 옛 Phase 폐기(DEC-86, 계획 N6.1 '옛 Phase 처리'), 옛 엔진 card라 재동결 없음(착수하지 않음).** 이 card는 옛 엔진 probe(`legacy/tests/probe_physical_consistency.py`) 승격 card이고 test 커밋·판정 기록이 없다. 새 엔진의 노드 KCL·전파 정합은 봉인 항목(계획 N3.6)이 맡고, 옛 엔진·test는 card LT-1(DEC-99)이 지운다. 본문은 기록이다(O-169).


생성: `tools/gates/interface_card.py`(05-role-separation §11.1). 본문 코드는 넣지 않는다(DEC-38).

## 관찰 가능한 계약

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `sizing_recipe` | `_metric_kcl_residual` | `def _metric_kcl_residual(spec: dict, ctx: SizingContext) -> float` |

### `sizing_recipe._metric_kcl_residual`

> F엔진(2026-09-08, B8) — **내부 노드의 KCL 잔차** `|Sum I_into_node|` 중 최댓값(A).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 변경 이력

- 2026-10-29 `cards/simplify`(검증 대기): 위 대체 표지만 더함 -- 본문 불변, 표지 전 원문 = `git show 07181524:docs/02-design/specs/20260923-probe-promote-consistency.interface.md`.
