# interface card: 20261021-it1-input-tie-removal

> **[대체 표지 2026-10-29 -- 검증 10 병합 가능 판정, master `07964dfe`] 대체됨 -- 현행 계획 card IT-1(범위 재작성) + card 0 IT-0b, 재동결 필요.** 이 card는 통합 브랜치 `integ/it12`에서 구현·판정됐다(판정 기록 `integ/it12:.ai/verification/20261021-it1-input-tie-removal.json`, master 미병합). 현행 계획 v6.38.4 N6.5 'IT-1 범위 재작성(v6.38.3, 사용자 결정 O-168·DEC-106)'이 이 card의 범위 2·범위 3 일부·범위 4, IT-Q1 (나)·X-IT5·순서 2 '다중 뿌리 정지 red'·완료 조건 7을 대체하고 범위 5(g = s 소자 한 규칙, N6.35 E-19)를 더한다. 범위 1(같은 DC 엣지 제거)은 그대로다. 아래 본문은 동결 당시(계획 v6.23·design 41 v1.12.3) 기록이며 현행 계획에 맞춰 덧대지 않는다(O-169). 계획 v6.38.4(승인 O-173 P9-M1a)가 이 card에 범위 6(B4 S1v 같은 입력 재계산 정리, N6.5 재작성 완료 조건 7)을 더했다. 재동결 범위 = 범위 1 + 재작성 범위 2~5(DEC-106·E-19) + 범위 6이고, card 0 IT-0b가 먼저다. 재동결 착수 = design v1.15.x 승인 뒤(master design 40·41 = v1.14.2, v1.15.x는 미승인). 재동결 때 지킬 것(O-178 e_m 칸 옮기지 않음, O-181 library 13·held-out 0 동안 A' 판정 정지)은 IT-2 공통 문서 표지와 같다.


test 작성 주체는 소스를 보지 않고 이 문서만 쓴다(05-role-separation §11.1, DEC-38 -- 본문 코드 없음). 정본 문장 = design 41 v1.12.3 §4.7-1(41:666-674)·§6.7-1a(41:1688-1694), master `468e6e73`. `E/` = `skills/analog-gmid-design/gmid_engine/`.

## 관찰 가능한 계약

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `gmid_engine.sizing.s2_values` | `BRANCH_INPUT_MULTIPLE_ROOTS` | 상수 `== "input_port_multiple_roots"` |
| `gmid_engine.sizing` | `REL_TIE`, `INPUT_GROUP_KEY`, `PATH_TIE`, `TIE_INPUT_ORDER` | **없음**(속성 부재) |

서명 불변 진입점(행동 red를 맡는 자리): `dc_writer_plan(snapshot, target_nets, input_dc_declared, order_hints=NO_ORDER_HINTS)`(S0 계산 블록), `dc_columns`, `run_kernel`/`size_and_seal`, `find_front`.

### 필드(graph) -- writer 하나, 형식 불변

| 필드 | 값 | writer |
|---|---|---|
| `node.dc_writer` | `NodeWrite(tier, relation, element, known, y_key, order)`; `relation` ∈ {`rail`, `declared_target`, `input_dc`, `vgs_gate`, `vgs_source`, `resistor_drop`, `free_window`}(`input_tie` 없음); 입력 포트인 W4 뿌리의 `y_key` = 그 뿌리 넷 이름(옛 `"input_common_mode"` 없음) | `dc_writer_plan` |
| `device.dc_coord` | `DeviceCoord(role, relation, partner)`; `role` ∈ {`writer`, `dependent`}, `relation` ∈ {`tree`, `parallel_vgs`, `cycle_vgs`, `fixed_vgs`} | `dc_writer_plan` |
| `graph.dc_tie_breaks` | `TieBreak(decision, candidates, chosen)`; `decision` ∈ {`writer_edge`, `w4_root`, `current_pivot`}(`input_tie_order` 없음) | `dc_writer_plan` |

규칙(41:668-672):
- 입력 DC 미선언이어도 G_vgs에 '같은 DC' 엣지가 없다. 같은 DC 엣지로 생긴 종속은 0이다.
- 뿌리 규칙: F 없는 성분에 입력 포트가 있으면 그중 (구조 색, 이름) 최소가 뿌리, 같은 색 후보가 둘 이상이면 `TieBreak(w4_root)`. 한 성분 안 뿌리가 아닌 입력 포트는 트리 경로(MOS VGS)로 쓰인다.
- 포트 경로가 둘 이상인 v1 고리는 ΔV를 소거한 KVL 하나가 남아 그 고리 멤버 하나가 `cycle_vgs` 종속이다(대칭이면 대칭 묶음과 중복). 종속 수 = 같은 DC 엣지 없는 G_vgs(F 한 점)의 순환 수.
- 입력 포트인 W4 뿌리가 둘 이상(G_vgs 밖 고립 입력 포트 -- 게이트·소스·저항 어디에도 닿지 않는 입력 포트 -- 도 뿌리로 셈)이면 `dc_writer_plan`이 `StructureUnresolvedError`를 낸다: `detail["reason"] == "unsupported_rule_branch"`, `detail["rule_branch"] == "input_port_multiple_roots"`, `detail["nets"]` = 그 뿌리 넷들(쓰기 순번 순). 탐색 전 정지.
- 입력 DC 선언 회로의 쓰기 계획은 바뀌지 않는다(입력 포트 = F, relation `input_dc`).

### 단언 금지

`order` 칸의 절대 순번 값(상대 순서만), `TieBreak.candidates`의 내부 표현 이외 순서, `input_version` 문자열 값(같음·다름만), 뿌리별 y 묶음·뿌리별 포화 창(미구현 -- 단언하지 않음), `ls_swing` 출력(IT-2 몫).

## test 목록(위치 = `E/tests/sizing/test_writer_plan.py` 안 새 함수 -- 규칙 H, 이름 접두 `test_it1_`, 겹침 `git grep`)

oracle: (손) toy 연결에서 손으로 유도한 writer·종속 분류·순환 수, (식) 위 규칙, (독립) 어휘 부재.

| id | 내용 | oracle | base |
|---|---|---|---|
| T-a | 입력 DC 미선언 차동 입력 toy: relation `input_tie` 0, 입력 포트 W4 뿌리 `y_key` = 그 넷, 종속 목록 = 손계산(같은 DC 종속 0, 포트 경로 둘 이상인 v1 고리 ΔV 소거 `cycle_vgs` 포함) | (손) | red |
| T-b | 종속 수 = 같은 DC 엣지 없는 G_vgs(F 한 점) 순환 수 | (손) | red |
| T-c | 입력 DC 선언 toy 쓰기 계획 세 필드 = 손계산 | (손) | **green**(red 목록 제외) |
| T-d | 두 입력 포트가 서로 다른 G_vgs 성분 toy → 정지, detail 셋 | (식) | red |
| T-d′ | 고립 입력 포트 + 다른 성분 입력 포트 뿌리 toy → 같은 정지 | (식) | red |
| T-e | 어휘 부재 넷·`BRANCH_INPUT_MULTIPLE_ROOTS` 값 | (독립) | red(`AttributeError`) |
| T-h | T-a toy의 넷·소자 이름 맞바꿈 → 같은 구조 결과(y 키는 맞바꾼 이름) | (손) | red |

### 고칠 기존 test(test 주체 몫 -- 이유 'K-3', `broken_tests`에 나열, 약화 아님)

`tests/sizing/conftest.py`(입력 묶음 픽스처), `test_writer_plan.py`(같은 DC 기대), `test_scc_order.py`(tie 사슬), `test_scc_newton.py`(입력 묶음 y), `test_block_columns.py`, `test_input_window.py`(y 키 `input_common_mode`), `test_kernel_context.py`(`gvgs_counts`), `test_s2_values.py`(`REL_TIE` 등 어휘 단언), `test_size_and_seal_local.py`, `tests/generality/pipeline.py`(포트 넷 y 키 이름 치환), `tests/search/canon_cases.py`(입력 묶음 y 분류), 기준선 `tests/integration/fixtures/u17_1b_s0_baseline.json`(감사 변화표 뒤 별도 커밋 -- IT-Q3 (가)). 정확한 줄은 spec card 'test 작성 주체 몫'(착수 때 감사가 다시 잰 값).

### red 예상 목록 규칙

엔진 동작·엔진 트리 구조를 보는 test만(T-c 제외). 새 키워드 직접 호출 `TypeError`는 red로 세지 않는다(이 card는 새 키워드 없음).

## 판정 측정(audit)

| # | 측정 | 합격 |
|---|---|---|
| I-1 | red-green(T-a·b·d·d′·e·h), T-c base green 유지, head 0 failed | 통과 |
| I-2 | graph 단일 정본 I1~I6(spec card) -- writer 자리 하나, 둘째 생산자 0, 새 cache·`sctx` 슬롯·`EvalResult` 값 칸·사본 0, 바뀐 필드 소비자 표 | 위반 0 |
| I-3 | library 9회로 변화표(IT-0 `20261021-it0-baseline` AB 대비, M-I1~M-I5, 원인 = 범위 1~4), 'IT-1 병합본 대 IT-0 SIM' 차이와 원인, 결정성 | 변화가 모두 원인 칸에 있음 |
| I-4 | 무동작: 선언 2회로 쓰기 계획·S0 필드·결과 JSON 필드별 같음(NFR-4), common_gate는 y 키 이름만 | 같음 |
| I-5 | 잔재 grep(계획 N6.5 완료 조건 3 패턴 P − 확정 제외 3줄) = 0, 패턴이 놓치는 줄 대조 기록 | 0 |
| I-6 | G-10(바뀐 회로), WP-10 중복 인자 0, `tests/structure` 규칙 A~I | 0 / 통과 |
| I-7 | DEC-76 세 요구(완료 조건 7): sizing CONTRACT 3절 '미구현(발동 0)', 계획 DEC-64 상태 칸·DEC-59 발동표 행(오케스트레이터), 정지 red base red·head green | 있음 |
| I-8 | gap-detector(design 41 §4.7-1·§6.7-1a ↔ 구현) ≥ 90 % | 통과 |

## 변경 이력

- 2026-10-29 `cards/simplify`(검증 대기): 위 대체 표지만 더함 -- 본문 불변, 표지 전 원문 = `git show 07181524:docs/02-design/specs/20261021-it1-input-tie-removal.interface.md`.
- 2026-10-29 `cards/revise-1029`: 대체 표지 문언 갱신(v6.38.4 승인 O-173 반영: 범위 6 확정, 재동결 범위·착수 조건, '검증 대기' → 병합 표기) -- 본문 불변, 고치기 전 원문 = `git show 052465ed:docs/02-design/specs/20261021-it1-input-tie-removal.interface.md`.
