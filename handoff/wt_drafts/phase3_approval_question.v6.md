# Phase 3 승인 질문 문안 -- design `30-module-split`(초안 v6)

대상: `_drafts/draft_phase3_design_v6.md`, spec card `_drafts/draft_p3_{g1,t0,d0a}.spec.md`, 문서 개정 문안 `_drafts/p3_doc_amendments.md`. 기준 gate `master` `7535799`.
바탕: 3차 검토 `review3_phase3_v5.md` §8 문안(B1~B4 반영 뒤 올린다는 조건 -- v6에서 반영). 오케스트레이터가 AskUserQuestion으로 네 질문을 한 번에 올린다. 각 선택지는 중립으로 쓰고 권고만 (Recommended)로 표시한다.
답을 받은 뒤 승인 기록: UD-0·D-19 → `20260930-30-module-split-design`(`target_kind: diff`, design 30 + 문서 개정 diff -- D-19 답에 맞는 N3.10 MOD2 행 문안), UD-5 → `20260930-p3-gate-move-aware`
(`target_kind: diff`, G1 spec card·design 05 §10·계획 533행), UD-1 → 같은 design 승인 기록의 범위 설명에 U-03 답으로 적는다.

---

> **[Phase 3 design 승인 -- 4건]**
>
> **UD-0. design `30-module-split`(10모듈 분할) 승인**
>
> Phase 3에서 할 일은 네 가지입니다. ① `sizing_recipe.py`·`stick_diagram.py` 등을 계획 N3.10의 10모듈로 **본문을 바꾸지 않고** 옮깁니다(모듈마다 card 1건, 이동 전용 도구로 AST 해시 동일 확인).
> ② 재수출 shim을 거쳐 추적 파일의 import를 갱신합니다. ③ shim과 `sizing_recipe.py`를 지웁니다. ④ MOD10 진입점을 만듭니다. card는 16건이고, phase 3 card(준비 card 포함)는 Phase 2 DoD 뒤에 병합합니다.
>
> 이 승인이 함께 덮는 문서 개정(문안 첨부 `p3_doc_amendments.md`):
> - 계획 N3.10 표: `load_topology`·`validate_theta_declaration_order` → MOD3(MOD3 구조 유도 함수를 불러 계층상 MOD3), `optimize_full_circuit_budget`는 Phase 3 동안 MOD8(θ 탐색부 추출 뒤 MOD6)
> - 계획 534행 shim 문장(이관 중 잔여 정의 허용, `topology_library`·`design_report` shim 포함), N3.12.3 test-only 목록에 T0·T1
> - `00-common` 진입점에 `topology_path` 인자, `10-test-separation` §5.6 '파일' 열을 설명으로
>
> **기준에 닿는 기본값 두 가지**(이 승인이 덮습니다):
> - (a) **D-9** -- 계획 534행 "추적 파일 전부 갱신"의 예외: 판정 기록 증거 스크립트(`.ai/verification/**`)와 기준 커밋 측정 원자료 1개(`probe_stage_partition.py`)는 기록 보존을 위해 갱신하지 않으므로, shim 삭제 뒤 import가 깨진 채 남습니다(기록된 커밋에서만 재실행).
> - (b) **D-17** -- 모듈 속성을 덮어써 계측하는 probe·진단 스크립트 8개(대입 14줄)는 덮어쓰기 대상을 새 모듈로 옮기고, 호출부 갱신 card의 "import 줄 외 동일" 검사에서 그 대입 줄만 뺍니다(probe 기능 보존).
>
> **위임하지 않는 것**: 이동 도구가 B26-1·B34 병합 뒤 실제 코드에서 위 3건 밖의 계획 표 개정이 필요하다고 계산하면, 그 표 diff는 이 승인에 포함되지 않고 그때 따로 여쭙습니다.
>
> - **승인 (Recommended)** -- 위 범위 그대로. 추가 표 개정은 나오면 다시 묻는다.
> - **승인 + 추가 표 개정 위임** -- 이동 도구가 계산한 표 개정은 다시 묻지 않고 계산 결과대로 반영한다.
> - **수정 요청** -- (a)·(b) 중 바꿀 것을 지정(예: (a) 판정 기록 스크립트도 갱신 / (b) 해당 probe를 'Phase 3 뒤 동작하지 않음'으로 표시).
> - **보류**
>
> **D-19. `rail_declaration`(B26-1의 전원 선언 접근자)을 둘 모듈**
>
> 선언 `supply_nets`의 형식을 검사해 거부하는 함수입니다. 유일한 호출자는 `load_topology`(MOD3로 갑니다).
> - **(가) MOD2 `topology_authoring` (Recommended)** -- N3.10 MOD2 '대표 대상'에 이름을 더합니다. 선언 형식을 검사·거부하는 다른 함수(`validate_metric_units` 등)와 같은 곳이고, 다음 card B37a의 같은 성격 접근자(`port_declaration`)도 같은 곳에 둡니다. 계층 위반은 없습니다(MOD3 → MOD2 호출). 다만 선언 순서 검사 `validate_theta_declaration_order`는 규칙상 MOD3로 가므로 선언 검사가 두 모듈에 나뉘는 것은 어느 쪽이든 같습니다.
> - **(나) 규칙대로 MOD3 `circuit_state_graph`** -- 유일한 호출자 `load_topology` 옆입니다. 계획 표에 이 이름을 더하지 않습니다. MOD2의 선언 검사 함수들과는 떨어집니다.
>
> **UD-5. 게이트 변경 G1(옮긴 정의를 '새 정의'로 보지 않게 V3·V6·V7 수정) 승인과 방식**
>
> 지금 게이트는 바이트 그대로 옮긴 함수도 새 함수로 봅니다. 그래서 엔진 이동 card는 변이 약 1.6만 개 때문에 판정할 수 없습니다. 어느 방식이든 약화는 없습니다(합성 반례 51단계 중 거부해야 할 단계는 전부 거부, 실제 엔진 통째 이동의 거짓 거부 0). 계획 533행 한 문장과 design 05 §10 문구도 이 승인이 덮습니다.
> - **(가) 전역 이동 인식 규칙 (Recommended)** -- 게이트 변경 1회로 끝나고, card마다 추가 승인이 없습니다. Phase 3 안에서는 이동 도구가 이관표와 한 번 더 대조합니다.
> - **(나) 승인 기록에 선언한 이동만 인정** -- M card 8건마다 승인 기록이 1건씩 더 필요합니다. 선언 안의 우회(조건부 재정의 등)는 (가)와 같은 규칙으로만 막을 수 있습니다.
> - **보류**
>
> **UD-1. U-03 -- 추적되지 않는 스크립트 `workspaces/smoke_run_harness_session18_save.py`**
>
> 이 파일은 `sizing_recipe`(`SemiEmpiricalGmIdLUT`·`optimize_full_circuit_budget`)와 `stick_diagram.save_instance_json`을 import합니다. shim 삭제 뒤 두 import가 모두 깨집니다.
> - **(가) 깨지게 둠 (Recommended, 계획 기본안)** -- 추적 파일만 갱신합니다.
> - **(나) 지금 저장소에 추가(추적)하고 호출부 갱신 card(F1)에서 함께 갱신**
> - **(다) 삭제** -- 사용자 작업입니다(오케스트레이터는 추적 안 된 사용자 파일을 지우지 않습니다).

---

## 질문에 넣지 않은 것(원칙 기본값 -- design 30 §9.3, UD-0이 덮는다)

D-1~D-8·D-10~D-16·D-18·D-20~D-25는 코드 배치·판정 절차이고 회로 해석이 없다(3차 검토 §7). v6에서 더한 것: D-22(M9~F1의 SD ↔ MOD9 임시 순환 대비 import 줄 위치 + 모듈별 단독 import
점검 -- 판정을 더하는 쪽), D-23(phase 3 card 병합 = Phase 2 DoD 뒤), D-24(E3를 AST로 -- 정규식이 놓친 6파일을 잡는 쪽), D-25(M10 진입점 test 회로 = 가장 싼 library 회로, 판정 기준 불변).

## 뒤에 올 승인(지금 묻지 않는다)

T0·T1·F1의 V5 승인(test 커밋 뒤 diff 해시로), D0b가 계산하는 추가 N3.10 개정(나오면 -- UD-0 '위임하지 않는 것').
