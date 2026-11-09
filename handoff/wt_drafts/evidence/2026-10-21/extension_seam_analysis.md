# 확장 이음매(extension seam) 실현 가능성 분석 -- "topology 엔진을 더한다" 대신 "규칙 분기 처리기를 더한다" (2026-10-21)

- 기준: 저장소 `chip-design-skills` master `e87092b3`, 읽기 전용(git -C만, 저장소 파일 변경 0). `E/` = `skills/analog-gmid-design/gmid_engine/`.
- 실측: 단계 A를 13회로(library 9 + heldout 4, spec 포함)에 직접 돌림 -- 스크립트 `C:/Users/HSLEE/AppData/Local/Temp/claude/C--Users-HSLEE-Documents-Todoc-fpga-chip-design-skills/63c6146a-ab1d-4035-a169-bae810986922/scratchpad/seam/run_a.py`, 결과 같은 폴더 `out/stage_a.jsonl`(출력은 scratchpad에만 씀, `-B`로 바이트코드도 안 씀).
- IT-0 기록: `integ/it12:.ai/verification/20261021-it0-baseline.json`(base `c237d96e`)을 `git show`로 읽음.
- 표기: 확인하지 못한 것은 '미확인'.

## 0. 결론 먼저

1. **판정: 조건부로 가능하다. 큰 구조 변경이나 재작성은 필요 없다.** 다만 "topology마다 엔진 하나"는 원칙(회로 전용 code 금지·topology 태그 금지, 구조 규칙 E·I)과 정면으로 충돌한다. 원칙과 맞는 꼴은 **"규칙 분기(rule_branch)마다 처리기 하나"**다. 계획 DEC-59·DEC-76이 이미 지원 범위를 "회로 부류가 아니라 규칙 분기 발동"으로 정의하고 있다(plan.md:258, 275). 그래서 이 꼴은 새 개념이 아니라 기존 정의를 code 구조로 옮기는 것이다.
2. **지금은 그런 이음매가 없다.** `@compute_block`은 등록부가 아니라 데코레이터다(`E/core/compute_block.py:176-190`). 블록 호출 순서는 손으로 쓴 순차 호출이다(`E/graph/s1_build.py:78-90`, `E/sizing/kernel_context.py:82-90`, `E/search/search_context.py:174-187`). 분기 판정과 정지는 블록 안의 인라인 `if`/`raise`/`findings.append`다(예: `E/sizing/writer_plan.py:176-179`, `E/graph/blocks.py:296-299`, `E/graph/loop_classify.py:150-156`). 새 분기를 지원하려면 지금은 그 소유 블록 파일을 고쳐야 한다.
3. **graph 단일 정본 장치는 이음매에 오히려 유리하다.** `WriterTable`이 필드마다 writer 하나를 강제한다(`E/core/writer_table.py:28-46`). 그래서 처리기를 "같은 필드에 쓰는 별도 compute block"으로 만들면 `WriterPermissionError`로 바로 막힌다. 처리기는 **소유 블록이 부르는 순수 함수(전략)**여야 한다. 반환값은 소유 블록이 자기 WRITES로 쓴다. 이 구조면 둘째 생산자가 구조적으로 생기지 않는다.
4. **첫 증명 분기 권고: S-OS2 `icm_config_differential_output_structure`(차동 출력 + 되먹임 선언).** 일반형 규칙은 계획에 이미 있다(O-68 (2), O-85 (1) -- plan.md:334, 326). library 소비 회로도 있다(IT-0 `OS/13/S-OS2_tuple_nonempty(current_reuse_telescopic_ota)` = 1). 그 회로는 오늘 master 단계 A를 통과한다(§1.3). 소유 블록 `icm_config`는 아직 구현 전(IT-2c)이므로, 이음매를 IT-2c와 함께 넣으면 옛 code를 고칠 필요 없이 "미등록 = fail-closed → 등록 = 일반형"을 실제 소비자로 증명할 수 있다.

## 1. 지금 엔진이 "지원 밖/미구현"이라고 말하는 자리 전수

