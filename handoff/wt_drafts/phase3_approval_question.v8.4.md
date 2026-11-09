# Phase 3 승인 질문 문안 -- design `30-module-split`(초안 v8.4)

대상: `_drafts/draft_phase3_design_v8.md`, spec card `_drafts/draft_p3_{g1,t0,d0a}.spec.md`, 문서 개정 문안 `_drafts/p3_doc_amendments.md`(새 측정 스크립트 §7·§8 포함, 문안 `_drafts/p3_scripts/e_inst_p3_proposed/e_inst_p3.py`·`_drafts/p3_scripts/e_lib_p3_proposed/e_lib_p3.py`).
**대상 판(5차 검토 m1)**: 질문을 올릴 때 이 파일들의 sha256을 승인 기록 '범위 설명'에 적는다 -- 이 문안 작성 시점 값은 맨 아래 '대상 판 해시'. 질문 전에 파일이 바뀌면 다시 계산한다.
기준 gate `master` **`dd60db6`**(`git -C <repo> rev-parse gate/master`, v8.4): `0f23786..dd60db6` = P10b 병합·md 일치 card·**Phase 2 완료 판정 기록 `2eefda1`(대상 H = `5f643a9`, PASS -- 아래 (c)의 'Phase 2 완료 판정 대상 커밋' = `5f643a9`)**·백로그·V3 면제 묶기(34) 문서·spec·승인이고
엔진 `A/*.py`·`tools/`·N3.10 표·레지스트리 목적지 열은 무변경이다(계획서는 839행 N4.2 V3 한 줄, 레지스트리는 §8 덧붙임 -- design 30 부록 A F1v84; 문서 개정 '현재' 블록 `dd60db6`에서 일치). v8.3까지는 `0f23786`.
바탕: 3차 검토 `review3_phase3_v5.md` §8, 4차 검토 `review4_phase3_v6.md`, 5차 검토 `review5_phase3_v7.md`('고친 뒤 승인 요청 가능' -- B1·B2·S1~S6·m1~m7을 v8에서 반영),
6차 검토 `review6_phase3_v8.md`('고친 뒤 승인 요청 가능' -- N1 E5 비교 판을 UD-0 (c)로, N2 E2 기준, N3 backfill card, N4 V1 옵션 문장, m-a~m-c를 v8.1에서 반영; 개정 전 사본 `phase3_approval_question.v8.md`).
**v8.2(오케스트레이터 결정)**: UD-0 (c)의 기본안(Recommended)을 선례 `20260930-phase2-e4-baseline` 모양으로 바꿨다 -- 같은 상황에서 사용자가 고른 쪽("둘다 기본안으로 진행해")을 따른다는 원칙. B0 비교는 대안. 개정 전 사본 `phase3_approval_question.v8.1.md`, design 사본 `draft_phase3_design_v8.1.md`.
**v8.3(7차 검토 `review7_phase3_v82.md` -- '고친 뒤 승인 요청 가능')**: S1 design §10 E5 판정 python의 `rails` 계약값 판정을 정확 일치로, m1 계약값 `supply_nets`를 P2D library에서 읽음(둘 다 판정을 더하는 쪽, 아래 UD-0 (c) 문장에 반영),
m2 UD-0 (c) 기본안의 비용 문장과 '계약 모양 시제품으로 실측', S2 **A2-③ 삭제** -- 2026-10-01 B26 묶음 [card phase] 답 "phase 3 + 정정 기록 (Recommended)"(decision 기록 `20261001-b26-phase3-cards`)로 이미 결정됐다. 개정 전 사본 `phase3_approval_question.v8.2.md`.
**v8.4(승인 질문 전 마무리)**: G1 착수 키트(`__future__` 혼합 9단위 → 준비 card FU, 머리 수치 15,650·859, `SourceIndex.tree`), D0a 키트(import 머리 생성 이름마다 한 번),
T0 키트(V5 '리터럴 변경 3 + 비교 완화 1'), D0b 착수 키트·D0b 검토(이관표 계층: 배정 규칙 보강 + N3.10 A-1 충돌 보정 8건(토큰 11개) → 모의 `upward`·`cycles`·`unassigned` 0), 기준 `dd60db6`.
판단: FU·import 머리는 승인된 기준을 바꾸지 않아 질문 항목을 늘리지 않고 UD-0 본문의 사실로 적는다. 승격 규칙은 계획 517행 '레지스트리 열이 정본'의 뜻을 바꾸므로 '기준에 닿는 기본값' (d)로 드러내고,
N3.10 보정 8건(토큰 11개)은 계획 표 개정이라 '함께 덮는 문서 개정'에 적는다(질문 수는 그대로 넷). 개정 전 사본 `phase3_approval_question.v8.3.md`.
오케스트레이터가 AskUserQuestion으로 **네 질문**(UD-0·D-19·UD-5·UD-1)을 한 번에 올린다(v8에서 더한 A2-③은 v8.3에서 뺐다 -- 다시 묻지 않는다). 각 선택지는 중립으로 쓰고 권고만 (Recommended)로 표시한다.
답을 받은 뒤 승인 기록: UD-0·D-19 → `20260930-30-module-split-design`(`target_kind: diff`, design 30 + 문서 개정 diff + 새 측정 스크립트 -- D-19 답에 맞는 N3.10 MOD2 행 문안), UD-5 → `20260930-p3-gate-move-aware`
(`target_kind: diff`, G1 spec card·design 05 §10·계획 533행), UD-1 → 같은 design 승인 기록의 범위 설명에 U-03 답으로 적는다. A2-③은 `20261001-b26-phase3-cards`로 이미 기록됐다(이 질문 밖).

