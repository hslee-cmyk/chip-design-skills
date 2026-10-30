# interface card: 20260930-df36-instance-relpath

> **[상태 표지 2026-10-29] 실행·병합 완료 기록 -- 현행 규칙·절차 아님.** 판정 기록 `.ai/verification/20260930-df36-instance-relpath.json`(FAIL 0)이 있고 이 card의 커밋은 master에 병합됐다. 옛 계획 Phase 2(죽은 코드·DUP 정리) card이고 Phase 2는 폐기됐다(계획 N6.1 '옛 Phase 처리' 2행 -- 새 엔진은 모듈 지도 N3.10으로 처음부터 개념당 정본 하나). 본문의 spec card·interface card·auditor 판정(V1~V10)·DEC-40 승인·R1 절차는 DEC-86으로 폐기했다(계획 N3.12·N4.2, DEC-40 행) -- 현행 완료 조건은 계획 N6.3이다. 본문의 `A`(`skills/analog-gmid-design/assets`) 아래 옛 엔진·test는 `skills/analog-gmid-design/legacy/`로 옮겨졌고(`60727b06`) 새 test 체계(`gmid_engine/tests/`)에서 돌지 않는다. card LT-1(DEC-99)이 `legacy/`를 지운 뒤에는 tag `legacy-final`에만 남는다. `run_harness.py`는 지금 `legacy/workspaces/`에 있다. 본문은 기록이며 덧대지 않는다(O-169).

생성: `tools/gates/interface_card.py`(05-role-separation §11.1). 본문 코드는 넣지 않는다(DEC-38).

## 관찰 가능한 계약

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `stick_diagram` | `save_instance_json` | `def save_instance_json(path: str, topology_json_path: str, sizing_results: dict, pipeline_result: dict) -> None` |

### `stick_diagram.save_instance_json`

> instance-output JSON 작성 — `pipeline_result`(`run_topology_pipeline()`의 반환값, 또는
> 독립된 물리 cell이 여러 개인 회로라면 §6.9 아래 문단처럼 직접 조립한 동일 스키마의 dict)를
> 손대지 않고 그대로 옮겨 쓴다(§1 표 5번 원칙: 함수 반환값 그대로, 손으로 축약/재구성 금지).
> `sizing_results`는 `{name: {"W":..., "L":..., "ID":..., "gm":..., "gm_id":...}}` 형태를
> 기대한다(sizing_recipe.py의 SizingResult 필드명 그대로).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 변경 이력

- 2026-10-29 `cards/revise-1029`: 위 상태 표지만 더함 -- 본문 불변, 표지 전 원문 = `git show 052465ed:docs/02-design/specs/20260930-df36-instance-relpath.interface.md`.