### 1.1 `StructureUnresolvedError` 직접 정지 (S1·S0·ss 층)

공통 형태: `detail = {"reason": "unsupported_rule_branch", "rule_branch": ...}`(`E/graph/s1_values.py:55`). 정지 분류 정의는 `E/core/failure_errors.py:48-49`에 있다. 비테스트 소스에서 `NotImplementedError`는 **0건**이다(grep `NotImplementedError` → `E/` 비테스트 0).

| rule_branch | 자리(file:line) | 층 | 구조 부류(연결로 정의) | 13회로 발동 |
|---|---|---|---|---|
| `mos_kind_unsupported` / `passive_kind_unsupported` / `source_kind_unsupported` | 기록 `E/graph/s1_structure.py:69,79`(표 `E/graph/s1_values.py:28-34`), 정지 `E/graph/dc_conduction.py:36-39`; MOS kind 정지 `E/graph/dc_roles.py:72-73`; CONTRACT `E/graph/CONTRACT.md:154,394` | S1 | 원소 kind ∉ {nmos,pmos}/{capacitor,resistor}/{current_source}(이상 전압원 포함) | 0 -- 13회로 모두 A2_build_s1 통과(§1.3) |
| `dc_self_loop` | `E/graph/dc_conduction.py:44,89` | S1 | DC 엣지 양 끝이 같은 넷 | 0 |
| `dc_isolated_loop` | `E/graph/branches.py:69-71` | S1 | 닻(레일) 없는 고리 segment | 0 |
| `bulk_multi_domain` / `bulk_rail_potential_tie` | `E/graph/bulk_default.py:84-86, 98` | S1 | bulk 기본값 영역 충돌 | 0 |
| `column_enumeration_over_budget` | `E/graph/columns.py:91-92` | S1 | 기둥 열거 > 상한(DEC-71 (3) 폴백 미구현, DEC-76) | 0 |
| `gvgs_self_edge` | `E/graph/gvgs_cycles.py:77-78` | S1 | G_vgs 자기 엣지 | 0 |
| `ds_self_swap_zero_current` | `E/graph/s1_symmetry.py:130-132` | S1 | 자기동형이 전도 MOS의 d/s를 맞바꿈(구조적 0 전류) | 0 |
| `column_unassigned`(reason, rule_branch 아님) | `E/graph/column_block_map.py:72`, 단계 A4 `E/pipeline/stage_a.py:154-160` | S1 결합 | 어느 블록·기둥에도 귀속되지 않는 소자(DEC-71 (2)) | **cnr_ota(IDC, x24.M1), erfc_ota(M21)** -- §1.3 |
| `dc_resistor_cycle` | `E/sizing/writer_plan.py:176-179`(상수 `E/sizing/s2_values.py:96`) | S0 쓰기 계획 | G_vgs에서 저항만으로 닫힌 비트리 엣지 | **cnr_ota**(x40 VCR–VDD_1V8) -- `wt/_drafts/evidence/2026-10-21/de1_output_structure_13.md:14`, plan.md:1129 I-H1 |
| `mos_zero_current_structural` | `E/sizing/current_basis.py:130-133`(상수 `E/sizing/s2_values.py:97`) | S0 전류 기저 | KCL 기저에서 MOS 전류항이 구조적으로 0 | **erfc_ota**(M19·M20·M21) -- 같은 근거 |
| `mos_orientation_unsupported` | 상수만 있음 `E/sizing/s2_values.py:98`, raise 자리는 grep으로 찾지 못함 | S0 | -- | 미확인(raise 자리 미확인) |
| `ss_element_kind` | `E/metrics/ss_circuit.py:23-29` | ss | 소신호 회로에 스탬프가 없는 원소 kind | 0(단계 B까지 간 회로 기준, 미확인 -- 이번에 단계 B는 돌리지 않음) |
| `count_budget_undefined`(reason) | `E/pipeline/stage_a.py:232-234` | A2 | MOS 없음·LUT 슬라이스 없음 | 0 |
| `linked_topology_files` 거부(SchemaRejected, DEC-76) | `E/authoring/linked_files.py:20-24` | 로드 | 여러 topology 파일 합치기 미이식 | 0 |

