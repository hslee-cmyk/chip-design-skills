---
template: design
version: 1.5
plan_version: 6.3
---

# gain-budget-gmid-sizing -- 40-engine Design Document (새 엔진 `gmid_engine`, 색인·아키텍처)

> **Summary**: 새 gm/ID 사이징 엔진(`skills/analog-gmid-design/gmid_engine/`)의 설계 정본이다. 계획서 N3.1 흐름 GB0~GB9를 패키지·파일에 대응시키고, 단계마다 알고리즘·입출력·불변식·실패 코드·as-built 상태를 적는다. 계획서가 요구하고 실행 로드맵에서 빠졌던 gain-budget 흐름(FR-1·FR-2·FR-4·FR-8)은 `41-gain-budget`에서 전부 설계한다. gap 분석 기준표는 `42-gap-checklist`다.
>
> **Project**: chip-design-skills (analog-gmid-design skill) · **Author**: Claude Code
> **Date**: 2026-10-08 · **Status**: v1.5. 사용자 결정 2026-10-08 "j해석은 네의견에 모두 동의해."(J 공동분석)를 반영했다.
> - §3.2-3: `structure.json` concept 어휘 5개 신규, override/confirm 소비, `structure_rule_fp`, 단계 A 파이프라인 수정(`declared_loop_cuts`·사실 로드 순서), 회로별 사실 표(U1b 병합 뒤 작성)
> - §3.8-8: `ff_gm_ratio`, SP-2 (c) `icm_margin_v`
> - §9.2: sf `icm_margin_v` 제약
> - §9.3: J 결정 표 신설
> - §10.1: API 추가
> - §11: 구현 단위 U1b와 J 추가 범위
> - 구조 규칙은 41 §1.12에 있다
>
> v1.4는 사용자 결정 2026-10-08 "q3,q4는 네 제안대로 해"를 반영했다: §3.8-8 offset·미러비·스윙·ICMR metric 7개(닫힌 어휘), §9 Q3·Q4 확정과 §9.2 회로별 선언, §9 Q7 J 목록 추가, §10.2 오라클 Monte-Carlo·DC 스윕, §11 U3·U5·U6·U7·U9·U13 범위. v1.3은 사용자 결정 2026-10-08 "Q1~Q11 모두 네 의견대로 진행해"(§8·§9 확정)를 반영하고, §11 구현 단위를 추가했다. 아래는 v1.2에서 반영한 내용이다.
> - 재검증 지적 N1~N9와 Low 항목
> - 잡음 경로를 범위 안으로 넣기로 한 사용자 결정(2026-10-08)
> - `[ng-layer0-canon]` 49283c6 대칭 실측
> - v1.1에서 반영한 C1~C4, H1~H8, M1~M14, L1~L8과 R19 정정은 유지한다.
> **Planning Doc**: [gain-budget-gmid-sizing.plan.md](../../01-plan/features/gain-budget-gmid-sizing.plan.md) v6.2
> **as-built 기준**: master `004b7d2`(ng-perf-sizing 병합분 포함). 아직 병합되지 않은 브랜치도 함께 본다: `ng-cmfb-pm`(6a6e4c7), `ng-oracle-early`(d56ba66), `ng-tolv-cache`(674a6a1), `ng-layer0-canon`(0c5dc20), `ng-area-budget`(538eeab), `worktree-agent-a90dfb25fa6fe9f04`(7090b9f, LUT r2), `ng-bridge`(d529ea5).

진행 순서는 bkit PDCA다: 이 design → 구현 → gap 분석(`42-gap-checklist`).

## 문서 구성

| 파일 | 내용 |
|---|---|
| `40-engine`(이 문서) | §1 범위·원칙 / §2 아키텍처(흐름·상태 층·패키지 API) / §3 단계별 설계 GB0~GB9(gain-budget 외, §3.2-3 `structure.json` 개념·파이프라인) / §4 SPICE 오라클 / §5 CM(CMFB) 루프 / §6 대칭 / §7 면적 예산·성능 / §8 승인 없이 축소된 범위와 계획 이탈 / §9 사용자 결정(2026-10-08 확정, Q3·Q4 포함, §9.2 회로별 offset·스윙·ICMR 선언, §9.3 J 결정) / §10 신규 API·검증(오라클·DoD·IC test) / §11 구현 단위(병렬 배분) |
| `41-gain-budget` | FR-1(SP1 stage 유도, §1.12 J 구조 규칙), FR-2(블록 gain 모델과 MNA 잔차), FR-3 연계, FR-8(탐색 전 달성 불가), FR-4(층 0 gain 예산 조합 front와 `gain_budget_db`), 스펙에서 gm/ID·L 출발값 유도 |
| `42-gap-checklist` | FR·NFR·DEC·설계 항목마다 한 행: 설계 절, as-built 상태, 증거 위치 |

**표기**: `E/` = `skills/analog-gmid-design/gmid_engine/`. `P` = 계획서. 상태 어휘는 **OK**(as-built가 설계와 같음) / **DEV**(as-built가 설계와 다름. 어떻게 다른지 함께 적음) / **PART**(일부만 있음) / **MISS**(없음). 브랜치에만 있는 것은 `[브랜치명]`을 붙인다.

---

## 1. 범위와 원칙

### 1.1 범위

계획서 N1.3의 FR-1~FR-9, N1.4의 NFR-1~NFR-6, N3.1의 GB0~GB9를 구현한다. 지원 범위와 합격 기준은 계획서 그대로다(N1.2, DEC-59, DEC-85, N6.2 T1~T9). 옛 엔진(`legacy/`)은 참고와 대조 기준선으로만 쓴다(DEC-82).

### 1.2 엔진 원칙(설계 제약)

이 원칙들은 계획서와 사용자 결정에 근거하며, 아래 모든 절의 알고리즘이 지킨다.

| ID | 원칙 | 근거 |
|---|---|---|
| EP-1 | **topology 무관.** 회로·소자·넷 이름으로 분기하지 않는다. 지원하지 않는 구조를 만나면 `unsupported_rule_branch`로 정지한다. 일반성은 library 밖의 합성·변형(metamorphic) test로 잰다 | 사용자 2026-10-07 대원칙 3, DEC-62, WP-05 |
| EP-2 | **같은 값을 다시 계산하지 않는다.** 필드가 곧 캐시다(writer 1개 + 입력 버전). graph 밖 캐시는 LUT memo 하나이고 상한이 있다. 루프 불변식은 S0당 한 번 만든다 | 사용자 2026-10-07 대원칙, NFR-2, WP-23, DEC-83 |
| EP-3 | **책임별 파일 분할.** 파일 구성 규칙 A~D를 따른다. 구조 test 규칙 A~I(`E/tests/structure/structure_checks.py`)는 인용만 하고 여기서 다시 정의하지 않는다 | 사용자 대원칙 2, WP-24 |
| EP-4 | **상수를 지어내지 않는다.** 모든 임계값은 선언값 하나(PDK·LUT·spec)에서 식으로 계산한다. 이 문서도 식만 적는다 | WP-03, N9.2-3 |
| EP-5 | **작성자 ≠ 검증자.** 기대값은 오라클 4종에서만 만든다 | WP-13, N3.11 |
| EP-6 | **LUT·PDK가 출처다.** 공정량(VDSAT·fT·gm/gds·IDu·잡음·용량·격자·MIM 밀도·mismatch 계수)은 LUT 열이나 PDK 선언에서 읽는다. 출처(파일·sha256·행)를 함께 기록한다 | DEC-87, DEC-91, N3.16 PDK 상수 |
| EP-7 | **판정과 출발값을 구분한다.** 근사식·구간·예산 배분은 출발점(층 0)과 보고에만 쓴다. 판정은 언제나 봉인된 스냅샷의 전회로 계산(DEC-74)과 SPICE 오라클이 한다 | DEC-67, DEC-74, DEC-92 (2) |
| EP-8 | **충돌은 보고하고 조용히 풀지 않는다.** 구간이 비거나 선언과 유도가 어긋나면 레코드로 남긴다(`review_needed`·실패 레코드·충돌 표) | DEC-44, WP-02 |

---

## 2. 아키텍처

### 2.1 데이터 흐름 GB0~GB9와 패키지 대응

```
spec + topology + LUT + PDK 선언
  └─ GB0 authoring.load_topology / load_sizing_spec ─────────────── S0 지문
       └─ GB1 graph.build_s1 (DC 역할·미러·L 동치류·가지·기둥·G_vgs·matching) ── S1
            └─ GB2 graph.build_s1v (SP1: 뷰·셀·구동 종류·stage·블록·루프·극점 노드) ── S1v   [41 §1]
                 └─ GB3 graph.coupling_vars (K1~K8, 기둥↔블록 매핑) ── S1v
                      └─ GB4 metrics.achievability (블록 gain 상한·구조 DOF·면적 하한) ─ INFEASIBLE_TARGET  [41 §4]
                           └─ start_intervals (스펙 → gm/ID·L·I 출발 구간) ── 보고 표       [41 §6]
                                └─ GB6 search.layer0 (블록 국소 front → 조합 DP → gain_budget_db → 조립점) [41 §5]
                                     └─ GB6 search.find_front (외층 ε-제약 SLSQP, 비지배 필터)
                                          │  후보 θ마다 평가 커널:
                                          │   GB7 sizing.size_and_seal → 봉인 → GB5 제약 판정 → GB8 metrics.ss_evaluate
                                          └─ GB9 S3 archive, MOD7 layout ⇄ MOD8 W_request, 판정 축 재필터, SPICE 오라클
```

| 단계 | 패키지(MOD) | 주 진입점(공개 API) | 설계 절 | 상태 |
|---|---|---|---|---|
| GB0 spec | `authoring`(MOD2) | `load_topology`, `load_sizing_spec`, `rail_declaration` | §3.1 | PART |
| GB1 구조 | `graph`(MOD3) | `build_s1` 계열(`s1_dc_roles`, `s1_columns`, `s1_gvgs`, `s1_matching_groups`) | §3.2 | PART |
| GB2 stage | `graph`(MOD3) | **신규** `build_s1v` | 41 §1 | MISS |
| GB3 결합 | `graph`(MOD3) | **신규** `coupling_vars`, `column_block_map` | §3.3 | MISS |
| GB4 달성가능성 | `metrics`(MOD5) | **신규** `achievability` | 41 §4 | MISS |
| GB5 보상 | `metrics`(MOD5) + `sizing` θ 스키마 | `ss_evaluate`, `dc_theta_schema`(zero_cancel) | §3.5 | PART |
| GB6 할당 | `search`(MOD6) | `find_front`, **신규** `layer0_budget` | 41 §5, §3.6 | PART |
| GB7 DC | `sizing`(MOD4) | `size_and_seal`, `seal_dc`, `build_kernel_context` | §3.7 | OK(일부 DEV) |
| GB8 metric | `metrics`(MOD5) | `ss_evaluate`, `metric_value`, `area_search`, `supply_currents` | §3.8 | PART |
| GB9 탐색·검증 | `search`·`layout`(MOD7)·`convergence`(MOD8)·`report`(MOD9)·`pipeline`(MOD10)·`tools/spice_oracle` | `archive`, `run_layout`, **신규** `run_gmid_design_pipeline` | §3.9, §4 | PART |

위 그림은 대략의 흐름이다. 실제 계산 순서(S0당 1회 단계 A, 봉인 평가가 필요한 단계 B, 탐색 단계 C)와 그 사이에 순환이 없다는 규칙의 정본은 41 §0의 DAG다.

import 계층은 `core` < `lut` < `authoring` < `graph` < `sizing` < `metrics` < `search` < `layout` < `convergence` < `report` < `pipeline` 이다(P N3.10). GB4·GB5가 MOD5에 있는 이유는 P N3.1 '모듈 열 정정'이다.

### 2.2 상태 층(S0~S3)

| 층 | 정본 | writer | as-built |
|---|---|---|---|
| S0 지문 | topology·LUT·spec·유도 규칙 코드 해시 | `authoring`·`graph.s1_key` | OK |
| S1 구조 | 노드·소자·수동소자·관계 엣지·가지·기둥·matching | `graph` | PART(`l_class` proposed만, declared/ratified 전이 없음) |
| S1v 뷰 | 뷰별 셀·구동 종류·stage·블록·극점 노드·루프·끊는 점 | `graph.build_s1v`(신규) | MISS |
| S2 `dc`/`ss`/`ls`/`layout` | 노드전압·소자 op / 소신호 / 대신호 / 레이아웃 | `sizing` / `metrics` / `metrics`(신규 `ls`) / `layout` | dc OK, ss OK, ls MISS, layout PART |
| S3 탐색 기억 | evals·runs jsonl, front 점 스냅샷 참조 | `search.archive` | OK(기록 타입 결함 §3.9) |

불변 스냅샷·구조 공유·필드 = 캐시는 `E/core/graph_snapshot.py:34,148-200`, `E/core/field_value.py:12-35`, `E/core/compute_block.py:77`에 구현되어 있다(OK).

### 2.3 패키지 간 인터페이스(공개 API)

이미 있는 이름은 각 패키지의 `__all__` 그대로다. **신규**는 이 설계가 추가하는 것이다.

| 공급 → 소비 | API | 형식 | 상태 |
|---|---|---|---|
| core → 전체 | `GraphSnapshot`, `FieldValue`, `compute_block`, `LutMemo`(lut), `FailureRecord`, `exit_code_for`, `normalized_margin`, `read_pdk_decl`, `MetricSignature` | 기존 | OK |
| lut → sizing·metrics·layout | `op_point`, `vgs_for_gm_id`, `vdsat`, `gmb`, `caps`, `tol_v_table`, `tol_vdsat_table`, `curve_report`, `load_lut_set` | 기존 | OK |
| lut → 41 §6 | **신규** `ft_curve(kind, L, VDS, VSB)`, `intrinsic_gain_curve(...)`, `vdsat_curve(...)`, `idu_curve(...)`(gm/ID 축 곡선), **신규** `vgs_for_current_density`(DEC-88) | (gm/ID 배열 → 값 배열), LUT 곡선 표 memo | MISS(조합으로는 계산 가능) |
| authoring → graph·search | `SizingSpec`(제약·목표·θ 범위·설정), **신규 필드** `gain_budget_db_override`, `driving_spec`, `untie_orbits`(옛 설계 이름 `symmetry_untie`), `cm_sense_elements`[ng-cmfb-pm], `element_values.*.measurement_load`[ng-area-budget] | spec 로더 | PART |
| graph → sizing·search·metrics | S1(기존), **신규** `S1v{views[], blocks[], pole_nodes[], loops[], cuts[], coverage}`, **신규** `orbits`(자기동형 궤도) | S1v 스냅샷 필드 | MISS |
| sizing → search | `size_and_seal`, `build_kernel_context`, `dc_theta_schema`, `dc_current_basis` | 기존 | OK |
| metrics → search | `ss_evaluate`, `metric_value`, **신규** `block_local_gain`, `achievability`, `ls_fields` | | PART |
| search → layout·report·pipeline | `find_front` → `FrontPoint`, `node_across_front`, **신규** `layer0_budget` → `BudgetCombination{gain_budget_db, ...}` | | PART |
| layout ⇄ convergence | `run_layout` → `LayoutResult{W_requests, revalidation}`, **신규** `converge(snapshot)` | | MISS(MOD8) |
| pipeline | **신규** `run_gmid_design_pipeline(spec, *, search, output_dir, instrument, activations_out)` | exit code = `exit_code_for` | MISS(`[ng-bridge]`에 오라클 입력 생산자만) |

---

## 3. 단계별 설계 (gain-budget 핵심은 41)

### 3.1 GB0 -- spec·topology 로드 (MOD2)

**알고리즘**: topology를 닫힌 어휘로 읽고 거부 게이트를 순서대로 적용한다: `supply_nets` 필수 → 숨은 레일 (iii) → 넷 대소문자 유일 → `bias_inputs` 선언·gate 전용 → `source_manifest` 수 대조 → 태그 키 무시(U-50). spec은 출처 필수 제약, 정본 이름, `optional_stages` 화이트리스트, θ 범위를 읽는다.

**출력**: 검증된 `Topology`, `SizingSpec`, S0 지문. **실패**: `SchemaRejectedError`(exit 7).

**이 설계가 추가하는 spec 필드**(MOD2 로더):

| 필드 | 형식 | 소비자 |
|---|---|---|
| `gain_budget_db_override` | `[{block: [출력노드 넷 이름, ...], value_db, source}]`. 블록 키는 출력노드 이름을 정렬한 배열이다(41 §1.7-3) | 41 §5.7 |
| `structure_count_budget` | `{value, source}`, 선택 항목. 없으면 LUT 격자에서 유도한 값을 쓴다(41 §0) | 41 §0 |
| 잡음 제약 `noise_th_in_v2hz`·`noise_fc_in_hz`(보고), `noise_excess_th`(가드), `noise_out_int_vrms`(폐루프 적분) -- 주파수·대역 필드 없음(41 §7.1: 주파수를 숫자로 고르지 않는다, `freq_hz`는 `unknown_key`). 옛 이름 `noise_in_density_ss_v_rthz`·`noise_in_integrated_ss_v`는 `metric_unknown` | `constraints[]` 행, `source` 필수 | 41 §7.1 |
| `driving_spec` | `{slew_rate_v_per_s?, load_peak_amp?, load_dc_amp?, source}` | §3.8 `ls` |
| `search.untie_orbits`(as-built, 옛 설계 이름 `symmetry_untie`) | `{원소 이름: {source}}`(MOS·수동소자, `user_spec`만, 원소가 topology에 없으면 `untie_element`) | §6 |
| `cm_sense_elements` | `[<요소 이름>]` + `source: user_spec` | §5 `[ng-cmfb-pm]` |
| `element_values.<el>.measurement_load` | bool | §7.1 `[ng-area-budget]` |

