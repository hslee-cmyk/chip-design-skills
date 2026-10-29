---
id: 20260923-d-delete-dead
phase: 2
evidence_type: equivalence
gate_change: no
approval: 20260923-u02-d-list
---

> **[상태 표지 2026-10-29] 실행·병합 완료 기록 -- 현행 규칙·절차 아님.** 판정 기록 `.ai/verification/20260923-d-delete-dead.json`(FAIL 0)이 있고 이 card의 커밋은 master에 병합됐다. 옛 계획 Phase 2(죽은 코드·DUP 정리) card이고 Phase 2는 폐기됐다(계획 N6.1 '옛 Phase 처리' 2행 -- 새 엔진은 모듈 지도 N3.10으로 처음부터 개념당 정본 하나). 본문의 spec card·interface card·auditor 판정(V1~V10)·DEC-40 승인·R1 절차는 DEC-86으로 폐기했다(계획 N3.12·N4.2, DEC-40 행) -- 현행 완료 조건은 계획 N6.3이다. 본문의 `A`(`skills/analog-gmid-design/assets`) 아래 옛 엔진·test는 `skills/analog-gmid-design/legacy/`로 옮겨졌고(`60727b06`) 새 test 체계(`gmid_engine/tests/`)에서 돌지 않는다. card LT-1(DEC-99)이 `legacy/`를 지운 뒤에는 tag `legacy-final`에만 남는다. 본문은 기록이며 덧대지 않는다(O-169).

## 의도

design `20-dead-code-dup` v1.1 §7·§8 P5: 레지스트리 등급 D 중 **저장소 전체 참조가 0인 7개**와, 그 중 하나만 부르던 `GmIdLUT.junction_cap`을
지운다. 삭제 기준은 §6.4 G-1~G-4이고, "지금 회로가 안 쓴다"가 아니라 **선언으로도 코드로도 도달 경로가 없다**가 근거다.
A = `skills/analog-gmid-design/assets`. 동작 보존 변경이라 판정은 equivalence(E-LIB·E-INST) + GONE + NEW-TOPO다.

## 관찰 가능한 계약

1. 다음 8개 정의가 없어진다.

| 대상 | 위치 | G-2 근거(참조) |
|---|---|---|
| `converge_with_parasitics` | `sizing_recipe.py:126` | 저장소 전체 참조 0 |
| `slew_rate` | `sizing_recipe.py:179` | 0 |
| `SemiEmpiricalGmIdLUT.fT` | `sizing_recipe.py:674` | 0(`.fT(` grep 0건, 동명 지역변수와 구분해 AST로 재측정) |
| `lut_conditions_from_npz` | `sizing_recipe.py:5371` | 0 |
| `suggest_headroom_stack_groups` | `stick_diagram.py:1538` | 0 |
| `render_stick_diagram` | `stick_diagram.py:6901` | 0 |
| `derived_spec` | `workspaces/run_harness.py:374` | 0 |
| `GmIdLUT.junction_cap` | `sizing_recipe.py:76` | 유일한 호출자가 `converge_with_parasitics`(같이 지운다) |

2. **G-1(선언 도달 경로 없음)**: 8개 중 어느 것도 엔진의 어떤 딕셔너리에도 값으로 등록돼 있지 않다(`_METRICS_REGISTRY`·`_CMRR_ESTIMATOR_REGISTRY`·`_PSRR_ESTIMATOR_REGISTRY`·`_COMPENSATION_REGISTRY` 포함 전수). test가 이 사실을 AST로 판정한다 -- 이름이 문자열 키에 묶인 값으로 나타나지 않음.
3. **G-4**: 이 8개는 선언으로 고를 수 없으므로 삭제로 사라지는 선택지가 없다. 대신 test는 **미래 topology가 새 metric type을 선언했을 때 조용히 넘어가지 않고 거부되는지**를 단언한다(`_METRICS_REGISTRY` 미등록 type → `ValueError`, `sizing_recipe.py:5875`).
4. **GONE**: 삭제한 이름이 `A/*.py`·`workspaces/run_harness.py`·`A/tests/**`에서 AST 참조 0.
5. **E-LIB**: library의 로드 가능한 회로 전부에서 `load_topology`·`run_topology_pipeline` 결과가 base와 같다.
6. **E-INST**: 파일럿과 `folded_cascode`의 `instance.json` 키 정렬 sha256이 base와 같다(같은 경로에서 비교).
7. **NEW-TOPO**: 라이브러리에 없는 합성 topology(새 회로 이름·새 넷 이름·소자 수가 다른 넷리스트)로 `load_topology`·`run_topology_pipeline`이 base와 병합본에서 같은 결과를 낸다.
8. 레지스트리 §7에서 이 8행을 같은 커밋에서 지운다(계획 N0.3).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

equivalence: 코드가 줄지만 동작은 같아야 한다. 증거는 E-LIB·E-INST·NEW-TOPO(전후 동일)와 GONE(참조 0).

## oracle 종류와 출처

(c) 동작 보존: 기대값은 base 트리의 실행 결과다(새 기대값을 만들지 않는다). G-1·G-4 판정의 입력은 저장소의 현재 등록 딕셔너리와 합성 선언이다(oracle (a)).

## 거부해야 할 입력

계약 3의 합성 선언: `_METRICS_REGISTRY`에 없는 metric type을 선언한 합성 spec → `ValueError`. 합성으로 이름을 등록한 딕셔너리 → 계약 2의 판정이 실패(판정이 실제로 거부하는지).

## library 회로 적용 여부

적용: E-LIB(로드 가능한 회로 전부)와 E-INST(사이징 스펙이 선언된 회로). 합성 topology는 NEW-TOPO.

## 무동작 판정 입력(무발동 값)

library 회로 전부와 기존 test -- 판정이 base와 같다(삭제가 동작을 바꾸지 않는다).

## 재현할 수치

없음(해시 동일성은 계약 6의 동작 보존 증거).

## 결정 필요 항목

없음(U-02 승인 `20260923-u02-d-list` 1항). F1(삭제 대상이 실은 불린다)이 나오면 그 항목만 '보류'로 옮기고 승인표 개정을 요청한다.

## 변경 이력

- 2026-10-29 `cards/revise-1029`: 위 상태 표지만 더함 -- 본문 불변, 표지 전 원문 = `git show 052465ed:docs/02-design/specs/20260923-d-delete-dead.spec.md`.