### 1.2 S1v `기록만` 분기 (SEVERITY_UNSUPPORTED Finding → 단계 A에서 정지)

정지 지점은 한 곳이다. 단계 A가 `s1v_findings`로 모아 status `stopped`를 낸다(`E/pipeline/stage_a.py:240-250`). 정식 진입점의 정지는 `E/graph/s1v_build.py:22-31`(`_stop`)이다. 등급 상수는 `E/graph/s1v_values.py:110`, code 목록은 `E/graph/s1v_values.py:133-167`에 있다.

| finding code | 생산 자리 | 구조 부류 | 13회로 발동(오늘 master 실측) |
|---|---|---|---|
| `cs_output_low_impedance` | `E/graph/blocks.py:296-299` | 이득 블록 출력 노드 임피던스 등급 low | cnr_ota 2, erfc_ota 4 |
| `loop_record_only` | `E/graph/loop_classify.py:150-156` | 루프 분류 (4): 순방향 노드를 지나지만 Miller·3-a·3-b 아님(사유 `global_feedback_or_cross_coupled` / 두 능동) | cnr_ota 4, erfc_ota 2, r2r_opamp 3 |
| `undeclared_loop_constraint` | `E/graph/s1v_fields.py:96`, `E/graph/view_analysis.py:150` | 루프 뷰에 안정도 제약 선언 없음(**구조가 아니라 spec 선언 공백**) | cnr_ota 2, erfc_ota 4 |
| `cell_ambiguous`, `pass_group_unsupported` | `E/graph/cells.py:80, 103` | 셀 판정 모호·혼합 방향 병렬 소자 | 0 |
| `buffer_multi_output` | `E/graph/buffer_bundles.py:57` | 버퍼 묶음 출력 둘 이상 | 0 |
| `composite_over_budget`, `composite_dag_not_chain` | `E/graph/composite_blocks.py:182, 185` | 복합 블록 예산 초과·사슬 아님 | 0 |
| `gate_on_current_node` | `E/graph/drive_kind.py:113` | 전류 노드에 gate | 0 |
| `cycle_enumeration_over_budget` | `E/graph/loops.py:180` | 단순 사이클 열거 > N_S | 0 |
| `view_required` | `E/graph/views.py:84` | 뷰 선언 필요 | 0 |

### 1.3 단계 A 실측 (master `e87092b3`, spec 포함, 13회로)

| 회로 | 묶음 | status | 정지(unsupported) | review_needed |
|---|---|---|---|---|
| common_gate_amplifier, current_reuse_telescopic_ota, folded_cascode, nmcnr_amplifier, pushpull_follower_buffer, sf_pushpull_output_opamp, two_stage_ota, two_stage_ota_sf | library | ok | -- | -- |
| ngcc_3stage_ff | library | review_needed(exit 2) | -- | `dc_role_unresolved_group` M14·M8 (IT-0 V2 기록과 같음) |
| **cnr_ota** | heldout | **stopped** | `cs_output_low_impedance` 2, `loop_record_only` 4, `undeclared_loop_constraint` 2, A4 `column_unassigned`(IDC, x24.M1) | `dc_role_unresolved_group` 4, `l_owner_name_order` 4 |
| **erfc_ota** | heldout | **stopped** | `cs_output_low_impedance` 4, `loop_record_only` 2, `undeclared_loop_constraint` 4, A4 `column_unassigned`(M21) | `dc_role_unresolved_group` 6, `composite_block_pending_ratify` 7, `drive_inherit_cycle` 1, `loop_polarity_conflict` 2 |
| **r2r_opamp** | heldout | **stopped** | `loop_record_only` 3(사유 global_feedback_or_cross_coupled) | `dc_role_unresolved_group` 2 |
| rfc_ota | heldout | review_needed(exit 2) | -- | `dc_role_unresolved_group` 3, `l_owner_name_order` 1 |

