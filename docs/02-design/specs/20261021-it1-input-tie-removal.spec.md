---
id: 20261021-it1-input-tie-removal
phase: 해당 없음 (DEC-86 -- merge_gate 미사용, N6.3 절차)
evidence_type: red-green
gate_change: no
approval: 20261021-it1-o13-scope
---
## 의도

- **절차(phase)**: 계획 DEC-86(285행)·N3.12 머리(669행)로 역할 분리 gate·spec card 흐름·merge_gate가 꺼졌다. 판정 = N6.3(매 변경 뒤 새 test 전체 실행, 작성자 ≠ test 작성자 WP-13, 약화 보고, 변경당 커밋 1) + 독립 측정·검증 agent이고 merge_gate가 아니다. 머리 블록은 형식 호환용이다.

계획 v6.23 N6.5 card IT-1(입력 포트 '같은 DC' 엣지 `input_tie` 폐기 -- 사용자 결정 B2·K-3·O-13 (1)(2))을 design 41 v1.12.3 §4.7-1 1~5·test interface와 §6.7-1a(개정 문단) 그대로 구현한다. 목표 한 줄: **입력 DC 미선언 회로의 쓰기 계획에서 같은 DC 엣지·`input_tie` 쓰기와 그 어휘를 없애고, 입력 포트 W4 뿌리의 y 키를 뿌리 넷으로 두며, 입력 포트인 W4 뿌리가 둘 이상이면 `dc_writer_plan`이 탐색 전에 `input_port_multiple_roots`로 정지한다. 이 card는 새 규칙을 정하지 않는다.**

- card base = master `468e6e73`(card B 병합 포함). 착수 base = 통합 브랜치 `integ/it12`의 IT-0 판정 기록 커밋(아래 '통합 브랜치 계획'). 줄 번호는 착수 때 감사가 다시 잰다.
- `E/` = `skills/analog-gmid-design/gmid_engine/`. 줄 `41:n` = design 41 `docs/02-design/features/gain-budget-gmid-sizing.41-gain-budget.design.md`(master `468e6e73`).
- **동결 갱신(2026-10-21)**: 이 card 브랜치에 master `0de6a34a`(design 40/41/42 v1.12.4, 계획 v6.24 -- 사용자 결정 O-72 (1)·O-70 (2))를 병합했다. card 안 줄 번호 인용은 따로 '(v1.12.4)' 표시가 없으면 base `468e6e73` 값이다. 줄 이동(`git diff -U0 468e6e73 0de6a34a` hunk 실측): design 41은 735행 이상 +1(734행에 한 줄 추가), 계획은 318행 이상 +6·1110행 이상 +8; 그 앞 줄은 같다. 착수 때 감사가 다시 재는 규칙은 그대로다.
  이 card가 인용하는 design 41 줄(666-674, 1686-1694, 1947)은 735행 앞이거나 v1.12.4 개정 hunk 밖이라 내용 불변 -- 1686행 이후는 +1(v1.12.4).