| 항목 | 상태 | 증거 |
|---|---|---|
| topology 게이트(supply_nets·숨은 레일·manifest·태그 키) | OK | `E/authoring/rails.py`, `hidden_rails.py:16`, `source_manifest.py:19`, `topology_schema.py:22` |
| gate 전용 바이어스 넷 | DEV(승인됨): `ports` role 대신 최상위 키 `bias_inputs`(사용자 Q9 (i)). 계획서 DEC-94 문구를 고쳐야 한다 | `E/authoring/bias_inputs.py:20` |
| 옛 이름 거부 | DEV: topology에는 `legacy_name` 표가 없다(닫힌 어휘로 대신 거부). spec 옛 이름 표가 정본 이름 `input_dc_net`·`topology_hash`·`derived`를 거부한다. topology `ports.direction`을 필수로 받는다(N3.16에서는 흡수 대상) | `E/authoring/_spec_fields.py:28-33`, `authoring/CONTRACT.md:151-152,201` |
| `gain_budget_db_override`·`driving_spec` | MISS: 로더가 `unknown_key`로 거부한다 | `authoring/SPEC_CONTRACT.md:226-228` |
| `spice_unverifiable[]` 사전 출력(DEC-90 (3)). **형식**(2026-10-09 정의): metric 서명(`MetricSignature`, 레지스트리와 계산 대기 카탈로그 모두)에 `oracle_measure: str \| None` 필드 -- 그 metric을 재는 오라클 measure 이름(`tools/spice_oracle` 출력 이름, 엔진은 이름만 들고 오라클을 import하지 않는다), 잴 수 없으면 None. spec 로더가 `SizingSpecDoc.spice_unverifiable` = 판정 제약(`judged`) 중 `oracle_measure is None`인 metric 이름 tuple(정렬)을 만들고, 단계 A 보고서 맨 앞에 실행 전 출력한다. 대응표는 metrics CONTRACT에 두고 U6 measure(잡음·offset MC·스윙·ICMR 포함)로 채운다 | MISS | -- |
| 면적 예산 제약 | PART: master는 `objective.budgets` 형식만 있다(9회로 모두 pending). 제약 행은 `[ng-area-budget]`에 있다 | `E/authoring/spec_settings.py:62` |

### 3.2 GB1 -- 구조 유도 (MOD3)

**알고리즘**은 P 용어집 '소자 역할'과 DEC-17·60·61·64·71·93을 따른다. 처리 순서: DC 전도 그래프(잎 가지치기·병렬 합침) → 가지·기둥 → DC 역할 → `equal_vgs`·kcl 그룹 → G_vgs 사이클 v0/v1/v2/VDS-1 → matching 레코드 → L 동치류와 그 주인.

**불변식**:
- 모든 유도 사실에 status와 evidence{rule, nets}가 있다.
- `review_needed`가 남아 있으면 GB4 앞에서 `StructureUnresolvedError`(exit 2)로 정지한다.

| 항목 | 상태 | 증거 |
|---|---|---|
| DC 역할(묶음 4개, 멤버 10) | OK. 규칙 (4) `structure.json` 상속은 MISS | `E/graph/dc_roles.py:52` |
| 가지·기둥(파일럿 41/62) | OK | `E/graph/columns.py` |
| G_vgs 분류 | OK | `E/graph/gvgs_cycles.py:56` |
| matching(J14·DEC-93, `mirror_tail_ratio`) | OK | `E/graph/matching_groups.py:78` |
| 차동쌍 유도 조건 '신호 gate 정확히 2' | PART: 뷰가 없어 바이어스 형제를 빼는 단계만 적용한다 | `graph/CONTRACT.md:538` |
| L 동치류 주인(DEC-17)과 L 공유(LR1) | DEV: `l_class`가 proposed라 평가 경로가 읽지 않는다. 소자마다 L이 따로 있다 | `graph/CONTRACT.md:220`, `E/sizing/theta_schema.py:6` |
| 교류접지 | PART: 정적 (1)(2)만 있다. (3) 이상 전압원은 정지, (4) 뷰별 바이어스 종속 넷은 41 §1.2로 넘긴다 | `E/graph/ac_ground_static.py` |
| 기둥↔블록 매핑표, `vertical_stack_id` 대조 | MISS. 블록(41 §1)이 생긴 뒤 §3.3에서 만든다 | -- |
| `structure.json` ratified 로드, declared/ratified 전이 | PART `[u1-sp1]`: 로더와 `drive_kind`·`stage_members` 소비만 있다. 아래 보완 3의 신규 concept, confirm 전이, `structure_rule_fp`는 MISS(U1b) | `[u1-sp1] E/graph/structure_load.py` |
| 복합 diode(41 §1.12.1)를 DC 역할 규칙 1로, `dc_role` 상속(규칙 4) | MISS(U1b) | `E/graph/dc_roles.py` 규칙 4 '구현하지 않는다' |
| L 동치류 주인 `main_path_signal`(41 §1.12.5) | MISS(U1b). as-built는 tail → current_source_member → name_order | `[u1-sp1] E/graph/l_classes.py` |
| 단계 A가 `declared_loop_cuts`를 넘김 | MISS(U1b) | `[u1-sp1] E/pipeline/stage_a.py` `run_stage_a`의 `build_s1v` 호출 |

**설계 보완**:
1. L 동치류는 GB1이 `derived`로 낸다. 증거는 LR1 규칙(같은 gate 넷·같은 source 넷·같은 kind인 `equal_vgs` 멤버)이다. θ 스키마는 동치류당 L 변수 하나를 둔다. 주인 선택은 DEC-17 순서를 따르되, 'gain 제약 전달 뷰의 첫 gain stage에 붙은 tail' 판정은 GB2 S1v가 생긴 뒤에 확정한다.
2. `structure.json` 로더를 둔다. `topology_hash`·`rule_hash`가 S0와 맞을 때만 ratified 사실을 적용하고, 다르면 해당 사실을 `review_needed`로 되돌린다(P N3.3 전이 표).
3. **`structure.json` 개념 어휘·소비 방식·파이프라인**(J 공동분석, 사용자 결정 2026-10-08 "j해석은 네의견에 모두 동의해."). 구조 규칙은 41 §1.12에 있다. 여기서는 회로 해석 사실을 담는 그릇과 그 소비만 정한다.

   **형식**(P N3.3 그대로): `{schema_version, topology_hash, rule_hash, facts[{concept, subject, value, status: "ratified", evidence{rule, nets[]}, approval_id}]}`. `subject`·`value`는 문자열이다. 넷·소자 이름 여럿을 담는 subject는 이름을 정렬한 **JSON 배열 텍스트**로 쓴다(예: `["M6","M8"]`). 구분자 문자열을 쓰지 않는 이유는 블록 키(41 §1.7-3)와 같다.

   **concept 어휘**(닫힌 어휘. 밖의 이름은 `SchemaRejectedError`, gate `structure_json`):

   | concept | subject | value 어휘 | 소비 방식 | 소비 코드 |
   |---|---|---|---|---|
   | `drive_kind`(기존) | 넷 | `voltage` \| `current` | override | `build_s1v`(구동 종류 고정, `[u1-sp1]` 구현됨) |
   | `stage_members`(기존) | 출처 이름 | 소자 이름(공백 구분, 기존 형식) | declared 대조 | 단계 A → `declared_compare`(`[u1-sp1]` 구현됨) |
   | `dc_role`(신규) | 소자 | `signal` \| `bias_current_source` \| `diode_reference` \| `diode_reference_composite` \| `diode_reference_composite_cascode` | 유도 결과가 J-U3-c `review_needed`인 소자는 **override**, 그 밖은 **confirm** | `E/graph/dc_roles.py` 규칙 4(상속, J-U3-b. 사실이 생겨 구현한다) |
   | `loop_role`(신규) | 루프 id | `loop_view` \| `compensation_internal` \| `composite_diode_internal` \| `bias_scc` | confirm | `E/graph/loop_roles.py` |
   | `feedforward_cell`(신규) | 소자 | `ff:<탭>-><merge>` \| `ff_bias:<탭>-><merge>` \| `ff_load:<탭>-><merge>` | confirm | `E/graph/feedforward_cells.py` |
   | `ac_ground_exception`(신규) | 넷 | 뷰 id | override(그 뷰 한정, 41 §1.12.6) | `E/graph/ac_ground_view.py` |
   | `matching_pair`(신규) | 소자·수동소자 쌍(JSON 배열) | `branch_symmetric` | override(레코드 추가, status ratified, evidence에 approval_id) | `E/graph/matching_groups.py` |

   - 루프 id: 루프 뷰는 as-built 뷰 id `loop:<끊는 소자>:<끊는 넷>`이다. 루프 뷰가 아닌 사이클은 정준 회전(이름 정렬 첫 노드에서 시작)의 노드 이름 JSON 배열이다.
   - `<탭>`·`<merge>`가 넷 이름이므로 `feedforward_cell` value는 `->`로 잇는다. 넷 이름에 `->`가 들어 있는 topology는 로드에서 거부한다(`structure_value_ambiguous`).
   - **L 동치류 주인은 사실로 두지 않는다**. 41 §1.12.5 규칙의 산출이다.

   **소비 방식**(사실을 조용히 버리지 않는다, EP-8):
   - **override**: 엔진이 구조로 정하지 못하는 값을 사실이 정한다. 적용한 사실은 S1v `applied_facts`에 남긴다.
   - **confirm**: 엔진이 유도한 값과 대조한다.
     - 같으면 그 유도 레코드의 status를 `ratified`로 올리고 approval_id를 붙인다.
     - 다르면 `review_needed`(`structure_fact_mismatch{concept, subject, derived, ratified}`)다.
     - 엔진이 그 subject를 만들지 않았으면 `review_needed`(`structure_fact_orphan`)다.
   - **declared 대조**: 기존 그대로다.

   **rule_hash**:
   - `structure_rule_fp()`는 사실이 대조하거나 덮어쓰는 값을 만드는 모든 graph 파일의 지문이다. 대상 = `S1V_RULE_FILES` ∪ {`composite_diode.py`, `dc_roles.py`, `gs_groups.py`, `matching_groups.py`, `feedforward_cells.py`, `loop_roles.py`}.
   - 로더는 `s1v_rule_fp()` 대신 이 지문으로 stale을 판정한다. as-built는 S1v 파일만 보므로 S1 쪽 소비 파일이 바뀌어도 stale을 못 잡는다.
   - **작성 순서**: 사실 파일은 U1b 코드가 master에 병합된 **뒤에** 그 코드의 `structure_rule_fp()`로 쓴다. 먼저 쓰면 코드 병합 즉시 `structure_fact_stale`로 되돌아간다.
   - **규칙 파일이 나중에 바뀌면**: 사실은 stale(review_needed)이 된다.
     - confirm 사실은 오케스트레이터가 새 코드의 유도 결과가 사실과 전부 같음을 보인 대조 기록을 남기고 새 rule_hash로 다시 쓴다. 해석이 바뀌지 않았으므로 같은 approval_id를 쓴다.
     - override 사실은 사용자가 다시 확인해야 한다.

   **파이프라인 수정**(`E/pipeline/stage_a.py`, `[u1-sp1]` 기준 `run_stage_a`):
   1. 순서: A1 로드 → **사실 로드**(topology 지문 = `doc.connectivity_fp`라 `build_s1` 전에 이미 있다) → `build_s1(doc, supplies_v, structure=facts)`(`dc_role` 사실 소비) → `build_s1v(..., structure=facts, declared_loop_cuts=cuts)`.
   2. `cuts`: spec 루프 뷰 선언(`ViewDecl` kind loop)의 끊는 넷 중 안정도 제약 행(`pm_*` metric)이 그 뷰를 가리키는 것이다. 단계 A가 spec에서 직접 계산한다(authoring 소유 파일을 고치지 않는다). 지금 `[u1-sp1]` `stage_a.py`는 이 인자를 넘기지 않아, spec에 루프 안정도 제약을 선언해도 `undeclared_loop_constraint`가 풀리지 않는다.
   3. S1 키에 적용된 `dc_role` 사실의 지문을 넣는다. 같은 topology라도 사실이 다르면 S1이 다르다.
   4. 단계 A 보고서에 다음을 출력한다: `applied_facts`, `structure_fact_*` 기록, `ff_ratio_candidates`, `buffer_window_report`(41 §4.6), `required_input_cm_v`(SP-2 (c) 회로).

   **회로별 사실 표(작성 예정 -- U1b 병합 뒤 오케스트레이터가 쓴다)**: 아래는 J 결정이 정한 내용이다. confirm 사실은 U1b 9회로 실측 결과가 이 값과 같을 때만 쓴다. 다르면 쓰지 않고 차이를 보고한다.

   | 회로 | concept | subject | value | 방식 | 근거(패킷) |
   |---|---|---|---|---|---|
   | ngcc_3stage_ff | `feedforward_cell` | M6B, M6A, M7 / M5 | `ff:ND->Vout` / `ff_load:ND->Vout`(M6A) / `ff_bias:ND->Vout`(M5) | confirm | A.5 |
   | ngcc_3stage_ff | `feedforward_cell` | M14 | `ff:V1->Vout` | confirm | A.5 |
   | ngcc_3stage_ff | `loop_role` | `loop:M8:V1` | `compensation_internal` | confirm | B.5 |
   | ngcc_3stage_ff | `dc_role` | M8, M14(각 1행) | `signal` | override(J-U3-c 그룹) | F.3 |
   | nmcnr_amplifier | `loop_role` | `loop:M201:NodeM2` | `compensation_internal` | confirm | B.5 |
   | current_reuse(파일럿) | `ac_ground_exception` | Vbias2 | `loop:M37a:Voc` | override | C.6 |
   | current_reuse(파일럿) | `dc_role` | M58, M63 | `diode_reference_composite` | confirm | C.6 |
   | sf_pushpull_output_opamp | `dc_role` | M6, M8, M14 / M5, M7, M13 / M9, M17, M11, M16, M20 | `diode_reference_composite` / `diode_reference_composite_cascode` / `bias_current_source` | confirm | D.6 |
   | sf_pushpull_output_opamp | `loop_role` | 복합 diode 내부 사이클 9개 | `composite_diode_internal` | confirm | D.6 |
   | sf_pushpull_output_opamp | `matching_pair` | `["M6","M8"]`, `["M5","M7"]`, `["R1a","R1b"]` | `branch_symmetric` | override | D.5 |
   | sf_pushpull_output_opamp | `drive_kind` | N17, N20 / N910, N1112, N1516 | `voltage` / `current` | override -- **U1b 뒤에도 엔진이 못 가르는 넷만** | D.6, J12-b |

### 3.3 GB3 -- 결합 변수 y와 기둥↔블록 매핑 (MOD3)

**왜 필요한가**: 41 §5의 층 0 조립은 블록 국소 해들을 이어 붙이면서 블록 경계를 넘는 관계를 등식으로 풀어야 한다. 그 관계 목록이 y다. 따라서 GB3은 정밀 경로만의 기능이 아니라 기본 경로 조립의 입력이다(§8 R2).

**알고리즘**: S1v 블록(41 §1)과 S1 관계 엣지를 대조해 아래 레코드를 만든다.
- K1: 부하 소자가 다른 블록의 미러·L 동치류에 속함.
- K2: 블록을 가로지르는 `equal_vgs`.
- K3: 블록 경계를 넘는 `stacked_vsb`.
- K4: 공유 가지·기둥의 노드전압(매핑표의 공유 소자).
- K7: 여러 뷰가 공유하는 소자.
- K8: 측면 주입.

각 레코드는 `CouplingVar{kind, members, blocks, domain, init_rule}`이다. 매핑표 `column_block_map{column, block, device, shared}`는 S1 기둥과 S1v 블록을 교차해서 만든다.

**불변식**:
- 어느 블록에도, 어느 바이어스 기둥에도 속하지 않는 소자가 있으면 정지한다(`StructureUnresolvedError`, 사유 `column_unassigned`, DEC-71 (2)).

**상태**: MISS. as-built의 y는 W4 창 위치 [0, 1]로만 있다(`E/search/search_domain.py:97`).

### 3.4 GB4 -- 달성가능성 (MOD5) → 41 §4

41 §4는 다섯 단계로 이루어진다.
1. **LUT 곡선 검사 → 해법 매핑**(41 §4.1). 곡선 칸을 세 가지로 처리한다.
   - 단조이면 역산한다.
   - 비단조이거나 Fritsch–Carlson(FC) 조건을 어기면 격자 전수로 계산한다.
   - 단위가 맞지 않으면 로드를 거부한다.
2. **블록 gain 상한**(41 §4.2). LUT 격자를 전수 계산해 행 memo로 남긴다. 예산을 넘으면 그 상한은 '미상'으로 둔다.
3. **Σ 판정**(41 §4.3).
4. **인증된 면적 하한**(41 §4.4).
5. **DOF**(41 §4.5).

| 항목 | 상태 | 증거 |
|---|---|---|
| LUT 곡선 칸 분류 | PART: 분류는 있다. 해법 매핑이 없고, `op_point`는 FC 위반 칸에서 사유 기록 없이 선형으로 넘어간다 | `E/lut/lut_set.py:124-173`, `E/lut/curve_check.py:37` |
| 2~5 | MISS | `grep -rn "achievab\|block_gain_bound" E/` 0 |

### 3.5 GB5 -- 보상 (MOD5 + sizing θ)

**규칙**은 DEC-92다.
- 값이 선언되지 않은 보상 수동소자는 θ의 연속 성분이다.
- GBW·PM은 봉인된 `ss` 스냅샷의 전회로 MNA로 판정한다.
- 영점 상쇄 저항은 R = 1/Σgm(S)로 정한다(J7).
- `gm_req`는 같은 스냅샷 MNA에서 1-D 근으로 구한다.
- 근사식은 층 0 출발값에만 쓰고, 근사와 MNA의 차를 `comp_approx_gap`으로 기록한다.

**보상 수동소자 후보 집합**은 S1v 극점 노드 목록의 두 노드 사이에 걸린 수동소자다(41 §1.7). 다음 둘은 후보에서 뺀다.
- 루프 뷰 (3-b)의 복귀 경로에만 있고 (2) Miller 구간에 없는 수동소자. 예: CM 감지 평균 저항. 이것이 6a 열린 항목 ⑤의 해법이다.
- spec이 feedback이나 CM 감지 소자로 선언한 요소.

**단일단**: 단일단 여부는 태그가 아니라 구조로 판정한다. S1v에서 이득 블록이 하나이고 Miller (2) 루프가 없으면 단일단이다. `compensation: null` 태그는 읽지 않는다(U-50, DEC-85). 단일단이면 gm_1 ≥ 2π·`gbw_target_hz`·C_out,total을 θ 제약으로 둔다(U-12 기본안). C_out,total = `ss.node_c_farad`(출력노드) + 부하 요소 값이다. U-12가 확정되기 전에는 이 행을 '보고만' 한다. 출발값은 41 §6.5의 매크로 모델에서 같은 값이 나온다.

**CM 감지 소자**(사용자 결정 2026-10-07 'R1·R2 = (b)', 일반화 2026-10-08 "동의", M4): 감지 소자는 출력을 측정 가능하게 부하하지 않아야 하고, 값이 동작점과 무관한 감지 쪽 수동소자는 엔진이 값을 계산한다.