- cnr_ota와 erfc_ota는 단계 A에서 이미 멈춘다. 그래서 S0 쓰기 계획 정지(`dc_resistor_cycle`·`mos_zero_current_structural`)는 **두 번째 벽**이다. 앞 벽을 지원해도 그 뒤에서 다시 멈춘다. 이 두 정지는 엔진 import 손 스크립트로 잰 값이다(de1_output_structure_13.md:14).
- review_needed(`dc_role_unresolved_group` 등)는 "지원 밖"이 아니다. 구조로 못 가르는 사실을 `structure.json` ratify 사실로 받는 경로다. 처리기 대상이 아니라 공동분석 대상이다.

### 1.4 쓰기 계획 규칙 분기(W0~W4)와 설계만 된 멈춤

- W0~W4는 **지원 밖 분기가 아니라 writer 등급**이다(`E/sizing/writer_plan.py:8-24`, 고정 노드 F = W0 ∪ W3 ∪ W2(d), 뿌리 W4). 그 안에서 지원 밖은 아래 셋이고 **셋 다 master에 code가 없다**(grep 0, `integ/it12`에도 0 -- 그 브랜치는 IT-0 기록 커밋뿐).
  - `input_port_multiple_roots`: design 41:671·1692(IT-1). library 9 발동 0(IT-0 `M-I1-r/library9/SIM/multi_root_circuits` = 0, 회로별 `n_input_w4_roots` = 1).
  - S-OS1 `icm_config_output_root_w3`: design 41:725(IT-2c 실행 중 fail-closed). 발동 0(IT-0 `OS/13/S-OS1` = 0). 13회로 W3 선언 0(`pending CI-15`)이라 지금은 공허하다(it0-baseline.spec.md:79).
  - S-OS2 `icm_config_differential_output_structure`: design 41:744(2). 발동은 **current_reuse_telescopic_ota(비지 않은 feedback tuple) 1, cnr_ota(빈 tuple `()`) 1**(IT-0 `OS/13/S-OS2_*`). 일반형은 계획 O-68 (2)·O-85 (1)에 있다(plan.md:334, 326).
- 잡음 `()`: 정지가 아니다. `noise_plan`의 세 갈래는 `None` → `undefined`/`noise_feedback_undeclared`, 원소 모름·절단 모호 → `undefined`, `()` → `open`이다(`E/metrics/noise_plan.py:38-52`). `()`의 의미가 다른 독자(β=1)와 갈리는 곳은 이 한 곳이다. 그런데 `noise_out_int_vrms` 제약이 있는 `()` 회로는 0개다(`wt/_drafts/evidence/2026-10-21/feedback_empty_unify_feasibility.md` §0 1-2, 재측정 안 함). 이것은 분기 처리기 문제가 아니라 **의미 통일(계획 문언)** 문제다.

## 2. 엔진의 현재 짜임

