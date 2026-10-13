---
template: design
version: 1.9
plan_version: 6.8
---

# gain-budget-gmid-sizing -- 40-engine Design Document (새 엔진 `gmid_engine`, 색인·아키텍처)

> **Summary**: 새 gm/ID 사이징 엔진(`skills/analog-gmid-design/gmid_engine/`)의 설계 정본이다. 계획서 N3.1 흐름 GB0~GB9를 패키지·파일에 대응시키고, 단계마다 알고리즘·입출력·불변식·실패 코드·as-built 상태를 적는다. 계획서가 요구하고 실행 로드맵에서 빠졌던 gain-budget 흐름(FR-1·FR-2·FR-4·FR-8)은 `41-gain-budget`에서 전부 설계한다. gap 분석 기준표는 `42-gap-checklist`다.
>
> **Project**: chip-design-skills (analog-gmid-design skill) · **Author**: Claude Code
> **Date**: 2026-10-13 · **Status**: v1.9 -- 사용자 결정 2026-10-13 "1은 권고, 2도 권고, 3도 권고대로" (3)과 "①, ②, ③ 권고대로 진행해" ① 반영: §10.5 A' 판정 기준 신설(판정자 ngspice·독립 대조군 AI 손분석·피검 엔진 시작점·front, 판정 규칙, U17 단계 ② 완료 조건), §11 U17 ② 행 test 열에 완료 조건 인용. 결정 밖 세부는 계획 U-76 기본안(사용자 변경 가능): fail-closed, 둘 다 실패 = 판정 불능, 시작점 판정 T4-pre, 미측정 제약 행 제외·목록, held-out 개발 전환, A' 문서 위치·front 비적용. 계획 v6.8 DEC-98·U-75·U-76. 경위는 history.
>
> v1.8.2 -- 사용자 결정 2026-10-13 "1은 권고"(d/s 비트 동일 범위 (라))와 U17 ①-a·①-c·①-d 실측 정정 반영: §6-8 D-2·D-3·§3.10.11 U-62·§10.2 -- topology d/s 표기 = 물리 방향 선언(사용자만 수정하는 정본), d/s 표기 맞바꿈에 대해 대칭 결과(궤도·정준 위치·`dc_colour`)는 비트 동일, 전류 부호는 표기 기준 방향 변환 뒤 동일, 사이징 결과(writer 계획·θ 스키마·ties·front)는 선언 방향을 따르고 틀린 선언은 봉인 7이 거부(`no_root_in_window`). 정정(결정 아님): §2.4.8 `dc_colour` 소유자 = graph 대칭 블록 `s1_symmetry`, §6-8 D-1 예시 toy 교체(완전 차동 직렬 가지 + 출력 사이 R1), §2.4.10 허용 모듈에 `core/snapshot_codec.py`, §2.4.3 U-68 정리 = 프로세스당 첫 실제 쓰기 1회·환경 변수 `GMID_S0_SNAPSHOT_DIR`, §2.4.4 분할 대상에 GB5 `passive_values`(단계 ② 이월 기록). 경위는 history.
>
> v1.8.1 -- U17 ①-d·①-e 실측에 문구를 맞춘 정정(사용자 결정 변경 아님): §6-3·§6-8·§10.2 (전류 묶음 수, 탐색 θ 변수 수) 정의를 `len(SearchDomain.ties)`(전체 묶음 수)·`len(SearchDomain.variables)`로(파일럿 29/38, 그중 전류 묶음 7), §6-3 열 순서 방향(자유 열 선택에서 비자명 궤도 우선 = 열 정렬 키에서는 비자명 궤도 원소를 뒤로), §6-5·§10.2 review 기록 코드 `diff_pair_orbit_split`, §2.3·§3.9 `LayoutResult` 칸 문구 → 설계점 스냅샷 `ly_*` 필드·`layout_outputs(snapshot)`. 경위는 history.
>
> v1.8 -- 사용자 결정 2026-10-12 다섯 건과 구현·검증 실측 정정 반영: §6-5 diff_pair review (나')("나'로 진행해"), §3.2-3 sf `drive_kind` 사실 없음·파일럿 `rule_hash` 재기록("1, 가로 해"·"2번 승인."), §6-3·§6-8 전류 기저 열 순서 규칙("3번 권고대로"), §2.4.8·§11 U16 `layout_outputs`("4번 권고대로"), §6-8 `tied_current_box_empty`, §2.4.3 `s0_snapshot` 보고서 키·PDK 선언 필수 인자·U-68 재현 판정, §2.4.8·§2.4.12 Q7 측정 완료·Q8 열림(`constraint_rows` ②로 이월), §2.4.9·§11 `test_g10_second_run_s0_zero` ②로, §10.2 test 3행. 경위는 history.
>
> v1.7 -- `budget_ref` 폐지(사용자 결정 2026-10-12 "다로 해"): `budget_ref` 엣지·concept를 만들지 않는다. 옛 `budget_reference_device`의 역할은 S1 레일-레일 기둥(DEC-71 (1), `E/graph/columns.py`)이 흡수한다. §3.2 `budget_ref` 문단, §3.7-8 폐기(노드 변수 writer = 쓰기 계획 규칙)와 구현 단위 측정 의무, §9.4 J8. 직전 안("가로 해"의 구조 유도 규칙, 열린 질문 BR-1·BR-2)은 이 결정으로 대체·소멸.
>
> v1.6 -- **v1.6 graph 정본 개정 (사용자 결정 2026-10-12), 사용자 승인(2026-10-12 "design 승인")**. 사용자 결정 2026-10-12 "1~4까지 새로고친 네 제안대로 해"(graph 단일 정본 + 계산 중복 제거)와 "G는 승인"(G-5·G-7·G-8·G-9·G-10)을 설계로 옮겼다.
> - §2.4 신설: graph 밖 허용 저장소 넷, S0 수준 층 필드와 디스크 영속화, 이식(graft)과 분할 계산 블록, S3 메모리 색인·스냅샷 보존, LUT memo 순수성·인스턴스 하나·상한 식, 값 사본 제거, 필드 소유표, G-10 계수·test, G-8 강제 장치, 열린 질문 Q1~Q7
> - §1.2 EP-2, §2.2 상태 층 표, §2.3 API, §3.7-3 tol_I, §7.3 성능·캐시 표, §11 단위 U17(3단계) 갱신. 42에 D-GR1~D-GR15 추가
> - 사용자 결정 2026-10-12 "P-1~P-15까지 권고대로 고쳐"(사용자 승인(2026-10-12 P)): §3.10 신설(P-2·P-3·P-6·P-7·P-10·P-11·P-12·P-13), §3.1 옛 이름·포트(P-4), §3.6 DEC-88 행(P-7), §3.9 MOD8 열린 항목 닫음(P-6), §10.3a DF 재발 금지 표(P-8). 42에 D-P2~D-P13 추가, DEC-22 행 정정
> - 계산값 재사용 확인 추가(사용자 지시 2026-10-12 "coding시에 계산값 재사용원칙도 준수되었는지 확인하는 과정을 넣고 이 확인내용을 항상 보고해"): §10.4·§11 공통 완료 조건, 단위 보고 필드
> - design 승인(사용자 승인(2026-10-12 "design 승인")): 승인 표시, §10.4·§11 공통 완료 조건에 graph 단일 정본 확인·gap 분석 단계 추가
> - U-04 결정(사용자 결정 2026-10-12 "U-04 권고대로"): §3.1 spec origin 행
> - U-51 결정(사용자 결정 2026-10-12 "U-51은 (나)로"): §3.6 외층 보상 단 폴백, §3.10.8·§3.10.10
> - U-71 결정(사용자 결정 2026-10-12 "U-71승인"): §3.10.3 (c)
> - K-2·GQ1·GQ3·GQ4·U-14·U-20·U-32·U-45 결정(사용자 결정 2026-10-12 "K-2 권고대로, GQ1/GQ3/GQ4, U-14,U-20,U-32,U-45 권고대로"): §2.4.5 Q4, §2.4.12 Q1·Q4·Q7, §3.10.8 U-20, §3.10.10
> - U-67 결정(사용자 결정 2026-10-12 "U-67은 (나)로"): §3.10.8 I-A13, §3.10.11, §3.9 MOD7(LY4 대칭·`ly.lod`), §4 LOD 오라클 입력
> - C-3 결정(사용자 결정 2026-10-12 "C-3은 네 제안대로 해"): nmcnr L 주인 M105, §3.2-3 사실 표·상태
> - U-66 결정(사용자 결정 2026-10-12 "U-66은 (가)로"): §3.10.8·§3.10.11
> - U-63 결정(사용자 결정 2026-10-12 "U-63은 (가)로"): §3.10.11
> - U-60 결정(사용자 결정 2026-10-12 "U-60은 (가)로"): §2.4.6 (가) 확정, (나)는 한 줄 기록, DF-07 주석
> - C-1·C-3(사용자 결정 2026-10-12 "7절 권고대로"): 41 §1.5-4 혼재 노드 구동 종류 규칙 일반화, `structure.json` concept `l_owner` 추가(§3.2-3, 41 §1.12.5), C-6 파일럿 사실 파일 상태, U-65·U-68·U-69·U-70 결정("GQ2, N1, N3, K2 권고대로")
> - 결정 반영 동기화(2026-10-12): §6-8 d/s 맞바꿈 그래프 하나·D-1·D-3 결정("5절 권고대로"), §3.10.11 U-60~U-70 상태(U-61·62·64 결정, U-68~70 신설), §3.10.9 PN1~PN5 결정("4절도 권고대로"), §3.7-8 `budget_ref` 경로
> - 최종 검증·gap 재분석 반영(2026-10-12): 이식 투영 = 값 기반 정준 사상(N1), 열린 질문 해소·U-60~U-67 등록(N3), LUT memo 퇴출 판정 (가) 권고·(나) 함수 분류(N4), d/s 자기 맞바꿈 정지(N5), §3.7 DEC-12·13, §3.10.8 행 추가, §3.10.9~3.10.11, §9.4 남은 J 표, §10.4 단위 DoD 명령
> - design-validator 반영(2026-10-12, needs fixes → M1~M9·m1~m8): 분할 SCC·위상 순서·θ 배정, 이식 전제(시드 금지), 코덱 타입 등록부 계층, 색인 `local`/`solved`, memo 순수성 구조 강제, 퇴출 판정 사용자 결정 두 안, KernelContext·SearchContext 칸 배정·`metrics_dc` 분해능·단계 B 층·층 0 필드, 계수 소유 `RunCounters`, 보존 소유자. Q1~Q7 기본안(Q6만 사용자 결정)
>
> v1.5(2026-10-08): 사용자 결정 "j해석은 네의견에 모두 동의해."(J 공동분석)를 반영했다.
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
> **Planning Doc**: [gain-budget-gmid-sizing.plan.md](../../01-plan/features/gain-budget-gmid-sizing.plan.md) v6.5
> **as-built 기준**: master `004b7d2`(ng-perf-sizing 병합분 포함). 아직 병합되지 않은 브랜치도 함께 본다: `ng-cmfb-pm`(6a6e4c7), `ng-oracle-early`(d56ba66), `ng-tolv-cache`(674a6a1), `ng-layer0-canon`(0c5dc20), `ng-area-budget`(538eeab), `worktree-agent-a90dfb25fa6fe9f04`(7090b9f, LUT r2), `ng-bridge`(d529ea5).

진행 순서는 bkit PDCA다: 이 design → 구현 → gap 분석(`42-gap-checklist`).

## 문서 구성

| 파일 | 내용 |
|---|---|
| `40-engine`(이 문서) | §1 범위·원칙 / §2 아키텍처(흐름·상태 층·패키지 API·§2.4 graph 단일 정본·재사용 규칙) / §3 단계별 설계 GB0~GB9(gain-budget 외, §3.2-3 `structure.json` 개념·파이프라인) / §4 SPICE 오라클 / §5 CM(CMFB) 루프 / §6 대칭 / §7 면적 예산·성능 / §8 승인 없이 축소된 범위와 계획 이탈 / §9 사용자 결정(2026-10-08 확정, Q3·Q4 포함, §9.2 회로별 offset·스윙·ICMR 선언, §9.3 J 결정) / §10 신규 API·검증(오라클·DoD·IC test) / §11 구현 단위(병렬 배분) |
| `41-gain-budget` | FR-1(SP1 stage 유도, §1.12 J 구조 규칙), FR-2(블록 gain 모델과 MNA 잔차), FR-3 연계, FR-8(탐색 전 달성 불가), FR-4(층 0 gain 예산 조합 front와 `gain_budget_db`), 스펙에서 gm/ID·L 출발값 유도 |
| `42-gap-checklist` | FR·NFR·DEC·설계 항목마다 한 행: 설계 절, as-built 상태, 증거 위치 |

**표기**: `E/` = `skills/analog-gmid-design/gmid_engine/`. `P` = 계획서. 상태 어휘는 **OK**(as-built가 설계와 같음) / **DEV**(as-built가 설계와 다름. 어떻게 다른지 함께 적음) / **PART**(일부만 있음) / **MISS**(없음). 브랜치에만 있는 것은 `[브랜치명]`을 붙인다.

---

## 1. 범위와 원칙

### 1.1 범위

계획서 N1.3의 FR-1~FR-9, N1.4의 NFR-1~NFR-6, N3.1의 GB0~GB9를 구현한다. 지원 범위와 합격 기준은 계획서 그대로다(N1.2, DEC-59, DEC-85, N6.2 T1~T9). 옛 엔진(`legacy/`)은 참고로만 쓴다(DEC-82). 단위별 옛 엔진 대조는 범위 밖이다(P N6.3, 사용자 승인 2026-10-12 P-14).

### 1.2 엔진 원칙(설계 제약)

이 원칙들은 계획서와 사용자 결정에 근거하며, 아래 모든 절의 알고리즘이 지킨다.

| ID | 원칙 | 근거 |
|---|---|---|
| EP-1 | **topology 무관.** 회로·소자·넷 이름으로 분기하지 않는다. 지원하지 않는 구조를 만나면 `unsupported_rule_branch`로 정지한다. 일반성은 library 밖의 합성·변형(metamorphic) test로 잰다 | 사용자 2026-10-07 대원칙 3, DEC-62, WP-05 |
| EP-2 | **같은 값을 다시 계산하지 않는다.** 필드가 곧 캐시다(writer 1개 + 입력 버전). graph 밖에는 LUT memo(순수 함수, S0당 하나, 상한 있음)·S3 기록과 메모리 색인·실행 계수·S0 수준 graph 스냅샷 직렬화만 둔다. 다른 lineage의 같은 입력 버전 결과는 이식한다. S0 수준 값은 S0당 한 번, 같은 S0의 다음 실행은 0번 계산한다(§2.4) | 사용자 2026-10-07 대원칙, 2026-10-12 graph 단일 정본 결정, NFR-2, WP-23, DEC-83 |
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
| S1v 뷰 | 뷰별 셀·구동 종류·stage·블록·극점 노드·루프·끊는 점 | `graph.build_s1v`(신규) | DEV: 객체(`S1v`)로 컨텍스트에 실린다. §2.4.8에서 S0 수준 필드로 |
| S0 수준 파생(v1.6) | 결합 변수 y·매핑, GB4 상한표, 출발 구간, metric 구조 입력 | `coupling_vars`·`achievability`·`start_intervals`·`metric_structure` | DEV: 객체 사본(`sctx.ach`·`sctx.start`·`StartContext`·`CurveBook`). §2.4.8 |
| S2 `dc`/`ss`/`ls`/`layout` + 수동소자 값·`dc_gm`·제약 행(v1.6) | 노드전압·소자 op / 소신호 / 대신호 / 레이아웃 / 수동소자 값 / tol_I·`ss` 공용 gm / 제약 행 | `sizing` / `metrics` / `metrics`(신규 `ls`) / `layout` / GB5 블록 / `dc_tolerances` / search 제약 블록 | dc OK, ss OK, ls MISS, layout DEV(별도 lineage), 수동소자 값·`dc_gm`·제약 행 MISS |
| S3 탐색 기억 | evals·runs jsonl, front 점 스냅샷 참조, 메모리 색인(v1.6) | `search.archive`, `search.s3_index`(신규) | OK(기록 타입 결함 §3.9). 색인 MISS(as-built `sctx.cache` 등, §2.4.5) |

불변 스냅샷·구조 공유·필드 = 캐시는 `E/core/graph_snapshot.py:34,148-200`, `E/core/field_value.py:12-35`, `E/core/compute_block.py:77`에 구현되어 있다(OK). 재사용은 같은 lineage 안에서만 일어난다(블록 이름 하나의 `block_version`). lineage를 넘는 재사용(이식)과 분할 입력 버전은 §2.4.4가 더한다.

### 2.3 패키지 간 인터페이스(공개 API)

이미 있는 이름은 각 패키지의 `__all__` 그대로다. **신규**는 이 설계가 추가하는 것이다.

| 공급 → 소비 | API | 형식 | 상태 |
|---|---|---|---|
| core → 전체 | `GraphSnapshot`, `FieldValue`, `compute_block`, `LutMemo`(lut), `FailureRecord`, `exit_code_for`, `normalized_margin`, `read_pdk_decl`, `MetricSignature` | 기존 | OK |
| core → 전체(v1.6) | **신규** `graft`, `Donors`, `compute_block(..., partition=)`, `GraphSnapshot.write(name, part, input_version, rows)`·`block_version(name, part)`(서명 변경), 스냅샷 코덱(`snapshot_codec`), 타입 등록부(`type_registry.register`), `RunCounters`(`run_counters`). `LutMemo.call(fn, *args)`가 `lookup`을 대체하고 memo 함수는 `lut/derived_fns.py` | §2.4.3·2.4.4·2.4.6·2.4.9 | MISS |
| search 내부(v1.6) | **신규** `S3Index{get, failure, find, local, solved, retain, release}` | §2.4.5 | MISS |
| lut → sizing·metrics·layout | `op_point`, `vgs_for_gm_id`, `vdsat`, `gmb`, `caps`, `tol_v_table`, `tol_vdsat_table`, `curve_report`, `load_lut_set` | 기존 | OK |
| lut → 41 §6 | **신규** `ft_curve(kind, L, VDS, VSB)`, `intrinsic_gain_curve(...)`, `vdsat_curve(...)`, `idu_curve(...)`(gm/ID 축 곡선), **신규** `vgs_for_current_density`(DEC-88) | (gm/ID 배열 → 값 배열), LUT 곡선 표 memo | MISS(조합으로는 계산 가능) |
| authoring → graph·search | `SizingSpec`(제약·목표·θ 범위·설정), **신규 필드** `gain_budget_db_override`, `driving_spec`, `untie_orbits`(옛 설계 이름 `symmetry_untie`), `cm_sense_elements`[ng-cmfb-pm], `element_values.*.measurement_load`[ng-area-budget] | spec 로더 | PART |
| graph → sizing·search·metrics | S1(기존), **신규** `S1v{views[], blocks[], pole_nodes[], loops[], cuts[], coverage}`, **신규** `orbits`(자기동형 궤도) | S1v 스냅샷 필드 | MISS |
| sizing → search | `size_and_seal`, `build_kernel_context`, `dc_theta_schema`, `dc_current_basis` | 기존 | OK |
| metrics → search | `ss_evaluate`, `metric_value`, **신규** `block_local_gain`, `achievability`, `ls_fields` | | PART |
| search → layout·report·pipeline | `find_front` → `FrontPoint`, `node_across_front`, **신규** `layer0_budget` → `BudgetCombination{gain_budget_db, ...}` | | PART |
| layout ⇄ convergence | `run_layout` → 설계점 스냅샷의 S2 `ly_*` 필드(§2.4.7·§2.4.8, `LayoutResult` = (스냅샷, 계산 블록 목록)), 파생 값(`w_requests`·`revalidation` 등)은 `layout_outputs(snapshot)`, **신규** `converge(snapshot)` | | MISS(MOD8) |
| pipeline | **신규** `run_gmid_design_pipeline(spec, *, search, output_dir, instrument, activations_out)` | exit code = `exit_code_for` | MISS(`[ng-bridge]`에 오라클 입력 생산자만) |


### 2.4 graph 단일 정본·재사용 규칙 (v1.6 graph 정본 개정)

> **v1.6 graph 정본 개정**(사용자 결정 2026-10-12 "1~4까지 새로고친 네 제안대로 해", 같은 날 "G는 승인"). **design 문안은 사용자 승인(2026-10-12 "design 승인")됐다**. 결정 자체(1~4절, G-5·G-7·G-8·G-9·G-10)는 승인됐고, 이 절은 그 결정을 엔진 설계로 옮긴 것이다. 계획 근거는 DEC-83·NFR-2·WP-23·N3.3·N3.5·N3.6(v6.4 정정)이다. 41(gain 예산)은 이 절을 "40 §2.4"로 인용한다.
>
> **as-built 기준**: `u15-layer0-tests` @bd19cc6(`wt/u15-layer0-tests`). 아래 증거 줄 번호는 모두 그 커밋의 `E/` 기준이다.
>
> **design-validator 반영**(2026-10-12, M1~M9·m1~m6): 분할과 SCC(§2.4.4), 이식 비트 동일 전제(§2.4.4), 코덱 타입 등록부의 import 계층(§2.4.3), 색인 API 분리(§2.4.5), memo 순수성의 구조 강제(§2.4.6), 퇴출 판정은 U-60 (가)(§2.4.6, "U-60은 (가)로"), 빠진 항목(§2.4.7·2.4.8), 계수 소유(§2.4.9), 보존 소유자(§2.4.5). 열린 질문은 기본안을 정해 두었다(§2.4.12, 사용자 승인(2026-10-12 "design 승인")).

#### 2.4.1 상태 층과 graph 밖에 허용되는 것

설계 값은 Circuit State Graph 필드에만 있다. 필드마다 writer 하나와 그 값을 만든 입력 버전이 있다(필드가 곧 캐시, DEC-83). 층은 수명으로 나눈다.

| 층 | 담는 것 | 수명·키 | writer |
|---|---|---|---|
| **S0 수준 층** | S1(구조), S1v(뷰·셀·stage·블록·루프·극점 노드·끊는 점·L 동치류), 결합 변수 y와 기둥↔블록 매핑(GB3), GB4 달성가능성(블록 gain 상한표·곡선 검사·구조 DOF·면적 하한·헤드룸 행·판정·층 0 정의역 상한), 출발 구간(41 §6), metric 구조 입력, 커널 컨텍스트의 구조 파생(θ 스키마·고정 노드·L 묶음, §2.4.7) | S0 하나에 스냅샷 하나. 디스크에 직렬화한다(§2.4.3) | 단계 A의 GB1~GB4·A8·A9 계산 블록(§2.4.8) |
| **단계 B 층** | 결합 잔차 분포 r̂(41 B1), 수치 rank(41 B2) | 실행 수명. S0 수준 스냅샷 위에 쓰고 **직렬화하지 않는다**: 표본이 그 실행에서 이미 평가한 점(`residual_probe(pool=)`)에서 오므로 S0만의 함수가 아니다 | `residual_probe`, `dof_numeric` |
| **설계점 층(S2)** | `dc`·`ss`·`ls`·`layout`·수동소자 값·제약 행·목적 분해능. 평가마다 S0 수준 스냅샷 위에 쓴다(구조 공유) | 설계점 스냅샷. 보존 규칙은 §2.4.5 | 평가 커널·봉인·GB5·GB8·MOD7 블록 |
| **층 0 층** | 블록 국소 후보의 커널 결과와 블록 범위 metric, 매크로 풀이 결과, 조립 기록, 회차 기록(41 §5) | 국소·조립 스냅샷. S3 색인으로 찾는다(§2.4.5) | 평가 커널 블록(같은 writer), 층 0 블록(§2.4.8) |

**graph 밖에 허용되는 것은 넷뿐이다**(결정 G-1·G-2'). 이 밖의 저장소는 구조 test가 거부한다(§2.4.10 G-8).

| # | 저장소 | 담을 수 있는 것 | 담을 수 없는 것 |
|---|---|---|---|
| (a) | **LUT memo**(S0당 인스턴스 하나, §2.4.6) | `lut` 패키지의 순수 함수 결과. 디스크 LUT 파생표(tol_V·tol_VDsat·곡선 표 등)와 1변수 근을 포함한다 | graph 필드를 읽어 만든 값, 소자 이름을 키로 한 설계 값 |
| (b) | **S3 기록**과 **S3 메모리 색인** | evals·runs jsonl(디스크), 평가 요약 + 스냅샷 지문 + 보존 중인 스냅샷 참조(메모리, §2.4.5). 실패 캐시는 evals 실패 줄에서 재구성한 색인의 보기다 | 요약에 없는 설계 값의 사본 |
| (c) | **실행 계수**(`core/run_counters.py` 하나, §2.4.9) | 호출 수, 시간, 평가 예산 N_T·E_B, 마감, 블록·분할 계수와 그 증거 집합. 실행 수명이고 상한은 실행 평가 수로 정해진다 | 값 캐시 |
| (d) | **S0 수준 graph 스냅샷의 디스크 직렬화** | S0 수준 층 전체(§2.4.3). graph 직렬화이지 별도 DB가 아니다 | 단계 B 층, 설계점 층, 층 0 층 |

**의도적 재계산**(결정 3절)은 둘뿐이다. 계수(§2.4.9)는 이 둘을 따로 센다.
- SPICE 오라클: 독립 검증이므로 엔진 값을 쓰지 않는다(§4).
- FD 스텝: θ가 다르므로 입력 버전이 다르다. 그 성분을 읽는 블록만 계산한다(WP-23 (5)).

**대칭 탐색**(D-2): 자기동형 궤도와 d/s 맞바꿈 검출(사용자 2026-10-12 결정 "6. 가")은 S1 하나에서 한다. 궤도 결과는 S0 수준 필드다. 알고리즘은 §6(대칭)의 몫이다. 다른 브랜치 초안 f786dc6은 병합하지 않고 참고만 한다.

#### 2.4.2 S0 수준 층의 필드

S0 수준 값은 계산 블록(`core.compute_block`)으로 만들고 S0 수준 스냅샷에 쓴다. 블록이 선언한 입력만 읽으므로 입력 버전이 같으면 다시 계산하지 않는다. 같은 S0의 다음 실행은 §2.4.3의 디스크 스냅샷 위에서 같은 블록을 부르고, 모든 블록이 재사용으로 끝난다(계산 0).

- 레코드 key: S0 수준 graph 레코드는 개념마다 key 하나다. S1 = `s1`(as-built `graph.GRAPH_KEY`). 신규는 `s1v`, `coupling`, `ach`, `start`, `kernel`이다. 소자별 값은 `device` 레코드의 필드다(필드 이름 접두 `s1v.`·`ach.`·`start.`).
- 값 형식: as-built frozen dataclass(`E/graph/s1v_values.py`, `E/metrics/achievability_types.py`, `E/search/start_values.py`의 `StartRow`·`StartConflict`·`MacroResult`·`StartRung`·`Placement`)를 필드 값으로 그대로 쓴다. 묶음 객체(`S1v`, `Achievability`, `StartIntervals`)는 필드 묶음으로 풀고 사본을 두지 않는다.
- 읽기: 소비자는 S0 수준 스냅샷의 필드를 읽는다. 컨텍스트 객체에 그 값을 옮겨 담지 않는다(§2.4.7).

#### 2.4.3 S0 수준 스냅샷의 영속화

결정 G-2'다. 옛 계획 문구 'S1 디스크 캐시'를 대체한다.

| 항목 | 규칙 |
|---|---|
| 대상 | S0 수준 층 전체(§2.4.1 표 첫 행). 단계 B 층·설계점 층·층 0 층은 쓰지 않는다 |
| 키 | (i) S0 전체 지문(P N3.3 v6.4: topology 정규화 해시, LUT 내용 해시 + 생성 메타, spec 전체 해시, PDK 선언 파일 내용 해시, 유도 규칙 코드 해시, metric 정의 코드 해시) (ii) `structure.json` 사실 지문(as-built S1 키에 포함) (iii) 엔진 코드 지문 = `gmid_engine` 아래 **test가 아닌 모든 패키지**의 `.py` 파일 바이트 sha256(파일 경로 정렬). 블록 입력 버전의 코드 해시는 블록 함수 자신의 코드 객체만 덮으므로(`E/core/compute_block.py:65`) 실행 사이 재사용에는 (iii)이 필요하다. as-built `search_context._code_fp`(`E/search/search_context.py:39-48`)는 6개 패키지만 덮어 범위가 좁다. (i)의 PDK 선언 해시 때문에 `run_stage_a`의 PDK 선언은 **필수 인자**다(기본값 없음, 없으면 키를 만들지 않고 거부 -- Q1 fail-closed) |
| 형식 | gzip JSON 하나: `{schema_version, key{...}, writers, block_versions, records[{kind, key, fields{name: {value, writer, input_version, write_count}}}], fp, body_sha256}`. 값은 타입 있는 인코딩이다: float = `float.hex`, tuple·frozenset(정준 순서)·frozen dataclass = `{"__type__": "<모듈>.<클래스>", ...}`. 옛 S3 `_plain`(repr로 떨어지는 직렬화, `E/search/archive.py:19-37`)은 쓰지 않는다 |
| 타입 등록부 | 디코더는 **실행 시 타입 등록부**(`core/type_registry.py`)에 있는 타입만 받는다. 목록 밖 타입은 거부한다. import 계층(P N3.10)을 지키기 위해 등록은 아래에서 위로 한다: 각 패키지의 `__init__`이 자기 필드 값 형식을 `register(cls)`로 올린다. `pipeline`이 모든 패키지를 import해 등록부를 채운 뒤 코덱을 부른다. core는 상위 패키지(`graph`·`metrics`·`search` 등)를 import하지 않는다. `_module_map` test는 등록부를 읽기만 한다(§2.4.10 ②) |
| 검증 | 읽은 뒤 스냅샷 `fp`를 다시 계산해 저장된 `fp`와 비교한다. 다르거나 `body_sha256`이 틀리면 손상으로 본다 |
| 손상 처리 | 다시 계산하고 **같은 키의 파일을 원자적으로 교체**한다. 손상 사실은 **단계 A 보고서의 `s0_snapshot` 키**(값 `hit` \| `miss` \| `corrupt`)에 남긴다(U17 ①-a). 결과 JSON 계수 `perf.s0_snapshot.corrupt`는 `RunCounters`(§2.4.9)가 생기는 단계 ②에서 더한다 |
| 쓰기 | 원자적이다: 같은 디렉터리의 임시 파일에 쓰고 교체한다. 키가 이미 있고 검증을 통과하면 쓰지 않는다 |
| 위치 | P N3.5: `gmid_engine` 아래 `.gitignore` 등록 디렉터리. 파일 이름 = `<키 지문>.json.gz`. 환경 변수 `GMID_S0_SNAPSHOT_DIR`가 비어 있지 않으면 그 폴더를 쓴다(test 격리 수단, LUT 파생표 캐시 `GMID_LUT_TABLE_CACHE_DIR`와 같은 관례. 기본 위치는 바뀌지 않는다) |
| 무효화 | 키가 다르면 없는 것으로 본다(SC-d). 부분 재사용은 하지 않는다. 키가 다른 옛 파일은 U-68 결정대로 쓰기 시점에 정리한다(§2.4.12 Q2). **U-68 정리 = 프로세스당 첫 실제 쓰기 1회**: 프로세스에서 처음으로 파일을 실제로 쓴 저장만 정리하고(적중·이미 있는 키는 쓰기가 아니다) 같은 프로세스의 다음 쓰기는 정리하지 않는다. 표시는 `core/snapshot_codec.py`의 모듈 수준 1비트 `_CLEANUP_STARTED`다(정리를 시작하기 전에 켠다 -- 정리가 실패해도 그 프로세스에서 다시 시도하지 않는다). 값 캐시가 아니라 §2.4.1 (d) S0 스냅샷 영속화 범주의 상태다(§2.4.10 허용 모듈). U-68의 '현재 파일로 만들 수 있는 키' 재현 판정 = **입력 파일 원본 sha256**(topology·spec·LUT·PDK 선언·`structure.json` -- 키 (ii)와 일치) + **엔진 코드 지문**(키 (iii))이다(구현도 `structure.json`을 포함한다). `structure.json`을 넣는 것은 U-68 원문 취지(어떤 checkout으로도 재현할 수 없는 옛 파일만 정리)를 지키기 위해서다: 키 (ii)가 사실 지문을 담으므로 빼면 현재 사실 파일로 만든 키를 재현 불가로 오판해 지운다 |
| 계수 | 단계 ①: 단계 A 보고서 `s0_snapshot` 키(`hit` \| `miss` \| `corrupt`). 단계 ②: `RunCounters`의 `perf.s0_snapshot{hit, miss, corrupt}`(§2.4.9). 적중이면 S0 수준 블록 계산 수 0이 G-10 판정 2다 |

#### 2.4.4 이식(graft) 연산

결정 1절 #1이다. 서로 다른 lineage의 스냅샷에서 **입력 버전이 같은 블록 결과**를 가져오고, 공유량이 닿는 결과만 계산한다. 층 0 조립(41 §5.5)이 첫 소비자다. 국소 스냅샷 조회는 S3 색인(§2.4.5)으로 한다.

**분할 계산 블록**(core 확장): as-built 계산 블록은 열 전체를 한 번에 쓰고, 재사용 판정도 블록 이름 하나의 `block_version`으로 한다(`E/core/compute_block.py:73-90`, `E/core/graph_snapshot.py:144-200`). 이 상태로는 국소 결과를 합친 조립점의 투영이 어느 국소 스냅샷과도 같지 않아 이식할 것이 없다. 그래서 블록에 분할을 둔다.
- 선언: `compute_block(name, reads=..., writes=..., partition=<분할 함수>)`. 분할 함수는 S0 수준 필드(S1 기둥·가지, S1v L 동치류, 쓰기 계획)만 읽어 `{분할 key: (쓰는 레코드 key 집합, 읽는 레코드 key 집합, 읽는 θ 성분 집합)}`을 낸다. 분할이 없으면 분할 key는 `*` 하나다(as-built와 같다).
- **분할 key 규칙**:
  1. 기둥 하나에만 덮이는 소자·넷은 그 기둥 id다. 둘 이상의 기둥에 덮이는 소자·넷(공유 소자, 기둥 경계 넷)은 `shared:<기둥 id 정렬>`이다. 덮는 집합은 as-built `size_and_seal_local.covered_sets`(`E/sizing/size_and_seal_local.py:65-85`)와 같은 정의다.
  2. **SCC를 쪼개지 않는다**: 블록 내부 의존 그래프(같은 블록이 쓰는 행 → 그 행을 읽는 같은 블록의 행)의 강연결 성분이 두 분할에 걸치면 그 분할들을 하나로 합친다. 합친 분할의 key는 합친 기둥 id들로 만든 `shared:<…>`다. 예: 기둥 둘에 걸친 W2 순환 블록(as-built `dc_columns`의 SCC 고정점)은 한 분할이다.
  3. **θ 성분 배정**: θ 성분은 그 성분이 정하는 행이 속한 분할에 배정한다. 여러 분할의 행을 정하는 성분(블록을 가로지르는 L 동치류의 L, 결합 변수 y, 공유 전류)은 그 분할들을 덮는 `shared:<…>` 분할에 배정한다. 블록을 가로지르는 L 동치류의 멤버 소자 행도 같은 `shared:` 분할로 간다.
  4. **실행 순서**: 분할 사이 의존(한 분할이 쓴 행을 다른 분할이 읽음)은 SCC를 합친 뒤 DAG다. 분할은 이 DAG의 위상 순서(같은 순위는 분할 key 정렬)로 판정·계산한다.
- 입력 버전: 분할마다 `fp_of((name, 코드 해시, 그 분할의 투영 지문))`. 기록은 `block_versions[(writer, 분할 key)]`다.
- **투영 지문 = 값 기반 정준 사상**(design-validator N1): 분할이 읽는 모든 양을 `{(kind, key, field): value_fp}` 하나로 모은 정준 사상(키 정렬)의 지문 + 그 분할에 배정된 θ 성분 + 나머지 extras다. writer·input_version·쓰기 횟수는 넣지 않는다. 그래서 같은 양이 스냅샷 행에서 오든(조립점: 이웃 분할이 쓴 행) 국소 봉인의 `fixed` extras에서 오든(국소 후보: 이웃 값을 고정 입력으로 받음) 같은 값이면 같은 지문이다. 이것이 국소 스냅샷 → 조립점 이식이 맞는 조건이다.
- **`fixed`는 extras로만 넘긴다**: 국소 봉인(41 §5.3.9)은 `fixed` 값을 graph 행으로 쓰지 않는다(그 행의 writer는 다른 분할·블록이다). 분할 블록은 읽는 양을 투영에서 찾고, 행에 없으면 `fixed` extras의 같은 (kind, key, field) 칸에서 읽는다. 둘 다 있으면 호출 계약 위반(`ValueError`)이다.
- **이식이 비트 동일인 전제**(분할 블록의 의무): 분할 블록은 투영 밖의 어떤 입력도 읽지 않는다. 반복 풀이의 초기값도 투영의 함수다. 직전 스냅샷(S2p)·parent·이전 반복의 값을 시드로 쓰지 않는다. 시드가 필요한 블록은 분할 블록이 될 수 없고 `*` 하나로 남는다(이식 대상 아님). 구조 test가 분할 블록 함수의 인자가 `Projection` 하나뿐인지 확인한다(as-built 규칙 그대로, `E/core/compute_block.py:12-13`).
- 쓰기: graph setter 서명을 `GraphSnapshot.write(name, part, input_version, rows)`로 바꾼다. `rows` = `{(kind, field): {key: value}}`이고 key는 그 분할의 쓰는 레코드 key 집합과 정확히 같아야 한다(다르면 `ValueError`). 분할 밖 행은 건드리지 않는다. `block_version(name, part)`가 `input_version`이 된다. 분할 없는 블록은 `part = "*"`이고 동작은 as-built `write`와 같다. 한 블록의 분할들은 서로 다른 행을 쓰므로 writer 하나 규칙(SC-a)은 그대로다.
- 대상: 평가 커널 ②~⑤와 봉인 항목 블록, 층 0 블록 범위 metric, GB5 수동소자 블록 `passive_values`(§2.4.8 `device: passive_value`. 읽는 레코드 = 영점 상쇄 셀 소자의 `dc_gm`. 분할이 없으면 전류 θ만 바뀐 자식에서도 블록 전체가 다시 계산되므로 이 분할로 해소한다 -- U17 ①-c 재검증 기록, **U17 단계 ②로 이월**). 분할이 정의되지 않는 블록(전회로 MNA, 전역 metric)은 `*`이다.

**API**(`E/core/graft.py`, 신규):

```python
def graft(target: GraphSnapshot, block: ComputeBlock, part: str, donor: GraphSnapshot) -> GraphSnapshot
# donor.block_version(block.name, part) 가 target 위에서 계산한 그 분할 입력 버전과 같을 때만, donor 의 그 분할 행(block.writes 열)을
# target.write(block.name, part, 같은 입력 버전, 그 행) 로 쓴다. 다르면 ValueError(호출 계약 위반 -- 판정은 아래 호출 규칙이 먼저 한다).

class Donors(Protocol):
    def find(self, writer: str, part: str, input_version: str) -> GraphSnapshot | None: ...
# ComputeBlock.__call__(snapshot, *extras, donors: Donors | None = None, counters: RunCounters)
```

**호출 규칙**: 계산 블록은 분할마다 위상 순서로 다음을 판정한다.
1. 같은 lineage 재사용: `snapshot.block_version(name, part)`가 입력 버전과 같으면 아무것도 하지 않는다(as-built와 같다).
2. 이식: `donors.find(name, part, 입력 버전)`가 스냅샷을 주면 `graft`로 그 행을 가져온다.
3. 계산: 둘 다 아니면 그 분할만 계산한다.

공유량(공유 소자, 결합 변수 y, 블록을 가로지르는 L 동치류, 기둥 경계 넷)이 바뀐 분할은 투영이 달라져 입력 버전이 어느 원천과도 맞지 않는다. 그래서 '공유량이 닿는 필드만 계산'은 별도 규칙 없이 위 판정에서 나온다. 앞 분할이 계산되어 값이 바뀌면 그 행을 읽는 뒤 분할의 투영도 바뀌어 계산된다(위상 순서라 판정 시점에 입력이 확정되어 있다).

**불변식과 결정론**:
- 이식한 행은 계산한 행과 값이 같다. 블록은 투영만의 순수 함수이므로(위 전제) 같은 입력 버전이면 같은 값이다. test: 같은 θ를 (가) 빈 lineage에서 전부 계산, (나) 국소 스냅샷들에서 이식한 두 결과의 스냅샷 `fp`와 모든 필드 `value_fp`가 같다.
- 원천 순서 무관: 같은 입력 버전의 원천이 여럿이면 S3 색인 순번(seq)이 가장 작은 것을 쓴다. 원천 목록 순서를 섞어도 결과 `fp`가 같다(test).
- writer 권한: `graft`는 `GraphSnapshot.write`(graph setter)만 쓴다. 새 쓰기 경로가 없으므로 SC-a·SC-b 검사가 그대로 적용된다.
- 계수: 블록 계수에 `grafts`를 더한다. `calls = reuses + grafts + computes`(§2.4.9).

#### 2.4.5 S3 메모리 색인과 스냅샷 보존

결정 1절 #2와 G-5다. as-built `sctx.cache`(`{EvalKey: EvalResult}`, `E/search/search_context.py:65`), `disk_failures`(같은 파일 :66), `computed_keys`(:67), `local_seal_memo`(:88, `E/search/layer0_budget.py:385-386`, `E/search/local_candidates.py:141-144`)를 색인 하나로 바꾼다. 오케스트레이터 초안 EvalCache(MOD6)와 `local_seal_memo`는 철회한다(G-5).

**색인 항목**(`E/search/s3_index.py`, 신규) = S3 evals 한 줄과 같은 내용 + 메모리 전용 칸:
- S3 줄 내용: 평가 키, seq, θ, 상태, 실패 레코드, 목적 값(전력·면적·b_P), 제약 행(c, active), 미측정, 경고, origin(단계·시작점·층 0 블록 키·기둥·bin·회차), `snapshot_fp`. 이 값들은 스냅샷 필드에서 한 번 읽어 쓴다(writer = S3 기록기). 설계 값의 새 정본이 아니다.
- 메모리 전용: 분할 입력 버전 표 `{(writer, 분할 key): 입력 버전}`, 보존 중이면 스냅샷 참조, 보존 소유자 집합.

**조회 API**:

```python
class S3Index:
    def get(self, key: EvalKey) -> IndexEntry | None                       # 같은 θ 재요청. 적중이면 커널 0
    def failure(self, key: EvalKey) -> FailureRecord | None                # 실패 캐시 보기
    def find(self, writer: str, part: str, input_version: str) -> GraphSnapshot | None   # §2.4.4 Donors. 보존 중인 스냅샷만
    def local(self, block_key: str, column: frozenset[str], theta_block_fp: str, fixed_fp: str) -> GraphSnapshot | IndexEntry | None
        # 41 §5.3.9 국소 후보 찾기. 보존 중이면 스냅샷, 놓았으면 요약 항목. 찾으면 다시 봉인하지 않는다
    def solved(self, block_key: str, bin_key: str, fixed_fp: str) -> bool  # 41 §5.3.2 L-3: (목표 bin, 고정 입력 지문) 쌍을 이미 풀었는지
    def retain(self, key: EvalKey, owner: str) -> None
    def release(self, owner: str) -> None
```
- `failure`의 출처: 시작할 때 S3 evals 실패 줄(같은 S0·스키마·코드 지문)에서 항목을 재구성한다(as-built `_disk_failures`, `E/search/search_context.py:92-102`).
- `solved`의 출처: 층 0 회차 기록 필드(§2.4.8 'L-3 회차 기록')를 색인할 때 (블록 키, bin, 고정 입력 지문) 쌍을 함께 등록한다.

**정보(m8)**: 이전 실행의 S3 feasible 점을 시작점으로 쓰면(P N3.5 시작점 ②, `n_starts`) 그 점은 실행마다 다시 평가된다. 그 실행에서 처음 계산하는 것이므로 G-10 판정 1의 위반이 아니고 `regenerated_from_prior_run`으로 따로 센다. 실행을 넘어 설계점 스냅샷을 재사용하는 것은 현재 결정 밖이다(디스크 영속화는 S0 수준 층만, §2.4.3).

**보존 규칙**(결정 1절 #2): 스냅샷은 소유자가 있는 동안만 메모리에 둔다.

| 소유자 | 보존하는 것 | 놓는 때 |
|---|---|---|
| 진행 중인 SLSQP 풀이 | 현재 반복점, 직전 채택점(FD 스텝의 parent와 다음 반복의 기준점) | 그 풀이가 끝날 때 |
| 외층 시작점 대기열 | 대기 중인 시작점(층 0 조립점, 출발 구간 후보 등)의 스냅샷 | 그 시작점의 풀이가 끝날 때 |
| 층 0 단계(모든 회차) | 블록 국소 front 점의 국소 스냅샷, 조립점 스냅샷(조립의 이식 원천이고 다음 회차의 고정 입력 출처) | 층 0 단계가 끝날 때. 조립점은 그때 '외층 시작점 대기열'로 넘어간다 |
| front | front 점(DEC-77) | 실행 끝 |
| 채택 | 채택 해 | 실행 끝 |

소유자가 없는 스냅샷은 색인에서 참조를 지우고 요약만 남긴다. front·채택 점은 S3 `snapshots/`에도 쓴다(as-built `write_snapshot`. 직렬화는 §2.4.3과 같은 타입 있는 인코딩으로 바꾼다).

**놓은 스냅샷이 다시 필요할 때**(Q4, **결정**(사용자 결정 2026-10-12 "K-2 권고대로, GQ1/GQ3/GQ4, U-14,U-20,U-32,U-45 권고대로"), GQ3 = U-73):
- 같은 실행에서 만든 θ를 다시 기준점으로 쓰느라 스냅샷을 재생성하면 **FAIL**이다(보존 소유자 누락이라는 설계 결함). 계수 `regenerated_after_release`.
- 이전 실행의 S3 점(시작점 출처 ③ '지문이 일치하는 S3 feasible 점')에서 시작하는 것은 허용한다. 그 실행에서 처음 계산하는 것이라 중복이 아니다. 계수 `regenerated_from_prior_run`으로 따로 센다.

#### 2.4.6 LUT memo: 순수성·인스턴스 하나·상한

결정 G-4'·#8이다.

**순수성의 구조 강제**:
- memo 함수는 **`lut` 패키지 안에만** 정의한다(`E/lut/derived_fns.py`와 기존 lut 조회 파일). import 계층(P N3.10)상 `lut`은 `graph`·`sizing`·`metrics`·`search`를 import할 수 없으므로 graph 필드를 읽을 길이 구조적으로 없다.
- 호출은 `memo.call(fn, *args)`뿐이다. 클로저 `compute`를 받는 as-built `lookup(region, fn_name, key, compute)`(`E/lut/lut_memo.py:60-62`)는 없앤다.
- 정적 검사(규칙 G 확장, §2.4.10): `memo.call`의 첫 인자는 모듈 수준 이름(`ast.Name`·`ast.Attribute`)이어야 한다. lambda·중첩 함수·부분 적용은 거부한다.
- 실행 시 검사(`call` 안): `fn.__closure__ is None`, `fn.__qualname__ == fn.__name__`(모듈 수준), `fn.__module__`이 `gmid_engine.lut` 패키지 이름(`gmid_engine.lut.__name__`에서 읽는다, 문자열 리터럴 아님) + `.`으로 시작. 하나라도 어기면 `TypeError`.
- 인자: 첫 인자는 `LutSet`이고 나머지는 숫자·문자열·bool·None과 그것들의 tuple이다(as-built `BoundedLRU` 불변 키 검사, `E/core/bounded_lru.py:7-9`). 키 = (LUT 지문, `fn.__module__`, `fn.__name__`, 인자).
- 디스크 파생표는 같은 규칙에 디스크 층만 더한다(as-built `lookup_persistent`·`TableCache`, `E/lut/table_cache.py`).

**memo로 옮기는 것**(LUT와 숫자 인자만의 함수인데 지금 다른 곳에 있는 것). 모두 `lut/derived_fns.py`의 모듈 수준 함수가 된다.

| as-built | 위치 | memo 함수와 인자 |
|---|---|---|
| `solve_self` 1변수 근 | `E/sizing/block_columns.py:335-398`(키 :397) | `self_node_root(lut, kind, w_key, L, ln_idu, relation, known, vds0, vds1, vsb0, vsb1, lo, hi, tol)`. 인코딩: `relation` = 관계 어휘 문자열(as-built `REL_VGS_GATE`·`REL_VGS_SOURCE` 값), `known` = 그 1변수 노드 식이 읽는 이미 정해진 노드전압의 float tuple(식의 단자 순서 고정: gate·drain·source·bulk 중 미지수가 아닌 것). 객체·dict는 넘기지 않는다 |
| `cell_floors` 칸 정점 하한·전도 하한 | `E/search/cell_floor.py:47-60`(`sctx.cell_floors`, `search_context.py:84`) | `peak_floor(lut, kind, w_key, lo, hi)`, `conduction_floor(lut, kind, w_key, lo, hi)` |
| `edge_costs` | `E/metrics/edge_cost_bounds.py:51`. `E/search/iv_curves.py:49-52`(`CurveBook._edges`)와 `E/metrics/achievability.py:233`이 따로 계산한다 | `edge_costs(lut, kind, w_key)` |
| `CurveBook._ref`(기준 VDS)·`_tol`(tol_vdsat 최댓값) | `E/search/iv_curves.py:84-87,125-139` | `reference_vds(lut, kind, w_key, L)`, `tol_vdsat_max(lut, kind, w_key, L, vds)` |
| `ParamTables` 행(x, y, z) | `E/metrics/block_param_tables.py:37-54`. `achievability.py:308`과 `iv_context.py:69`가 S0마다 두 벌을 만든다 | `param_row(lut, kind, w_key, i_l, i_d, i_s)` |
| `block_columns.tol_cells` | `E/sizing/block_columns.py:177` | `tol_v_table(...).at`(이미 lut 함수)을 memo로 직접 부른다 |

`one_var_writers`(`cell_floor.py:38`의 `_ONE_VAR_KEY`)는 LUT 함수가 아니라 쓰기 계획의 파생이므로 S0 수준 필드다(§2.4.8).

**인스턴스 하나**: S0마다 `LutMemo` 하나를 만들고 준비 단계(GB4·출발 구간)와 탐색이 같은 것을 쓴다. as-built는 둘이다. 준비 memo는 `StartContext.memo`·`LocalInputs.memo`·`ParamTables._memo`가 계속 쥐고 있고, `_wire_sweep_memo`(`E/search/search_context.py:105-121`)가 탐색용 새 memo를 만들며 계수용 첫 평가를 임시 컨텍스트에서 돌리고 버린다(:112-121). `sweep_memo.py`(`_CountingMemo`)는 단계 ③에서 지운다.

**상한과 퇴출 판정 -- 결정(사용자 결정 2026-10-12 "U-60은 (가)로", U-60 = (가))**
- 키: 연속 축 값 그대로(as-built와 같다).
- 상한(영역 r = point·curve·root마다): B_r = U_S0,r + Σ_i K_max,i·(U_pass,i,r + U_macro,i,r) + (n_θ + 1)·U_eval,r.
  - U_S0,r = S0 수준 층을 계산하며 센 서로 다른 키 수다. 디스크 S0 스냅샷이 적중하면 0이다.
  - U_L0,r = Σ_i K_max,i·(U_pass,i,r + U_macro,i,r). 블록 i의 **첫 후보 하나**에서 한 번 센다(U_pass = 첫 후보 고정점 한 바퀴의 서로 다른 키 수, U_macro = 같은 바퀴 매크로 호출의 키 수, K_max,i = 그 바퀴의 N3.6 반복 상한). N_T를 곱하지 않는다. 41 §5.8에 같은 문장이 있다. 층 0이 꺼진 회로는 0이다.
  - U_eval,r = 외층 첫 평가가 센 서로 다른 키 수다.
  - 세 항 모두 실행 시작 쪽에서 한 번 세고 고정한다. N_T·E_B·벽시계에 의존하지 않는다(결정론, NFR-4).
- **판정**: 퇴출은 허용하고 퇴출 수는 `perf`에 보고한다. 퇴출된 키를 다시 계산하면(`recomputes_after_eviction` > 0) FAIL이다. 계획 NFR-2·N3.5를 이 문구로 고쳤다.
- 기록(대안, 채택 안 됨): (나) 격자 마디 키·퇴출 0 FAIL은 root 영역 상한이 E_total(N_T)에 의존해 쓰지 않았다.

**공통 규칙**:
- memo는 계수 상태로 시작한다(상한 없음, 키를 센다). 상한의 항을 다 셌으면 상한을 고정한다. 이미 모은 항목은 그대로 둔다. 계수 평가가 곧 실제 첫 평가이고 S3 색인에 기록된다.
- 계수 0 영역을 '저장 없이 매번 계산'으로 두는 `_Unmemoized`(`E/lut/lut_memo.py:25-36`)는 없앤다(같은 키 재계산이 생긴다).
- DF-07(상한에 닿으면 LRU 퇴출, 캐싱 중단 금지, §10.3a)은 그대로다. 퇴출은 정상 동작이고, 퇴출된 키의 재계산만 FAIL이다.

#### 2.4.7 값 사본 제거

결정 #5·#6·#9와 G-7이다. 아래 객체는 graph 필드나 S0 수준 필드의 사본을 들고 있다. 사본을 지우고 필드를 읽는다.

| 객체 | as-built 사본 | 바뀐 형태 |
|---|---|---|
| `SearchContext`(G-7) | `E/search/search_context.py:54-89`의 모든 칸 | **참조**(S0 수준 스냅샷 뿌리, LUT memo, spec, PDK 선언, S3 경로) + **S3 메모리 색인** + **실행 계수**만 둔다. `__slots__`와 frozen으로 고정하고, 바꾸는 길은 S3 색인 API와 계수 API뿐이다. 칸마다 갈 곳은 아래 'SearchContext 칸 배정' 표 |
| `KernelContext` | `base`, `inputs`, `lut`, `schema`(θ 스키마, `zero_cancel` 포함), `fixed_values`, `resistor_values`, `plan_versions`, `l_ties`(`E/sizing/s2_values.py:429-443`) | 설계 값은 S0 수준 필드: `graph/kernel`: `theta_schema`(`zero_cancel` 포함), `fixed_values`, `resistor_values`, `l_ties`. `plan_versions`는 쓰기 계획 블록의 `block_version` 읽기로 대체한다. 남는 칸은 참조(`base` = S0 수준 스냅샷, `lut` = LUT memo와 폭 키, `inputs` = spec 파싱 결과) |
| `StartContext` | `cls`, `kinds`, `pins`, `rails`, `rail_v`, `node_colour`, `l_owner`, `basis`, `element_values`, `zero_cancel`, `l_cells`, `box` 등 graph 열 사본과 `curves`·`memo`·`block_local`(`E/search/start_values.py:186-235`) | 없앤다. 출발 구간 블록이 선언한 입력 필드를 투영으로 읽는다 |
| `CurveBook` | LUT 파생 사전 3개와 `points`(`E/search/iv_curves.py:37-40,102-108`) | 없앤다. LUT 파생은 memo 함수(§2.4.6), `points`는 소자 필드 `start.point`(§2.4.8) |
| `S1v`·`Achievability`·`StartIntervals` 묶음 객체 | 컨텍스트와 단계 결과(`StageAResult`·`StageBResult`)에 객체째 실린다 | S0 수준 필드(§2.4.2). 단계 결과는 S0 수준 스냅샷 참조만 넘긴다 |
| `SsEvaluation` | `ss`·`dc` `MetricBundle`(`E/metrics/ss_types.py:79-88`) | `lineage`(스냅샷)만 둔다. metric은 `graph/metrics` 필드에서 읽는다 |
| `EvalResult` | `objectives`, `constraints`, `unmeasured`, `warnings`(`E/search/search_values.py:146-162`) | (평가 키, 색인 항목, 보존 중이면 스냅샷). 목적 값과 분해능은 `metrics_dc` 필드에서, 제약 행은 `graph/metrics: constraint_rows`에서 읽는다. 스냅샷을 놓았으면 색인 항목(S3 기록)에서 읽는다. ε 행은 풀이 매개변수라 필드가 아니다 |
| `Objectives`(search) | `gate_area_m2`(Σ dc_op W·L), `power_resolution_w`(b_P)를 search가 다시 계산한다(`E/search/objectives.py:12-14,31-45`) | `metrics_dc`가 `gate_area_m2`와 새 필드 `power_resolution_w`(읽기: `dc_gm`, `dc_tol_v`, `dc_current_basis`, `dc_rail_v`)를 쓴다. search의 재계산(`_power_resolution`)을 지운다 |
| `LayoutResult` | `devices`, `groups`, `rows`, `floorplan`, `diffusion`, `w_requests` 등과 별도 lineage `snapshot`(`E/layout/contract_output.py:366-387`, `E/layout/run.py:109`의 `GraphSnapshot.empty(LY_WRITERS)`) | 레이아웃 필드는 그 **설계점 스냅샷**의 S2 `layout` 필드다. 별도 lineage는 없다. 레이아웃 재시도는 같은 설계점 lineage의 새 스냅샷이다. `LayoutResult`는 (스냅샷, 이번 호출의 계산 블록 목록)만 둔다 |
| `LocalSeal` | `snapshot_fragment`, `gain_db`, `power_w`, `area_m2`(`E/sizing/size_and_seal_local.py:119-129`) | 국소 스냅샷(41 §5.3.9). 봉인 통과·실패 레코드는 봉인 필드, 국소 전력·면적·gain·Z_out은 블록 범위 metric 필드(§2.4.8) |
| 수동소자 값 | `passive_values()`를 부를 때마다 다시 만든다(`E/metrics/passive_values.py:16-31`의 호출처 `ss_evaluate.py:96`, `E/convergence/converge_point.py:49`). 봉인 아닌 점은 `kernel.py:146-150`이 같은 규칙을 다시 적는다. `sctx.spec_passive_values`(`search_context.py:206-207`)도 있다 | S2 필드 `device.passive_value`(§2.4.8). 영점 상쇄 R = 1/Σ`dc_gm`(dc 단계 필드)이라 봉인 전에도 정의되고, `kernel.py:146-150` 사본과 '봉인 아닌 점은 값 없음' 분기를 지운다 |

**SearchContext 칸 배정**(Q5, design 기본안(최종 승인에 포함)):

| as-built 칸 | 갈 곳 |
|---|---|
| `dc` | 참조: S0 수준 스냅샷 뿌리 + LUT memo(위 `KernelContext` 행) |
| `domain`(`SearchDomain`: 변수·상자·원뿔·묶음·W_min·격자·면적 분해능) | S0 수준 필드 `graph/kernel: search_domain`(writer `search_domain`, 읽기: θ 스키마·S1·PDK 선언·spec θ 범위·면적 예산·untie) |
| `settings` | spec 참조(실행 설정) |
| `context_fp`, `schema_fp`, `code_fp` | S0 지문과 §2.4.3 키에서 읽는다(사본 없음) |
| `element_values`, `spec_passive_values` | 수동소자 값 필드(S2) |
| `judged_constraints`, `ss_constraints`, `constraint_notes` | S0 수준 필드 `graph/kernel: constraint_classes`(spec 제약의 목적 축·ss·미측정 분류, writer = 제약 분류 블록, 읽기: spec·metric 등록부 지문) |
| `junction`(`JunctionSource`), `mismatch`(`MismatchSource`) | S0 수준 필드 `graph/kernel: junction_source`, `mismatch_source`(PDK 선언·LUT 생성 규칙 선언의 파생) |
| `driving` | spec 참조(`spec.driving_spec`, 파생 없음) |
| `area_decl` | S0 수준 필드 `graph/kernel: passive_area_decl` |
| `model_error` | S0 수준 필드 `graph/kernel: model_error`(오라클 대조 결과는 spec `derived.model_error_*` 선언에서 온다) |
| `structure`, `noise_decl`, `s1v`, `ach`, `start` | S0 수준 필드(§2.4.8) |
| `spec` | 참조 |
| `archive` | S3 경로 참조(색인이 소유) |
| `cache`, `disk_failures`, `computed_keys`, `local_seal_memo` | S3 메모리 색인 |
| `cell_floors` | LUT memo(§2.4.6) + `dc_self_referential` 필드 |
| `counters`, `eval_times`, `seq`, `eval_budget`, `eval_budget_source`, `deadline` | 실행 계수(`core/run_counters.py`) |

#### 2.4.8 필드 소유표

graph 밖에 있던 값마다 갈 곳을 정한다. '층'의 S0 = S0 수준 층, B = 단계 B 층, S2 = 설계점 층, L0 = 층 0 층이다. 이 표에 없는 graph 밖 설계 값이 발견되면 같은 방식으로 행을 더한다(G-8 위치 검사가 찾는다). §2.4.7의 `KernelContext`·`SearchContext` 칸 배정도 이 표의 일부다.

| 값(as-built 위치) | 필드(kind/key: field) | writer(계산 블록) | 층 |
|---|---|---|---|
| S1v 전체(`sctx.s1v`, `StageAResult.s1v`) | `graph/s1v`: `views`, `blocks`, `composite_blocks`, `pole_nodes`, `loops`, `cuts`, `coverage`, `findings`, `l_classes`, `applied_facts` | `build_s1v`(GB2) | S0 |
| 자기동형 궤도·d/s 맞바꿈 부호(§6) | `graph/s1`: `orbits`, `current_symmetry` | graph 대칭 블록 `s1_symmetry`(`graph/s1_symmetry.py`, §6) | S0 |
| 구조 색(정준 순서, as-built master writer = sizing `dc_struct_colour`, `E/sizing/struct_colour.py:20`) | `device: dc_colour`, `node: dc_colour` = (`wl`, 정준 위치) 쌍의 정렬 순위(정점마다 유일, 이름 무관) | graph 대칭 블록 `s1_symmetry`(graph/s1, §6). sizing·search·metrics는 읽기만 한다 | S0 |
| 결합 변수 y, 기둥↔블록 매핑(보고서에만 있음, `E/pipeline/stage_a.py:101-121`) | `graph/coupling`: `vars`, `column_block_map`, `bias_columns` | `coupling_vars`(GB3) | S0 |
| GB4 `Achievability`(`sctx.ach`, `StageBResult`) | `graph/ach`: `curve_checks`, `gain_checks`, `area_bound`, `headroom_rows`, `verdict`, `block_bounds`(블록 키 순 tuple). `dof`는 **구조 DOF만**(41 A7) | `achievability`(GB4, 41 A4~A7) | S0 |
| 층 0 정의역 상한 A_i,max^L0(41 A9, §4.2) | `graph/ach: block_bounds_l0` | `block_bounds_l0`(41 A9) | S0 |
| 결합 잔차 분포 r̂(41 B1) | `graph/stage_b: residual_probe`(r̂, r̂_spread, 표본) | `residual_probe` | B |
| 수치 rank(41 B2) | `graph/stage_b: dof_numeric` | `dof_numeric` | B |
| 출발 구간 `StartIntervals`(`sctx.start`) | `device`: `start.row`(`StartRow`), `start.point`(옛 `CurveBook.points`). `graph/start`: `kvl_model`(쓰기 계획·고정 전위·종속 소자·의존 묶음, 41 §6.7), `kvl_rows`(선택점 행 표), `records`(`kvl_adjusted`·`kvl_macro_recheck`·`kvl_unsatisfied` 등 기록), `conflicts`(`StartConflict`), `inactive`(비활성 경계와 사유), `noise_inputs`(β·C_eff 입력, 41 §7.5), `macro`(`MacroResult`), `rungs`(출발 사다리 칸 tuple -- 칸 0 = 선택점, 정의는 41 §6.1-9), `placement`(as-built `Placement` -- 사다리 칸마다 θ 배치, 정의는 41 §6.1-9) | `start_intervals`(41 §6, A8) | S0 |
| metric 구조 입력 `metric_structure(s1v)`(`sctx.structure`) | `graph/s1v: metric_structure` | `metric_structure`(MOD5) | S0 |
| 잡음 입력 셀 `noise_decl(spec, s1v)`(`sctx.noise_decl`) | `graph/s1v: noise_input_cells` | `noise_decl`(MOD5) | S0 |
| 1변수 writer 집합(`sctx.cell_floors[("one_var_writers",)]`) | `device: dc_self_referential` | 쓰기 계획 블록(sizing) | S0 |
| 블록 국소 모델 입력 `LocalInputs`(`achievability.py:77-113`, `iv_context.py:63-69`에서 두 번) | `graph/ach: local_inputs` | `achievability`(GB4). 출발 구간이 같은 필드를 읽는다 | S0 |
| 커널 컨텍스트 구조 파생(`KernelContext.schema`·`fixed_values`·`resistor_values`·`l_ties`) | `graph/kernel`: `theta_schema`, `fixed_values`, `resistor_values`, `l_ties` | `build_kernel_context`를 블록으로(sizing) | S0 |
| `SearchDomain`, 제약 분류, 접합·mismatch 출처, 면적 선언, 모델 오차 | `graph/kernel`: `search_domain`, `constraint_classes`, `junction_source`, `mismatch_source`, `passive_area_decl`, `model_error` | 각각 search·metrics의 S0 블록(§2.4.7 표) | S0 |
| 수동소자 값(spec ∪ θ ∪ 영점 상쇄 R = 1/Σ`dc_gm`) | `device: passive_value` | GB5 수동소자 블록(`passive_values`를 블록으로). 엔진·오라클 입력(U16)·레이아웃 어댑터가 이 필드를 읽는다 | S2 |
| tol_I의 gm(`dc_gm_bound`, S2p 의존, `E/sizing/seal_tolerances.py:36-45`, `E/sizing/kernel_run.py:51-96`) | `device: dc_gm` = ID × (그 동작점의 LUT gm/ID) | `dc_tolerances`(dc 단계, writer 1개). 봉인 3·`ss_dev`·b_P·수동소자 R이 읽는다(§3.7-3) | S2 |
| 게이트 면적·전력 분해능(search가 다시 계산, `E/search/objectives.py:31-45`) | `graph/metrics`: `gate_area_m2`, `power_resolution_w` | `metrics_dc` | S2 |
| 제약 행(`EvalResult.constraints`) | `graph/metrics: constraint_rows` | search 제약 블록. **U17 단계 ②로 이월**(①-c 범위 밖). 미측정(`EvalResult.unmeasured`) 값의 자리는 미정 -- ② design 보완 때 정한다(§2.4.12 Q8) | S2 |
| 레이아웃 결과(`LayoutResult` 값들, 별도 lineage) | S2 `layout` 필드(as-built `E/layout/_ly_fields.py` 필드 이름 그대로) | MOD7 블록 | S2 |
| 레이아웃 파생 값(`review_needed`·`devices`·`coverage`·`w_requests`·`w_invariant_ok`·`revalidation`) | **필드 아님**. 반환값 함수 `layout_outputs(snapshot)`이 S2 `layout` 필드에서 그때 만든다(사용자 결정 2026-10-12 "4번 권고대로", (A)). U16 결과 JSON이 설계점마다 한 번 부르게 배선하는 것이 U16 완료 조건이다(42 D-LY5). U16 전까지 프로덕션 호출처 0(test만)은 사용자 승인 | -- | -- |
| 국소 봉인 결과(`LocalSeal`) | 국소 스냅샷의 봉인 필드(as-built 봉인 항목 필드 그대로) | 봉인 블록 | L0 |
| 블록 범위 국소 metric(41 §5.3.9: 국소 전력·면적·gain, rout 모드 Z_out) | `graph/local`: `power_w`, `area_m2`, `gain_db`, `z_out_ohm`. key = `local:<블록 키>`(분할 = 그 블록이 덮는 기둥) | 국소 metric 블록(MOD5, 봉인 통과 점에서만) | L0 |
| 층 0 매크로 풀이 결과(41 §5.3.6, `macro_solve(..., node_c, gm_bounds, gain_targets)`) | `graph/layer0: macro`(`MacroResult`). 입력 버전 = (`node_c`, `gm_bounds`, `gain_targets`, gm_id, lengths)를 extras로 넣은 투영 지문 | `layer0_macro` 블록(search) | L0 |
| `comp_approx_gap`(41 §5.5) | `graph/layer0: comp_approx_gap` = {approx: 극점·영점 목록·UGF·PM, mna: 극점·영점 목록·`ugf_ss_hz`·`pm_ss_deg`, gap: (ugf [Hz], pm [deg]) 스칼라 차} | `layer0_assembly_record` 블록(조립 스냅샷) | L0 |
| L-3 회차 기록(41 §5.3.2·§5.3.9: 회차 r의 예산·고정 입력 지문·푼 (bin, 고정 입력 지문) 쌍·조합 front·멈춤 사유) | `graph/layer0: rounds`(회차 순 tuple) | `layer0_budget` | L0 |
| 국소 봉인 결과 캐시(`sctx.local_seal_memo`) | 없음. 국소 스냅샷 + S3 색인 `local`·`solved`(§2.4.5) | -- | L0 |
| 평가 캐시·실패 캐시·계산한 키 집합(`sctx.cache`·`disk_failures`·`computed_keys`) | 없음. S3 메모리 색인 | S3 기록기 | (b) |
| `cell_floors` 칸 하한, `CurveBook` LUT 파생, `ParamTables`, `edge_costs`, `tol_cells`, `solve_self` 근 | 없음. LUT memo 함수(§2.4.6) | -- | (a) |
| `counters`, `eval_times`, `seq`, `eval_budget`, `deadline`, 블록 계수 | 없음. 실행 계수 | 계수 API | (c) |

#### 2.4.9 G-10 중복 계산 계수와 test

결정 4절이다. 시간은 판정에 쓰지 않고 계수만 쓴다(WP-23).

**계수의 소유**(M8): 실행 하나에 `RunCounters` 하나(`core/run_counters.py`)가 모든 계수와 그 증거 집합을 가진다. 계산 블록 객체(`ComputeBlock`)는 상태가 없다: as-built `_calls`·`_reuses`·`_computes`·`_recomputes`·`_seen_inputs`(`E/core/compute_block.py:67-71`)를 지우고, 호출이 `counters`를 인자로 받는다(§2.4.4 API). 다른 곳의 증거 상태도 옮긴다.

| 증거 집합 | as-built | 상한(실행 평가 수로) |
|---|---|---|
| 블록·분할별 계산한 입력 버전 | `ComputeBlock._seen_inputs`(모듈 수준 블록 객체에 실행을 넘어 남는다) | ≤ Σ_블록 분할 수 × (E_total + 1) (+1 = S0 수준 계산 한 번) |
| 퇴출된 memo 키 | `BoundedLRU._evicted`(`E/core/bounded_lru.py:38,58-65`) | ≤ 그 영역의 퇴출 수(U-60 결정 (가): point·curve·root 미적중 수 이하) |
| 디스크 파생표 사건 | `TableCache.events`(`E/lut/table_cache.py:195-228`, 끝없이 늘어나는 tuple) | ≤ 슬라이스 수 × 파생 표 종류 수 × 사건 종류 수 |

**E_total**(이 문서의 유일한 정의): 실행 하나의 커널 평가 수 상한 = E_B(외층 평가 예산, §3.6) + N_T(층 0 평가 예산, 41 §5.8). 이 문서의 다른 곳과 41은 이 정의를 인용한다.

`RunCounters`는 실행 경계에서 새로 만든다(as-built `reset_stats`를 대체). 실행 계수는 graph 밖 (c)이다. **API**(바꾸는 길은 이것뿐):
- `record(block, part, outcome, input_version)`: outcome ∈ {`reuse`, `graft`, `compute`}. `compute`면 (block, part, input_version)이 이미 있었는지 보고 `recomputes_same_input`을 센다.
- `evicted(region, key)`, `recomputed(region, key) -> bool`: LUT memo가 퇴출·재계산을 알린다.
- `table_event(event, fn_name)`: 디스크 파생표 사건.
- `count(name, n=1)`: 그 밖의 이름 있는 계수(평가 수, 색인 적중 등).
- `snapshot() -> PerfCounters`: 불변 값으로 내보낸다(결과 JSON `perf`). 읽기는 이것으로만 한다.

**계수**(결과 JSON `perf`, D0 계측 형식에 더한다):
- (블록, 분할)마다: `calls`, `reuses`(같은 lineage), `grafts`, `computes`, `recomputes_same_input`. 마지막은 실행 안에서 이미 계산한 (블록, 분할, 입력 버전)을 다시 계산한 수다.
- 의도적 재계산은 `computes`에 들어가되 원인을 나눠 센다: `fd_step`(θ가 다름), `regenerated_from_prior_run`(§2.4.5).
- LUT memo: 영역마다 `hits`, `misses`, `evictions`, `recomputes_after_eviction`(as-built `LruStats`), 상한 B_r의 항.
- S0 수준 스냅샷: `hit`, `miss`, `corrupt`. S3 색인: `hits`, `fail_hits`, `kernel_calls`, `outside_domain`, `regenerated_after_release`.

**판정**(FAIL 조건):
1. 실행 안에서 (블록, 분할)마다 `recomputes_same_input` = 0.
2. 같은 S0로 두 번째 실행하면 S0 수준 블록의 `computes` = 0(모두 `reuses`).
3. LUT memo `recomputes_after_eviction` = 0(U-60 결정 (가), "U-60은 (가)로"). `evictions`는 보고만 한다.
4. 층 0 조립점 평가에서 공유량이 닿지 않는 분할의 `computes` = 0(모두 `grafts`).
5. as-built `recompute_same_key`(`E/search/kernel.py:120-121`)는 S3 색인 `get` 적중 판정으로 대체되며 0이어야 한다.
6. `regenerated_after_release` = 0(§2.4.5 Q4 기본안).

**test**(R26에 따라 패키지 폴더 체계를 따르고, 9회로 실행은 `E/tests/integration/`):
- `test_g10_no_recompute_9circuits`: 9 library 회로 각각 층 0 + 외층을 짧은 평가 예산으로 실행해 판정 1·3·4·5·6을 단언한다.
- `test_g10_second_run_s0_zero`: 같은 S0로 두 번 실행해 판정 2를 단언한다. 두 번째 실행의 S0 수준 스냅샷 결과 `fp`가 첫 실행과 같다. 판정 2는 `RunCounters`의 블록 `computes`를 읽으므로 **U17 단계 ②**의 test다(§11 U17 표). 단계 ①에서는 단계 A 보고서 `s0_snapshot` = `hit`과 `fp` 동일만 `test_s0_snapshot_roundtrip`이 본다.
- `test_graft_equals_compute`(국소(`fixed` extras) → 조립 경로 포함: 두 블록 toy에서 각 블록을 이웃 값 `fixed`로 국소 봉인한 스냅샷을 원천으로 조립하면, 비공유 분할은 전부 이식되고 결과 `fp`가 빈 lineage 전체 계산과 같다), `test_graft_donor_order_invariant`, `test_partition_scc_not_split`(SCC가 두 기둥에 걸친 toy에서 한 분할): §2.4.4 불변식.
- `test_s0_snapshot_roundtrip`: 직렬화 → 읽기 → `fp` 비트 동일. 손상 파일은 재계산 후 같은 키로 교체. 등록부 밖 타입은 거부.
- `test_lut_memo_single_instance`: 실행 하나에서 만들어진 `LutMemo` 인스턴스 수 = 1(생성 계수).
- `test_lut_memo_purity`: lambda·중첩 함수·`lut` 밖 함수를 `call`에 주면 `TypeError`.

#### 2.4.10 강제 장치 (G-8, 사용자 승인 2026-10-12)

네 가지다. G-10(§2.4.9)이 그 위의 보강이다. 구조 규칙 A~I의 정의 파일은 `E/tests/structure/structure_checks.py`이고(EP-3), 여기서는 확장 내용만 적는다.

**① 구조 규칙 G 확장**. as-built 규칙 G는 모듈 수준 가변 대입, `lru_cache`·`cache` 데코레이터, `global` 문만 본다(`structure_checks.py:880-920`, 상수 :55-61). 다음을 더한다.

| 검사 | 거부 대상 |
|---|---|
| 인스턴스·클래스 속성 캐시 | 메서드 안 `self.<a> = {}`·`[]`·`set()`·`dict()` 등 가변 컨테이너 대입, 클래스 본문의 가변 컨테이너 속성 |
| dataclass 기본 컨테이너 | `field(default_factory=dict/list/set)` |
| `cached_property` | 데코레이터 |
| `lru_cache` 호출형 | `functools.lru_cache(...)(f)`, `cache(f)` 같은 호출 |
| 모듈 수준 캐시 객체 | 모듈 수준 `BoundedLRU(...)`·`LutMemo(...)`·`OrderedDict()`·`WeakValueDictionary()` 등 |
| `id(` 호출 | 허용 모듈 밖의 모든 `id(...)` 호출(쓰임과 무관하게. as-built 실측 tests 제외 0건) |
| memo 호출 형식 | `memo.call`의 첫 인자가 모듈 수준 이름이 아님(§2.4.6) |

**허용 모듈 목록**(고정, 이 밖은 예외 없음):
- core graph 모듈: `core/graph_snapshot.py`, `core/compute_block.py`, `core/projection.py`, `core/graft.py`, `core/field_value.py`, `core/graph_record.py`, `core/writer_table.py`, `core/type_registry.py`
- LUT memo와 디스크 캐시: `lut/lut_memo.py`, `lut/table_cache.py`, `core/bounded_lru.py`
- S3: `search/archive.py`, `search/s3_index.py`
- S0 스냅샷 영속화(§2.4.1 (d)): `core/snapshot_codec.py` -- U-68 정리의 프로세스당 1회 표시 `_CLEANUP_STARTED`(모듈 수준 1비트, 값 캐시 아님, §2.4.3) 하나만
- 실행 계수 모듈 하나: `core/run_counters.py`(신규)

목록에 넣지 않는 것과 이유:
- `lut/sweep_memo.py`: 단계 ③에서 지운다(§2.4.6). 남아 있는 동안에도 허용하지 않는다.
- `core/fingerprint.py`: 상태가 없다(as-built에 캐시·가변 속성 0). 목록에 넣을 이유가 없다.

as-built 실측(bd19cc6, tests 제외) 확장 검사에 걸리는 곳은 다음과 같다. 단계 ③(§11 U17)이 전부 해소한다.
- 속성 컨테이너: `graph/blocks.py:65-67`, `layout/pattern_select.py:116`, `layout/rows.py:80,86-87`, `metrics/block_param_tables.py:25-26`, `metrics/ss_metrics.py:102`, `search/iv_curves.py:37-40`, `search/macro_poles.py:92-95`, `search/search_context.py:65-66,84`, `sizing/block_columns.py:149,171,177-178`
- `default_factory`: `layout/euler_graph.py:19`, `layout/mirror_trail.py:46`
- `cached_property`: `layout/_helpers_alias.py:28,32,36`
- 계수 상태: `core/compute_block.py:67-71`, `core/bounded_lru.py:38`, `lut/table_cache.py:199`(허용 모듈이지만 §2.4.9에 따라 `RunCounters`로 옮긴다)

한 함수 호출 안에서 만들고 버리는 작업 객체(그래프 탐색 중간 상태 등)는 캐시가 아니다. 그런 클래스는 허용 목록이 아니라 구조로 고친다. 상태를 함수 지역 변수로 옮기거나, 결과를 불변 값으로 돌려준다.

**② 설계 값 타입 위치 검사**(AST): 설계 값 타입 = §2.4.3 타입 등록부(`core/type_registry.py`)에 등록된 필드 값 형식이다. 검사는 실행 시 등록부를 `pipeline`처럼 채운 뒤(모든 패키지 import) 그 이름 목록으로 소스 AST를 훑는다. `_module_map` test는 등록부를 읽기만 한다. 허용 모듈 밖에서 다음을 거부한다.
- **주석**: 인스턴스 속성·클래스 속성·dataclass 필드·모듈 수준 이름의 형식 주석이 등록 타입이거나 등록 타입을 원소로 하는 컨테이너(`tuple[T, ...]`, `dict[K, T]` 등)인 것
- **대입**: 그런 자리(`self.<a>`, 클래스 본문, 모듈 수준)에 등록 타입 생성자 호출 결과나 그것을 원소로 하는 컨테이너 리터럴·컴프리헨션을 대입하는 것
- 제외: 원시 타입(숫자·문자열·bool·None)과 그 tuple, 함수 지역 변수, 반환값, 함수 인자, frozen dataclass 정의 자체(값 형식 선언 모듈)

**③ 계획 SC-a·SC-b lint**:
- SC-a 원시 대입: `object.__setattr__`은 core graph 모듈과 frozen dataclass의 `__post_init__` 정규화(as-built `metrics/records.py`, `metrics/mna_types.py`, `metrics/junction_cap.py`, `core/failure_record.py`, `authoring/topology_model.py`)에서만 허용한다. `GraphSnapshot`·`GraphRecord`·`FieldValue`의 속성과 `tables`·`block_versions`에 대한 대입·변경 호출은 core graph 모듈 밖에서 거부한다. 기존 IC9(`test_no_raw_duplicated_writes`, §10.3)와 같은 검사기를 쓴다.
- SC-b `setdefault`: 기본값 인자가 빈 리터럴 컨테이너나 상수가 아닌 `setdefault`(계산된 값을 '없을 때만' 넣는 형태)를 거부한다. 빈 컨테이너 그룹 묶기(`d.setdefault(k, []).append(x)`)는 허용한다. as-built 실측: `setdefault` 호출 147개 중 해당 16개(`convergence/place_layout.py:60`, `core/pdk_decl.py:283`, `graph/canonical_form.py:135`, `graph/composite_diode.py:103`, `graph/drive_kind.py:73`, `graph/feedforward_cells.py:224`, `graph/gvgs_cycles.py:75`, `graph/views.py:81`, `graph/view_analysis.py:163`, `layout/crossover.py:36,37`, `layout/diffusion.py:58`, `search/search_domain.py:144`, `sizing/writer_plan.py:78,148,151`). 단계 ③에서 각각 고치거나, 설계 값 재사용 건너뛰기가 아님을 보이고 허용 목록에 줄 단위로 근거를 적는다.

**④ 9회로 실행 test**: §2.4.9의 `test_g10_no_recompute_9circuits`가 ①~③의 정적 검사가 못 보는 실행 중 중복을 잡는다. 같은 실행에서 SearchContext·커널 컨텍스트의 도달 가능한 객체를 훑어 등록 타입 인스턴스가 graph 스냅샷·S3 색인 밖에 없는지도 확인한다(②의 동적 짝).

#### 2.4.11 tol_I 정정 요약

P N3.6 v6.4다. 상세는 §3.7-3에 있다. `device.dc_gm` 필드 하나를 dc 단계 블록이 쓰고, 봉인 3(tol_I = tol_V × 순환 블록 소자 gm 최댓값), `ss_dev`, 전력 분해능 b_P(`metrics_dc`의 `power_resolution_w`), 영점 상쇄 수동소자 R이 같은 필드를 읽는다. parent(S2p)에 의존하지 않으므로 같은 θ는 parent와 관계없이 같은 봉인 결과를 낸다.

#### 2.4.12 열린 질문과 기본안 (design 기본안(최종 승인에 포함))

design-validator 지적(2026-10-12)에 따라 기본안을 정했다. 사용자 승인 전까지 이 기본안으로 적는다.

| # | 질문 | 기본안 |
|---|---|---|
| Q1 | P N3.3 S0 지문 목록에 PDK 선언 파일 해시가 없었다(출발 구간·면적 선언·접합 출처가 PDK 선언을 읽는다) | 계획 N3.3 S0 행에 PDK 선언 파일 내용 해시를 더했다(v6.4). §2.4.3 키 (i)에 들어간다 -- **결정**(사용자 결정 2026-10-12 "K-2 권고대로, GQ1/GQ3/GQ4, U-14,U-20,U-32,U-45 권고대로")(GQ1, U-72) |
| Q2 | 키가 다른 옛 S0 수준 스냅샷 파일의 정리 | **결정**(사용자 결정 2026-10-12 "GQ2, N1, N3, K2 권고대로")(U-68): 승인된 tol_V 캐시 정리와 같은 방식으로 쓰기 시점에 1회 삭제(삭제 코드 허용). 어떤 checkout으로도 재현할 수 없는 키만 지우고, 실패하면 아무것도 지우지 않는다 |
| Q3 | 층 0 국소 스냅샷의 보존 | §2.4.5 보존 표의 '층 0 단계(모든 회차)'와 '외층 시작점 대기열' 소유자(M9) -- design 기본안(최종 승인에 포함) |
| Q4 | 놓은 스냅샷의 θ를 다시 기준점으로 쓸 때의 재계산 | 같은 실행에서 만든 θ의 재생성은 FAIL. 이전 실행 S3 점에서 시작하는 것은 허용하고 따로 센다(§2.4.5) -- **결정**(사용자 결정 2026-10-12 "K-2 권고대로, GQ1/GQ3/GQ4, U-14,U-20,U-32,U-45 권고대로")(GQ3, U-73) |
| Q5 | SearchContext의 선언 파생 입력 | §2.4.7 'SearchContext 칸 배정' 표 -- design 기본안(최종 승인에 포함) |
| Q6 | LUT memo 상한·퇴출 판정 | **결정**(사용자 결정 2026-10-12 "U-60은 (가)로"): §2.4.6 (가) |
| Q7 | tol_I가 자기 동작점 gm으로 바뀌면 b_P와 봉인 3 판정이 바뀐다 | 단계 ①에서 9회로 front를 다시 재고, 봉인 3 판정이 바뀐 점(옛 상계로 통과·새 gm으로 거부, 또는 반대)을 회로별로 기록한다 -- **결정**(사용자 결정 2026-10-12 "K-2 권고대로, GQ1/GQ3/GQ4, U-14,U-20,U-32,U-45 권고대로")(GQ4, U-74). **측정 완료(①-c)**: 결과는 history에 기록했다 |
| Q8 | `graph/metrics: constraint_rows`(§2.4.8)에서 미측정(`unmeasured`) 값의 자리 | **열림**: U17 단계 ②로 이월하면서 ② design 보완 때 정한다(①-c 구현에서 드러남). 정하기 전에는 `constraint_rows`를 쓰지 않는다 |

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
| 옛 이름 거부 | DEV: topology에는 `legacy_name` 표가 없다(닫힌 어휘로 대신 거부). topology `ports.direction`을 필수로 받는다(`E/authoring/ports.py:22,57-59`). spec 정본 이름 `input_dc_net`·`topology_hash`·`derived` 거부는 U5에서 고쳐졌다(bd19cc6 `_spec_fields.py:28`). **설계(사용자 승인(2026-10-12 P), P-4)**: (1) `ports`는 topology에만 있다(P N3.16 v6.5, N3.15 정정). spec의 `ports`는 위치가 틀린 필드로 거부한다 (2) 포트 방향은 role에서 유도한다(입력 role → input, 출력 role → output). `direction` 키는 흡수된 옛 이름이라 `SchemaRejectedError`로 거부한다(필수 아님). role 어휘 밖이라 방향을 유도할 수 없는 포트는 `port_role`로 거부한다 (3) 옛 이름 표는 같은 파일의 정본 이름과 겹치지 않는다: 로더 test가 두 집합의 교집합 = ∅를 단언한다 | `E/authoring/_spec_fields.py:28-36`, `E/authoring/ports.py:22-70`, `authoring/CONTRACT.md:151-152,201` |
| 문자열 값 안 옛 이름(P N3.16) | `tests/authoring/test_old_names_in_string_values.py`: library spec·topology의 **모든 문자열 값**(예 `value_from_spec: "PM_target_deg"`)을 훑어 옛 이름 표 원소가 0개임을 단언한다(키 검사는 로더가 하고 값 문자열은 이 test가 한다) | MISS | -- |
| `human.objective` 형식(P N3.15·DEC-77) | as-built 형식 `objective.budgets[{axis, value, source}]`(axis ∈ `OBJECTIVE_AXES` = `power_dc_w`·`area_search_m2`, `E/authoring/spec_settings.py:62`)이다. 최적화 축은 (전력, 면적)으로 고정이라 이 필드는 축 선택이 아니라 선택적 축 예산이다. 결정 11로 면적 예산은 판정 제약 `area_search_m2 <= 값`으로도 선언되므로, 같은 축의 예산이 두 곳에 있으면 로더가 `duplicate_axis_budget`로 거부한다(FR-9 개념 하나·위치 하나). 예산이 없으면 front를 내고 정지한다(DEC-77) | PART | `E/authoring/spec_settings.py:62` |
| spec `origin`(U-04, P N3.15 `meta.origin`, SC-d) | **결정**(사용자 결정 2026-10-12 "U-04 권고대로"): `meta.origin` ∈ {`canonical`, `fixture`} 필수, 없으면 로더 거부(`SchemaRejectedError`). `fixture` spec은 자기 지문을 선언하고 정본 유도 임계값(canonical spec의 `_derived`·`value_from_constraint` 대상)을 읽지 않는다 -- 참조하면 로더 거부 | MISS | -- |
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
   | `l_owner`(신규, C-3 사용자 결정 2026-10-12 "7절 권고대로") | L 동치류 대표 멤버 목록(동치류 멤버 이름 정렬 JSON 배열) | 주인 소자 이름(그 동치류 멤버) | override(41 §1.12.5 주인 규칙 1~4를 덮음. 주인이 멤버가 아니거나 subject가 엔진 유도 동치류와 다르면 `structure_fact_mismatch`, 그 동치류가 없으면 `structure_fact_orphan`) | `E/graph/l_classes.py` |

   - 루프 id: 루프 뷰는 as-built 뷰 id `loop:<끊는 소자>:<끊는 넷>`이다. 루프 뷰가 아닌 사이클은 정준 회전(이름 정렬 첫 노드에서 시작)의 노드 이름 JSON 배열이다.
   - `<탭>`·`<merge>`가 넷 이름이므로 `feedforward_cell` value는 `->`로 잇는다. 넷 이름에 `->`가 들어 있는 topology는 로드에서 거부한다(`structure_value_ambiguous`).
   - **L 동치류 주인**은 기본적으로 41 §1.12.5 규칙의 산출이다. 구조 규칙이 이름 순서(`l_owner_name_order`)로만 가르는 동치류는 `l_owner` 사실이 덮는다(C-3). status·rule_hash 규칙은 다른 concept와 같다(`l_classes.py`가 `structure_rule_fp` 대상이다: S1V_RULE_FILES에 이미 있다). 회로별 주인은 사용자가 정한다(nmcnr {M104, M105} → M105, 사용자 결정 2026-10-12 "C-3은 네 제안대로 해").

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
   | sf_pushpull_output_opamp | `loop_role` | 복합 diode 내부 사이클 3개({N1,N5}, {N2,N7}, {N12,N13}; U1b 실측) | `composite_diode_internal` | confirm | D.6 |
   | sf_pushpull_output_opamp | `matching_pair` | `["M6","M8"]`, `["M5","M7"]`, `["R1a","R1b"]` | `branch_symmetric` | override | D.5 |
   | sf_pushpull_output_opamp | `drive_kind` | (사실 없음) | -- | **쓰지 않는다**(사용자 결정 2026-10-12 "1, 가로 해", C-1 보완 (가)). 41 §1.5-4 규칙이 N17·N20 = `voltage`(근거 `follower`, M18·M19), N910·N1112·N1516 = `current`(근거 `cascode`)를 구조로 가른다. 9회로 발동표가 예상 집합과 다르면 사실로 메우지 않고 구현을 멈추고 보고한다 | D.6, J12-b, C-1 |
   | nmcnr_amplifier | `l_owner` | `["M104","M105"]` | `M105` | override -- **결정**(사용자 결정 2026-10-12 "C-3은 네 제안대로 해"). 근거: M104·M105는 folding 노드 NMOS 전류 싱크(gate 공통)이고, 주경로 Vin_p→M103→NodeF2→M107→NodeM2에서 F2 쪽 M105의 ro가 1단 R_out ≈ gm107·ro107·(ro105‖ro103)로 gain을 직접 정한다(J-F '주인 = 주경로 신호 소자'와 같은 취지). 사실 파일은 `l_owner` concept 구현(U1b structure 사실) 뒤 쓰고, 단계 A의 `l_owner_name_order` review가 사라지는지 확인한다 | C-3 |

   **사실 파일 상태**: 파일럿 `current_reuse_telescopic_ota.structure.json`(`ac_ground_exception` Vbias2, C-6 사용자 결정 2026-10-12 "7절 권고대로")은 별도 브랜치에서 작성 중이다. 단계 A 통과를 확인하고, 사실이 더 필요하면 다시 승인을 받는다. **`rule_hash` 재기록**(사용자 결정 2026-10-12 "2번 승인.", approval_id `user_decisions 2026-10-12 C-6 재확인`): 사실 내용은 바꾸지 않고 `rule_hash`만 새 `structure_rule_fp()`로 갱신한다. 시점 = ①-d의 마지막 규칙 변경(41 §1.5-4 C-1 보완 (가)·§6-3 전류 기저 열 순서 규칙 반영) 뒤 한 번. 갱신 뒤 파일럿 단계 A의 Vbias2 판정이 갱신 전과 같은지 확인해 보고한다. 달라지면 갱신하지 않고 사용자에게 다시 묻는다. 나머지 회로의 사실 파일은 위 표대로 U1b 병합 뒤 쓴다. nmcnr 파일에는 `l_owner` 사실(subject [M104, M105], value M105)이 들어가고, 쓴 뒤 nmcnr 단계 A 보고서에서 `l_owner_name_order` review가 없어져야 한다. 같은 패턴(전류원 멤버 동률)이 다른 회로에서 나오면 규칙 '동률이면 drain이 주경로 노드인 멤버'로 일반화한다(같은 결정 기록).

**`budget_ref` 엣지는 없다**(P DEC-55·N3.3 S1·N3.16, 사용자 결정 2026-10-12 "다로 해"). 옛 topology 선언 `budget_reference_device`(소자 X의 VDS 예산 기준 소자 Y)의 역할은 S1 레일-레일 기둥(DEC-71 (1), 위 표 '가지·기둥', `E/graph/columns.py`: 레일 쌍 사이 가지 그래프의 모든 노드 단순 경로)이 흡수한다. 노드 전압은 변수 하나이므로 공유 노드 n에서 V(n) = V(레일_Y) ± |VDS(Y)|(Y가 아래 레일 쪽이면 +, 위 레일 쪽이면 −) 항등과 예산 (V_top − V_bot) − |VDS(Y)|는 X·Y가 함께 있는 기둥의 KVL 식에서 저절로 성립한다. 그 노드 변수를 누가 쓰는지는 쓰기 계획 규칙(writer 유일, 봉인 5, DEC-95)이 정한다(§3.7-8).
- topology·spec 키 `budget_reference_device`는 유도 입력으로도, 대조용 declared 엣지로도 읽지 않는다(U-50 lint, 예외 없음). `structure.json` concept 어휘에도 `budget_ref`는 없다.
- 노드를 공유하지 않는 옛 선언 4건(M61→M5, M68→M6, M38→M36a, two_stage_ota M4→M5)은 계획 J8 엔진 유도 항목 그대로다(§9.4).
- 근거 실측(오케스트레이터, master `a3987ab` `build_s1`, 2026-10-12, topology `device_roles`의 `budget_reference_device` 9건):
  - 옛 선언: 노드를 공유하는 옛 선언 5건(파일럿: M9a→M10 Vop1, M9b→M8 Vg15, M18a→M19 Vom1, M18b→M17 Vg25, M60→M66 Vbias4)이 **모두 같은 S1 기둥에 함께 있다(빠짐 0)**. M60은 source = vdd라 아래 29쌍 규칙 밖이지만 기둥 vdd-M60-Vbias4-M66-gnd에 함께 있다.
  - 별도 근거(구조 규칙 후보, 옛 선언 여부와 무관): 'X.source 비레일·X.drain = n 비레일이고, n을 drain으로 쓰는 레일-source MOS Y' 후보 29쌍(파일럿 16 / nmcnr 4 / folded·ngcc·two_stage·two_stage_sf 각 2 / common_gate 1 / pushpull·sf_pushpull 0)이 **모두 이미 같은 기둥에 함께 있다(빠짐 0)**. 예(nmcnr): 기둥 vdd-M101-NodeTail-M102-NodeF1-M104-vss와 vdd-M108-M106-NodeF1-M104-vss.

### 3.3 GB3 -- 결합 변수 y와 기둥↔블록 매핑 (MOD3)

**왜 필요한가**: 41 §5의 층 0 조립은 블록 국소 해들을 이어 붙이면서 블록 경계를 넘는 관계를 등식으로 풀어야 한다. 그 관계 목록이 y다. 따라서 GB3은 정밀 경로만의 기능이 아니라 기본 경로 조립의 입력이다(§8 R2).

**알고리즘**: S1v 블록(41 §1)과 S1 관계 엣지를 대조해 아래 레코드를 만든다.
- K1: 부하 소자가 다른 블록의 미러·L 동치류에 속함.
- K2: 블록을 가로지르는 `equal_vgs`.
- K3: 블록 경계를 넘는 `stacked_vsb`.
- K4: 공유 가지·기둥의 노드전압(매핑표의 공유 소자).
- K7: 여러 뷰가 공유하는 소자.
- K8: 측면 주입(J12-d 계획 기본안. ratify되지 않았다, §9.4).

각 레코드는 `CouplingVar{kind, members, blocks, domain, init_rule}`이다. 매핑표 `column_block_map{column, block, device, shared}`는 S1 기둥과 S1v 블록을 교차해서 만든다.

**불변식**:
- 어느 블록에도, 어느 바이어스 기둥에도 속하지 않는 소자가 있으면 정지한다(`StructureUnresolvedError`, 사유 `column_unassigned`, DEC-71 (2)).

**U10 as-built 보완**(2026-10-09 오케스트레이터 결정, 모두 이름 없는 구조 규칙):
- **바이어스 기둥 = 의사 블록**: 어느 블록에도 속하지 않는 소자만으로 된 기둥(바이어스 기둥)을 K1·K2·K4 판정에서 의사 블록 `bias:<기둥>`으로 센다. 기준 diode(바이어스 기둥)와 블록 소자 사이 미러·`equal_vgs`도 층 0 조립이 지켜야 하는 관계이기 때문이다(예: sf M3↔M4, ngcc M6A↔M7).
- **K3 정의**: 비레일 넷에서 MOS e의 drain과 MOS d의 source가 만나고 둘의 블록이 다르면 `stacked_vsb`(d의 VSB가 e의 VDS에 묶임). 9회로 0건.
- **K1 부하 역할 집합**: {load, mirror, diode_load, tail_source}. 다른 블록·바이어스 의사 블록에서 미러로 전류를 받는 꼬리 전류원도 K1이다(실제 블록과 의사 블록에 같게 적용). 표현은 `BlockRef(view, ("bias:<기둥 id>",))`.
- **K7 범위**: 동작점이 있는 소자(MOS)만 센다. 커패시터·저항은 값이 뷰마다 같아 나눌 것이 없다.
- 레코드에 `nets`(관계가 걸린 넷), 매핑표 행에 `basis`(`block_member`·`column_mate`·`bias_column`)를 더한다.
- `column_unassigned` 범위 = DC 가지에 든 원소. 커패시터·가지치기된 저항은 KVL이 없어 제외한다.
- 소비자는 U15 층 0 조립이며, 그 전에는 단계 A 보고서 `coupling`이 유일한 출구다.
- 관찰(U7로 넘김): 버퍼 블록은 부하 수동소자를 블록에 붙이지 않는다(출력 CL이 블록 멤버가 아님). 이득 블록과 규칙이 다르다.
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

**대상**: CM 분할(§5 `authoring.cm_partition`, `cm_sense_elements` 선언을 반영한 결과 하나만 쓴다 -- 같은 도달 규칙을 다른 모듈에 복사하지 않는다)이 감지(소비) 쪽으로 분류한 소자에 닿은 **자유 수동소자 전부(R·C)**. 자유 = θ 성분이고 값이 DC 동작점을 바꾸지 않는다: DC 전류 기저에서 가지치기되었거나, U2 `current_symmetry`가 **구조적 전류 0**으로 판정한 소자(예: 대칭 출력 사이 직렬 감지 저항 -- CM 동작점에서 양끝 전위가 같다). 2026-10-09 정정: 가지치기만으로 정의하면 결정 (b)의 대상(파일럿 R1·R2)이 빠져 형태 표와 충돌했다. 출력 넷에 직접 닿는지는 보지 않는다.

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

상수는 새로 두지 않는다. 허용 손실은 각 metric의 분해능이다.

**U11 test 후속 정의**(2026-10-09 오케스트레이터, 결정 (b)의 목적 = 출력 부하 최소화에서 유도):
- **감지 쪽 범위**: 감지 넷 = 레일·출력이 아니고 MOS gate만 걸리며 MOS channel이 닿지 않는 넷. 대상 = 감지 넷을 포함하는 **수동소자만으로 이어진 연결 성분**(channel이 닿는 넷에서 멈춤)에 든 자유 수동소자 전부. 그래서 출력과 감지 넷 사이 수동소자 중간 넷을 거치는 평균망(Ra·Rb·Rc)이 모두 대상이고, channel이 닿는 오차증폭 내부 넷의 커패시터는 대상이 아니다.
- **제거 극한에서 정의되지 않는 metric**: 소자를 없앴을 때 정의가 사라지는 metric(감지 넷이 DC로 떠서 PM·GBW가 미정, CM 루프가 끊겨 PM_cm 미정)은 그 소자의 손실 행에서 **그 metric만 뺀다**(소자 전체를 건너뛰지 않는다). 그 metric의 제약 만족은 4번 재판정이 지킨다. 남은 손실 행이 하나도 없으면 사유를 기록하고 원래 값을 둔다.
- **최소 면적 값**: 손실 경계의 근을 분해능 수준(그 소자 θ의 소신호 상대 분해능)까지 찾고, 근 위쪽 한 칸을 넘지 않는다. 소자 제거는 R → ∞·C → 0 극한으로 구현해도 되나, 그 값은 유도해 주석에 남긴다(as-built: R = √(float max)).

**면적 예산 출발점(as-built U11, 잠정)**: `fit_to_area_budget`이 예산을 넘는 시작점의 ln IDu를 모두 같은 Δ만큼 옮겨 예산 안으로 넣는다. 설계 정본은 41 §6.4 면적 상한으로 출발 구간을 자르는 것(U13)이며, U13이 들어오는 커밋에서 이 이동 방식을 지운다. 선언된 제약이 없어 분해능이 없으면 건드리지 않고 사유를 기록한다.

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
- **보상 단 폴백**(U-51, 사용자 결정 2026-10-12 "U-51은 (나)로"): 보상 단 gm/ID는 θ에 포함한다(DEC-04). 폴백은 **계수 기반**이다: 외층 SLSQP가 그 시작점의 반복 상한(as-built `slsqp_outer` 식 maxiter = Σ_i max(⌈log2(상자폭_i / FD 스텝_i)⌉, 1), `E/search/slsqp_outer.py:179-181`) 안에 수렴하지 못하면 그 시작점에서만 보상 단 θ를 GB5 규칙값(gm_req = DEC-92 MNA 1-D 근, §3.5)으로 고정해 한 번 다시 푼다. 폴백 사실과 이유(`compensation_fixed_fallback{start, reason: slsqp_maxiter}`)를 기록하고 그 점을 '추정'으로 표시한다. 벽시계·U-47 예산에 의존하지 않는다(결정론). 9회로 실행에서 폴백 빈도를 재서 보고한다.

**이 설계가 바꾸는 것**:
1. **예산 점**: 목적 예산이나 면적 예산 제약이 선언되면 그 값을 ε로 고정해 한 번 풀고, 그 결과를 front와 함께 낸다(DEC-77, U-13). 결정 11의 `area_search_m2 <=` 제약은 탐색 축 예산이므로 '면적 ε = 예산 값'으로 전력을 최소화하는 풀이 하나를 추가한다.
2. **제약·목적의 척도화**(§7.2): 행마다 판정 단위와 풀이 단위를 나눈다.
3. **시작점 출처**: 층 0 조립점(41 §5)과 출발 구간 후보(41 §6)를 맨 앞에 둔다. as-built `layer0_center`(θ 상자 중심 + 전류 Chebyshev 중심)는 블록 국소 문제의 기준점 생성기로 옮긴다(41 §5.9 상태). 시작점 출처를 대체하므로 WP-01에 따라 옛 경로를 지운다.
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
| DEC-88 ln IDu 연속 하한 | DEV: 1변수 writer의 칸 정점·전도 하한을 bounds로 조인다. 설계(사용자 승인(2026-10-12 P), P-7): 동작점 의존 연속 부등식 제약 행으로 바꾸고 bounds 조임을 지운다(§3.10.4) | `search/CONTRACT.md:573`, `E/search/cell_floor.py` |

### 3.7 GB7 -- DC 정본과 봉인 (MOD4)

**규칙**: P N3.4~N3.6. 평가 커널 = ② 전류 → ③ L → ④ 기둥·SCC → ⑤ W → 봉인 1~8. W_request가 있으면 그 소자의 W는 고정 입력이다(LY3).

**이 설계가 바꾸는 것**:
1. **L 동치류 공유**: §3.2-1을 따른다.
2. **미러 비율 강제**: `matching_ratio`(그룹의 W/L 비)를 전류 기저의 강제 관계로 넣는다(DEC-70). 비율의 출처는 θ 변수이며, 대칭 묶음(§6)이 같은 비율 1을 준다.
3. **tol_I**(v1.6 graph 정본 개정, 사용자 결정 2026-10-12 G-3' 승인, P N3.6 v6.4): tol_I = tol_V × 순환 블록 소자 gm의 최댓값이고, gm은 **후보 자기 동작점의 dc 단계 gm 필드 `device.dc_gm` 하나**를 읽는다. `dc_gm` = 그 소자 ID × 그 동작점(L, VGS, VDS, VSB)의 LUT gm/ID(`dc_op.gm_id`)이고 writer는 `dc_tolerances` 하나다. `ss_dev`(as-built는 `op.gm_id * op.current`를 따로 계산, `E/metrics/ss_linearize.py:70`), 봉인 3(`E/sizing/seal_kcl.py:35`), 전력 분해능 b_P(`E/search/search_values.py:123`)가 모두 이 필드를 읽는다. parent에 의존하지 않으므로 같은 θ는 parent와 무관하게 같은 봉인 결과를 낸다. 순환 없음: `dc_gm`은 ⑤ W 블록 뒤의 `dc_op`에서 계산하고 tol_I는 봉인 3에서만 쓴다(SCC 수렴은 tol_V를 쓴다). **폐기**: 옛 문언 'S2p `ss` gm, 첫 평가만 격자 최대 gm'과 as-built U4 경로(`previous_gm_id`·`inherited_gm_id`·`canonical_gm_id`, `E/sizing/kernel_run.py:51-96`, `gm_grid_max`, `dc_gm_bound` 필드). 수동소자 θ만 바뀐 자식의 DC 재사용은 parent 입력을 이어받는 특수 경로 없이 입력 버전 일치로 성립한다(`dc_gm`이 수동소자 θ를 읽지 않는다). 영점 상쇄 수동소자 R = 1/Σ`dc_gm`도 이 필드를 읽으므로 봉인 전 점에서도 정의된다(§2.4.7). **폐기하는 근거**: as-built의 '봉인은 어느 동작점에서나 안전한 상계(곡선 전체 최대 gm)가 필요하다'(`E/search/objectives.py:36-38`)는 쓰지 않는다. 봉인 3이 판정하는 것은 이 후보 동작점의 KCL 잔차이고, 그 허용오차의 gm은 이 동작점의 값이다(사용자 결정 G-3'). 판정 변화는 단계 ①에서 9회로로 재고 기록한다(§2.4.12 Q7).
4. **종속 소자 선택 DEC-95 (3)**: ratified 선택(`structure.json`)과 ② 'GB5 gm 요구·뒤 stage 독립'을 Kruskal 엣지 키 앞에 둔다. ②의 입력은 S1v stage 번호다.
5. **W4 초기값**: 층 0이 배분한 기둥 VDS를 쓴다(41 §5.3.4 (c) VDS 배분).
6. **DEC-12 diode 창**: diode 노드 창은 그 VGS를 공유하는 미러 멤버 전원의 W 한계를 함께 본다. 멤버 VDS가 아직 정해지지 않았으면 그 멤버의 포화 하한 = LUT `VDSAT` 열 보간 + tol_VDsat(DEC-88, 봉인 7과 같은 양)을 바닥으로 쓴다. 멤버의 L이나 ID가 정해지지 않았으면 창을 만들지 않고 `SealViolationError`(사유 `diode_window_member_undefined`, 멤버 기록)로 명시적으로 실패한다. 역할 라벨 바닥(`min_vds_by_role`, DF-20)은 쓰지 않는다.
7. **DEC-13 적층 diode**: `stacked_vsb`로 묶인 diode 두 개는 두 노드전압을 한 W2 블록에서 함께 푼다(2변수 고정점, 수렴·상한은 N3.6). 각 소자의 vsb는 DEC-61대로 그 순간의 노드전압과 bulk 넷에서 유도한다(두 bulk가 같으면 아래 vsb = 위 vsb + 위 vds가 그 특수형이다). 한 소자씩 차례로 풀지 않는다(DF-01 버전 혼재 방지: 두 소자의 W·gm은 같은 반복의 vsb로 계산된다).
8. **`budget_ref` 쓰기 경로 -- 폐기**(P DEC-55, N3.4 W1, N3.16; 사용자 결정 2026-10-12 "다로 해"; design 소관): `budget_ref` 엣지가 없으므로 그 로드·유도·쓰기 경로도 없다. 옛 선언 대상 노드 변수의 writer는 쓰기 계획 규칙(writer 유일, 봉인 5, DEC-95)이 정하고, 예산 관계는 기둥 KVL(§3.2 `budget_ref` 문단)이 낸다. topology·spec 키 `budget_reference_device`는 읽지 않는다(U-50 lint `TAG_ROLE_KEYS_U50`, 예외 없음).
   - **구현 단위 측정 의무**(이 항목이 걸린 구현 단위의 보고에 넣는다): **대상** = 노드를 공유하는 옛 선언 5건(파일럿: M9a→M10, M9b→M8, M18a→M19, M18b→M17, M60→M66). 나머지 8회로는 대상 0건으로 보고하고, 비공유 4건은 J8 소관이라 제외한다. 각 대상(X→Y, 공유 노드 n)에서 (a) 쓰기 계획에서 노드 n의 writer가 정확히 1개(티어·블록 기록), (b) X·Y가 같은 S1 기둥 id에 함께 있음, (c) |B_X − ((V_top − V_bot) − |VDS(Y)|)| ≤ tol_V(N3.6)를 재서 기록한다. V_top·V_bot = 그 기둥 양 끝 레일 전압, B_X = |V(n) − V(Y 반대쪽 끝 레일)|.
   - **as-built**: `E/graph/CONTRACT.md` 4.5의 "`budget_ref`(선언 전용)는 만들지 않는다"는 결과(엣지 없음)가 이 결정과 같다. 그 '선언 전용' 문구는 코드 쪽 정정 대상으로 42 후속 항목에 둔다.

| 항목 | 상태 | 증거 |
|---|---|---|
| W0~W4 writer 계획 | OK(W3는 9회로 모두 0. CI-15·18 대기) | `E/sizing/writer_plan.py` |
| SCC 고정점·K_max·NONCONVERGENT | OK(+ GS 실패 시 감쇠 Newton, Brent `bracket_root` -- master 병합됨) | `E/sizing/fixed_point.py:21`, `scc_newton.py:33` |
| 봉인 1~8 | OK(+ 계획에 없는 봉인 9 '전도 여유') | `E/sizing/seal.py:30` |
| tol_I | DEV(S2p gm/ID 또는 격자 최대 gm 상계. v1.6 정의 `dc_gm`과 다름) | `E/sizing/seal_tolerances.py:36-45`, `E/sizing/kernel_run.py:51-96`(bd19cc6) |
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
| LY4 L 혼합 행 대칭(U-67) | L이 섞인 interdigitation 행에서 소자마다 finger 위치가 행 중심에 거울 대칭인지 검사한다. 어긋나면 그 matching 그룹 `review_needed`(사용자 결정 2026-10-12 "U-67은 (나)로") |
| LOD 기하(U-67) | 출력 계약에 소자별·finger별 `ly.lod{device: ((sa, sb, sd), ...)}`를 넣는다. sa·sb = 그 finger gate 가장자리에서 행의 확산 끝(OD 끝)까지 거리(왼쪽·오른쪽), sd = 이웃 finger gate 사이 확산 길이. 행 배치(`row` finger 순서, `finger_pitch_overhead_m`, dummy 폭)에서만 계산한다(DEC-91 `ly.diffusion`과 같은 출처 하나). 엔진 판정은 이 값을 읽지 않는다(사용자 결정 2026-10-12 "U-67은 (나)로") |
| 판정 축 면적 | 수동소자 면적(MIM 배치 면적 = 값/밀도 + PDK 여유)을 포함 항목으로 넣는다. 지금은 MOS 행만 들어간다 |

**MOD8 `convergence`**(U14 구현 2026-10-09, 계약 `E/convergence/CONTRACT.md`; U16 배선 대기). 알고리즘:
- (1) front 점마다 `run_layout`을 실행한다.
- (2) `W_requests`가 있거나 폭 키가 바뀌었으면 그 W를 고정 입력으로 평가 커널을 1회 돌리고 봉인 1~8을 확인한다(LY3·LY7).
- (3) K_max(P N3.6 식, 구간 = W 변경 비)까지 반복하고, 닿으면 NONCONVERGENT로 둔다.
- (4) 수렴한 스냅샷으로 판정 축 면적을 계산하고 front를 다시 비지배 필터에 통과시킨다. 동률 폭은 ΔA_tie다(DEC-79). 순위가 뒤집힌 점은 (1)로 돌아간다. 교대 횟수 상한도 K_max다.

**MOD8 구현 요약(U14)**:
- 진입점 `converge(sctx, pdk_decl, points, pool=(), slice_keys=None)`(점마다 `converge_point` -> `refilter` -> 교대). 호출자는 U16: `find_front(...)` 뒤 `converge(sctx, pdk_decl, front.front)`.
  `convergence` 는 패키지 순서상 `search` 위라 `find_front` 가 부를 수 없다(역방향 import 금지) -- 배선은 파이프라인 몫이다.
- `run_layout` 의 유일한 프로덕션 호출처는 `convergence.place_layout`, 평가 커널 재호출의 유일한 호출처는 `search.evaluate(geometry=)`(키의 `w_fixed_fp` 자리). 봉인 스냅샷 -> `LayoutInput` 어댑터는
  `layout_input_of`(`W_adjustable` = 쓰기 소자, matching = derived·ratified, 수동소자 = `layout.passives_from_decl(passive_values(...))`).
- LY7: 레이아웃 결과마다 실현 기하(모든 소자의 실현 W 고정 + 실현 폭 슬라이스 + 설계점 스냅샷 `ly_diffusion` 필드의 확산 기하)로 평가 커널 1회·봉인·제약 행 재확인. 같은 기하가 나오는 고정점에서 freeze,
  `K_max = k_max(max |ln(W_실현/W_사이징)|, min 실효 W 허용오차)`(첫 레이아웃에서 한 번)에 닿으면 NONCONVERGENT. 접합 용량은 `ss_evaluate(diffusion=)` -> `ss_dev` 가 실현 확산 기하로 계산한다.
- W_request: 그룹 요청(cc_nf)은 요청한 (폭 키, nf) 로 평가, 위반하면 거부(`rejected_requests`) -> 레이아웃은 pattern None -> **완화 판정**(`relaxation_decision`): common-centroid 를 요구하는 그룹이
  pattern None 이고 응답 대기도 아니면(nf 조정·W 조정 모두 불가) hub 가 있는 쌍은 interdigitation 전용 `mirror` role 로 다시 놓고 `Relaxation` 기록(맨 앞 review_needed 대상, dx·dy), hub 없는 branch_symmetric 은
  `not_relaxable` 로 배치 없이 기록한다.
- 판정 축 재필터: 축 (전력, 레이아웃 외곽 면적), 동률 폭 = (b_P 큰 값, `layout.area_tie_m2`) 를 `search.nondominated(ties=)` 에 넘긴다. 교대: `pool`(탐색 축에서 지배당한 봉인 점) 중 탐색 축 면적을 대리값으로 비지배인 점만
  레이아웃·재검증하고 다시 거른다(상한 `K_alt` = `k_max(면적 범위, ΔA_tie 최솟값)`).
- **설계 gap(열린 항목) -- 닫힘**(사용자 승인(2026-10-12 P), P-6): (a) kind당 폭 슬라이스 → §3.10.1(P-2), (b) 종속 소자 W 고정 → §3.10.2(P-3), (c) 쌍 전류비 → §3.10.3 전류비 보장 규칙, (d) 면적 모델 오차 → 선언 전까지 기록만, (e) front 생성 뒤 재측정(U16 완료 조건). 상세는 §3.10.3.

**MOD9 `report`**(MISS): 결과 JSON(DRS 8섹션 키, `perf`, front 표, 출발 구간 표 41 §6.6, `gain_budget_db`, 충돌 표, 실패 레코드)을 낸다.

**MOD10 `pipeline`**(MISS): `run_gmid_design_pipeline`이 GB0→…→GB9를 순서대로 부르고 `exit_code_for`로 끝낸다. `[ng-bridge]`의 `oracle_input`·`front_oracle`을 이 진입점 아래로 옮긴다.


### 3.10 계획 이탈·누락 반영 (사용자 승인 2026-10-12 P)

사용자 결정 2026-10-12 "P-1~P-15까지 권고대로 고쳐"(계획→design gap 분석의 이탈·누락)를 이 문서 몫만큼 옮긴다. 이 절의 내용은 **사용자 승인(2026-10-12 P)**된 것이다. P-1·P-9·P-15와 41 §4.5 문구는 41의 몫이다. P-4·P-5·P-14는 계획 정정이고, 40은 §3.1(P-4)만 고친다.

#### 3.10.1 P-2 레이아웃 finger 폭은 행별, sizing은 소자별 폭 슬라이스 (LY2)

- **규칙**: P LY2대로 finger_w는 물리 행마다 정한다. 한 kind 안에서도 행이 다르면 폭이 다를 수 있다.
- **sizing 쪽 변경**: 평가 커널의 폭 슬라이스를 kind당 하나에서 **소자당 하나**로 바꾼다.
  - `LutAccess.w_keys`: `{kind: 폭 키}` → `{소자: 폭 키}`. 레이아웃이 없을 때(사이징 단계) 기본값은 그 kind의 LUT 기준폭 키이고, 소자마다 같은 값을 넣는다.
  - `w_key_of(lut, kind)` → `w_key_of(lut, device)`. 호출부(as-built `block_columns`, `block_widths`, `seal_tolerances`, `ss_linearize` 등)를 같은 변경에서 바꾼다.
  - 소자 폭 키는 설계점 입력이다: MOD8 재평가의 `RealizedGeometry.w_keys`가 소자별 값을 준다. 평가 키의 `w_fixed_fp`가 이것을 덮는다(as-built 그대로).
  - `dc_op`의 폭 키 칸은 소자 값이다(같은 kind라도 다를 수 있다).
- **폐기**: kind당 폭 키 하나로 레이아웃의 PDK 폭 키를 좁히던 경로(`place_layout`의 `layout_score` 최소 키 선택). MOD8 설계 gap (a)는 이것으로 닫힌다(§3.9).

#### 3.10.2 P-3 차동쌍 시도 순서와 종속 소자의 W 고정 (LY5)

- **순서**: P LY5대로 (i) nf 조정(같은 (ID, gm/ID, L)에서 finger_w를 줄임) → (ii) W 조정(LY3 W_request로 MOD8 재평가) → (iii) 둘 다 안 되면 interdigitation 완화(`relaxed: true`, `attempts[{nf, W, reason}]`, 맨 앞 `review_needed`, dx·dy). 레이아웃은 소자를 미리 'W 조정 불가'로 분류하지 않는다.
- **종속 소자도 W를 고정 입력으로 받는다**: as-built는 종속 소자(좌표 = 노드 VGS 순방향, `dc_coord`)의 W를 고정할 수 없어 차동쌍 `cc_same_W`가 바로 완화로 갔다(MOD8 gap (b)).
  - W가 고정된 종속 소자는 ID와 W에서 전류밀도 ln IDu = ln(ID·L/W)가 정해진다. 그래서 그 소자의 VGS도 `vgs_for_current_density`로 정해진다.
  - 이 VGS와 그 소자를 묶는 관계(`equal_vgs` 등)가 정하는 VGS가 다를 수 있다. 이 차는 봉인 2(VGS 정합)가 판정한다. 위반이면 그 W_request는 거부되고(`rejected_requests`), 다음 순서(완화)로 간다.
  - **LY4 hub 없는 `branch_symmetric`**도 같은 순서(nf → W → 완화)를 따른다. 공유 hub가 없어 interdigitation 완화가 불가하면 배치 없이 `not_relaxable`로 맨 앞 `review_needed`에 올린다(as-built `relaxation_decision`과 같다).
  - 고정 W는 쓰기 계획을 바꾸지 않는다. 종속 소자의 좌표 종류는 그대로이고, ln IDu가 고정 입력으로 더해질 뿐이다.

#### 3.10.3 P-6 MOD8 열린 항목 닫기

§3.9 'MOD8 구현 요약'의 설계 gap (a)~(e)를 다음으로 닫는다. design에 남는 열린 질문은 없다(N9.2).

| 항목 | 처리 |
|---|---|
| (a) kind당 폭 슬라이스 | §3.10.1(P-2)로 해소 |
| (b) 종속 소자 W 고정 불가 | §3.10.2(P-3)로 해소 |
| (c) LY1 소자별 W 허용오차가 소자 사이 전류비를 보장하지 않음 | **결정**(사용자 결정 2026-10-12 "U-71승인", U-71). **전류비 보장 규칙**: matching·미러 그룹의 소자 쌍 (i, j)마다 실현 W 비의 차 \|ln(W_i/W_j)_실현 − ln(W_i/W_j)_사이징\| ≤ min(tol_V,i·(gm/ID)_i, tol_V,j·(gm/ID)_j)를 지킨다. 유도: 같은 VGS를 받는 쌍의 전류비 오차는 W 비 오차와 같고(ΔI/I = Δln W), 봉인 3의 KCL 허용오차가 tol_I = tol_V·gm이므로 ΔI ≤ tol_V·gm ⇔ Δln W ≤ tol_V·(gm/ID)다. 이 규칙은 소자별 LY1 허용오차 위에 더하는 쌍 조건이다. 레이아웃이 finger 후보를 고를 때 지키고, 못 지키면 W_request를 낸다. 결과적으로 재평가 봉인 3이 이 원인으로 거부하는 경우가 없어진다. as-built의 폭 키를 하나씩 빼며 재시도하는 `key_exclusion`은 지운다 |
| (d) DEC-80 (ii) 면적 모델 오차 선언값이 없음 | 선언 전까지 탐색 축 대 판정 축 차를 **기록만** 한다. `review_needed` 승격은 하지 않는다. 선언이 생기면 DEC-80 (ii) bin 폭에 들어간다 |
| (e) front가 0개라 손으로 봉인한 점으로 실측함 | 탐색이 library 회로에서 front를 낸 뒤 MOD8을 다시 잰다(U16 완료 조건) |

#### 3.10.4 P-7 DEC-88 반전 수준 하한 = 연속 부등식 제약

- **규칙**: P DEC-88대로 쓰기 소자 ln IDu의 반전 수준 하한(정점)은 상태(L, VDS, VSB)에 의존하므로 bounds가 아니라 SLSQP **연속 부등식 제약 행**이다.
- **행**: 쓰기 소자 m마다 c_m = (ln IDu_m − floor_m(L_m, VDS_m, VSB_m)) / b_m ≥ 0.
  - floor_m은 그 후보 동작점의 (kind, 소자 폭 키, L, VDS, VSB) 곡선에서 gm/ID 정점의 ln IDu다. LUT 순수 함수이므로 LUT memo 함수다(§2.4.6, as-built `cell_floor._peak_floor`의 칸 최댓값 대신 동작점 값).
  - as-built r9 전도 하한(봉인 9)도 같은 방식의 제약 행으로 둔다(**결정**(사용자 결정 2026-10-12 "GQ2, N1, N3, K2 권고대로") U-69, 계획 DEC-88에 봉인 9 명시): floor = 그 동작점에서 ln(gm·tol_V/I_off) = 0이 되는 ln IDu.
  - b_m(분해능)과 정규화는 N3.14 정규화 위반량 규칙을 따른다(다른 제약 행과 같다).
- **폐기**: 칸 정점·전도 하한으로 θ 상자를 조이는 경로(`E/search/cell_floor.py`의 `ln_idu_floors`가 bounds를 바꾸는 것, `search/CONTRACT.md:573`). §3.6 표의 DEC-88 행을 고친다.

#### 3.10.5 P-10 finger 피치 여유를 PDK에서 유도 (I-A12)

- **규칙**: 판정 축 면적(레이아웃 외곽 면적)의 finger 피치 여유 `finger_pitch_overhead_m`은 상수가 아니라 PDK 선언에서 계산한다. 옛 `stick_diagram.PROCESS_GEOMETRY`의 0.0은 쓰지 않는다.
- **식**: 사용자가 ratify한 PDK 레이아웃 규칙 식 다섯 개 중 하나를 그대로 쓴다(사용자 2026-10-08 "4번도 네 판단에 동의해", 대상: finger 피치 여유, 행 간격, dummy, tap, well 간격). 선언 파일은 `assets/sky130_pdk_decl.json`이다. 새 규칙을 만들지 않는다.
  - as-built `layout.LayoutPdk.from_lut`이 이 다섯 길이를 PDK 선언에서 읽는다(`E/layout/contract_input.py:43,129-152`, `layout/CONTRACT.md:226-239`).
  - 실측 sky130: (overhead, gap, dummy, tap, well) = (2.8e-7, 4.7e-7, 5.4e-7, 6.8e-7, 1.63e-6) m.
  - 행 폭 = Σ nf × (L + overhead). finger마다 접촉 확산 하나다(`layout/diffusion.py:7`).
- 판정 축 면적 항목 `AREA_ITEM_FINGER_OVERHEAD`(`E/layout/floorplan.py:79`)가 이 값과 규칙 출처를 함께 쓴다. 계획 I-A12는 옛 엔진 상수에 대한 기록이고, 새 엔진에서는 이 경로로 닫힌다.
- dummy(I-A13 일부)도 같은 ratify 식이다: 행 끝 하나당 `poly.1a + poly.7 + overhead/2` = 선언 `dummy_w_m`(피치/2 근사, `layout/CONTRACT.md:392`). 행마다 양끝 둘이 판정 축 면적에 들어간다(`row_end_dummy_x2_per_row`).

#### 3.10.6 P-11 최종 해의 활성 제약 여유 판정과 활성/비활성 보고 (NFR-5)

- **입력**: 최종 해(front 점과 채택 해)마다 제약 행 k의 판정 단위 c_k(§7.2)와 metric 여유 m_k = c_k·b_k.
- **바닥**: floor_k = max(b_k, ME_k). b_k = 그 metric의 격자 분해능(`MetricResult.resolution`), ME_k = 측정된 모델 오차(DEC-72). ME_k가 측정되지 않았으면 그 행은 **'여유 판정 보류'**다(통과로도 실패로도 세지 않는다).
- **분류**: m_k ≤ floor_k이면 **활성**, 그보다 크면 **비활성**.
- **NFR-5 판정**: (i) 두 목적 축에서 그 해가 front 위(비지배)인가, (ii) 제약마다 활성/비활성/보류와 여유·바닥을 보고했는가. 성능 스펙은 제약이므로 통과/실패가 아니라 활성/비활성과 여유를 적는다(P N6.3).
- **보고 위치**: 결과 JSON front 표의 점마다 `constraints[{metric, op, bound, value, margin, floor, b, model_error, state: active|inactive|margin_pending}]`. 예산 게이트로 bin 폭이 넓어졌으면 '해상도 굵음(배수 n)'과 함께 그 해상도 기준임을 적는다(DEC-80).

#### 3.10.7 P-12 규칙 분기 발동표를 결과 JSON에 출력 (DEC-59)

- **위치**: 결과 JSON `rule_branches`. 전용 파일 `rule_branch_coverage.json`은 만들지 않는다(R7).
- **형식**: `rule_branches[{branch, kind: computed|record_only, views[{view, activated, cells[], out_of_forward_cells[]}], library_activated_circuits, library_verified_circuits}]`.
  - `views`: 발동은 여기 뷰마다 센다. 셀 단위 분기는 순방향 경로 위 셀만 세고, 순방향 밖 셀은 `out_of_forward_cells`에 소자 이름으로 적는다.
  - `kind`: `계산 규칙 있음`(computed) / `기록만`(record_only).
  - `library_activated_circuits`·`library_verified_circuits`: library 회로 중 그 분기가 발동한 회로 수와 검증 발동 회로 수.
- **정지**: 검증 발동 회로가 0인 분기를 탄 회로와 `record_only` 분기를 탄 회로는 탐색 전에 `unsupported_rule_branch`로 정지한다(DEC-59 그대로).
- 실행 하나는 회로 하나라 library 집계(`library_*`)는 실행 안에서 계산하지 않는다. 실행마다 자기 회로 발동만 기록하고 9회로 합계는 U16 통합 test 보고가 모은다(§3.10.9 PN2 결정, "4절도 권고대로").

#### 3.10.8 P-13 그 밖의 누락 항목

| 항목 | design |
|---|---|
| `ID_source` 타입(P N3.7) | 소자 필드 `device.dc_id_source` ∈ {`kcl`(KCL·미러 비율로 정해짐), `ideal_source_ref`(값 선언 이상 전류원), `theta_current`(θ 전류 변수, DEC-70. class-AB 정지전류처럼 게이트-소스 KVL 루프가 있는 가지도 여기다. 그 루프는 전류가 아니라 멤버 gm_id 하나를 종속시킨다, DEC-64)}. writer = 계산 블록 ② 전류. 결과 JSON 소자 행에 싣는다 |
| `tol_V` 정의(P N3.6) | 셀 = (kind, 폭 키, L 점, VDS). 셀 값 = 그 셀 안 내부 격자점의 leave-one-out 보간 오차 최댓값이고, 축 VGS·VDS·VS와 bin 안 L을 쓴다(bin 경계를 넘지 않는다. L 점이 2개인 bin은 검증 전용 중점). 운영 보간과 같은 방법으로 재고, 간격 2배 격자 오차를 2^p(선형 2, Hermite 4)로 나눈다(Richardson, DEC-87). 지표 배정: 봉인 2·3·SCC 수렴·W 허용오차 = ID 환산 지표, 층 0 gm/ID 역산 = gm/ID 역산 지표, 봉인 1·6·8 = 그 전압을 만든 LUT 조회 종류(as-built는 ln IDu 좌표 역산이라 ID 환산 지표, `E/sizing/seal_tolerances.py:5-7`). 계산 함수 정본은 `lut` tol_V 파일이다. 양끝 격자점(leave-one-out 정의 불가)은 같은 bin 안 인접 내부점의 LOO 값을 쓴다(외삽 금지 DF-27, §3.10.9 PN3 결정) |
| 결합 잔차의 쓰임(P N3.7) | 41 B1 r̂(§2.4 단계 B 층)의 소비처 셋: (i) 진단 보고(결과 JSON `diagnostics.residual_probe`), (ii) 6c DoD의 결합 잔차 표(결과 JSON `residual_table[{block, metric, r_hat, r_spread, n_samples, seal_failures}]`), (iii) 신뢰 한계: 잔차가 그 metric의 모델 오차 선언값(DEC-72)보다 크면 그 블록 분해값을 할당 입력으로 쓸 때 `trust_limits[{block, metric, residual, model_error}]`를 함께 기록한다. 판정 위치는 바꾸지 않는다(DEC-74) |
| LY8 3열(P LY8, T8) | 결과 JSON `metric_columns[{metric, engine_at_sizing_w, engine_at_realized_w, spice_at_realized_w}]`. 모델 오차 파일(DEC-72)에는 2열 − 3열만 쓴다. sizing 직후 기하의 SPICE는 진단 실행(태그 `sizing`)이다 |
| 근방 반경 확장 규칙(P DEC-71 인계) | 초기 반경 = 41 §5.9의 r_j = max(\|θ_local − θ_조립\|, h_j)(h_j = 그 성분의 격자 분해능). feasible이 없으면 반경을 2배로 넓힌다. 2배는 DEC-80 예산 게이트와 같은 규칙이라 새 상수가 아니다. 멈춤: 반경이 전역 bounds에 닿거나, 확장에 쓴 평가 수가 DEC-34 예산 식(N = ⌊(B − T_fixed)/t_eval⌋)의 남은 몫을 넘을 때. 층 0은 전역 bounds를 줄이지 않는다 |
| IC3 필드 완전성 | `test_coverage_and_field_completeness`: 결과 JSON에 T1 필드(아래)가 소자·노드마다 빠짐없이 있고, 레이아웃 coverage(`check_stick_diagram_coverage` 대응) 누락 0, 이름 충돌 0. 필수 필드 목록은 결과 JSON 스키마 한 곳에서 정의하고 test가 그것을 읽는다 |
| IC7 무동작 계수 | `test_all_library_topologies_run`: DEC-47 대상 구분상 그 기능이 필요 없는 library 회로에서 그 기능의 발동 계수 = 0(규칙 분기 발동표 `views[].activated`와 블록 계수로 잰다) |
| IC11 거부 케이스 먼저 | P N4.1 IC11 문언 그대로: 같은 test 파일에서 먼저 **레일 셋 이상 또는 음전위 레일 회로를 `supply_nets` 없이 로드하면 GB0 로드 게이트가 거부함**을 증명한다(DEC-60). 거부 픽스처는 합성 음전위 레일 회로(`supply_nets` 없음)와 3레일 회로 `pushpull_follower_buffer`에서 `supply_nets`를 지운 변형 둘이다. 그 뒤 원점 이동 동등성을 단언한다: 2레일 `two_stage_ota` (1.8, 0) 대 (0.9, −0.9) V, 3레일 `pushpull_follower_buffer` (vdd 1.8 / vss 0 / agnd 0.9) 대 (0.9 / −0.9 / 0) V(2026-10-12 gap 재분석 정정: nmcnr는 Q8 정정 뒤 음전위 레일이 없어 쓰지 않는다) |
| 단위 보고 필드(P N6.3, U-18, P-14) | 구현 단위의 보고(결과 JSON과 별개인 단위 완료 보고 스키마)에 `broken_tests[{test, reason}]`와 `criteria_weakened[{criterion, before, after, reason, approval_id}]`를 둔다. 그 옆에 `graph_canon_check{lint_g, type_location, ownership_diff[], g10{recompute_same_input, s0_second_run_computes, lut_recompute_after_eviction}}`와 `reuse_check{g10{...}, blocks[{block, part, reuses, grafts, computes}], duplicate_arg_calls_in_loops, loop_invariants_hoisted[]}`를 숫자와 함께 **항상** 둔다(사용자 지시 2026-10-12 "coding시에 계산값 재사용원칙도 준수되었는지 확인하는 과정을 넣고 이 확인내용을 항상 보고해"). 0개면 빈 목록이다. 기준 약화는 매 건 승인 기록 id가 있어야 한다(U-18) |
| cProfile(NFR-2, U-49) | 진입점 `run_gmid_design_pipeline(..., profile_path=None)`과 CLI `--profile <path>`. 주면 그 경로에 cProfile 파일을 쓴다. P N6.1 단위 6 완료 조건(cProfile 기록 파일)에 들어가고, 그 기록 전에는 탐색 층을 늘리거나 줄이지 않는다(U-49). 시간 수치는 판정에 쓰지 않는다 |
| 공유 계산 블록 변경의 DoD(DEC-51) | 9회로 합격을 낸 뒤 `core`·`sizing`·`metrics`·`search`의 공유 계산 블록 알고리즘을 바꾸는 변경은 9회로 전후 차(노드전압, front, SPICE verdict)를 보고에 붙인다. 명령은 §10.4 '공유 블록 전후 대조'. SPICE verdict가 하나라도 바뀌면 사용자 확인을 받는다 |
| I-C10·U-20 `stack_headroom_slack_v` | **결정**(사용자 결정 2026-10-12 "K-2 권고대로, GQ1/GQ3/GQ4, U-14,U-20,U-32,U-45 권고대로")(U-20): 봉인 항목 1·5가 같은 사실을 보므로 metric을 두지 않는다(봉인 검사로 흡수). 새 엔진 metric 등록부에 이 이름은 없다 |
| I-A13 dummy·LDE | **결정**(사용자 결정 2026-10-12 "U-67은 (나)로", U-67): dummy는 §3.10.5의 ratify 식으로 판정 축 면적에 들어간다. (1) L이 섞인 interdigitation 행의 좌우 대칭 검사를 구현한다: 행 finger 패턴에서 소자마다 finger 위치의 행 중심 거울상이 같은 소자의 finger인지 본다(LY4 common-centroid 정의, 새 상수 없음). 어긋나면 그 matching 그룹을 `review_needed`(`interdigitation_not_mirror_symmetric{group, row, device}`)로 올린다(U12). (2) LOD는 오라클 검증에만 넣는다(아래 §3.9 LY8·§4). 엔진 판정과 LUT에는 LOD가 없다. (3) WPE·PSE는 대상이 아니다(PDK 모델에 파라미터가 없어 규칙을 만들지 않는다) |
| I-A11 크로스오버 주파수 차이 | 옛 엔진의 선언식(36.6 MHz) 대 전체 응답(30.50 MHz) 차이다. 새 엔진은 GBW·PM을 봉인 스냅샷 전회로 MNA로만 판정하고(DEC-74, §3.5), 근사식은 층 0 출발값에만 쓰며 근사와 MNA의 차를 `comp_approx_gap`으로 기록한다(41 §5.5). 그래서 이 차이는 판정에 들어가지 않고 회로마다 측정량으로 남는다. 옛 엔진 원인 규명은 범위 밖이다(P-14) |
| 정밀 경로 선언(DEC-73·76) | spec `search_method`가 정밀 경로(내층 DP·중층 좌표강하)를 선언하면 탐색 전에 `unsupported_rule_branch`(사유 `precise_path_not_implemented`)로 정지한다. 정밀 경로는 기본 꺼짐이고(DEC-73) 구현이 없는 분기를 타면 정지한다(DEC-76 안전망). **결정**(사용자 결정 2026-10-12 "U-66은 (가)로", U-66). 정밀 경로 design은 U-33 측정이 기본 경로 부족을 보일 때만 시작한다 |
| 보상 단 폴백(U-51) | 사용자 결정 2026-10-12 "U-51은 (나)로": 보상 단 gm/ID는 θ에 포함한다(DEC-04). 폴백은 **계수 기반**이다: 외층 SLSQP가 그 시작점의 반복 상한(as-built `slsqp_outer` 식 maxiter = Σ_i max(⌈log2(상자폭_i / FD 스텝_i)⌉, 1), `E/search/slsqp_outer.py:179-181`) 안에 수렴하지 못하면 그 시작점에서만 보상 단 θ를 GB5 규칙값(gm_req = DEC-92 MNA 1-D 근, §3.5)으로 고정해 한 번 다시 푼다. 폴백 사실과 이유(`compensation_fixed_fallback{start, reason: slsqp_maxiter}`)를 기록하고 그 점을 '추정'으로 표시한다. 벽시계·U-47 예산에 의존하지 않는다(결정론). 9회로 실행에서 폴백 빈도를 재서 보고한다. 기록은 결과 JSON front 점의 `fallbacks[]`와 `perf.compensation_fixed_fallback` 계수 |
| 복합 블록 묶음 크기 상한(DEC-81) | 묶음 크기 상한을 계수 예산 N_S(`structure_count_budget`, 41 §0)로 둔다. 근거는 L-10과 같다(실행 시간에 의존하지 않아 결정론). **결정**(사용자 결정 2026-10-12 "GQ2, N1, N3, K2 권고대로")(U-65, 계획 DEC-81 정정) |
| T1·T7·T8 형식(P N6.2) | T1: 소자 행 `{W, L, finger_w, n_fingers, ID, VGS, VDS, VSB, gm_id, ID_source}`(오라클 넷리스트 `w = finger_w`, `m = n_fingers`), 노드전압 전부, 이상원·수동소자 값, metric, front 표, 실패 레코드, exit code. T7: SPICE를 돌리는 front 점 = U-45 기본안(양 끝점 + 예산 점)이고 넷리스트 기하는 그 점의 MOD8 수렴 기하(LY8). T8: 위 3열 |
| 바이어스 소자 gds 귀속과 '층 0 AC 무동작'(P DEC-71 (2)) | 바이어스 기둥 소자의 gds가 다른 블록의 국소 AC 이득에 들어가면 그 소자는 기여받는 블록의 국소 문제에 고정 입력으로 들어가고 공유 소자로 표시되며 확정은 조립에서 한다. 어느 블록에도 gds로 기여하지 않는 순수 기준전압 소자만 AC 제약 없이 풀고, 하한은 포화 여유·매칭 선언·DC 등식이다. 그 하한마저 없으면 결과 JSON `layer0.ac_inactive[{column, devices, reason}]`로 보고한다(조용히 자명해를 내지 않는다). 블록에도 바이어스 기둥에도 들지 않는 소자는 `column_unassigned`로 정지한다(as-built `stage_a`) |
| N3.13 bisection 켜기 경로 | 기본 비활성. spec `optional_stages`(DEC-75)에 bisection 대상 제약 metric 목록을 선언하면 켜진다. 진입점은 `achievable_metric_bound(mode="bisect")`이고 `run_gmid_design_pipeline` 위의 도구가 부른다(MOD10, 패키지 순서상 pipeline 위). 결과는 선언의 `value`와 `_derived{지문, 스텝 이력, 시각}`으로 기록한다. 42 DEC-22 행은 N/A가 아니라 MISS(기본 비활성, 켜기 경로 설계됨)다. 키는 `optional_stages.bisection.metrics: [...]`다(DEC-68 명명, §3.10.9 PN4 결정) |
| TS7 xfail 규칙(P N3.11) | 계약 test는 처음부터 `xfail(reason="<담당 단위 id>", strict=True)`로 둔다. 담당 단위가 완료되면 그 단위 변경에서 xfail 표시를 지운다. strict이므로 단위 완료 전에 통과하면(XPASS) FAIL이 나서 활성화를 강제한다 |

#### 3.10.9 정한 기본값 (design 소관, 열린 질문 없음 -- P N9.2-8)

아래 1~4와 마일스톤 범위 밖(PN5)은 사용자가 그대로 결정했다(사용자 결정 2026-10-12 "4절도 권고대로", PN1~PN5).

design이 정할 수 있는 것은 아래처럼 정했다. 사용자 결정이 필요한 것은 계획 N7.2 U-60~U-70으로 올렸다(§3.10.11).

1. **P-10 finger 피치 여유**: §3.10.5. 2026-10-08 ratify된 PDK 레이아웃 규칙 식을 쓰고 새 규칙은 만들지 않는다.
2. **P-12 `library_*` 합계**: 실행 하나의 결과 JSON은 **자기 회로의 발동만** 적는다(`views[].activated`, `cells`, `out_of_forward_cells`). 9회로 합계 `library_activated_circuits`·`library_verified_circuits`는 결과 JSON 필드가 아니다. U16 integration test(`test_all_library_topologies_run`, IC7)가 9회로 결과 JSON을 모아 test 보고에 낸다. 저장되는 coverage 파일은 없다(R7). 정지 판정(검증 발동 0 분기)에 쓰는 '검증 발동' 여부는 분기 목록의 속성이다(`kind`와 같은 자리, 코드 상수가 아니라 graph 규칙 등록부의 분기 레코드에 `verified_circuits` 목록으로 두고, U16 test가 9회로 실행과 대조한다).
3. **P-13 tol_V 양끝 격자점**: leave-one-out이 정의되지 않는 양끝 격자점의 셀 값은 **같은 bin 안에서 이웃한 내부 격자점의 leave-one-out 값**이다. 외삽하지 않는다(DF-27: 축 밖 입력은 실패 레코드). 이웃 내부점이 없는 축(점 2개)은 L 축과 같은 규칙으로 검증 전용 중점을 쓴다(P N3.6).
4. **P-13 bisection 켜기 키**: spec `optional_stages.bisection.metrics: [<metric 이름>, ...]`(DEC-68 이름 규칙, DEC-75). 목록에 든 제약 metric만 N3.13 절차를 탄다.

#### 3.10.10 실측으로 정하는 계획 항목의 측정 설계 (U-23·U-33)

계획이 '실측 후 결정'으로 둔 두 항목의 측정 방법이다. 판정 기준은 계획 문언 그대로이고, design은 실행 방법만 정한다.

| 항목 | 측정 도구 | 비교군 | 기록 | 판정(계획 문언) |
|---|---|---|---|---|
| U-33 층 0을 기본 경로로 | `tools/compare_paths.py`(pipeline 위 도구, MOD10). 같은 spec·탐색 인자로 회로마다 실행 | (i) 콜드 스타트(층 0 끔, 선언 x0·S3 시작점) (ii) 층 0 조립점 출발 (iii) 정밀 경로는 U-66 (가): 미구현 정지라 측정 대상이 아니다 | 평가 수(층 0 몫 포함), front 점 대조(두 축), 제약마다 활성/비활성·여유(§3.10.6), wall-clock, 국소 대 전역 차(ΔVGS, Δ노드전압, Δgm_id, 블록 gain 차) | 층 0이 평가 수를 줄이면서 목적값·활성 제약 여유가 max(격자 분해능, 모델 오차) 안에서 같거나 나으면 기본 경로 |
| U-23 입력-캐스코드 L 동일 강제 | 같은 도구, L 묶음 선언만 바꿔 실행 | (A) 독립 L (B) 동일 강제 (C) A + LR5 격자 확장 (D) A + VDS 균등 고정 | 평가 수, 목적값, 제약 여유, 레이아웃(행 안 L 종류 수, finger 배정 성공, finger 합·box 비, 파일럿만), tail 포화 여유, `parasitic_pm_ss_deg`, 미러 전류비 오차 | 계획 U-23 문언(B가 finger 배정 실패면 기각 등) |

- 두 측정 모두 결과를 파일에 회로마다 이어 쓴다(중간 종료에도 남는다). 판정은 사용자 결정 기록으로 닫는다.
- U-14(공유 VGS 후보 gain 차 ≤ 분해능이면 전력 작은 쪽), U-45(SPICE front 점 = 양 끝점 + 예산 점), U-32(단위 접미사는 사람이 선언하는 spec 값에만)는 **결정**(사용자 결정 2026-10-12 "K-2 권고대로, GQ1/GQ3/GQ4, U-14,U-20,U-32,U-45 권고대로")이다. U-51은 **결정**(사용자 결정 2026-10-12 "U-51은 (나)로"): 보상 단 gm/ID는 θ에 포함하고, 외층 SLSQP가 반복 상한 안에 수렴하지 못한 시작점에서만 보상 단을 GB5 규칙값으로 고정해 다시 푼다(계수 기반, '추정' 표시, §3.6 외층).

#### 3.10.11 사용자 결정으로 올린 항목 (계획 N7.2 U-60~U-70)

design이 정하면 안 되는 것(범위·회로 해석·판정 기준 변경)은 계획 N7.2에 행을 더하고, 그 항목에 걸린 구현 단계의 착수 조건으로 둔다(N9.2-8). 결정된 행은 결정 원문을 적는다.

| U | 내용 | 상태와 내용 | 구현 단위 |
|---|---|---|---|
| U-60 | LUT memo 상한과 퇴출 판정(§2.4.6) | **결정**(사용자 결정 2026-10-12 "U-60은 (가)로"): (가) 퇴출 허용·퇴출 수 보고, `recomputes_after_eviction` = 0 판정, 상한 N_T 무관. U17 ③ 착수 조건 해소 | -- |
| U-61 | d/s 맞바꿈의 종류가 다른 소자 전류 묶음 상자(§6-8, D-1) | **결정**(사용자 결정 2026-10-12 "5절 권고대로"): 구성원 상자의 교집합, 비면 거부. 같은 궤도 안 불일치는 지금처럼 거부 | U2·U11(`search_domain`) |
| U-62 | d/s 맞바꿈과 DEC-97(§6-8, D-3) | **결정**(사용자 결정 2026-10-12 "5절 권고대로"): DEC-97 (3) '방향 없음'을 MOS d/s로 넓힘, 위치·`wl`·생성자 모두 그래프 하나(D-2), d/s 뒤집은 입력은 대칭 결과(궤도·정준 위치·`dc_colour`, 전류 부호는 표기 기준 방향 변환 뒤)만 비트 동일하고 사이징 결과는 선언 방향을 따른다(범위 (라), 사용자 결정 2026-10-13 "1은 권고", 틀린 선언은 봉인 7 거부), 9회로 `dc_colour` 순서 변화는 test 기대값 재생성 | U2 |
| U-63 | 층 0 정지 범위(41 PQ2, §5.3.11) | **결정**(사용자 결정 2026-10-12 "U-63은 (가)로", U-63): 정지는 경로 열거 예산 초과와 후보 격자 Π > N_S 둘뿐. N_T,i는 평가 상한(`layer0_candidates_truncated` 기록 + 블록 front '추정'). 현재 library 정지 0 | U15 |
| U-64 | 층 0 정의역 상한 A^L0의 쓰임(41 L-14) | **결정**(사용자 결정 2026-10-12 "3은 권고대로"·"L14부터 PQ5까지"): 층 0 전용(첫 배분 제외, bin 위 끝 보조). exit 3·41 §6.4-1은 축소 전 표 | U9 A9·U15 |
| U-65 | 복합 블록 묶음 크기 상한(DEC-81) = N_S | **결정**(사용자 결정 2026-10-12 "GQ2, N1, N3, K2 권고대로"): 계수 예산 N_S | U1 복합 블록 |
| U-66 | 정밀 경로 선언 시 정지(DEC-73·76) | **결정**(사용자 결정 2026-10-12 "U-66은 (가)로"): `unsupported_rule_branch` 정지, 조용한 폴백 없음. 정밀 경로 design은 U-33 측정이 기본 경로 부족을 보일 때만 | U11 |
| U-67 | LOD·WPE·PSE와 L 혼합 interdigitation 대칭 검사(I-A13) | **결정**(사용자 결정 2026-10-12 "U-67은 (나)로"): L 혼합 행 대칭 검사 구현, LOD는 오라클 sa/sb/sd로만, WPE·PSE 제외 | U12(대칭), U16·U6(LOD 오라클 입력) |
| U-68 | 키가 다른 옛 S0 수준 스냅샷 파일 정리(§2.4.3, GQ2) | **결정**(사용자 결정 2026-10-12 "GQ2, N1, N3, K2 권고대로"): 승인된 tol_V 캐시 정리와 같은 방식으로 삭제 코드 허용 -- 저장소·모든 worktree의 현재 파일로 만들 수 있는 키는 보존, 어떤 checkout으로도 만들 수 없는 키의 파일만 쓰기 시점에 1회 삭제, 방금 쓴 파일·링크·폴더 밖·형식 다른 파일 제외, 실패 시 아무것도 지우지 않음 | U17 ① 정리 코드 |
| U-69 | 봉인 9 전도 하한의 연속 제약화(§3.10.4)와 계획 DEC-88 정정 | **결정**(사용자 결정 2026-10-12 "GQ2, N1, N3, K2 권고대로"): 동작점별 연속 부등식 제약, 계획 DEC-88에 봉인 9 명시(정정함) | U17 ③·U11 제약 행 |
| U-70 | 반쪽 귀환이 비대칭인 차동 출력의 잡음 N_in 계수(41 §7.5, K-2 재확인) | **결정**(사용자 결정 2026-10-12 "GQ2, N1, N3, K2 권고대로"): N_in 구조 유도, 대칭 귀환(Cf1 = Cf2) 식, 비대칭 회로는 '추정' | U8·U13 잡음 출발 경계 |

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
   - **U6 test 후속 정의**(2026-10-09 오케스트레이터): (i) 창 판정의 floor는 **관측 노드(루프 끊는 점)** 기준 reltol·|V_op| + vntol이다. (ii) 오라클 ICMR 좌표는 창 끝에서의 **실제 입력 공통모드 (V_inp + V_inn)/2**다(엔진 `icmr_v`와 같은 정의). (iii) 차동 입력이 없는 회로의 ICMR은 `unavailable`이다. (iv) 하측 이득 여유 필드 이름은 `low_side_gain_margin_db`. (v) `noise_excess_th`의 입력 셀 소자 이름은 오라클 넷리스트 이름으로 사상해 찾는다(수동소자 접두 포함). 선언된 이름 중 하나라도 못 찾으면(`input_cell_missing` 비어 있지 않음) 찾은 부분집합으로 계산하지 않고 `noise_excess_th`는 None + `excess_reason`(누락 이름)이며, 이 metric의 제약은 PASS가 아니라 INCOMPLETE/N/A다(fail-closed).

| 항목 | 상태 | 증거 |
|---|---|---|
| free/forced, 포화, off_current, CMRR/PSRR, 접합 기하 | OK | `tools/spice_oracle/README.md:60-69,114-117,146-147,300-318` |
| C10 조기 종결 계약 | PART(계약만 있고 master 미반영) | `[ng-oracle-early]` 계약 L14-81 |
| 지속 진동 = unstable | DEV: 계약과 test가 undetermined로 고정되어 있다 | 계약 L42-54, `tools/spice_oracle/tests/test_oracle_c10_stability.py:710` |
| 개루프 RHP: Nyquist Z + 과도로 판정, 결정 불가일 때만 INCOMPLETE | DEV: `pm_undefined`이면 무조건 N/A→INCOMPLETE | `[ng-cmfb-pm]` README '판정', `tools/spice_oracle/README.md:516` |
| `.pz` P 계수, N 위상 펼침 | MISS | `grep -n "\.pz" tools/spice_oracle` 0 |
| 잡음 `.noise` 대조 | MISS | 41 §7.6 |
| `pm_cm_ss_deg` 측정 | OK `[ng-cmfb-pm]`. `[ng-bridge]` `ORACLE_MEASURES`에는 없다 | -- |


**LOD 입력**(사용자 결정 2026-10-12 "U-67은 (나)로", U-67): 오라클 넷리스트의 MOS 인스턴스는 MOD8 수렴 레이아웃의 `ly.lod`에서 finger별 `sa`·`sb`·`sd`를 받는다(sky130 subckt 인자, 모델의 `lod.spice`·`saref`/`sbref`. 값이 0이면 응력 모델이 꺼진 기본 동작이다). finger별 값이 다르면 finger마다 인스턴스를 나눈다(`m`으로 묶지 않는다). 엔진 예측(LOD 없음)과 오라클 측정의 차는 metric별 `model_error_<metric>`(DEC-72)로 기록되어 제약 여유에 들어간다. 출처는 `ly.lod` 하나이고 오라클이 기하를 따로 계산하지 않는다(DEC-91과 같은 원칙). 담당: U16(엔진 → 오라클 입력), U6(넷리스트 인자).

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
   - **전류 기저 열 순서 규칙**(사용자 결정 2026-10-12 "3번 권고대로", (가)): 결정 취지 = "대칭 궤도 원소를 자유 열로 먼저 남긴다"(위 '대칭인 것끼리 묶는다'의 규칙화). 자유 열 선택에서 비자명 궤도 원소를 우선한다. 행사다리꼴은 앞 열부터 pivot(종속)으로 잡으므로, **열 정렬 키에서는 비자명 궤도 원소를 뒤로** 둔다: 열 정렬 키 = (그 원소의 궤도가 비자명인가 -- 비자명이 뒤, `dc_colour`, 이름). (결정 원문의 키 표기 '비자명 먼저'는 자유 열 선택 순서를 뜻한다. 열 정렬에서 앞에 두면 비자명 원소가 pivot이 되어 파일럿이 27/40으로 나빠진다 -- ①-d 실측.) `current_basis`는 `graph/s1: orbits`(§2.4.8)를 읽는다. 측정 의무: (묶음 수, 탐색 θ 변수 수) = (`len(SearchDomain.ties)` -- 전류·L·ln IDu·수동소자 값 묶음 전체, `len(SearchDomain.variables)`). 그중 전류 묶음 수(대표가 θ 전류 성분인 묶음)는 함께 기록한다. 기준선 = master `8e46548` as-built 값(파일럿 29/38, 그중 전류 묶음 7. 나머지 8회로 각 회로 값)과 같아야 한다. ①-d 실측: 규칙 적용 뒤 파일럿 29/38·전류 묶음 7, 나머지 8회로 base와 같음. "D-3 반영 뒤·열 순서 규칙 전" 측정값(파일럿 28/39, 전류 묶음 6)은 기록만 한다. 파일럿 전류 묶음 구성: M1a~M1b 유지, M4a~M4b 대신 M19~M10.
4. **해제**: spec `search.untie_orbits: {원소: {source}}`(as-built 정본, 옛 이름 `symmetry_untie`)에 적힌 소자는 궤도에서 빼고 따로 변수를 둔다. 의도적 비대칭 사이징에 쓴다.
5. **불변식**:
   - **궤도와 matching 사이에는 포함 관계를 불변식으로 두지 않는다**(H1·N8, `[ng-layer0-canon]` 실측). 어느 쪽도 일반적으로 다른 쪽을 포함하지 않는다.
     - 비율 미러는 궤도가 아니다.
     - 반회로 대응은 궤도지만 matching 그룹 하나에 들어가지 않는다. 실측 예: 파일럿 M11a/M20a(class-AB KVL 루프 멤버), M37a/M37b(CMFB 쌍).
     - 대신 대조 표 `orbit_matching_crosstab`을 보고한다. MOS 궤도마다 그 궤도가 걸친 matching 레코드, 그리고 matching 레코드마다 그 레코드가 걸친 궤도를 적는다. 수동소자 궤도(Cc1/Cc2, Rz1/Rz2, R1/R2, CL1/CL2 등)는 matching 대상이 아니므로 표에서 뺀다.
     - `review_needed`로 올리는 것은 하나뿐이다(사용자 결정 2026-10-12 "나'로 진행해", (나')). `diff_pair` 레코드의 두 멤버가 다른 궤도이고, (a) 회로의 출력 포트(topology `ports`)가 차동 쌍(`differential_output_p/n`)이며 (b) 그 `diff_pair`의 두 gate가 회로의 차동 입력 포트 p/n일 때만이다. 기록 코드는 `diff_pair_orbit_split`이다(`orbit_matching_crosstab`의 `findings`, 단계 A 보고서 review 목록). 이 경우만 대칭 차동쌍의 정의와 직접 모순된다. 그 밖의 `diff_pair` 궤도 불일치는 `orbit_matching_crosstab`에 기록만 한다.
     - 9 library 회로 기대: review 0. 파일럿 M1a/M1b는 같은 궤도라 통과, M37a/M37b는 gate가 Voc/Voc_des라 대상 아님(CMFB 단일 출력 오차증폭기), 단일 출력 7회로는 (a)에 걸리지 않는다. 실제로 거부하는지는 파일럿에서 넷 하나를 비대칭으로 바꾼 합성 회로로 확인한다(§10.2).
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
8. **MOS drain/source 맞바꿈**(사용자 결정 2026-10-12 "6. 가", 대칭 탐색 그래프 하나 = 사용자 결정 2026-10-12 "1~4까지 새로고친 네 제안대로 해" 1절 D-2, D-1·D-3 = 사용자 결정 2026-10-12 "5절 권고대로" -- **결정됨**):
   - **규칙**: MOS는 d/s에 대해 물리적으로 대칭이다. 자기동형은 한 MOS의 drain을 상 MOS의 source로 보낼 수 있다(자기 자신으로 가며 d/s를 맞바꾸는 것 포함). 계획 DEC-97 (3)의 '방향 없는 원소'를 2단자 수동소자에서 MOS d/s까지 넓힌 것이다(D-3).
   - **그래프 하나**(D-2): 정준 위치 `position`, 1-WL 색 `wl`, 자기동형 생성자를 **모두 같은 그래프 하나**에서 정한다. 그 그래프에서 MOS의 `d`·`s` 엣지는 같은 라벨 `c`(채널)다. `g`·`b` 라벨, 원소 처음 색(kind, is_diode, 선언 표시 `_declaration_marks`), 노드 색(레일, 포트 role, 선언 표시)은 그대로다. 그래서 맞바꿈은 gate·bulk 넷과 모든 선언이 보존될 때만 생긴다. 두 번 탐색하지 않는다. 이 그래프는 **대칭 결과**(궤도·정준 위치·`wl`·`dc_colour`·전류 부호)만 정한다. 사이징은 topology의 선언 d/s 방향을 그대로 쓴다(아래 비트 동일 범위, D-3).
   - **불변식 유지**: 한 그래프에서 정하므로 "개별화·정제 뒤 남는 동률 = 정확히 자기동형 궤도"와 graph CONTRACT 4.7 (h) "궤도 ⊆ `wl` 클래스"가 맞바꿈 궤도에서도 성립한다. 궤도 id(구성원 정준 위치 최솟값)와 대표(구조 색 최소)는 이름에 불변이다.
   - **비트 동일 범위**(DEC-97 (4), D-3, 범위 (라) = 사용자 결정 2026-10-13 "1은 권고"): topology의 d/s 표기는 **물리 방향 선언**이다(사용자만 수정하는 정본, 엔진은 고치지 않는다). 이름 전단사·수동소자 단자 순서 변경은 지금처럼 비트 동일 결과(궤도, 정준 위치, `dc_colour`, front 정규화 해시)를 낸다. **MOS d/s 표기 맞바꿈**에 대해서는 **대칭 결과**(궤도, 정준 위치, `dc_colour`)가 비트 동일이고, 전류 부호는 표기 기준 방향 변환(뒤집은 소자 f = −1을 원소·상에 곱함)을 적용하면 동일하다. **사이징 결과**(writer 계획, θ 스키마, ties, front)는 선언 방향을 따르므로 비트 동일 대상이 아니다. 근거: 엔진 51개 파일이 표기 source를 물리 source로 쓴다(U17 ①-d 구현 조사) -- 사이징까지 표기 무관으로 만들려면 엔진 전반을 바꿔야 하고, (라)는 엔진 변경 0이다. 틀린 선언은 봉인 7(VDS − VDsat ≥ tol)이 거부한다: 선언 VDS ≤ 0이라 창 안에 근이 없어 `no_root_in_window`(fail-closed). test: `tests/search/test_orbit_ties.py::test_ds_flip_symmetry_bit_identical`(옛 `test_ds_flip_ties_bit_identical` -- ties 비교를 빼고 대칭 결과만 비교), 봉인 7 거부는 `tests/sizing/test_block_columns.py`(d/s 반대 선언 거부, 바른 선언의 같은 동작점은 통과).
   - **결과(측정 대상)**: d·s 구별이 사라지므로 9 library 회로의 정준 순서·`dc_colour` 순서가 바뀐다(궤도는 2026-10-12 측정에서 맞바꿈 자기동형이 없어 그대로다. 전류 묶음은 KCL 열 순서가 `dc_colour`를 따라 바뀌므로 '그대로'가 아니다 -- §6-3 전류 기저 열 순서 규칙으로 파일럿 (묶음 수 `len(SearchDomain.ties)`, 탐색 θ 변수 수 `len(SearchDomain.variables)`)를 master `8e46548` as-built 값 29/38(그중 전류 묶음 7)로 회복하고(전류 묶음 M1a~M1b 유지, M4a~M4b 대신 M19~M10) 나머지 8회로는 as-built 값 그대로 -- ①-d 실측 일치. 규칙 전 측정값 28/39(전류 묶음 6)는 기록만). 이 순서를 기대값으로 쓰는 test는 **독립 test 작성 주체가 기대값을 다시 만든다**(작성자 ≠ 검증자, 기준 약화 아님 -- 정준 순서 정의가 바뀐 결과).
   - **전류 부호**: 자기동형이 MOS의 drain을 상 MOS의 drain으로 보내지 않으면 그 전류 성분은 부호 −1로 묶인다(2단자 수동소자 규칙과 같다, graph `reverses_orientation`).
   - **자기 맞바꿈 = 구조적 0 전류 → 정지**(design-validator N5): 자기동형이 전도 MOS 하나를 자기 자신으로 보내며 d/s를 맞바꾸면 그 소자 전류는 `I = −I`로 구조적 0이다. 전류 0인 전도 MOS는 gm/ID·VGS 역산이 정의되지 않는다(ID > 0 전제, 봉인 7). 이 분기의 계산 규칙은 만들지 않고(DEC-76) 탐색 전에 `unsupported_rule_branch`(사유 `ds_self_swap_zero_current`, 소자·생성자 기록)로 정지한다. test: 합성 toy(U11 `pass_device` 변형 -- 대칭 두 출력 사이의 통과 MOS 하나)에서 정지와 사유를 단언한다(`tests/graph/test_s1_symmetry.py`, 원본 `graph/s1_symmetry.py`). 9 library 회로는 발동 0이다(측정 2026-10-12).
   - **종류가 다른 소자의 전류 묶음 상자**(D-1, 결정 사용자 결정 2026-10-12 "5절 권고대로"): 맞바꿈이 만든 대칭이 KCL과 함께 종류가 다른 소자의 전류를 묶을 수 있다(예: 완전 차동 직렬 가지 + 출력 사이 R1 toy -- 가지마다 nmos 입력과 pmos 부하가 출력 노드에서 만나고 두 출력 사이에 R1이 있다. 반사가 R1 단자 순서를 뒤집어 I_R1 = 0이고, KCL로 nmos 궤도 {M1, M2}와 pmos 궤도 {M3, M4}의 전류가 궤도를 넘어 묶인다. 옛 예시 'U11 `pass_device` 변형(통과 MOS Mx 포함)'은 위 자기 맞바꿈 정지(`ds_self_swap_zero_current`)에 먼저 걸려 `search_domain`에 닿지 않는다 -- U17 ①-d 통합 test 지적). 궤도를 넘는(KCL 유도) 전류 묶음의 탐색 상자 = 구성원 상자의 **교집합**이고, 비면 실패 레코드 `tied_current_box_empty`로 거부한다. 같은 궤도 안 상자 불일치는 지금처럼 `tied_orbit_bounds_differ`로 거부한다(search CONTRACT 3.24-4). `search_domain` 변경이다(승인됨).
   - **범위**: U2(`canonical_form`, `automorphism_orbits`, `current_symmetry`)와 `search_domain`(D-1 상자)이 바뀐다. 다른 모듈은 U2 결과를 그대로 소비한다. D-SYa~c·R16의 궤도·묶기·해제 규칙은 그대로다.
   - **계획 정정**: 계획 DEC-97 (1)(3)(4)를 같은 커밋에서 고쳤다(v6.5 정합 정정).

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
| LUT memo 상한 | v1.6: S0당 인스턴스 하나, 계수 상태로 시작해 고정(첫 평가를 버리지 않는다), `memo.call(fn, *args)` 순수성(`lut` 패키지 함수만). 상한 식과 퇴출 판정은 U-60 결정 (가)(§2.4.6): 상한 N_T 무관, 퇴출 허용, 퇴출 뒤 재계산 0. test의 상수 4096을 지운다 | DEV(bd19cc6: `_wire_sweep_memo`가 sweep 항만으로 두 번째 인스턴스를 만들고 계수용 첫 평가를 버린다, `E/search/search_context.py:105-121`) |
| tol_V 디스크 캐시 | 키 = 코드 버전 + 입력 내용 sha + 설정 지문. 저장소 밖 경로, 원자적 쓰기, 깨지면 재계산. 정리는 첫 쓰기 때만, 저장소와 모든 worktree의 `lut_v2_location.json`이 가리키지 않는 자료 id만 지우고, 사용 중·링크·폴더 밖 파일은 건너뛴다(사용자 결정 2026-10-08) | PART `[ng-tolv-cache]`: `TableCache`가 `__all__`에 없고 test가 없다. 계획서 N3.5 '디스크 캐시 위치' 문구를 갱신해야 한다 |
| 1변수 풀이 | Brent `bracket_root` + 입력 재사용 memo + 평가 안 tol_V 셀 재사용. v1.6: `solve_self` 근은 LUT memo 순수 함수, `tol_cells`는 memo로(§2.4.6) | OK(master `004b7d2`, `E/sizing/bracket_root.py`). v1.6 형태는 DEV(클로저 memo, `block_columns.py:177,397-398`) |
| core 성능 2~5 | memo 키, 레코드 지문 보관, 투영 지문, 열 키 캐시 | OK(master 병합) |
| 블록 국소 모델 | 블록 노드 부분 MNA를 봉인 스냅샷당 한 번 조립하고, ω=0 극한 풀이만 한다(41 §2.3) | MISS |
| GB4 상한표·출발 구간 | S0 수준 graph 필드(§2.4.8). S0당 한 번, 같은 S0의 다음 실행은 디스크 스냅샷에서 계산 0(§2.4.3) | DEV(S0당 한 번이지만 객체 사본이고 실행마다 다시 계산. `ParamTables`는 두 벌) |
| 중복 계산 계수(G-10) | (블록, 분할)별 reuses·grafts·computes·recomputes_same_input, memo·S0 스냅샷·S3 색인 계수, 9회로 test(§2.4.9) | PART(`BlockStats`, `recompute_same_key`만) |
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
| R3 | GB4를 'INFEASIBLE_TARGET만'으로 축소, DOF·수치 rank 범위 밖 | R §0.2 행 33, K6. 계획 N6.1 단위 7('GB4 축소')에도 반영됨 | FR-8, GB4, IC6 | **복원**(Q1, 41 §4.5) | 구조 DOF와 수치 rank 복원(표본 수 = `dof_rank_sample_count`, 41 §4.5). 블록 gain 상한은 계획대로 격자 전수로 계산하고, 예산을 넘으면 '미상'으로 둔다(41 §4.2) |
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
| Q11 | U-59 | 잡음: 파일럿은 `noise_out_int_vrms ≤ 300 µVrms`(CMFB·바이어스 포함, 하한 1 Hz, 상한은 유도값)이다. 스위치 kT/C 항은 파일럿이 `sampling_caps`를 선언하지 않아 0이다(41 §7, 결정 C-2). 나머지 7회로는 `noise_excess_th ≤ 2`에 열잡음 평탄값·1/f corner 보고를 더한다. pushpull_follower는 보고만 한다. LUT에 저주파 점을 추가한다. DEC-96을 고친다(41 §7) |

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

### 9.4 남은 J 항목 (계획 N7.1, ratify 전)

J-A~J-F(§9.3)가 닫은 것 밖의 J 항목이다. ratify 전에는 엔진 유도 결과(`derived`)를 쓰고, 선언과 어긋나면 `review_needed`로 GB4 전에 정지한다(P N3.3). 아래 '현재 기본안'은 계획 N7.1 문언에 기본안이 있으면 그것이고, 없으면 '엔진 유도'다. 어느 행도 ratify되지 않았다.

| J | 내용(요약) | 현재 기본안 | 상태 |
|---|---|---|---|
| J2 | diode gate 소자의 gate→drain을 같은 stage(미러)로 볼지(nmcnr M201→M203/M204) | 엔진 유도(41 §1 셀·stage 규칙) | 열림 |
| J3 | class-AB(J3-ac 블록 경계, J3-dc `kvl_branch`·정지전류·루프 종속 gm_id·방향별 전류) | stage1 출력노드 = Vop1(계획 문언 기본안) | 열림 |
| J5 | 5T 미러부하·NMCNR 폴딩 미러의 기모드 축약 | 엔진 유도 | 열림 |
| J6 | 출력노드 부하 귀속(파일럿 M18a/M19/M18b, nmcnr M104/M106) | 엔진 유도(규칙 3 load) | 열림 |
| J8 | `fold_group`·`shared_gm_id_groups`·노드 비공유 옛 `budget_reference_device` 선언 4건·의도 태그 | 엔진 유도(태그는 유도 입력이 아니다, U-50). `budget_ref` 엣지는 없다: 공유 노드 옛 선언의 역할은 기둥이 흡수한다(§3.2, 사용자 결정 2026-10-12 "다로 해"). 비공유 4건(M61, M68, M38, two_stage M4)은 이 J8 엔진 유도로 다룬다 | 열림(`budget_ref` 부분은 결정됨) |
| J10 | follower·pass 끝 경로의 독립 블록 여부 | 독립 버퍼 블록(DEC-57, DEC-63 경계 절차) | 열림 |
| J12-a | 버퍼 블록 경계 3건 | 엔진 유도(DEC-63) | 열림 |
| J12-b | A·B·N17·N20 구동 종류 | 전압 구동(용어집 혼재 우선 규칙). N17·N20은 41 §1.5-4 C-1 보완 (가)의 follower 판정이 구조로 정한다(사용자 결정 2026-10-12 "1, 가로 해", §3.2-3 사실 불필요) | 열림(A·B·값 의존 노드·load 귀속) |
| J12-c | G_vgs 사이클 판독·분류(DEC-64) | 엔진 유도 | 열림 |
| J12-d | M17/M20 = K8 측면 주입 대 분기·합류(DEC-81) | K8(계획 문언 기본안). **ratify되지 않았다** -- §3.3 K8 레코드는 이 기본안에서 나온다 | 열림 |
| J12-e | 출력 방향 분류(DEC-65) | 엔진 유도 | 열림 |
| J12-f | 루프 종속 gm_id 소자 선택·합류 노드 KCL | 엔진 유도 | 열림 |
| J12-g | two_stage_ota_sf follower M8의 Miller 루프 밖 여부 | 엔진 유도 | 열림 |
| J12-i | common_gate_amplifier 대조표 | 규칙 유도 결과 그대로(계획 문언) | 열림 |
| J13 | 가지·기둥 유도와 매핑표 대 `vertical_stack_id` | DEC-71 (1)(2) 유도 규칙 그대로, 불일치만 확정(계획 문언) | 열림 |
| J9 | folded·nmcnr `ports`, nmcnr·two_stage `passive_elements` 누락 | 선언 데이터로 해소 -- 현 library topology에 `ports`(각 4개)·`passive_elements`(folded 1, nmcnr 5, two_stage 3)가 있다(측정 2026-10-12 gap 재분석 정정). 회로 해석이 아닌 선언 누락이라 J ratify 없이 닫는다 | 닫힘 |
| J14(sf 밖 8회로) | matching 분류 9회로 대조표 중 sf 외 회로의 matching 레코드(`diff_pair`·`mirror`·`branch_symmetric`·`bias_distribution`·`feedback_shared`) ratify | 엔진 유도(DEC-93 (1) 규칙) | 열림 |

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
| d/s 비트 동일 범위(§6-8 D-3, (라)) | (a) d/s 표기만 맞바꾼 입력(전류 부호는 뒤집은 소자 f = −1 손 유도 변환), (a) d/s를 반대로 선언한 toy(선언 VDS ≤ 0) | `tests/search/test_orbit_ties.py::test_ds_flip_symmetry_bit_identical`(옛 `test_ds_flip_ties_bit_identical`), `tests/sizing/test_block_columns.py`(봉인 7 거부) | 궤도·정준 위치·`dc_colour`(노드·원소) 비트 동일, 전류 부호는 뒤집은 소자 f = −1을 원소·상에 곱한 뒤 동일. ties·writer 계획·θ 스키마·front는 비교하지 않는다(선언 방향을 따름). 반대 선언 → 봉인 7 `no_root_in_window`(item 7) 거부, 바른 선언의 같은 동작점 → 봉인 7 통과 |
| diff_pair review(§6-5, (나')) | (d) 9 library 회로, (a) 파일럿에서 넷 하나를 비대칭으로 바꾼 합성 회로 | `tests/graph/test_orbit_matching_crosstab.py`(원본 `graph/orbit_matching_crosstab.py`) | 9회로 review 0(각 회로 `orbit_matching_crosstab` 기록). 합성 회로: (a)(b)를 만족하는 `diff_pair`가 다른 궤도가 되어 `review_needed`(코드 `diff_pair_orbit_split`). 출력 포트가 단일이거나 gate가 입력 포트가 아니면 crosstab 기록만 |
| 전류 기저 열 순서(§6-3) | (d) 9 library 회로 | `tests/sizing/test_current_basis.py`(기존 파일에 추가) | (묶음 수, 탐색 θ 변수 수) = (`len(SearchDomain.ties)`, `len(SearchDomain.variables)`): 파일럿 29/38, 그중 전류 묶음(대표가 θ 전류 성분) 7(M1a~M1b 묶임, M19~M10 묶임), 나머지 8회로는 master `8e46548` as-built 값과 같음. 28/39(규칙 전, 전류 묶음 6)는 기록만. 열 정렬에서 비자명 궤도 원소가 뒤(자유 열로 남음). 열 순서 키가 이름 전단사에 불변 |
| 궤도 넘는 전류 상자(§6-8 D-1) | (a) 완전 차동 직렬 가지 + 출력 사이 R1 toy(nmos·pmos 궤도 전류가 KCL로 묶임, 구성원 상자 교집합 빈 경우·안 빈 경우. `ds_self_swap` 정지에 걸리지 않는다) | `tests/search/test_search_domain.py`(기존 파일에 추가) | 빈 교집합 → `tied_current_box_empty` 거부, 같은 궤도 안 불일치 → `tied_orbit_bounds_differ` |
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
| IC11 | `test_rail_origin_shift_invariance` | 거부 먼저: 합성 음전위 레일 회로·`pushpull_follower_buffer`(`supply_nets` 삭제). 동등: `two_stage_ota` (1.8, 0) 대 (0.9, −0.9) V, `pushpull_follower_buffer` (1.8/0/0.9) 대 (0.9/−0.9/0) V(§3.10.8과 같은 회로) | VGS·VDS·VSB·gm_id·W·metric이 tol 안에서 같음 | 10 |

### 10.3a DF 재발 금지 표 (P N5.2, 사용자 승인 2026-10-12 P-8)

P N5.2의 DF는 옛 엔진의 결함 기록이고, 새 엔진에서는 재발 금지 계약이다. DF마다 계약 test 또는 구조 lint 하나를 두고, 그 test가 걸린 구현 단위(§11)의 완료 조건에 넣는다. test는 처음부터 TS7 규칙(§3.10.8)대로 `xfail(reason="<단위>", strict=True)`다. '상시'는 매 변경마다 도는 구조 test(`E/tests/structure/`, 규칙 A~I와 §2.4.10 확장)다. test 파일 이름은 test 작성 주체가 확정하며, 확정하면 이 표를 갱신한다.

| DF | 재발 금지 내용(새 엔진) | 계약 test | 담당 단위 |
|---|---|---|---|
| DF-01 | 옛 입력 버전으로 계산한 파생 필드는 봉인 4가 거부(버전 혼재 금지) | `tests/sizing/test_df01_stale_input_version_rejected` (+ IC10) | U4 |
| DF-02 | 노드 경로 충돌은 봉인 1이 거부 | `tests/sizing/test_df02_node_conflict_rejected` | U4 |
| DF-03 | 후보 실패는 `ValueError`가 아니라 N3.14 실패 레코드이고 탐색이 계속됨 | `tests/search/test_df03_candidate_failure_continues` | U11 |
| DF-04 | 소자는 정확한 이름(또는 구조)으로만 찾음, 부분문자열 금지 | 구조 규칙 E(이름 리터럴) + IC4 | 상시 |
| DF-05 | 미러비 σ는 그룹의 모든 쌍을 봄 | `tests/metrics/test_df05_mirror_ratio_all_pairs` | U7 |
| DF-06 | 광범위 except 금지 | 구조 규칙 F | 상시 |
| DF-07 | 상한에 닿으면 LRU 퇴출(캐싱 중단 금지). U-60 결정 (가)에서 퇴출은 정상 동작이고 퇴출된 키의 재계산만 FAIL이다(§2.4.6) | `tests/core/test_df07_bounded_lru_evicts` | U17 ③ |
| DF-08 | spec 지문 불일치면 유도 임계값을 쓰지 않고 거부 | `tests/authoring/test_df08_fingerprint_mismatch_rejected` | U5 |
| DF-09 | 면적 예산 식이 선언 계수를 상쇄하지 않음(§7.1 식 손계산 대조) | `tests/search/test_df09_area_budget_formula` | U11 |
| DF-10 | 역산(VGS·L·gm/ID)은 단조 구간 밖에서 근을 내지 않고 실패 레코드를 냄 | `tests/lut/test_df10_inverse_monotonic_guard` | U3 |
| DF-11 | LUT 조회 실패 시 대입값 금지(실패 레코드) | `tests/sizing/test_df11_no_substitute_on_lut_failure` | U4 |
| DF-12 | 입력환산 offset은 모든 소자의 기여를 셈(gm 없는 소자를 조용히 빼지 않음) | `tests/metrics/test_df12_offset_all_devices` | U7 |
| DF-13 | `id()` 키·상한 없는 캐시 금지 | 구조 규칙 G 확장(§2.4.10) | 상시(U17 ③에서 활성) |
| DF-14 | `except Exception` 폴백 금지 | 구조 규칙 F | 상시 |
| DF-15 | 영점 상쇄 R은 입력 버전 있는 필드(`device.passive_value`) | `tests/metrics/test_df15_zero_cancel_is_versioned_field` | U17 ① |
| DF-16 | 전력 축 = 선언 레일 Σ V·I(직렬 기둥 중복 계상 없음) | `tests/metrics/test_df16_power_rail_sum` | U7 |
| DF-17 | 기대값·기준선 파일에 실패 출력(FAIL 문자열, 예외 메시지, 실패 판정 값)이 들어 있지 않음. 아직 통과하지 못하는 계약은 `xfail(strict=True)`로만 표시 | `tests/structure/test_df17_no_failing_baseline`(기대값 파일 전수 검사 + `xfail`에 `strict=True` 없는 test 0) | 상시 |
| DF-18 | 실패하면 0이 아닌 exit code(`exit_code_for`), θ*는 결과 JSON에 기록 | `tests/pipeline/test_df18_exit_code_on_failure` | U16 |
| DF-19 | 레일은 선언(`supply_nets`·`supplies_v`)으로만 판정 | `tests/authoring/test_df19_rails_from_declaration` (+ IC11) | U5 |
| DF-20 | 근거 없는 폴백 상수 금지 | 구조 규칙(숫자 리터럴) | 상시 |
| DF-21 | 실행 불가 probe 금지 -- 새 엔진에는 probe 폴더가 없다 | 구조 규칙(파일 구성 A~D) | 상시 |
| DF-22 | 지문 불일치 기록은 거부로 이어짐(DF-08과 같은 test) | `test_df08_fingerprint_mismatch_rejected` | U5 |
| DF-23 | 소자·넷·회로 이름 리터럴이 동작을 정하지 않음 | 구조 규칙 E + IC4 | 상시 |
| DF-24 | vsb는 bulk 선언과 노드전압에서만 유도(레일 원점 가정 금지) | IC11 `test_rail_origin_shift_invariance` | U16 |
| DF-25 | 포화 하한은 LUT `VDSAT` 열(2/(gm/ID) 금지) | `tests/sizing/test_df25_seal7_uses_vdsat_column` | U4 |
| DF-26 | 레일 판정에 넷 이름 집합 금지(DF-19와 같은 test) | `test_df19_rails_from_declaration` + IC11 | U5 |
| DF-27 | LUT 축 밖 입력은 실패 레코드(클램프·외삽 금지) | `tests/lut/test_df27_axis_out_of_range_rejected` | U3 |
| DF-28 | CGS·CGB 열이 없으면 근사 표시를 기록(조용한 근사 금지) | `tests/metrics/test_df28_cgs_cgb_approximation_flagged` | U7 |
| DF-29 | metric이 회로 파일·넷 이름 리터럴을 열지 않음 | 구조 규칙 E + IC4 | 상시 |
| DF-30 | metric 등록부에 회로 이름 키 없음 | `tests/metrics/test_df30_registry_no_circuit_keys` | U7 |
| DF-31 | 보상 규칙에 회로별 함수 없음(구조 판정) | `tests/metrics/test_df31_no_circuit_compensation` | U7 |
| DF-32 | 헤드룸은 S1 유도 역할로만(라벨 금지) | IC4 `test_role_label_removal_invariance` | U13 |
| DF-33 | spec에 소자 이름 기반 override 필드 없음(로더 거부) | `tests/authoring/test_df33_device_override_rejected` | U5 |
| DF-34 | 회로마다 코드 추가 없이 9회로 실행(PDK 상수는 PDK 선언 하나) | IC7 `test_all_library_topologies_run` | U16 |
| DF-35 | 저장소 절대 경로를 코드에 박지 않음 | `tests/structure/test_df35_no_absolute_repo_paths` | 상시 |
| DF-36 | 산출물의 경로는 저장소 루트 기준 상대 경로 | `tests/report/test_df36_relative_paths` | U16 |
| DF-37 | 광범위 except가 N3.14 클래스를 삼키지 않음 | 구조 규칙 F | 상시 |

### 10.4 DoD 명령

`$PY` = `C:\Python314\python.exe`, 작업 위치는 저장소 루트다.

**공통 완료 조건**: 모든 엔진 코드 변경 단위는 아래 표의 해당 명령과 함께 **graph 단일 정본 확인**(사용자 결정 2026-10-12 "design 승인, 이후에는 design과 구현을 gap분석해. 그리고, 모든엔진은 graph 단일정본 원칙이 준수되었는지를 coding후에 항상 확인하는 과정을 넣어."): 엔진 코드를 바꾸는 모든 변경 단위는 병합 전에 다음 넷을 통과한다. (a) 구조 규칙 G 확장 lint(G-8, §2.4.10 ①) green (b) 설계 값 타입 위치 검사(§2.4.10 ②) green (c) 40 §2.4.8 필드 소유표 대조 -- graph 밖 저장소는 허용 넷(LUT memo 순수 함수, S3 기록·색인, 실행 계수, S0 수준 스냅샷 직렬화)뿐이고 새로 생긴 값은 graph 필드다. 새 필드는 같은 변경에서 소유표에 행을 더한다 (d) G-10 중복 계산 계수(§2.4.9)를 그 변경이 건드린 회로에서 잰다: 같은 실행 안 같은 입력 버전 재계산 0, 같은 S0 두 번째 실행의 S0 수준 계산 0, LUT memo 퇴출 뒤 재계산 0. 그리고 구현 단계(U17 ①②③과 각 구현 단위)가 끝날 때마다 design ↔ 구현 gap 분석(bkit gap-detector, 일치율 90% 이상, 미만이면 반복 개선)을 한다. 명령은 표의 'graph 단일 정본 확인' 행이다. **계산값 재사용 확인**(사용자 지시 2026-10-12 "coding시에 계산값 재사용원칙도 준수되었는지 확인하는 과정을 넣고 이 확인내용을 항상 보고해"): (a) G-10 계수 -- 같은 실행 안 같은 입력 버전 재계산 0, 같은 S0 두 번째 실행의 S0 수준 계산 0, LUT memo 퇴출 뒤 재계산 0 (b) 계산 블록·분할·필드별 재사용(`reuses`·`grafts`)과 재계산(`computes`) 계수를 `perf`에 기록 (c) cProfile + 중복 인자 계측으로 루프 안 같은 인자 반복 호출 0(WP-10) (d) 루프 불변식이 루프 밖(S0 수준 필드, WP-23 (3))으로 나갔는지 확인. **두 확인(graph 단일 정본·계산값 재사용)의 결과는 숫자와 함께 단위 보고에 항상 넣는다**(단위 보고 필드 `graph_canon_check`·`reuse_check`).

| 범위 | 명령 |
|---|---|
| 전체(slow 제외) | `$PY -m pytest skills/analog-gmid-design/gmid_engine/tests -q -m "not slow"` |
| IC 계약 | `$PY -m pytest skills/analog-gmid-design/gmid_engine/tests -q -k "test_ic"` |
| 9회로 구조 표(S1v·A_max·Π·인증 비율) | `$PY -m pytest skills/analog-gmid-design/gmid_engine/tests/integration/test_structure_tables.py -q` |
| 9회로 E2E(T9) | `$PY -m pytest skills/analog-gmid-design/gmid_engine/tests/integration -q` |
| 오라클 | `$PY -m pytest skills/analog-gmid-design/tools/spice_oracle/tests -q` |
| graph 단일 정본 확인((a)(b) 정적, (d) 계수)과 계산값 재사용 확인((a)(b) `perf` 계수, (c) `--profile`, (d) 루프 불변식 대조) | `$PY -m pytest skills/analog-gmid-design/gmid_engine/tests/structure -q -k "rule_g or design_value_location"` 뒤 `$PY -m pytest skills/analog-gmid-design/gmid_engine/tests/integration -q -k "g10"`(건드린 회로). (c)는 변경 diff와 §2.4.8 소유표를 대조해 보고에 적는다 |
| design ↔ 구현 gap 분석 | bkit gap-detector(42 기준표 기준), 일치율 90% 이상 |
| 계산값 재사용 확인 (c) 중복 인자 호출 | `$PY -m gmid_engine.pipeline <spec> --profile runs/<run_id>/profile.out --instrument runs/<run_id>/dup_args.jsonl` 뒤 `$PY -m pytest skills/analog-gmid-design/gmid_engine/tests/perf -q -k "duplicate_args or loop_invariant"`: 루프 안 같은 인자 반복 호출 수 = 0(WP-10), 루프 불변 입력이 S0 수준 필드에서 읽힘(WP-23 (3)). 결과 숫자는 단위 보고 `reuse_check`에 넣는다 (사용자 지시 2026-10-12 "coding시에 계산값 재사용원칙도 준수되었는지 확인하는 과정을 넣고 이 확인내용을 항상 보고해") |
| P N6.2 단위 4(IC9, 공유 gate 넷 전압 하나, 4회로 KCL 잔차 ≤ tol_I, IC1·IC2·IC10) | `$PY -m pytest skills/analog-gmid-design/gmid_engine/tests/sizing -q -k "ic1 or ic2 or ic9 or ic10 or shared_gate_net or kcl_residual"` |
| P N6.2 단위 5(MNA 조립 계수 1, 풀이 계수 = ω 수) | `$PY -m pytest skills/analog-gmid-design/gmid_engine/tests/metrics -q -k "mna_assembly_count or mna_solve_count"` |
| P N6.2 단위 6(cProfile 기록 파일, WP-23 계수) | `$PY -m gmid_engine.pipeline <spec> --profile runs/<run_id>/profile.out` 뒤 `$PY -m pytest skills/analog-gmid-design/gmid_engine/tests/perf -q` |
| P N6.2 단위 10(IC11 2·3레일, push-pull 등식 잔차 ≤ 멤버 수 × tol_V) | `$PY -m pytest skills/analog-gmid-design/gmid_engine/tests/integration -q -k "ic11 or kvl_branch_residual"` |
| 공유 블록 전후 대조(DEC-51) | `$PY tools/compare_runs.py --before <base 결과 디렉터리> --after <변경 결과 디렉터리>`: 9회로 노드전압·front·SPICE verdict 차 표를 쓴다. verdict 차가 있으면 보고 맨 앞 |

### 10.5 A' 판정 기준 (P DEC-98, U17 단계 ② 완료 조건)

사용자 결정 2026-10-13 "1은 권고, 2도 권고, 3도 권고대로" (3)과 "①, ②, ③ 권고대로 진행해" ①. 이 절은 규칙만 적는다. 첫 사례(nmcnr 시범)의 경위·수치는 계획 history H1·H4에 있다.

| 역할 | 누구 | 규칙 |
|---|---|---|
| 판정자 | ngspice(`tools/spice_oracle/`, §4) | 합격 정의 = P N6.2 T4·T5(DEC-90). 엔진 점과 손분석 설계를 같은 정의로 판정한다 |
| 독립 대조군 | AI 손분석 | 엔진 코드를 보지 않는다. 회로마다 1회 문서로 고정한다. 값마다 유도 근거(회로 원리·LUT 조회·spec 값)를 적고 상수를 발명하지 않는다(P WP-03). 결과는 엔진 입력(spec·topology·`structure.json`·출발값)으로 쓰지 않고 판정 기준으로도 쓰지 않는다(판정은 ngspice) |
| 피검 | 엔진 시작점(층 0·출발 구간, 41 §5·§6)과 front | 단계 ② 완료 조건은 시작점을 본다. front(T6·T7)에는 A' 판정을 적용하지 않고 손분석점과의 전력·면적 차만 기록한다(P U-76 (6) 기본안) |

**판정 규칙**

| 엔진 | AI 손분석 | 분류 | 기록 |
|---|---|---|---|
| 실패 | 통과 | 엔진 결함 | A' 대조표로 원인 |
| 통과 | 실패 | AI 해석 오류 | 사용자 공동분석(P N7.1) |
| 통과 | 통과 | -- | 전력·면적 차 |
| 실패 | 실패 | 판정 불능(P U-76 (2) 기본안) | 사용자 공동분석(AI만 실패와 같은 경로), 원인 확정 전 완료 아님 |

* 엔진 실패 = 아래 완료 조건의 점을 내지 못함(봉인 미통과 또는 spec 제약 행 c < 0) 또는 그 점의 ngspice 불합격. AI 실패 = 손분석 설계의 ngspice 불합격(두 정의는 결정 문언 풀이).
* A' 대조표 = 같은 항목(소자 L·gm/ID·ID·W, 노드전압, 보상 소자 값, spec 제약 행 c 등)에서 손분석 값과 엔진 값을 맞대고, 갈린 항목마다 회로 원리 근거의 원인 가설을 적은 표. 손분석과 대조표는 `docs/03-analysis/aprime/<회로>.md` 한 문서이고, 실측 원본(넷리스트·로그)은 그 문서에서 경로로 참조한다(P U-76 (6) 기본안).

**U17 단계 ② 완료 조건**

1. 대상 = library 9회로 + held-out 회로. held-out = library 9회로 밖이고 엔진 개발(코드·test 픽스처·`structure.json` 사실·spec 값 조정·발동표 측정)에 쓰지 않은 회로. **선정은 사용자 몫**(P U-75).
2. 회로마다 엔진이 시작점(층 0·출발 구간)으로 봉인 통과(P N3.6)이고 spec 제약 행(`graph/metrics: constraint_rows`, §2.4.8)이 모두 c ≥ 0인 점을 내고, 그 점이 ngspice **T4-pre**·T5를 통과한다. 미측정 제약 행(§2.4.12 Q8)과 `spice_unverifiable[]` 제약은 c ≥ 0 판정에서 빼고 보고서에 목록으로 낸다. ngspice는 측정할 수 있는 항목만 판정한다(P U-76 (4) 기본안).
   - **T4-pre**(P U-76 (3) 기본안): 시작점은 MOD8 전 단계이므로 넷리스트 W = sizing W 그대로(레이아웃 전). 접합 용량 ad/as/pd/ps는 LUT 특성화와 같은 기하 규칙 -- `assets/sky130_lut_sweep.py` `DUT_LINE`(w = 5 µm, ad = as = 2.5 pm², pd = ps = 7 µm)을 W에 비례시킨다. 판정 정의는 T4와 같고 기하만 다르다. 최종 front 판정은 기존 T4·T5 그대로다.
3. 실패 회로는 A' 대조표를 남긴다. 실패 회로가 남으면 완료가 아니다(fail-closed). 회로별 예외는 그 회로의 대조표 + 사용자 결정으로만 둔다(P U-76 (1) 기본안).
4. library 9회로 도달률(2를 만족한 회로 수 / 9)은 회귀 지표로만 기록한다. 일반성의 근거는 held-out 회로다.
5. held-out 회로의 실패를 고치려고 엔진을 바꾸면 그 회로는 개발 회로로 옮기고, 다음 일반성 판정에는 새 held-out 회로가 필요하다(P U-76 (5) 기본안).
6. 1·2·3·5의 세부와 위 대조표 위치는 결정 원문 밖이라 원칙으로 정한 기본안이다(P U-76, 사용자 변경 가능).

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
  - **graph 단일 정본 확인**(사용자 결정 2026-10-12 "design 승인, 이후에는 design과 구현을 gap분석해. 그리고, 모든엔진은 graph 단일정본 원칙이 준수되었는지를 coding후에 항상 확인하는 과정을 넣어."): 엔진 코드를 바꾸는 모든 변경 단위는 병합 전에 다음 넷을 통과한다. (a) 구조 규칙 G 확장 lint(G-8, §2.4.10 ①) green (b) 설계 값 타입 위치 검사(§2.4.10 ②) green (c) 40 §2.4.8 필드 소유표 대조 -- graph 밖 저장소는 허용 넷(LUT memo 순수 함수, S3 기록·색인, 실행 계수, S0 수준 스냅샷 직렬화)뿐이고 새로 생긴 값은 graph 필드다. 새 필드는 같은 변경에서 소유표에 행을 더한다 (d) G-10 중복 계산 계수(§2.4.9)를 그 변경이 건드린 회로에서 잰다: 같은 실행 안 같은 입력 버전 재계산 0, 같은 S0 두 번째 실행의 S0 수준 계산 0, LUT memo 퇴출 뒤 재계산 0. 그리고 구현 단계(U17 ①②③과 각 구현 단위)가 끝날 때마다 design ↔ 구현 gap 분석(bkit gap-detector, 일치율 90% 이상, 미만이면 반복 개선)을 한다. **계산값 재사용 확인**(사용자 지시 2026-10-12 "coding시에 계산값 재사용원칙도 준수되었는지 확인하는 과정을 넣고 이 확인내용을 항상 보고해"): (a) G-10 계수 -- 같은 실행 안 같은 입력 버전 재계산 0, 같은 S0 두 번째 실행의 S0 수준 계산 0, LUT memo 퇴출 뒤 재계산 0 (b) 계산 블록·분할·필드별 재사용(`reuses`·`grafts`)과 재계산(`computes`) 계수를 `perf`에 기록 (c) cProfile + 중복 인자 계측으로 루프 안 같은 인자 반복 호출 0(WP-10) (d) 루프 불변식이 루프 밖(S0 수준 필드, WP-23 (3))으로 나갔는지 확인. **두 확인(graph 단일 정본·계산값 재사용)의 결과는 숫자와 함께 단위 보고에 항상 넣는다**(단위 보고 필드 `graph_canon_check`·`reuse_check`).

**U0 -- 선행 병합**(오케스트레이터, code agent 아님)
- 대상 브랜치: `ng-cmfb-pm`, `ng-oracle-early`(계약), `ng-tolv-cache`, `ng-layer0-canon`, `ng-area-budget`, `worktree-agent-a90dfb25fa6fe9f04`(LUT r2), `ng-bridge`.
- 이 브랜치들을 병합하고, 병합할 때마다 전체 suite를 돌린다(사용자 결정 3).
- 이후 단위들은 병합된 master를 출발점으로 쓴다.

| 단위 | 범위(소유 파일·패키지) | 설계 절 | 선행 | 웨이브 | 확인 행(42) | test 계획 |
|---|---|---|---|---|---|---|
| **U1 SP1 구조** | `E/graph/` 신규 파일: `views`, `ac_ground_view`, `signal_reach`, `cells`, `drive_kind`, `stage_bfs`, `blocks`, `pole_nodes`, `loops`, `loop_classify`, `loop_cuts`, `polarity`, `buffer_bundles`, `output_direction`, `composite_blocks`, `declared_compare`, `s1v_build`. `structure.json` 로더. L 동치류 `derived` 처리와 주인 결정 | 41 §1, 40 §3.2 | U0 | 1 | FR-1, DEC-17·29·43·57·63·65·81, D-GB1a, D-GB2a~j | 41 §9 SP1·루프 행. toy 2~4소자(a), 9회로 표(d), 이름 전단사 |
| **U1b J 규칙 + structure 사실** | `E/graph/` 신규 파일 `composite_diode.py`, `feedforward_cells.py`, `loop_roles.py`. 수정 파일: `dc_roles.py`(규칙 1c 복합 diode, 규칙 4 `dc_role` 상속), `s1_build.py`(`structure` 인자, S1 키에 사실 지문), `drive_kind.py`(미러 입력 확장), `cells.py`(복합 diode 묶음 `diode_load`), `stage_bfs.py`(diode 단자 비용), `blocks.py`·`composite_blocks.py`(FF 분리, FF 합류는 복합 블록 아님), `loop_classify.py`((1.6) 추가, (나) 축소), `polarity.py`(DC 사이클 극성·`ac_only`), `l_classes.py`(`main_path_signal`), `view_analysis.py`, `ac_ground_view.py`(뷰 한정 예외), `matching_groups.py`(`matching_pair`), `structure_load.py`(concept 어휘·override/confirm·고아·불일치), `s1v_values.py`·`s1v_key.py`(`structure_rule_fp`), `s1v_build.py`(`loop_roles` 소비, `applied_facts`). `E/pipeline/stage_a.py`·`stage_a_report.py`(사실 로드 순서, `declared_loop_cuts`, 보고 행). `graph/CONTRACT.md`·`pipeline/CONTRACT.md` 해당 절 | 41 §1.12·§1.13, 40 §3.2-3, §9.3 | U1·U2 병합(U1 = `[u1-sp1]`·`[u1-sp1-tests]`) | 2 | D-J1~D-J7 | 41 §9의 J 행 5개(toy (a), 9회로 (d), 거부 확인, red test 먼저). 9회로 발동표: D1 = 41 §1.13 실측 집합, 나머지 7회로 무동작. FF는 ngcc만. 루프 뷰·정지·review 수의 U1 대비 변화표. 이름 전단사 불변. **사실 파일 작성은 이 단위가 아니다**: 병합 뒤 오케스트레이터가 §3.2-3 표를 실측과 대조해 쓴다 |
| **U2 대칭** | `ng-layer0-canon`의 정준 라벨링·궤도를 `E/graph/canonical_form.py`·`automorphism_orbits.py`로 옮긴다. 수동소자 무향 처리와 부호 −1 묶기. `orbit_matching_crosstab`(`E/graph/orbit_matching_crosstab.py`, test `tests/graph/test_orbit_matching_crosstab.py` -- diff_pair review (나') 포함). `E/search/orbit_ties.py`·`tie_expand.py` 갱신 | 40 §6 | U0 | 1 | D-SYa~d, R16 | 40 §10.2 대칭 행. 파일럿 R1/R2 궤도, 단자 순서 뒤집기 metamorphic |
| **U3 LUT·PDK 확장** | `E/lut/`: `vgs_for_current_density`, VS Hermite, FC 정책, `ft_curve`·`intrinsic_gain_curve`·`vdsat_curve`·`idu_curve`, `noise_params`, 잡음 LUT r1 로더, `LutMemo.from_sweep` 배선 도우미. `assets/sky130_lut_sweep.py`에 `.noise` 모드와 **mismatch 감도 모드**(Q3: `*_slope_spectre` 섭동 → DVGS 열, 새 버전 파일 `..._mismatch_r1.npz`, 공유 데이터 덮어쓰기 금지) 추가, `mismatch_dvgs` 로더·`tol_mismatch`. `E/core/pdk_decl.py`와 PDK 선언 json에 EF, mismatch slope(카드 `.model` 블록별 bin 지도 + slope 이름, pfet L < 0.5 µm `vth0_slope1` 등), poly 저항 양 추가 | 41 §4.1, §6.4-2·2b, §7.2, 40 §7.1, R25 | U0 | 1 | DEC-87·88, D-LUTc, D-NZ2, D-PF1·2, D-GB4a(분류 쪽), D-PG, D-MM1·2 | 격자점·칸 중앙 ngspice 대조(c), 감도 열 칸 중앙 섭동 대조(c), `vth0` 성분 = √2·slope(bin별)(a), 소자 쌍 MC 단위 확인(c), Ω당 면적 손계산(a) |
| **U4 sizing 보강** | `E/sizing/`: L 동치류 L 공유(θ 스키마), 미러 비 강제, S2p 기반 tol_I(v1.6 §3.7-3·U17 ①로 대체, G-3' -- 자기 동작점 `dc_gm`), DEC-95 (3) 전체 순서, W_request 고정 W, `size_and_seal_local` | 40 §3.7, 41 §5.3 | U0(② 순서 항목은 U1 인터페이스 필요) | 1 | DEC-17(θ 쪽)·32·70·95, D-GB7a~d, D-LS | IC1·IC2·IC10 test, 국소 봉인 toy |
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
| **U14 MOD8 수렴** | `E/convergence/`: `converge`(W_request 루프, LY7 재평가, 판정 축 재필터, K_max). **U12 인계(2026-10-09)**: 봉인 스냅샷 → `LayoutInput` 어댑터(수동소자는 `layout.passives_from_decl` 사용), `run_layout`의 유일한 프로덕션 호출처, ΔA_tie(`area_tie_m2`)를 `pareto.nondominated(ties=)`에 배선, `LayoutResult.diffusion`(U17 ①-e 뒤 설계점 스냅샷 `ly_diffusion` 필드)·`RealizedDevice.diffusion` 재검증 소비, LY5 즉시 완화를 지운 뒤 W 조정 불가 그룹(pattern None)의 완화 판정 | 40 §3.9 | U4, U12 | 3 | D-M8, R12 | W_request 합성 픽스처, 커널 호출 계수 |
| **U15 층 0 gain 예산** | `E/search/`: `layer0_budget`, `gain_bins`, `local_candidates`, `local_front`, `combo_dp`, `assembly`, `budget_override`, `layer0_inverse`, `l_targets`(41 v1.6 §5.3·§5.10 구현 변경 목록). `layer0_center`는 대체되어 초기점 생성 전용이 된다 | 41 §5 | U4, U7, U9, U10, U13 | 4 | FR-4, DEC-03·10·71·73, D-L0a~i | 2블록 toy DP = 전수, 파일럿 `gain_budget_db` 출력 |
| **U16 보고·진입점·통합** | `E/report/`, `E/pipeline/`(`ng-bridge` 흡수). **인계(2026-10-09)**: (i) 엔진이 정한 finger 폭(mismatch σ의 bin 선택, U7 `device_sigma`: W/ceil(W/w_bin_max(L)))을 오라클 입력으로 넘겨 오라클 넷리스트 `w=finger_w m=n`이 같은 bin을 쓰게 한다(출처 하나); (ii) `build_search_context(s1v=)`로 S1v를 넘기는 진입점(구조 의존 metric·잡음 입력 셀); (iii) U7 `model_error_pairs` 적재(오라클 대조 결과); (iv) 내부 루프 뷰 `loop_cut` 선언의 PM metric 평가 경로(U1b 인계), (v) 결과 JSON이 설계점마다 `layout_outputs(snapshot)`을 한 번 부르는 배선(완료 조건, 사용자 결정 2026-10-12 "4번 권고대로", 42 D-LY5), `tests/integration/`의 9회로 E2E·구조 표·IC7·IC11·회귀 추적 | 40 §3.9, §10 | U14, U15, U6 | 5 | D-M9·M10, D-IC, D-T, T1~T9 | 9회로 E2E, 오라클 대조 |

**U17 graph 단일 정본·중복 계산 제거**(v1.6 graph 정본 개정, 사용자 결정 2026-10-12, design 문안 사용자 승인(2026-10-12 "design 승인")). 설계 절은 §2.4이고 확인 행은 42 D-GR1~D-GR15다. G-9에 따라 41 §5 층 0 개정(U15 재구현)과 같은 design 개정에 묶고, 구현은 세 단계로 순서대로 한다. 단계마다 옛 코드와 그 test를 같은 변경에서 지운다(WP-01). 재작성 범위는 사용자 규칙을 따른다: 옛 구조가 남는 곳은 전체 재작성, 나머지는 부분 수정이다.

| 단계 | 범위(소유 파일) | 재작성 범위 | 같은 변경에서 지우는 것 | 선행 | 확인 행 | test |
|---|---|---|---|---|---|---|
| **① graph 층 이동** | S1v 저장(`E/graph/s1v_build.py` 출력층, `s1v_values.py`의 `S1v` 묶음), GB3 출력(`coupling_vars.py`), U9 출력층(`E/metrics/achievability.py`·`achievability_types.py`의 `Achievability` 묶음), U13 데이터 흐름(`E/search/start_intervals.py`, `iv_context.py`, `iv_curves.py`, `start_values.py`의 `StartContext`·`StartIntervals`), S0 수준 스냅샷 직렬화(신규 `E/core/snapshot_codec.py`·`type_registry.py`, 패키지마다 `__init__` 등록, `E/pipeline/stage_a.py`·`stage_b.py` 배선), 단계 B 층(`residual_probe`·`dof_numeric` 필드, 직렬화 제외), 커널 컨텍스트 구조 파생과 SearchContext 선언 파생의 S0 수준 필드(`E/sizing/kernel_context.py`, `E/search/search_domain.py`, 제약 분류, 접합·mismatch 출처, 면적 선언, 모델 오차), CurveBook·ParamTables의 LUT 파생을 `E/lut/derived_fns.py`로(호출 형식은 ③에서 `call`로), `metrics_dc`의 `gate_area_m2`·`power_resolution_w`(search `_power_resolution` 삭제), 수동소자 값 블록(`E/metrics/passive_values.py` → 계산 블록, 소비자 `ss_evaluate.py`·`search/kernel.py`·`convergence/converge_point.py`. `search/_helpers_area.py`는 출발 구간(S0 층) 추정이라 S2 필드 `device.passive_value`를 읽을 수 없으므로 ①-b(S0 필드 이동)로 이월), tol_I gm 필드(`E/sizing/seal_tolerances.py`, `seal_kcl.py`, `kernel_run.py`, `seal.py`, `E/metrics/ss_linearize.py`, `search/objectives.py`·`search_values.py` b_P), 레이아웃 필드(`E/layout/run.py`, `contract_output.py`의 `LayoutResult`, `E/convergence/` 어댑터) | **전체 재작성**: S1v 저장, U9 출력층, U13 데이터 흐름(`StartContext`·`CurveBook` 폐기), S0 수준 스냅샷 경로. **부분 수정**: 수동소자 값(R = 1/Σ`dc_gm`), tol_I, 레이아웃 출력, `metrics_dc` | `StartContext`, `CurveBook`, `ParamTables` 두 벌 생성, `search/objectives.py`의 `_power_resolution`·`gate_area_m2` 계산, `S1v`·`Achievability`·`StartIntervals` 묶음 전달, `previous_gm_id`·`inherited_gm_id`·`canonical_gm_id`·`gm_grid_max`와 `dc_gm_bound` 필드, `kernel.py:146-150` 수동소자 규칙 사본, `sctx.spec_passive_values`, 레이아웃 별도 lineage(`GraphSnapshot.empty(LY_WRITERS)`), 이것들을 직접 단언하던 test | U9·U13 병합(as-built) | D-GR2·3·7·8·13, D-GR9(레이아웃 부분) | `test_s0_snapshot_roundtrip`, 수동소자 필드 단일 writer, tol_I parent 무관(같은 θ·다른 parent → 같은 봉인 결과), 9회로 front 재측정 기록(Q7) |
| **② search 상태·층 0** | core 분할 계산 블록과 `graft`(`E/core/compute_block.py`, `graph_snapshot.py`의 `block_versions` 키, 신규 `core/graft.py`), 평가 커널 ②~⑤·봉인 블록의 분할 선언(`E/sizing/block_*.py`, `seal_*.py`), S3 메모리 색인과 보존(신규 `E/search/s3_index.py`, `local`·`solved` 분리, 보존 소유자 5종, `archive.py` 타입 있는 직렬화), 계수 소유 이동(`ComputeBlock` 무상태화, 신규 `core/run_counters.py`, `BoundedLRU._evicted`·`TableCache.events` 이동), 층 0 필드(`graph/layer0: macro`·`comp_approx_gap`·`rounds`, `graph/local` 블록 범위 metric), 제약 행 `graph/metrics: constraint_rows`(①-c에서 이월, `unmeasured` 자리는 §2.4.12 Q8), 결과 JSON 계수 `perf.s0_snapshot`(①에서는 단계 A 보고서 `s0_snapshot` 키), `SearchContext`(G-7), `kernel.evaluate`, `EvalResult`·`SsEvaluation` 사본 제거, 층 0의 이식 사용(`layer0_budget.py`, `local_candidates.py`, `local_front.py`, `combo_dp.py`, `assembly.py`, `size_and_seal_local.py`의 `LocalSeal`) | **전체 재작성**: search 상태층(`search_context.py`, `kernel.py`의 캐시·기록 부분, `EvalResult`), 층 0 데이터 흐름(41 §5 v1.6 U15 재구현과 한 변경). **부분 수정**: core 블록(분할 추가, 분할 없는 블록은 `*` 하나로 as-built와 같은 동작), 커널 블록 분할 선언 | `sctx.cache`·`disk_failures`·`computed_keys`·`cell_floors`·`local_seal_memo`, `_disk_failures`, `ComputeBlock`의 계수 칸·`_seen_inputs`·`reset_stats`, `SsEvaluation.ss/dc`, `EvalResult`의 값 칸, `LocalSeal.snapshot_fragment`·`power_w`·`area_m2`, 오케스트레이터 초안 EvalCache, 이것들을 단언하던 test | ①, U15 design(41 §5 v1.6) 승인 | D-GR1·4·5·9·10·14 | `test_g10_second_run_s0_zero`(`RunCounters` 필요, §2.4.9에서 ①에서 옮김), `test_graft_equals_compute`, `test_graft_donor_order_invariant`, `test_partition_scc_not_split`, 분할 블록 시드 금지(같은 θ·다른 parent → 같은 분할 값), 보존 규칙(풀이 중 기준점 유지·끝나면 놓음), 색인 적중 = 커널 0, 층 0 조립점에서 비공유 분할 `computes` 0. **완료 조건 = A' 판정 기준**(§10.5, P DEC-98: library 9회로 + held-out 회로에서 시작점이 봉인 통과·spec 제약 행 c ≥ 0이고 ngspice 통과, 실패 회로는 A' 대조표, 9회로 도달률은 회귀 지표) |
| **③ LUT memo·lint·G-10** | `E/lut/lut_memo.py`(`call`·계수 상태·상한 B_r), `sweep_memo.py`, LUT 순수 함수로 옮기는 것(`E/search/cell_floor.py`, `E/metrics/block_param_tables.py`, `edge_costs` 호출처, `E/sizing/block_columns.py`의 `solve_self`·`tol_cells`), 구조 규칙 G 확장·설계 값 타입 위치 검사·SC-a/SC-b lint(`E/tests/structure/structure_checks.py`, `_module_map.py` 필드 형식 열), memo 상한·퇴출 판정(§2.4.6 사용자 결정 (가)/(나)에 따라 -- 결정이 착수 조건), G-10 test(`E/tests/perf/`, `E/tests/integration/`) | **전체 재작성**: memo 생성·상한 배선(`_wire_sweep_memo`, `sweep_memo`), `ParamTables`. **부분 수정**: `cell_floor`·`solve_self`·`tol_cells`(memo 함수로 옮김), 구조 검사(규칙 추가) | `LutMemo.lookup`(클로저형), `_Unmemoized`, `_CountingMemo`·`sweep_memo.py`, 두 번째 memo 인스턴스, `ParamTables` 클래스와 두 벌 생성, `CurveBook`의 LUT 사전(①에서 클래스 삭제), §2.4.10 실측 위반 줄 전부, 이것들을 단언하던 test | ②, §2.4.6 사용자 결정 | D-GR6·11·12·15 | `test_lut_memo_single_instance`, `test_lut_memo_purity`, `test_g10_no_recompute_9circuits`, 구조 규칙 G 확장의 거부 확인 픽스처(규칙마다 위반 예 1개가 실제로 거부됨) |

**U17과 다른 단위의 관계**:
- U15(층 0)는 ②와 한 변경이다. 41 §5.3.9의 `local_seal_memo` 문구는 41 개정이 §2.4.5를 인용해 바꾼다.
- U16(오라클 입력)은 수동소자 값을 `device.passive_value` 필드에서 읽는다(①).
- U2(대칭)의 궤도 결과는 S0 수준 필드다(§2.4.8). 별도 브랜치 초안 f786dc6은 병합하지 않는다.

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
| 4' | U17 ①(U15 재구현 전), U17 ②(U15 재구현과 한 변경), U17 ③ | v1.6 graph 정본 개정. U15 재구현을 U17 ② 안에서 한다(G-9) |
| 5 | U16, 그 뒤 gap 분석(`42` 기준표 재측정) | J 공동분석은 J-A~J-F만 2026-10-08에 결정됐고(§9.3) 그 구현이 U1b다. 남은 J(§9.4)는 ratify 전이라 엔진 유도로 돌고, `review_needed`가 남는 회로는 GB4 전에 정지한다 |

**임계 경로**: U1 → U1b → U9 → U13 → U15 → U16. U9가 주경로 블록 정의를 읽으므로 U1b가 임계 경로에 들어간다. U1(SP1)이 가장 크므로, 하위 파일 단위로 나눠 같은 웨이브 안에서 순차로 커밋한다.