- 사용자 결정 원문: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/user_decisions.md` B2(225행)·K-3(243행)·O-13 (1)(2)(IT-Q1 (나)·IT-Q2·IT-Q3 (가)·IT-Q4)·O-14 (2)(계획 card 승인)·O-19 (2)(IT-2와 같은 통합 병합)·O-61 P4 (a)(고립 입력 포트도 뿌리로 셈)·O-67 (5)(design v1.12.3 승인).
- **동작 변경**이다(41:816 4.7-8 -- 입력 DC 미선언 회로의 쓰기 계획·θ y·결과). 무동작 입력 = 입력 DC 선언 회로(library pushpull_follower_buffer·sf_pushpull_output_opamp).
- **착수 조건**: (가) card 0 IT-0 판정 기록 `.ai/verification/20261021-it0-baseline.json`이 통합 브랜치에 있음(변화표 기준·M-I1 다중 뿌리 발동·M-I4) (나) 승인 기록 `.ai/approvals/20261021-it1-o13-scope.md` -- **충족**(사용자 결정 O-72 (2), 2026-10-21; 이 브랜치에 커밋) (다) IT-0이 다중 입력 뿌리 발동 ≥ 1을 냈다면 **착수하지 않고 보고**(K-3 축소 X-IT5 재결정 -- 계획 N6.5 범위 4).

### 설계 대조(design 41 §4.7-1 대 계획 N6.5 순서 1 design 정정 항목 -- 2026-10-21 이 card 작성 때 대조)

| 계획 N6.5 순서 1 항목 | design 41 v1.12.3 자리 | 결과 |
|---|---|---|
| 1753행 test 위치(F-IT4 -- `test_writer_plan.py` 안 새 함수) | 41:674 test interface '위치', 41:1947 test 표 행 | 반영됨 |
| 1497행 as-built 문단 → 개정 후 문언 | 41:1690 '개정 전(as-built)'·41:1691 '개정(정본 = §4.7-1)' | 반영됨 |
| IT-Q1 (나) rule_branch 이름, §6.7-1a '미구현(발동 0)' | 41:671 `input_port_multiple_roots`·`BRANCH_INPUT_MULTIPLE_ROOTS`, 41:1693 K-3 축소 '미구현(발동 0)' | 반영됨 |
| IT-Q2 반영(40 §3.7·§3.8-8, sizing CONTRACT) | design 40 1232행(W0~W4 행 DEV 정정), 1272행(`icm_margin_v` = 포트별 최솟값, '(나)든 (다)든 계산 경로 하나' X-IT8); 판정 값은 41:820 4.7-8a 칸('미측정' -- IT-0 M-I4) | 반영됨(판정 값만 IT-0 대기, 계산 경로는 판정과 무관). sizing CONTRACT는 구현 몫(범위 5) |
| 1499행 → O-13 (1) 문언 | 41:1686 v1 항목, 41:1692 '결과(O-13 (1))' | 반영됨 |
| O-15 (B)·O-19 (2)·O-21 정의 함께 | 41 §4.7-2~4.7-5(IT-2 몫, O-58 S-1로 개정된 판) | 반영됨 |
| (참고) 완료 조건 7 (a)(b) -- 계획 DEC-64 상태 칸·DEC-59 발동표 행 | 계획에 `input_port_multiple_roots` 0건(grep) | design 정정 항목이 아니라 **완료 때 계획 갱신**(오케스트레이터 열린 항목) |

**빠진 design 정정 항목 없음** -- 멈추지 않는다.

## 관찰 가능한 계약

번호는 design 41 §4.7-1 test interface (a)~(d)와 같다. 정본 문장은 41:666-674·41:1691-1693이고 여기에는 판정 꼴만 둔다.

### graph 단일 정본 계약(프로젝트 CLAUDE.md '★graph 단일 정본' 1~7 -- 판정자가 별도 검사 항목으로 잰다)

| 필드 | writer(하나) | IT-1 변화 | READS 하는 엔진 소비자(≥ 1) |
|---|---|---|---|
| `node.dc_writer` | `dc_writer_plan` | 형식 불변, relation 어휘에서 `input_tie` 없어짐, 입력 포트 W4 뿌리 `y_key` = 뿌리 넷 | `dc_columns`, `scc_order`, `theta_schema`(y 성분), `achievability` |
| `device.dc_coord` | `dc_writer_plan` | 형식 불변, 값 변화(같은 DC 종속 0) | `dc_columns`, `achievability` |
| `graph.dc_tie_breaks` | `dc_writer_plan` | 형식 불변, decision `input_tie_order` 없어짐 | 결과 기록(as-built 소비자 그대로 -- 착수 실측으로 소비자 수 기록) |
| `node.port_direction`(S1, 바뀌지 않음) | 기존 writer 그대로 | `dc_columns` READS에 추가(41:672) | `dc_columns.input_roots` |

- **I1 writer 하나**: 위 필드의 `@compute_block` WRITES 자리는 `writer_plan.py` 하나(`git grep`). 새 graph 필드 0(계획 N6.5 완료 조건 4 (c)).
- **I2 둘째 생산자 0**: 입력 포트 판정은 `node.port_direction` 필드를 READS로 읽는다 -- `dc_columns`·`scc_order`·`achievability`가 포트 방향·W4 뿌리·같은 DC 묶음을 다시 계산하지 않는다(`git grep "port_direction"` 자리 = 정의·READS 선언·읽기). 다중 뿌리 판정은 `dc_writer_plan` 안 한 자리.
- **I3 새 cache 0**: 새 dict·memo·`lru_cache`·`sctx.*` 슬롯·`EvalResult` 값 칸·필드 사본 0(`git grep` diff 기준). 재사용 길 = graph reuse·S3 graft 둘뿐.
- **I4 참조 전달**: y 키는 `NodeWrite.y_key` 필드 값 그대로(넷 이름을 다른 자리에서 다시 고르지 않음).
- **I5 G-10**: 같은 입력 버전에서 `dc_writer_plan` `computes` 증분 0, WP-10 중복 인자 0(바뀐 회로에서 잼).
- **I6 graph 계산값 소비**: 바뀐 필드마다 엔진 소비자 ≥ 1(위 표; 계획 소비자 표 '그대로 소비' 행 `theta_schema:142`·`search_domain:124`·`orbit_ties:22` 포함).

### 동작 계약(test 단언 -- 41:674)

| 계약 | 내용 | base |
|---|---|---|
| (a) | 입력 DC 미선언 차동 입력 toy: relation `input_tie` 0, 입력 포트 W4 뿌리 `y_key` = 그 넷 이름, 종속 목록 = 손계산(같은 DC 엣지로 생긴 종속 0, 포트 경로가 둘 이상인 v1 고리의 ΔV 소거 `cycle_vgs` 포함) | red |
| (b) | 종속 수 = 같은 DC 엣지 없는 G_vgs(F 한 점)의 순환 수(손계산) | red |
| (c) | 입력 DC 선언 toy의 쓰기 계획 = 손계산 오라클 | **green**(무동작 성질) |
| (d) | 두 입력 포트가 서로 다른 G_vgs 성분인 toy → `StructureUnresolvedError`, `detail["reason"] == "unsupported_rule_branch"`, `detail["rule_branch"] == "input_port_multiple_roots"`, `detail["nets"]` = 두 뿌리 넷(쓰기 순번 순) | red |
| (d′) | G_vgs 밖 고립 입력 포트 + 다른 성분 입력 포트 뿌리 toy → 같은 정지(O-61 P4 (a), 41:672) | red |
| (e) | 어휘 부재: `gmid_engine.sizing`에 `REL_TIE`·`INPUT_GROUP_KEY`·`PATH_TIE`·`TIE_INPUT_ORDER` 속성 없음, `BRANCH_INPUT_MULTIPLE_ROOTS == "input_port_multiple_roots"` | red(`AttributeError`·부재) |
| (f) | 계획 완료 조건 3 잔재 grep: 패턴 P(계획 N6.5 완료 조건 3 원문) 결과에서 확정 제외 3줄을 뺀 수 = 0 | red(master `468e6e73` 117줄) -- 감사 측정 |

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `gmid_engine.sizing.s2_values` | `BRANCH_INPUT_MULTIPLE_ROOTS` | 상수 `"input_port_multiple_roots"`(`BRANCH_RESISTOR_CYCLE` 옆) |

서명 불변 진입점(행동 red): `dc_writer_plan(snapshot, target_nets, input_dc_declared, order_hints=NO_ORDER_HINTS)`, `dc_columns`, `run_kernel`/`size_and_seal`, `find_front`.
없어지는 심볼: `REL_TIE`, `INPUT_GROUP_KEY`, `PATH_TIE`, `TIE_INPUT_ORDER`(`E/sizing/s2_values.py:37, :39, :44, :118`)와 `E/sizing/__init__.py` export, `writer_plan._TIE`·`_KIND_TIE`, `scc_order`의 tie 사슬.

## 판정 유형 근거

red-green: (a)(b)(d)(d′)는 서명 불변 진입점 `dc_writer_plan` 경유 행동 red, (e)는 존재 부재 red(`AttributeError` -- 00-common §8.1 허용), (c)는 base에서도 green(무동작 성질 -- red 목록에서 제외), (f)는 감사 측정. 결정성은 감사의 같은 head 두 번 비트 동일.

## oracle 종류와 출처

(손) toy 연결에서 손으로 유도한 writer·종속 분류·순환 수(이름 없는 toy, 넷·소자 이름 맞바꿈에도 같은 값). (식) 41:671 정지 detail 꼴. (독립) `git grep` 수·`RunCounters`. 피검 함수 출력으로 기대값을 만들지 않는다. **기준선**(S0 `u17_1b_s0_baseline.json`·NFR-4·card 기대값)은 IT-Q3 (가): 감사의 9회로 변화표(IT-0 대비)를 근거로 test 주체가 별도 커밋으로 갱신, 설명되지 않는 변화가 있으면 갱신하지 않고 멈춤.

## 거부해야 할 입력

- 입력 포트인 W4 뿌리가 둘 이상(고립 입력 포트 포함)인 쓰기 계획 → `StructureUnresolvedError`(탐색 전, S0 블록). **'통과'가 아니라 '실제로 거부'를 먼저 확인**(red (d)(d′)).
- 뿌리별 y 묶음(`domain.ties`)·뿌리별 포화 창을 만드는 코드 -- 미구현(발동 0, DEC-76). 만들면 범위 위반.

## library 회로 적용 여부

적용한다. 입력 DC 미선언 library 7회로가 바뀐다(2입력 6회로는 쓰기 계획·종속·θ y, common_gate_amplifier는 y 키 이름만 -- 계획 F-IT2). 선언 2회로는 무동작(쓰기 계획·S0 필드·결과 JSON 필드별 같음 -- IT-0 M-I7 대비). heldout은 재지 않는다. 회로·소자·넷 이름 코드 0(EP-1).

## 무동작 판정 입력(무발동 값)

library pushpull_follower_buffer·sf_pushpull_output_opamp(입력 DC 선언) -- 쓰기 계획 세 필드·S0 필드·결과 JSON이 IT-0 AB 기록과 필드별 같음(NFR-4). 정지 분기는 IT-0 M-I1 발동 0이면 library 전 회로 무발동.

## 재현할 수치

toy 손계산은 test 주체 소유. 9회로 변화표는 감사 소유(IT-0 대비 M-I1~M-I5, 원인 = 범위 1~4).

## 결정 필요 항목

- **U-1 승인 기록 -- 결정됨**(사용자 결정 O-72 (2), 2026-10-21 '(권고)'): IT-1 동작 변경 승인. 기록 = `.ai/approvals/20261021-it1-o13-scope.md`(머리 `approval:` 줄이 가리킴). 옛 사유(O-67 (5) 원문이 IT-1 동작 변경을 덮지 않음)는 이 기록으로 해소.
- **U-2 통합 브랜치 계획**(오케스트레이터 기본안, 아래) -- O-19 (2)·O-69 (2) 그대로라 사용자 결정 불요. IT-0 기록을 master에 따로 넣을지만 오케스트레이터 선택(기본 = 통합 브랜치 첫 커밋).
- 그 밖 as-built 결정 금지 -- design에 없는 것은 멈추고 보고.

## 통합 브랜치 계획(O-19 (2), O-69 (2))

브랜치 `integ/it12`(base = 측정 base master). 커밋 순서(변경당 커밋 1, 각 역할 worktree에서 만든 커밋을 오케스트레이터가 show→Edit→commit으로 옮김 -- cherry-pick 지시 금지):

| # | 커밋 | 역할 | Change-Id |
|---|---|---|---|
| 0 | IT-0 판정 기록 | audit | `20261021-it0-baseline` |
| 1 | IT-1 red test + 바뀐 기대값(소비자 표 test 행) | test | `20261021-it1-input-tie-removal` |
| 2 | IT-1 code(범위 1~5, CONTRACT, 옛 문언) | code | 같음 |
| 3 | IT-1 판정 기록(red 재현·9회로 변화표·graph 정본 I1~I6·gap) | audit | 같음 |
| 3b | 기준선 갱신(IT-Q3 (가), 3의 변화표 근거) | test | 같음 |
| 4~7 | IT-2a → IT-2b → IT-2c → IT-2d 각 test → code → audit | -- | `20261021-it2a-…`~`it2d-…` |
| 8 | 통합 병합본 판정(전체 test 0 failed, 결정성, G-10 9회로, gap) | audit | 통합 |
| -- | master 병합 **한 번**(사용자 병합 승인) -- IT-1만 병합된 기간 없음 | 오케스트레이터 | -- |

IT-1 FAIL·dispute면 IT-1 커밋만 다시(05 §12), IT-2 하위 card는 IT-1 code 커밋 위에서만 착수.

## code 작성자 멈춤 조건(멈추고 보고 -- 만들지 않는다)

- S-1 IT-0 M-I1에서 다중 입력 뿌리 발동 ≥ 1(library) -- 정지 안전망이 실제 회로를 막는다.
- S-2 소비자 표 밖 소비자(같은 DC·`INPUT_GROUP_KEY`·`REL_TIE` 의존)가 착수 실측에서 새로 나옴 -- 표 갱신과 함께 보고(계획 N6.5 '소비자 집합이 늘거나 줄면 보고').
- S-3 `_solve_input_window`·`_interior_solution`의 θ 키를 뿌리 넷으로 바꿀 때 입력 뿌리가 둘 이상인 경로가 남아 보임(41:672 '뿌리는 4로 최대 하나').
- S-4 `ls_swing.py:114`(`v_icm = volts[inputs[0]]`)를 고쳐야 test가 통과해 보임 -- IT-2 몫, 고치지 않는다.
- S-5 graph 정본: 입력 포트 판정·W4 뿌리 판정을 `dc_writer_plan` 밖에서 다시 해야 할 것 같음(정본 자리 없음 -- 계획부터, CLAUDE.md 규칙 6).

## test 작성 주체 몫(code 주체는 고치지 않는다 -- 작성자 ≠ 검증자)

줄은 계획 N6.5 소비자 표(base `5fea301`) -- 착수 때 `git grep`으로 다시 잼:

- 새 test: `E/tests/sizing/test_writer_plan.py` 안 (a)(b)(c)(d)(d′)(e) -- 접두 `test_it1_`, 이름 겹침 `git grep` 확인(41:674, 규칙 H).
- 바뀐 기대(이유 'K-3', `broken_tests`에 나열): `E/tests/sizing/conftest.py:681`, `test_writer_plan.py:1, :16, :89-193`(특히 `:120-129` 같은 DC 기대), `test_scc_order.py:29-55`, `test_scc_newton.py:404-463`, `test_block_columns.py:887`, `test_input_window.py:23, :129-137`, `test_kernel_context.py:163-169`(`gvgs_counts`), `test_s2_values.py:183-197`(+`:181` `REL_TIE` 어휘 단언), `test_size_and_seal_local.py:75, :156`, `E/tests/generality/pipeline.py:249`(포트 넷 y 키가 이름 치환 대상), `E/tests/search/canon_cases.py:111`(입력 묶음 y '그 밖'), 기준선 `E/tests/integration/fixtures/u17_1b_s0_baseline.json`(커밋 3b).
- 옛 문언 test 줄: `test_block_columns.py:545`, `test_input_window.py:1, :4, :216`, `test_scc_newton.py:843`.
- 기대 `criteria_weakened` = 0 -- 바뀐 기대마다 '규칙 변경(K-3), 약화 아님'을 적는다.

## 작성 전 실측

(worktree `wt/spec-it0-it1`, master `468e6e73`, 2026-10-21.)

1. 사실 문장 재측정: 잔재 패턴 P `git grep -nE` = **117줄**(계획 5fea301 값과 같음; 파일별 상위 `sizing/block_columns.py` 21, `sizing/CONTRACT.md` 21, `sizing/writer_plan.py` 17, `sizing/scc_order.py` 9, `sizing/__init__.py` 8, `tests/sizing/test_writer_plan.py` 7). `E/sizing/s2_values.py:37` `REL_TIE`·`:39` `INPUT_GROUP_KEY`·`:44` `PATH_TIE`·`:96` `BRANCH_RESISTOR_CYCLE`·`:118` `TIE_INPUT_ORDER`; `E/sizing/writer_plan.py:76-77`(`_TIE`·`_KIND_TIE`)·`:105`·`:213-214`·`:234`; `E/sizing/scc_order.py:21, :26, :125, :137, :140`; `E/metrics/achievability.py:39, :316`. `E/tests/sizing/test_writer_plan.py` 있음. 계획 소비자 표의 나머지 줄은 base `5fea301` 값이고 card B 병합 뒤 착수 때 감사가 다시 잰다(계획 N6.5 '멈추지 않는다').
2. 이름 충돌: `input_port_multiple_roots`·`BRANCH_INPUT_MULTIPLE_ROOTS` 엔진 0건, `test_it1_` 0건.
3. 원칙의 계약화: graph 단일 정본 → I1~I6, 회로 이름 금지 → 'library 회로 적용 여부', fail-closed → 정지 (d)(d′).
4. 쓰기 경로: test 주체 = interface card만(소스 열람 금지)·`gmid_engine/tests/**`, code 주체 = `gmid_engine/**`(테스트 제외)·CONTRACT·레지스트리(역할 agent 정의의 옛 경로표가 `assets/*`뿐이라 브리핑에 명시).
5. 계획서 소비자: 지우는 이름(`REL_TIE` 등)의 계획·design 인용은 as-built 인용으로만 남음(41:1690). 계획 DEC-64 상태 칸·DEC-59 발동표 행(완료 조건 7 (a)(b))은 완료 때 오케스트레이터.
6. 미배선: 새 상수 `BRANCH_INPUT_MULTIPLE_ROOTS`는 `dc_writer_plan` 정지 자리에서 쓰임(운영 경로).
7. 기존 계약 test: 착수 때 감사 `git grep`(`E/tests/structure` 규칙 A·B·C·H·M).
8. V3 규모: **미확인 (IT-1 code 뒤)** -- 착수 base(IT-0 커밋) 위 IT-1 code 커밋에서 오케스트레이터가 `tools/gates/mutate_changed.py`로 채운 뒤 동결.
9. 승인 줄: `approval: 20261021-it1-o13-scope` -- 기록 `.ai/approvals/20261021-it1-o13-scope.md` 커밋됨(사용자 결정 O-72 (2)). O-67 (5) 원문이 IT-1 동작 변경을 덮지 않아 둔 기록이다.
10. 범위 계약: diff 계약은 이 card `Change-Id` 커밋들의 diff로 한정.
11. test 이름: 접두 `test_it1_`, 피검 함수 본문 직접 호출.
12. 같음 판정: `NodeWrite`·`DeviceCoord`·`TieBreak`는 필드 비교, 종속 목록은 정렬 tuple, 정지 detail은 키별 비교.
13. red 모양: (e)는 `AttributeError`(허용), 나머지는 서명 불변 진입점 행동 red.

## 승인 기록(커밋됨 -- 정본 = `.ai/approvals/20261021-it1-o13-scope.md`, 사용자 결정 O-72 (2))

아래는 승인 전 초안(역사 기록 -- 내용 비교용). 사용자 원문·범위의 정본은 위 파일 하나다.

```text
---
id: 20261021-it1-o13-scope
date: 2026-10-21
target_kind: decision
target: O-13-IT1-SCOPE
scope: card IT-1(20261021-it1-input-tie-removal) -- design 41 v1.12.3 §4.7-1·§6.7-1a의 동작 변경(입력 DC 미선언 회로의 같은 DC 엣지·input_tie 제거, 입력 포트 W4 뿌리 y 키 = 뿌리 넷(결과 JSON 키 y:input_common_mode -> y:<넷>), 같은 DC 종속 0, 다중 입력 뿌리 정지 input_port_multiple_roots), IT-Q3 (가) 기준선 갱신(감사 변화표 근거), IT-2a~d와 하나의 통합 병합(O-19 (2))
---
## 사용자 원문
> (사용자 승인 원문을 그대로)
## 범위 설명
덮는 것: 위 동작 변경과 소비자 표 test 기대 갱신(이유 K-3), S0 기준선 u17_1b_s0_baseline.json 갱신. 덮지 않는 것: 그 밖 기준 약화(criteria_weakened), 다중 뿌리 y 묶음·뿌리별 창 구현(DEC-76 미구현), ls_swing 입력 창(IT-2), heldout 측정.
```