| 요소 | 실제 | 근거 |
|---|---|---|
| `@compute_block` | **등록부가 아니라 데코레이터**다. 블록 객체는 READS 투영과 입력 버전(이름+코드 해시+투영 지문)을 만들고, reuse → graft → 실패 재연 → 계산 순서로 처리한다. 결과 키는 WRITES와 정확히 같아야 한다. | `E/core/compute_block.py:1-26, 125-173, 176-190` |
| writer 권한 | 층마다 `WriterTable`(`S1_WRITERS` `E/graph/s1_values.py:194`, `S1V_WRITERS` :215, `S2_WRITERS` `E/sizing/s2_values.py:180`, `METRICS_S0_WRITERS` `E/metrics/s0_fields.py:26`, `SEARCH_S0_WRITERS` `E/search/s0_fields.py:34`)를 `union`해서 `S0_WRITERS`를 만든다(`E/search/s0_fields.py:40`). 같은 필드에 writer가 둘이면 표를 만들 때 바로 오류다. | `E/core/writer_table.py:28-46, 80` |
| 블록 호출 순서 | 손으로 쓴 순차 호출. S1 13블록 `E/graph/s1_build.py:78-90`, S0 쓰기 계획 `E/sizing/kernel_context.py:82-90`, 탐색 S0 `E/search/search_context.py:174-187`. S1v는 큰 블록 하나(`s1v_fields`, `E/graph/s1v_fields.py:249-278`)가 `analyze_view`(일반 함수들)를 부른다. | 같은 줄 |
| 분기 디스패치 | **if/elif 인라인**이다. 표나 등록부는 없다. 정지는 블록 안 `raise`(S1·S0) 또는 Finding 기록 → 한 곳 정지(S1v, `E/pipeline/stage_a.py:240-250`). 지원 kind만 상수 표다(`E/graph/s1_values.py:28-34`). | §1 표 |
| 층 규칙(tests/structure) | A 파일당 진입점 하나, B 남의 `_` 이름 import 금지, **C 층 순서 core<lut<authoring<graph<sizing<metrics<search<layout<convergence<report<pipeline·`__all__` 공개 API만**, D 숫자 리터럴, **E 회로 이름 문자열 금지**, F 광범위 except 금지, **G 모듈 수준 가변 캐시 금지(tuple·frozenset·MappingProxyType 허용)**, H test 1:1, **I 회로별 정보·태그 키로 행동 결정 금지**, K front 조회 경로, M 실행 비공유 | `E/tests/structure/README.md:39-47` 표 |
| 코드 지문 | 블록 입력 버전의 코드 해시는 블록 함수 자신의 code만 덮는다. 엔진 전체 `.py` 지문 `engine_code_fp`가 실행마다 S3 줄 `code_fp`에 들어간다. 그래서 블록이 부르는 다른 파일(처리기)이 바뀌어도 실행 사이 재사용은 code_fp가 막는다. 실행 안 색인은 실행 수명이다(`open_run`). | `E/core/engine_code_fp.py:1-10`, `E/core/compute_block.py:8-21`, `E/pipeline/stage_a.py:33, 208` |

**이음매가 있는가: 없다.** 새 분기를 "새 블록이나 규칙 항목 추가"만으로 붙일 자리는 없다. 가장 가까운 것은 다음 둘이다.

- (a) S1v의 **정지 한 곳 집중**(Finding code가 데이터라 정지 판정이 `stage_a.py:240-250` 한 곳). 다만 분기를 *처리*하는 code는 여전히 `blocks.py`·`loop_classify.py` 안에 인라인으로 있다.
- (b) `UNSUPPORTED_BRANCHES` 상수 표. kind → 분기 이름 표일 뿐 처리기가 없다.

## 3. 사용자 아이디어를 원칙 안에서 다시 쓰기

- "topology마다 엔진"은 세 원칙과 부딪힌다. 회로 식별로 엔진을 고르면 그 자체가 회로별 정보로 행동을 정하는 것이다(규칙 I `E/tests/structure/README.md:47`, 메모리 '회로 전용 금지'). 엔진 선택 키가 topology 이름·태그가 된다(규칙 E·I, analog-grammar 금지). 그리고 같은 양(동작점·창)을 엔진마다 따로 계산하게 되어 둘째 생산자가 생긴다(graph 단일 정본 1·3).
- 원칙과 맞는 꼴: **분기 키 = 연결·물리로 정의된 rule_branch code**(이미 `detail["rule_branch"]`·Finding.code로 있다). 판정(어느 분기인가)은 소유 블록이 연결만으로 하고, 처리(그 분기에서 값 계산)는 등록된 처리기가 한다.
- §1 정지들의 부류 대응: 모두 **연결·물리 부류**다. 이름 붙은 topology에 대응하는 것은 하나도 없다.
  - 원소 kind(`*_kind_unsupported`), 그래프 위상(`dc_self_loop`, `dc_isolated_loop`, `gvgs_self_edge`, `dc_resistor_cycle`), KCL 기저(`mos_zero_current_structural`, `ds_self_swap_zero_current`), 귀속(`column_unassigned`), 임피던스 등급(`cs_output_low_impedance`), 루프 분류 (4)(`loop_record_only`), 예산(`*_over_budget`), 출력 구조(S-OS1 = high_impedance 출력의 writer 사슬 뿌리가 W3 목표, S-OS2 = 출력 포트 ≥2 + 되먹임 선언), 입력 뿌리 수(`input_port_multiple_roots`).
  - 예외: `undeclared_loop_constraint`는 구조가 아니라 **spec 선언 공백**이다. 처리기로 풀 대상이 아니라 spec을 고칠 대상이다(처리기로 기본값을 지어내면 '상수 발명'이 된다).
  - `dc_role_unresolved_group` 같은 review_needed는 ratify 사실 경로다. 처리기 대상이 아니다(회로 해석 공동분석 원칙).

