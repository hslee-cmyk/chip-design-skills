---
template: design
version: 1.0
plan_version: 6.0
---

# gain-budget-gmid-sizing -- 40-engine Design Document (새 엔진 `gmid_engine`, 색인·아키텍처)

> **Summary**: 새 gm/ID 사이징 엔진(`skills/analog-gmid-design/gmid_engine/`)의 설계 정본이다. 계획서 N3.1 흐름 GB0~GB9를 패키지·파일에 대응시키고, 단계마다 알고리즘·입출력·불변식·실패 코드·as-built 상태를 적는다. 계획서가 요구하고 실행 로드맵에서 빠졌던 gain-budget 흐름(FR-1·FR-2·FR-4·FR-8)은 `41-gain-budget`에서 전부 설계한다. gap 분석 기준표는 `42-gap-checklist`다.
>
> **Project**: chip-design-skills (analog-gmid-design skill) · **Author**: Claude Code
> **Date**: 2026-10-08 · **Status**: v1.0 초안
> **Planning Doc**: [gain-budget-gmid-sizing.plan.md](../../01-plan/features/gain-budget-gmid-sizing.plan.md) v6.0
> **as-built 기준**: master `f0f0fb8`, 그리고 미병합 브랜치 `ng-cmfb-pm`(6a6e4c7), `ng-oracle-early`(d56ba66), `ng-perf-sizing`(f8d04ac), `ng-tolv-cache`(674a6a1), `ng-layer0-canon`(0c5dc20), `ng-area-budget`(538eeab), `worktree-agent-a90dfb25fa6fe9f04`(7090b9f, LUT r2), `ng-bridge`(d529ea5)

진행 순서는 bkit PDCA다: 이 design → 구현 → gap 분석(`42-gap-checklist`).

## 문서 구성

| 파일 | 내용 |
|---|---|
| `40-engine`(이 문서) | §1 범위·원칙, §2 아키텍처(흐름·상태 층·패키지 API), §3 단계별 설계 GB0~GB9(gain-budget 외), §4 SPICE 오라클, §5 CM(CMFB) 루프, §6 대칭, §7 면적 예산·성능, §8 승인 없이 축소된 범위, §9 사용자 결정이 필요한 질문 |
| `41-gain-budget` | FR-1(SP1 stage 유도), FR-2(블록 gain 모델과 MNA 잔차), FR-3 연계, FR-8(탐색 전 달성 불가), FR-4(층 0 gain 예산 조합 front와 `gain_budget_db`), 스펙에서 gm/ID·L 출발값 유도 |
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
| authoring → graph·search | `SizingSpec`(제약·목표·θ 범위·설정), **신규 필드** `gain_budget_db_override`, `driving_spec`, `symmetry_untie`, `cm_sense_elements`[ng-cmfb-pm], `element_values.*.measurement_load`[ng-area-budget] | spec 로더 | PART |
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
| `gain_budget_db_override` | `{<블록 키>: {value_db, source}}`. 블록 키 = 그 블록 출력노드 넷 이름(topology 데이터) | 41 §5.6 |
| `driving_spec` | `{slew_rate_v_per_s?, load_peak_amp?, load_dc_amp?, source}` | §3.8 `ls` |
| `symmetry_untie` | `[{devices: [...], source}]` | §6 |
| `cm_sense_elements` | `[<요소 이름>]` + `source: user_spec` | §5 `[ng-cmfb-pm]` |
| `element_values.<el>.measurement_load` | bool | §7.1 `[ng-area-budget]` |