---

> **[Phase 3 design 승인 -- 4건]**
>
> (참고: B34·test 보강·backfill·B26-1 네 card의 Phase는 2026-10-01 B26 묶음 [card phase]에서 이미 답하셨습니다 -- `phase: 3`, Phase 3 이동 card 전 병합. 다시 묻지 않습니다.)
>
> **UD-0. design `30-module-split`(10모듈 분할) 승인**
>
> Phase 3에서 할 일은 네 가지입니다. ① `sizing_recipe.py`·`stick_diagram.py` 등을 계획 N3.10의 10모듈로 **본문을 바꾸지 않고** 옮깁니다(모듈마다 card 1건, 이동 전용 도구로 AST 해시 동일 확인).
> ② 재수출 shim을 거쳐 추적 파일의 import를 갱신합니다. ③ shim과 `sizing_recipe.py`를 지우고, `stick_diagram.py`의 임시 재수출도 지운 뒤 추적 파일이 그 이름을 여전히 찾는지 확인합니다(DoD에 추가 -- 판정을 더하는 쪽).
> ④ MOD10 진입점을 만듭니다. card는 17건입니다(준비 card 하나 -- 이동 전에 `design_report.py`·`audit_current_forced.py` 머리에 `from __future__ import annotations` 한 줄을 넣습니다. 옮겨 갈 모듈의 다른 원본 파일들에 이미 있는 줄이라,
> 없으면 그 9개 함수는 '바이트 그대로 이동'으로 인정되지 않습니다. 넣어도 동작이 같음을 실측했습니다: 함수 몸체 코드 동일, 전체 test·E-LIB·E-INST 결과 동일).
> phase 3 card(준비 card 포함)는 Phase 2 완료 판정(2026-10-01 PASS)과 B34·B26-1·B33 병합 뒤에 병합합니다. Phase 3 이동이 시작되면(이관표 확정부터 shim 삭제까지) 엔진 파일·
> 게이트와 이동 도구(`tools/gates`·`tools/migrate`)·레지스트리 목적지 열을 바꾸는 다른 card는 병합하지 않습니다.
> 완료 판정의 전체 test는 phase 3 기준 실행과 DoD 모드 실행 두 번이고, 동작 보존(E-LIB·E-INST)의 비교 판은 아래 (c)입니다. 호출부 갱신(F1) 뒤에는 기존 E-INST 측정 스크립트가 돌지 않아,
> 같은 해시를 재는 새 측정 스크립트를 design과 함께 넣습니다(E-INST용 하나, 그리고 (c)의 의도된 필드를 빼고 재는 E-LIB용 하나 -- 둘 다 옛 스크립트와 같은 결과임을 완료 판정 때 먼저 확인).
>
> 이 승인이 함께 덮는 문서 개정(문안 첨부 `p3_doc_amendments.md`):
> - 계획 N3.10 표: `load_topology`·`validate_theta_declaration_order` → MOD3(MOD3 구조 유도 함수를 불러 계층상 MOD3), `optimize_full_circuit_budget`는 Phase 3 동안 MOD8(θ 탐색부 추출 뒤 MOD6)
> - 계획 N3.10 표(v8.4 추가 -- 지금 코드에서 표에 적힌 함수가 더 큰 번호 모듈의 함수를 불러 규칙으로는 풀 수 없는 8건, 함수 이름 11개): θ 평가 커널 조립·시작점·SLSQP 함수 4개(`_build_theta_evaluator` 등)는 레이아웃 해석을 불러
>   Phase 3 동안 MOD8(위 `optimize_full_circuit_budget`과 같은 모양, θ 탐색부 추출 때 MOD6), `require_declared_spec_source` MOD2 → MOD3, `apply_theta_feed` MOD4 → MOD5, 도우미 4개를 부르는 쪽 모듈로
>   (`metric_unit_scale` → MOD2, `_multilinear_interp_point_multi` → MOD1, `_metric_nulling_resistor_ohm` → MOD4, `find_hub_merge_candidates` → MOD3), 갈 곳이 없던 삭제 후보 `signal_path_nodes` → MOD3.
>   이 개정과 (d)를 함께 적용한 모의에서 이관표의 위쪽 import·순환·미배정이 모두 0입니다(시제품 관찰 -- 실제 값은 이관표 card가 다시 계산).
> - 계획 534행 shim 문장(이관 중 잔여 정의 허용, `topology_library`·`design_report` shim 포함), N3.12.3 test-only 목록에 T0·T1
> - `00-common` 진입점에 `topology_path` 인자, `10-test-separation` §5.6 '파일' 열을 설명으로
> - 새 파일 `docs/03-analysis/gain-budget-gmid-sizing-30-module-split/scripts/e_inst_p3.py`(Phase 3 E-INST 측정 스크립트)와 같은 디렉터리 `e_lib_p3.py`(E-LIB 측정 스크립트 -- 기존 것에 '뺄 meta 키' 인자 하나만 더함)
>
> 레지스트리 §7의 `보류(Phase 3)` 처리 칸 9개는 이관표 card가 `보류(Phase 4)`로 바꿉니다 -- U-02 승인 1항 원문 "보류(Phase 3 모듈 이동·Phase 4 배선)" 중 이동 몫은 레지스트리 '이관 목적지' 열과 이동 도구가 넘겨받고,
> 보류 항목 집합은 그대로입니다(U-02 '재검토'가 승인표 변경은 사용자 승인이라 적어 여기 드러냅니다).
>
> **기준에 닿는 기본값 네 가지**(이 승인이 덮습니다):
> - (a) **D-9** -- 계획 534행 "추적 파일 전부 갱신"의 예외: 판정 기록 증거 스크립트(`.ai/verification/**`)와 기준 커밋 측정 원자료 1개(`probe_stage_partition.py`)는 기록 보존을 위해 갱신하지 않으므로,
>   shim과 `stick_diagram` 임시 재수출을 지운 뒤 일부 import가 깨진 채 남습니다(기록된 커밋에서만 재실행). 지금 실측으로 깨지는 것: 원자료 1개(`sizing_recipe` import와 `stick_diagram`에서 읽는 이름 4개),
>   그리고 `stick_diagram`을 import하는 판정 기록 스크립트 8개 중 **F2 뒤 `stick_diagram`에 남지 않는 이름을 읽는 2개**(`e_lib_inst.py`, `diff_dup.py` -- 근사 배정 기준, 정확한 수는 이관표 확정 뒤).
>   나머지 6개(`e_lib.py`)는 깨지지 않습니다.
> - (b) **D-17** -- 모듈 속성을 덮어써 계측하는 probe·진단 스크립트 8개(대입 14줄)는 덮어쓰기 대상을 새 모듈로 옮기고, 호출부 갱신 card의 "import 줄 외 동일" 검사에서 그 대입 줄만 뺍니다(probe 기능 보존).
> - (c) **D-28 동작 보존 비교 판** -- 완료 판정의 E-LIB·E-INST를 무엇과 비교할지입니다.
>   **기본안 (Recommended)**: **Phase 2 완료 판정 대상 커밋**(`5f643a9`)과 Phase 3 마지막 병합본을 같은 경로에서 비교합니다. 그 사이 card가 의도적으로 바꾼 필드만 빼서 그 card의 계약값으로 따로 판정하고,
>   나머지는 해시가 같아야 합니다. 빼는 필드는 card 계약에서 유도하고 **계약 모양 시제품**(B26-1 실물이 아니라 계약 1·2만 흉내 낸 것)으로 실측했습니다 -- E-LIB의 `load_topology` `meta["rails"]` **하나**(B26-1이 더하는 키). 그 값은 "`nets` = 그 회로의 `supply_nets` 선언(비교 시작 판 기준)" 하나짜리 값과 **정확히 같아야** 하고, 다른 필드가 끼거나 사이에 선언이 바뀌면 실패입니다.
>   E-INST(instance.json)에서 빼는 필드는 **없습니다**: B34·B26-1은 계약상 같은 값이고, test 보강 card는 엔진을 바꾸지 않으며, backfill 결함 card가 바꾸는 `relaxed_pairs`의 `interdig_ok`는
>   instance.json·보고서에 쓰이지 않습니다(파일럿에서 그 값이 저장 함수까지 넘어가지만 파일에 0회 -- 실측).
>   기본안의 비용: 빼는 필드 목록은 design에 박힌 상수라, 그 사이 card의 계약이 바뀌거나 새 엔진 card가 끼면 design 개정(승인 diff)을 다시 받아야 합니다(판정자가 목록을 늘릴 수 없음).
>   **대안**: 비교 판 = **B0**(M1 판정 기록의 `base_commit`, Phase 3 이동 직전 판). Phase 2 완료 판정 판과 B0 사이(B34 → test 보강 card → backfill 결함 card → B26-1)는 각 card의 판정 기록이 잇습니다.
>   측정 명령은 같고 비교 커밋 하나만 바뀝니다.
>   **선례**: Phase 2 완료 판정의 같은 질문(승인 기록 `20260930-phase2-e4-baseline`)에서 선택지는 "기본안 = da03c0e와 Phase 2 마지막 병합본을 같은 경로에서 비교하고 `topology_ref`만 DF-36 계약값으로 판정,
>   대안 = card별 판정 기록 사슬로 갈음"이었고, 답은 "둘다 기본안으로 진행해"였습니다. 이번 기본안은 그 선례와 같은 모양입니다(v8.1 문안은 반대로 B0를 기본안으로 두었습니다).
>   대안이 나은 경우: 비교 창을 Phase 3 이동만으로 좁혀, 앞선 card의 의도된 변경과 Phase 3 결함이 한 비교에 섞이지 않게 하고 싶을 때입니다.
>   (v8.4: 위 준비 card는 E-LIB·E-INST 값을 바꾸지 않아 빼는 필드 목록은 그대로입니다 -- 실측.)
> - (d) **D-31 이관 목적지 계산 규칙** -- 계획 517행은 "함수별 목적지는 레지스트리의 '이관 목적지' 열이 정본"이라 적고, 같은 줄에 "import는 번호가 작은 모듈 쪽으로만"을 둡니다. 지금 열에는 둘이 충돌하는 칸이 있습니다
>   (적힌 모듈보다 큰 번호 모듈의 함수를 부르는 함수 -- 시제품 관찰 32개). **기본안 (Recommended)**: 그런 칸은 '그 번호 이상'(하한)으로 읽어 계층이 요구하는 번호로 올리고(승격), 이관표 card가 열을 계산 결과로 다시 써서
>   열과 이관표를 다시 같게 만듭니다. 즉 이 승인 뒤 옛 열 값은 정본이 아니라 하한입니다. 단 MOD7 `stick_diagram`(계획 책임 "레이아웃만")으로는 규칙이 올리지 않습니다 -- 그런 경우는 계획 표 개정으로 따로 여쭙니다.
>   같은 규칙 보강으로 모듈 docstring은 옮기지 않고, `audit_current_forced.py`(도구로 남음)의 나머지 함수는 그 파일에 남고, 부르는 곳이 없는 함수는 부르는 대상 쪽 모듈로, 서로만 부르는 함수는 `stick_diagram.py`에 남습니다.
>   **대안**: 열을 정본으로 그대로 두고 충돌 함수 32개를 계획 N3.10 표에 하나씩 적어 옮긴다(계획서에 함수 이름이 쌓이고, 표 토큰도 결국 열 칸을 덮어씁니다).
>
> **위임하지 않는 것**: 이동 도구가 B26-1·B34 병합 뒤 실제 코드에서 위에 적은 계획 표 개정(3건 + 8건 + D-19) 밖의 개정이 필요하다고 계산하면, 그 표 diff는 이 승인에 포함되지 않고 그때 따로 여쭙습니다.
>
> - **승인 (Recommended)** -- 위 범위 그대로. 추가 표 개정은 나오면 다시 묻는다.
> - **승인 + 추가 표 개정 위임** -- 이동 도구가 계산한 표 개정은 다시 묻지 않고 계산 결과대로 반영한다.
> - **수정 요청** -- (a)·(b)·(c)·(d) 중 바꿀 것을 지정(예: (a) 판정 기록 스크립트도 갱신 / (b) 해당 probe를 'Phase 3 뒤 동작하지 않음'으로 표시 / (c) 대안 -- B0와 비교하고 Phase 2 완료 판정 판과는 card 판정 기록 사슬로 잇는다 / (d) 대안 -- 열을 정본으로 두고 충돌 함수를 계획 표에 적는다).
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
> 지금 게이트는 바이트 그대로 옮긴 함수도 새 함수로 봅니다. 그래서 엔진 이동 card는 변이 약 1.6만 개(15,650 -- `0f23786` 재측정) 때문에 판정할 수 없습니다. 어느 방식이든 약화는 없습니다(합성 반례 51단계 중 거부해야 할 단계는 전부 거부, 실제 엔진 통째 이동의 거짓 거부 0). 계획 533행 한 문장과 design 05 §10 문구도 이 승인이 덮습니다.
> - **(가) 전역 이동 인식 규칙 (Recommended)** -- 게이트 변경 1회로 끝나고, card마다 추가 승인이 없습니다. Phase 3 안에서는 이동 도구가 이관표와 한 번 더 대조합니다.
> - **(나) 승인 기록에 선언한 이동만 인정** -- M card 8건마다 승인 기록이 1건씩 더 필요합니다. 선언 안의 우회(조건부 재정의 등)는 (가)와 같은 규칙으로만 막을 수 있습니다.
> - **보류**
>
> **UD-1. U-03 -- 추적되지 않는 스크립트 `workspaces/current-reuse-telescopic-ota-report/smoke_run_harness_session18_save.py`**
>
> 이 파일은 `sizing_recipe`(`SemiEmpiricalGmIdLUT`·`optimize_full_circuit_budget`)와 `stick_diagram.save_instance_json`을 import합니다(9·10행). shim 삭제 뒤 두 import가 모두 깨집니다.
> (추적 안 된 `.py`는 이것과 `.claude/hooks/*` 4개뿐 -- v8.4 재확인.)
> - **(가) 깨지게 둠 (Recommended, 계획 기본안)** -- 추적 파일만 갱신합니다.
> - **(나) 지금 저장소에 추가(추적)하고 호출부 갱신 card(F1)에서 함께 갱신**
> - **(다) 삭제** -- 사용자 작업입니다(오케스트레이터는 추적 안 된 사용자 파일을 지우지 않습니다).