## 4. 최소 변경 design 제안

### 4.1 모양

1. **처리기 = 소유 블록이 부르는 순수 함수**(별도 compute block 아님). 서명은 `handler(projection_view, subject) -> 부분 결과`다. 반환은 소유 블록 WRITES의 부분(특정 key들의 값)이고, 소유 블록이 합쳐 한 번에 쓴다. 이렇게 하면 writer는 여전히 소유 블록 하나다. WriterTable을 바꿀 필요가 없다.
2. **등록부 = 소유 블록 층 안의 불변 표**: `BRANCH_HANDLERS = MappingProxyType(...)`. 규칙 G는 `MappingProxyType`을 허용한다(`E/tests/structure/README.md:45, 134`). 키는 rule_branch code 문자열 상수이고, 같은 키 중복은 모듈 로드 때 `ValueError`로 막는다(WriterTable과 같은 꼴). 층 규칙 C 때문에 등록부는 **소유 블록과 같은 하위 패키지**에 둔다(전역 등록부 하나는 층 역류를 만든다).
3. **디스패치 = 지금의 정지 자리 그대로.** 예: `writer_plan.py:176`의 `raise` 앞에서 `BRANCH_HANDLERS.get(branch)`를 조회한다. 없으면 지금과 같은 `StructureUnresolvedError`를 같은 detail로 낸다(fail-closed 불변). 있으면 처리기를 부른다. S1v는 Finding을 만드는 자리에서 처리기가 있으면 severity를 `unsupported`가 아니라 처리 결과로 바꾸는 꼴이다(DEC-59 '계산 규칙 있음/기록만' 속성 = 등록 여부).
4. **처리기의 READS ⊆ 소유 블록 READS.** 처리기는 투영만 받으므로 소유 블록 선언 밖 필드를 읽을 수 없다(`Projection`, `E/core/compute_block.py:8`). 처리기가 새 필드를 읽어야 하면 소유 블록 READS 선언을 바꾼다. 그러면 입력 버전도 같이 바뀐다.
5. **새 양이 필요하면** 처리기가 아니라 계획에서 새 필드와 그 writer 블록을 정한다(단일 정본 3·6, S-7).

### 4.2 처리기가 통과해야 할 계약 test

1. 등록 키가 정지 code 목록(`s1_values.py`/`s2_values.py`/`s1v_values.py` 상수)에 있는 것만 쓰는가. 같은 키에 처리기가 둘이면 거부한다.
2. 처리기 반환 키 ⊆ 소유 블록 WRITES 키, 반환 subject ⊆ 그 분기가 발동한 subject. 서로 다른 처리기가 같은 (필드, key)를 내면 소유 블록이 fail-closed한다(아래 4.4).
3. **미등록이면 그대로 정지**: 처리기를 빼면 기존 detail과 비트 동일한 정지가 나오는가(양성 대조 -- '게이트는 실제로 거부한다' 원칙).
4. **무동작**: 그 분기가 발동하지 않는 회로(13회로 전수)에서 등록 전후 모든 graph 필드 지문이 같은가(메모리 '일반화 측정').
5. 처리기 소스에 회로·소자·θ 이름이 없는가(규칙 E·I는 자동 적용). 처리기가 금지 태그 키를 읽지 않는가(규칙 I-a).
6. 처리기가 모듈 수준 가변 상태·memo를 갖지 않는가(규칙 G). 블록 안 local memo만 승인 예외 O-15 (E).
7. 발동 회로 손계산 오라클(작성자 ≠ 검증자): 처리기 결과 = 손계산.