**대상**: CM 분할(§5 `authoring.cm_partition`, `cm_sense_elements` 선언을 반영한 결과 하나만 쓴다 -- 같은 도달 규칙을 다른 모듈에 복사하지 않는다)이 감지(소비) 쪽으로 분류한 소자에 닿은 **자유 수동소자 전부(R·C)**. 자유 = θ 성분이고 DC 전류 기저에서 가지치기되어 값이 동작점을 바꾸지 않는다. 출력 넷에 직접 닿는지는 보지 않는다.

| CMFB 형태 | 대상 | 값을 정하는 기준이 되는 metric(예) |
|---|---|---|
| 저항 분압(파일럿) | 감지 R | 차동 gain |
| 저항‖커패시터 | 감지 R, C | 차동 gain·PM, PM_cm |
| follower 완충 + 저항 | follower 뒤 R | T_cm(0)·PM_cm(출력은 gate만 부하) |
| triode MOS 평균, DDA | 없음(감지 MOS는 일반 θ 탐색이 정한다) | -- |
| 스위치드 커패시터 | 지원 안 함 | -- |

처리 순서(소자마다 1-D, 다른 θ 고정):
1. 외층이 풀이를 마친다.
2. 손실 행: 선언된 제약 metric m마다 Δm(x) = m(x) − m(소자 제거) 를 정의한다. 소자 제거 = R → ∞ 또는 C → 0 스탬프 제거(ω → 0 및 필요한 주파수에서 다시 푼다). 영향받는 metric = 소자 제거로 값이 분해능 이상 움직이는 metric.
3. 모든 영향받는 m에 대해 |Δm(x)| ≤ b_m(그 metric 분해능 `MetricResult.resolution`)을 만족하면서 **면적이 가장 작은 값**을 `bracket_root`로 찾는다(R은 작을수록, C는 클수록 부하가 크므로 각각 한쪽 경계). 범위는 θ 범위(사용자 결정 8).
4. 그 값으로 바꾼 뒤 평가 커널을 1회 돌려 모든 제약을 다시 판정한다.
5. 재판정에서 이전에 만족하던 행이 하나라도 위반되거나 미측정이 늘면 원래 값을 유지하고 사유를 기록한다.
6. **적용 범위**: 1~5는 front 점마다 한 번씩 따로 적용한다(M4). 모든 점에 적용한 뒤 front를 비지배 필터에 한 번 더 통과시킨다(수동소자 면적이 면적 축에 들어가므로, §9 Q9). 필터에서 빠진 점과 사유는 기록한다.

상수는 새로 두지 않는다. 허용 손실은 각 metric의 분해능이다. 선언된 제약이 없어 분해능이 없으면 건드리지 않고 사유를 기록한다.

| 항목 | 상태 | 증거 |
|---|---|---|
| 보상 수동소자 θ 연속 성분 + MNA 판정 | OK | `metrics/CONTRACT.md:555-567` |
| Rz = 1/Σgm 구조 규칙 | OK(J7 ratify 대기) | `E/sizing/theta_schema.py:15-25,79,144`, `E/metrics/ss_evaluate.py:48` |
| `gm_req` 1-D 근, `comp_approx_gap` | MISS | `E/search/find_front.py:45-48`('범위 밖') |
| 극점 노드 목록에서 후보 집합 유도 | MISS(SP1이 없어서) | -- |
| 단일단 gm_1 규칙(U-12) | MISS(계획상 확정 대기) | -- |
| CM 감지 저항 최소 R | MISS | `grep -rn "load_loss\|cm_sense" E/` 0 |

### 3.6 GB6 -- 할당·탐색 (MOD6)

층 0과 gain 예산은 41 §5에 있다. 이 절은 외층이다.

**외층**(as-built를 유지한다):
- 시작점(층 0 조립점 → S3 feasible → x0)마다 ε-제약 SLSQP를 푼다.
- 끝점 E_P·E_A를 먼저 풀고, 면적 상한 쪽은 b_A 간격, 전력 상한 쪽은 b_P 간격으로 스윕한다.
- 비지배 필터를 거친 점에만 L-b를 적용한다(LR10).
- 예산이 없으면 front를 내고 정지한다.

**이 설계가 바꾸는 것**:
1. **예산 점**: 목적 예산이나 면적 예산 제약이 선언되면 그 값을 ε로 고정해 한 번 풀고, 그 결과를 front와 함께 낸다(DEC-77, U-13). 결정 11의 `area_search_m2 <=` 제약은 탐색 축 예산이므로 '면적 ε = 예산 값'으로 전력을 최소화하는 풀이 하나를 추가한다.
2. **제약·목적의 척도화**(§7.2): 행마다 판정 단위와 풀이 단위를 나눈다.
3. **시작점 출처**: 층 0 조립점(41 §5)과 출발 구간 후보(41 §6)를 맨 앞에 둔다. as-built `layer0_center`(θ 상자 중심 + 전류 Chebyshev 중심)는 블록 국소 문제의 초기점 생성기로 옮긴다(41 §5.2). 시작점 출처를 대체하므로 WP-01에 따라 옛 경로를 지운다.
4. `n_starts` 선언과 L-c '분지' 판정을 넣는다. L-c 분지 = bin 벡터가 다른 시작점(LR10).
5. **ε 간격과 점 예산**(DEC-80, H6):
   - **간격**: ε 간격은 격자 분해능이 아니라 DEC-80 (ii) 면적 bin 폭 = max(레이아웃 격자 분해능, 면적 축 모델 오차)다. 전력 쪽 간격은 max(b_P, 전력 모델 오차)다. 모델 오차가 측정되기 전에는 격자 분해능만 쓰고 front를 '추정'으로 표시한다.
   - **점 예산**: ε 점 수 상한 = 외층 예산 N_C = N − (단계 B 사용분)이다. N은 41 §5.8 식으로 구한다. 점 하나의 비용은 실측 풀이 평가 수 중앙값이다.
   - **예산 초과 시**: 간격을 2배씩 넓힌다. 이 2배는 DEC-80 예산 게이트 규칙 그대로이며 새 상수가 아니다. 넓힌 배수와 '해상도 굵음(배수 n)'을 front 표에 적는다.
6. **SLSQP·ε-제약·시작점 출처**(DEC-54): 스칼라화는 ε-제약 하나만 쓰고 가중합은 쓰지 않는다. 시작점 출처는 다음 순서다.
   1. 층 0 조립점(41 §5)
   2. 출발 구간 후보(41 §6.6)
   3. 지문이 일치하는 S3 feasible 점 상위 `n_starts`
   4. 선언 x0
   5. as-built `layer0_center` 점: t_eval을 처음 재는 데 쓰고 다른 출처가 없을 때만 시작점으로 쓴다

   준난수 전역 샘플(DEC-34)은 선언했을 때만 켠다(DEC-75).
7. **근방 반경**: 41 §5.9.

| 항목 | 상태 | 증거 |
|---|---|---|
| ε 두 방향·비지배·L-a/L-b | OK | `E/search/eps_sweep.py:1-14`, `pareto.py:31`, `slsqp_outer.py:49`, `l_bin_search.py:1-12` |
| ε 간격 = DEC-80 bin 폭 + 점 예산 | PART(간격 = b_A = grid × W_min와 2배 예산 게이트는 있음. 모델 오차 항, '추정' 표시, 41 §5.8 예산 식 연결이 없음) | `E/search/eps_sweep.py:1-14` |
| L-c 분지 판정 | PART(시작점마다 따로 돌고 키 중복만 제거) | `E/search/eps_sweep.py:4` |
| 예산 점 | MISS(`budget_point.py` 미작성) | `search/CONTRACT.md:537` |
| `n_starts`, Sobol 전역 샘플(DEC-34, 기본 비활성) | MISS / 비활성 | `search/CONTRACT.md:591` |
| front 표 필드 | PART: 판정 축 면적, gain 예산, gm_id·I0·ln IC 열이 없다 | `E/search/find_front.py:60-70` |
| SLSQP 척도 | DEV: `[ng-area-budget]`이 행·목적·ftol에 임의 양수 상수를 곱한다(§7.2에서 대체) | `[ng-area-budget] E/search/slsqp_outer.py` |
| DEC-88 ln IDu 연속 하한 | DEV: 1변수 writer의 칸 정점·전도 하한을 bounds로 조인다(기록된 결정) | `search/CONTRACT.md:573` |

### 3.7 GB7 -- DC 정본과 봉인 (MOD4)

**규칙**: P N3.4~N3.6. 평가 커널 = ② 전류 → ③ L → ④ 기둥·SCC → ⑤ W → 봉인 1~8. W_request가 있으면 그 소자의 W는 고정 입력이다(LY3).

**이 설계가 바꾸는 것**:
1. **L 동치류 공유**: §3.2-1을 따른다.
2. **미러 비율 강제**: `matching_ratio`(그룹의 W/L 비)를 전류 기저의 강제 관계로 넣는다(DEC-70). 비율의 출처는 θ 변수이며, 대칭 묶음(§6)이 같은 비율 1을 준다.
3. **tol_I**: 직전 봉인 스냅샷(S2p)의 `ss` gm으로 계산하고, 첫 평가만 격자 최대 gm을 쓴다(P N3.6).
4. **종속 소자 선택 DEC-95 (3)**: ratified 선택(`structure.json`)과 ② 'GB5 gm 요구·뒤 stage 독립'을 Kruskal 엣지 키 앞에 둔다. ②의 입력은 S1v stage 번호다.
5. **W4 초기값**: 층 0이 배분한 기둥 VDS를 쓴다(41 §5.3 (c)).

| 항목 | 상태 | 증거 |
|---|---|---|
| W0~W4 writer 계획 | OK(W3는 9회로 모두 0. CI-15·18 대기) | `E/sizing/writer_plan.py` |
| SCC 고정점·K_max·NONCONVERGENT | OK(+ GS 실패 시 감쇠 Newton, Brent `bracket_root` -- master 병합됨) | `E/sizing/fixed_point.py:21`, `scc_newton.py:33` |
| 봉인 1~8 | OK(+ 계획에 없는 봉인 9 '전도 여유') | `E/sizing/seal.py:30` |
| tol_I | DEV(늘 격자 최대 gm × W/w_m) | `E/sizing/seal_tolerances.py` |
| 미러 비율 강제 | MISS | `sizing/CONTRACT.md:276` |
| DEC-95 (3) 전체 순서 | PART(① 구조 색·이름만) | `E/sizing/writer_plan.py:13-17` |
| W_request 고정 W | MISS | `E/sizing/block_widths.py:9` |

### 3.8 GB8 -- metric (MOD5)

**규칙**: P N3.8. 모든 metric 판정은 외층 전회로 계산 한 곳에서 한다(DEC-74).

**이 설계가 추가하는 것**:
1. **블록 국소 모델과 잔차**: 41 §2.
2. **감도 게이트**(N3.8): S0 지문이 바뀔 때와 최종 해에서 돈다. 분해 metric(블록 gain)이 읽지 않는 소자를 건드리는 θ 방향으로 섭동한다. ε = ‖A·x − b‖₂/‖b‖₂ × 그 metric의 x 감도로 정한다. 분해 값 변화 ≤ ε인데 MNA 값 변화 > ε이면 오류다. as-built `sensitivity.py`(LUT 파라미터 adjoint로 metric 분해능을 내는 것)는 다른 양이므로 유지하고, 게이트는 새 파일로 둔다.
3. **`ls` 필드**:
   - 방향별 최대 전류는 DEC-65의 β·σ·κ 규칙으로 계산한다.
   - 슬루 등가 용량 `ls.c_slew_farad`를 둔다.
   - 스윙·ICMR 한계는 P N3.8 경로 합으로 계산한다. metric 정의는 아래 8이다.
   - `driving_spec`이 선언되면 이 값들로 제약 행을 만든다.
4. **보고 metric**:
   - `nqs_ratio` = `ugf_ss_hz` / 신호 경로 소자 최소 f_T. f_T는 봉인 `ss`의 gm/(2π·cgg)이다.
   - 옛 `mismatch_sigma_v`(matching 그룹별 Pelgrom 두 항)는 아래 8의 `offset_in_sigma_mv`·`mirror_ratio_sigma_pct`로 대체한다(사용자 결정 2026-10-08 Q3).
5. **전력 축 = Σ V·I**(`power_dc_w`, 사용자 결정 2026-10-08 Q6. U-10 변경, DEC-78 문구 정정 대상): 레일마다 전압 × 공급 전류를 계산해 더한다. '기둥마다 전류를 한 번 센' 값과의 대조는 매 실행 기록하고, 둘이 어긋나면 `review_needed`로 올린다.
6. **`verified_by`·모델 오차**: 레지스트리 항목에 `verified_by`·`model_error_ref`를 두고, 오라클 대조 결과(DEC-72)를 `derived.model_error_<metric>`에 쓴다.
7. **잡음**(사용자 결정 2026-10-08, 범위 안): 다음 넷을 둔다. 설계는 41 §7이다.
   - 입력 환산 잡음 밀도와 적분 잡음 metric
   - LUT 잡음 열(PDK BSIM4 `.noise` 특성화, 새 버전 파일)
   - MNA adjoint 잡음 해석과 소자별 기여 표
   - 오라클 `.noise` 대조
8. **offset·미러비·스윙·ICMR**(사용자 결정 2026-10-08 "q3,q4는 네 제안대로 해", 근거 `_drafts/engine/matching_swing_spec_proposal.md` §1). 닫힌 어휘로 MOD5 레지스트리에 `MetricSignature`로 등록하고, 레지스트리 밖 이름은 `metric_unknown`으로 거부한다. 옛 이름 `mismatch_sigma_mv`·`mirror_ratio_error_mv`·`mismatch_sigma_v`는 spec 옛 이름 표에 넣어 거부한다(새 이름으로 안내).

| metric | 정의 | 단위 | domain / view_kind | 분해능 | 쓰임 |
|---|---|---|---|---|---|
| `offset_in_sigma_mv` | **입력 환산 랜덤 offset 1σ**. 회로의 **모든 MOS** i에 독립 게이트 전압 오차원 σ_VGS,i(41 §6.4-2 A_eff 모델: LUT 감도 열 × bin별 slope / √(W_i·L_i))를 두고, 봉인 `ss` 스냅샷의 MNA 저주파(ω → 0) 전달로 출력(차동 출력이면 차동)까지 보낸 분산을 합해 차동 이득 A_dm으로 나눈다: σ²_in = Σ_i (Z_i·gm_i·σ_VGS,i)² / A_dm². Z_i는 소자 i 드레인 전류 → 출력 전달 임피던스이고, 잡음 해석(41 §7.3)과 같은 adjoint 해 한 번으로 모든 i를 얻는다 | mv | ss / transfer(gain 제약 전달 뷰) | LUT `tol_mismatch`와 소신호 tol의 adjoint 감도 전파 | 파일럿 제약, 나머지 보고 |
| `offset_excess` | `offset_in_sigma_mv` ÷ (입력 셀 소자만의 같은 합). 입력 셀은 S1v의 gain 제약 전달 뷰 첫 이득 블록 input 셀(`noise_excess_th`와 같은 구조 규칙) | ratio | ss / transfer | 위 두 값의 전파 | 구조 가드 `<= √2`(부하 분산 ≤ 입력쌍 분산의 경계) |
| `offset_sys_mv` | **계통 offset**: 봉인 DC 동작점(실제 VDS 반영)에서 입력 차 0일 때의 출력 오차 / A_dm. 출력 오차 기준은 차동 출력 = Vop − Vom, 단일 출력 = spec에 선언된 출력 기준 DC(선언이 없으면 값을 내지 않고 `reference_undeclared`로 보고) | mv | dc→ss / transfer | DC tol(tol_V)의 전파 | 상한 = `value_from_constraint: offset_in_sigma_mv`(기존 규칙 '계통 ≤ 랜덤 예산', 그 제약이 있는 회로만), 나머지 보고 |
| `mirror_ratio_sigma_pct` | S1 matching 그룹 중 mirror 계열(whole, consumer_symmetric, `mirror_tail_ratio`, bias_distribution)마다 랜덤 전류비 σ(ΔI/I) = (gm/ID)·σ_ΔVGS,pair | pct | dc→ss / 없음(뷰 불필요: 대상은 S1 미러 matching 그룹. view_kind `ratio`는 {num, den} 응답비 뷰라 해당 없음, U5 as-built 2026-10-08) | tol 전파 | 보고만 |
| `swing_out_v` | **포화 기준 출력 스윙**: 출력 DC 동작점을 중심으로, 출력 경로의 모든 MOS가 VDS ≥ VDSAT + tol_vdsat(사용자 SPICE 포화 규칙 + LUT `tol_vdsat_table`)를 지키는 대칭 peak-to-peak 폭. 단일 출력 = 2·min(V_hi − V_o, V_o − V_lo). 차동 출력(포트쌍 p/n) = 출력마다 계산한 반폭의 최솟값 × 4(차동 p-p). [V_lo, V_hi]는 P N3.8 경로 합(VDS 엣지 = 포화 하한, VGS 엣지 = 그 전류의 VSB 포함 VGS)이다. 구간 자체도 레코드로 낸다 | v | ls | tol_vdsat·tol_V 합 | 파일럿·nmcnr 제약, 나머지 보고 |
| `icmr_v` | 입력 공통모드 창 [Vin,min, Vin,max] ∩ [rail_lo, rail_hi]의 폭(레일 밖 입력 불허). 경계 = 입력 경로 소자 전부 VDS ≥ VDSAT + tol_vdsat. 창이 비면 음수 폭(부족량)을 그대로 낸다 | v | ls | 같음 | ngcc·nmcnr 제약, 나머지 보고 |
| `icm_margin_v` | 선언된 입력 DC(spec `input_dc`)와 위 창 경계의 최소 거리 min(V_icm − Vin,min, Vin,max − V_icm). 경계에 tol이 이미 들어 있으므로 ≥ 0이면 'LUT tol 여유를 두고 창 안'이다. 입력 DC가 SP-2 대기면 SP-2 (c)(J-E, 41 §4.6)에 따라 V_icm = 해의 W4 자유 변수 y_icm으로 계산하고, `required_input_cm_v{value, window}`를 함께 보고한다 | v | ls | 같음 | 아래 규칙 |
| `ff_gm_ratio` | feedforward 묶음마다 r_ff = G_ff / gm_in(B_b)(41 §1.12.2-5). 묶음이 없는 회로는 값 없음 | ratio | ss / transfer | gm tol 전파 | 보고. spec이 값·`source`를 선언하면 제약(값은 사용자 몫, 출처 후보 You 1997·Leung & Mok 2001) |

   - **topology 무관**: offset은 회로 이름·그룹 규칙 없이 MNA 전달로 계산한다. S1 matching 그룹(J-U4)은 계산 대상이 아니라 **해석·대조**에만 쓴다: 소자별 기여 표 `offset_contrib[{device, share, matching_record}]`를 내고, 기여가 큰 소자가 matching 레코드에 들지 않으면 `review_needed`가 아니라 보고 행으로 남긴다(레이아웃 matching 대상 확인용).
   - **ICMR 제약 규칙**(사용자 결정 Q4 (4)): ICMR = 폭 + 선언 입력 DC 포함. `icmr_v >= w` 제약이 있는 회로는 입력 DC가 선언되면 `icm_margin_v >= 0`도 같은 출처로 함께 판정한다. 3σ 관례는 쓰지 않는다.
   - **판정 위치**: 다른 metric과 같이 외층 전회로 계산 한 곳(DEC-74). 출발 구간(41 §6.2·§6.4-2)은 출발값과 보고에만 쓴다(EP-7).
   - **단위 어휘**: `core/units.METRIC_UNITS`에 `pct`, `ratio`, `v`가 없으면 더한다(`ratio`·`v`는 잡음 경로와 공유).
   - 파일: `E/metrics/offset_analysis.py`(offset_in·excess·contrib), `offset_systematic.py`, `mirror_ratio.py`, `ls_swing.py`(swing·icmr·icm_margin, `ls_fields`가 부른다).