| 항목 | 상태 | 증거 |
|---|---|---|
| topology 게이트(supply_nets·숨은 레일·manifest·태그 키) | OK | `E/authoring/rails.py`, `hidden_rails.py:16`, `source_manifest.py:19`, `topology_schema.py:22` |
| gate 전용 바이어스 넷 | DEV(승인됨): `ports` role 대신 최상위 키 `bias_inputs`(사용자 Q9 (i)). 계획서 DEC-94 문구를 고쳐야 한다 | `E/authoring/bias_inputs.py:20` |
| 옛 이름 거부 | DEV: topology에는 `legacy_name` 표가 없다(닫힌 어휘로 대신 거부). spec 옛 이름 표가 정본 이름 `input_dc_net`·`topology_hash`·`derived`를 거부한다. topology `ports.direction`을 필수로 받는다(N3.16에서는 흡수 대상) | `E/authoring/_spec_fields.py:28-33`, `authoring/CONTRACT.md:151-152,201` |
| `gain_budget_db_override`·`driving_spec` | MISS: 로더가 `unknown_key`로 거부한다 | `authoring/SPEC_CONTRACT.md:226-228` |
| `spice_unverifiable[]` 사전 출력(DEC-90 (3)) | MISS | -- |
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
| `structure.json` ratified 로드, declared/ratified 전이 | MISS | -- |

**설계 보완**:
1. L 동치류는 GB1이 `derived`로 낸다. 증거는 LR1 규칙(같은 gate 넷·같은 source 넷·같은 kind인 `equal_vgs` 멤버)이다. θ 스키마는 동치류당 L 변수 하나를 둔다. 주인 선택은 DEC-17 순서를 따르되, 'gain 제약 전달 뷰의 첫 gain stage에 붙은 tail' 판정은 GB2 S1v가 생긴 뒤에 확정한다.
2. `structure.json` 로더를 둔다. `topology_hash`·`rule_hash`가 S0와 맞을 때만 ratified 사실을 적용하고, 다르면 해당 사실을 `review_needed`로 되돌린다(P N3.3 전이 표).

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

**단일단(`compensation: null`)**: gm_1 ≥ 2π·`gbw_target_hz`·C_out,total을 θ 제약으로 둔다(U-12 기본안). C_out,total = `ss.node_c_farad`(출력노드) + 부하 요소 값이다. 이 행은 U-12가 확정되기 전에는 '보고만' 한다.

| 항목 | 상태 | 증거 |
|---|---|---|
| 보상 수동소자 θ 연속 성분 + MNA 판정 | OK | `metrics/CONTRACT.md:555-567` |
| Rz = 1/Σgm 구조 규칙 | OK(J7 ratify 대기) | `E/sizing/theta_schema.py:15-25,79,144`, `E/metrics/ss_evaluate.py:48` |
| `gm_req` 1-D 근, `comp_approx_gap` | MISS | `E/search/find_front.py:45-48`('범위 밖') |
| 극점 노드 목록에서 후보 집합 유도 | MISS(SP1이 없어서) | -- |
| 단일단 gm_1 규칙(U-12) | MISS(계획상 확정 대기) | -- |

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

| 항목 | 상태 | 증거 |
|---|---|---|
| ε 두 방향·비지배·L-a/L-b | OK | `E/search/eps_sweep.py:1-14`, `pareto.py:31`, `slsqp_outer.py:49`, `l_bin_search.py:1-12` |
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
5. **W4 초기값**: 층 0이 배분한 기둥 VDS를 쓴다(41 §5.4).

| 항목 | 상태 | 증거 |
|---|---|---|
| W0~W4 writer 계획 | OK(W3는 9회로 모두 0. CI-15·18 대기) | `E/sizing/writer_plan.py` |
| SCC 고정점·K_max·NONCONVERGENT | OK(+ GS 실패 시 감쇠 Newton, `[ng-perf-sizing]` Brent) | `E/sizing/fixed_point.py:21`, `scc_newton.py:33` |
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
   - 스윙·ICMR 한계는 P N3.8 경로 합으로 계산한다.
   - `driving_spec`이 선언되면 이 값들로 제약 행을 만든다.
4. **보고 metric**:
   - `nqs_ratio` = `ugf_ss_hz` / 신호 경로 소자 최소 f_T. f_T는 봉인 `ss`의 gm/(2π·cgg)이다.
   - `mismatch_sigma_v`는 Pelgrom 식으로 계산한다. 계수는 §8 R17 선행 조건이 풀린 뒤에 쓸 수 있다.