---

## 질문에 넣지 않은 것(원칙 기본값 -- design 30 §9.3, UD-0이 덮는다)

D-1~D-8·D-10~D-16·D-18·D-20~D-30은 코드 배치·판정 절차이고 회로 해석이 없다(3차 검토 §7). D-31(배정 규칙 보강)은 계획 517행의 뜻을 바꾸므로 UD-0 (d)로 묻는다(v8.4). v6에서 더한 것: D-22(M9~F1의 SD ↔ MOD9 임시 순환 대비 import 줄 위치 + 모듈별 단독 import
점검 -- 판정을 더하는 쪽), D-23(phase 3 card 병합 = Phase 2 DoD 뒤), D-24(E3를 AST로 -- 정규식이 놓친 6파일을 잡는 쪽), D-25(M10 진입점 test 회로 = 가장 싼 E-INST 회로, 판정 기준 불변).
v7에서 더한 것: D-26(DoD E3b -- `stick_diagram` 임시 재수출을 지운 뒤 추적 파일이 읽는 이름이 모두 해석되는지, 판정을 더하는 쪽. UD-0 ③ 문장에 반영),
D-27(D0b부터 F2까지 다른 card 병합 금지 -- 오케스트레이터 병합 순서 규칙. B26-2~B26-4·B35는 기본 F2 뒤. UD-0 ④ 문장에 반영).
v8에서 더하거나 고친 것(5차 검토): DoD 전체 test = `PT3`(`--gmid-phase=3`) + `PT3 --gmid-dod`(B1 -- 판정을 더하는 쪽, Phase 2 승인 `20260930-phase2-e4-phase`와 같은 모양, UD-0 ④ 뒤 문장에 반영),
E3b가 star import·동적 이름·파싱 오류를 base에 있어도 FAIL(B2 -- 판정을 더하는 쪽), D-27 동결 범위에 `tools/gates/**`·`tools/migrate/**`·레지스트리 목적지 열(S6 -- UD-0 ④ 문장에 반영),
D-28(Phase 3 E-INST 측정 스크립트 `e_inst_p3.py`를 design 커밋에 고정, DoD가 옛 스크립트와의 동등을 먼저 잼 -- 문서 개정 목록에 반영; **D-28의 동작 보존 비교 판은 여기서 빼서 UD-0 '기준에 닿는 기본값' (c)로 묻는다** -- v8.1, 6차 검토 N1),
D-25 문언(E-INST 회로 집합 안에서 가장 짧은 회로 = `folded_cascode` -- S4).
v8.4에서 더한 것: **D-29**(`__future__` 혼합 -- 준비 card FU가 D0b 전에 `design_report.py`·`audit_current_forced.py` 머리에 `from __future__ import annotations` 한 줄. 계획 533행 이동 증명·G1 M-4·M card 기준을 바꾸지 않고
동작 불변 실측(함수 몸체 코드 객체 17개 동일, 전체 test 1047 passed·15 xfailed 동일, E-LIB·E-INST 동일, V3 변이 0) -- UD-0 ④에 card 17과 한 줄로 반영. 대안 (가) M card에서 V3 판정은 M card 기준 약화, (다) 배정 변경은 N3.10 책임 개정이라 기각,
design 30 §6.5), **D-30**(MOD 파일 import 머리 = 이동 도구가 생성, 이름마다 import 한 번 -- 원본 import 줄을 모으면 같은 이름이 두 번 묶여 G1이 거부; 판정을 더하는 쪽).
D-10 근거에 U-02 1항 원문(UD-0 본문에 반영). 이관표 card(D0b) 행의 '전 행'·'합성 입력' 문구를 대상 행·실제 단위 표본으로, 판정 목록 일곱(`import_conflicts` 포함)으로 design에서 닫음(D0b 검토 S4·B2 -- card 결정이 아니라 design 문장).
v8.3에서 고친 것(7차 검토): E5 판정 python -- `rails` 계약값 정확 일치(S1)·계약값 `supply_nets`를 P2D library에서(m1), 둘 다 판정을 더하는 쪽이라 UD-0 (c) 문장에만 반영. A2-③ 결정 반영(§9.2·§11-11·§6.4·D-23·D-28 (e) -- 네 card가 Phase 3 DoD `^phase: 3$` 목록에 듦, B26-1 등가 면제는 M card 이동을 따라갈 필요 없음).
v8.2에서 고친 것(오케스트레이터 결정): UD-0 (c) 기본안을 선례 모양으로(Phase 2 완료 판정 대상 커밋과 비교 + 의도된 필드 `meta["rails"]`만 계약값으로 따로 판정), E-LIB용 `e_lib_p3.py` 추가(문서 개정 §8).
v8.1에서 고친 것(6차 검토): E2 통과 기준에 `E2 INVALID` 줄 없음(N2 -- D-27 사후 강제를 판정에 넣는 쪽), D-26 한계에 E3b가 놓치는 세 모양(m-a), D-28에 `e_inst_p3.py` 출처 확인 범위(m-b).