| 항목 | 상태 | 증거 |
|---|---|---|
| MNA(ω 무관 조립 + ω별 풀이, gmb, 접합 용량, pencil) | OK | `E/metrics/mna_build.py:47`, `mna_solve.py:42`, `stamp_mos.py`, `junction_cap.py`, `pencil_roots.py` |
| `gain_ss_db`, `ugf`, `gbw`, `pm_ss_deg`(β 또는 β=1), ratio, `parasitic_pm_ss_deg` | OK | `metrics/CONTRACT.md:173-235` |
| `rout_ss_ohm` | PART(블록 테브난 잔차 없음) | `metrics/CONTRACT.md:205-213` |
| 블록 국소 모델·잔차, 감도 게이트 | MISS | `metrics/CONTRACT.md:13-14` |
| `ls`·스윙·ICMR·nqs | MISS | `metrics/CONTRACT.md:14` |
| offset·미러비·스윙·ICMR metric(8) | MISS: spec에 옛 이름 `mismatch_sigma_mv`·`mirror_ratio_error_mv`(파일럿·two_stage·two_stage_sf), ngcc `{metric: pending MOD5}`만 있고 레지스트리 항목이 없다 | `authoring/SPEC_CONTRACT.md:261`(S2), `E/core/units.py:7,13`, `assets/library/current_reuse_telescopic_ota.sizing_spec.json:215,224`, `ngcc_3stage_ff.sizing_spec.json:87` |
| 전력 축 | PART: Σ V·I는 OK(결정 Q6). 기둥 대조 없음 | `E/search/objectives.py:9` |
| 면적 탐색 축 | PART(master는 수동소자 단위 면적 None. MIM·측정 부하 제외는 `[ng-area-budget]`) | `E/metrics/dc_metrics.py:18-19,80-83` |
| `verified_by`, `spice_unverifiable` | MISS | `metrics/CONTRACT.md:246,424` |
| 잡음 metric·LUT 잡음 열·adjoint 해석 | MISS | `grep -rn "noise" E/metrics E/lut` 결과에 해석 코드 없음 |

### 3.9 GB9 -- 기록·레이아웃 수렴·보고·진입점

**S3**: as-built OK(`E/search/archive.py`). **결함**: 디스크 실패 캐시에서 레코드를 복원할 때 float가 repr 문자열로 돌아와 `layer0_center._repairable`에서 `TypeError`가 난다(h_lo). **설계 수정**: S3·실패 캐시 레코드를 타입이 있는 스키마로 둔다. 숫자는 `float.hex` 문자열로 쓰고, 읽을 때 스키마로 되돌리며, 스키마 밖 레코드는 무시하지 않고 거부한다(`archive_record_invalid`). 왕복(쓰기→읽기) 동일성 test를 둔다.

**MOD7 레이아웃**(P N3.17). 대부분 OK다(`E/layout/`). 이 설계가 고치는 것:

| 대상 | 수정 |
|---|---|
| ΔA_tie | `grid²` → `MANUFACTURINGGRID × max(두 점 bbox의 변 4개)`(DEC-79, DEC-95 (2))(`E/layout/floorplan.py:83`) |
| LY5 | `W_adjustable=False`로 바로 완화하는 경로를 지우고, 판정을 MOD8에 맡긴다 |
| LY4 | `matching_L_mismatch` 기록을 넣는다 |
| LY8 | 출력 계약에 `ly.diffusion{ad, as, pd, ps}`를 넣는다. BSIM4 perMod=1 둘레 규약을 따르고, 엔진 접합 용량과 오라클 입력이 같은 값을 쓴다 |
| LY10 | tap은 행마다 넣지 않고 그룹 경계에만 넣는다 |
| 판정 축 면적 | 수동소자 면적(MIM 배치 면적 = 값/밀도 + PDK 여유)을 포함 항목으로 넣는다. 지금은 MOS 행만 들어간다 |

**MOD8 `convergence`**(MISS). 알고리즘:
- (1) front 점마다 `run_layout`을 실행한다.
- (2) `W_requests`가 있거나 폭 키가 바뀌었으면 그 W를 고정 입력으로 평가 커널을 1회 돌리고 봉인 1~8을 확인한다(LY3·LY7).
- (3) K_max(P N3.6 식, 구간 = W 변경 비)까지 반복하고, 닿으면 NONCONVERGENT로 둔다.
- (4) 수렴한 스냅샷으로 판정 축 면적을 계산하고 front를 다시 비지배 필터에 통과시킨다. 동률 폭은 ΔA_tie다(DEC-79). 순위가 뒤집힌 점은 (1)로 돌아간다. 교대 횟수 상한도 K_max다.

**MOD9 `report`**(MISS): 결과 JSON(DRS 8섹션 키, `perf`, front 표, 출발 구간 표 41 §6.6, `gain_budget_db`, 충돌 표, 실패 레코드)을 낸다.

**MOD10 `pipeline`**(MISS): `run_gmid_design_pipeline`이 GB0→…→GB9를 순서대로 부르고 `exit_code_for`로 끝낸다. `[ng-bridge]`의 `oracle_input`·`front_oracle`을 이 진입점 아래로 옮긴다.

---

## 4. SPICE 오라클 (`tools/spice_oracle/`)

**역할**: 엔진을 import하지 않는 독립 판정 장치다(P N3.8). 합격 조건은 free 모드에서 (i) 선언 성능 제약 만족 (ii) ID > 0인 모든 MOS 포화 (iii) 엔진이 전도로 예측한 MOS가 꺼지지 않음(`off_current_A`)이다. forced 모드는 진단 전용이다. 이 부분은 as-built OK다(README C22~C24).

**C10 폐루프 과도 판정**(`docs/03-analysis/oracle-c10-early-termination.contract.md`, `[ng-oracle-early]` d56ba66 개정본 위에 아래 규칙을 더한다):

1. **d56ba66에서 그대로 쓰는 것**. 아래 L번호는 개정 계약 파일 기준이다.
   - f_crit 대역: L14-15
   - n_pp, tmax: L25, L28
   - 분해능을 아는 창 판정 g: L37
   - 조기 unstable(엄격 증가): L40
   - 연장 실행 상한 n: L71-72
   - `wall_s_per_window` 유도: L75-78
   - 시간 초과·치명 오류 = `failed`: L79-81
2. **지속 진동은 불안정(한계 사이클)이다**(사용자 결정 2026-10-08 4번). 창 진폭 M_j가 아래를 모두 만족하면 `unstable`(사유 `limit_cycle`)이다.
   - 바닥보다 분해능 넘게 크다: M_j·(1 − reltol) > floor'.
   - 연속 창의 변화가 분해능 안이다: |M_j − M_{j−1}| ≤ (M_j + M_{j−1})·reltol + floor'.
   - g↓(감소)가 아니다.

   j ≥ 3인 창에서 이 조건이 j−1, j에 연속으로 성립하면 조기 종결한다. 창 수 3은 L40과 같은 정의이므로 새 상수가 아니다.
   - **안정 fixture 불변 조건**(계약 L63-64를 이어받음): 구현 커밋에서 기존 안정 판정 회로·fixture 전체(`stable`, `decaying`→`stable`)를 돌려, 이 한계 사이클 조건이 한 번도 성립하지 않았음을 확인하고 기록한다. 하나라도 성립하면 규칙 설계를 되돌린다.
   - **고Q 안정 회로의 표시**: 창 하나당 감쇠가 분해능보다 작으면, 고Q로 천천히 감쇠하는 안정 회로를 K 창 안에서 한계 사이클과 구별할 수 없다. 이 경우 판정은 보수적으로 `unstable(limit_cycle)` → FAIL이다. 대신 보고 맨 앞에 `limit_cycle_vs_slow_decay_unresolved{M_1..M_K, 창당 변화비}`를 둔다. 사용자가 이 FAIL이 판정 한계에서 나왔다는 것을 알아볼 수 있게 하기 위해서다.
3. 2번은 d56ba66의 다음 두 곳을 대체한다.
   - L48-52 '그 밖(분해능 안의 같음 포함) → undetermined'
   - L42-44·L52-54 '일정 진폭 지속 진동은 undetermined 유지(사용자 승인)'

   2026-10-08 사용자 결정이 이 문구보다 나중이다. `tools/spice_oracle/tests/test_oracle_c10_stability.py:710`의 `test_sustained_oscillation_undetermined_incomplete` 기대값도 바뀐다. 기대값은 test 작성 주체가 고친다.
4. 폐루프 과도에서 `unstable`(limit_cycle 포함)이 나오면 FAIL이다(사용자 결정 B).
5. **개루프 RHP 극점 처리**(조정자 정정, R19 / §9 Q10):
   - 개루프 RHP 극점이 있어도 폐루프는 안정할 수 있다(조건부 안정). 그래서 오라클은 개루프 RHP 극점만으로 FAIL을 내지 않는다.
   - 엔진의 결정 A('RHP 극점 → 위반 행')는 **탐색용 보수 규칙**이다. 엔진이 위반으로 본 점을 오라클이 합격으로 볼 수 있고, 그 차이는 T8 모델 오차와 함께 기록한다.
   - 이 처리는 결정 A의 문구('불안정(실패)')를 오라클 쪽에서 완화한다. 그래서 별도 질문으로 둔다(§9 Q10).
6. **Nyquist 판정 정의**(N2). 오라클은 엔진과 독립이며 엔진 값을 쓰지 않는다.
   - **P(개루프 RHP 극점 수)**: 오라클이 직접 구한다. 끊은 개루프 테스트벤치(같은 루프 절단)에 ngspice `.pz`를 돌려 실수부 > 0인 극점을 센다. 0 근처 극점은 분해능 밖으로 실수부가 양수인 것만 센다. 분해능 기준은 `.pz` 결과의 상대 정밀도(reltol)다.
   - **N(−1 둘레 감김 수)**: 같은 개루프 `.ac` 표본 L(jω)에서 1 + L의 위상을 펼쳐(unwrap) 센다. N = −Δ_{ω:0→∞} arg(1+L)/π이고, 음의 주파수 대칭을 쓴다.
   - **주파수 범위**: 하단은 |L|이 평탄해진 저주파(첫 표본에서 위상 기울기가 0으로 수렴), 상단은 |L| < 1이고 단조 감소하는 구간까지다.
   - **표본 조건**: 인접 표본 사이 arg(1+L) 변화가 π/2 이하여야 한다. 넘는 곳은 그 구간을 이분해 다시 `.ac`한다(상한 K_max). 그래도 넘으면 N은 '미정'이다.
   - **Z = N + P**. Z ≥ 1이면 불안정 FAIL, Z = 0이면 안정이다.
7. **최종 판정과 이행 순서**:
   - Z와 폐루프 과도를 함께 본다. Z ≥ 1 또는 과도 `unstable`이면 FAIL이다. Z = 0이고 과도가 stable/decaying이면 안정이다. 둘 다 결론을 못 내면 INCOMPLETE다.
   - **6이 구현되기 전에는 폐루프 과도만 쓴다.** 이때 Z는 '미정'으로 보고하고, 개루프 RHP만으로는 FAIL·INCOMPLETE를 정하지 않는다.
8. **U6 판정 규칙 보완**(사용자 결정 2026-10-09 "3개 모두 네의견대로 해", U6 구현 보고 반영):
   - **한계 사이클 = 감쇠하지 않음**: 2번의 '분해능 안에서 일정'을 대체한다. j ≥ 3에서 최근 두 창의 진폭 M_j가 앞 창보다 분해능 이상 줄지 않으면 지속 진동 `unstable(limit_cycle)`이다. 진폭이 출렁이는 지속 진동(rb1e6형)도 포함한다. 창마다 분해능 이상 계속 줄면 slow decay로 판정을 이어 간다.
   - **`.pz` 신뢰 규칙**: 큰 BSIM4 회로에서 `.pz`가 경고 없이 거짓 RHP 극점을 낸다(파일럿 23개, 개루프 `.tran`에 증가 없음). 그래서 폐루프 과도가 stable이면 `.pz`를 쓰지 않는다(Z = 0, P = −N). 과도 unstable이면 FAIL. 과도 미정이면 N ≥ 1 → FAIL, N = 0이면 **개루프 과도가 증가를 확인할 때만** `.pz` P를 쓰고 아니면 INCOMPLETE다. 과도 stable인데 `.pz`가 −N과 다르면 `pz_conflict`를 기록한다.
   - **자극 위치**: 폐루프 과도의 자극과 관측은 루프 끊는 점에 둔다. 그 루프의 폐루프 극점은 끊는 점에서 들뜨고 관측되므로, '자극이 모드를 못 들뜨게 해서 안정으로 남는' 위험을 그 루프 뷰 범위에서 닫는다. 남는 한계는 보고서에 적는다.
   - **조건부 안정**: Z = 0이고 과도 stable이면 `pm_valid`를 유지한다. PM은 모든 |T| = 1 교차의 최솟값이다. P ≥ 1이거나, 교차 주파수 아래 |T| > 1 구간에서 위상이 −180°를 넘으면 `conditionally_stable`을 표시하고 **하측 이득 여유**(루프 이득이 몇 dB 줄면 감김 수가 바뀌는지, 같은 `.ac`에서 읽음)를 보고한다. spec 값이 없으므로 제약이 아니라 보고다.

| 항목 | 상태 | 증거 |
|---|---|---|
| free/forced, 포화, off_current, CMRR/PSRR, 접합 기하 | OK | `tools/spice_oracle/README.md:60-69,114-117,146-147,300-318` |
| C10 조기 종결 계약 | PART(계약만 있고 master 미반영) | `[ng-oracle-early]` 계약 L14-81 |
| 지속 진동 = unstable | DEV: 계약과 test가 undetermined로 고정되어 있다 | 계약 L42-54, `tools/spice_oracle/tests/test_oracle_c10_stability.py:710` |
| 개루프 RHP: Nyquist Z + 과도로 판정, 결정 불가일 때만 INCOMPLETE | DEV: `pm_undefined`이면 무조건 N/A→INCOMPLETE | `[ng-cmfb-pm]` README '판정', `tools/spice_oracle/README.md:516` |
| `.pz` P 계수, N 위상 펼침 | MISS | `grep -n "\.pz" tools/spice_oracle` 0 |
| 잡음 `.noise` 대조 | MISS | 41 §7.6 |
| `pm_cm_ss_deg` 측정 | OK `[ng-cmfb-pm]`. `[ng-bridge]` `ORACLE_MEASURES`에는 없다 | -- |

---

## 5. 공통 모드(CMFB) 루프

사용자 결정(2026-10-08, CM 일반화·구동/소비 분류·결정 A·보완)을 그대로 설계로 둔다. 구현은 `[ng-cmfb-pm]`에 있다.

1. **루프 정의**: 차동 출력 포트쌍(role p/n)에 같은 부호(가중 ½, ½)로 Middlebrook 주입해 T_cm을 잰다. 평균 회로의 형태는 따지지 않는다. 오라클도 같은 정의를 쓴다.
2. **절단 분류**: 출력에 채널이 붙은 MOS마다 반대쪽 단자에서 채널·R·C를 따라간다. 이때 두 출력 넷은 통과하지 않는다.
   - 레일에 닿으면 구동(x)이다. 이상 전류원 단자는 레일로 본다.
   - 감지 넷·gate·다른 출력에서 끝나면 소비(n)다.
   - 판단이 애매하면 명시적으로 정지(`cm_partition_ambiguous`)하고 spec `cm_sense_elements` 선언(`user_spec`)을 요구한다.
3. **판정 규칙**:
   - `pm_cm_ss_deg` 제약은 spec에 선언된 회로에만 건다.
   - CM 루프에서 PM이 정의되지 않으면(T_cm(0) ≤ 1, 또는 0 dB 교차 없음) 위반이다(결정 A).
   - 개루프 RHP 극점이 있으면 위반이다.
   - 제약이 선언되지 않았어도 차동 포트쌍이 있으면 T_cm을 늘 계산해 보고한다. 이때 T_cm(0) > 1이면 경고 `cm_loop_unconstrained`를 낸다.
4. **위반 판정과 척도는 별개다**(M1).
   - **판정**: 결정 A에 해당하면 그 행은 **늘 위반**이다(부호가 위반). 이 판정은 척도에 의존하지 않는다.
   - **크기**: 판정 단위 크기는 c = 20·log10|T_cm(0)|/s다. 이 값은 ≤ 0이다. s는 그 metric의 분해능(`MetricResult.resolution`)이다.
   - **분해능이 없을 때**: as-built는 s = 1 dB로 대체하는데, 이것은 근거 없는 상수라 지운다(EP-4). 대신 행은 위반으로 유지하고, 풀이 단위 크기만 §7.2 규칙으로 정한다(s_k = max(|c 원값|, ...)). 그리고 front에 '분해능 미측정'을 표시한다.
   - RHP 극점 행(c = −max Re/|p|)도 같은 방식으로 다룬다.
5. **스위치드 커패시터 CMFB**는 `unsupported`로 명시 정지한다.

| 항목 | 상태 |
|---|---|
| 1·2·3·5 | OK `[ng-cmfb-pm]`(미병합) |
| 4 분해능 없을 때 1 dB 대체 | DEV(상수) |
| metrics CONTRACT 7.11의 '`cm_output_loop` boolean' 문구 | DEV(문서가 README·S-33과 모순) |
| 계획서 N3.16 view_kind에 `cm_loop` 없음 | 계획서 문구 갱신 필요 |