5. **전력 축**: DEC-78은 '레일 공급 전류의 합'이고, as-built는 Σ V·I(`power_dc_w`)다. 두 값은 레일 전압이 다르면 front 순서가 달라질 수 있다. 어느 쪽을 쓸지는 §8 R24(사용자). 어느 쪽이든 '기둥마다 전류를 한 번' 센 값과의 대조를 매 실행 기록하고, 어긋나면 `review_needed`로 둔다.
6. **`verified_by`·모델 오차**: 레지스트리 항목에 `verified_by`·`model_error_ref`를 두고, 오라클 대조 결과(DEC-72)를 `derived.model_error_<metric>`에 쓴다.

| 항목 | 상태 | 증거 |
|---|---|---|
| MNA(ω 무관 조립 + ω별 풀이, gmb, 접합 용량, pencil) | OK | `E/metrics/mna_build.py:47`, `mna_solve.py:42`, `stamp_mos.py`, `junction_cap.py`, `pencil_roots.py` |
| `gain_ss_db`, `ugf`, `gbw`, `pm_ss_deg`(β 또는 β=1), ratio, `parasitic_pm_ss_deg` | OK | `metrics/CONTRACT.md:173-235` |
| `rout_ss_ohm` | PART(블록 테브난 잔차 없음) | `metrics/CONTRACT.md:205-213` |
| 블록 국소 모델·잔차, 감도 게이트 | MISS | `metrics/CONTRACT.md:13-14` |
| `ls`·스윙·ICMR·nqs·mismatch | MISS | `metrics/CONTRACT.md:14` |
| 전력 축 | DEV(Σ V·I, 기둥 대조 없음) | `E/search/objectives.py:9` |
| 면적 탐색 축 | PART(master는 수동소자 단위 면적 None. MIM·측정 부하 제외는 `[ng-area-budget]`) | `E/metrics/dc_metrics.py:18-19,80-83` |
| `verified_by`, `spice_unverifiable` | MISS | `metrics/CONTRACT.md:246,424` |

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

1. 걸음 상한·관찰 창·조기 unstable(분해능을 넘는 엄격 증가 g↑)·연장 상한 n·`wall_s_per_window` 유도·시간 초과와 치명 오류 = `failed`는 d56ba66 그대로다.
2. **지속 진동 = 불안정(한계 사이클)**(사용자 결정 2026-10-08 4번). 창 진폭 M_j가 다음을 모두 만족하면 `unstable`(사유 `limit_cycle`)이다.
   - 바닥 floor'를 분해능 밖으로 넘는다: M_j·(1 − reltol) > floor'.
   - 연속 창 사이 변화가 분해능 안이다: |M_j − M_{j−1}| ≤ (M_j + M_{j−1})·reltol + floor'.
   - 감소 판정 g↓가 성립하지 않는다.
   이 조건이 j ≥ 3인 첫 창에서 두 번 연속(j−1, j) 성립하면 조기 종결한다. 창 수 3은 개정본 조기 규칙과 같은 정의를 재사용한다(새 상수가 아니다).
3. 판정은 '분해능 안의 같음 → undetermined'(d56ba66 L48-54)를 대체한다. 그래서 d56ba66의 '일정 진폭 지속 진동은 undetermined 유지(사용자 승인)' 문구와 `test_sustained_oscillation_undetermined_incomplete` 기대값은 사용자 결정 2026-10-08 4번으로 바뀐다. 기대값 갱신은 test 작성 주체가 한다.
4. `unstable`(limit_cycle 포함)은 폐루프 불합격(FAIL)이다(사용자 결정 2026-10-08 B '불안정은 계속 불합격').
5. **엔진과 오라클의 대칭**: 엔진은 개루프 RHP 극점을 위반 행으로 다룬다. 오라클은 `pm_undefined`를 N/A→INCOMPLETE로 다룬다. 사용자 결정 A('RHP 극점으로 인한 정의 불가는 불안정(실패)')에 맞춰 오라클도 FAIL로 둔다.

