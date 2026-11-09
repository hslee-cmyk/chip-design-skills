# Phase 3 승인 질문 문안 -- design `30-module-split`(초안 v8)

대상: `_drafts/draft_phase3_design_v8.md`, spec card `_drafts/draft_p3_{g1,t0,d0a}.spec.md`, 문서 개정 문안 `_drafts/p3_doc_amendments.md`(새 측정 스크립트 §7 포함, 문안 `_drafts/p3_scripts/e_inst_p3_proposed/e_inst_p3.py`).
**대상 판(5차 검토 m1)**: 질문을 올릴 때 이 파일들의 sha256을 승인 기록 '범위 설명'에 적는다 -- 이 문안 작성 시점 값은 맨 아래 '대상 판 해시'. 질문 전에 파일이 바뀌면 다시 계산한다.
기준 gate `master` `0f23786`(5차 검토 m6): v7은 `a796468`에서 확인했고, `git diff --name-only a796468 0f23786` = 승인 기록 `20261001-p10b-v3-equiv`·P10b spec card 2파일뿐이라
엔진·`tools/`·계획서·레지스트리는 무변경이다(v6 문안의 `7535799`는 작성 시작 시점).
바탕: 3차 검토 `review3_phase3_v5.md` §8, 4차 검토 `review4_phase3_v6.md`, 5차 검토 `review5_phase3_v7.md`('고친 뒤 승인 요청 가능' -- B1·B2·S1~S6·m1~m7을 v8에서 반영).
오케스트레이터가 AskUserQuestion으로 **다섯 질문**을 한 번에 올린다(v8: A2-③ 추가 -- 5차 검토 S3). 각 선택지는 중립으로 쓰고 권고만 (Recommended)로 표시한다.
답을 받은 뒤 승인 기록: UD-0·D-19 → `20260930-30-module-split-design`(`target_kind: diff`, design 30 + 문서 개정 diff + 새 측정 스크립트 -- D-19 답에 맞는 N3.10 MOD2 행 문안), UD-5 → `20260930-p3-gate-move-aware`
(`target_kind: diff`, G1 spec card·design 05 §10·계획 533행), UD-1 → 같은 design 승인 기록의 범위 설명에 U-03 답으로 적는다, **A2-③ → 새 decision 승인 기록**(답이 (가)면 승인 기록 `20260930-b26-before-phase3` ③의 병합 시점 정정, (나)면 순서 변경 기록).

---