---

## 6. 대칭 -- 정준 라벨링과 자기동형 궤도 θ 묶기

사용자 결정(2026-10-08 "정준 라벨링 + 대칭 변수 묶음, 기본값 묶음")을 설계로 둔다.

1. **완전 정준 라벨링**(신규 `E/graph/canonical_form.py`): S1을 색 그래프로 본다. 꼭짓점 = 소자·넷, 색 = kind, 단자 종류, 레일 여부, 포트 role.
   - 1-WL 색 정제(as-built `E/sizing/struct_colour.py`)에서 출발한다.
   - 색 칸이 이산이 아니면 개별화와 정제를 반복하는 탐색 트리로 정준형을 정한다(nauty 방식). 탐색 트리의 가지 순서는 색 칸의 정준 순서다.
   - 이름을 쓰지 않는다. 결과는 정준 순서와 자기동형 생성자다.
2. **궤도**(신규 `E/graph/automorphism_orbits.py`): 생성자들로 소자 궤도를 만든다. 레일과 포트 role은 고정한다. 차동 포트 p/n은 서로 바뀔 수 있다.
3. **θ 묶기**(`E/sizing/theta_schema.py`): 같은 궤도의 소자는 θ 성분을 하나 공유한다. 대상은 ln IDu, L 동치류 L, 보상 수동소자 값이다. 전류 기저 성분은 궤도에 대해 대칭인 것끼리 묶는다. 이것이 기본값이다.
4. **해제**: spec `search.untie_orbits: {원소: {source}}`(as-built 정본, 옛 이름 `symmetry_untie`)에 적힌 소자는 궤도에서 빼고 따로 변수를 둔다. 의도적 비대칭 사이징에 쓴다.
5. **불변식**:
   - **궤도와 matching 사이에는 포함 관계를 불변식으로 두지 않는다**(H1·N8, `[ng-layer0-canon]` 실측). 어느 쪽도 일반적으로 다른 쪽을 포함하지 않는다.
     - 비율 미러는 궤도가 아니다.
     - 반회로 대응은 궤도지만 matching 그룹 하나에 들어가지 않는다. 실측 예: 파일럿 M11a/M20a(class-AB KVL 루프 멤버), M37a/M37b(CMFB 쌍).
     - 대신 대조 표 `orbit_matching_crosstab`을 보고한다. MOS 궤도마다 그 궤도가 걸친 matching 레코드, 그리고 matching 레코드마다 그 레코드가 걸친 궤도를 적는다. 수동소자 궤도(Cc1/Cc2, Rz1/Rz2, R1/R2, CL1/CL2 등)는 matching 대상이 아니므로 표에서 뺀다.
     - `review_needed`로 올리는 것은 하나뿐이다. `diff_pair` 레코드의 두 멤버가 같은 궤도에 들지 않는 경우다. 이 경우만 대칭 차동쌍의 정의와 직접 모순된다.
   - 이름을 전단사로 바꾼 입력은 비트 단위로 같은 결과(front 정규화 해시)를 낸다.
   - 1-WL 결과와 정준형이 다른 회로는 그 목록을 보고한다.

| 항목 | 상태 | 증거 |
|---|---|---|
| 1-WL 색 정제 | OK(순서 tie-break 용도) | `E/sizing/struct_colour.py:1-15` |
| 완전 정준 라벨링(nauty 방식), `dc_orbit`, 꼭짓점마다 다른 `dc_colour` | PART `[ng-layer0-canon]` 49283c6(미병합) | `E/sizing/struct_canon.py` |
| 궤도 θ 묶기, 해제 | PART `[ng-layer0-canon]` | `E/search/orbit_ties.py`, `tie_expand.py`, `SearchDomain.ties`, spec `human.search.untie_orbits` |
| 이름 바꿈에도 비트 동일(정준 행·합·행렬 순서) | PART `[ng-layer0-canon]` | 실측: 8회로 + 합성 3개, 층 0 기준 |
| 9 library 회로에서 묶기 활성 | DEV: **9회로 모두에서 비활성**이다. 수동소자를 방향 있는 것으로 다루기 때문이며, 아래 7의 확정 규칙으로 고친다 | -- |
| 위치 | DEV: 설계의 `E/graph/canonical_form.py`·`automorphism_orbits.py` 대신 `sizing`·`search`에 있다. 다음 변경에서 정준형·궤도는 S1 구조 사실이므로 `graph`(MOD3)로 옮긴다(EP-3, 개념당 파일 하나) | -- |

6. **실측 회귀 기록**: canonical 시작점 변경 뒤 folded_cascode와 two_stage_ota가 하나뿐이던 front 점을 잃었다. 원인은 시작점 운이다. 대응은 41 §5(층 0 gain 예산 조합점)와 41 §6(스펙 기반 출발 구간)으로 시작점을 여러 개, 근거 있게 만드는 것이다. 이 두 회로를 회귀 추적 대상으로 `tests/integration`에 둔다.
7. **2단자 수동소자는 방향 없이 다룬다**(사용자 결정 2026-10-08 "대칭 묶음 방식: b", 확정 규칙):
   - **배경**: as-built 브랜치 실측에서 묶기가 9회로 모두 비활성이었다. 원인은 DC 전류가 흐르는 저항을 방향 있는 것으로 보아 방향 보존 자기동형만 허용한 데 있다. 파일럿 R1/R2는 단자 순서가 반대로 그려져 있어 거울 대칭이 잡히지 않았다.
   - **라벨링**: 정준 라벨링에서 R·C 같은 2단자 수동소자는 무향 엣지다. 단자 순서는 색에 넣지 않는다.
   - **묶기**: 궤도를 묶을 때 θ 값(R, C 값)은 같게 둔다. 예: R1 = R2.
   - **전류 변수**: 그 수동소자를 지나는 가지 전류 변수는, 자기동형이 단자 순서를 뒤집으면 부호 −1로 묶는다(I_R2 = −I_R1). 뒤집지 않으면 +1로 묶는다.
   - **topology**: library topology의 단자 순서는 바꾸지 않는다(WP-07).
   - **확인**: 이름을 전단사로 바꾸거나 수동소자 단자 순서를 바꾼 입력에서 궤도와 front 정규화 해시가 같은지 metamorphic test로 본다. 파일럿에서 R1/R2 궤도가 잡히는지도 test한다.

---

## 7. 면적 예산·척도화·성능

### 7.1 면적 예산(사용자 결정 11, 2026-10-08)

**규칙**:
- 회로별 spec 제약 `area_search_m2 <= 예산`을 둔다. 값은 결정 11의 표다.
- 면적 = MOS 게이트 면적 Σ W·L + 보상·내부 커패시터 면적이다.
- 커패시터 면적 = 값 / ρ_MIM이다. ρ_MIM은 `core` PDK 선언 양 `mim_cap_density_f_per_m2`를 `read_pdk_decl`로 읽은 값이고, 코드에 숫자를 적지 않는다.
  - 원본은 `C:/pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice`의 `camimc`다(sha256과 행 번호를 선언에 기록).
  - 단위 환산(F/µm² → F/m²)은 선언 로더가 한다.
- spec `element_values.<el>.measurement_load: true`로 표시한 측정 부하(CL·CL1·CL2·RL)는 면적에서 뺀다. 이름이 아니라 선언으로 가른다.
- 저항 단위 면적은 선언이 없으면 `passive_area_undeclared`로 보고한다. 이 처리에는 두 결정이 걸린다(M3).
  - DEC-79: 보상·부하 수동소자가 있는 회로에서 수동소자 면적 선언이 없으면 front는 `review_needed`다.
  - 사용자 결정 11: 면적 = MOS 게이트 면적 + 커패시터 면적이고, 저항은 언급하지 않는다.
  - **결정**(Q9, 2026-10-08): 저항 면적을 포함한다.
    - **단위 면적 유도**: 폭 W_R, 시트 저항 R_□인 poly 저항의 면적은 R·W_R²/R_□ + 두 끝 접촉 머리 면적이다. 그러므로 Ω당 면적 = W_R,min²/R_□이고, 머리 면적은 저항마다 한 번 더한다.
    - **입력값**: R_□는 PDK 저항 모델 파일(`C:/pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice`의 poly 저항 시트 파라미터)에서 읽는다. 최소 폭과 머리 길이는 PDK 규칙(periphery rules의 poly 저항 항목)에서 읽는다. 셋 다 `core` PDK 선언 양 `poly_res_sheet_ohm_per_sq`, `poly_res_min_w_m`, `poly_res_head_area_m2`로 두고 출처(sha256, 행·규칙 번호)를 함께 기록한다.
    - **저항 종류 선택**: PDK에 선언된 poly 저항 종류 중 Ω당 면적이 가장 작은 것을 쓴다. 고정 상수가 아니라 규칙이다.
    - **측정 부하 제외**: 측정 부하(`measurement_load`, 예: nmcnr RL)는 커패시터와 마찬가지로 면적에서 뺀다.
- 제약 행은 c = (v − A)/b_A다(판정 단위).

**S-3b 잠정 상한과 그 닫힘**:
- **잠정 상한**(L6): 예산이 없을 때 쓰는 as-built 전류 상자 상한이다. I_max는 그 kind의 모든 폭 슬라이스에서 단일 finger 기준 최대 ID다(`E/search/current_box.py:12-33`). 회로 근거가 없는 LUT 범위 값이라서 '잠정'이라 부른다.
- **닫힘**: 예산이 선언되면 I_max = IDu_max·A_budget/L_lo²로 바꾼다. 근거는 W·L = I·L²/IDu ≤ A_budget이다.

**설계가 더하는 것**:
1. **예산을 지키는 출발점**: 41 §6.4의 면적 상한(L ≤ √(A_budget·IDu/I), W ≤ A_budget/L)으로 출발 구간을 자른다. 층 0 국소 문제에도 면적 bin 상한을 예산으로 둔다.
2. **소자별 W 타당성**: 레이아웃 전에 W ≤ A_budget/L_min을 상자 제약으로 둔다. 예산이 없으면 S-3b 잠정 상한을 쓰되 보고에 '잠정'을 붙인다. W가 수 mm인 시작점은 이 제약에서 거부된다.
3. **면적 달성가능성**(GB4 확장, 41 §4.4): 인증된 면적 하한 A_lb만 정지 근거로 쓴다(C1).
   - A_lb에 넣는 전류는 선언되었거나 KCL로 고정된 전류뿐이고, 나머지는 0으로 둔다.
   - L은 LUT 최소 L, 커패시터는 θ 하한을 쓴다.
   - A_lb > 예산 + b_A이면 INFEASIBLE_TARGET(`area_budget_below_lower_bound`)으로 정지한다.
   - 출발값으로 만든 면적 추정 A_est는 보고만 하고 정지 근거로 쓰지 않는다.
4. **front를 잃은 4회로의 원인 보고**: B = 120 s 실측에서 folded·ngcc·nmcnr·pushpull은 front 0이었고, sf_pushpull·current_reuse는 시작점이 0이었다. 회로마다 다음을 결과 JSON에 쓴다.
   - (i) A_lb와 A_est를 예산과 비교한 값
   - (ii) 출발 구간 충돌 표(41 §6.6)
   - (iii) 예산 점 풀이의 위반 행
   이 정보로 '예산이 불가능' / '시작점 문제' / '탐색 문제'를 가른다. 예산 값을 고치는 것은 사용자 몫이다(§9 Q8).

| 항목 | 상태 | 증거 |
|---|---|---|
| 제약 행, MIM 밀도, 측정 부하 제외, S-3b I_max | OK `[ng-area-budget]`(미병합) | 538eeab, `E/search/area_decl.py` |
| 예산을 지키는 출발점, W 타당성, A_lb 사전 판정 | MISS | -- |
| 레이아웃 판정 축의 수동소자 면적, MOD8 재필터 | MISS | `E/layout/floorplan.py` |
| B = 120 s 결과 | front: common_gate 2, two_stage 1(최대 W 0.39 mm), two_stage_sf 1(최대 W 3.2 mm, 면적 7.3e-3 mm²). folded·ngcc·nmcnr·pushpull 0(folded·pushpull은 예산이 없을 때 예산의 약 2000배에서 front가 있었다). sf_pushpull·current_reuse는 시작점 0 | `[ng-area-budget]` 실행 보고 |

### 7.2 SLSQP 제약·목적 척도화

**문제**: 면적 행은 판정 단위 c = (v − A)/b_A가 약 1e6 규모라서 SLSQP가 status 4(제약 비호환)를 낸다. `[ng-area-budget]`은 이를 임의 양수 상수 곱으로 우회했다. 이 설계는 그 우회를 아래 규칙으로 대체한다.

**규칙**: 행 k의 **판정 단위** c_k = (경계 − 값)/b_k(b_k = 그 metric의 분해능)는 활성·동률·위반 판정과 보고에만 쓴다. **풀이 단위**는 ĉ_k = c_k · b_k / s_k이며, s_k = max(|경계_k|, |값_k(x_start)|, b_k)다. 즉 '경계에 대한 상대 여유'다. 목적은 f̂ = f / max(|f(x_start)|, b_f)이다. `ftol` = b_f / max(|f(x_start)|, b_f)로, 목적 분해능을 같은 척도로 옮긴 값이다.

s_k는 시작점마다 한 번 정하고 그 풀이 안에서는 고정한다. 그래야 SLSQP 문제가 반복 중에 바뀌지 않는다. 모든 양이 선언값·분해능·시작점 값에서 오므로 새 상수가 없다.

**불변식**: 척도화 전후의 활성 집합·위반 판정이 같다(판정은 c_k로만 한다).

**상태**: DEV(as-built `[ng-area-budget]`은 상수 곱).

### 7.3 성능·캐시

| 항목 | 설계 | 상태 |
|---|---|---|
| LUT memo 상한 | `LutMemo.from_sweep`(상한 = (n_θ + 1)·U_eval)을 평가 커널 컨텍스트 생성 때 부른다. U_eval은 첫 평가에서 센 서로 다른 키 수다. test의 상수 4096을 지운다 | PART(호출부 0) |
| tol_V 디스크 캐시 | 키 = 코드 버전 + 입력 내용 sha + 설정 지문. 저장소 밖 경로, 원자적 쓰기, 깨지면 재계산. 정리는 첫 쓰기 때만, 저장소와 모든 worktree의 `lut_v2_location.json`이 가리키지 않는 자료 id만 지우고, 사용 중·링크·폴더 밖 파일은 건너뛴다(사용자 결정 2026-10-08) | PART `[ng-tolv-cache]`: `TableCache`가 `__all__`에 없고 test가 없다. 계획서 N3.5 '디스크 캐시 위치' 문구를 갱신해야 한다 |
| 1변수 풀이 | Brent `bracket_root` + 입력 재사용 memo + 평가 안 tol_V 셀 재사용 | OK(master `004b7d2`, `E/sizing/bracket_root.py`) |
| core 성능 2~5 | memo 키, 레코드 지문 보관, 투영 지문, 열 키 캐시 | OK(master 병합) |
| 블록 국소 모델 | 블록 노드 부분 MNA를 봉인 스냅샷당 한 번 조립하고, ω=0 극한 풀이만 한다(41 §2.3) | MISS |
| GB4 상한표·출발 구간 | S0당 한 번(평가 커널 컨텍스트) | MISS |
| LUT r2 데이터, 검증 중점 L (0.165, 0.85, 1.75, 3.25) | OK `[worktree-agent-a90df…]`(미병합, master보다 45커밋 뒤) | -- |

---

## 8. 승인 없이 축소된 범위와 계획 이탈 (승인하거나 되돌릴 대상)

아래 표는 두 종류를 함께 모았다.
- R1~R28: 로드맵(`_drafts/engine/ROADMAP.md`, 이하 R), 초안, CONTRACT가 계획 요구를 줄이거나 미룬 곳.
- R29~R33: **이 design 자체가 계획 문구와 다르게 정한 곳**.

**결정(사용자 2026-10-08, "Q1~Q11 모두 네 의견대로 진행해")**: 아래 목록이 정본이다. 표의 '상태' 열은 결정 이전 상태를 남겨 둔 것이다.

| 결정 | 해당 행 |
|---|---|
| **복원** | R2, R3, R4(U-49를 복원으로 닫음, 계획서 정정), R5, R6, R8, R9, R10, R11, R12, R13, R14, R15, R16, R20, R21, R22, R23, R25(LR3은 실측 bin 규칙으로 계획 정정) |
| **축소 유지 승인** | R7: `rule_branch_coverage.json`을 만들지 않는다. `기록만` 분기와 S1 지원 밖 분기의 `unsupported_rule_branch` 정지는 그대로 둔다(DEC-59 안전망). R26: test 폴더 체계는 현행 그대로 쓴다. 패키지별 `tests/<패키지>/`, `structure/`, `integration/`, `generality/`이고 §10.3·10.4 경로가 이를 따른다 |
| **수용** | R29: 층 0 첫 회차 = spec 출발 구간. knee 앵커는 추가 후보로 쓴다. R30: U-12를 구조 매크로 모델로 대체한다. R31: U-24에 CM 루프 예외를 둔다 |
| **다른 질문에서 결정** | R17 → Q2, R19 → Q10, R24 → Q6(전력 축 = Σ V·I, U-10 변경), R27 → 잡음 범위 안(Q11), R32 → Q5b |
| **이미 결정됨** | R1(사용자 철회), R18·R33(결정 4번), R28(계획 승인) |