### 4.3 변경 크기

| 변경 | 파일 | 크기 |
|---|---|---|
| 등록부 한 개(첫 소유 블록 하나만) | 새 파일 1개(예: 소유 블록 하위 패키지 안 공개 진입점 하나 -- 규칙 A) + 그 하위 패키지 `__init__.py` `__all__` 한 줄 + test 1:1(규칙 H) | 작음 |
| 소유 블록 정지 자리 | 그 블록 파일 한 곳(raise 앞 조회 몇 줄) | 작음 |
| 처리기 하나 | 새 파일 1개 + test 1개 + 등록부 한 줄 | 분기 규칙 크기만큼(이음매와 무관) |
| core | **변경 0**(compute_block·WriterTable·Projection 그대로) | -- |
| 재작성 | **불필요** | -- |

- 범위 경고: §1 정지 자리는 소유 블록이 **10곳 이상**으로 흩어져 있다(S1 8개 블록, S1v 생산 함수 9곳, S0 2곳, ss 1곳). 모든 소유 블록에 등록부를 미리 깔면 소비자 0인 장치가 된다(만들면 배선 원칙 위반, DEC-76 '발동 0은 만들지 않는다'). 그래서 **발동 회로가 있는 소유 블록 하나에만** 넣고, 둘째 소유 블록은 그 분기에 실제 소비자가 생길 때 같은 꼴로 넣는다.
- "core 파일을 안 고친다"는 성립한다. 하지만 "아무 기존 파일도 안 고친다"는 성립하지 않는다. 처리기마다 등록부 한 줄, `__all__` 한 줄, (READS가 늘면) 소유 블록 READS 선언이 바뀐다. 구조 규칙 C·H상 불가피하고, 그 편이 맞다(입력 버전이 READS를 따라가야 하므로).

### 4.4 graph 단일 정본 위험과 막는 법

| 위험 | 막는 법 |
|---|---|
| 처리기 둘이 같은 필드에 씀 | 처리기는 직접 쓰지 않는다. 소유 블록이 반환을 합칠 때 (필드, key) 겹침을 단언하고, 겹치면 fail-closed한다. 별도 블록으로 쓰려 하면 WriterTable이 먼저 막는다(`E/core/writer_table.py:39-43`). |
| 한 회로에서 두 분기가 함께 발동(예: 출력 둘 중 하나 S-OS1, 다른 하나 S-OS2) | subject(출력 넷)별로 key가 나뉘어야 한다. 같은 subject에 둘이 걸리면 정의 불능이다(O-85 (1) '두 출력 판정이 갈리면 정의 불능'과 같은 규칙). |
| 처리기가 다른 블록 소유 양을 다시 계산(둘째 생산자) | READS로만 읽는다. 예: S-OS2는 `kvl_sensitivity`(design 41:734 (3))를 불러야 하고 감도 연립을 다시 쓰면 안 된다(O-68 (2) '기존 `kvl_sensitivity` 닫힘 행 k ∈ {1,2}'). |
| 처리기별 cache·memo·사본 | 규칙 G + 브리핑 금지 조항, S3 graft만. |
| 등록부 자체가 "값 칸"이 되는 것 | 등록부는 함수 참조뿐이고 계산값을 담지 않는다. 함수 code 변경은 `engine_code_fp`가 실행 사이 재사용을 끊는다. |
| 판정(detection)과 처리의 둘째 판정 | 분기 판정은 소유 블록 하나만 한다. 처리기는 받은 code를 다시 판정하지 않는다. |

### 4.5 계획·design 문서 변경(PDCA 순서)