> **[Phase 3 design 승인 -- 5건]**
>
> **UD-0. design `30-module-split`(10모듈 분할) 승인**
>
> Phase 3에서 할 일은 네 가지입니다. ① `sizing_recipe.py`·`stick_diagram.py` 등을 계획 N3.10의 10모듈로 **본문을 바꾸지 않고** 옮깁니다(모듈마다 card 1건, 이동 전용 도구로 AST 해시 동일 확인).
> ② 재수출 shim을 거쳐 추적 파일의 import를 갱신합니다. ③ shim과 `sizing_recipe.py`를 지우고, `stick_diagram.py`의 임시 재수출도 지운 뒤 추적 파일이 그 이름을 여전히 찾는지 확인합니다(DoD에 추가 -- 판정을 더하는 쪽).
> ④ MOD10 진입점을 만듭니다. card는 16건이고, phase 3 card(준비 card 포함)는 Phase 2 DoD와 B34·B26-1·B33 병합 뒤에 병합합니다. Phase 3 이동이 시작되면(이관표 확정부터 shim 삭제까지) 엔진 파일·
> 게이트와 이동 도구(`tools/gates`·`tools/migrate`)·레지스트리 목적지 열을 바꾸는 다른 card는 병합하지 않습니다.
> 완료 판정의 전체 test는 phase 3 기준 실행과 DoD 모드 실행 두 번이고, 동작 보존(E-LIB·E-INST)은 Phase 3 이동 직전 판과 비교합니다. 호출부 갱신(F1) 뒤에는 기존 E-INST 측정 스크립트가 돌지 않아,
> 같은 해시를 재는 새 측정 스크립트 하나를 design과 함께 넣습니다(옛 스크립트와 같은 결과임을 완료 판정 때 먼저 확인).
>
> 이 승인이 함께 덮는 문서 개정(문안 첨부 `p3_doc_amendments.md`):
> - 계획 N3.10 표: `load_topology`·`validate_theta_declaration_order` → MOD3(MOD3 구조 유도 함수를 불러 계층상 MOD3), `optimize_full_circuit_budget`는 Phase 3 동안 MOD8(θ 탐색부 추출 뒤 MOD6)
> - 계획 534행 shim 문장(이관 중 잔여 정의 허용, `topology_library`·`design_report` shim 포함), N3.12.3 test-only 목록에 T0·T1
> - `00-common` 진입점에 `topology_path` 인자, `10-test-separation` §5.6 '파일' 열을 설명으로
> - 새 파일 `docs/03-analysis/gain-budget-gmid-sizing-30-module-split/scripts/e_inst_p3.py`(Phase 3 E-INST 측정 스크립트)
>
> **기준에 닿는 기본값 두 가지**(이 승인이 덮습니다):
> - (a) **D-9** -- 계획 534행 "추적 파일 전부 갱신"의 예외: 판정 기록 증거 스크립트(`.ai/verification/**`)와 기준 커밋 측정 원자료 1개(`probe_stage_partition.py`)는 기록 보존을 위해 갱신하지 않으므로,
>   shim과 `stick_diagram` 임시 재수출을 지운 뒤 일부 import가 깨진 채 남습니다(기록된 커밋에서만 재실행). 지금 실측으로 깨지는 것: 원자료 1개(`sizing_recipe` import와 `stick_diagram`에서 읽는 이름 4개),
>   그리고 `stick_diagram`을 import하는 판정 기록 스크립트 8개 중 **F2 뒤 `stick_diagram`에 남지 않는 이름을 읽는 2개**(`e_lib_inst.py`, `diff_dup.py` -- 근사 배정 기준, 정확한 수는 이관표 확정 뒤).
>   나머지 6개(`e_lib.py`)는 깨지지 않습니다.
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
> - **(가) MOD2 `topology_authoring` (Recommended)** -- N3.10 MOD2 '대표 대상'에 이름을 더합니다. 선언 형식을 검사·거부하는 다른 함수(`validate_metric_units` 등)와 같은 곳이고, 다음 card B37a(아직 승인 전)의
>   같은 성격 접근자(`port_declaration`)도 같은 곳에 둘 예정입니다. 계층 위반은 없습니다(MOD3 → MOD2 호출). 다만 선언 순서 검사 `validate_theta_declaration_order`는 규칙상 MOD3로 가므로 선언 검사가 두 모듈에 나뉘는 것은 어느 쪽이든 같습니다.
> - **(나) 규칙대로 MOD3 `circuit_state_graph`** -- 유일한 호출자 `load_topology` 옆입니다. 계획 표에 이 이름을 더하지 않습니다. MOD2의 선언 검사 함수들과는 떨어집니다.
>
> **UD-5. 게이트 변경 G1(옮긴 정의를 '새 정의'로 보지 않게 V3·V6·V7 수정) 승인과 방식**
>
> 지금 게이트는 바이트 그대로 옮긴 함수도 새 함수로 봅니다. 그래서 엔진 이동 card는 변이 약 1.6만 개 때문에 판정할 수 없습니다. 어느 방식이든 약화는 없습니다(합성 반례 51단계 중 거부해야 할 단계는 전부 거부, 실제 엔진 통째 이동의 거짓 거부 0). 계획 533행 한 문장과 design 05 §10 문구도 이 승인이 덮습니다.
> - **(가) 전역 이동 인식 규칙 (Recommended)** -- 게이트 변경 1회로 끝나고, card마다 추가 승인이 없습니다. Phase 3 안에서는 이동 도구가 이관표와 한 번 더 대조합니다.
> - **(나) 승인 기록에 선언한 이동만 인정** -- M card 8건마다 승인 기록이 1건씩 더 필요합니다. 선언 안의 우회(조건부 재정의 등)는 (가)와 같은 규칙으로만 막을 수 있습니다.
> - **보류**
>
> **UD-1. U-03 -- 추적되지 않는 스크립트 `workspaces/current-reuse-telescopic-ota-report/smoke_run_harness_session18_save.py`**
>
> 이 파일은 `sizing_recipe`(`SemiEmpiricalGmIdLUT`·`optimize_full_circuit_budget`)와 `stick_diagram.save_instance_json`을 import합니다(9·10행). shim 삭제 뒤 두 import가 모두 깨집니다.
> (추적 안 된 `.py`는 이것과 `.claude/hooks/*` 4개뿐 -- `0f23786` 실측.)
> - **(가) 깨지게 둠 (Recommended, 계획 기본안)** -- 추적 파일만 갱신합니다.
> - **(나) 지금 저장소에 추가(추적)하고 호출부 갱신 card(F1)에서 함께 갱신**
> - **(다) 삭제** -- 사용자 작업입니다(오케스트레이터는 추적 안 된 사용자 파일을 지우지 않습니다).
>
> **A2-③. B34·B26-1을 병합할 Phase -- 승인 기록과 순서 결정의 충돌(별도 항목)**
>
> 사실: (1) 승인 기록 `20260930-b26-before-phase3` 27·28행 ③은 "B26-1 -- spec card `20260930-b26-rail-accessor-set`을 **Phase 2 진행 중에 병합**하는 것(card `phase: 2`, DF-35·DF-36 선례)"과
> "B34 -- spec card `20260930-b34-grammar-explicit`을 **Phase 2 진행 중에 병합**하는 것(card `phase: 2`)"을 덮습니다. (2) 그 뒤 순서 결정("응, 그렇게 진행해")은 P10b → Phase 2 완료 판정 → V3 card 34·35 → B34 → B26-1,
> 즉 두 card를 **Phase 2 완료 판정 뒤**에 둡니다. (3) 계획 1001행은 "먼저 병합하는 card의 spec card `phase` 값은 병합 시점의 진행 Phase다"라고 적으므로, 완료 판정 뒤 병합이면 `phase`는 3입니다.
> 지금 card 초안 셋(B34·B26-1·앞선 test 보강 card `20260930-b26-pre-test-strengthen`)은 모두 `phase: 2`입니다. (4) 게이트는 card `phase`를 '진행 중인 Phase'와 대조하지 않습니다(`merge_gate.py` 532~549·1008~1010행 실측) --
> 어느 값으로도 통과하므로 맞는 값은 계획 문장과 이 답이 정합니다. (5) Phase 3 판정식은 어느 답이든 같습니다(두 card를 'Phase 3 이동 전 병합 card'로만 다룹니다).
> - **(가) card `phase: 3`, Phase 3 이동 card 전 병합 유지 (Recommended)** -- 순서는 지금 결정대로 두고, 세 card 초안의 `phase`를 3으로 고치며, ③ 문장의 'Phase 2 진행 중'을 'Phase 2 완료 판정 뒤·Phase 3 이동 card 전'으로 고친 것을 **새 decision 승인 기록**으로 남깁니다(옛 기록은 고치지 않음).
> - **(나) B34·B26-1을 Phase 2 완료 판정 앞으로 당겨 `phase: 2` 유지** -- ③ 문장 그대로. Phase 2 완료 판정이 두 card의 효과를 포함하게 되고, 순서 결정 (2)를 바꾸는 기록을 남깁니다.
> - **보류**
>
> (이 충돌은 `_drafts/pending_questions.md` Q-B34-PHASE가 'B34·B26-1·b26pre 착수 전에 함께 묻기'로 이미 추적한다. 이 질문으로 답을 받으면 Q-B34-PHASE를 닫는다 -- 오케스트레이터 몫.)