| # | 축소 내용 | 출처 | 계획 근거 | 상태 | 권고 |
|---|---|---|---|---|---|
| R1 | 층 0을 최소형(시작점 하나)으로. 블록별 gain bin front·조합 DP·`gain_budget_db` 출력 없음 | R §4 D18, R §0.2, `search/CONTRACT.md:26-31` | FR-4, DEC-03·71·73·77 | **사용자가 철회(2026-10-08)** | 41 §5대로 복원 |
| R2 | GB3(결합 변수 y) 범위 밖 | R §0.2 행 32, D18 | GB3, DEC-71 (7) | 미결 | 복원: 층 0 조립의 입력(§3.3). 내층 DP·중층 좌표강하는 DEC-73대로 기본 꺼짐 유지 |
| R3 | GB4를 'INFEASIBLE_TARGET만'으로 축소, DOF·수치 rank 범위 밖 | R §0.2 행 33, K6. 계획 N6.1 단위 7('GB4 축소')에도 반영됨 | FR-8, GB4, IC6 | 미결 | 구조 DOF와 수치 rank 복원(표본 수 = `dof_rank_sample_count`, 41 §4.5). 블록 gain 상한은 계획대로 격자 전수로 계산하고, 예산을 넘으면 '미상'으로 둔다(41 §4.2) |
| R4 | U-49 기본안(층 0 최소형, gain bin front·GB3 범위 밖)이 계획서 안에 있다 | P N7.2 U-49 | FR-4와 긴장 | 미결(계획서 안의 대기 결정) | 2026-10-08 지시로 U-49를 '복원'으로 닫고 계획서를 정정 |
| R5 | 블록 국소 모델·MNA 잔차·감도 게이트 범위 밖 | `metrics/CONTRACT.md:13-14`, 초안 M15:191, L7a:261 | FR-2, DEC-05·66, N3.8 | 미결 | 복원(41 §2, §3.8) |
| R6 | SP1(셀·0-1 BFS·stage·루프 (0)~(4)·끊는 점·R(u)·DEC-81) 연기, declared 대조 연기 | 초안 U25:196·201·133, R N5~N7 미착수 | FR-1, GB2, DEC-43·57·59·63·65·81 | 미결 | 복원(41 §1) |
| R7 | `rule_branch_coverage.json`과 검증 발동 0 분기 정지 없음 | graph CONTRACT | DEC-59 | 미결 | 복원(41 §1.10) |
| R8 | GB5 `gm_req`·`comp_approx_gap` 범위 밖 | `find_front.py:45-48` | DEC-92 (1)(2) | 미결 | 복원(§3.5) |
| R9 | `ls`(슬루·방향별 전류)·스윙·ICMR·`nqs_ratio`·`mismatch_sigma_v` 범위 밖 | `metrics/CONTRACT.md:14` | DEC-58·65·96, N3.8 | 미결 | 복원(§3.8) |
| R10 | spec 로더가 `gain_budget_db_override`·`driving_spec`을 거부 | `SPEC_CONTRACT.md:226-228`, R D5('N3.15 축소') | GB0, DEC-03, DEC-58 | 미결 | 복원(§3.1) |
| R11 | 예산 점 풀이 미작성, `n_starts`·x0 미작성 | `search/CONTRACT.md:535-537,591` | DEC-77, U-13, N3.5 | 미결 | 복원(§3.6) |
| R12 | MOD8 루프·LY7 재평가·판정 축 재필터 미구현(`pending_wiring`) | `layout/CONTRACT.md` 4.14, `search` S-14 | DEC-79 (b), DEC-84, LY3·LY7, 사용자 12번 (나) | 계획은 범위 안 | 구현(§3.9) |
| R13 | L 동치류 L 공유 사실상 꺼짐(`l_class` proposed) | `graph/CONTRACT.md:220` | DEC-17, LR1 | 미결 | 복원(§3.2) |
| R14 | 미러 비율 전류 강제 없음, DEC-95 (3) ratified·② 없음, tol_I 격자 최대 gm | `sizing/CONTRACT.md:276,741,766` | DEC-70, DEC-95, N3.6 | 미결 | 복원(§3.7) |
| R15 | 뷰별 교류접지(바이어스 종속 넷) U5로 연기. 차동쌍 '신호 gate 정확히 2' 조건 빠짐 | `graph/CONTRACT.md:491,538`, JU4:131 | SP1-1 (4), DEC-93 (1) | 미결 | 복원(41 §1.2) |
| R16 | 대칭 θ 묶기 열린 항목 | `search/CONTRACT.md` 3.23 (4) | 사용자 2026-10-08 대칭 결정 | 미결 | 구현(§6) |
| R17 | Pelgrom 계수 선언 없음 → mismatch 보고·matching L 하한 불가 | core 조사 | DEC-96 (2), N3.16 | 선행 조건 | PDK `*__mismatch.corner.spice`의 `vth0_slope`·`toxe_slope` 계열에서 A_VT·A_β를 유도하는 식과 단위 확인을 MOD1/`core` PDK 선언에 둠(§9 Q2). Q3(2026-10-08)로 A_eff 모델(전 slope 변수·bin별 slope·LUT 감도 열)로 확장(41 §6.4-2) |
| R18 | C10: 지속 진동을 undetermined로 유지(계약에 '사용자 승인'으로 기록) | `[ng-oracle-early]` 계약 L42-54 | 사용자 결정 2026-10-08 4번 | 사용자 결정과 모순 | 사용자 결정대로 되돌림(§4) |
| R19 | 오라클이 `pm_undefined`(개루프 RHP 극점 포함)를 일괄 INCOMPLETE로 판정 | `[ng-cmfb-pm]` README, `tools/spice_oracle/README.md:516` | 사용자 결정 A(엔진 탐색 규칙), P N3.6 오라클 합격 정의 | 미결 | Nyquist Z와 폐루프 과도로 판정하고, 둘 다 결정할 수 없을 때만 INCOMPLETE(§4-5). 개루프 RHP만으로 FAIL을 주지 않는다 |
| R20 | ΔA_tie = grid² | `E/layout/floorplan.py:83` | DEC-79, DEC-95 (2) | 미결 | 계획 식으로 수정 |
| R21 | LY5 `W_adjustable=False` 즉시 완화 | `layout/CONTRACT.md:217,306-311` | LY5 마지막 문장 | 미결 | 제거 |
| R22 | LY8 `ly.diffusion` 없음, 판정 축 면적에 수동소자 없음 | `E/layout/_ly_fields.py` | DEC-89 (5), DEC-91 (2), DEC-79 | 미결 | 구현(§3.9) |
| R23 | `verified_by`·모델 오차 레지스트리, `spice_unverifiable` 없음 | `metrics/CONTRACT.md:246,424` | DEC-72, DEC-90 (3), N3.8 | 미결 | 구현(§3.8) |
| R24 | 전력 축 = Σ V·I(`power_dc_w`). DEC-78은 공급 전류 합 | `E/search/objectives.py:9`, `metrics/CONTRACT.md:544,627` | DEC-78, U-10 | 정의 차이 | 사용자 결정(§9 Q6) |
| R25 | LUT: GMBS 열이 있는데 VS 축 선형, FC 위반 칸 선형 폴백, `vgs_for_current_density` 없음, bin 소속을 메타 대신 식으로 판정 | `lut/CONTRACT.md` 1.4, 4.0.1, 4.2 | DEC-87, DEC-88, LR3 | 미결 | `vgs_for_current_density`와 VS Hermite 구현. bin 소속은 실측 384/384 일치 근거로 식 유지를 제안하되 계획 LR3 정정이 필요(사용자 확인) |
| R26 | 새 test 체계의 `contracts/`·`regression/`·`oracles/`·`perf/` 폴더 없음 | `E/tests/` | N3.11, N6.2 T9, IC1~IC11 | 미결 | 단위별로 작성 |
| R27 | 슬루·정착은 SPICE 기록만 한다. 잡음 경로 없음 | 초안 SF:209, M15:43 | DEC-90 (2), DEC-96 (3) | 슬루·정착 '기록만'은 사용자 승인(Q5 (ii)). **잡음은 사용자 결정 2026-10-08로 범위 안이 됨**("노이즈 spec을 추가해서 코드를 만들어야지.") | 슬루·정착은 유지. 잡음은 41 §7대로 구현한다(spec 제약, LUT 잡음 열, adjoint 잡음 해석, 오라클 `.noise`). 계획서 N1.2와 DEC-96 (3)의 잡음 문구는 정정이 필요하다 |
| R28 | 정밀 경로(내층 DP·중층)·전역 샘플·bisection 기본 비활성 | 초안 M6:299 | DEC-73·75 | **계획 승인됨**(기본 비활성) | 유지 |
| R29 | (design 이탈) 층 0 첫 회차의 고정 입력을 LR5 knee 앵커가 아니라 41 §6 출발값으로 둔다 | 41 §5.3 | DEC-71 (3), LR5 | 사용자 확인 필요 | 채택 권고. 근거: 출발값은 스펙에서 나오고, knee는 스펙과 무관하다 |
| R30 | (design 이탈) U-12 단일단 규칙을 일반 매크로 모델(41 §6.5)의 특수해로 대신 낸다. 단일단 판정을 `compensation: null` 태그가 아니라 구조로 한다 | 41 §6.5, §3.5 | U-12, U-50, DEC-85 | U-12 미확정 | 채택 권고(같은 값이 나오고 태그에 의존하지 않음) |
| R31 | (design 이탈) U-24 정지에서 '포트쌍 CM 루프 대응' 루프 뷰를 빼고 사용자 CM 결정(보고 + 경고)을 적용한다 | 41 §1.8 | U-24, 사용자 2026-10-08 CM 결정 | 사용자 확인 필요 | 채택 권고(두 결정의 충돌을 구조적 대응으로 해소) |
| R32 | (design 결정) gain 제약·rout 제약이 모두 없는 회로는 층 0을 끄고 '성능 판정 보류'로 탐색. DEC-71 (3)은 '사이징 대상에서 뺀다' | 41 §5.1 | DEC-71 (3), DEC-85 | 사용자 결정 | §9 Q5b |
| R33 | (design 결정) 지속 진동 판정을 d56ba66 문구(undetermined, '사용자 승인')에서 사용자 결정 2026-10-08 4번(unstable)으로 바꾼다 | §4-2·3 | 사용자 결정 4번 | 사용자 결정이 근거 | 적용 |

---

## 9. 사용자 결정

**결정일 2026-10-08**. 사용자 원문은 "Q1~Q11 모두 네 의견대로 진행해"이며, 전문은 `_drafts/user_decisions.md`의 마지막 항목에 있다. 계획서 N7.2에 U id로 올리는 일은 계획서 정정 커밋에서 한다.

| # | U | 결정 |
|---|---|---|
| Q1 | U-53 | §8 결정 목록대로 |
| Q2 | U-54 | Pelgrom 계수는 PDK `*__mismatch.corner.spice`에서 가져온다. 유도식과 단위는 41 §6.4-2에 기록하고, MC 대조 test로 확정한다 |
| Q3 | U-17 확장 → U-55로 닫음 | **확정(2026-10-08 "q3,q4는 네 제안대로 해")**. mismatch 모델 = 유효 계수 A_eff(toxe의 Vth 기여·약반전 voff 항 포함, LUT 감도 열, bin별 slope -- 41 §6.4-2), 옛 식 대체. 파일럿 `offset_in_sigma_mv ≤ 3.3 mV`(옛 5 mV 대체). 출처 없는 회로는 절대값 대신 구조 가드 `offset_excess ≤ √2` + 보고. 아래 §9.2 |
| Q4 | U-55 | **확정(2026-10-08, 같은 원문)**. 스윙 = 포화 기준(`swing_out_v`), ICMR = 폭(`icmr_v`) + 선언 입력 DC 포함(`icm_margin_v`), 여유 = LUT tol, 레일 밖 입력 불허, 3σ 관례 미사용. 파일럿 스윙 ±1.2 V, nmcnr ICMR·스윙 ≥ 0.5 V, ngcc ICMR ≥ 0.6 V 유지. 헤드룸 불가는 탐색 전 보고(41 §4.6). 아래 §9.2 |
| Q5 | U-44 | topology `_declared_target_spec`(2026-09-21 확정)의 성능 목표를 제약으로 올린다. 회로별 현황은 아래 표 |
| Q5b | U-56 | 제약이 남지 않는 회로도 사이징에서 빼지 않는다. '성능 판정 보류'로 탐색하고 보고한다(41 §5.1) |
| Q6 | U-10 변경 | 전력 축 = Σ V·I(as-built `power_dc_w`). DEC-78 문구를 고친다. 기둥 대조 기록은 유지한다 |
| Q7 | U-06 | **SP1이 산출한 J 항목은 2026-10-08 결정으로 닫혔다(§9.3).** J 공동분석은 SP1 구현 뒤에 한다. Q3·Q4 결정(2026-10-08)으로 목록에 더한 항목: (i) 입력 DC 값 -- nmcnr 0 V(agnd 관례)는 L ≥ 0.5 µm 입력에서 ICMR 창 밖, 파일럿·two_stage·folded·ngcc·common_gate SP-2 값(41 §4.6), (ii) sf_pushpull 차동 대응 짝 M6↔M8·M5↔M7의 matching(서로 다른 gate 묶음이라 J-U4 대칭쌍 그룹이 없다, 레이아웃 matching 대상 확정), (iii) sf_pushpull·pushpull 4-팔로워 버퍼 스택의 헤드룸(41 §4.6 보고 결과를 보고 회로 해석) |
| Q8 | U-57 | 면적 예산은 그대로 둔다. 진단(§7.1-4) 결과를 보고 다시 논의한다 |
| Q9 | U-36 확장 | 저항 면적을 면적 축에 넣는다. 저항 단위 면적은 PDK에서 유도한다(§7.1) |
| Q10 | U-58 | 오라클 최종 판정은 Nyquist Z = N + P(`.pz`로 독립 측정)와 폐루프 과도로 한다. 둘 다 판정할 수 없을 때만 INCOMPLETE다. 탐색은 결정 A의 보수 규칙을 유지한다(§4-5~7) |
| Q11 | U-59 | 잡음: 파일럿은 `noise_out_int_vrms ≤ 300 µVrms`(CMFB·바이어스·스위치 포함, 하한 1 Hz, 상한은 유도값)이다. 나머지 7회로는 `noise_excess_th ≤ 2`에 열잡음 평탄값·1/f corner 보고를 더한다. pushpull_follower는 보고만 한다. LUT에 저주파 점을 추가한다. DEC-96을 고친다(41 §7) |

**Q5 회로별 성능 제약 현황**(spec `constraints` + `_declared_target_spec`):

| 회로 | 이미 제약에 있는 것 | 이번에 올리는 것 | 아직 없는 값 |
|---|---|---|---|
| current_reuse(파일럿) | gain ≥ 54, PM ≥ 70, CMRR·PSRR ≥ 60 | 잡음 ≤ 300 µVrms. Q3·Q4(§9.2): offset σ ≤ 3.3 mV(옛 mismatch ≤ 5 대체), 출력 스윙 ±1.2 V | 입력 DC(SP-2) |
| two_stage_ota | gain ≥ 57 | GBW ≥ 7 MHz(보상 목표 `user_spec`을 제약으로). Q3: 옛 mismatch ≤ 5 폐기 → 가드 `offset_excess ≤ √2` | PM(SP-3) |
| two_stage_ota_sf | rout ≤ 1 kΩ, gain은 two_stage_ota를 참조 | GBW는 두 회로 상속. Q3: 옛 mismatch 참조 폐기 → 가드 | PM |
| ngcc_3stage_ff | GBW ≥ 10 MHz, PM ≥ 63.4 | `icmr_v ≥ 0.6 V`(값 유지, 이름 부여). Q3: 가드 | gain |
| nmcnr_amplifier | GBW ≥ 816 kHz, PM ≥ 70 | Q4: `icmr_v ≥ 0.5 V`, `swing_out_v ≥ 0.5 V`. Q3: 가드 | gain(논문 > 100 dB는 채택하지 않음) |
| sf_pushpull_output_opamp | gain ≥ 65, GBW ≥ 60 MHz, rout ≤ 1 kΩ | Q3: 가드 `offset_excess ≤ √2` | PM(SP-3) |
| pushpull_follower_buffer | rout ≤ 1 kΩ | -- | (버퍼, 다른 값 불필요) |
| folded_cascode | 없음 | Q3: 가드 `offset_excess ≤ √2` | gain·GBW·PM 모두 → Q5b 판정 보류 |
| common_gate_amplifier | 없음 | -- | gain·GBW 모두 → Q5b 판정 보류 |

모든 회로에 공통으로 잡음 가드와 면적 예산 제약(결정 11)을 함께 둔다.

### 9.1 (기록) 결정 전 질문 원문

결정 이전의 질문 표다. 기록용으로 남긴다.

| # | U 후보 | 질문 | 왜 사용자 몫인가 | 막는 것 |
|---|---|---|---|---|
| Q1 | U-53 | §8 R2~R26과 R29~R31 각 행(R19는 Q10으로 따로 묻는다)을 복원할지, 승인(축소 유지)할지. 특히 R3(DOF 수치 rank), R4(U-49 닫기), R25(LR3 bin 소속 규칙 정정) | 범위 | 해당 구현 |
| Q10 | U-58 | 결정 A('RHP 극점으로 정의 불가 = 불안정(실패)')를 엔진 탐색 규칙으로만 두고, 오라클 최종 판정은 Nyquist Z와 폐루프 과도로 할지(§4-5~7, R19). 조건부 안정 회로를 합격시킬 수 있는 완화다 | 사용자 결정 문구의 해석 | 오라클 판정 |
| Q11 | U-59 | 회로별 잡음 제약 값: `noise_in_density_ss_v_rthz`(어느 주파수에서 얼마인가: 열잡음 영역, 1/f 영역), `noise_in_integrated_ss_v`(대역과 값). 어느 회로에 둘지도 정해야 한다 | spec 값 | 잡음 제약·출발 구간 활성(41 §7) |
| Q2 | U-54 | Pelgrom 계수 출처로 PDK `sky130_fd_pr__{n,p}fet_01v8__mismatch.corner.spice`(slope 파라미터, 체크아웃 f62031a1)를 쓸지. 유도식과 단위 확인은 엔진이 하고, 출처를 기록한다 | PDK 출처 채택 | matching L 하한(41 §6.4-2), `mismatch_sigma_v` |
| Q3 | U-17 확장 | 오프셋·미러비 오차 스펙 값. 파일럿 `mismatch_sigma_mv ≤ 5`는 U-17 pending이다. 나머지 8회로에도 둘지 | spec 값 | matching L 하한 활성 |
| Q4 | U-55 | 출력 스윙·ICMR 스펙 값. ngcc `icmr_v ≥ 0.6 V` 말고는 선언이 없다 | spec 값 | 헤드룸 gm/ID 하한의 스윙 몫(41 §6.2) |
| Q5 | U-44 | gain 제약이 없는 5회로(common_gate, folded, ngcc, nmcnr, pushpull)의 gain 값, 그리고 GBW·PM이 없는 회로의 값 | spec 값 | 그 회로의 gain 예산·속도 상한 비활성(41 §5.1) |
| Q5b | U-56 | gain 제약도 rout 제약도 없는 회로의 처리. DEC-71 (3)대로 사이징 대상에서 뺄지, 층 0 없이 탐색만 하고 '성능 판정 보류'로 둘지. DEC-85(9회로 전부 합격)와 충돌한다 | 범위 | 그 회로의 층 0·합격 판정 |
| Q6 | U-10 재확인 | 전력 목적 축을 DEC-78 '레일 공급 전류 합'(U-10 확정)으로 할지, as-built Σ V·I로 할지. 3레일 회로에서 front 순서가 달라질 수 있다 | 목적 축 정의 | §3.8 |
| Q7 | U-06 확장 | SP1 유도 뒤 J 공동분석: J2~J13, J12-a~i, 6a 열린 항목 ⑮(J 항목이 없는 DC 역할 그룹 둘) | 회로 해석 | GB2 `review_needed` 해소 → 탐색 |
| Q8 | U-57 | 7.1 진단 뒤에도 예산 안에 해가 없는 회로가 남으면 그 회로의 면적 예산을 바꿀지 | spec 값 | 그 회로 합격 |
| Q9 | U-36 확장 | 저항 면적을 면적 축에 넣을지(단위 면적 PDK 선언 필요), 결정 11 문구대로 뺄지 | 목적 축 정의 | §7.1, DEC-79 `review_needed` |