| 항목 | 상태 | 증거 |
|---|---|---|
| free/forced, 포화, off_current, CMRR/PSRR, 접합 기하 | OK | `tools/spice_oracle/README.md:60-69,114-117,146-147,300-318` |
| C10 조기 종결 계약 | PART(계약만 있고 master 미반영) | `[ng-oracle-early]` 계약 L14-81 |
| 지속 진동 = unstable | DEV: 계약과 test가 undetermined로 고정되어 있다 | 계약 L42-54, `tools/spice_oracle/tests/test_oracle_c10_stability.py:710` |
| RHP → FAIL 대칭 | DEV(오라클은 INCOMPLETE) | `[ng-cmfb-pm]` README '판정' |
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
4. **위반 행의 척도**: c = 20·log10|T_cm(0)|/s. s는 그 metric의 분해능(`MetricResult.resolution`)이다. 분해능이 없을 때 쓰는 1 dB 대체값(as-built)은 상수이므로 지운다(EP-4). 분해능이 없으면 그 행을 '판정 보류'로 두고 front를 '추정'으로 표시한다.
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
4. **해제**: spec `symmetry_untie: [{devices, source}]`에 적힌 소자는 궤도에서 빼고 따로 변수를 둔다. 의도적 비대칭 사이징에 쓴다.
5. **불변식**:
   - 궤도는 matching 레코드(`diff_pair`·`branch_symmetric`·mirror whole)와 맞아야 한다. 어긋나면 `review_needed`다.
   - 이름을 전단사로 바꾼 입력은 비트 단위로 같은 결과(front 정규화 해시)를 낸다.
   - 1-WL 결과와 정준형이 다른 회로는 그 목록을 보고한다.

| 항목 | 상태 | 증거 |
|---|---|---|
| 1-WL 색 정제 | OK(순서 tie-break 용도) | `E/sizing/struct_colour.py:1-15` |
| 정준 Halton 차원 순서 | PART `[ng-layer0-canon]` | `E/search/canonical_order.py` |
| 완전 정준형·궤도·θ 묶기·해제 | MISS | `search/CONTRACT.md` 3.23 (4) '열린 항목' |

---

## 7. 면적 예산·척도화·성능

### 7.1 면적 예산(사용자 결정 11, 2026-10-08)

**규칙**:
- 회로별 spec 제약 `area_search_m2 <= 예산`을 둔다. 값은 결정 11의 표다.
- 면적 = MOS 게이트 면적 Σ W·L + 보상·내부 커패시터 면적이다.
- 커패시터 면적 = 값 / `mim_cap_density_f_per_m2`다. PDK 선언 값은 `camimc`이고, 출처는 `C:/pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice`(2.00e-15 F/µm² = 2.0e-3 F/m², sha256 고정)다.
- spec `element_values.<el>.measurement_load: true`로 표시한 측정 부하(CL·CL1·CL2·RL)는 면적에서 뺀다. 이름이 아니라 선언으로 가른다.
- 저항 단위 면적은 선언이 없으면 `passive_area_undeclared`로 보고한다.
- 제약 행은 c = (v − A)/b_A다(판정 단위).

**S-3b 닫힘**: 예산이 선언되면 전류 상자 상한 I_max = IDu_max·A_budget/L_lo²로 둔다. 근거는 W·L = I·L²/IDu ≤ A_budget이다.