## 뒤에 올 승인(지금 묻지 않는다)

T0·T1·F1의 V5 승인(test 커밋 뒤 diff 해시로 -- **T0는 시제품 기준 V5 도구 발견 4 = 리터럴 변경 3 + 비교 완화 1**: 비교 완화는 유일성 단언 `len(...) == 1`이 새 비교 연산자로 잡힌 것이라 판정을 더하는 단언이지만,
T0 승인 질문·승인 기록 범위 설명에 '비교 완화 1건(유일성 단언)'을 이름으로 적는다 -- 실제 발견·해시는 test 커밋에서 다시 잰다, `draft_p3_t0.spec.md` 113~117행), D0b가 계산하는 추가 N3.10 개정(나오면 -- UD-0 '위임하지 않는 것'),
**M10 V3 생존이 남으면 그 면제 승인**(design 30 §2.3: 생존은 V3 FAIL이고 면제는 사용자 승인 -- 5차 검토 m4).

## 대상 판 해시(v8.4 작성 완료 시점, sha256 앞 16자리 -- 질문 때 다시 계산해 승인 기록에 적는다. 기준 gate `master` `dd60db6`. v8.4에서 바뀐 것: design·문서 개정·D0a spec card(이 개정), G1·T0 spec card(각 착수 키트 -- v8.3 목록 뒤 개정))