### 9.2 Q3·Q4 회로별 선언 (사용자 결정 2026-10-08 "q3,q4는 네 제안대로 해")

원문 전문은 `_drafts/user_decisions.md` 마지막 항목, 분석 근거는 `_drafts/engine/matching_swing_spec_proposal.md`다. metric 정의는 §3.8-8, 출발 구간은 41 §6.2·§6.4-2, 탐색 전 보고는 41 §4.6이다. 모든 제약 행은 `{metric, op, value, source}` 형식이고 `source`는 아래 '출처' 열이다.

| 회로 | offset (Q3) | 스윙·ICMR (Q4) | 출처·유도 |
|---|---|---|---|
| current_reuse(파일럿) | `offset_in_sigma_mv <= 3.3`(옛 `mismatch_sigma_mv <= 5` 대체). `offset_sys_mv <= value_from_constraint: offset_in_sigma_mv`(옛 `mirror_ratio_error_mv` 대체) | `swing_out_v >= 2.4`(차동 p-p, 논문 Table I 출력 스윙 스펙 ±1.2 V). `icm_margin_v >= 0`: 입력 DC는 SP-2 (c)(J-E)로 y_icm에서 판정하고 `required_input_cm_v`를 보고한다. 입력 창이 pfet 최단 L bin에서만 열리면 경고 `icmr_window_short_l_bin`(41 §4.6)을 낸다 | `user_spec`(2026-10-08). 3.3 mV 유도: 입력 용량이 논문 β ≈ 0.48 가정(Cf = Cs = 500 fF → Cgg1 ≈ 41.7 fF)을 넘지 않는 최대 면적에서 σ_os = (Σ A_i√c_i)/(2√Cin), gm/ID 15·L 0.5 µm A_eff 기준(제안서 §2.3 (C)). 이 값은 β 0.48 가정의 앵커이고, β 손실이 전력과 교환되는 점은 목적 함수가 다룬다. 정적 ½ LSB 규칙은 이 Cf/Cs에서 해가 없음(제안서 §2.3 (A))을 함께 기록한다 |
| two_stage_ota | 옛 5 mV 절대값 폐기 → `offset_excess <= √2` 가드 + `offset_in_sigma_mv`·`offset_sys_mv` 보고 | 보고만 | 가드 `user_spec`(부하 기여 ≤ 입력쌍 기여, 잡음 가드와 같은 등분 원칙) |
| two_stage_ota_sf | 옛 `value_from_file: two_stage_ota#mismatch_sigma_mv` 폐기 → 같은 가드 + 보고 | 보고만(출처의 '상한 제한'이 sky130에서 좁은 스윙으로 나타난다) | 같음 |
| folded_cascode, ngcc_3stage_ff, nmcnr_amplifier, sf_pushpull_output_opamp | 같은 가드 + 보고(출처에 offset 값 없음) | ngcc: `icmr_v >= 0.6`(값 불변, 이름만 부여, 1.8 V 기준 VDD/3). nmcnr: `icmr_v >= 0.5`, `swing_out_v >= 0.5`(원문 단위 이득 0.5 V 계단 측정 조건, 원문 절대값 그대로). 입력 DC는 SP-2 (c)(J-E: 창 안 자유 변수, agnd 0 V 관례 미적용, `required_input_cm_v` 보고). folded: 보고만. **sf_pushpull: 입력 DC 0.9 V(agnd) 유지 + `icm_margin_v >= 0` 제약**(J-E), 4-팔로워 출력 버퍼 창은 탐색 전 실현가능성 보고(41 §4.6 `buffer_window_report`) | ngcc: 기존 사용자 확정. nmcnr: `user_spec`(Leung et al. Table 1 측정 조건 앵커). sf_pushpull `icm_margin_v`: `user_spec`(J-E 2026-10-08, agnd = 분할 전원 중간 레일 확인). ICMR 제약 회로는 입력 DC가 선언되면 `icm_margin_v >= 0`을 함께 판정(§3.8-8) |
| pushpull_follower_buffer, common_gate_amplifier | 차동쌍이 없어 offset 제약·가드 없음. pushpull은 정지 전류 산포를 `mirror_ratio_sigma_pct`와 같은 식으로 보고 | 보고만(pushpull 선언 입력 DC agnd라 `icm_margin_v` 보고, common_gate 스윙은 출처 식 VDD − VDSAT3 − VDSAT1 − VDSAT2와 대조) | -- |
| 전 회로 | `mirror_ratio_sigma_pct` 보고 | 탐색 전 헤드룸 달성가능성 보고(41 §4.6) | -- |

**유지·이관 항목**:
- bulk 기본 규칙(NMOS = 최저 레일, PMOS = 최고 레일)은 유지한다(Q4 (6)).
- 입력 DC 변경, sf_pushpull M6↔M8·M5↔M7 matching, 버퍼 스택 헤드룸은 회로 해석이므로 J 공동분석 목록에 넣었다(위 Q7 행). 2026-10-08 J 결정으로 닫혔다(§9.3).
- Monte-Carlo offset 분포와 스윙·ICMR DC 스윕 확인은 오라클(U6)이 한다(§10.2).
- 옛 이름(`mismatch_sigma_mv`, `mirror_ratio_error_mv`)이 쓰인 library spec 3개(파일럿·two_stage·two_stage_sf)는 U5가 새 이름·값으로 바꾸고, 옛 이름은 로더 옛 이름 표로 거부한다.

### 9.3 J 공동분석 결정 (사용자 결정 2026-10-08 "j해석은 네의견에 모두 동의해.")

**근거와 원문**: 분석 패킷은 `_drafts/engine/J_joint_analysis_2026-10-08.md`(SP1 `[u1-sp1]` 9회로 실측)다. 결정 전문은 `_drafts/user_decisions.md` 마지막 항목이다. 패킷의 권장안(A2·B1·C1·D1·E·F1-a)을 모두 채택했다.

| 패킷 절 | 결정 | 설계 위치 | 닫는 계획 J 항목 |
|---|---|---|---|
| J-C·J-D 공통 | **복합 diode 구조 규칙 D1**: 같은 DC 가지를 따라가 자기 gate에 닿는 소자 = diode형 바이어스. 실측 발동 sf 6·파일럿 2, 나머지 7회로 무동작. DC 역할·미러 인식·루프 분류에 공통으로 쓴다 | 41 §1.12.1, §1.13 | J12-h, J11(레플리카 루프), N3.2-2 (나) 보류 |
| J-C | 파일럿 CMFB 루프 뷰에서만 Vbias2 교류접지(J1 예외), M58·M63 = 레플리카(D1). 'M58 전류 분할'은 GB7 꼬리 예산 항목(I_tail,eff = I6 + I7 − I68), AC 경로 아님. M7 이중 역할(DC 꼬리 + AC CM 주입) 공존 | 41 §1.12.6, §1.12.1 '바뀌지 않는 것', §3.2-3 사실 표 | J11(파일럿 CMFB·M58), J4 |
| J-D | sf: 세 그룹 = 저항 자기바이어스 캐스코드 미러의 복합 diode 기준(D1). M6↔M8·M5↔M7·R1a↔R1b `branch_symmetric` matching | 41 §1.12.1, §3.2-3 `matching_pair` | J12(sf 부분), J14(sf 부분), J12-h |
| J-A | ngcc A2: 주경로 3단 V1 → V2 → Vout + feedforward 셀 FF1·FF2. gain 예산은 주경로 곱에만 둔다. gmf = 우회한 단 gm 비율은 sizing 제약 후보(출처 기록) | 41 §1.12.2, §2.1·2.2, §4.3, §5.1, §6.5, §3.8-8 `ff_gm_ratio` | J12(ngcc 묶음 경계·gmf1 가지), J12-d 갈래(ngcc만 발동, K8 유지) |
| J-B | 중첩 Miller 내부 루프 = 보상 루프(루프 뷰 미생성). 안정도 = 전체 `pm_ss_deg` + 개루프 RHP 극점 없음(P = 0) | 41 §1.12.3 | J11(ngcc·nmcnr 루프 뷰) |
| J-F | 루프 극성 = 뷰의 DC 사이클 극성, 커패시터 경유 사이클은 `ac_only`. L 동치류 주인 = 주경로 신호 소자(구조 규칙 `main_path_signal`), ngcc {M8, M14} 주인 M8, DC 역할 신호 소자 | 41 §1.12.4·5, §3.2-3 `dc_role` | J7 |
| J-E | nmcnr 입력 DC = SP-2 (c) 창 안 자유 변수(agnd 0 V 관례 미적용). sf 0.9 V 유지 + `icm_margin_v >= 0` 제약 + 4-팔로워 출력 창 사전 보고. 파일럿 SP-2 (c) 유지 + 짧은 L bin 경고 | 41 §4.6 입력 DC 정책, §9.2 | Q7 (i)·(iii) |

**구현 전제(결정 원문 순서)**: design 개정(이 v1.5) → 공유 엔진 코드(U1b, §11) → 회로별 `structure.json`(§3.2-3 표, U1b 병합 뒤).

---

## 10. 신규 API·검증

### 10.1 신규 공개 API 서명

41 §8에 있는 API(`build_s1v`, `block_local_gain`, `achievability`, `start_intervals`, `layer0_budget`, `size_and_seal_local`, `count_budget`, `EvalBudget`, `noise_params`, `noise_analysis`, `mismatch_dvgs`, `headroom_bound`)에 아래를 더한다.

```python
def coupling_vars(s1: S1, s1v: S1v) -> Coupling                                    # E/graph/coupling_vars.py  {vars[CouplingVar], column_block_map}
def canonical_form(s1: S1) -> Canonical                                             # E/graph/canonical_form.py {order, generators}
def automorphism_orbits(s1: S1, canon: Canonical, untie: list[Untie]) -> Orbits     # E/graph/automorphism_orbits.py
def ls_fields(snap: GraphSnapshot, s1v: S1v, spec: SizingSpec) -> LsFields          # E/metrics/ls_fields.py
def offset_analysis(snap: GraphSnapshot, s1v: S1v, view_key: str) -> OffsetResult  # E/metrics/offset_analysis.py {sigma_in_mv, excess, contrib[], resolution}
def swing_icmr(snap: GraphSnapshot, s1v: S1v, spec: SizingSpec) -> SwingIcmr       # E/metrics/ls_swing.py {swing_out_v, out_ranges[], icmr_v, window, icm_margin_v}
def sensitivity_gate(snap: GraphSnapshot, s1v: S1v, metric: str) -> GateResult     # E/metrics/sensitivity_gate.py
def solve_budget_point(ctx: SearchContext, budget: ObjectiveBudget) -> FrontPoint   # E/search/budget_point.py
def converge(front: Front, ctx: SearchContext, pdk: PdkDecl) -> ConvergedFront      # E/convergence/converge.py (MOD8)
def build_report(result: PipelineResult) -> dict                                    # E/report/report_json.py (MOD9)
def run_gmid_design_pipeline(spec_path, *, search=None, output_dir=None, instrument=False, activations_out=None) -> int  # E/pipeline/run.py
# J 공동분석(§3.2-3, 41 §1.12) -- 단위 U1b
def structure_rule_fp() -> str                                                       # E/graph/s1v_key.py  (사실 stale 판정 지문, §3.2-3)
def build_s1(doc, supplies_v=None, previous=None, column_limit=None, *, structure=None) -> S1Graph  # E/graph/s1_build.py  (기존 서명에 keyword `structure` 추가 -- dc_role 사실 소비)
```

41 §8의 `composite_diodes`, `feedforward_cells`, `loop_roles`도 U1b가 만든다.

### 10.2 검증: 오라클 종류와 test

오라클 종류 (a) 손계산, (b) 참조구현, (c) SPICE, (d) 사용자 선언은 P N0.4를 따른다. 41 §9 표에 다음 행을 더한다.

| 항목 | 오라클 | test(신규) | 단언 |
|---|---|---|---|
| 대칭 궤도·θ 묶기 | (a) 5T·캐스코드 toy, (b) 전수 순열 자기동형(소자 ≤ 8 toy) | `tests/graph/test_canonical_form.py`, `test_automorphism_orbits.py` | diff_pair 두 멤버가 같은 궤도에 든다. crosstab을 생성한다. 이름 전단사나 수동소자 단자 순서를 바꿔도 front 해시가 같다. 파일럿 R1/R2가 한 궤도로 묶이고 전류 부호는 −1이다 |
| MOD8 수렴·재필터 | (a) W_request 합성 픽스처 | `tests/convergence/test_converge.py` | 레이아웃 안 재시도에서 커널 호출 0. 결과마다 재평가 1회. K_max에 닿으면 NONCONVERGENT |
| C10 한계 사이클·Nyquist | (c) 지속 진동 fixture, 조건부 안정 fixture | `tools/spice_oracle/tests/test_oracle_c10_stability.py` | 지속 진동 → unstable(limit_cycle) FAIL. 개루프 RHP이면서 Z = 0이고 과도 안정 → 합격 |
| 척도화 | (a) 1e6 규모 행 픽스처 | `tests/search/test_slsqp_scaling.py` | status 4 없음. 척도화 전후 활성 집합 동일 |
| 아카이브 타입 | (a) 왕복 | `tests/search/test_archive_records.py` | float 왕복 비트 동일. 문자열 숫자는 거부 |
| CM 감지 저항 | (a) R 부하 손계산 | `tests/search/test_cm_sense_r.py` | 최소 R에서 ΔG ≤ b_gain |
| offset 해석(§3.8-8) | (a) 이름 없는 5T·2단 toy 손계산(입력쌍 + 차동쌍 drain 미러 부하), (b) 소자별 섭동 DC 재풀이(MNA 전달과 다른 방법) | `tests/metrics/test_offset_analysis.py` | σ_in이 resolution 안에서 일치. 캐스코드 기여가 1/(gm·ro) 배로 감쇠. 이름 전단사 불변 |
| 스윙·ICMR(§3.8-8) | (a) CS·캐스코드·follower toy 경로 합 손계산 | `tests/metrics/test_ls_swing.py` | 경계 = VDSAT + tol_vdsat, 레일 밖 자름, 빈 창은 음수 폭, 입력 DC 미선언이면 `input_dc_pending` |
| 오라클 offset Monte-Carlo | (c) ngspice mismatch 블록 변수를 소자마다 gauss로 둔 MC(오라클 측, 엔진 비의존). 표본 수는 MC σ 추정의 상대 표준오차가 엔진 resolution과 같아지도록 유도 | `tools/spice_oracle/tests/test_oracle_offset_mc.py` | MC 입력 offset σ와 엔진 `offset_in_sigma_mv`의 차를 `model_error_offset_in_sigma_mv`(DEC-72)로 기록. 파일럿 제약 판정에 오라클 값 사용 |
| 오라클 스윙·ICMR DC 스윕 | (c) 출력 DC(되먹임으로 이동)·입력 공통모드 `.dc` 스윕에서 모든 MOS VDS ≥ VDSAT 구간 측정 | `tools/spice_oracle/tests/test_oracle_swing_icmr.py` | 측정 구간과 엔진 [V_lo, V_hi]·창의 차를 모델 오차로 기록. 41 §4.6 '알려진 사례' 4건의 실제 창을 잰다 |

### 10.3 IC1~IC11 계약 test (P N4.1)

R26(축소 유지)에 따라 test 경로는 현행 체계를 따른다. 별도의 `contracts/` 폴더는 만들지 않는다.
- 각 IC test는 담당 패키지 폴더 `E/tests/<패키지>/test_ic<n>_<이름>.py`에 둔다.
- 9회로를 실행하는 test(IC7·IC11)는 `E/tests/integration/`에 둔다.

| IC | test | 입력 | 단언 | 단위 |
|---|---|---|---|---|
| IC1 | `test_vgs_consistency_all_devices` | 9회로 봉인 해 | 모든 소자 \|ΔlnIDu\|/(gm/ID) ≤ tol_V | 4 |
| IC2 | `test_order_shuffle_invariance` | 소자·그룹 순서를 섞은 입력 2벌 | 이산 필드 동일. 연속 필드는 tol 안 | 4 |
| IC3 | `test_coverage_and_field_completeness` | 레이아웃·결과 JSON | 소자 누락 0, 이름 충돌 0 | 9 |
| IC4 | `test_role_label_removal_invariance` | 태그 키가 있는 입력과 없는 입력 | 결과 해시 동일(T2) | 3 |
| IC5 | `test_gate_docstring_declares_blind_spots` | `check_*` 등 게이트 함수 전수 | docstring에 '검사하지 않는 것'과 `영역:` | 0 |
| IC6 | `test_ic6_dof` | 사고19 픽스처 | over/underdetermined 판정(41 §4.5) | 7 |
| IC7 | `test_all_library_topologies_run` | 9회로와 검증 발동 0 분기 변형 | 발동표 생성, 정지(exit 2) | 3 |
| IC8 | `test_unevidenced_derivation_stops_before_search` | 증거 없는 유도 픽스처 | exit 2 | 3 |
| IC9 | `test_no_raw_duplicated_writes` | 소스 AST | 원시 대입 0(구조 규칙 G와 같은 검사기 재사용) | 0 |
| IC10 | `test_cache_key_covers_mutable_state` | 같은 θ, 입력 필드 하나만 변경 | 옛 값 미반환 | 4 |
| IC11 | `test_rail_origin_shift_invariance` | nmcnr ±0.9 V와 0/1.8 V, 3레일 회로 | VGS·VDS·VSB·gm_id·W·metric이 tol 안에서 같음 | 10 |

### 10.4 DoD 명령

`$PY` = `C:\Python314\python.exe`, 작업 위치는 저장소 루트다.