1. **계획 먼저**(S-7, 메모리 '계획과 다르면 계획부터'): DEC-59에 "`계산 규칙 있음` 분기 = 소유 블록 등록부에 처리기가 있는 분기"라는 문장을 넣고, DEC-76에 "미등록 = 기존 안전망 정지"를 넣는다. N3.4(writer 권한)에는 "처리기는 writer가 아니다·반환은 소유 블록이 쓴다"를 넣는다. N3.14 실패 규약은 변경 없음을 확인한다. **원래 취지와 다른 점**: 사용자가 말한 "topology 엔진 추가"를 "규칙 분기 처리기 추가"로 바꾼 것이다. 이 바꿈 자체를 사용자 결정으로 받아야 한다.
2. 독립 계획 검증 → 사용자 승인.
3. design 40 §2.4(compute block 절)에 등록부 계약(4.1·4.2)을 둔다. design 41 §4.7-3b `icm_config`의 정지 S-OS1·S-OS2 자리를 디스패치 자리로 바꾼다. 소유 패키지 CONTRACT.md에 등록부 표를 둔다. 함수 레지스트리 문서(`docs/03-analysis/...function-registry.md`)에 개념 행을 하나 둔다.
4. design ↔ 계획 gap → 구현(code/test 역할 분리) → gap 분석.

## 5. 판정과 첫 분기

- **판정: 조건부 가능.**
  - 조건 1: topology 단위가 아니라 rule_branch 단위로 한다.
  - 조건 2: 처리기는 writer가 아니다. 소유 블록 READS/WRITES 안에서 계산하고, 소유 블록이 쓴다.
  - 조건 3: 등록부는 발동 회로가 있는 소유 블록 하나부터 둔다(DEC-76).
  - 조건 4: 계획 개정·사용자 승인이 먼저다.

  core 변경과 재작성은 필요 없다. 이음매 자체는 작은 변경이다. 실제 비용은 분기마다의 **계산 규칙(물리)**을 계획에 정하는 일이다. 이음매는 그 비용을 줄이지 않는다. 바꿔 주는 것은 "규칙이 정해진 뒤 붙이는 자리"가 소유 블록 본문이 아니라 독립 파일·등록 한 줄이 된다는 점과, fail-closed가 등록 여부 하나로 정해진다는 점이다.
- **첫 분기 권고: S-OS2 `icm_config_differential_output_structure`.**
  - 근거 (1): 일반형 규칙이 계획에 이미 있다. 차동 모드만 닫음, 입력 CM = x, 출력 CM은 CMFB, `kvl_sensitivity` 닫힘 행 k ∈ {1,2}(plan.md:334 O-68 (2)). 두 출력 판정 불일치 = 정의 불능(plan.md:326 O-85 (1)).
  - 근거 (2): library 소비자가 있다. current_reuse_telescopic_ota(IT-0 OS 칸 1). 이 회로는 오늘 단계 A ok이고 S0 쓰기 계획도 통과한다(IT-0 칸이 채워짐).
  - 근거 (3): 소유 블록 `icm_config`가 IT-2c로 새로 만들어진다. design이 이미 S-OS2를 fail-closed로 시작하게 정했으므로(design 41:17 v1.12.4 (2)) "미등록 정지 → 등록 처리기"가 그대로 이음매의 양성·음성 대조가 된다.
  - 주의 (가): IT-0에서 이 회로의 `M-I3 n_front`는 AB·SIM 모두 0이다. 그래서 front 끝까지의 효과 관측은 미확인이다(n_front 칸 의미를 이번에 확인하지 않음).
  - 주의 (나): cnr_ota의 `()` 발동은 heldout이고 단계 A에서 이미 멈추므로 소비자가 아니다.
- **고르지 않은 후보와 이유**:
  - `dc_resistor_cycle`(cnr_ota)·`mos_zero_current_structural`(erfc_ota): heldout뿐이다. 앞 벽(단계 A `cs_output_low_impedance`·`loop_record_only`·`column_unassigned`)이 있어 끝까지 가는 소비자가 없다.
  - `loop_record_only`(r2r_opamp 등): heldout뿐이다. DEC-59상 library 발동·ratify가 먼저다.
  - `input_port_multiple_roots`·S-OS1: 발동 0(공허)이다.