* `draft_phase3_design_v8.md` `ba5131aba3f07b0e`(v8.3: `5ea5683e376eb7f5`)
* `p3_doc_amendments.md` `bf5c0c5f311fec40`(v8.3: `5104bfe4c23aeebf` -- §1 (a)~(d) 새 문안 갱신·§9·적용 실측)
* `draft_p3_g1.spec.md` `cacf06adf1bc5bba`(v8.3 목록: `bc26a6d4b840cc4b` -- G1 착수 키트 v9 확정판: 계약 0 `SourceIndex.tree`, 머리 수치 15,650·859·스크립트 4, 31단계)
* `draft_p3_t0.spec.md` `f490002034a57f8d`(v8.3 목록: `35f7e3e7850a2847` -- T0 착수 키트 개정, V5 '리터럴 변경 3 + 비교 완화 1' 문장 113~117행)
* `draft_p3_d0a.spec.md` `b6f7dc22157596b5`(v8.3 목록: `1f9592d491303132` -- D0a 착수 키트 개정 `2f86484626e7fd6a` 위에 이 개정: `mod_imports`·`import_conflicts`·`import-dup`, `SourceIndex.tree`, 규칙 docstring 제외·A-K·승격·A-6·A-7·단조)
* `p3_scripts/e_inst_p3_proposed/e_inst_p3.py` `7d26134ad00ec504`(변경 없음)
* `p3_scripts/e_lib_p3_proposed/e_lib_p3.py` `c6b82fc7b4cd974c`(변경 없음)
* 판정 python(design §10 E5 `PYEOF` 블록 셋째를 그대로 뽑은 것 -- design 해시에 포함, 재측정 대조용) `ae6422d680dae2ab`(변경 없음 -- §10은 v8.3과 같다)
* 재측정 스크립트 `p3_scripts/p3v83_judge_scenarios.sh` `7c9be52da0fc7ff0`, 출력 `p3_scripts/p3v83_judge_scenarios.out.txt` `52bbe243777d6d65`(design 부록 A F4v83, 변경 없음)
* (참고, UD-5 승인 기록 초안) `g1_kit/approval_20260930-p3-gate-move-aware.md` `8236cb3377cc7463`