| 범위 | 명령 |
|---|---|
| 전체(slow 제외) | `$PY -m pytest skills/analog-gmid-design/gmid_engine/tests -q -m "not slow"` |
| IC 계약 | `$PY -m pytest skills/analog-gmid-design/gmid_engine/tests -q -k "test_ic"` |
| 9회로 구조 표(S1v·A_max·Π·인증 비율) | `$PY -m pytest skills/analog-gmid-design/gmid_engine/tests/integration/test_structure_tables.py -q` |
| 9회로 E2E(T9) | `$PY -m pytest skills/analog-gmid-design/gmid_engine/tests/integration -q` |
| 오라클 | `$PY -m pytest skills/analog-gmid-design/tools/spice_oracle/tests -q` |

---

## 11. 구현 단위 (병렬 배분용)

**목적**: 오케스트레이터가 code agent를 최대 6개까지 동시에 돌릴 수 있도록 구현을 독립 단위로 나눈다.

**배분 규칙**
- **파일 소유**: 한 단위가 고치는 파일은 그 단위만 고친다. 아래 '범위' 열이 파일 소유권이다.
- **공유 파일**
  - `E/_module_map.py`: 각 단위는 자기 행만 추가한다. 병합할 때 오케스트레이터가 합친다.
  - `E/<패키지>/__init__.py`의 `__all__`: 그 패키지를 소유한 단위만 고친다. 다른 단위의 새 API가 필요하면 아래 '선행' 열의 단위가 먼저 공개한다.
- **선행 단위가 끝나기 전**: 그 인터페이스(41 §8, 40 §10.1 서명)를 기준으로 toy 입력 test부터 쓴다. 실제 회로 test는 선행 단위가 병합된 뒤에 활성화한다.
- **완료 조건**(PDCA 구현 단계, 각 단위 공통)
  - 아래 '확인 행'의 42 기준표 행이 OK가 된다.
  - 그 단위의 test가 통과한다.
  - 전체 suite(`not slow`)가 통과한다.
  - 코드 작성 주체와 test 작성 주체가 다르다(WP-13).

**U0 -- 선행 병합**(오케스트레이터, code agent 아님)
- 대상 브랜치: `ng-cmfb-pm`, `ng-oracle-early`(계약), `ng-tolv-cache`, `ng-layer0-canon`, `ng-area-budget`, `worktree-agent-a90dfb25fa6fe9f04`(LUT r2), `ng-bridge`.
- 이 브랜치들을 병합하고, 병합할 때마다 전체 suite를 돌린다(사용자 결정 3).
- 이후 단위들은 병합된 master를 출발점으로 쓴다.

| 단위 | 범위(소유 파일·패키지) | 설계 절 | 선행 | 웨이브 | 확인 행(42) | test 계획 |
|---|---|---|---|---|---|---|
| **U1 SP1 구조** | `E/graph/` 신규 파일: `views`, `ac_ground_view`, `signal_reach`, `cells`, `drive_kind`, `stage_bfs`, `blocks`, `pole_nodes`, `loops`, `loop_classify`, `loop_cuts`, `polarity`, `buffer_bundles`, `output_direction`, `composite_blocks`, `declared_compare`, `s1v_build`. `structure.json` 로더. L 동치류 `derived` 처리와 주인 결정 | 41 §1, 40 §3.2 | U0 | 1 | FR-1, DEC-17·29·43·57·63·65·81, D-GB1a, D-GB2a~j | 41 §9 SP1·루프 행. toy 2~4소자(a), 9회로 표(d), 이름 전단사 |
| **U1b J 규칙 + structure 사실** | `E/graph/` 신규 파일 `composite_diode.py`, `feedforward_cells.py`, `loop_roles.py`. 수정 파일: `dc_roles.py`(규칙 1c 복합 diode, 규칙 4 `dc_role` 상속), `s1_build.py`(`structure` 인자, S1 키에 사실 지문), `drive_kind.py`(미러 입력 확장), `cells.py`(복합 diode 묶음 `diode_load`), `stage_bfs.py`(diode 단자 비용), `blocks.py`·`composite_blocks.py`(FF 분리, FF 합류는 복합 블록 아님), `loop_classify.py`((1.6) 추가, (나) 축소), `polarity.py`(DC 사이클 극성·`ac_only`), `l_classes.py`(`main_path_signal`), `view_analysis.py`, `ac_ground_view.py`(뷰 한정 예외), `matching_groups.py`(`matching_pair`), `structure_load.py`(concept 어휘·override/confirm·고아·불일치), `s1v_values.py`·`s1v_key.py`(`structure_rule_fp`), `s1v_build.py`(`loop_roles` 소비, `applied_facts`). `E/pipeline/stage_a.py`·`stage_a_report.py`(사실 로드 순서, `declared_loop_cuts`, 보고 행). `graph/CONTRACT.md`·`pipeline/CONTRACT.md` 해당 절 | 41 §1.12·§1.13, 40 §3.2-3, §9.3 | U1·U2 병합(U1 = `[u1-sp1]`·`[u1-sp1-tests]`) | 2 | D-J1~D-J7 | 41 §9의 J 행 5개(toy (a), 9회로 (d), 거부 확인, red test 먼저). 9회로 발동표: D1 = 41 §1.13 실측 집합, 나머지 7회로 무동작. FF는 ngcc만. 루프 뷰·정지·review 수의 U1 대비 변화표. 이름 전단사 불변. **사실 파일 작성은 이 단위가 아니다**: 병합 뒤 오케스트레이터가 §3.2-3 표를 실측과 대조해 쓴다 |
| **U2 대칭** | `ng-layer0-canon`의 정준 라벨링·궤도를 `E/graph/canonical_form.py`·`automorphism_orbits.py`로 옮긴다. 수동소자 무향 처리와 부호 −1 묶기. `orbit_matching_crosstab`. `E/search/orbit_ties.py`·`tie_expand.py` 갱신 | 40 §6 | U0 | 1 | D-SYa~d, R16 | 40 §10.2 대칭 행. 파일럿 R1/R2 궤도, 단자 순서 뒤집기 metamorphic |
| **U3 LUT·PDK 확장** | `E/lut/`: `vgs_for_current_density`, VS Hermite, FC 정책, `ft_curve`·`intrinsic_gain_curve`·`vdsat_curve`·`idu_curve`, `noise_params`, 잡음 LUT r1 로더, `LutMemo.from_sweep` 배선 도우미. `assets/sky130_lut_sweep.py`에 `.noise` 모드와 **mismatch 감도 모드**(Q3: `*_slope_spectre` 섭동 → DVGS 열, 새 버전 파일 `..._mismatch_r1.npz`, 공유 데이터 덮어쓰기 금지) 추가, `mismatch_dvgs` 로더·`tol_mismatch`. `E/core/pdk_decl.py`와 PDK 선언 json에 EF, mismatch slope(카드 `.model` 블록별 bin 지도 + slope 이름, pfet L < 0.5 µm `vth0_slope1` 등), poly 저항 양 추가 | 41 §4.1, §6.4-2·2b, §7.2, 40 §7.1, R25 | U0 | 1 | DEC-87·88, D-LUTc, D-NZ2, D-PF1·2, D-GB4a(분류 쪽), D-PG, D-MM1·2 | 격자점·칸 중앙 ngspice 대조(c), 감도 열 칸 중앙 섭동 대조(c), `vth0` 성분 = √2·slope(bin별)(a), 소자 쌍 MC 단위 확인(c), Ω당 면적 손계산(a) |
| **U4 sizing 보강** | `E/sizing/`: L 동치류 L 공유(θ 스키마), 미러 비 강제, S2p 기반 tol_I, DEC-95 (3) 전체 순서, W_request 고정 W, `size_and_seal_local` | 40 §3.7, 41 §5.3 | U0(② 순서 항목은 U1 인터페이스 필요) | 1 | DEC-17(θ 쪽)·32·70·95, D-GB7a~d, D-LS | IC1·IC2·IC10 test, 국소 봉인 toy |
| **U4b 미러 비 강제** | DEC-70 `matching_ratio` 전류 기저 강제 관계 I_out = ρ·I_ref. 비율 출처를 새 θ 종류로 두고, 그 θ를 아는 search 쪽(`search_domain`, `fd_jacobian`, `cone_rows`, `start_points`, `layer0_center`)과 대칭 쪽(`orbit_ties`, `current_symmetry`)을 같은 커밋에서 고친다. 상자는 멤버·기준 전류 상자에서 유도한다(상수 금지). 경위: U4가 sizing 쪽만으로는 search를 깨거나 안 쓰이는 코드가 되어 멈춤(`sizing/CONTRACT.md` 15절, 2026-10-08) | 40 §3.7, P N3.4 DEC-70 | U4, U11 | 2 | D-GB7b, DEC-70 | 미러 toy 손계산(ρ = 2, 3), 대칭 묶음 비율 1과 겹치지 않음, θ 원뿔 상한 유도 대조 |
| **U5 authoring·spec** | `E/authoring/`: `gain_budget_db_override`(배열 키), `driving_spec`, `structure_count_budget`, 잡음 metric 어휘, `noise_testbench`, 옛 이름 표 수정(`input_dc_net`·`topology_hash`·`derived`), `spice_unverifiable[]`. `E/core/units.py` 잡음 단위와 Q3·Q4 단위(`pct`, `ratio`, `v`). Q3·Q4 metric 어휘(`offset_in_sigma_mv`, `offset_excess`, `offset_sys_mv`, `mirror_ratio_sigma_pct`, `swing_out_v`, `icmr_v`, `icm_margin_v`)와 옛 이름 표(`mismatch_sigma_mv`, `mirror_ratio_error_mv`, `mismatch_sigma_v`). `assets/library/*.sizing_spec.json`에 Q5 승격·Q11 잡음 제약·**§9.2 Q3·Q4 선언**(파일럿 3.3 mV·스윙 2.4 V·icm_margin, 6회로 가드, ngcc·nmcnr ICMR, nmcnr 스윙) 반영 | 40 §3.1, §3.8-8, §9, §9.2, 41 §7.1 | U0 | 1 | FR-9, DEC-68·69·90(3), D-GB0a, D-NZ1, D-Q34 | 거부 test(옛 이름·출처 없음·`metric_unknown`), 9회로 로드, §9.2 표와 spec 대조 |
| **U6 오라클** | `tools/spice_oracle/`: C10 한계 사이클과 안정 fixture 불변, 고Q 표시, `.pz` P, 위상 펼침 N과 Z 판정, `.noise` 개루프·폐루프 SC 테스트벤치, **offset Monte-Carlo**(mismatch 블록 gauss, 입력 환산 분포)와 **스윙·ICMR `.dc` 스윕**(Q3·Q4 (8)), `ORACLE_MEASURES` 추가 | 40 §4, §10.2, 41 §7.6 | U0 | 1 | D-OR1~5, D-NZ6 | 40 §10.2 C10·offset MC·스윙 DC 스윕 행. 조건부 안정 fixture, `.noise` 손계산 저항 분압, MC 표본 수 유도 |
| **U7 metrics 이득·보고** | `E/metrics/`: `block_model`, `block_residual`, 결합 잔차 측정, `sensitivity_gate`, `ls_fields`(슬루·방향별 전류), `ls_swing`(`swing_out_v`·`icmr_v`·`icm_margin_v`), `nqs_ratio`, `offset_analysis`(`offset_in_sigma_mv`·`offset_excess`·`offset_contrib`, MNA adjoint 공유), `offset_systematic`, `mirror_ratio`(옛 `mismatch_sigma_v` 대체), `verified_by`·모델 오차 레지스트리 | 41 §2, 40 §3.8 | U1(블록 정의), U3(A_eff 감도 열) | 2 | FR-2, DEC-05·23·58·66·72·96, D-BM, D-SG, D-GB8a~c, D-OF1~3, D-MR, D-SW, D-ICM | CS·캐스코드 손계산, 단일 블록 잔차 0, offset toy 손계산·섭동 재풀이(b), 스윙·ICMR 경로 합 toy |
| **U8 metrics 잡음** | `E/metrics/noise_sources.py`, `noise_analysis.py`, 잡음 제약 행 연결 | 41 §7.3·7.4 | U3, U5 | 2 | D-NZ3·4 | 4kTR·4kTγgm 손계산(a), ngspice `.noise`(c) |
| **U9 GB4 달성가능성** | `E/metrics/achievability.py`, `curve_checks.py`, `block_gain_bound.py`, `dof_report.py`, `area_lower_bound.py`, `headroom_bound.py`(Q4 헤드룸 창 상한·유도 보고), `E/search/count_budget.py` | 41 §0, §4 | U1, U3 | 2 | FR-8, D-GB4a~f, D-NS, D-NM | 격자 직접 전수 toy(b), 불가능 스펙 exit 3, IC6 사고19, 계수 예산 결정론, follower 스택·두 극성 입력 toy 상한 |
| **U10 GB3 결합** | `E/graph/coupling_vars.py`, `column_block_map` | 40 §3.3 | U1 | 2 | D-GB3, DEC-71 (2)(7) | 9회로 매핑표, 귀속 안 된 소자 정지 |
| **U11 search 정비** | `E/search/`: SLSQP 척도화, 타입 있는 아카이브 레코드, 예산 점 풀이, `n_starts`·L-c 분지, ε 간격과 점 예산, CM 감지 저항 최소화, CM 1 dB 대체 제거, 면적 예산 출발점과 W 타당성 | 40 §3.6, §5-4, §7.1·7.2, §3.5 | U0 | 2 | D-SC, D-AC, D-BP, D-ST, D-EPS, D-CM4, D-CMR, D-AR2·3 | 1e6 행 픽스처, 왕복 비트 동일, 예산 점 1개 |
| **U12 layout 정비** | `E/layout/`: ΔA_tie, LY5 즉시 완화 제거, `matching_L_mismatch`, `ly.diffusion`, 그룹 경계 tap, 판정 축 면적에 수동소자(MIM·poly 저항) 포함 | 40 §3.9 | U3(저항 PDK 양) | 2 | D-LY1~4, R20~22 | 해시 대조, 면적 손계산 |
| **U13 출발 구간·매크로 모델** | `E/search/start_intervals.py`, `iv_*`(Q3·Q4: `iv_headroom`의 스윙·ICMR·입력 DC 예산 분할, `iv_matching_l`의 A_eff 기반 matching L 하한과 offset 가드 부하 gm/ID 상한), `macro_poles.py`, `dominant_node.py`, `eval_budget.py` | 41 §6(§6.2, §6.4-2·2a), §7.5, §5.8 | U1, U3, U9 | 3 | D-SIa~g, D-DN, D-NZ5 | 손계산 toy, 이상 VCCS 2·3극점, 절대 offset 회로에서만 L 하한 활성 |
| **U14 MOD8 수렴** | `E/convergence/`: `converge`(W_request 루프, LY7 재평가, 판정 축 재필터, K_max) | 40 §3.9 | U4, U12 | 3 | D-M8, R12 | W_request 합성 픽스처, 커널 호출 계수 |
| **U15 층 0 gain 예산** | `E/search/`: `layer0_budget`, `gain_bins`, `local_candidates`, `local_front`, `combo_dp`, `assembly`, `budget_override`. `layer0_center`는 대체되어 초기점 생성 전용이 된다 | 41 §5 | U4, U7, U9, U10, U13 | 4 | FR-4, DEC-03·10·71·73, D-L0a~i | 2블록 toy DP = 전수, 파일럿 `gain_budget_db` 출력 |
| **U16 보고·진입점·통합** | `E/report/`, `E/pipeline/`(`ng-bridge` 흡수), `tests/integration/`의 9회로 E2E·구조 표·IC7·IC11·회귀 추적 | 40 §3.9, §10 | U14, U15, U6 | 5 | D-M9·M10, D-IC, D-T, T1~T9 | 9회로 E2E, 오라클 대조 |

**J 결정(§9.3)이 다른 단위에 더하는 범위**(파일 소유는 위 표 그대로이고, 범위만 더한다):

| 단위 | 더하는 범위 | 설계 절 | 확인 행 |
|---|---|---|---|
| U4 | SP-2 (c): 입력 DC 대기 회로의 W4 입력 공통모드 y_icm 범위 = 입력 창(봉인 시점 경계) | 41 §4.6 | D-J5 |
| U5 | metric 어휘 `ff_gm_ratio`(단위 ratio). sf_pushpull spec에 `icm_margin_v >= 0`(`user_spec` J-E) | 40 §3.8-8, §9.2 | D-J2, D-J5 |
| U7 | FF 경로 기여, 분해 합성값 A_decomp 잔차, `ss.ff_contrib`, `ff_gm_ratio` 값. `icm_margin_v`를 y_icm에서 계산, `required_input_cm_v` | 41 §1.12.2-4·5, §2, 40 §3.8-8 | D-J2, D-J5 |
| U9 | 주경로 블록만 A_i,max. FF 상한을 더한 Σ 판정. `icmr_window_short_l_bin` 경고, `buffer_window_report` | 41 §4.3, §4.6 | D-J2, D-J5 |
| U13 | FF 묶음 출발값(G_ff = r_ff · gm_in(B_b), r_ff = 1) | 41 §6.5 | D-J2 |
| U15 | bin·조합·`gain_budget_db`는 주경로 블록만 | 41 §5.1 | D-J2 |
| U6 | 확인 항목: 보상 내부 루프 회로(ngcc·nmcnr)의 전체 PM 판정에 개루프 P = 0(`.pz`)이 들어가는지 | 41 §1.12.3, 40 §4 Q10 | D-J3 |

**웨이브 계획**(동시 6개 이하)

| 웨이브 | 단위 | 비고 |
|---|---|---|
| 1 | U1, U2, U3, U4, U5, U6 | 서로 소유 파일이 겹치지 않는다 |
| 2 | U1b, U7, U8, U9, U10, U11, U12 | 각 단위는 자기 선행 단위가 병합되는 대로 시작한다. U1b는 U1과 같은 `E/graph/` 파일을 고치므로 U1·U2 병합 뒤에 시작한다. U7·U9·U10은 블록 정의가 바뀌므로 U1b 인터페이스(41 §8, 주경로 블록·`feedforward_cells`)로 toy test를 쓰고, 실제 회로 test는 U1b 병합 뒤 켠다. 동시 6개 상한 때문에 U1b가 먼저 들어가고 U12가 한 칸 밀린다 |
| 3 | U13, U14 | -- |
| 4 | U15 | -- |
| 5 | U16, 그 뒤 gap 분석(`42` 기준표 재측정) | J 공동분석(Q7)은 `[u1-sp1]` 9회로 표로 진행해 2026-10-08에 결정됐다(§9.3). 그 구현이 U1b다 |

**임계 경로**: U1 → U1b → U9 → U13 → U15 → U16. U9가 주경로 블록 정의를 읽으므로 U1b가 임계 경로에 들어간다. U1(SP1)이 가장 크므로, 하위 파일 단위로 나눠 같은 웨이브 안에서 순차로 커밋한다.