**설계가 더하는 것**:
1. **예산을 지키는 출발점**: 41 §6.4의 면적 상한(L ≤ √(A_budget·IDu/I), W ≤ A_budget/L)으로 출발 구간을 자른다. 층 0 국소 문제에도 면적 bin 상한을 예산으로 둔다.
2. **소자별 W 타당성**: 레이아웃 전에 W ≤ A_budget/L_min을 상자 제약으로 둔다. 예산이 없으면 S-3b 잠정 상한을 쓰되 보고에 '잠정'을 붙인다. W가 수 mm인 시작점은 이 제약에서 거부된다.
3. **면적 달성가능성**(GB4 확장, 41 §4.3): 면적 하한 A_lb = Σ_k I_k,min·L_k,min²/IDu_k,max가 예산보다 크면 탐색 전에 INFEASIBLE_TARGET(사유 `area_budget_below_lower_bound`)으로 정지한다. I_k,min은 gm 요구(41 §6.3)에서 나온다.
4. **front를 잃은 4회로의 원인 보고**: B = 120 s 실측에서 folded·ngcc·nmcnr·pushpull은 front 0이었고, sf_pushpull·current_reuse는 시작점이 0이었다. 회로마다 다음을 결과 JSON에 쓴다.
   - (i) A_lb 대비 예산
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
| 1변수 풀이 | Brent `bracket_root` + 입력 재사용 memo + 평가 안 tol_V 셀 재사용 | OK `[ng-perf-sizing]` |
| core 성능 2~5 | memo 키, 레코드 지문 보관, 투영 지문, 열 키 캐시 | OK(master 병합) |
| 블록 국소 모델 | 블록 노드 부분 MNA를 봉인 스냅샷당 한 번 조립하고, ω=0 극한 풀이만 한다(41 §2.3) | MISS |
| GB4 상한표·출발 구간 | S0당 한 번(평가 커널 컨텍스트) | MISS |
| LUT r2 데이터, 검증 중점 L (0.165, 0.85, 1.75, 3.25) | OK `[worktree-agent-a90df…]`(미병합, master보다 45커밋 뒤) | -- |

---

## 8. 승인 없이 축소된 범위 (승인하거나 되돌릴 대상)

아래 표는 로드맵(`_drafts/engine/ROADMAP.md`, 이하 R)이나 초안·CONTRACT가 계획 요구를 줄이거나 미룬 곳이다. **결정은 사용자 몫이다.** 권고는 이 design의 의견일 뿐이다. 'D18 철회'(사용자 2026-10-08)로 이미 되돌리기가 정해진 항목은 그렇게 표시했다.

