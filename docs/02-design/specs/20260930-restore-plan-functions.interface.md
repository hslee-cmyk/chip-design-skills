# interface card: 20260930-restore-plan-functions

> **[상태 표지 2026-10-29] 실행·병합 완료 기록 -- 현행 규칙·절차 아님.** 판정 기록 `.ai/verification/20260930-restore-plan-functions.json`(FAIL 0)이 있고 이 card의 커밋은 master에 병합됐다. 옛 계획 Phase 2(죽은 코드·DUP 정리) card이고 Phase 2는 폐기됐다(계획 N6.1 '옛 Phase 처리' 2행 -- 새 엔진은 모듈 지도 N3.10으로 처음부터 개념당 정본 하나). 본문의 spec card·interface card·auditor 판정(V1~V10)·DEC-40 승인·R1 절차는 DEC-86으로 폐기했다(계획 N3.12·N4.2, DEC-40 행) -- 현행 완료 조건은 계획 N6.3이다. 본문의 `A`(`skills/analog-gmid-design/assets`) 아래 옛 엔진·test는 `skills/analog-gmid-design/legacy/`로 옮겨졌고(`60727b06`) 새 test 체계(`gmid_engine/tests/`)에서 돌지 않는다. card LT-1(DEC-99)이 `legacy/`를 지운 뒤에는 tag `legacy-final`에만 남는다. 본문의 DEC-26 인용('`canonical_spec()`만 정본')은 옛 문언이다 -- 현행 DEC-26은 회로 spec 파일(`<name>.sizing_spec.json`) 하나가 정본이고 옛 `canonical_spec()`은 옛 엔진 전용이다. 본문의 `A/sky130_nfet_pfet_lut_sample.npz`는 O-180이 지우기로 했다(LUT는 v2 r2 묶음만) -- LUT 정리(브랜치 `data/lut-v2-only`) 병합 전에는 `assets/`에 있고 병합 뒤에는 git 이력에만 있다. 본문은 기록이며 덧대지 않는다(O-169).

생성: `tools/gates/interface_card.py`(05-role-separation §11.1). 본문 코드는 넣지 않는다(DEC-38).

## 관찰 가능한 계약

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `run_harness` | `canonical_spec` | `def canonical_spec(circuit_key: str) -> dict` |
| `sizing_recipe` | `require_declared_spec_source` | `def require_declared_spec_source(topology_path: str, spec: dict) -> None` |

### `run_harness.canonical_spec`

> 이 회로의 **정본 spec**을 준다 -- 조사 스크립트가 써야 할 기본 진입점(2026-09-10).

### `sizing_recipe.require_declared_spec_source`

> 라이브러리 회로를 사이징할 때 spec의 **출처 선언**을 강제한다(2026-09-10).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `sizing_recipe` | `lut_conditions_from_npz` | `def lut_conditions_from_npz(npz_data) -> dict` |
| `run_harness` | `derived_spec` | `def derived_spec(circuit_key: str, why: str, **overrides) -> dict` |

## 변경 이력

- 2026-10-29 `cards/revise-1029`: 위 상태 표지만 더함 -- 본문 불변, 표지 전 원문 = `git show 052465ed:docs/02-design/specs/20260930-restore-plan-functions.interface.md`.