---

## 질문에 넣지 않은 것(원칙 기본값 -- design 30 §9.3, UD-0이 덮는다)

D-1~D-8·D-10~D-16·D-18·D-20~D-28은 코드 배치·판정 절차이고 회로 해석이 없다(3차 검토 §7). v6에서 더한 것: D-22(M9~F1의 SD ↔ MOD9 임시 순환 대비 import 줄 위치 + 모듈별 단독 import
점검 -- 판정을 더하는 쪽), D-23(phase 3 card 병합 = Phase 2 DoD 뒤), D-24(E3를 AST로 -- 정규식이 놓친 6파일을 잡는 쪽), D-25(M10 진입점 test 회로 = 가장 싼 E-INST 회로, 판정 기준 불변).
v7에서 더한 것: D-26(DoD E3b -- `stick_diagram` 임시 재수출을 지운 뒤 추적 파일이 읽는 이름이 모두 해석되는지, 판정을 더하는 쪽. UD-0 ③ 문장에 반영),
D-27(D0b부터 F2까지 다른 card 병합 금지 -- 오케스트레이터 병합 순서 규칙. B26-2~B26-4·B35는 기본 F2 뒤. UD-0 ④ 문장에 반영).
v8에서 더하거나 고친 것(5차 검토): DoD 전체 test = `PT3`(`--gmid-phase=3`) + `PT3 --gmid-dod`(B1 -- 판정을 더하는 쪽, Phase 2 승인 `20260930-phase2-e4-phase`와 같은 모양, UD-0 ④ 뒤 문장에 반영),
E3b가 star import·동적 이름·파싱 오류를 base에 있어도 FAIL(B2 -- 판정을 더하는 쪽), D-27 동결 범위에 `tools/gates/**`·`tools/migrate/**`·레지스트리 목적지 열(S6 -- UD-0 ④ 문장에 반영),
D-28(Phase 3 E-INST 측정 스크립트 `e_inst_p3.py`를 design 커밋에 고정, DoD가 옛 스크립트와의 동등을 먼저 잼, 동작 보존 비교 판 = Phase 3 이동 직전 판 B0 -- v7의 'Phase 2 DoD와 같은 해시'는
B26-1의 의도된 `load_topology` meta 변경(`rails`)을 셀 수 있어 원리상 성립하지 않았다. UD-0 ④ 뒤 문장과 문서 개정 목록에 반영), D-25 문언(E-INST 회로 집합 안에서 가장 짧은 회로 = `folded_cascode` -- S4).

## 뒤에 올 승인(지금 묻지 않는다)

T0·T1·F1의 V5 승인(test 커밋 뒤 diff 해시로), D0b가 계산하는 추가 N3.10 개정(나오면 -- UD-0 '위임하지 않는 것'),
**M10 V3 생존이 남으면 그 면제 승인**(design 30 §2.3: 생존은 V3 FAIL이고 면제는 사용자 승인 -- 5차 검토 m4).

## 대상 판 해시(v8 작성 완료 시점, sha256 앞 16자리 -- 질문 때 다시 계산해 승인 기록에 적는다)

* `draft_phase3_design_v8.md` `29ae10e99ff4b40d`
* `draft_p3_g1.spec.md` `3a99df21414d6e99`
* `draft_p3_t0.spec.md` `35f7e3e7850a2847`
* `draft_p3_d0a.spec.md` `1f9592d491303132`
* `p3_doc_amendments.md` `c775320e6c2b7e1a`
* `p3_scripts/e_inst_p3_proposed/e_inst_p3.py` `7d26134ad00ec504`