| # | 축소 내용 | 출처 | 계획 근거 | 상태 | 권고 |
|---|---|---|---|---|---|
| R1 | 층 0을 최소형(시작점 하나)으로. 블록별 gain bin front·조합 DP·`gain_budget_db` 출력 없음 | R §4 D18, R §0.2, `search/CONTRACT.md:26-31` | FR-4, DEC-03·71·73·77 | **사용자가 철회(2026-10-08)** | 41 §5대로 복원 |
| R2 | GB3(결합 변수 y) 범위 밖 | R §0.2 행 32, D18 | GB3, DEC-71 (7) | 미결 | 복원: 층 0 조립의 입력(§3.3). 내층 DP·중층 좌표강하는 DEC-73대로 기본 꺼짐 유지 |
| R3 | GB4를 'INFEASIBLE_TARGET만'으로 축소, DOF·수치 rank 범위 밖 | R §0.2 행 33, K6. 계획 N6.1 단위 7('GB4 축소')에도 반영됨 | FR-8, GB4, IC6 | 미결 | 구조 DOF와 수치 rank 복원(표본 수 = `dof_rank_sample_count`, 41 §4.4) |
| R4 | U-49 기본안(층 0 최소형, gain bin front·GB3 범위 밖)이 계획서 안에 있다 | P N7.2 U-49 | FR-4와 긴장 | 미결(계획서 안의 대기 결정) | 2026-10-08 지시로 U-49를 '복원'으로 닫고 계획서를 정정 |
| R5 | 블록 국소 모델·MNA 잔차·감도 게이트 범위 밖 | `metrics/CONTRACT.md:13-14`, 초안 M15:191, L7a:261 | FR-2, DEC-05·66, N3.8 | 미결 | 복원(41 §2, §3.8) |
| R6 | SP1(셀·0-1 BFS·stage·루프 (0)~(4)·끊는 점·R(u)·DEC-81) 연기, declared 대조 연기 | 초안 U25:196·201·133, R N5~N7 미착수 | FR-1, GB2, DEC-43·57·59·63·65·81 | 미결 | 복원(41 §1) |
| R7 | `rule_branch_coverage.json`과 검증 발동 0 분기 정지 없음 | graph CONTRACT | DEC-59 | 미결 | 복원(41 §1.9) |
| R8 | GB5 `gm_req`·`comp_approx_gap` 범위 밖 | `find_front.py:45-48` | DEC-92 (1)(2) | 미결 | 복원(§3.5) |
| R9 | `ls`(슬루·방향별 전류)·스윙·ICMR·`nqs_ratio`·`mismatch_sigma_v` 범위 밖 | `metrics/CONTRACT.md:14` | DEC-58·65·96, N3.8 | 미결 | 복원(§3.8) |
| R10 | spec 로더가 `gain_budget_db_override`·`driving_spec`을 거부 | `SPEC_CONTRACT.md:226-228`, R D5('N3.15 축소') | GB0, DEC-03, DEC-58 | 미결 | 복원(§3.1) |
| R11 | 예산 점 풀이 미작성, `n_starts`·x0 미작성 | `search/CONTRACT.md:535-537,591` | DEC-77, U-13, N3.5 | 미결 | 복원(§3.6) |
| R12 | MOD8 루프·LY7 재평가·판정 축 재필터 미구현(`pending_wiring`) | `layout/CONTRACT.md` 4.14, `search` S-14 | DEC-79 (b), DEC-84, LY3·LY7, 사용자 12번 (나) | 계획은 범위 안 | 구현(§3.9) |
| R13 | L 동치류 L 공유 사실상 꺼짐(`l_class` proposed) | `graph/CONTRACT.md:220` | DEC-17, LR1 | 미결 | 복원(§3.2) |
| R14 | 미러 비율 전류 강제 없음, DEC-95 (3) ratified·② 없음, tol_I 격자 최대 gm | `sizing/CONTRACT.md:276,741,766` | DEC-70, DEC-95, N3.6 | 미결 | 복원(§3.7) |
| R15 | 뷰별 교류접지(바이어스 종속 넷) U5로 연기. 차동쌍 '신호 gate 정확히 2' 조건 빠짐 | `graph/CONTRACT.md:491,538`, JU4:131 | SP1-1 (4), DEC-93 (1) | 미결 | 복원(41 §1.2) |
| R16 | 대칭 θ 묶기 열린 항목 | `search/CONTRACT.md` 3.23 (4) | 사용자 2026-10-08 대칭 결정 | 미결 | 구현(§6) |
| R17 | Pelgrom 계수 선언 없음 → mismatch 보고·matching L 하한 불가 | core 조사 | DEC-96 (2), N3.16 | 선행 조건 | PDK `*__mismatch.corner.spice`의 `vth0_slope`·`toxe_slope` 계열에서 A_VT·A_β를 유도하는 식과 단위 확인을 MOD1/`core` PDK 선언에 둠(§9 Q2) |
| R18 | C10: 지속 진동을 undetermined로 유지(계약에 '사용자 승인'으로 기록) | `[ng-oracle-early]` 계약 L42-54 | 사용자 결정 2026-10-08 4번 | 사용자 결정과 모순 | 사용자 결정대로 되돌림(§4) |
| R19 | 오라클이 RHP 극점을 INCOMPLETE로 판정 | `[ng-cmfb-pm]` README | 사용자 결정 A | 미결 | FAIL로 맞춤(§4) |
| R20 | ΔA_tie = grid² | `E/layout/floorplan.py:83` | DEC-79, DEC-95 (2) | 미결 | 계획 식으로 수정 |
| R21 | LY5 `W_adjustable=False` 즉시 완화 | `layout/CONTRACT.md:217,306-311` | LY5 마지막 문장 | 미결 | 제거 |
| R22 | LY8 `ly.diffusion` 없음, 판정 축 면적에 수동소자 없음 | `E/layout/_ly_fields.py` | DEC-89 (5), DEC-91 (2), DEC-79 | 미결 | 구현(§3.9) |
| R23 | `verified_by`·모델 오차 레지스트리, `spice_unverifiable` 없음 | `metrics/CONTRACT.md:246,424` | DEC-72, DEC-90 (3), N3.8 | 미결 | 구현(§3.8) |
| R24 | 전력 축 = Σ V·I(`power_dc_w`). DEC-78은 공급 전류 합 | `E/search/objectives.py:9`, `metrics/CONTRACT.md:544,627` | DEC-78, U-10 | 정의 차이 | 사용자 결정(§9 Q6) |
| R25 | LUT: GMBS 열이 있는데 VS 축 선형, FC 위반 칸 선형 폴백, `vgs_for_current_density` 없음, bin 소속을 메타 대신 식으로 판정 | `lut/CONTRACT.md` 1.4, 4.0.1, 4.2 | DEC-87, DEC-88, LR3 | 미결 | `vgs_for_current_density`와 VS Hermite 구현. bin 소속은 실측 384/384 일치 근거로 식 유지를 제안하되 계획 LR3 정정이 필요(사용자 확인) |
| R26 | 새 test 체계의 `contracts/`·`regression/`·`oracles/`·`perf/` 폴더 없음 | `E/tests/` | N3.11, N6.2 T9, IC1~IC11 | 미결 | 단위별로 작성 |
| R27 | 슬루·정착은 SPICE 기록만, 잡음 경로 없음 | 초안 SF:209, M15:43 | DEC-90 (2), DEC-96 (3) | **사용자 승인됨**(Q5 (ii), "잡음·왜곡 스펙은 없어") | 유지. 잡음 경로는 설계만 두고 비활성(41 §6.3) |
| R28 | 정밀 경로(내층 DP·중층)·전역 샘플·bisection 기본 비활성 | 초안 M6:299 | DEC-73·75 | **계획 승인됨**(기본 비활성) | 유지 |

