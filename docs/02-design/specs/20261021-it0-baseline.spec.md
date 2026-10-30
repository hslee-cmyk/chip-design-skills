---
id: 20261021-it0-baseline
phase: 해당 없음 (DEC-86 -- merge_gate 미사용, N6.3 절차)
evidence_type: test-only
gate_change: no
---

> **[상태 표지 2026-10-29] 완료 이력** -- card 0 IT-0 측정 완료(판정 기록 `integ/it12:.ai/verification/20261021-it0-baseline.json`, base `c237d96e`, V2·V4 PASS·나머지 N/A), master 미병합(IT-1 + IT-2 통합 병합 때 함께 들어감). 현행 계획의 후속 측정은 card 0 **IT-0b**(계획 v6.38.4 N6.5 'IT-1 범위 재작성' 완료 조건 2 -- spec card 미작성). 본문의 heldout 4회로는 O-181로 library로 옮겨졌고(지금 library 13회로·held-out 0, 새 held-out이 생길 때까지 A' 일반성 판정 정지), 'IT-2c 착수 실측 (c)'는 계획 v6.38.4가 착수 조건에서 뺐다(`67e7b182`). 본문은 동결 기록이며 덧대지 않는다(O-169).

## 의도

- **절차(phase)**: 계획 DEC-86(285행)·N3.12 머리(669행)로 역할 분리 gate·spec card 흐름·merge_gate가 꺼졌다. 판정 = N6.3(매 변경 뒤 새 test 전체 실행, 작성자 ≠ test 작성자 WP-13, 약화 보고, 변경당 커밋 1) + 독립 측정·검증 agent이고 merge_gate가 아니다. 머리 블록은 형식 호환용이다.

계획 v6.23 N6.5 순서 0 **card 0 IT-0**(검증자 측정, 엔진 무변경)이다. IT-1(N6.5)·IT-2(N6.6, 하위 card IT-2a~d -- 사용자 O-69 (2))의 **변화표 기준(as-built 기록)**과 **착수 전 필수 기록**을 한 판정 기록에 남긴다. 목표 한 줄: **엔진 소스를 한 줄도 바꾸지 않고, as-built와 §6.7-1a 모사 두 쪽에서 아래 '측정 항목' 표의 칸을 모두 재 판정 기록에 적는다. 값은 판정 기록에서만 인용한다(작성자 ≠ 검증자).**

- card base = master `468e6e73`(XRUN-F1 card B 병합 `138a6db3` 포함 -- 계획 N6.5 순서 0 'base = IT-1의 실제 base = card B 병합 master'). 측정 base는 감사가 측정 시점 master 머리로 다시 정하고, `468e6e73` 이후 엔진 결과를 바꾸는 card(예: XRUN-F1 card C)가 병합됐으면 **그 master에서 잰다**(N6.5 순서 0 '다시 잰다'). base 커밋은 판정 기록 `base_commit`.
- 경로 접두 `E/` = `skills/analog-gmid-design/gmid_engine/`. `P` = `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`(master `468e6e73`), `D41` = `docs/02-design/features/gain-budget-gmid-sizing.41-gain-budget.design.md` v1.12.3(인용 줄).
- **동결 갱신(2026-10-21)**: 이 card 브랜치에 master `0de6a34a`(design 40/41/42 v1.12.4, 계획 v6.24 -- 사용자 결정 O-72 (1)·O-70 (2))를 병합했다. card 안 줄 번호 인용은 따로 '(v1.12.4)' 표시가 없으면 base `468e6e73` 값이다. 줄 이동(`git diff -U0 468e6e73 0de6a34a` hunk 실측): design 41은 735행 이상 +1(734행에 한 줄 추가), 계획은 318행 이상 +6·1110행 이상 +8; 그 앞 줄은 같다. 착수 때 감사가 다시 재는 규칙은 그대로다.
- 근거 원문: P N6.5 순서 0(M-I1~M-I7), N6.6 완료 조건 (6)(발동률·front가 빈 회로 수)·(10) (a)(루프 절단 미적용), D41 4.7-8a(결과 칸 여섯), D41 4.7-3b 740행(구동 쌍 넷, IT-2 card C-2), D41 4.7-1a 멈춤 S-OS1·S-OS2(4.7-8a 마지막 칸), 사용자 결정 O-13 (2)(IT-Q2 판정 규칙), O-61 P4 (a)(b), O-64 (2), O-66(13회로 출력 구조 표), O-69 (2) C-3 해소(`_drafts/user_decisions.md`).
- 이 card는 **test-only**다(선례 `.ai/verification/20261016-op1-baseline`: 검증자 보관 card, `code_commit` null). test 작성 주체·code 작성 주체가 없고 **interface card를 두지 않는다**. 산출물은 감사의 판정 기록 하나다.

## 관찰 가능한 계약

### 측정하는 두 쪽

| 쪽 | 정의 | 만드는 법 |
|---|---|---|
| **AB**(as-built) | 측정 base 그대로 | 격리 복제본 `iso-ab` |
| **SIM**(§6.7-1a 모사) | IT-1 범위 1·2·5만 흉내 낸 쓰기 계획: 같은 DC 엣지(`_TIE`) 없음, 입력 포트 W4 뿌리 y 키 = 뿌리 넷, `members` = 자기 자신, `REL_TIE` 분기 없음 | 둘째 격리 복제본 `iso-sim`에 **측정 전용 패치** `scripts/it1_sim.patch`를 적용(패치는 판정 기록 폴더에만 커밋, 엔진 브랜치·master에 들어가지 않음). 범위 4 정지(다중 입력 뿌리)는 **넣지 않는다** -- 정지 대신 발동을 센다(M-I1). 패치 diff 줄 수와 sha256을 기록 |

- SIM 패치는 IT-1 구현이 아니다. code 작성 주체에게 주지 않고(브리핑 금지), IT-1 판정 때 감사가 'IT-1 병합본 대 SIM' 차이를 따로 적는다(차이가 있으면 원인 = 범위 3·4 또는 모사 한계로 설명).
- **heldout 4회로**(cnr_ota·erfc_ota·r2r_opamp·rfc_ota)는 **'출력 구조 분류 발동' 칸에만** 쓴다(D41 4.7-8a N-3 '측정만'). 그 밖 칸은 library 9회로만(P N6.5 완료 조건 2 'heldout은 재지 않는다', N6.2 A' held-out 행).

### 측정 항목(감사가 채움 -- 칸마다 회로별 값, '판정 기록 키'는 `it0_table.json`의 키)

| # | 칸(원문) | 쪽 | 회로 | as-built에서 재는 법 | 판정 기록 키 |
|---|---|---|---|---|---|
| M-I1 | 쓰기 계획(P N6.5 순서 0) | AB·SIM | 9 | `dc_writer_plan` 출력 필드 `node.dc_writer`·`device.dc_coord`·`graph.dc_tie_breaks` 그대로 덤프: 종속 소자 목록·분류(`cycle_vgs`·`fixed_vgs`·`parallel_vgs`), W4 뿌리·y 키, θ y 성분 수, `domain.ties`로 묶인 y 수, 입력 포트마다 writer(뿌리 / MOS 이름 / `input_tie`), `dc_tie_breaks` | `m_i1` |
| M-I1-r | **다중 입력 뿌리·고립 입력 포트·F 성분 미선언 포트**(D41 4.7-8a 넷째 칸, 4.7-1 4·5, 4.7-3 3 (나)) | SIM | 9 | SIM 쓰기 계획에서 (a) 입력 포트인 W4 뿌리 수(G_vgs 밖 고립 입력 포트 = y 키가 그 넷인 W4 포함 -- O-61 P4 (a)) ≥ 2인 회로 (b) 고립 입력 포트 수 (c) 입력 DC 미선언인데 F(레일·W3) 성분에 속해 W4 뿌리가 아닌 입력 포트(O-61 P4 (b)) | `multi_root`, `isolated_input`, `f_component_undeclared` |
| M-I2 | 층 0 시작점(D41 1500행) | AB·SIM | 9 | `layer0_start(sctx)` 결과 `start.row`·`start.point`·사다리 칸 0 결과, 단계 A 정지면 그 사실·code | `m_i2` |
| M-I3 | 봉인·front·결과 키 | AB·SIM | 9 | `find_front` 결과의 봉인 결과, front 지문(`fp_of` front 점 θ·metric), 결과 JSON 키 집합(`y:input_common_mode` → `y:<넷>` 확인) | `m_i3` |
| M-I4 | **IT-Q2 판정**(D41 4.7-8a 첫 칸, O-13 (2)) | SIM | 9 | SIM front 점마다(그리고 θ0 봉인점) 입력 포트 쌍 \|V_p − V_q\| 대 두 포트 노드 tol_V 중 큰 값(봉인이 쓰는 `dc_tol_v`, `E/sizing/seal_node_conflict.py`의 정의). tol_V 미정 노드는 비트 동일 기준. 하나라도 넘으면 그 회로 '차 있음' → 전 회로 0이면 (나), 아니면 (다)(O-13 규칙 그대로 -- 기계적) | `m_i4` |
| M-I5 | 달성가능성 DOF·rank | AB·SIM | 9 | `achievability` 출력의 DOF·rank(AB의 `tie:<넷>` 등식 수 함께) | `m_i5` |
| M-I6 | 순환수 = 종속 수 | AB·SIM | 9 | G_vgs(F 한 점, SIM은 같은 DC 엣지 없음) 순환 수(\|E\| − \|V\| + 성분 수, 엣지 = 쓰기 계획 `_edges` 출력 그대로)와 `device.dc_coord` 종속 수. graph-consumption M-G7과 같은 측정이면 하나로 재고 두 계획이 인용 | `m_i6` |
| M-I7 | 무동작 예측 | AB·SIM | 2(+1) | 입력 DC 선언 2회로(pushpull_follower_buffer·sf_pushpull_output_opamp) AB와 SIM 쓰기 계획 세 필드 필드별 같음(NFR-4 순수 리팩터링 기준, O-34); common_gate_amplifier는 y 키 이름만 다름 | `m_i7` |
| SP | **s_p 부호**(D41 4.7-8a 둘째 칸) | SIM | 9 | SIM front 점·θ0 봉인점에서 뿌리 아닌 입력 포트마다 dV_p/dx 부호. 값 출처 = as-built 감도 연립 `E/sizing/input_window.py` `_sensitivities`를 그 해에 **관찰 전용**으로 부른 결과(창 계산 결과는 바꾸지 않음). 음수면 O-49 P2 발동 | `s_p_sign` |
| KW | **커널 창 상태 발동 수**(D41 4.7-8a 셋째 칸, P N6.6 완료 조건 (6) 발동률) | AB·SIM | 9 | 아래 '커널 창 상태 분류'로 `_solve_input_window` 호출마다 상태를 매기고, 회로마다 (상태별 평가 수) / (`dc_columns` 평가 수)와 (입력 뿌리가 있는 평가 수). 입력 DC 선언 2회로는 as-built에 입력 포트 창이 없어 **'정의 안 됨(as-built 창 없음)'**으로 적는다 | `kernel_window_status` |
| FE | **front가 빈 회로 수**(D41 4.7-8a 다섯째 칸, O-64 (2)) | AB·SIM | 9 | 아래 'front 제외 모사'. 회로마다 원래 front 점 수, 제외 점 수, 재필터 뒤 점 수; 0이 되는 회로 수 | `front_empty` |
| OS | **출력 구조 분류 발동**(D41 4.7-8a 여섯째 칸) | AB 연결 | 9 + 4 | 아래 '출력 구조 분류 측정' | `output_structure` |
| C2 | 구동 쌍 넷 ⊆ ac 접지 ∪ 입력 넷(D41 740행, IT-2 card C-2) | AB | 9 + toy 없음 | 회로마다 S1 `ss` 뷰 전부(`view_system`이 None이 아닌 뷰)에 대해 `pairs` 넷 집합 ⊆ `ss.ground_nets` ∪ `ss.input_nets`인지, 아닌 뷰·넷 목록 | `drive_pair_nets` |
| C3 | 되먹임 선언 자리 상태(IT-2 card C-3, O-69 (2) (b′) 해소) | AB | 9 | 탐색 컨텍스트 `ctx.base`의 `graph/s1v: noise_input_cells` 값 `NoiseDecl.feedback`이 tuple(원소 있음) / `()` / None 중 무엇인지(None이면 spec `human.feedback` 상태 `PendingMark`·거부 구분) | `feedback_slot` |
| LC | 루프 절단 미적용(P N6.6 완료 조건 (10) (a)) | AB | 9 | (i) 정적: `git grep -n "_feedback_cuts\|input_terminal_nets" -- E/sizing E/search E/metrics` 0 (ii) 동적: `gmid_engine.authoring._feedback_cuts.input_terminal_nets`를 호출 수만 세는 관찰 래퍼로 감싸고, `dc_writer_plan`·`run_kernel`·`seal_dc` 실행 구간의 호출 수 = 0 | `loop_cut` |

### 커널 창 상태 분류(as-built `E/sizing/block_columns.py` `_solve_input_window` 갈래 -- 줄은 `468e6e73`, 측정 base에서 다시 잼)

| 상태 | as-built 갈래 | IT-2 대응(D41 4.7-3) |
|---|---|---|
| `no_root` | `input_roots()` 빈 집합 → 풀이 한 번 | 해당 없음 |
| `unmeasured` | 1/2 풀이 창 측정 실패(`windows is None`)이고 `_interior_solution`도 None → 종래 사상 | `unmeasured` |
| `interior` | 1/2 실패, `_interior_solution` 성공(이어서 아래 갈래 중 하나와 함께 기록) | 보조 표지 |
| `tol_undefined` | `c.tolerance` `SealViolationError` → 창 한 번 적용 | `unsettled`(O-61 P5) |
| `remeasure_failed` | 되풀이 중 `again is None`으로 break | 판정 기록에 따로(설계 갈래 대응은 감사가 D41 4.7-3 원문과 대조해 적고, 대응이 분명하지 않으면 '대응 불명'으로 적어 보고) |
| `k_max_exhausted` | `k_max` 회 안에 `settled` 없음 | `unsettled`(O-61 P5) |
| `settled` | `settled`로 break | `measured` |

- 상태는 **관찰 전용 래퍼**로 얻는다: 원 함수를 부르고 반환을 바꾸지 않는 모듈 속성 래퍼(`_solve_input_window`의 진입·`c.tolerance` 예외·`input_windows` 반환 열·`k_max` 값을 기록)만 허용. 래퍼가 판정을 다시 계산하면(둘째 생산자) 안 된다 -- `settled` 여부는 래퍼가 본 `windows`/`again` 열과 tol을 as-built와 같은 식으로 비교한 **측정**이며, 그 식은 판정 기록 `scripts/`에 원문 줄 인용과 함께 둔다.
- **래퍼 무해 확인**: 같은 회로를 래퍼 있음/없음으로 한 번씩 돌려 front 지문 비트 동일(다르면 측정 무효 -- 멈추고 보고).

### front 제외 모사(FE -- O-64 (2) 규칙의 as-built 적용)

1. 쪽(AB·SIM)마다 `find_front` 최종 front 점 θ마다 그 점의 커널 평가를 관찰 래퍼로 한 번 다시 돌려(같은 settings, 새 컨텍스트) 커널 창 상태를 얻는다.
2. 그 점이 `tol_undefined`·`k_max_exhausted`이고 spec에 ICMR 계열 선언 제약(`icm_margin_v`·`icmr_v`·`required_input_cm_v` 가운데 하나라도 `ss_constraints`에 있음)이 있으면 제외. 제약 없는 값이면 제외하지 않음(보고에서만 정의 불능).
3. 남은 점으로 비지배 재필터(엔진 front 비지배 판정 함수를 그대로 부름 -- 재구현 금지).
4. 보조 열: `unmeasured`도 제외로 셀 때의 수(D41 L8 (d) 'unmeasured로 최종 front 제외'의 근사)를 따로 적는다. 주 판정은 1~3.

### 출력 구조 분류 측정(OS -- D41 4.7-1a 규칙, 13회로)

- **엔진 값이 아직 없다**(`node.dc_output_structure`는 IT-2b). 감사 측정 스크립트가 D41 4.7-1a '계산' 문언 그대로(F′ = 레일 ∪ 선언 입력 포트, W3 목표 넷은 F′ 아님, `_TIE` 엣지 없음, G_vgs 엣지 = AB 쓰기 계획 `_edges` 출력에서 `_TIE` 순위 엣지를 뺀 것, 출력 넷부터 너비 우선)로 분류한다 -- 측정 oracle이고 엔진에 들어가지 않는다.
- 쓰기 계획이 정지하는 회로(heldout cnr_ota `dc_resistor_cycle`, erfc_ota `mos_zero_current_structural` -- O-66 '따로')는 **엔진 경로 값 = '분류 없음(정지 code)'**으로 적고, 연결만으로 낸 값은 따로 적는다.
- 출력마다 적는 열: 회로, 출력 넷, 분류(`high_impedance`/`kvl_fixed`/정지), W3 여부, 단단한 경로 위 W3 출력 수(MOS 경로 = OS (e) 꼴 `kvl_fixed` / 저항만 경로 = `dc_resistor_cycle` 정지)(MF-1), **S-OS1 발동**(`high_impedance` 출력의 `node.dc_writer` 사슬 뿌리가 출력 아닌 W3 목표 노드), **S-OS2 발동**(출력 포트 둘 이상 + spec 되먹임 선언 -- `NoiseDecl.feedback`/spec `feedback`이 원소 있는 tuple인 경우와 `()`인 경우를 **나눠** 센다; D41 4.7-1a '되먹임 구성이 선언된'이 `()`(β=1 선언)를 포함하는지 문언이 정하지 않으므로 둘 다 적고 보고).
- **O-66 표 대조**: `_drafts/evidence/2026-10-21/de1_output_structure_13.md` 15출력(KVL 7·HZ 8, 경우 1 = 0)과 출력마다 같은지. 다르면 그 출력과 원인(엔진 `_edges` 대 netlist 연결 차이 등)을 적고 보고.
- W3 선언 0(13회로 모두 `pending CI-15`)이라 S-OS1·경우 1은 지금 공허할 수 있다 -- 그 사실을 적고 'CI-15 결정 뒤 재측정' 표시.

### 판정 기록(산출물 -- `.ai/verification` 관례, schema `.ai/verification/_schema.json`)

| 파일 | 내용 |
|---|---|
| `.ai/verification/20261021-it0-baseline.json` | schema 필수 키: `id`, `spec_card` = `docs/02-design/specs/20261021-it0-baseline.spec.md`, `evidence_type` = `test-only`, `base_commit`(측정 base), `test_commit`(이 판정 기록 커밋 = `Role: audit`), `code_commit` = null, `checks` V1~V10(아래), `reproduced_numbers`(회로별 수치 -- `name` = `<칸>/<회로>/<항목>`, `command` = 재현 명령), `approvals` = [], `auditor_run`(time·worktree·commands) |
| `.ai/verification/20261021-it0-baseline/it0_table.json` | 위 '판정 기록 키'별 회로 사전. 칸마다 `side`(AB/SIM)·`value`·`source`(명령·래퍼 이름). D41 4.7-8a 여섯 칸은 `col_4_7_8a` 아래 같은 이름으로 한 번 더 묶는다(IT-2 card가 인용하는 자리) |
| `.ai/verification/20261021-it0-baseline/cases.jsonl` | 회로·쪽·칸마다 한 줄 **즉시 append**(중간에 죽어도 건짐 -- 장시간 실행은 `run_in_background`) |
| `.ai/verification/20261021-it0-baseline/scripts/` | 측정 스크립트, `it1_sim.patch`(sha256), 관찰 래퍼, 커널 상태 판정 식(원문 줄 인용) |
| `.ai/verification/20261021-it0-baseline/report_items.json` | 아래 '사용자 보고 항목'의 발동 값과 보고 필요 여부 |

checks 배정(op1-baseline 선례): V1 N/A(엔진 diff 0 -- `git diff --name-only <base>..<test_commit>`이 판정 기록 폴더 밖 0), V2 PASS 조건 = test-only 모양 + 모든 칸 채움(빈 칸이면 '측정 불가 + 사유'), V3 N/A(def 변경 0), V4 = 래퍼 무해 확인·결정성(같은 base 두 번 `it0_table.json` 수치 비트 동일), V5~V10은 해당 없으면 N/A와 근거. 판정 기록은 **감사만** 쓴다.

- **잴 수 없는 칸의 처리**(design 41 v1.12.4 834행 '잴 수 없는 착수 실측의 처리', 사용자 결정 O-72 (1)): 칸을 잴 수 없으면 판정 기록에 **'미측정 + 사유'**로 적는다. 다른 회로·다른 점의 대체 측정을 만들어 넣지 않고, 조용히 진행하지 않는다 -- 오케스트레이터가 IT-2c code 착수 전에 사용자에게 보고한다. IT-2c 착수 실측 (a) `current_reuse_telescopic_ota` 봉인점 T_p·δA_num, (b) 진짜 A = 0 대칭 사례, (c) 오라클 실제 vntol·reltol(design 41 v1.12.4 834행)은 이 card의 측정 항목이 아니다 -- IT-2c 판정 기록 몫(IT-2 공통 문서 'IT-2c 착수 실측'). (a)가 지금 잴 수 없다는 근거(`layer0_start` 출발점 없음, `_drafts/evidence/2026-10-21/dvout_feasibility.md` 5행)는 이 card 작성 때 다시 재지 않았다(미확인).

### 사용자 보고 항목(결과가 이 조건이면 오케스트레이터가 사용자에게 올린다)

| 항목 | 보고 조건 | 이유 |
|---|---|---|
| **S-OS1 발동** | 13회로 중 ≥ 1 | 멈춤 갈래 -- 일반형은 계획 개정 먼저(D41 4.7-1a, 회로 해석 공동분석) |
| **S-OS2 발동** | 13회로 중 ≥ 1(원소 tuple·`()` 따로) | 멈춤 갈래 -- O-67 (1)·O-68 (2) (나) 일반형은 계획·design 개정 뒤 후속 card(IT-2는 fail-closed) |
| **다중 입력 뿌리 발동** | library 9 중 ≥ 1 | IT-1 정지 안전망이 실제 회로를 막음 -- K-3 축소(X-IT5) 재결정 대상(P N6.5 범위 4 '발동 회로가 library에 들어오면 구현') |
| front가 빈 회로 | ≥ 1(주 판정) | 정보 보고(결정됨 O-64 (2)) -- IT-2 뒤 그 회로에 front가 없어짐 |
| F 성분 미선언 포트·고립 입력 포트 | library ≥ 1 | 정보 보고(결정됨 O-61 P4) |
| C-2 실패 | 구동 쌍 넷 ⊄ ac 접지 ∪ 입력 넷인 뷰 ≥ 1 | **IT-2c 멈춤**(D41 740행 -- 계획 먼저) |
| (10) (a) 실패 | 루프 절단 호출 > 0 또는 grep ≥ 1 | **IT-2c 멈춤**(S-3) |
| C-3 | 9회로 중 `feedback` None ≥ 1 | 정보 보고(그 회로는 IT-2c에서 '결정 대기' 갈래) |
| O-66 표 불일치 | ≥ 1 출력 | 보고(승인된 표와 다름) |
| M-I4 | -- | 보고 불요(O-13 규칙으로 기계적) -- 결과는 IT-1 완료 보고에 포함 |
| 커널 상태 `remeasure_failed` 대응 불명 | 대응 불명 ≥ 1 | 보고(design 갈래 누락 가능) |

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

(없음 -- 엔진 무변경. 측정 스크립트는 판정 기록 폴더 안이고 엔진 모듈이 아니다.)

## 판정 유형 근거

test-only: 엔진 소스·test 변경 0이고 산출물은 측정 기록이다(선례 20261016-op1-baseline). red·equivalence 절이 없다. 결정성(같은 base 두 번 같은 수치)은 V4로 잰다.

## oracle 종류와 출처

(독립) 엔진 출력 필드 덤프(쓰기 계획·front·`achievability`·S1 뷰)와 관찰 래퍼 기록. (식) 커널 상태 분류·front 제외 모사·출력 구조 분류는 위 정의(원문 = P N6.6 범위 1·O-64 (2), D41 4.7-1a)를 측정 스크립트로 옮긴 것 -- 엔진에 들어가지 않는 측정 oracle이다. (비교) O-66 13회로 표(netlist 연결만, 사용자 승인됨).

## 거부해야 할 입력

- 엔진 소스·test·fixture를 바꾸는 측정(SIM 패치는 `iso-sim` 복제본에만 적용, 판정 기록 폴더 밖 diff 0 -- V1).
- 반환값을 바꾸는 래퍼(래퍼 무해 확인 실패 → 측정 무효, 멈추고 보고).
- heldout을 OS 칸 밖에 쓰는 것.

## library 회로 적용 여부

측정한다(9회로 전 칸, heldout 4는 OS 칸만). 엔진 동작 변경은 없다.

## 무동작 판정 입력(무발동 값)

해당 없음(측정 card). M-I7이 IT-1의 무동작 대상(선언 2회로)을 예측한다.

## 재현할 수치

모든 칸 값은 판정 기록 `reproduced_numbers`·`it0_table.json`에만 있다(이 card는 값을 예측하지 않는다). 사전 근사(참고만, 판정 근거 아님): P N6.5 F-IT9 다중 입력 뿌리 발동 0(근사 모사), O-66 15출력 KVL 7·HZ 8·경우 1 = 0.

## 결정 필요 항목

- **D-1 SIM 방법**(오케스트레이터 확인, 사용자 결정 불요 예상): P N6.5 순서 0이 '§6.7-1a 모사 두 쪽'을 요구하고 방법은 정하지 않았다. 이 card는 '격리 복제본 측정 전용 패치'로 정한다. 감사가 쓴 패치가 IT-1 구현의 사실상 초안이 될 위험이 있어 code 작성 주체에게 주지 않는다(위 계약). **원래 취지와 다를 수 있는 점**: 옛 측정(D41 556행 `measure_v4.py`)은 연결 근사 스크립트였다 -- 이 card는 엔진 경로로 재므로 더 정확하나, 측정 주체가 엔진 코드 패치를 쓴다. 이것이 받아들여지지 않으면 SIM 쪽 M-I2~M-I5·SP·M-I4는 IT-1 code 커밋 뒤(같은 통합 브랜치)로 옮겨 재야 한다 -- 그 경우 IT-Q2 판정이 IT-1 구현 뒤로 밀린다(IT-1 design 정정 순서 1의 IT-Q2 반영도 함께).
- **D-2 입력 DC 선언 2회로의 KW 칸**: as-built에 입력 포트 창이 없어 발동률이 정의되지 않는다. P N6.6 완료 조건 (6)은 '9회로 발동률'이라 적는다 -- 이 card는 '정의 안 됨(as-built 창 없음)'으로 적고, 그 두 회로의 발동률은 IT-2b 판정 변화표에서 처음 잰다. **받아들여짐**(사용자 결정 O-72 (3), 2026-10-21 '(권고)' -- 원래 취지와 다름 승인: 계획 N6.6 완료 조건 (6) '9회로'). 결정 끝, 보고 불요.
- **D-3 S-OS2 '선언'에 `()` 포함 여부**: 두 수를 다 적고, 하나라도 발동하면 보고와 함께 design 문언 확인 요청.

## 작성 전 실측

(worktree `wt/spec-it0-it1`, master `468e6e73`, 2026-10-21.)

1. 사실 문장 재측정: `E/sizing/block_columns.py:691-735` `_solve_input_window` 갈래(`input_roots` 빈 집합 → `_solve`, `_interior_solution`, `SealViolationError` → 창 한 번, `for _ in range(k_max(...))`·`again is None` break·`settled` break, `_refine_ends`)를 다시 읽음. `E/metrics/_helpers_view.py:15-29` `view_system` `fixed` = `ss.ground_nets` ∪ `ss.input_nets` ∪ `pairs` 넷. `E/authoring/_feedback_cuts.py:11` `input_terminal_nets` 정의. `E/search/find_front.py:64` `find_front(sctx, given_starts)`·`:68` `layer0_start`. `.ai/verification/_schema.json` 필수 키 10개·`spec_card` 정규식 `docs/02-design/specs/<id>.spec.md`. 선례 `.ai/verification/20261016-op1-baseline.json`(test-only, `code_commit` null, V1·V3 N/A).
2. 이름 충돌: id `20261021-it0-baseline` -- `.ai/verification/`·`docs/02-design/specs/`에 같은 이름 0.
3. 원칙의 계약화: 엔진 무변경 → V1·'거부해야 할 입력'; 작성자 ≠ 검증자 → 값은 판정 기록에서만; heldout 제한 → 측정 항목 '회로' 열.
4. 쓰기 경로: 감사만(`.ai/verification/20261021-it0-baseline*`). 오케스트레이터는 결과를 D41 4.7-8a 칸·IT-2 card에 **인용**만(값 사본 없이 판정 기록 경로·키를 참조 -- graph 단일 정본 규칙 4의 문서판).
5. 계획서 소비자: 지우는 이름 없음.
6. 미배선: 새 def 없음.
7. 기존 계약 test: 해당 없음.
8. V3 규모: 대상 0.
9. 승인 줄: 없음(계획 정의 범위의 측정). D-2는 사용자 결정 O-72 (3)으로 받아들여졌다(원래 취지와 다름 승인 -- 결정 원문 `_drafts/user_decisions.md` 693행이 근거, 측정 범위를 넓히거나 기준을 약화하지 않으므로 별도 decision 기록 없음). D-1은 오케스트레이터 확인 항목 그대로.
10. 범위 계약: diff = 판정 기록 폴더만.
11~13. 해당 없음(test 없음).

## 변경 이력

- 2026-10-29 `cards/revise-1029`: 위 상태 표지만 더함 -- 본문 불변, 표지 전 원문 = `git show 052465ed:docs/02-design/specs/20261021-it0-baseline.spec.md`.