---

## 9. 사용자 결정이 필요한 질문

spec 값·회로 해석·범위만 남긴다. 알고리즘 선택은 이 design이 정했다.

| # | 질문 | 왜 사용자 몫인가 | 막는 것 |
|---|---|---|---|
| Q1 | §8 R2~R26 각 행: 복원 / 승인(축소 유지) 중 어느 쪽인가. 특히 R3(DOF 수치 rank), R4(U-49 닫기), R25(LR3 bin 소속 규칙 정정) | 범위 | 해당 구현 |
| Q2 | Pelgrom 계수 출처로 PDK `sky130_fd_pr__{n,p}fet_01v8__mismatch.corner.spice`(slope 파라미터, 체크아웃 f62031a1)를 쓰는 데 동의하는가. 유도식과 단위는 엔진이 계산하고 출처를 기록한다 | PDK 출처 채택 | matching L 하한(41 §6.4), `mismatch_sigma_v` |
| Q3 | 오프셋·미러비 오차 스펙 값(파일럿 `mismatch_sigma_mv ≤ 5`는 U-17 pending). 다른 8회로에도 둘 것인가 | spec 값 | matching L 하한 활성 |
| Q4 | 출력 스윙·ICMR 스펙 값(ngcc `icmr_v ≥ 0.6 V` 외에는 선언이 없다) | spec 값 | 헤드룸 gm/ID 하한의 스윙 몫(41 §6.2) |
| Q5 | gain 제약이 없는 5회로(common_gate, folded, ngcc, nmcnr, pushpull)의 gain 값과 GBW·PM이 없는 회로의 값(U-44) | spec 값 | 그 회로의 gain 예산·속도 상한은 비활성(41 §5.1) |
| Q6 | 전력 목적 축: DEC-78 '레일 공급 전류 합'(U-10 확정)인가, as-built Σ V·I인가. 3레일 회로에서 front 순서가 달라질 수 있다 | 목적 축 정의(사용자 확정 사항) | §3.8 |
| Q7 | SP1 유도 뒤 J 공동분석: J2~J13, J12-a~i, 6a 열린 항목 ⑮(J 항목이 없는 DC 역할 그룹 둘) | 회로 해석 | GB2 `review_needed` 해소 → 탐색 |
| Q8 | 7.1의 진단 뒤에도 예산 안에 해가 없는 회로가 남으면 그 회로의 면적 예산을 바꿀 것인가 | spec 값 | 그 회로 합격 |
