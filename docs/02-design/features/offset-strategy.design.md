---
template: design
version: 0.3.3
plan: ../../01-plan/features/offset-strategy.plan.md
plan_version: 0.7.3
---

# offset-strategy Design Document (card OS-0)

> **Summary**: 승인된 계획 `offset-strategy.plan.md` v0.7.2(사용자 결정 S-1~S-14, T-34~T-37, O-1, O-53 A2·B3, O-61 P1·P9, O-62, O-63 (3)·O-65, O-62 (3)·O-63 (1)·(2)·O-64 (2)·O-68 (3)·O-70)을 엔진 `gmid_engine` 설계로 옮긴다. 계획 N10.3의 G-S1~G-S6을 닫고, 요구 스키마(판정 온도 범위 칸 포함)·로더 사유 코드, 실행 계획 `RunPlan`·`build_run_plan`, 실행 계획 세션과 그것을 쓰는 얇은 진입 `run_plan`(엔진 사슬 진입점 정본, W-1), 변형 유도 제약의 별도 입력 `derived`(PD-1), 결과 JSON 칸, 하네스 노출 목록, 비교 도구, 예산 식, OS-V(matching 오라클 측정)·OS-L(실행 중 변형 추가)의 형식, 파일 분할, 배선표, test 목록, card별 완료 조건을 정한다. offset-trim design(OT)과 40 design의 개정안, trim 시험 회로 spec 재작성안, OS-2 검증 fixture를 함께 낸다.
>
> **Project**: chip-design-skills (analog-gmid-design skill) · **Author**: Claude Code (design 작성자 역할)
> **Status**: design v0.3.3 초안 (2026-10-21). 계획 v0.7.3(사용자 O-70 (2), 병합 `2dab561b`)과 gain-budget v6.24(병합 `59ecc88e` -- DEC-74·N3.3 (b) front 판정 기록 종류 = 출력 기록, O-68 (3))에 맞췄다: 커널 행 ① A_dc 갈래 fail-closed, front ② 갈래 먼저·미수렴(O-64 (2)), 완료 조건 10 정의 불능·미수렴 toy, OS-2 착수 조건 보강(PS-1 이름·PS-7·open_run 점검), 실현성 점검표 §18.6(사용자 규칙 2026-10-21). 검증 반영(줄 인용 복구, PS-8 재분류, `variant_key` 명시 인자). 남은 멈춤은 §18.4. 독립 검증 재확인·사용자 승인 전이다. 이전 판들의 Status 문단은 [history](offset-strategy.design.history.md) H7에 있다.
> **기준**: 코드 인용은 master `e1a611ec`(XRUN-F1 card B 병합 뒤 -- `E/search/open_run.py`·`E/search/s3_index.py` 있음, `run_stage_a` 서명 `E/pipeline/stage_a.py:206`; card C의 `search_ceiling.py`·`search_stop.py`는 아직 없음)의 `파일:줄`이다. v0.2.x 사실표 가운데 이 기준에서 바뀐 행은 §2에서 고쳤다. `E/` = `skills/analog-gmid-design/gmid_engine/`, `O/` = `skills/analog-gmid-design/tools/spice_oracle/`. design 인용은 `OT §x`(`offset-trim.design.md` v0.2, T-18), `40 §x`, `41 §x`. 다른 계획 인용은 `OTP Nx`(offset-trim 계획 v0.5.5, 브랜치 `trim-plan-r1` `e8b58cd`, 사용자 승인 T-34~T-37), `OPP Nx`(oracle-portability 계획 v0.4.2, master `d579939`, 사용자 승인 O-1).
> **전제**: 구현은 XRUN-F1 card C 병합 뒤이고(S-4), OS-2는 U17 ② 병합 + Q8 결정 + DE-1 (c) + PS-1 이름 + PS-7 열거 API 뒤 착수다(계획 v0.7.3 N7.1·N7.2 OS-2 행). 이 기준에는 card C와 U17 ②가 없다(평가 키 부분 `S3Index.get` 등 없음, as-built `sctx.cache`). 그래서 이 문서는 40 §2.4.4~§2.4.14의 병합 뒤 구조를 전제로 쓴다.

---

## 0. 문서 안내

* **담는 것**: 규칙, 정의, 값 형식, 함수 서명, 사유 코드, 결과 JSON 칸, 노출 목록, 파일 분할, 배선표, test 목록, card별 완료 조건, 다른 문서 개정안.
* **담지 않는 것**: 경위, 검토 과정, 대안 비교의 세부, 버전 이력(history), 수치 상수. 값은 spec 선언, 단위 어휘(`E/core/units.py`), 엔진 해석값, LUT, PDK 선언에서만 온다. 예외는 사용자가 결정한 fixture 값이고 출처와 함께 적는다(계획 N0).
* **이름 원칙**: 규칙에 회로·소자·넷 이름을 쓰지 않는다. 회로 이름은 사실 표와 fixture·측정 대상에만 나온다.
* **용어**: 계획 N0.1 그대로. 이 문서가 더하는 용어는 아래다.

| 용어 | 정의 |
|---|---|
| 유도 제약 | 요구에서 엔진이 만든 판정 제약. spec `constraints`와 따로 두는 별도 입력 `derived`(PD-1). 값 형식 `OffsetBound`(§3.4) |
| 합성 행 | matching 유도 제약의 **커널** 제약 행 `req:offset_matching<=`(§3.1). v0.3.0부터 항은 σ_in 하나다(k·σ_in ≤ 문턱, O-53 A2). 이름은 v0.2 관례를 유지한다 |
| front 판정 | matching 합성 판정 k·σ_in + \|V_id*\| ≤ 문턱을 front 점에서 판정하는 것. 자리 = gain-budget DEC-74 front 전용 예외 자리 하나(§3.7). 새 자리를 만들지 않는다 |
| 실행 계획 세션 | 실행 하나(= 실행 계획 하나)의 수명 객체 `PlanSession`. 열기·변형 실행·변형 추가·닫기(계획 N3.12) |
| 토폴로지 변형 | 변형의 topology. 원본 `TopologyDoc`이나 승인된 파생 topology(OT §7) |
| B_S0 | 색인 상한 식의 S0 계산 벌 수 = 변형 수(+ 국면 2 원본 비교 벌, 계획 N3.7 PD-7) |
| 구동기 | 엔진 밖에서 세션을 쥐고 오라클(별도 프로세스)을 부르며 변형을 추가하는 코드(OTP G-12, 위치·서명은 offset-trim design) |

---

## 1. 입력·원칙

### 1.1 확정 결정(인용)

원문은 `wt/_drafts/user_decisions.md`의 해당 절이다.

| ID | 내용(요지) | 이 문서 반영 |
|---|---|---|
| S-1~S-4 | 요구 스키마, 방식별 유도, 파이프라인 층 재작성, compare 두 국면, 순서 | §3~§11 |
| S-5·S-6 | XS-1~XS-14 승인, DS-U1~DS-U9 결정 | §4, §7, §10 |
| S-7 | "계획과 다른 부분이 생기면 계획부터 수정" | §18.2(계획과 다른 결정 없음) |
| S-8 | PD-1 `derived` 별도 입력, PD-2 TR card 배정·OD-3 수용, PD-3 DS-2 '대상 없음', PD-4 XS-10 범위 서술, PD-5 요구 섹션은 있을 때만 지문, PD-6 공통 판정 검사 OS-5, PD-7 B_S0 = 변형 수·card C `S3Index` 인터페이스, PD-8 `run_stage_a` 필수 키워드·40 '전달' 행 개정 | §3.6, §4, §5.3, §6, §7.3, §11, §17 |
| S-9 | W-1 (i) `run_plan` = 사슬 진입점 정본, 하네스·test 수작업 사슬 대체, U16은 나중에 CLI를 `run_plan`에. F-1 fixture. T-30 연결 | §6, §14, §16 |
| S-10 | PD-9 (가) 공존 거부 = 판정 제약만 | §4.2 L2 |
| S-11 | V-1 = OS-V card, F-1 위치 = 저장소 안·library 밖 | §12, §14 |
| S-12·T-37 | XS-16(실행 중 목록 증가)·XS-17(공개 진입 `run_plan` + 세션, 사슬 하나)·XS-18(= OTP X-23, Δ_T 입력은 S-3 취지 안)·XS-19(메모리 동시 점유, 반복마다 메모리 보고, OS-L 병합 전 반복당 색인 크기 측정) 허용 | §6, §13 |
| T-29~T-33 | offset·trim 잔여 합격 = SPICE 오라클 온도 범위 판정(T-29), SPICE 온도 보정 루프는 offset-trim 계획 소유·순서 TR-7 뒤(T-30), 공정 무관 방법론(T-31), 처음 범위 = offset·trim 잔여(T-32), 오라클 시뮬레이터 무관(T-33) | §8 합격 표기, §12, §13 |
| T-34 | 판정 온도 범위 = T-14 범위, spec 한 곳 선언, 모든 소비자가 참조(숫자 사본 금지), 위치 = 요구 안 칸 | §4.1 |
| T-35 | OTP D-24 안 B: 반복 = 같은 실행 안 변형, D-19 반복 상한 = 실행 설정(기본값 없음) | §13 |
| T-36 | OTP D-20 (가), D-25 (c)+(c-2): 출처 무결성, 대조 주체 = 엔진 밖 구동기, 엔진에는 통과한 값만 | §13(인터페이스 서명을 닫는다) |
| O-1 | oracle-portability: 오라클 MC = 시뮬레이터·PDK 네이티브 MC, 크기 확인 = TR-7 엔진 σ 대 오라클 MC σ | §12 |
| O-53 A2 (XS-20) | matching 판정 위치 둘: 커널 k·σ_in ≤ `offset_in_max_v`, front k·σ_in + \|V_id*\| ≤ `offset_in_max_v`(ΔW 1차, 단위 9 뒤 실현 W 재판정, 위반 점 front 제외·비지배 재필터). 원래 취지와 다름 승인 | §3.1, §3.7, §12 |
| O-53 B3 · O-50 G1 | 계통 offset 정본 = 부호 있는 V_id* 한 칸(gain-budget DEC-23), 출력 기준 정의 자리 = DEC-23 하나 | 기호 \|V_id*\| 전부, §8 `output_reference`, §12 |
| O-34 (1) | 변경 종류별 판정 기준(결정성·순수 리팩터링 필드별·동작 변경 네 다리), 정본 gain-budget N6.3(인용만) | §3.6, §16.1 OS-2·OS-V, §16.3 완료 조건 10 test |
| O-61 P1 | 스냅샷 파생 때 남는 필드 = `ctx.base`에 있는 writer ∪ 그 평가가 부르는 블록(정본 gain-budget v6.22 N3.3 '스냅샷 파생 규칙', 422행) | §3.1 '스냅샷 파생 규칙 영향' |
| O-61 P9 · O-62 | OS-2 착수 조건 = U17 ② 병합(`constraint_rows` 필드·writer) + 40 §2.4.12 Q8 결정. 과도기 `EvalResult` 값 칸·결과 JSON 재계산 금지. 계획 v0.7 기준 개정(design v0.3.x) | §3.1 '행 값', §16.1 |
| 원래 취지 | "계산 재사용은 처음 topology를 실행할 때는 항상 계산하고 그 계산된 값이 나머지 최적화를 진행할 때 재사용되게 한다는 것이 원래 취지였어" | §3.2, §5.3, §6.3, §13 |

**이어받는 결정**: U-89, X-7, X-12, X-17, T-2·T-7·T-8, T-15, T-19~T-23, T-24~T-28(계획 N2 표 그대로).

### 1.2 원칙과 강제 장치

| 원칙 | 강제 장치 |
|---|---|
| graph 단일 정본(NFR-S2, 프로젝트 CLAUDE.md '★graph 단일 정본' 규칙 1~7) | 계산값은 graph 필드로만(필드마다 writer 하나), 재사용은 graph reuse와 실행 수명 S3 블록 결과 색인 graft 둘뿐, 새 cache·memo·dict·`sctx.*` 슬롯·`EvalResult` 값 칸·값 사본·둘째 생산자 금지, 단계 사이 전달은 참조로. 이 문서의 점검표는 §18.5. 요구 값은 spec 섹션 한 곳. 유도 제약은 해석된 값 + 참조 경로(기존 `ConstraintDecl.value`·`ref` 형식, `E/authoring/spec_model.py:125-138`). 판정 온도 범위도 요구 안 한 곳(T-34). Δ_T는 변형 추가 입력 하나로만 들어온다(§13) |
| 재사용(NFR-S1, 원래 취지) | 유도 제약은 spec 밖 입력이다(§5.3). S1v·`achievability`·`constraint_classes`·`search_domain`의 입력은 같은 topology 변형 사이에 같다. `start_intervals`는 문턱 항목을 읽으므로 문턱 값이 다른 OS-L 반복 사이와 compare 국면 1(matching 대 trim 국면 1)에서 다르다(§3.2·§6.3, 계획 N3.12 '재사용 범위' ①) |
| topology 무관(NFR-S3) | 뷰는 포트 역할에서, 기준 DC는 `DcInputs`에서, 단위는 레지스트리 단위 칸에서 읽는다 |
| fail-closed(NFR-S4) | §4.2·§13.3 사유 코드 전부 탐색 전 정지(변형 추가 거부는 추가 전) |
| 결정성(NFR-S5) | 계획 함수는 순수 함수, 처음 변형 순서 고정, 추가 변형은 추가 순서(§5.2·§13) |
| 상수 발명 금지(NFR-S6) | 합성 행 문턱·분해능·단위 환산은 정의와 단위 어휘에서(§3.1). 비교 도구에 가중치·문턱 없음 |
| 만들면 배선(NFR-S7) | §15 배선표. OS-L은 TR-TL과 같은 변경(계획 N7.2) |
| 작성자 ≠ 검증자(NFR-S8) | test 기대값은 interface card만 보고 쓴다. 완료 조건 1의 F2·F3 제외 목록은 검증자 소유 |

---

## 2. 엔진 실측 사실(`194981f`)

v0.3.1 기준 `e1a611ec`(card B 병합 뒤)에서 다시 잰 행은 E-S9·E-S12·E-S14·E-S15·E-S18·E-S21이다. 나머지 줄 번호는 v0.2 기준(`194981f`) 그대로이고 착수 때 재측정한다(card 처리 규칙 '사실 문장은 쓰는 자리에서 재측정').

| ID | 사실 | 근거 |
|---|---|---|
| E-S1 | offset metric 셋의 레지스트리 단위는 `mv`, view_kind는 `transfer`. 레지스트리 metric은 계산된 값 묶음의 필드 하나다 | `E/metrics/registry.py:5-6, :56-58` |
| E-S2 | view를 적지 않은 transfer metric 제약은 로더가 기본 포트 뷰를 받는다. 정해지지 않으면 `view_required` | `E/authoring/spec_constraints.py:198-204`, `E/authoring/spec_views.py:69-84, :171-184` |
| E-S3 | library offset 제약은 view를 적지 않는다 | `assets/library/current_reuse_telescopic_ota.sizing_spec.json:226-243` |
| E-S4 | σ_in·`offset_sys_mv`(V_id*) 계산은 요청 `ViewDecl`로 `view_system`을 직접 쓴다(S1v 씨앗 불필요) | `E/metrics/offset_analysis.py:56-57`, `E/metrics/offset_systematic.py:31-33` |
| E-S5 | `offset_sys_mv` = \|오차\|/\|A_dm\|(mv). 단일 출력 기준 = `targets`의 출력 넷 값, 없으면 `reference_undeclared` | `E/metrics/offset_systematic.py:42-47, :55` |
| E-S6 | `dc_inputs_from_spec`은 결정 대기 노드 목표를 '미선언'으로 투영하고, `metrics_aux`의 `targets`가 그 `node_targets`다 | `E/sizing/dc_inputs.py:11-12, :24-41`, `E/metrics/ss_evaluate.py:103` |
| E-S7 | `build_s1v`는 spec 전체가 아니라 `judged_constraints` tuple을 extras로 받는다 | `E/graph/s1v_build.py:39-42` |
| E-S8 | `ss_evaluate` 요청 목록은 항목의 `.metric`·`.view`만 읽는다(`MetricRequest`와 같은 두 칸) | `E/metrics/ss_evaluate.py:50-57`, `E/metrics/ss_types.py:57-61` |
| E-S9 | 커널 행 = `seal_rows + _spec_rows + ss_rows + ls_rows` | `E/search/kernel.py:136, :155, :158` |
| E-S10 | matching L 하한 = `offset_in_sigma_mv <=` 최솟값 × `MILLI` / √2 | `E/search/iv_context.py:89`, `E/search/iv_matching_l.py:107, :123` |
| E-S11 | mv → V 정본 = `core.MILLI` | `E/core/units.py:13, :22`, 함수 레지스트리 §15 |
| E-S12 | 값 있는 판정 제약 가운데 `_OFFSET_METRICS` = (`offset_in_sigma_mv`, `offset_excess`) 둘이 있을 때만 LUT mismatch 데이터를 필수로 확인한다. `offset_sys_mv`는 대상이 아니다(mismatch 데이터를 쓰지 않는다) | `E/search/search_context.py:143, :155` |
| E-S13 | 제품 사슬 진입점이 없다. 사슬은 test 하네스가 만든다 | `E/pipeline/__init__.py:1-4` |
| E-S14 | (card B 뒤) `run_stage_a(topology_path, spec_path, lut, *, output_dir, donors, counters, supplies_v=None, structure_path=None)` -- `donors`·`counters` 필수 키워드(PD-8 (ii)가 card B에서 이미 반영됨). 결과 `StageAResult`에 `donors`·`counters` 참조 칸(과도기 칸, X-13) | `E/pipeline/stage_a.py:87-90, :206` |
| E-S15 | `find_front`의 검증 출처 notes와 `run_id` 지문 | `E/search/find_front.py:83-85, :131` |
| E-S21 | (card B) 실행 경계 객체 생성 = `open_run() -> (donors, counters)` 하나. `S3Index()` 생성자 인자 없음(card C·OS-5가 필수 인자를 더함), 지금 메서드 `find`·`register`·`find_failure`·`register_failure`·`entry_count`(평가 키 부분 `get` 등은 U17 ②). 구조 규칙 M(M-a~M-f) | `E/search/open_run.py:15-17`, `E/search/s3_index.py:17-52`, 40 §2.4.5 '수명' (1)·(2) |
| E-S16 | 참조 제약의 `judged`는 참조 해석(`resolve_spec_references`)에서 정해진다. 로더는 그 뒤 최종 거부를 한다 | `E/authoring/spec_constraints.py:263-265`, `E/authoring/spec_load.py:142-145` |
| E-S17 | 검증 출처 표: `offset_in_sigma_mv` = `spice_oracle`(measure `offset_in_sigma_mv`), `offset_sys_mv` = `spice_unverifiable`. 레지스트리 metric마다 표 행이 있어야 한다(없으면 `KeyError`) | `E/metrics/verified_by.py:12, :44-45` |
| E-S18 | **하네스 사슬과 읽는 값**(전수, B-1): `nfr4_run_dump.py`(`e1a611ec`)는 (1) `find_front` 모듈 속성 `layer0_start`·`sweep_front`를 감싸 관찰(:315-329) (2) `donors, counters = open_run()`(:378, 규칙 M M-c) → `run_stage_a(...)`(:379) 뒤 `a.code_fp`·`a.report_paths[0]`·`a.status`·`a.s1.snapshot.fp`(:381-386) (3) `LutMemo` 크기 인자를 정해 만들고(:389) `run_stage_b(a, memo, pdk, output_dir, diagnostic=True, settings)`(:390) 뒤 `b.report_paths[0]`·`b.s1.snapshot.fp`·`b.status`(:391-394) (4) 둘 다 `ok`일 때만 커널 컨텍스트 → `build_search_context(kctx, a.spec, settings, s3 루트, pdk, rule, code_fp=a.code_fp)`(:403) → `sctx.domain.w_min_m`·`sctx.dc.base`(:404-405) → `find_front(sctx, [])`(:407) → `fr.perf`·`fr` 전체(:408-411) → `sctx.cache.values()`의 `seq`·`evaluation.snapshot`(:417-418; as-built 칸 -- U17 ②(40 §2.4.7 G-7)·GC-7에서 지울 대상이다. 정본 읽기 경로는 S3 메모리 색인 `S3Index`의 평가 키 부분, §6.4) → `sctx.context_fp`로 S3 폴더의 evals·runs 줄 (5) 탐색하지 않았으면 S0 스냅샷 = `b.s1` 또는 `a.s1`의 스냅샷(:444) | `E/tests/integration/nfr4_run_dump.py:315-444` |
| E-S19 | **수작업 사슬을 가진 test**(2026-10-16 grep `run_stage_a`·`run_stage_b`·`build_kernel_context`·`build_search_context`·`find_front(` 호출 수): 전체 사슬(A → B → 커널 → 탐색 → `find_front`) = `tests/integration/nfr4_run_dump.py`, `test_no_s0_files_written.py`, `test_rerun_s3_independence.py`. 탐색 컨텍스트까지의 부분 사슬(뒤에 층 0 등 내부 함수를 직접 부름) = `test_layer0_boundary_rows.py`, `test_s0_layer_9circuits.py`, `search/u13_hand.py`, `search/u13_real.py`. 단계 B 없는 사슬 = `search/test_cell_floor.py`, `core/test_blas_env.py`(진입점 재확인 test) | grep 결과 |
| E-S20 | 오라클 measure 이름은 `O/oracle_compare.py` MEASURES의 키다(엔진은 이름만 든다). 오라클 재구성 뒤 측정 정의는 오라클 코어 `O/core/`에 있다(OPP N0.1·N3.1) | `E/metrics/verified_by.py:36-38`, OPP N0.1 |

---

## 3. G-S1~G-S6

### 3.1 G-S1 matching 판정 ① 커널 행(계획 v0.7 N3.3 ①, O-53 A2)

matching 판정 식 k·σ_in + \|V_id*\| ≤ `offset_in_max_v`(S-1)는 **두 자리**에서 판정한다(O-53 A2, XS-20): ① 평가 커널의 제약 행 k·σ_in ≤ 문턱(이 절), ② front 판정 k·σ_in + \|V_id*\| ≤ 문턱(§3.7, gain-budget DEC-74 front 전용 예외 자리의 소비자). 계통 offset V_id*는 θ 프레임 봉인점에서 구조적으로 0이라 커널에서 잴 수 없다(DEC-74). 그래서 커널 행에 V_id* 항은 없다. 한계를 σ 몫과 V_id* 몫으로 나누는 비율은 만들지 않는다(NFR-S6, 계획 N3.10 G-S1).

**형식(오케스트레이터 기본안 OB-1, 계획 XS-10·PD-4 범위, 계획 G-S1 ① (ii))**: 새 metric을 만들지 않는다. `ss_constraint_rows`에 인자 `bounds`를 더해 `offset_in_sigma_mv`를 k배로 읽는 커널 행을 만든다. 근거: (1) metric은 계산된 묶음의 필드라 k(spec 값)를 넣으면 metric 블록 입력이 판정 값에 의존한다(E-S1). (2) 커널 행은 이미 계산되는 σ_in 결과 하나만 읽는다(새 블록·재계산 없음). (3) 레지스트리·`verified_by` 이름 공간을 바꾸지 않는다.

| 항목 | 규칙 |
|---|---|
| 요청 | `MetricRequest(b.sigma_metric, b.view)` **하나**. 커널이 `sctx.ss_constraints`와 함께 `ss_evaluate`에 넘긴다(E-S8). `b.sys_metric`(V_id*)은 커널에서 요청하지 않는다(커널에서 구조적 0, DEC-74) |
| 값 | v = k·σ_in(V). σ_in = `sigma_in_mv`·u. **항은 하나다** |
| 문턱 | L = b.threshold.value_v(§3.4 문턱 항목). 처음 변형은 요구 `offset_in_max_v`의 해석된 값, OS-L 추가 변형은 구동기가 OT §20.3 `tightened_threshold`를 한 번 불러 만든 조인 문턱 항목의 값이다. 커널 행과 front 판정(§3.7)은 **같은 문턱 항목 하나**를 읽는다(계획 N3.3 '두 판정의 문턱은 같은 문턱 항목 하나'). **커널·`ss_constraint_rows`는 문턱을 합성하지 않고 항목 값을 읽기만 한다**(평가마다 합성하지 않음 = 같은 입력 재계산 0, 계획 N3.12 ③) |
| 분해능 | s = k·s_σ, s_σ = max(σ_in 결과 `resolution`, `offset_in_sigma_mv` 모델 오차 선언)·u. 기존 ss 행 규칙(`E/search/ss_constraints.py:15-18, :82`)을 그대로 쓰고 k배만 한다. **규칙은 하나다**(항이 하나라 항별 합산·항별 판정이 없다) |
| 행 | 이름 `req:offset_matching<=`, c = (L − v)/s, `active` = c ≤ 1 |
| 봉인 안 된 점 | 미측정 (`offset_matching`, `<=`, `ss_requires_sealed_snapshot`) |
| 정의 불가 | (v0.3.3, 계획 v0.7.3 N3.3 ①) **σ_in이 gain-budget DEC-23 'A_dc 정의 불능 갈래'로 정의 불능이면 커널 행도 fail-closed로 그 점을 거른다**. 원인 = 갈래 사유 기록의 **참조**(offset 위반 아님, 사유 사본 없음). 기록 자리 종류 = 출력 기록(gb v6.24 DEC-74·N3.3 (b), O-68 (3)), 이름 = card DE-1 design·착수 실측(PS-1). **실현 경로(지금 코드에 있음, v0.3.3 검증 반영 -- 옛 PS-8 재분류)**: σ_in 값이 None이면 `ss_constraint_rows`는 행을 만들지 않고 `Undefined` 코드를 `unmeasured`에 넣는다(`E/search/ss_constraints.py:72-78` -- 위반 행이 아님) → `EvalResult.unmeasured`로 기록(`E/search/kernel.py:81`) → 그 점은 `unmeasured_front` 상태로만 남고 최종 front에서 빠진다(`E/search/eps_sweep.py:37, :44`, search CONTRACT 107-111행). 그래서 커널 행 ①의 fail-closed 거름은 새 장치 없이 성립한다. **원인 = 사유 코드 문자열**이 계획의 '갈래 사유 기록의 참조'다(사유 사본이 아니라 코드 이름 하나; 미측정 자리가 Q8로 바뀌면 그 자리를 따른다). 남는 의존은 둘이고 이미 착수 조건이다: (i) 갈래 `Undefined` 코드 이름(DE-1 (c) 몫 -- PS-1·DE-1 선행) (ii) 미측정 행의 자리(U17 ②·40 §2.4.12 Q8). 갈래가 아닌 다른 `Undefined` 코드(`E/metrics/mna_types.py:41`)도 같은 경로다. **두 자리 일관(V10)**: DE-1 (c) 뒤에는 커널 행 ①과 front 판정 ②가 같은 정본 A_dc와 같은 갈래 사유 필드를 읽는다(gain-budget I-H2가 두 A_dc 생산자를 하나로 합침) -- 한 점이 한쪽에서만 정의 불능일 수 없다 |
| 분해능 없음 | 기존 ss 행 규칙 그대로(`E/search/ss_constraints.py:79-85`): σ_in 결과 `resolution`이 None이면 행 없이 미측정 `resolution_undefined`, s_σ = 0(resolution 0이고 모델 오차 선언 없음)이면 행 없이 미측정 `resolution_zero_model_error_undeclared`(fail-closed) |
| 일찍 끝나는 분기 | 지금 `ss_constraint_rows`는 `if not declared: return (), ()`로 끝난다(`E/search/ss_constraints.py:63-64`). 요구는 있고 사용자 ss 제약이 없는 spec에서 합성 행이 빠지므로 이 분기를 `if not declared and not bounds`로 바꾼다. 봉인 안 된 점 분기(:65-66)는 bounds의 미측정 줄도 함께 낸다 |
| 행 값(graph 필드, v0.2.6 F3) | (v, L)은 결과 객체 칸이 아니라 합성 행을 쓰는 블록의 graph 필드 값이다. 필드 = `graph/metrics: constraint_rows`(40 §2.4.8 소유표 '제약 행' 행, S2), writer = search 제약 블록 하나(`ss_constraint_rows`를 부르는 블록). **입력 버전(검증 M2)**: 그 writer의 입력 버전(40 §2.4.4 식 `fp_of((name, 코드 해시, 투영 지문))`)의 투영에 그 변형 matching `OffsetBound`의 투영(k, 문턱 항목 `value_v`, `sigma_metric`, `view`)을 넣는다. 이것은 블록 입력 버전이고, 평가 키의 `constraint_set_fp`(§3.3, DS-1 (다), OS-5)와는 따로다 -- 둘이 같은 투영을 쓰는 것은 각자의 키 정의이고 값 사본이 아니다. 투영에 빠지면 문턱이 다른 변형이 같은 입력 버전으로 색인 적중해 옛 행을 graft하게 된다(fail-closed 위반). 행 형식에 (v, L)을 더하는 일(U17 ② 행 형식 넓힘)은 §17.2 40 개정안 알림이다(검증 M3). 근거: 40 §2.4 '필드마다 writer 1개', §2.4.7 값 사본 제거(`EvalResult`의 값 칸은 지울 대상이다 -- 40 지울 것 목록, 42 D-GR9), DEC-83(제약 값은 graph 필드). 합성 행 값 = (name, c, active, v, L). L은 문턱 항목 `value_v`를 읽은 값이다. 그 값은 (가) 이 writer의 **블록 입력 버전** 투영(위 '입력 버전')에 들어가고, (나) 따로 OS-5의 **평가 키** 칸 `constraint_set_fp`(§3.3·§10)에 들어간다 -- 두 키는 정의가 다르고 어느 쪽도 값 사본이 아니다(v0.3.3 문장 정정: 옛 '입력 버전(`constraint_set_fp`)'은 두 키를 섞었다). 결과 JSON(§8 `front_points[].derived_rows`)은 그 점 평가 스냅샷의 이 필드를 읽는다(다시 계산하지 않는다, OB-13). **선행(닫힘, 계획 v0.7.1 N7.1 'OS-2 착수 조건', O-61 P9·O-62)**: 이 필드는 U17 단계 ②로 이월됐고 40 §2.4.12 Q8(미측정 값 자리)이 정해지기 전에는 쓰지 않는다. 그래서 **OS-2 착수 조건 = U17 ② 병합(`constraint_rows` 필드와 writer) + Q8 결정(사용자)**이다. 그 전의 과도기 자리는 두지 않는다: `EvalResult` 값 칸은 사본이고 지울 대상에 새 소비자를 다는 것이라 금지, 결과 JSON을 쓸 때 (v, L)을 다시 계산하는 길도 둘째 생산자라 금지(프로젝트 CLAUDE.md 'graph 단일 정본' 규칙 1·2). U17 ②가 길어질 때 OS-2가 `constraint_rows` 필드와 writer만 당겨 만드는 안(Q8 결정은 여전히 필요)으로 바꿀지는 그때 사용자가 정한다(계획 그대로, 이 design은 정하지 않는다). 미측정 줄(위 '봉인 안 된 점'·'정의 불가'·'분해능 없음')의 자리도 같은 Q8을 따른다 |

* **단위(OB-2)**: 항 단위는 레지스트리 서명 단위 칸에서 읽고, `mv`이면 u = `core.MILLI`(E-S11). 그 밖 단위는 유도 제약을 만들 때 L5로 거부한다. 숫자 1000·0.001을 새로 쓰지 않는다.
* **view 출처(OB-3)**: 기본 포트 뷰. 사용자 offset 제약이 view를 적지 않을 때와 같은 규칙이다(E-S2·E-S3). 로더가 `default_views(topology, feedback).port`로 정해 `OffsetRequirement.view`에 담고, 정해지지 않으면 L3. 요구 섹션에 view 키는 없다.
* **S1v(OB-4, PD-3 근거)**: 유도 제약은 S1v 씨앗·`build_s1v` extras 밖이다(E-S4·E-S7). 그래서 같은 topology 변형끼리 S1v 입력이 같다. DS-2는 '대상 없음'으로 닫혔다(PD-3, S-8). 유도 제약이 뷰 씨앗을 요구하게 되면 DS-2를 다시 연다.
* **이름**: 행 접두 `req:`, 몸통 `offset_matching`은 방식 이름이다(새 이름 충돌 0, v0.1 E-S17).
* **스냅샷 파생 규칙 영향**: parent → child 파생 때 남는 필드 = **`ctx.base`에 있는 writer ∪ 그 평가가 부르는 블록**이다(사용자 결정 O-61 P1, 정본 gain-budget v6.22 N3.3 '스냅샷 파생 규칙' 422행 -- 이 design은 인용만 하고 규칙을 다시 적지 않는다). (1) σ_in 항(`metrics_ss` 필드)과 `constraint_rows`(search 제약 블록)는 모든 커널 평가가 부르는 블록이 쓰므로 남는다 -- 영향 없음. (2) `RunPlan`·`derived`·문턱 항목·`OffsetBound`는 graph 필드가 아니라 실행 입력이다(§5) -- 규칙 대상 아님. (3) 영향이 있는 것은 평가 커널 밖에서 쓰는 값, 곧 front 판정(§3.7)이 읽는 V_id*와 그 판정 기록이다. 그 writer는 커널 평가가 부르는 블록도 `ctx.base`의 writer도 아니라서 child 파생 때 지워진다. 그래서 front 판정 값은 **front 점 자신의 스냅샷에서 읽고** child 스냅샷에서 읽지 않는다(§3.7, 계획 N7.1 개정 항목 3).
* **기호(계획 N7.1 개정 항목 4)**: 계통 offset은 gain-budget DEC-23의 부호 있는 V_id* 한 칸이고(O-50 G1), 판정은 크기 \|V_id*\|로 한다. 이 문서의 옛 기호 V_sys는 모두 V_id*로 바꿨다. 엔진 이름 `offset_sys_mv`는 레지스트리 metric 이름이고 그 정본 값이 V_id*다(as-built 값은 크기 근사 -- E-S5, 부호 있는 값으로 바꾸는 일은 gain-budget DE-1 (c)).

### 3.2 G-S2 matching 출발값

* **규칙(OB-5, v0.3.1 계획 정합)**: 출발값 σ 목표 집합 Σ_t(V) = {사용자 판정 제약 `offset_in_sigma_mv <=` 값 × `MILLI`} ∪ {matching `OffsetBound`마다 **커널 판정 문턱 항목 `b.threshold.value_v` / b.k**}(계획 v0.7 N3.3 'matching의 출발값' 행(211행)·gain-budget LR6(604행): σ 목표 = 커널 판정 문턱(루프에서는 조인 문턱 항목) / k, 사본 없이 그 문턱 항목 참조). 처음 변형에서 문턱 항목 값 = 요구 `offset_in_max_v`이므로 v0.3.0까지의 결과와 같고, OS-L 추가 변형에서는 조인 문턱 항목을 읽는다. matching L 하한 σ_share = min(Σ_t)/√2(`E/search/iv_matching_l.py:123`의 `min(absolute) * MILLI`를 `min(Σ_t)`로). 두 경로는 로더가 함께 두지 않는다(L2).
* **L/k인 근거**: 커널 판정이 k·σ_in ≤ L이므로(§3.1) σ_in ≤ L/k는 그 커널 판정 자체이고, front 판정 k·σ_in + \|V_id*\| ≤ L(\|V_id*\| ≥ 0)의 필요조건이기도 하다. 몫을 나누는 비율을 만들지 않는다. 출발값 전용이다(판정은 바뀌지 않는다).
* **문턱 의존(OB-20 정정, v0.3.1)**: v0.2.x~v0.3.0의 OB-20('출발값은 요구 값만, 조인 문턱 안 씀')은 계획 v0.7 N3.3·LR6과 달라 고쳤다(§18.2 '정정한 어긋남' B3). 출발값은 문턱 항목을 참조로 읽는다.
* **전달 형식**: `start_intervals` 블록 extras에는 (k, 문턱 항목 `value_v`) 쌍 tuple `offset_start_targets`만 넣는다(`build_search_context`가 `derived`의 matching `OffsetBound`의 k와 `threshold` 항목에서 만든다 -- 값의 출처는 그 항목 하나, extras는 블록 입력 투영이다).
* **입력이 같은 범위**: (1) **OS-L 반복 사이**(같은 base에서 문턱 항목만 다른 변형): `offset_start_targets`가 달라 `start_intervals`는 그 변형에서 **계산된다**(정당한 계산, 입력이 다름 -- 계획 N3.12 '재사용 범위' ①: 제약 문턱을 입력으로 읽는 S0 수준 블록은 계산되고 offset-trim G-12 '문턱에 의존하는 블록' 목록 안에 있어야 한다). 같은 문턱 값의 추가 변형끼리는 적중이다. (2) **compare 국면 1**: matching 변형에만 `OffsetBound`가 있어 다르다(각각 계산).
* **OT §20.7 목록 알림(§18.2)**: OT TR-0T v0.3.1 §20.7은 OB-20을 근거로 문턱 의존 블록 목록에서 `start_intervals`를 뺐다. v0.3.1부터 `start_intervals`는 문턱 의존 블록이므로 그 목록(offset-trim G-12)에 **다시 넣어야 한다**. offset-trim design 소유라 이 문서는 알림 항목으로만 낸다. matching 쪽 문턱 의존 계산은 `start_intervals`(S0 수준 블록)와 커널 행 둘이다.
* **요구 없는 spec의 비트 동일**: 양의 계수 곱은 단조라 min(vᵢ·`MILLI`) = min(vᵢ)·`MILLI`.
* **바뀌는 곳**: `E/search/iv_context.py`(`StartView.sigma_targets_v`), `E/search/iv_matching_l.py`(:107·:123), `E/search/start_intervals.py`(:253 extras), `E/search/search_context.py`(:195 호출).

### 3.3 G-S3 변형 정체(OS-5 형식, OS-L 확장)

| 이름 | 정의 |
|---|---|
| `constraint_set_fp` | `fp_of((spec 섹션 지문 'constraints_fp', derived(문턱 항목은 `target`과 `value_v`의 `float.hex` -- Δ_T 기록 참조 `margin_ref`는 제외), trim_decl.decl_fp 또는 None))`. 그래서 **같은 `constraint_set_fp`면 문턱 값이 같다**(정의상 사실, 검증 v0.2.2 N-2). 원인(Δ_T 기록)은 `cause_fp`가 따로 든다 |
| `cause_fp`(원인 지문) | 문턱 항목의 Δ_T 기록 지문(`margin_ref`의 sha256, §3.4). 처음 변형은 None |
| **중복 판정 키**(계획 v0.6.2 N3.12) | (토폴로지 변형 connectivity_fp, `constraint_set_fp`, `cause_fp`). `variant_fp` = `fp_of(이 키)`. **반복 번호는 키에 넣지 않는다**(넣으면 추가마다 키가 달라 중복 거부가 걸리지 않는다) |
| 반복 번호 `iteration` | 처음 목록 0, 추가될 때마다 1씩. **표시(보고) 칸**으로만 S3 줄·결과 JSON에 싣는다 |
| 중복 | 같은 키가 처음 목록에 두 번이면 `ValueError`(계획 함수 결함). 추가에서 같은 키(같은 원인 지문 포함)면 거부 `duplicate`(§13.3). Δ_T 기록이 다른데 문턱 값이 같은 추가는 키가 달라 허용된다(계획 키 그대로). 그 두 변형의 평가 입력은 같으므로, 평가 재사용은 문턱 값을 담은 `constraint_set_fp`로 묶는다(§10.3) |
| S3 칸(XS-13) | evals·runs 줄 최상위 키 `variant` = `variant_fp`, 같은 줄에 표시 칸 `iteration`. **OS-5에서 구현**(계획 XS-13·N7.2 배정 그대로). 싣는 조건 = 계획의 변형이 둘 이상이거나 반복 번호가 1 이상인 변형(OS-L). 변형 하나인 실행(요구 없음, OS-2 matching 단일 변형)은 칸이 없다 -- 그 실행의 줄은 S3 폴더·runs 줄 `run_id`(§6.5, 유도 제약 지문 포함)와 evals 행 이름 `req:`로 구분된다. 요구 없는 실행의 줄은 그대로(완료 조건 1) |
| `run_id` | §6.5 |

### 3.4 G-S4 유도 제약 기록 형식

**`derived` 항목 형식**(이 design 소유, 계획 v0.6.2 N3.12 '형식 소유'): `derived` = 항목 tuple이고 항목은 두 종류다.

```python
# 문턱 항목 -- authoring 값 모듈(E/authoring/spec_model.py). OT §20.3 tightened_threshold 의 반환 형식이 이것이다
ThresholdItem(target: str,          # 문턱의 spec 선언 위치(= spec 참조, 칸 하나 -- 검증 v0.2.2 N-5): "human.offset_requirement.offset_in_max_v"
                                    #   | "human.offset_trim.residual_offset_v"(키 접미 `_v` -- 단위 V)
              value_v: float,       # 문턱 값(V). 처음 변형 = 선언의 해석된 값, 추가 변형 = 선언 값 − Δ_T
              margin_ref: tuple | None)   # Δ_T 기록 참조 (기록 키 temp_margin_<metric>_v, 기록 id, sha256). 처음 변형 None

# matching 유도 제약 -- search 값 모듈(E/search/search_values.py)
OffsetBound(name: str,              # "offset_matching"
            sigma_metric: str,      # "offset_in_sigma_mv"
            sys_metric: str,        # "offset_sys_mv"
            k: float,               # 요구 coverage_multiple 의 해석된 값
            k_ref: str,             # "human.offset_requirement.coverage_multiple"
            threshold: ThresholdItem,   # 문턱 자리(entry 자리) -- target = 요구 offset_in_max_v
            view: ViewDecl,
            source_fp: str)         # 요구 섹션 지문
```

* **항목 자리**: matching 문턱은 `OffsetBound.threshold` 자리, trim 잔여 문턱(target = `offset_trim.residual_offset_v`)은 `derived` 최상위의 `ThresholdItem` 항목으로 둔다(OT `trim_constraint_rows`가 읽는다, TR-TL 몫). 한 변형의 `derived`에 같은 `target`의 문턱이 둘이면 거부(`ValueError`, 형식 결함).
* **단위(검증 v0.2.1 N-8)**: `value_v`는 V다. `target` 키는 접미 `_v`여야 하고(DEC-68), Δ_T 기록 키도 `temp_margin_<metric>_v`(OT §20.2)라 같은 단위다. 접미가 `_v`가 아닌 `target`은 추가 거부 `threshold_unit`(§13.3).
* 처음 변형의 문턱 항목은 OS-2부터 실제로 쓰인다(합성 행의 L). 빈 자리를 미리 만드는 것이 아니다(계획 N3.11 '순서'와 정합). `margin_ref`가 None이 아닌 항목은 OS-L 전에는 생기지 않는다.
* 결과 JSON에는 참조 칸만 같은 이름으로 싣는다(값 칸 `k`·`value_v`는 싣지 않음 -- §8 '출력 기록 규칙').
* trim 국면 2 유도 제약 자체는 OT §10.6대로 `trim_decl`에서 만든다. k·V_res 출처만 §17.1로 바뀐다.

### 3.5 G-S5 S1v 계산 수 칸(사실 확인용)

`run_plan.shared.s1v_computes` = 실행 계획 안 S1v 블록(`s1v_fields` writer) `computes` 합, `s1v_inputs` = S1v 블록이 계산된 서로 다른 입력 버전 수(`RunCounters.snapshot()`에서). DS-2가 닫혔으므로(PD-3) 결정 근거가 아니라 '같은 topology 변형끼리 S1v 입력이 같다'의 확인용이다(완료 조건 4의 근거 칸).

### 3.6 G-S6 완료 조건 1의 비교 제외(PD-5 반영, 목록은 검증자 소유)

비교 = 요구 없는 실행. base = **OS-2의 실제 base master**(병합 직전 master -- XRUN-F1 card C 병합 뒤이고, gain-budget LA-1이 먼저 병합됐으면 그것도 포함)의 수작업 사슬(E-S18 하네스와 같은 인자·같은 진단 설정, 계획 v0.7 N7.2 'v0.5 반영'·N7.1 'OS-2와 gain-budget LA-1의 선후'), 대상 = OS-2 병합본의 `run_plan`. OS-2와 LA-1은 같은 통합 병합에 넣지 않는다(계획 N7.1). 같은 실행 환경, E_B 선언(40 §2.4.13 1차 검사 전제).

| 부류 | 칸 | 처리 |
|---|---|---|
| spec 지문 | `SizingSpecDoc.spec_fp`·`section_fps` | **제외하지 않는다**. 요구 섹션은 있을 때만 지문 묶음에 넣으므로(§4.1) 요구 없는 spec의 지문은 그대로다 |
| F2 블록 코드 해시에서 온 입력 버전 | `FieldValue.input_version`, 스냅샷 `block_versions`·`fp`, S3 evals `snapshot_fp`, `context_fp`(S3 폴더 이름·runs `s0`·평가 키 칸) | 제외. **판정 기준 변경으로 보고**한다(OT X-T5와 같은 종류) |
| F3 코드·실행 지문 | `code_fp`·`engine_code_fp`, `run_id` | 제외. 판정 기준 변경으로 보고 |
| 시간 T | 40 §2.4.13 (2) T 부류 | 제외 |
| 실행 경계 문구 변경(XS-7)으로 바뀌는 칸 | 예상 없음(그 실행의 블록 호출 집합은 같다). 나오면 FAIL로 보고하고 검증자가 목록에 더할지 정한다 | -- |
| 새 출력 | `<회로>.run_plan.json` | base에 없다. 내용을 단언한다: 변형 하나, `strategy`·`phase` null, `derived` 빈 목록 |
| 값 V | 그 밖 전부 | 비트 동일 |

* F2가 바뀌는 원인에는 spec 객체에 칸 `offset_requirement`(값 None)가 더해져 `fp_of(spec)`이 바뀌는 것도 들어간다(spec을 extras로 받는 `achievability`·`start_intervals`). 이것도 F2(입력 버전)이고 값은 바뀌지 않는다.

### 3.7 G-S1 matching 판정 ② front 판정(계획 v0.7 N3.3 ②, O-53 A2, DEC-74 소비자)

**자리(계획 N7.1 개정 항목 2)**: front 판정 k·σ_in + \|V_id*\| ≤ 문턱의 판정 자리는 **gain-budget DEC-74 front 전용 예외 자리 하나**다. 이 design은 새 판정 자리·새 V_id* 계산·새 위반 점 제외·새 비지배 재필터를 만들지 않는다. DEC-74가 이 예외의 '소비자 둘째'로 이 판정을 적었고(gain-budget v6.24 병합 `59ecc88e` DEC-74), 이 design은 그 소비자의 **입력 형식**만 정한다(계획 N7.2 OS-2 행 '(v0.7, O-53 A2)', 계획 N3.10 G-S1 ② '핵심 층 확장 = search front 판정 자리의 소비자 추가').

| 항목 | 규칙 |
|---|---|
| 판정 식 | k·σ_in + \|V_id*\| ≤ L(V). 정의·계산은 정본 인용만: V_id* = 부호 있는 계통 offset 한 칸(gain-budget DEC-23, ΔW 1차 감도 V_id* = −ΔV_out / A_dc, '1차' 표기, ΔW = 0이면 0 -- \|A_dc\| > 판정 분해능일 때만), 판정 W(단위 9 전 sizing W, 단위 9 뒤 실현 W로 다시), 위반 점 fail-closed front 제외·비지배 재필터(DEC-74) |
| 소비자가 받는 것 | 변형의 `derived`에 있는 matching `OffsetBound`(§3.4)의 참조: k(`k`·`k_ref`), 문턱 항목(`threshold` -- 커널 행과 **같은 항목 하나**), `sigma_metric`·`sys_metric` 이름, `view`. 전달 = `SearchContext.offset_bounds`(§5.3의 같은 참조 칸). 값 사본·새 칸 없음 |
| 값을 읽는 곳(계획 N7.1 개정 항목 3) | σ_in과 V_id*는 **그 front 점 자신의 스냅샷**에서 읽는다: σ_in = 그 점 평가 스냅샷의 `metrics_ss` 필드(커널 행이 읽은 같은 필드 -- 다시 계산하지 않는다), V_id* = DEC-74 자리가 그 점에서 낸 값(그 자리의 writer가 그 점 스냅샷에 쓴 필드 또는 기록). child 스냅샷에서 읽지 않는다(§3.1 '스냅샷 파생 규칙 영향' (3) -- 그 writer는 child 파생 때 남는 집합 밖이다). 값 사본을 만들어 넘기지 않는다 |
| 문턱 | 커널 행과 같은 문턱 항목 `b.threshold.value_v`. OS-L 조인 문턱도 같은 항목 하나(§13.2) |
| 단위 | σ_in·V_id* metric 단위 `mv` → u = `core.MILLI`(§3.1·OB-2와 같은 규칙), 문턱 V |
| 정의 불능(계획 v0.7.3 N3.3 ②) | **갈래 먼저**: \|A_dc\| ≤ 판정 분해능이면 ΔW와 무관하게 σ_in·V_id* 정의 불능(DEC-23 'A_dc 정의 불능 갈래', O-62 (3)·O-63 (1)). ΔW = 0 → V_id* = 0은 \|A_dc\| > 판정 분해능일 때만이다. 커널 출발 창 미수렴으로 front 값이 정의 불능인 점도 같다(O-64 (2) -- 그 규칙의 '선언 제약이 걸린 값'에 matching 유도 합성 제약이 들어간다). 정의 불능 점은 fail-closed로 front에서 빼고 비지배 재필터를 다시 돈다. **원인 = 그 정의 불능 사유 기록의 참조**(사유 사본 없음, offset 위반으로 적지 않음 -- 원인 오귀속 금지). 갈래 판정 자리는 DE-1 (c)가 고치는 A_dc 계산 자리 하나다(DEC-23 '엔진 소비자', 이름은 착수 실측). 이 design은 새 규칙을 두지 않는다 |
| 판정 결과의 자리 | DEC-74 자리의 **출력 기록** 하나(위반 점·정의 불능 점과 원인 참조). **종류 = 출력 기록**(gb v6.24 병합 `59ecc88e` DEC-74·N3.3 (b), 사용자 결정 O-68 (3)). 결과 JSON(§8)은 그것을 참조로 싣는다. **이름은 card DE-1 design·착수 실측이 정한다**(계획 v0.7.3 N7.1 'PS-1 잔여') -- 이름이 정해지기 전에는 OS-2를 시작하지 않는다(OS-2가 임시 기록 칸을 두면 둘째 자리 -- graph 규칙 1·3·6) |
| 단위 9 재판정 | 단위 9 card가 DEC-74 자리를 다시 부를 때 같은 소비자가 돈다. OS-2는 단위 9를 만들지 않는다(계획 N7.2 OS-2 행) |
| 검증 출처 | §12(OS-V) |

* **trim 방식**: front 판정이 아니라 offset-trim 보정 구간 판정이다(O-53 A2 끝 문장·A3, offset-trim 계획 v0.6 정본). 이 절은 matching 전용이다.
* **선행(계획 사슬 인용, v0.3.1 정정)**: DEC-74 front 자리(V_id* 계산·front 판정·위반 점 제외·비지배 재필터)를 만드는 card는 gain-budget **DE-1 (c)**다(gb N6.8 DE-1 범위 (c) '계통 offset'). 계획 사슬: LA-1의 선행에 DE-1이 있고(gb N6.1 LA-1 행 '선행' 칸), LA-1은 U17 ②와 **같은 통합 병합**이다(gb N6.14 LA-1 'U17 ②와 같은 통합 병합'·LA-Q5 (가)). 그래서 OS-2 착수 조건 'U17 ② 병합'(계획 N7.1)은 DE-1 병합을 이미 함의하고, 계획 v0.7.3은 OS-2 선행 칸에 DE-1 (c)를 명시했다. v0.3.0의 'LA-1(front 판정 배선, gb O-44 (1))이 이 자리를 만든다'는 근거가 틀렸고(O-44 (1)의 'front 판정 배선'은 DEC-98 oracle 판정 배선) 지웠다. 남는 것은 그 자리의 **이름**뿐이다(종류 = 출력 기록은 gb v6.24·O-68 (3)로 정해짐): 이 절의 소비자 형식, §8 `front_judgment` 칸, 완료 조건 10 (b) test의 필드 이름은 **DE-1 design·착수 실측 뒤 확정**이고, 그 전에는 OS-2를 시작하지 않는다(계획 v0.7.3 N7.1).

---

## 4. 요구 스키마와 로더

### 4.1 스키마 `human.offset_requirement`

선택 섹션(`HUMAN_OPTIONAL`에 더함, 스키마 버전 그대로):

```json
"offset_requirement": {
  "offset_in_max_v":              {"value": <V>,  "source": {<user_spec 출처>}},
  "coverage_multiple":            {"value": <k>,  "source": {<user_spec 출처>}},
  "strategy":                     {"value": "matching" | "trim" | "compare", "source": {<user_spec 출처>}},
  "judgment_temperature_range_c": {"value": {"lo": <°C>, "hi": <°C>}, "source": {<user_spec 출처>}}
}
```

| 키 | 뜻 | 형식 검사(사유) | 필수 |
|---|---|---|---|
| `offset_in_max_v` | 입력 환산 offset 한계(V) | 유한 양수(`offset_requirement_value`) | 예 |
| `coverage_multiple` | k(σ_in 배수). matching 상한과 trim 보정 구간이 같은 k(DS-U3) | 유한 양수(`offset_requirement_value`) | 예 |
| `strategy` | 방식 | 닫힌 어휘(`offset_requirement_strategy`) | 예 |
| `judgment_temperature_range_c` | offset·trim 잔여 합격을 판정할 온도 구간(°C, T-34). 소비자 = TR-7 온도 보고 sweep, SPICE 온도 보정 루프의 범위 판정(둘 다 이 선언을 참조, 숫자 사본 금지) | `lo`·`hi` 둘 다 유한 수, `lo` < `hi`(`offset_requirement_temperature_range`). 닫힌 키 `lo`·`hi`(기존 `ThetaBound(lo, hi)` 이름 관례, `E/authoring/spec_theta_bounds.py:9-10`) | **아니오(OB-21)** -- 소비자가 필요할 때 없으면 그 소비자가 `offset_requirement_temperature_range_undeclared`로 거부한다 |

* 이름은 DEC-68: `_v` = V, `_c` = °C(OT §5.1 선례 `trim_temperature_c`), 무차원 배수는 접미 없음. `lo`·`hi`는 칸 이름이라 단위 접미를 두지 않는다(단위는 키 이름 `_c`가 정한다).
* trim 온도 T_j가 구간 안에 드는지의 검사는 offset-trim 소관(OTP O-8)이다.
* 출처 `user_spec`만(`ALLOWED_KINDS`에 `offset_requirement` = (`user_spec`,)). 결정 대기는 섹션 전체 자리에만(값 하나만 대기는 `type`). 빠진 필수 키 `missing_key`, 밖의 키 `unknown_key`.
* 값 형식(`E/authoring/spec_model.py`): `OffsetRequirement(offset_in_max_v, coverage_multiple, strategy, view, judgment_temperature_range_c, sources)`. `judgment_temperature_range_c`는 (lo, hi) 또는 None.
* **지문(PD-5)**: `SizingSpecDoc`에 칸 `offset_requirement`(없거나 결정 대기면 None)를 더한다. `_section_fps`는 이 칸이 None이 아닐 때만 묶음 `("requirement_fp", ("offset_requirement",))`를 더한다(OT §3.3 선례). 그래서 요구 없는 spec의 `section_fps`·`spec_fp`는 지금과 비트 동일하다. 구현: `SECTION_GROUPS`(`E/authoring/spec_model.py:306-321`)는 그대로 두고, 선택 묶음 표 `OPTIONAL_SECTION_GROUPS`를 따로 두어 `_section_fps`(:324-335)가 값이 None이 아닌 것만 붙인다.

### 4.2 로더·계획 함수 규칙과 사유 코드

gate `spec_load` 행은 `load_sizing_spec`이 모든 위반을 모아 한 번에 거부하고(`E/authoring/spec_load.py:15-19`), gate `run_plan` 행은 `build_run_plan`이 던진다. 모두 `SchemaRejectedError`(exit 7).

| # | 상황 | 사유 코드 | gate | card |
|---|---|---|---|---|
| L1 | 값 형식 위반 | `offset_requirement_value`·`offset_requirement_strategy`·`offset_requirement_temperature_range`·`type`·`missing_key`·`unknown_key`·출처 규칙 | spec_load | OS-2 |
| L2 | 요구와 `offset_in_sigma_mv`·`offset_sys_mv`·`offset_excess`의 **판정 제약**(`judged` 참: 출처 `user_spec`, 판정 대상을 가리키는 `reference`)이 함께 있음(PD-9 (가), S-10). `pending_spice` offset 항목과 `pending_constraints`는 허용한다(그 항목이 판정 제약이 되는 순간 같은 검사가 거부) | `offset_requirement_conflicts_constraint`(detail = 위치, metric) | spec_load | OS-2 |
| L3 | 포트 뷰가 정해지지 않음 | `offset_requirement_view_required` | spec_load | OS-2 |
| L4 | matching(또는 compare의 matching 변형)이고 포트 뷰 관측이 단일 출력인데 그 넷이 `dc_inputs_from_spec(spec).node_targets`에 없음(`offset_systematic`과 같은 출처, '출력 기준 DC' 기능이 출처를 바꾸면 같은 변경에서 따라간다) | `offset_requirement_reference_undeclared` | run_plan | OS-2 |
| L5 | 유도 제약 항 단위가 `mv`가 아님 | `offset_requirement_unit_unsupported` | run_plan | OS-2 |
| L6 | `trim`·`compare` 경로 미개방 | `offset_strategy_not_open`(detail = strategy) | run_plan | OS-2(거부), TR-2·OS-5(해제) |
| L7 | `trim`·`compare`인데 `offset_trim` 없음 | `offset_requirement_trim_undeclared` | spec_load | TR-1 |
| L8 | `matching`인데 `offset_trim` 있음 | `offset_requirement_trim_unused` | spec_load | TR-1 |
| L9 | `offset_trim`만 있고 요구 없음 | `offset_trim_without_requirement` | spec_load | TR-1 |
| L10 | V_res > `offset_in_max_v` | `offset_trim_residual_exceeds_requirement` | spec_load | TR-1 |
| L11 | compare인데 공통 판정 없음(DS-U4: 1/f 하나 이상 + `area_search_m2 <=`, 둘 다 값 있는 판정 제약) | `offset_compare_common_judgment_missing` | run_plan | OS-5(PD-6) |
| L12 | 요구 섹션 결정 대기 | 사유 없음 -- 요구 없음과 같다 | -- | OS-2 |

* **L2의 자리**: `judged`는 참조 해석 뒤에 정해지므로(E-S16) L2 검사는 `resolve_spec_references` 뒤(`E/authoring/spec_load.py:142` 다음, 최종 거부 :144 전)에 한다(v0.2부터 이 순서, 검증 N-6 확인). 앞 게이트 위반이 있으면 로더는 참조를 해석하지 않고 거부하므로(`E/authoring/spec_load.py:130-132`) 그때 L2는 돌지 않는다(이미 거부). 검사 함수는 별도 파일(§14.1).
* **L3과 meta 불일치**: meta의 회로 이름·topology 지문이 맞지 않으면 로더는 `topo` = None으로 교차 검사를 끄고(`E/authoring/spec_load.py:90-93`) 그 로드는 meta 위반으로 거부된다. 이때 요구 섹션은 형식(L1)만 보고 포트 뷰를 유도하지 않는다(`view` = None, L3 판정 안 함). 기존 제약 로더가 `topology` None이면 기본 뷰를 유도하지 않는 것과 같은 규칙이다(`E/authoring/spec_constraints.py:39, :202-203`). 결과는 어차피 거부라 조용히 통과하는 경로가 없다.
* L4·L5·L6·L11을 계획 함수에 두는 근거(OB-7): L4는 sizing(`DcInputs`)을 읽어야 하는데 로더(authoring)는 sizing을 import할 수 없다. 나머지는 방식·국면별 규칙이다. 넷 다 단계 B·탐색 전이다.
* `offset_trim` 섹션은 TR-1 전에는 `unknown_key`다(T-28). 그래서 L7~L10은 TR-1이 구현한다.

### 4.3 k 단일 출처(DS-U3)

k는 `offset_requirement.coverage_multiple` 하나다. OT §5.1의 `offset_trim.coverage_multiple`은 없앤다(§17.1). trim 쪽 소비자(OT §9.4, §10.4, §10.6, §17)는 요구의 k를 읽는다. 승인 결속 지문은 요구 섹션을 포함한다(§17.1, OB-15).

---

## 5. 실행 계획

### 5.1 값 형식(`E/pipeline/run_plan_values.py`, frozen dataclass)

```python
PlanVariant(index: int,                 # 계획 안 순서(0부터, 추가 변형은 뒤에)
            label: str,                 # "baseline" | "matching" | "trim_phase1" | "trim_phase2"
            topology: TopologyDoc,      # 토폴로지 변형
            derived: tuple,             # OffsetBound tuple, 없으면 ()
            trim_decl: object,          # 국면 2면 TrimDecl, 그 밖 None
            iteration: int,             # 처음 목록 0, 추가 변형 1, 2, ...(§13)
            cause_fp: str | None,       # 추가 원인(Δ_T 입력 지문), 처음 목록 None
            variant_fp: str)            # §3.3
RunPlan(strategy: str | None, phase: int | None, requirement: OffsetRequirement | None,
        variants: tuple[PlanVariant, ...], budget_unit: str)    # budget_unit = "variant"(XS-12)
```

* `label` 어휘는 닫힌 집합이다. OS-2는 `baseline`·`matching`만 만든다.
* `RunPlan`은 graph 필드가 아니라 실행 입력·출력이다. 세션은 처음 `RunPlan`을 받고, 추가 변형은 세션이 새 `RunPlan` 값(앞 변형 + 추가 변형)으로 바꿔 든다(불변 값 교체).

### 5.2 계획 함수 `build_run_plan`

**서명**: OS-2 `build_run_plan(spec, topology) -> RunPlan`. TR-2부터 `build_run_plan(spec, topology, approvals) -> RunPlan`(계획 N3.5 '구현 시점'). 결정적 순수 함수, 파일을 읽거나 쓰지 않는다. **처음 변형 목록만** 만든다. 실행 중 추가는 세션 몫이다(§13).

| 요구 `strategy` | 승인 기록 | 처음 변형(순서대로) | card |
|---|---|---|---|
| 요구 없음 | -- | (원본, ()) `baseline` | OS-2 |
| `matching` | -- | (원본, (matching `OffsetBound`,)) `matching`. 만들기 전 L4·L5 | OS-2 |
| `trim`·`compare` | -- | L6 | OS-2 |
| `trim` | 없음 | (원본, ()) `trim_phase1` | TR-2 |
| `trim` | 있음 | TR-2: `trim_phase2_not_open`. TR-3부터: 승인된 구성마다 (파생, (), trim_decl) `trim_phase2` | TR-2 / TR-3 |
| `compare` | 없음 | `matching`, `trim_phase1`(원본 topology 둘). L4·L5·L11 | OS-5 |
| `compare` | 있음 | 승인된 구성마다 `trim_phase2` | TR-3·OS-5 |

* matching `OffsetBound`(같은 파일 비공개 함수): `name` = `offset_matching`, metric 이름은 레지스트리 이름, k·k_ref·view·source_fp는 `spec.offset_requirement`에서, `threshold` = `ThresholdItem(target = "human.offset_requirement.offset_in_max_v", value_v = 요구 값, margin_ref = None)`.
* 처음 순서는 표 순서 고정(DO-3). 변형 정체 중복이면 `ValueError`(§3.3).

### 5.3 변형 제약 주입(PD-1, S-8)

로드한 spec 객체 하나를 모든 변형이 같이 쓰고, 변형의 유도 제약만 `build_search_context(..., derived=...)`로 넣는다. spec 사본을 만들지 않는다. **탐색 층(search)에서** `derived`를 읽는 곳은 넷뿐이다(v0.3.0에 front 판정 입력이 더해짐). 이 셈은 탐색 층 계산 소비자만이다(검증 N3). 그 밖에 `derived`를 읽는 곳은 (1) 변형 정체 `constraint_set_fp`(§3.3, OS-5 평가 키 -- 지문 입력), (2) `run_id`의 중복 판정 키(§6.5), (3) 결과 JSON `variants[].derived` 참조 칸(§8, 출력 전용)이고, 셋 다 값을 계산하지 않는 지문·출력 소비자다.

| 소비자 | 읽는 방식 |
|---|---|
| 커널 요청·합성 행(§3.1) | `SearchContext.offset_bounds`(참조 칸 `derived`, `driving`이 `spec.driving_spec`을 읽는 방식과 같다, `E/search/search_context.py:129-131`) |
| 출발 구간(§3.2) | `start_intervals` extras `offset_start_targets` = ((k, 문턱 항목 `value_v`), ...) -- 커널 판정 문턱 항목에서(계획 N3.3·LR6) |
| LUT mismatch 필수 검사(E-S12) | `derived`가 비지 않으면 같은 검사(커널 행의 항 `offset_in_sigma_mv`가 mismatch 데이터를 쓴다. front 판정의 V_id*는 mismatch 데이터를 쓰지 않으므로 검사 근거는 σ_in 항이다) |
| front 판정 입력(§3.7) | 같은 참조 칸 `SearchContext.offset_bounds`. DEC-74 front 자리가 matching `OffsetBound`의 k·문턱 항목을 읽는다 |

그래서 S1v·`constraint_classes`·`search_domain`·`achievability`의 입력은 같은 topology 변형 사이(그리고 OS-L 반복 사이)에 같다. `start_intervals`는 문턱 값이 다른 OS-L 반복 사이와 compare 국면 1에서 다르다(§3.2).

---

## 6. 실행 계획 세션과 `run_plan`(W-1, XS-17)

### 6.1 세션(`E/pipeline/plan_session.py`)

```python
def open_plan_session(topology_path, spec_path, lut, memo, pdk_decl, lut_rule_decl, *, output_dir, settings,
                      archive_root, supplies_v=None, structure_path=None, given_starts=(), model_error=(),
                      diagnostic=False) -> PlanSession
# OS-L이 필수 키워드 iteration_cap(int | None, 기본값 없음)을 더한다(§13.4). OS-2에서는 빈 자리를 만들지 않는다

class PlanSession:
    plan: RunPlan                                   # 지금 목록(읽기 전용, 추가 때 새 값으로 바뀐다)
    stage_a: StageAResult                           # 원본 단계 A(읽기 전용) -- 열린 동안만, 닫은 뒤 접근은 ValueError
    block_index: S3Index                            # 세션의 블록 결과 색인(읽기 전용) -- 열린 동안만, 닫은 뒤 ValueError
    def search_context(self, index) -> SearchContext | None   # 그 변형의 탐색 컨텍스트(읽기 전용) -- 열린 동안만
    def run_variant(self, index) -> VariantResult   # 변형 하나 실행(같은 index 두 번이면 ValueError)
    def add_variant(self, base_index, threshold_item) -> PlanVariant   # OS-L(§13)
    def close(self) -> PlanResult                   # 결과 JSON을 쓰고 색인·계수를 버린다(계획 N3.12 ④)
```

* **열기**(실행 경계, XS-7): 블록 결과 색인과 계수는 **`donors, counters = open_run()` 하나로만** 만든다(40 §2.4.5 '수명' (1), E-S21 -- `S3Index(`·`RunCounters(` 직접 생성 금지, 규칙 M (M-b)). 그 쌍으로 원본 단계 A `run_stage_a(..., donors=donors, counters=counters)`를 돈다(필수 키워드, card B 서명 `E/pipeline/stage_a.py:206`).
  * **구조 규칙 M과의 관계**(40 §2.4.5 (2), 검증 B2): (M-a) `E/pipeline/plan_session.py`를 `open_run` 참조 허용 목록에 더한다(40이 'OS-2가 실행 계획 세션 열기 파일 하나를 더한다'고 적은 자리). (M-c) OS-2는 `run_stage_a` 호출 하나에 `open_run()` 하나라 규칙 그대로다. OS-5·TR-3(토폴로지 변형마다 단계 A, §6.3)에서 같은 쌍을 같은 세션 안 여러 `run_stage_a`에 넘기는 것은 40이 예약한 예외('실행 계획 세션 열기 파일 -- 같은 실행 계획 안 변형 공유는 그 파일 안에서만')이고, 그 예외의 `check_m` 반영은 그 card(OS-5)가 한다. (M-d) 세션은 쌍을 인스턴스 속성으로 쥔다. 40 (M-d)의 '수명이 긴 객체의 인스턴스 속성' 금지는 test 맥락 문언이라 엔진 세션 객체에 대한 허용 문언이 없다 -- §17.2 40 개정안(M-d 예외: 세션 인스턴스, `close`가 참조를 버림)으로 올린다. (M-f) 세션은 색인·계수를 디스크에 쓰지 않는다.
  * **card C·OS-5 생성자 인자**: card C의 상한 인자와 OS-5의 `s0_sets`(B_S0)는 `open_run`이 받아 넘긴다(40 '수명' (1)). **순환(검증 M10, 멈춤 §18.4 PS-6)**: B_S0는 계획(변형 수)에서 나오고(PD-7) 계획은 단계 A의 spec에서 나오는데, 단계 A는 `open_run`의 쌍을 받아야 돈다. 계획·40 어디에도 이 순서를 푸는 문언이 없다. OS-2는 `s0_sets`를 더하지 않으므로 OS-2는 막히지 않는다.
  * 이어서: 결과에 칸 `topology`(로드한 `TopologyDoc`)를 더한다. **계획 생성 조건은 하나다(검증 v0.2.1 N-4)**: `stage_a.spec is not None`이면 `build_run_plan(stage_a.spec, stage_a.topology)`(TR-2부터 `approvals`)로 처음 목록을 만든다(단계 A가 끝까지 가서 spec을 결과에 실은 경우 -- `E/pipeline/stage_a.py:194-196, :250`. 그 전 정지 경로는 spec을 싣지 않는다). spec이 None이면 계획 없이 원본 topology로 `run_stage_b`를 한 번 불러(`skipped`를 돌려준다, `E/pipeline/stage_b.py:141-142`) `PlanResult.stage_b_unplanned`에 둔다 -- 하네스가 단계 A 실패 때도 단계 B 보고서를 쓰는 것과 같은 출력 파일을 내기 위해서다(완료 조건 1의 출력 집합 정합). 계획 함수 거부(`SchemaRejectedError`)는 세션을 '거부 상태'로 열어 두고(`plan` = None, 사유 기록) `close`가 결과 JSON에 쓴다 -- 변형 실행은 0이다.
* **변형 실행 `run_variant(i)`**:
  1. 단계 B: 변형마다 `run_stage_b`를 부른다. 별도 pipeline 수준 캐시(토폴로지 지문 키 사전)는 두지 않는다(검증 N-7): 재사용 경로는 블록 결과 색인 하나이고(단계 B 블록은 입력이 `derived`와 무관해 같은 토폴로지 변형끼리 모두 색인 적중), 두 번째 재사용 경로를 만들지 않는다. OS-2는 변형이 하나라 한 번 부른다. `diagnostic`은 그대로 넘긴다: `run_stage_b(stage_a, memo, pdk_decl, output_dir=, settings=, diagnostic=diagnostic)`(`E/pipeline/stage_b.py:134` 서명 그대로, 진단 뜻 = 측정만, 단계 A 상태·exit code 유지).
  2. **탐색 조건**: 단계 A `ok`이고 단계 B `ok`일 때만 커널 컨텍스트 → `build_search_context(kctx, stage_a.spec, settings, archive_root, pdk_decl, lut_rule_decl, model_error, code_fp=stage_a.code_fp, derived=variant.derived)` → `find_front(sctx, given_starts)`. 아니면 `VariantResult.stop` = `stage_a_<상태>` 또는 `stage_b_<상태>`(하네스 :395와 같은 조건).
  3. `given_starts`는 원본 topology 변형에만 넘긴다(파생 topology는 θ 스키마가 달라 `()`, OB-17).
  4. `find_front`는 `gmid_engine.search` 패키지의 함수를 부른다. `find_front` 모듈 안에서 `layer0_start`·`sweep_front`를 모듈 전역 이름으로 부르는 방식(관찰 지점 계약 J-3·J-7)을 바꾸지 않으므로 하네스의 모듈 속성 감싸기가 `run_plan` 경로에서도 그대로 동작한다(E-S18 (1)).
* **닫기**(계획 N3.12 ④ '색인·계수를 버린다', '수명' 341행 '세션을 닫으면 버린다. 세션 사이·실행 사이에 넘기지 않는다'): `<회로>.run_plan.json`(§8)을 쓰고 색인·계수·탐색 컨텍스트·단계 A 결과의 참조를 버린다. 닫은 뒤 `stage_a`·`block_index`·`search_context`·`run_variant`·`add_variant`는 `ValueError`. `close`가 돌려주는 `PlanResult`와 `run_variant`가 돌려주는 `VariantResult`에는 색인·계수, 또는 그것을 담은 객체(`SearchContext`, 과도기 칸 `donors`·`counters`가 있는 `StageAResult`·`KernelContext`)의 참조를 싣지 않는다 -- 닫은 뒤 색인에 닿는 길은 0이다(40 §2.4.5 '수명', 규칙 M (M-d)).
* **허용 동작**(계획 N3.12): 세션을 열고 처음 변형은 실행하지 않은 채 변형을 추가해 그 변형만 실행할 수 있다(결정성 비교 기준이 쓴다).

### 6.2 `run_plan`(얇은 진입, `E/pipeline/run_plan.py`)

```python
def run_plan(topology_path, spec_path, lut, memo, pdk_decl, lut_rule_decl, *, output_dir, settings, archive_root,
             supplies_v=None, structure_path=None, given_starts=(), model_error=(), diagnostic=False) -> PlanResult
```

= `open_plan_session(...)` → 처음 변형 모두 `run_variant` → `close`. 사슬 구현은 세션 하나다(W-1 '사슬 두 벌 금지', XS-17).

### 6.3 공유 범위

| 대상 | OS-2(변형 하나) | OS-5·OS-L(변형 둘 이상) |
|---|---|---|
| 블록 결과 색인·`RunCounters` | 세션 열기에서 하나 | 같음 |
| 단계 A | 원본 한 번 | 토폴로지 변형마다 한 번 |
| 단계 B | 한 번 | 변형마다 호출, 같은 토폴로지 변형끼리 블록은 색인 적중(계산 0). 같은 토폴로지 변형들은 같은 `stage_b_report` 파일(회로 이름 기준 경로)을 가리키고 그 파일은 변형마다 다시 쓰인다. **'같은 내용'의 조건(검증 N5)**: 단계 B가 `derived`를 읽지 않고(`run_stage_b` 서명에 `derived`가 없다, §5.3 -- 소비자는 탐색 층뿐) 같은 `stage_a`·`diagnostic`·`settings`를 받으므로 보고서 내용이 같다. 단계 B가 `derived`나 변형별 입력을 읽게 되면 이 조건이 깨지므로 그때는 변형별 경로가 필요하다(그 변경의 design 몫) |
| S0 탐색 블록 | 한 번 | 같은 topology 변형끼리 적중(§5.3). `start_intervals`는 문턱 값이 같은 변형끼리만 적중, 문턱 값이 다른 OS-L 반복과 compare 국면 1에서는 변형마다 계산(입력이 다름, §3.2) |
| S1v | 한 번 | 같은 topology 변형끼리 같은 입력 |
| 평가 캐시 | 하나 | DS-1 = (다)(S-14, §10): `S3Index` 하나를 공유하고 평가 키에 `constraint_set_fp`를 넣는다. 지금 키 그대로 공유 금지 |

### 6.4 하네스 노출(B-1, W-1 요구 전수)

E-S18의 하네스가 읽거나 넘기는 값마다 자리다. 새 값을 만들지 않고 이미 있는 객체의 **읽기 전용 참조**를 낸다. **색인·계수에 닿는 값은 세션이 열린 동안 세션 공개 API로만 읽는다**: 하네스 순서 = `open_plan_session` → `run_variant` → 읽기 → `close`(검증 B1, 계획 N3.12 ④·'수명'). `run_plan`(열기 → 실행 → 닫기)의 반환 `PlanResult`에는 그런 값이 없다. **계획 규칙(v0.7.2, 사용자 O-63 (3)·O-65)**: 하네스가 블록 결과 색인의 평가 키 부분 같은 실행 수명 값을 읽어야 하면 `run_plan` 결과가 아니라 같은 세션 인터페이스의 공개 API로 세션이 열린 동안 읽는다(열기 → 변형 실행 → 읽기 → 닫기). 결과 객체는 색인·donors·계수 참조를 담지 않는다. 그 세션은 `run_plan`이 쓰는 사슬 그대로라 사슬은 하나다(계획 S-9 126행, N3.6 249행, N3.12 339·341행, N7.2 'v0.5 반영' W-1 485행, N11.1 665행). `run_plan`은 열기 → 처음 변형 모두 실행 → 닫기의 얇은 진입이고(§6.2), 실행 수명 값을 읽지 않는 호출자(그런 test·나중의 U16 CLI)는 `run_plan`을 쓴다. 파일 배정은 §14.1(`plan_session.py` = OS-2, `add_variant`·`iteration_cap` 키워드만 OS-L)과 같다. 세션의 열기·변형 실행·읽기·닫기는 OS-2 몫이고 OS-L은 `add_variant`만 더한다(계획 N7.2 OS-2 행).

| 하네스가 쓰는 것(E-S18) | 자리 |
|---|---|
| 입력 `lut`·`LutMemo`(크기 인자는 호출자)·`pdk`·`rule`·`settings`·S3 루트·output_dir·`given_starts` | `run_plan` 인자 그대로(호출자가 만든다) |
| 진단 모드 `diagnostic=True` | `run_plan(..., diagnostic=True)` → 단계 B에 같은 뜻으로. **표지는 단계 B 보고서의 `diagnostic` 칸 하나다**(`E/pipeline/stage_b.py:129` `report["diagnostic"]`, 같은 값이 `StageBResult`에 실림 :131). `run_plan` 결과는 그 칸을 참조로 낸다: 객체는 `VariantResult.stage_b`·`PlanResult.stage_b_unplanned`(`StageBResult` 참조), 결과 JSON은 변형마다 `stage_b_report`(그 보고서 경로, `report_paths[0]`). `PlanResult`·결과 JSON에 `diagnostic` 둘째 칸을 두지 않는다(graph 단일 정본 규칙 4, 계획 N7.1 확인 항목 1). 단계 B가 돌지 않은 실행(계획 거부)에는 표지가 없다 -- 진단 모드는 단계 B의 동작이므로 표지할 대상이 없다. **spec 없이 멈춘 단계 A(검증 N4)**: `stage_b_unplanned`의 보고서는 결과 JSON 최상위 칸 `stage_b_unplanned_report`(그 보고서 경로, 변형이 없어 `variants[]`에 자리가 없다)로 참조한다. 이 경로는 `E/pipeline/stage_b.py:140-142`의 `skipped` 분기이고 보고서 `diagnostic`을 **언제나 False**로 쓴다(진단 인자와 무관 -- 계산하지 않았다는 뜻). 그래서 그 경우의 표지는 '진단 모드로 계산했다'가 아니라 '계산 안 함'이다 |
| `find_front` 모듈 속성 감싸기 | 그대로 동작(§6.1 4) |
| 단계 A가 A1_load 등에서 spec 없이 멈춰도 하네스는 `run_stage_b`를 불러(`skipped`) 단계 B 보고서를 쓴다(`nfr4_run_dump.py:387-393`) | `PlanResult.stage_b_unplanned`(§6.1 '계획 생성 조건' -- spec이 None이면 원본 topology로 한 번 불러 같은 보고서 파일을 쓴다) |
| `a.code_fp`·`a.report_paths`·`a.status`·`a.s1.snapshot.fp` | 열린 동안 `session.stage_a`(`StageAResult` 참조) |
| `b.report_paths`·`b.status`·`b.s1.snapshot.fp` | `VariantResult.stage_b`(그 변형의 `StageBResult` 참조 -- 색인·계수 칸이 없다) |
| `sctx.domain.w_min_m`·`sctx.dc.base`·`sctx.context_fp` | 열린 동안 `session.search_context(i)`(탐색하지 않았으면 None) |
| 평가 결과 목록(하네스 `seq`·`evaluation.snapshot`) | 열린 동안 `session.block_index`의 **평가 키 부분 API**(계획 N7.1 확인 항목 2: 정본 = S3 메모리 색인의 평가 키 부분). `sctx.cache`는 노출하지 않고 읽는 경로도 만들지 않는다(U17 ②·GC-7에서 지울 대상, OS-2는 U17 ② 뒤 착수). 평가 목록을 모은 사본·dict를 만들지 않는다. **평가 키 부분의 열거 API는 40 §2.4.5 조회 API에 없다**(`get(key)`뿐이고 '색인을 순회하지 않는다' -- 결정성 행). 하네스가 전수를 읽는 길은 U17 ② design 몫이다(§18.4 PS-7, 멈춤) |
| `fr`(`SearchFront`)·`fr.perf` | `VariantResult.front` |
| 탐색하지 않았을 때의 S0 스냅샷(`b.s1` 또는 `a.s1`) | `VariantResult.stage_b.s1` / 열린 동안 `session.stage_a.s1` |
| S3 evals·runs 파일 | `archive_root / <context_fp>` -- `context_fp`는 열린 동안 `session.search_context(i)`에서, 닫은 뒤에는 결과 JSON `variants[].s3_dir`(경로 규칙 그대로) |

* 값 형식: `VariantResult(variant, stage_b, front, stop)`, `PlanResult(plan, stage_b_unplanned, variants, rejected, perf, report_path, exit_code)`(`E/pipeline/run_plan_values.py`). `perf` = 세션 전체 `RunCounters.snapshot()`의 반환(계수 객체가 아니라 그 출력). v0.3.0의 `PlanResult.block_index`·`PlanResult.stage_a`·`VariantResult.search_context`와 OB-37은 지웠다(검증 B1·M8 -- 계획 N3.12 ④ '버린다').
* **대체 범위(OB-22)**: 계획 W-1이 대체 대상으로 적은 것은 전체 사슬(`run_stage_a` → `run_stage_b` → `build_kernel_context` → `build_search_context` → `find_front`)이다. 그래서 E-S19의 전체 사슬 셋(`nfr4_run_dump.py`, `test_no_s0_files_written.py`, `test_rerun_s3_independence.py`)을 같은 변경에서 세션 경로(`open_plan_session` → `run_variant` → 읽기 → `close`, 사후 읽기가 없으면 `run_plan`)로 바꾸고 옛 수작업 사슬과 그 `open_run` 호출을 지운다. 탐색 컨텍스트까지만 만들고 내부 함수(층 0 등)를 직접 부르는 부분 사슬 test와 진입점 재확인 test는 단계 함수의 단위 시험이라 이 대체 범위에 넣지 않는다. 이 범위 해석은 §18.4 Q-1로 확인받는다.

### 6.5 `run_id`(OB-11)

`find_front`의 `run_id` 지문 tuple 끝에, 변형에 `derived`나 `trim_decl`이 있을 때만 그 변형의 **중복 판정 키**(§3.3: topology 지문, `constraint_set_fp`, `cause_fp`)의 `fp_of`를 더한다(`E/search/find_front.py:131`, 계획 v0.6.2 N3.12 '`run_id`에 키 반영'). **전달 = `find_front`의 명시 인자**(v0.3.3 검증 V11 -- graph 규칙 2: 승인된 자리 밖 새 context 슬롯 금지, `variant_key` 슬롯 승인 없음): 서명 `find_front(sctx, given_starts, *, variant_key)`(지금 `def find_front(sctx, given_starts)` `E/search/find_front.py:64`). `variant_key`는 필수 키워드(기본값 없음 -- X-7·PD-7 '기본값 인자로 피하지 않는다'와 같은 원칙)이고 소비자는 `run_id`(`:131`) 하나다. `SearchContext`에 칸을 두지 않는다. 부르는 곳: 엔진 소스 0(docstring 네 곳만 -- `search/find_front.py:3`, `search/__init__.py:5`, `convergence/__init__.py:4`, `convergence/converge.py:5`(`find_front(sctx, starts)` 예시) -- 같은 변경에서 서명 문구를 고친다), 새 호출 `PlanSession.run_variant` 하나, test·하네스 호출(2026-10-21 grep 14파일: `tests/search/` 9파일 -- `conftest.py`·`test_archive.py`·`test_cell_floor.py`·`test_find_front.py`·`test_front_entries.py`·`test_front_query.py`·`test_kernel.py`·`test_search_context.py`·`test_start_points.py`, `tests/integration/` 4파일 -- `nfr4_run_dump.py`·`test_g10_no_recompute_9circuits.py`·`test_no_s0_files_written.py`·`test_rerun_s3_independence.py`, `tests/core/test_blas_env.py`)은 같은 변경에서 `variant_key=None`을 넘긴다. 요구 없는 실행은 None이라 지금 식 그대로(완료 조건 1). 키가 다르면 같은 S3 루트에서도 runs 줄이 겹치지 않는다. 반복 번호는 키에 없으므로 `run_id`에 들어가지 않는다.

### 6.6 정지 처리

예외를 삼키지 않는다. 단계 A·B는 지금처럼 보고서와 exit code(`E/pipeline/stage_a.py:97-101`, `E/pipeline/stage_b.py:128-131, :146-150`). 계획 함수 거부는 이름으로 `SchemaRejectedError`만 받아 `PlanResult.rejected`(`exc.record.to_json()`)와 exit code에 싣는다. 넓은 `except` 없음.

---

## 7. 예산

### 7.1 변형별 E_total(XS-12)

* E_total,v = E_B + N_T + R_v, R_v = 2 × `len(sctx_v.domain.variables)`(X-17, 40 §2.4.9). E_B는 `SearchSettings.eval_budget`(모든 변형 같은 선언값). 선언이 없으면 변형마다 유도(card C `search_ceiling`).
* 실행 계획 전체 상한 = Σ_v E_total,v. 벽시계 정지는 변형마다(`E/search/find_front.py:67`). 추가 변형도 자기 E_total,v를 받는다(계획 N3.7).
* 반복 수 상한 = OTP D-19 실행 설정 선언값(T-35, 기본값 없음). 선언이 없으면 추가가 없다. 이 값은 구동기가 읽고 세션은 받지 않는다(세션은 추가 요청마다 §13.3 검사만 한다).

### 7.2 DS-U9 조사 결과(열림 유지)

계획 순서·구성과 무관하면서 '계획 안 = 단독' 비트 동일을 주는 시간 유도 규칙은 없다. 비트 동일의 전제가 'E_B 선언'이기 때문이다(40 §2.4.13 1차 검사 전제 (가)). 후보 넷(자기 첫 n_θ + 1 평가, 첫 변형 유도값 공유, 블록 적중 시간 환산, 사전 단독 시험 평가)은 모두 조건 2를 줄 수 없다(history H2). 결정 S-6대로 유도 실행은 조건 2·NFR-S5·조건 9 셋째 항목에서 빼고, `run_plan.notes`에 `{"verdict": "budget_derived", "meaning": "derived_budget_may_differ_from_standalone"}`를 싣는다.

### 7.3 색인 상한과 B_S0(PD-7)

* 상한 = Σ_블록 분할 수 × (Σ_v E_total,v + B_S0). 변형 하나·S0 한 벌이면 40 식 그대로다.
* B_S0 = 변형 수 + (국면 2 계획에 원본 topology 변형이 없으면 구조 비교용 원본 S0 한 벌). 실행 전에 계획만으로 계산되고 '서로 다른 S0 입력 수'보다 크거나 같다(안전 쪽, PD-7).
* **card C `S3Index` 인터페이스**(OS-5): 생성자에 필수 인자 `s0_sets`(B_S0)를 더하고(생성 자리는 `open_run` 하나라 `open_run(s0_sets=…)` 서명 변경으로 모인다 -- 40 §2.4.5. 순환은 §18.4 PS-6), 변형마다 정해진 E_total,v를 등록하는 메서드 `add_eval_ceiling(e_total)`을 더한다. 등록 시 상한 검사(40 §2.4.5 fail-closed (5))는 그 합을 쓴다. card C test를 같은 변경에서 고치고 기본값 인자로 피하지 않는다.
* **OS-L**: 변형이 추가되면 세션이 `S3Index.grow(s0_sets=1)`로 B_S0를 하나 늘리고 그 변형의 E_total,v를 `add_eval_ceiling`으로 더한다('늘리는' API, 계획 N3.7). 줄이는 API는 없다.
* 결과 JSON: `run_plan.shared.block_index_entries`·`block_index_bound`·`b_s0`. 각 변형 runs 줄 `perf.block_index_bound`에도 그때의 계획 전체 값을 싣는다.

---

## 8. 결과 JSON 칸(`<회로>.run_plan.json`, 최상위 키 `run_plan`)

| 칸 | 내용 | card |
|---|---|---|
| `strategy`, `phase` | 계획 값. 진단 표지는 칸을 두지 않고 변형마다 `stage_b_report`(단계 B 보고서 경로)가 가리키는 보고서의 `diagnostic` 칸(`stage_b.py:129`)을 참조한다(§6.4). 같은 토폴로지 변형은 같은 파일을 가리킨다(§6.3 '같은 내용' 조건) | OS-2 |
| `stage_b_unplanned_report` | 단계 A가 spec 없이 멈춰 계획이 없을 때 단계 B `skipped` 보고서 경로(그 보고서 `diagnostic`은 늘 False, `stage_b.py:142`), 그 밖 null(검증 N4) | OS-2 |
| `requirement` | `{ref: "human.offset_requirement", source_fp, strategy, view}` 또는 null. **spec 선언 값(`offset_in_max_v`·`coverage_multiple`·`judgment_temperature_range_c`)은 싣지 않고 참조만 싣는다**(아래 '출력 기록 규칙') | OS-2 |
| `rejected` | 계획 함수 거부 사유(`exc.record.to_json()`) 또는 null | OS-2 |
| `variants[]` | `{index, label, iteration, cause_fp, topology_fp, variant_fp, derived: [{name, sigma_metric, sys_metric, k_ref, threshold: {target, margin_ref}, source_fp}], budget: {eval_budget, eval_budget_source, e_total, gate_reserve}, stage_a_status, stage_b_status, stage_b_report, run_id, s3_dir, stop, front_points}` | OS-2(OS-5·OS-L에서 여러 개) |
| `variants[].output_reference` | V_id* 출력 기준(정의 자리 = gain-budget DEC-23 하나, O-53 B3): 포트 뷰 관측이 차동이면 `"differential"`(V(p) − V(n) = 0 기본), 단일이면 `{net, ref}` -- `ref`는 spec 기준 선언의 참조 경로(L4와 같은 출처). **값은 싣지 않는다**(v0.2.x의 `value_v` 사본 칸 삭제, graph 단일 정본 규칙 4 -- 변환기는 참조로 spec 값을 읽는다). DEC-23의 기준 종류 셋(값·넷·입력 추종) 가운데 이 칸이 덮는 것은 지금 L4의 '값' 종류뿐이다(§18.4 PS-4). 엔진 결과 → 오라클 입력 변환(U16 변환기)이 오라클 입력으로 옮긴다(§12) | OS-V |
| `variants[].front_points[]` | `{point_id, power_w, area_m2, derived_rows: [{name, c, active, value_v, limit_v}], front_judgment}`. `derived_rows` = 그 점 평가 스냅샷의 `graph/metrics: constraint_rows` 커널 행 값(§3.1 '행 값', v = k·σ_in, L = 문턱 항목 값)을 **읽은 것**. `front_judgment` = 그 점의 DEC-74 front 판정 출력(§3.7)의 참조(그 자리의 필드·기록 이름은 gain-budget design -- §18.4 PS-1이 닫히기 전에는 칸을 만들지 않는다). 판정 문턱이 조인 문턱이면 `threshold_margin_ref`(Δ_T 기록 참조)를 함께 싣는다 -- 최종 합격 판정 문턱은 spec 값이다(OT §20.1 '합격'). v0.2.x의 `margin_v`(= limit_v − value_v를 결과 JSON을 쓸 때 계산)는 graph 밖 둘째 계산이라 지웠다(c가 같은 여유를 이미 담는다) | OS-2 |
| `variants[].memory` | OS-L: 그 변형 끝의 색인 항목 수, 프로세스 최대 메모리(XS-19) | OS-L |
| `shared` | `{block_index_entries, block_index_bound, b_s0, s1v_computes, s1v_inputs, kernel_calls_total}` | OS-2(OS-5 다변형 의미) |
| `notes[]` | matching 변형이 있으면 `{"verdict": "final_acceptance_is_oracle_range_judgment"}`(계획 N3.11 '합격 표기', T-29). `budget_derived`(§7.2). compare 국면 1이면 `{"verdict": "not_a_recommendation"}`와 R1·R2 한계 문구. 합성 판정 행 검증 출처 `{"verdict": "verified_by", "rows": [["req:offset_matching", 종류, 항 metric별 종류], [<front 판정 행 id>, 종류, 항 metric별 종류]]}` -- 커널 행과 front 판정 행 둘(§12, 검증 M7). front 판정 행 id는 DEC-74 자리의 기록 이름을 따른다(DE-1 design 뒤 확정, §3.7) | OS-2 / OS-5 / OS-V |

* 권고·판정 문장은 싣지 않는다(FR-S7).
* **출력 기록 규칙(검증 M6, 하나의 규칙)**: 결과 JSON은 출력 전용 기록이다(엔진이 다시 읽지 않는다, S-3). (1) **spec 선언 값**은 싣지 않고 참조(`ref`·`target`·`k_ref`·`source_fp`)만 싣는다 -- 계획 N3.3 머리 '값은 요구 선언을 참조하고 숫자를 복사하지 않는다(NFR-S2)'. 출력 전용 기록에 값 + 참조를 함께 허용하는 계획 규칙은 없다. 그래서 `requirement`의 값 칸, `derived[].k`, `derived[].threshold.value_v`, `output_reference.value_v`를 싣지 않는다. 조인 문턱(처음 변형이 아닌 문턱)은 `threshold.target` + `margin_ref`(Δ_T 기록 참조)로 재구성된다. (2) **엔진 계산값**(graph 필드)은 그 필드를 읽은 값을 싣는다: `derived_rows`의 c·active·v·L은 `constraint_rows` 행 값이다(§3.1 '행 값', 값의 정본은 graph 필드 하나이고 JSON은 그 필드의 출력이다). (3) 계수·지문·경로·상태는 그 출처 객체의 출력이다. 비교 도구(§9)는 값이 필요하면 참조로 spec을 읽는다.

---

## 9. 비교 도구(OS-3)

* **위치(DO-7, OB-14)**: `skills/analog-gmid-design/tools/offset_compare/`(`compare.py` 진입점 `compare_offset_results(result_paths) -> ComparisonTable` + CLI `main(argv)`, `README.md`, `tests/test_compare.py`). 엔진 import 0(AST test). 엔진은 이 도구 출력을 입력으로 받지 않는다.
* **입력**: `<회로>.run_plan.json` 둘 이상(국면 1의 matching 변형, 국면 2의 trim 변형).
* **칸**: 출처(경로, `run_id`, `code_fp`, `variant_fp`, label, iteration), 공통 판정 선언(1/f metric·op·값, `area_search_m2` 상한), 요구 값(`offset_in_max_v`, k, 판정 온도 범위 -- 결과 JSON의 `requirement.ref`로 spec에서 읽는다, §8 출력 기록 규칙), front 점별 (전력, 면적), offset 한계 대비 여유(matching = 결과 JSON의 `limit_v`·`value_v`와 front 판정 참조를 나란히 놓는다, trim = `offset_in_max_v` − `residual_bound_v` -- 도구는 엔진 밖 표시이고 엔진 입력 경로가 없다. 여유 한 줄을 도구가 빼서 낼지는 §18.4 PS-5), 유도 제약 판정(c, active), 공통 판정 행 c.
* **불일치 표시**: `code_fp`·공통 판정 선언·요구 값이 다르면 표 머리에 그 사실을 쓴다.
* **금지**: 판정·권고 문장, 가중치, 문턱.

---

## 10. DS-1 평가 캐시 처리 -- 결정됨(S-14: (다))

**결정(사용자 2026-10-16 "모두 권고대로", 결정 기록 S-14)**: DS-1 = **(다) 키 분리**. 평가 키에 변형 제약 집합 지문(문턱 값 포함, §3.3 `constraint_set_fp`)을 넣고, 실제 계산 공유는 card B 블록 결과 색인이 맡는다. 구현 card는 OS-5(compare)·OS-L(보정 루프)이다. (가)·(나)는 기각 대안이고 기록만 남긴다(§10.1·§10.2). 공통 전제(**이 design의 전제에서는** -- 유도 제약이 S1v 씨앗·extras 밖이고(OB-4) 요구가 있으면 사용자 판정 제약이 변형 사이에 같다(L2), 이것이 PD-3 근거다): 같은 topology 변형끼리 spec 판정 제약·S1v·S0 입력이 같고, 다른 것은 유도 제약(합성 행·그 metric 요청)과 OS-L의 문턱(Δ_T)뿐이다.

### 10.1 (가) 평가 키 부분만 변형별 -- 기각 대안(기록)

`S3Index`를 블록 결과 부분과 평가 키 부분으로 나누고 평가 키 부분을 변형별로 두는 안. 같은 topology 변형이 같은 θ를 밟으면(문턱 값이 같은 OS-L 변형 포함) 같은 평가 키를 변형마다 다시 계산해 완료 조건 3과 모순이고 DS-U7과 충돌했다(옛 OD-2). S-14로 기각.

### 10.2 (나) 평가 분리 -- 기각 대안(기록)

커널 요청을 계획 안 합집합으로 계산하고 판정 행(`req:`)을 변형별 단계로 떼어 내는 안. 완료 조건 3은 지키지만 kernel·`EvalResult` 구조를 나누는 범위가 컸다. S-14로 기각.

### 10.3 (다) 키 분리 -- 채택(S-14)

* 바뀌는 곳: `EvalKey`에 칸 `constraint_set_fp`(§3.3 -- 문턱 항목의 `value_v` 지문 포함, `margin_ref`·`cause_fp` 제외)를 더하거나 `context_fp` 지문에 넣는다(`E/search/eval_key.py`, `E/search/search_context.py:206`). **OS-L 문턱 지문 = 문턱 값(`ThresholdItem.value_v`)의 지문**이다(검증 v0.2.2 N-2). Δ_T 기록 지문(`cause_fp`)을 넣으면 기록은 다르고 문턱 값이 같은 두 변형이 같은 평가 입력을 따로 계산하게 되어 완료 조건 3(같은 입력 재계산 0)을 깬다. `S3Index` 하나를 공유한다. 요구 없는 실행은 칸을 넣지 않아 완료 조건 1을 지킨다.
* 완료 조건 3: 형식상 지킨다. 문턱 값이 다른 변형끼리는 같은 θ의 커널 평가가 남고, 크기 결정 블록은 색인 적중, offset metric 블록은 요청이 같아도(OS-L) 행이 달라 커널은 돈다(XS-8). 문턱 값이 같으면 평가 항목을 공유한다.
* 놓기: 평가 키가 문턱 값으로 묶이므로, 원인이 다르고 문턱 값이 같은 변형이 나중에 올 수 있다. 그래서 (다)에서는 **평가 키 항목을 놓지 않는다**(놓으면 같은 입력 재계산이 생길 수 있다). 블록 결과 부분도 놓지 않는다.

* 실제 계산 공유: 변형 사이에 같은 θ의 커널 평가 자체는 변형마다 남지만(평가 키가 다르므로), 그 안의 블록 계산은 card B 블록 결과 색인이 입력 버전으로 공유한다(크기 결정 블록 적중). 이것이 S-14 '실제 계산 공유는 블록 결과 색인' 문언이고, XS-8이 허용한 '같은 θ 커널 평가는 변형마다 남음' 편차다.
* 구현 card: OS-5(compare 국면 1 다변형), OS-L(반복 변형). 바뀌는 곳은 search 층 `eval_key`·`search_context`의 키 구성 한 곳이다(XS-5 범위).

**놓기 규칙**(계획 N9): (다)에서는 평가 키 항목과 블록 결과 부분을 놓지 않는다(위 '놓기'). θ 무관 블록(단계 A·S0·커널 안 크기 결정 블록)도 놓지 않는다. 메모리 한도 위험이 실측되면 사용자에게 올린다(조용히 비우지 않음). 반복마다 메모리 보고(XS-19)가 그 실측이다.

---

## 11. 국면 규칙·승인 기록(PD-2 배정)

* 국면은 승인 기록 유무로만 정한다(DO-2). 위치 = topology 파일과 같은 폴더 `<circuit>.trim.json`(OT §8.1). 진입 인자로 국면을 고르지 않는다.
* 승인 파일이 있는데 국면 1을 다시 돌려면 사용자가 파일을 치운다(DO-9). 엔진은 승인 파일을 고치지 않는다.
* 낡은 승인은 국면 1로 돌아가지 않고 `trim_approval_stale`로 정지한다.

| 일 | card | 내용 |
|---|---|---|
| 승인 기록 없음 → 국면 1 | TR-2(+OS-5) | `build_run_plan` trim 국면 1 행, `run_trim_candidates`를 세션의 trim 국면 1 변형 실행 뒤에 부른다(OT §10.3a 방향 그대로) |
| 승인 파일 있음 → 국면 2 미구현 | TR-2 | 세션 열기가 정해진 위치에 파일이 있는지만 본다(읽지 않음). 있으면 `approvals` = `ApprovalFilePresent(path)` → `trim_phase2_not_open` |
| 승인 기록 로더·결속·낡은 승인 정지·국면 2 분기 | TR-3 | `load_trim_approval` → `approvals` = `TrimApprovals`, `bind_trim`(OT §8.3 1~5), 국면 2 변형 단계 A(+ 원본 비교 벌). `ApprovalFilePresent`는 TR-3에서 지운다 |
| 구조 동일 검사 | TR-4 | OT §3.2 |
| 국면 2 탐색 게이트 | TR-5b | TR-5b 전에는 국면 2 변형이 단계 A 뒤 `trim_phase2_search_not_open`으로 멈춘다(OD-3 = XS-15 수용). TR-5b가 지운다 |
| compare 다변형·공유·정체 칸·Σ 상한·공통 판정 | OS-5 | DS-1 = (다)(S-14)로 연다(§10.3) |
| 최종 비교 | OS-3 | TR-6 뒤 |

---

## 12. OS-V: matching 합성 판정의 오라클 측정(V-1, S-11)

**범위**: matching 판정 두 자리(커널 행 k·σ_in ≤ 문턱, front 판정 k·σ_in + \|V_id*\| ≤ 문턱 -- O-53 A2)의 검증 출처를 붙인다. **합성 판정 행의 결속만**이다(계획 v0.7 N7.2 OS-V 행, 감사 D3). `offset_sys_mv`(V_id*)의 `verified_by` = `spice_oracle` + OP-5 measure 연결은 gain-budget card VB-1(N6.18)이 하고, OS-V는 VB-1을 선행으로 인용하며 그 행을 다시 만들지 않는다(v0.2.x의 'OS-V가 `offset_sys_mv` 행을 바꾼다'는 둘째 생산자라 지웠다). **판정 조건 하나**(LUT 측정 조건 `temp_c`·`corner` = 엔진 합격 조건)의 측정만이다. 판정 온도 범위의 온도 점으로 넓히는 몫은 offset-trim TR-TL이 맡는다(OTP TR-TL 행 '소유 경계').

**경계(계획 v0.6.2 N7.2 OS-V 행)**: OS-V는 **새로 만들지 않고 재사용한다**. 오라클 코어(`O/core/`) 파일을 만들지 않고, oracle-portability와 파일이 겹치지 않는다.

| 대상 | 재사용하는 것 | OS-V가 하는 일 |
|---|---|---|
| σ_in 오라클 값 | 기존 measure `offset_in_sigma_mv`(네이티브 MC, O-1). 크기 일관 확인은 TR-7 §17-1(O-1 (2)) | 대조에 쓴다 |
| V_id* 오라클 값 | 계획 v0.7.2 N7.2 OS-V 행(476행) 문언 그대로: "oracle-portability OP-5의 계통 offset `.dc` 측정(부호 있는 V_id* 칸. 이 측정을 온도 조건에서 돌린 것 하나가 PC-10이다 -- O-53 B3. 공칭 MC 표본 offset은 V_id* 출처가 아니다)". offset-trim 계획 G-15(674행)와 같은 문언이다. 정의 = gain-budget DEC-23. 판정 조건 하나에서는 T = LUT `temp_c` | 대조에 쓴다 |
| `offset_sys_mv` `verified_by` 행 | gain-budget VB-1(N6.18) | **만들지 않는다**(선행 인용) |
| 엔진 | -- | 합성 판정 행의 측정 결속 하나: 검증 출처는 항 metric 종류에서 정한다 -- 커널 행(항 σ_in 하나)은 `offset_in_sigma_mv`의 종류를 그대로, front 판정(항 σ_in·V_id*)은 두 항이 모두 `spice_oracle`이면 `spice_oracle`, 아니면 `spice_unverifiable`(`find_front` notes `verified_by` 기록에 `rows`를 더하는 자리, `E/search/find_front.py:83-85`). 엔진은 오라클을 import하지 않는다 |

* **OS-V 전까지**: 합성 판정 행의 결속이 없으므로 두 자리 모두 `spice_unverifiable`로 결과 notes에 실행 전부터 나간다(DEC-90 (3), OT §10.6 선례; 계획 N7.2 OS-V 행 '이 card 전까지 합성 판정 metric은 `spice_unverifiable` 목록').
* **모델 오차**: 기록 키 이름은 `verified_by`의 규칙 `model_error_` + metric 이름(`E/metrics/verified_by.py:22, :59`)으로 `model_error_offset_in_sigma_mv`·`model_error_offset_sys_mv`다(이름은 확인됨). 그 값을 오라클 대조에서 만들어 `derived` 모델 오차 매핑에 넣는 주체·경로는 **확인 대기**(OP-5·OS-V 구현 때 대조 기록 형식이 정해진 뒤). 커널 행 분해능(§3.1)은 `model_error_offset_in_sigma_mv`를 바닥으로 쓴다. `model_error_offset_sys_mv`의 기록·측정 주체는 gain-budget ME-1(N6.19, 모델 오차 측정 주체 하나)이다.
* **V_id* 대조 규칙(OB-36, v0.3.0 열림)**: v0.2.x는 엔진 `offset_sys_mv`가 크기 근사(E-S5)라서 절댓값끼리 대조했다. 정본 V_id*는 부호 있는 한 칸이고(DEC-23, O-50 G1) 엔진 값을 부호 있는 값으로 바꾸는 일은 DE-1 (c)다. 대조(부호 포함 여부)의 정의는 gain-budget ME-1·VB-1 소관이고 이 계획에는 문언이 없다(§18.4 PS-2). 이 판은 v0.2.x의 절댓값 대조를 규칙으로 두지 않는다. mV 환산은 core 단위 어휘 `MV_PER_V`(`E/core/units.py:23`)를 쓴다. **정의 경계 불일치**(계획 v0.7.3 N7.2 OS-V 행, O-63 (2)): 엔진과 오라클 중 한쪽만 'A_dc 정의 불능 갈래'가 발동한 점은 값 오차가 아니라 '정의 경계 불일치'로 검증자 변화표에 적는다(범주 이름·정의 = oracle-portability N3.9 `offset_sys_mv` 행 (vi), 인용만).
* **오라클 입력의 출력 기준(검증 v0.2.2 N-7)**: 오라클이 V_id*를 재려면 출력 기준(정의 자리 = DEC-23 하나)이 입력으로 필요하다(OT §20.1 '오라클은 기준을 결과 JSON에서 읽는다'). 이 design은 `run_plan.json` 변형마다 칸 `output_reference`를 싣고(§8: 포트 뷰 관측에서 차동이면 `differential`, 단일이면 그 넷과 spec 기준 선언의 참조 -- 값 사본 없음, L4와 같은 출처), **엔진 결과 → 오라클 입력 변환(U16 변환기)이 그 칸을 오라클 입력으로 옮긴다**. 엔진은 오라클 입력 파일을 쓰지 않는다.
* **선행·착수 조건**: OS-2, gain-budget VB-1(`offset_sys_mv` measure 연결), 오라클 선행 oracle-portability OP-3·gain-budget EO-1·oracle-portability OP-5(계통 offset `.dc`, 감사 D4 -- 계획 N7.2 OS-V 행), 그리고 **오라클 입력 생산자**: 엔진 결과(`output_reference` 포함) → 오라클 입력 변환은 U16 변환기가 정본이다. U16 전에 OS-V를 병합하면 그동안의 생산자는 offset-trim 구동기(OT §20.7 `tools/temperature_loop/`, 결과 JSON을 읽어 오라클 입력을 만든다)이고, U16이 병합되면 같은 변환을 U16 변환기로 옮기고 구동기 쪽 사본을 지운다(변환 두 벌 금지). OS-V는 TR-TL의 선행이다. 판정 온도 범위의 온도 점으로 넓히는 몫은 TR-TL이다.

---

## 13. OS-L: 실행 중 변형 추가(T-35, XS-16~XS-19, TR-TL과 같은 변경)

### 13.1 서명(D-25 결정 T-36으로 닫음)

```python
PlanSession.add_variant(base_index: int, threshold_item: ThresholdItem) -> PlanVariant
```

* `threshold_item` = 구동기가 출처 무결성 대조(D-25 (c)+(c-2), OT §20.4)를 통과시킨 Δ_T 기록으로 OT §20.3 `tightened_threshold(spec_threshold_ref, delta_record)`를 **추가 한 번에 한 번** 불러 만든 조인 문턱 항목(§3.4 `ThresholdItem`, `margin_ref` 있음)이다. **첫 인자 `spec_threshold_ref` = base 변형의 처음 문턱 항목**(같은 target, `margin_ref` None -- 세션 `plan`의 처음 목록 변형에서 읽는다, 검증 v0.2.2 N-4). 앞 반복의 조인 문턱을 넣지 않는다(Δ_T는 누적하지 않는다, OT §20.2 '갱신'). TR-0T에 같은 문장을 두도록 알림 항목으로 올린다. Δ_T 기록 형식(`TemperatureMargin`, 키 `temp_margin_<metric>_v`)과 합성 함수는 offset-trim 소유이고, 항목 형식은 이 design 소유다(OT §20.3 '형식은 offset-strategy의 `derived` 항목 형식'과 대조 일치, `wt/trim-design-r1` `5c93cb6`).
* 결과 문턱 ≤ 0(`tightened_threshold_nonpositive`)은 `tightened_threshold`가 던지고 **구동기가 추가 전에 거부**한다(OT §20.3). 엔진이 `value_v` ≤ 0인 항목을 받으면 호출 계약 위반 `ValueError`다(사유 코드 아님 -- 구동기 경로에서는 생기지 않는다).
* 결과: 새 `PlanVariant` = base 변형과 같은 topology·같은 `trim_decl`이고, `derived`에서 `threshold_item.target`과 같은 target의 문턱 자리(matching = `OffsetBound.threshold`, trim 잔여 = 최상위 `ThresholdItem`)를 그 항목으로 바꾼 것. `cause_fp` = `threshold_item.margin_ref`의 sha256, `iteration` = 지금 최대 + 1(표시 칸). 세션의 `plan`이 새 값으로 바뀐다. 실행은 `run_variant(새 index)`로 따로 부른다.
* 엔진은 대조하지 않고 Δ_T 기록·오라클 결과 파일을 읽지 않는다(XS-18 = X-23 수용). 부르는 주체는 엔진 밖 구동기(OT §20.7 `tools/temperature_loop/`)뿐이다(엔진 안 search·kernel·블록은 부르지 않는다 -- 호출 grep).

### 13.2 문턱 경로(Δ_T가 들어가는 길은 하나)

구동기 → `tightened_threshold`(한 번) → `add_variant(base_index, threshold_item)` → 그 변형 `derived`의 문턱 자리 → 커널 행(§3.1)·front 판정(§3.7, 같은 항목)·`trim_constraint_rows`가 **항목 값을 읽기만** 한다(평가마다 합성하지 않음). 출발 구간 `start_intervals`(§3.2)도 같은 항목을 extras 투영으로 읽는다(계획 N3.3·LR6, 문턱 의존 블록). spec 측정 선언 절·오라클 결과 파일 읽기·그 밖 S0 블록으로는 들어가지 않는다.

### 13.3 추가 허용 범위(fail-closed, 사유 코드 `run_plan_variant_add_rejected`, detail `reason`)

| reason | 상황 |
|---|---|
| `session_closed` | 닫힌 세션 |
| `session_rejected` | 계획 함수가 거부한 세션 |
| `base_unknown` | base index가 계획에 없음 |
| `no_threshold_slot` | base 변형 `derived`에 `threshold_item.target`과 같은 target의 문턱 자리가 없음 |
| `threshold_not_tightened` | `threshold_item.margin_ref`가 None(조인 문턱이 아님 -- 처음 문턱과 같은 항목을 추가하려는 것) |
| `threshold_unit` | `target` 키 접미가 `_v`가 아님(§3.4) |
| `iteration_cap` | 추가된 변형 수 a(세션 열기 때 0)가 a ≥ 반복 상한이면 거부(§13.4의 한 정의), 상한 None(선언 없음)이면 늘 거부 |
| `duplicate` | 같은 중복 판정 키(같은 원인 지문 포함, §3.3)가 이미 있음 |

topology·사용자 판정 제약·요구·`strategy`·국면·문턱 밖 유도 제약 형태는 서명상 바꿀 수 없다(입력이 문턱 항목 하나이고 나머지는 base 값을 그대로 쓴다). 그래서 계획 N3.12의 '다른 topology·판정 제약 변경' 거부는 서명으로 보장되고, test는 그런 추가를 시도할 입력 자리가 없음을 확인한다.

### 13.4 예산·메모리

* **반복 상한 이중 확인(OB-31, 계획 v0.6.2 N3.12 '예산'의 design 몫 -- 채택)**: OS-L이 `open_plan_session`에 필수 키워드 `iteration_cap`(int | None, 기본값 없음)을 더한다. 값은 구동기가 실행 설정(OT §20.7 `iteration_cap`, D-19)에서 읽은 그 값을 넘긴다(정본은 실행 설정 하나, 세션은 받은 값을 칸으로만 든다). `run_plan`은 None을 넘긴다(추가 없음). **세는 단위(검증 v0.2.2 N-3, 한 정의)**: 반복 수 = 그 세션에서 추가된 변형 수 a(처음 목록은 세지 않음, 세션 열기 때 a = 0, 추가가 받아들여질 때마다 +1 = 그 변형의 `iteration`). 추가 요청 때 a ≥ `iteration_cap`이면 거부한다. 그래서 받아들여지는 추가는 최대 `iteration_cap`개다. OT TR-0T §20.6 `iteration_cap` 정지('반복 수 = 반복 상한')와 §20.7 순서 1(세션 열기)에 '반복 수 = 추가된 변형 수(처음 0)'와 '세션 열기에 `iteration_cap`을 넘긴다'를 같은 정의로 적도록 알림 항목으로 올린다. 구동기 쪽 검사와 이중이고, 엔진 혼자서도 상한 밖 색인 증가를 막는다.
* 추가 때 E_total,v·B_S0·색인 상한이 늘어난다(§7.3).
* 결과 JSON `variants[].memory`에 그 변형 끝의 색인 항목 수와 프로세스 최대 메모리를 싣는다(XS-19). OS-L 병합 전에 반복당 색인 크기(바이트)를 잰다.
* 놓기는 §10의 DS-1 선택지별 조건을 따른다.

---

## 14. 파일 분할

### 14.1 새 파일(규칙 A: 파일당 진입점 하나)

| 파일 | 진입점 | 층 | card |
|---|---|---|---|
| `E/authoring/spec_offset_requirement.py` | `offset_requirement_declaration(raw, topology, feedback)` | authoring | OS-2 |
| `E/authoring/spec_offset_conflicts.py` | `offset_requirement_conflicts(requirement, constraints)` | authoring | OS-2 |
| `E/pipeline/run_plan_values.py` | (값 모듈: `PlanVariant`·`RunPlan`·`VariantResult`·`PlanResult`) | pipeline | OS-2 |
| `E/pipeline/run_plan_build.py` | `build_run_plan(spec, topology)` | pipeline | OS-2 |
| `E/pipeline/plan_session.py` | `open_plan_session(...)`(클래스 `PlanSession`은 반환 형식) | pipeline | OS-2(`add_variant`는 OS-L) |
| `E/pipeline/run_plan.py` | `run_plan(...)` | pipeline | OS-2 |
| `tools/offset_compare/compare.py` | `compare_offset_results(result_paths)` | 도구 | OS-3 |
| `assets/fixture/offset_strategy/current_reuse_telescopic_ota.topology.json`·`.sizing_spec.json` | (fixture, §16.2) | 자산 | OS-2 |

값 형식 자리: `OffsetRequirement`·`ThresholdItem` → `E/authoring/spec_model.py`(OT §20.3 `tightened_threshold`가 authoring 층이라 같은 층에 둔다), `OffsetBound` → `E/search/search_values.py`.

### 14.2 고치는 파일

| 파일 | card | 범위 |
|---|---|---|
| `E/authoring/spec_schema.py`, `spec_load.py`(섹션 호출, L2 자리 :142 뒤), `spec_model.py`(`OffsetRequirement`, 칸, `OPTIONAL_SECTION_GROUPS`, `_section_fps`), `spec_sources.py`, `__init__.py` | OS-2 | 부분 |
| `E/search/search_values.py`(`OffsetBound` 값 형식. `constraint_rows` 행 값 형식의 정본은 U17 ②(40 §2.4.8)이고, OS-2는 **U17 ②가 정한 행 값 형식에 (v, L)을 더한다** -- §17.2 알림), `ss_constraints.py`(bounds, :63 일찍 끝나는 분기를 `not declared and not bounds`로), `kernel.py`(:136 요청, :155 bounds), `search_context.py`(`derived` 키워드·`offset_bounds`·mismatch 검사·`offset_start_targets`), `start_intervals.py`, `iv_context.py`, `iv_matching_l.py`, `find_front.py`(:83-85 rows, :131 `run_id`) | OS-2 | 부분(PD-4 범위: 계산 규칙 두 곳 + 전달 다섯 + 값 형식 하나) |
| **PD-4 목록 밖에서 바뀌는 파일(계획 549행 '그 자리의 파일이 위 목록 밖이면 design이 바뀌는 파일을 적어 보고한다')**: (1) DEC-74 front 판정 자리의 파일 -- front 판정 소비자를 붙이는 곳(파일 이름은 DE-1 design 뒤 확정, §3.7) (2) `E/metrics/ss_evaluate.py` docstring(문구만) (3) OS-5·OS-L 몫: `E/search/open_run.py`(`s0_sets` 필수 인자), `E/search/s3_index.py`, `E/search/eval_key.py`(DS-1 (다)), `E/search/kernel.py` `_record` (4) 엔진 밖·pipeline: `E/pipeline/*`(§14.1), `E/tests/structure/structure_checks.py` `check_m`(M-a 허용 목록·M-c 예외, §6.1) | 각 card | 보고(계획 549) |
| `E/pipeline/stage_a.py`(`donors`·`counters` 필수, `StageAResult.topology`), `pipeline/__init__.py` | OS-2 | 부분 |
| `E/metrics/ss_evaluate.py` docstring(`MetricRequest`도 받음) | OS-2 | 문구 |
| `E/tests/integration/nfr4_run_dump.py`, `test_no_s0_files_written.py`, `test_rerun_s3_independence.py` | OS-2 | 사슬을 세션 경로로(실행 수명 값을 읽는 하네스 = `open_plan_session` → `run_variant` → 읽기 → `close`, 읽지 않으면 `run_plan` -- §6.4, 계획 v0.7.2 W-1). 옛 수작업 사슬과 그 `open_run` 호출 삭제 |
| `E/search/s3_index.py`(`s0_sets` 필수 인자, `add_eval_ceiling`) + card C test | OS-5 | 부분 |
| `E/search/kernel.py` `_record`, `find_front.py` runs 줄(`variant` 칸) | OS-5 | 부분 |
| DS-1 선택지 파일(§10) | OS-5 | 선택에 따름 |
| `E/search/s3_index.py`(`grow`), `pipeline/plan_session.py`(`add_variant`), `plan_session.py`(`iteration_cap` 키워드) | OS-L | 부분. `ThresholdItem`·`OffsetBound.threshold`는 OS-2부터 있고(처음 문턱), OS-L은 커널·`ss_constraint_rows`를 바꾸지 않는다(합성 없음) |
| `find_front.py`(notes rows -- 커널 행·front 판정의 결속) | OS-V | 부분. `E/metrics/verified_by.py`의 `offset_sys_mv` 행은 gain-budget VB-1 몫이라 고치지 않는다. 오라클 파일은 만들지 않는다 |
| CONTRACT(`authoring`·`SPEC_CONTRACT`·`search`·`pipeline`·`metrics`), `_module_map.py`, 함수 레지스트리 §2 | 각 card | 갱신 |

### 14.3 층·모듈 지도·test·레지스트리

* 층 순서 그대로(authoring < … < search < pipeline). 도구·오라클은 엔진 밖.
* test 1:1(규칙 H), 9회로 실행은 `E/tests/integration/`.
* 함수 레지스트리 §2(2026-10-16 확인: 아래 개념 없음): 'offset 요구 → 실행 계획' = `pipeline.build_run_plan`, '엔진 사슬 진입(세션·얇은 진입)' = `pipeline.open_plan_session`·`pipeline.run_plan`, 'matching 합성 offset 판정 행' = `search.ss_constraint_rows`(bounds), 'offset 결과 나란히 보기' = `tools/offset_compare`. 대체되는 엔진 함수는 없고(사슬 함수가 없었다), 대체되는 것은 하네스·test의 수작업 사슬이다.

---

## 15. 배선표

| 새 함수·칸 | 호출 경로 | 대체하는 옛 경로 |
|---|---|---|
| `offset_requirement_declaration`·`offset_requirement_conflicts` | `load_sizing_spec` | -- |
| `build_run_plan` | `open_plan_session` | -- |
| `open_plan_session`·`PlanSession.run_variant`·`close` | `run_plan` | -- |
| `run_plan`·세션 공개 API(`open_plan_session`·`run_variant`·`stage_a`·`search_context`·`block_index`·`close`) | 엔진 사슬 진입점 정본(W-1). 하네스·test 전체 사슬 셋(§6.4)이 같은 변경에서 세션 경로로 부른다(실행 수명 값을 읽으면 세션 API, 아니면 `run_plan` -- 사슬은 하나). U16 `run_gmid_design_pipeline`은 나중에 `run_plan`을 부른다(계약에 적는다) | 하네스·test의 수작업 사슬 |
| `ss_constraint_rows`의 bounds | `kernel.evaluate` | -- |
| `build_search_context(derived=)`·`offset_bounds`·`offset_start_targets` | `PlanSession.run_variant` | -- |
| `StartView.sigma_targets_v` | `matching_bounds` | `iv_matching_l.py:107, :123`의 mv 목록 |
| `run_stage_a(donors=, counters=)` | `open_plan_session` | card B의 '`run_stage_a`가 두 객체를 만든다'(PD-8, §17.2) |
| `PlanSession.add_variant`, `S3Index.grow` | 엔진 밖 구동기(OTP G-12) -- **TR-TL과 같은 변경**에서 병합 | -- |
| notes rows(합성 판정 행 결속, OS-V) | `find_front` notes | 합성 판정 행 `spice_unverifiable` 고정 표기 |
| front 판정 입력(`offset_bounds`의 matching `OffsetBound`) | gain-budget DEC-74 front 전용 예외 자리(소비자 둘째, §3.7). 단위 9 card가 그 자리를 다시 부를 때 같은 소비자 | -- (자리는 DE-1 (c), 이름은 DE-1 design 뒤 확정 -- §3.7) |
| `compare_offset_results` | 사용자 CLI(OS-3) | -- |

---

## 16. card 범위·완료 조건·test

공통: design 승인 → test(interface card만) → code → 독립 판정. 완료 조건마다 (a) 배선 증거 (b) 상위 N6.3 확인 (c) gap 분석. 기능 완료 조건 번호는 계획 N7.2.

### 16.1 card

| card | 범위 | 선행 | 완료 조건 |
|---|---|---|---|
| **OS-2** | §4 L1~L6·L12, §3.1·§3.2·§3.7(front 판정 소비자), §5(요구 없음·matching, 거부), §6(세션·`run_plan`·노출·진단), §8(OS-2 칸), XS-7·PD-8, §6.5, 하네스 사슬 대체, F-1 fixture | OS-0(이 판, 계획 v0.7 기준) 승인, XRUN-F1 card C, PD-8 (ii) 확인(§17.2 -- card B에서 반영됨, E-S14), **U17 ② 병합(`graph/metrics: constraint_rows` 필드·writer) + 40 §2.4.12 Q8 결정(사용자)**(계획 v0.7.1 N7.1 'OS-2 착수 조건', O-61 P9 -- 과도기 `EvalResult` 값 칸·결과 JSON 재계산 금지). U17 ② 병합은 LA-1·DE-1 (c)(DEC-74 front 자리)를 함의하고 계획 v0.7.3이 DE-1 (c)를 선행 칸에 명시했다(§3.7). **계획 v0.7.3 착수 조건 보강(N7.1)**: (가) PS-1 잔여 -- DEC-74 front 판정 기록의 **이름**(종류 = 출력 기록, gb v6.24 DEC-74·N3.3 (b), O-68 (3))이 DE-1 design·착수 실측으로 정해진 뒤 (나) PS-7 -- U17 ② design(40 §2.4.5)이 S3 색인 평가 키 부분의 열거 API를 정한 뒤 (다) 점검 항목(결정 아님): 세션의 `open_run` 호출이 card C 최종 서명(`S3Index` 필수 상한 인자)을 따르고, 그 인자가 단계 A·B보다 먼저 정해져야 하는 순환(PS-6과 같은 꼴)이 아닌지 착수 전에 확인 -- 순환이면 design·40 §2.4.5 소유자 몫으로 올린다. 완료 판정 선행: gain-budget EO-1(SPICE 다리), oracle-portability OP-5·OS-V(계획 N7.2 OS-2 행) | 1(요구 없는 spec = 순수 리팩터링), 10(matching 요구 spec = 동작 변경, 정본 gain-budget N6.3), 5, 7, 8. **'보류' 규칙**(계획 N7.2 OS-2 행·완료 조건 10, gain-budget N6.3 (i)~(iv)): EO-1·OP-5·OS-V 전에는 SPICE 다리가 '보류'이고, 합성 판정은 판정 소비자가 있으므로 '대상 없음'으로 세지 않는다 -- 그동안 이 card는 미완료이고 병합 여부는 오케스트레이터가 사용자에게 올린다. 더해 fixture 실행에서 봉인된 평가마다 S3 evals 줄에 `req:offset_matching<=` 행(또는 정의된 미측정 사유)이 나온다 -- **front는 요구하지 않는다**(F-1 (a), S-14). front 점이 있으면 `derived_rows`도 확인한다, 색인·`RunCounters`가 세션당 하나, 하네스가 세션 경로(열기 → 변형 실행 → 읽기 → 닫기)로 같은 기록을 만든다(E-S18 항목 전부) |
| **OS-V** | §12 | OS-2, gain-budget VB-1, oracle-portability OP-3·OP-5, gain-budget EO-1 | 커널 행·front 판정의 검증 출처가 항 종류 규칙대로 정해진다(두 항 `spice_oracle`이면 front 판정도 `spice_oracle`), VB-1 행을 다시 만들지 않음(grep). **변경 종류 = 동작 변경, VB-1 완료 조건과 같은 꼴**(정의 이름 대조 test, 검증자 변화표, 결정성 -- 계획 N7.2 OS-V 행, O-34 (1)), 오라클 코어 측정 정의가 방언·PDK 이름 0(OPP 완료 조건 1의 검사 대상), 엔진 import 0 |
| **OS-5** | §3.3 S3 칸, §7, §10 DS-1 구현, §11 TR-2 몫, compare 국면 1·L11, card C 인터페이스 | OS-2, TR-2(U16 뒤), DS-1 결정 | 2, 3, 4 |
| **TR-3·TR-5b 몫** | §11 | OT 선행 그대로 | TR-3: 낡은 승인 다섯 경로 정지, 국면 2 변형 단계 A 뒤 `trim_phase2_search_not_open`. TR-5b: 그 정지 삭제 확인(XS-15) |
| **OS-L** | §13, §7.3 `grow` | OS-5, OS-V, TR-7, DS-1 결정 -- **TR-TL과 같은 변경** | 9. 더해 반복당 색인 크기 측정 기록 |
| **OS-3** | §9 | OS-2, OS-5, TR-6 | 6 |

### 16.2 F-1 fixture(사용자 승인 S-9·S-11)

* 위치: `skills/analog-gmid-design/assets/fixture/offset_strategy/`(저장소 안·library 밖, T-28 선례 `assets/fixture/` 계열).
* topology: library `current_reuse_telescopic_ota.topology.json`의 사본(연결 그대로, `connectivity_fp` 같음).
* spec: library spec 사본에 다음만 바꾼다. `meta.origin` = `fixture`. offset 판정 제약 둘(`offset_in_sigma_mv`, 그것을 참조하는 `offset_sys_mv`)을 지우고 `offset_requirement` = {`strategy`: `matching`, `coverage_multiple`: 3, `offset_in_max_v`: 3 × 3.3 mV를 V로 적은 값}. 각 `source` = `user_spec`, record = S-9(2026-10-16) 결정 원문, 3.3 mV는 2026-10-08 Q3 (2) 유래. **`offset_in_max_v`의 `source.record`에는 유도식 '3 × 3.3 mV'와 두 출처(S-9의 k = 3, Q3 (2)의 3.3 mV)를 문장으로 남긴다**(검증 v0.2.1 N-9) -- `value` 칸의 숫자만으로는 어디서 왔는지 보이지 않기 때문이다. `judgment_temperature_range_c`는 넣지 않는다(OS-2에 소비자가 없다, OB-21).
* structure 사실: fixture에 `structure.json` 사본을 두지 않는다. 실행은 `structure_path` = library `current_reuse_telescopic_ota.structure.json`을 넘긴다(승인 사실의 사본을 만들지 않음, OB-23. 연결이 같아 `connectivity_fp` 결속이 성립한다).
* library spec은 바꾸지 않는다. **비교 한계**(계획 N7.1): fixture 결과는 library 기준선과 비교하지 않는다. OS-2 완료 조건(유도 제약·로더·출발값이 실제 경로에서 동작)에만 쓴다.
* **F-1 = (a) 결정(S-14, 2026-10-16 "모두 권고대로")**: current_reuse fixture를 유지한다. OS-2 검증 항목은 front를 요구하지 않는다(봉인 평가의 `req:` 행·로더·출발값·결과 JSON 칸으로 판정, §16.1). current_reuse의 층 0 실패는 이 기능 밖의 별도 엔진 조사 card로 다룬다.

### 16.3 test 목록(독립 oracle)

| card | test | 내용 |
|---|---|---|
| OS-2 | `tests/authoring/test_spec_offset_requirement.py` | L1(판정 온도 범위의 `lo` ≥ `hi`·비유한·키 밖 포함), meta 불일치 spec에서 요구 섹션이 포트 뷰를 유도하지 않고 로드가 meta 위반으로 거부됨, 섹션 대기 → None + `pending`, 값 하나 대기 → `type`, L3, 포트 뷰 = view 없는 offset 제약이 받는 뷰, **요구 없는 spec의 `section_fps`·`spec_fp`가 칸 추가 전과 같음**(test가 지문 식을 같은 방식으로 재계산하지 않고, 칸 추가 전 커밋에서 잰 값을 픽스처로 고정 -- 검증자가 제공) |
| OS-2 | `tests/authoring/test_spec_offset_conflicts.py` | L2: metric 셋 × (`user_spec`, 판정 대상 `reference`) 거부, `pending_spice` 항목·그것을 가리키는 `reference`·`pending_constraints`는 통과, 참조 해석 뒤에 판정되는지(참조 대상만 바꾼 두 픽스처) |
| OS-2 | `tests/search/test_ss_constraints.py`(추가) | 커널 행(단일 항 k·σ_in): 손 계산 c, s = k·s_σ, 모델 오차 바닥, σ_in None·resolution None·resolution 0(모델 오차 없음) 사유, **V_id*(`offset_sys_mv`) 결과가 있어도 커널 행 값·c가 바뀌지 않음**, **사용자 ss 제약 없음(`declared` 빈 tuple) + bounds 있음 → 합성 행이 나온다**, 봉인 안 된 점, bounds 비면 지금 행과 같음 |
| OS-2 | `tests/search/test_kernel.py`(추가) | bounds 있으면 σ_in metric 요청 하나(`offset_sys_mv` 요청 없음), 없으면 지금과 같음 |
| OS-2 | front 판정 소비자 test(파일·필드 이름은 DE-1 design 뒤 확정, §3.7) | 같은 문턱 항목을 읽음(조인 문턱 항목으로 바꾸면 커널 행·front 판정이 함께 바뀜), 값은 front 점 자신의 스냅샷에서 읽음(child 스냅샷을 주면 읽지 않음 -- 관찰), 위반 점 front 제외·비지배 재필터는 DEC-74 자리의 것(새 재필터 호출 0, grep) |
| OS-2 | 완료 조건 10 (a) `tests/search/test_offset_kernel_row_toy.py` | **정의 손계산 오라클 toy**(피검 함수로 기대값을 만들지 않음): 손계산 σ_in에서 k·σ_in ≤ 문턱이 통과·거부를 맞게 낸다. **거부 경우를 먼저** 확인 |
| OS-2 | 완료 조건 10 (b) front 판정 toy(파일·필드 이름 DE-1 design 뒤 확정) | **ΔW ≠ 0** toy에서 gain-budget DEC-23 정의 문장으로 손계산한 V_id*로 k·σ_in + \|V_id*\| > 문턱인 점이 front에서 빠지고 비지배 재필터가 다시 돈다(**거부 먼저**). \|A_dc\| > 판정 분해능인 toy에서 **ΔW = 0**이면 V_id* = 0이라 통과하고, 이 경우는 front 판정을 실질적으로 시험하지 못한다는 사실을 test·보고에 정직하게 적는다(ΔW = 0 → 0은 \|A_dc\| > 판정 분해능일 때만 -- O-63 (1)). **갈래 먼저·정의 불능 toy**(계획 v0.7.3, O-62 (3)·O-63 (1)): \|A_dc\| ≤ 판정 분해능인 toy에 ΔW = 0인 점과 ΔW ≠ 0인 점을 주면 둘 다 ΔW와 무관하게 σ_in·V_id* 정의 불능이고, 커널 행 ①에서 걸러지든 front 판정 ②에서 빠지든 **원인 = 갈래 사유 기록의 참조, offset 위반 기록 0**이다(front에서 빠지면 비지배 재필터가 다시 돈다). **0·통과로 나오거나 offset 위반으로 기록되면 red**. **미수렴 toy**(O-64 (2)): gain-budget N6.6 완료 조건 (6)·(12)(a)를 인용하고, matching 합성 제약이 걸린 점이면 front에서 빠지고 원인 = 미수렴 사유 기록의 참조(offset 위반으로 기록되면 red). 기록 필드 이름은 PS-1(DE-1 design 뒤) |
| OS-2 | 완료 조건 10 (c) | 두 판정이 같은 문턱 항목 하나를 읽는다(문턱 사본 0, grep) |
| OS-2 | 완료 조건 10 봉인 불변식 | F-1 fixture front 점 전부가 평가 커널 봉인 통과(KVL·KCL·영역, gain-budget N3.6) |
| OS-2 | 완료 조건 10 SPICE 다리 | σ_in = 오라클 MC(A = `.tf`, OP-5), V_id* = 오라클 `.dc`(OP-5), 엔진 점 입력 = gain-budget EO-1 생산자. EO-1·OP-5·OS-V 전에는 '보류'(gain-budget N6.3 (i), §16.1) -- 이 조건은 닫지 않는다 |
| OS-2 | 완료 조건 10 검증자 값 변화표 | F-1 fixture 결과의 변화와 원인(원인 미설명 0). 검증자 소유, 결정성 비트 동일은 항상 |
| OS-2 | `tests/search/test_iv_matching_l.py`(추가) | (가) `offset_in_sigma_mv <= x` spec과 (나) L/k = x(V 환산) 유도 제약이 같은 L 하한, 요구 없는 경로 비트 동일 |
| OS-2 | `tests/search/test_search_context.py`(추가) | `derived` 있고 mismatch 데이터 없음 → 거부, 요구 없는 spec에서 `offset_sys_mv` 판정 제약만 있으면 mismatch 검사 대상 아님(지금 그대로), `offset_start_targets`는 (k, 문턱 항목 `value_v`)만(같은 k·문턱 값에 다른 `OffsetBound` 이름·refs를 주어도 `start_intervals` 입력 버전 같음, 문턱 항목 값을 바꾸면 입력 버전이 바뀜) |
| OS-2 | `tests/search/test_find_front.py`(추가) | `variant_key=None`이면 `run_id` 지금 식, 키가 있으면 다름, `variant_key` 빠지면 `TypeError`(거부 먼저), `SearchContext`에 `variant_key` 칸 없음 |
| OS-2 | `tests/pipeline/test_run_plan_build.py` | 요구 없음·matching·L4(단일 출력 노드 목표 없음/있음/차동 출력)·L5(단위 바꾼 가짜 서명)·L6, 두 번 불러 같음 |
| OS-2 | `tests/pipeline/test_plan_session.py` | 열기에서 색인·계수 하나, §6.1 계획 생성 조건 두 경우(검증 v0.2.2 N-8): (a) 단계 A가 spec 없이 멈춤(예: A1_load 거부) → 계획 없음·변형 실행 0·`stage_b_unplanned` = `skipped` 단계 B 한 번 (b) spec이 있고 단계 A가 `stopped`·`review_needed` → 계획은 만들어지고, 변형 실행에서 단계 B는 진단 설정대로·탐색 0·`stop` = `stage_a_<상태>`, 계획 거부 → 단계 B·탐색 호출 0(관찰), 진단 모드: 단계 A `review_needed`면 단계 B는 진단으로 돌고 탐색 0·`stop` = `stage_a_review_needed`, 같은 index 두 번 실행 `ValueError`, 닫은 뒤 실행·`stage_a`·`block_index`·`search_context` 접근 `ValueError`, `PlanResult`·`VariantResult`에서 `S3Index`·`RunCounters`·`SearchContext`·`StageAResult`에 닿는 속성 0(객체 그래프 순회 관찰 -- 계획 N3.12 ④), 세션 열기가 `open_run` 한 번(호출 관찰), 구조 test `check_m`이 `plan_session.py` 허용·다른 pipeline 파일 거부(거부 먼저) |
| OS-2 | `tests/pipeline/test_run_plan.py` | `run_plan` = 세션 사용(세션 함수 호출 관찰), 결과 JSON 칸(§8), `PlanResult`·`VariantResult` 노출 칸이 E-S18 목록을 모두 덮음 |
| OS-2 | `tests/integration/test_run_plan_baseline_9circuits.py` | 완료 조건 1(비교 제외는 검증자 소유) -- 판정은 auditor 격리 복제본 |
| OS-2 | `tests/integration/test_run_plan_matching_fixture.py` | F-1 fixture 실행(front 요구 없음, F-1 (a)): 봉인 평가마다 S3 evals 줄의 `req:` 행 또는 정의된 미측정 사유, front 점이 있으면 `derived_rows` c = S3 evals 행 c, notes `final_acceptance_is_oracle_range_judgment` |
| OS-V | `E/tests/metrics/test_verified_by.py`(추가) | 합성 판정 행 출처 규칙(커널 행 = σ_in 종류, front 판정 = 항 하나라도 unverifiable이면 unverifiable). `offset_sys_mv` 행·measure 연결 test는 gain-budget VB-1 소관, 오라클 쪽 측정 test는 oracle-portability 소관 |
| OS-5 | `tests/pipeline/test_run_plan_multi.py`, `tests/integration/test_run_plan_compare_phase1.py` | 완료 조건 2(순서 뒤집기 포함), 3, 4, L11, `variant` 칸, `S3Index` 상한 B_S0 |
| OS-L | `tests/pipeline/test_plan_session_add.py`, `tests/integration/test_run_plan_iteration.py` | §13.3 reason마다 거부를 먼저 확인(같은 원인 지문 재추가 → `duplicate`, 반복 번호만 다른 같은 키도 `duplicate`, 상한 None·초과 → `iteration_cap`), Δ_T가 들어가는 길 하나(`tightened_threshold` → `add_variant`, 호출 grep + 실행 경로), 커널·`ss_constraint_rows`에 합성 호출 0(grep), `run_id`가 중복 판정 키마다 다르고 반복 번호와 무관, 추가 변형에서 θ 무관 블록 계산 0 -- 단 문턱 의존 블록(`start_intervals` -- §3.2, offset-trim G-12 목록)은 문턱 값이 다른 추가 변형에서 계산되고 같은 문턱 값이면 적중, 새 세션 단독 추가 실행과 비트 동일(E_B 선언), `grow` 상한 늘어남, memory 칸 |
| OS-3 | `tools/offset_compare/tests/test_compare.py` | 엔진 import 0, 권고 어휘 0, 불일치 표시, 손 결과 JSON 대조 |

---

## 17. 다른 문서 개정안(OS-0과 함께 재승인)

### 17.1 OT 개정안

| OT 절 | 개정안 | 근거 |
|---|---|---|
| §4 흐름 | `run_plan` → 세션 열기(원본 단계 A, `build_run_plan(spec, topology, approvals)`) → 국면 1: 원본 변형 탐색 → `run_trim_candidates` / 국면 2: `bind_trim` → 파생 변형 단계 A(+ 원본 비교 벌) → 단계 B → 탐색. 진입 인자 `trim_approval_path`와 `trim_approval_without_decl`을 지운다 | XS-4, S-2 |
| §5.1 | `coverage_multiple` 삭제(k = 요구) | XS-6, DS-U3 |
| §5.2 | 이 design §4.2 L2·L7~L10으로 대체. 강등(`trim_demoted_constraints`)·`trim_constraint_conflicts` 삭제 | XS-1, PD-9 |
| §8.1 | `configurations: [{derived_connectivity_fp, selections}]`(N·N+1 둘 다 승인 가능) | XS-2 결과(OB-19) |
| §8.1·§8.3-4 | `spec_trim_fp` = `fp_of((offset_trim 섹션, offset_requirement 섹션))` | XS-6 결과(OB-15) |
| §9.4 | 추천 구성 N_rec, N_rec + 1. N_rec + 1의 m = min_p m_max,p(N_rec + 1), 정의 안 되면 `trim_config_next_undefined` | XS-2, DS-U6 |
| §9.5 | 구성마다 `<circuit>.trim_d<순위>_n<N>.topology.json`·`.md`·`.approval_draft.json` | XS-2 |
| §10.1 | 색인 상한 = 이 design §7.3 식 | XS-12, PD-7 |
| §10.4·§10.6·§17 | k = 요구 `coverage_multiple`. §17-3·5의 온도 범위 = 요구 `judgment_temperature_range_c` 참조(T-34) | XS-6, T-34 |
| §10.8 | 요구가 있으면 offset 판정 제약 셋 다 로더 거부(L2) | XS-1 |
| §13 | `demoted_constraints` 삭제, `mode` → `run_plan.phase` 참조 | XS-1 |
| §14.1·§14.2·§14.4·§15 | `spec_trim_conflicts.py` 삭제, `load_trim_approval` TR-1 → TR-3, `stage_a.py` 인자 행 삭제, TR-1 test는 L7~L10 거부로 | PD-2 |
| §16.1 | offset 판정 제약 셋 다 없음, 요구 섹션(trim, k, `offset_in_max_v` ≥ V_res), `offset_trim`(V_res·온도) | XS-9 |
| §18.2 X-T11 | '요구 섹션 포함' | OB-15 |

### 17.2 40 design 개정안(XS-7·XS-12·PD-7·PD-8)

| 40 절 | 개정안 |
|---|---|
| §2.4.5 '수명' | "실행 하나 = 실행 계획 하나(offset-strategy design §6). 실행 경계(실행 계획 세션 열기)에서 `RunCounters`와 함께 새로 만들고, 모든 변형의 모든 블록 호출에 같은 객체를 넘기며, 세션을 닫으면 버린다. 실행 사이에 넘기지 않는다" |
| §2.4.5 '전달'(PD-8) | **반영됨**(card B, 40 v1.11, E-S14): `run_stage_a`가 `donors`·`counters`를 필수 키워드로 받는다. OS-2는 같은 서명을 쓴다(서명 변경 없음) |
| §2.4.5 (2) 구조 규칙 M(검증 B2) | (M-a) 허용 목록에 `E/pipeline/plan_session.py`. (M-c) 예외 = `plan_session.py` 안 같은 세션의 여러 `run_stage_a`(OS-5·TR-3 몫, 40이 예약한 예외의 구체화). (M-d) 예외 = `PlanSession` 인스턴스 속성(세션 수명 = 실행 하나, `close`가 참조를 버림, 결과 객체에 싣지 않음 -- §6.1). 세 줄을 `check_m`과 픽스처에 같은 변경에서 반영 |
| §2.4.8 '제약 행' 행 · U17 ② 알림(검증 M3) | `graph/metrics: constraint_rows`의 행 값 형식에 (v, L)을 더한다(행 형식 넓힘, §3.1 '행 값'). 행 형식의 정본은 U17 ② design이고, 그 writer의 입력 버전 투영에 변형의 matching `OffsetBound` 투영이 들어간다(§3.1 M2). U17 ② design이 이 넓힘을 담지 않으면 OS-2가 착수할 수 없다 |
| §2.4.5 '상한'·§2.4.9 증거 집합 | Σ_블록 분할 수 × (Σ_v E_total,v + B_S0). `S3Index` 생성자 필수 인자 `s0_sets`(`open_run(s0_sets=…)`로 넘김, 40 '수명' (1)), `add_eval_ceiling`, OS-L `grow`. B_S0가 계획에서 나오는데 계획이 `open_run` 뒤 단계 A에서 나오는 순환은 §18.4 PS-6(멈춤) |
| §2.4.9 E_total | "**변형 하나**의 커널 평가 수 상한(XS-12). 실행 전체 상한은 Σ_v E_total,v" |
| §2.4.9 `RunCounters` 문단 | "실행 경계 = 실행 계획 세션 열기" |

### 17.3 trim 시험 회로 spec 재작성안(XS-9, 값은 사용자 자리)

T-24·T-25·T-27·T-28에서 바뀌는 것만:

```json
"human": {
  "offset_requirement": {
    "offset_in_max_v":   {"value": "<사용자 값 -- DS-U8, 로더 조건: ≥ residual_offset_v>", "source": {"kind": "user_spec", "record": "<결정 기록>", "decided": "<날짜>"}},
    "coverage_multiple": {"value": "<T-25의 k 값 그대로>", "source": {"kind": "user_spec", "record": "T-25 -- offset_trim.coverage_multiple 에서 옮김(XS-6)", "decided": "2026-10-15"}},
    "strategy":          {"value": "trim", "source": {"kind": "user_spec", "record": "<결정 기록>", "decided": "<날짜>"}},
    "judgment_temperature_range_c": {"value": {"lo": "<T-34(= T-14 범위) 하한>", "hi": "<T-34 상한>"}, "source": {"kind": "user_spec", "record": "T-34(2026-10-16)", "decided": "2026-10-16"}}
  },
  "offset_trim": {
    "residual_offset_v":  "<T-25 값·출처 그대로>",
    "trim_temperature_c": "<T-25 값·출처 그대로>"
  },
  "constraints": "<two_stage_ota spec 판정 제약(T-27) 그대로, offset_excess 항목은 뺀다(DS-U2)>"
}
```

* T-27의 '강등 경로 확인'은 강등이 없어져(XS-1) 대상이 사라진다. 반영은 TR-1 병합 뒤(T-28).
* 시험 회로는 TR-7·TR-TL이 판정 온도 범위를 쓰므로 그 칸을 넣는다(값 = T-34).

---

## 18. 결정 상태

### 18.1 오케스트레이터 기본안(사용자 결정 아님 -- 원칙 근거)

| ID | 항목 | 기본안 |
|---|---|---|
| OB-1 | G-S1 형식 | ① 커널 행 = `ss_constraint_rows` bounds의 단일 항 k·σ_in 행(계획 G-S1 ① (ii)), ② front 판정 = DEC-74 자리 소비자(§3.7, 형식은 계획 결정 O-53 A2) |
| OB-2 | 단위 | 레지스트리 `mv` → `core.MILLI`, 그 밖 L5 |
| OB-3 | view | 기본 포트 뷰, 로더가 정함 |
| OB-4 | S1v | 유도 제약은 S1v 밖(PD-3의 전제) |
| OB-5 | G-S2 | σ 목표 L/k |
| OB-7 | 검사 위치 | L4·L5·L6·L11은 계획 함수 |
| OB-9 | 경계 구현 | `run_stage_a` 필수 키워드, `StageAResult.topology`(PD-8 승인 범위의 세부) |
| OB-11 | `run_id` | 유도 제약이 있을 때만 지문에 더함 |
| OB-13 | 합성 행 (v, L) 자리 | v0.2.6(F3): `graph/metrics: constraint_rows` 합성 행 값(writer search 제약 블록). 옛 `EvalResult` 보고 칸은 철회 |
| OB-14 | 비교 도구 | `tools/offset_compare/compare.py` |
| OB-15 | 승인 결속 지문 | 요구 섹션 포함 |
| OB-16 | compare와 DS-1 | (DS-1이 S-14로 (다)로 닫혀 대상 소멸. OS-5가 (다)로 compare를 연다) |
| OB-17 | `given_starts` | 원본 topology 변형에만 |
| OB-19 | 승인 형식 | 구성 목록 |
| OB-20 | 출발값과 문턱 | **v0.3.1 정정**: 계획 v0.7 N3.3(211)·LR6(604)대로 σ 목표 = 커널 판정 문턱 항목 / k(루프는 조인 문턱 항목, 참조). `start_intervals`는 문턱 의존 블록(offset-trim G-12 목록 -- OT §20.7 알림, §18.2) |
| OB-21 | 판정 온도 범위 칸 | 선택 칸, 필요한 소비자가 없으면 거부. 값 모양 `{"lo", "hi"}` |
| OB-22 | 사슬 대체 범위 | 전체 사슬 셋만(§6.4) -- Q-1로 확인 |
| OB-23 | fixture structure 사실 | 사본 없이 `structure_path`로 library 파일 |
| OB-24 | 세션 형식 | `open_plan_session`·`PlanSession`(`run_variant`·`add_variant`·`close`), 계획 거부 시 '거부 상태' 세션 |
| OB-25 | 변형 추가 사유 코드 | `run_plan_variant_add_rejected` + detail `reason`(§13.3) |
| OB-26 | card C 인터페이스 이름 | `s0_sets`·`add_eval_ceiling`·`grow` |
| OB-27 | OS-V 합성 판정 행 검증 출처 | 커널 행 = σ_in 종류, front 판정 = 항이 모두 `spice_oracle`이면 `spice_oracle`(§12). `offset_sys_mv` 행은 VB-1 |
| OB-28 | 커널 행 분해능 0·None | v0.3.0: 항이 하나라 기존 ss 행 규칙 그대로(§3.1). v0.2.x의 항별 판정 규칙은 대상 소멸 |
| OB-37 | (v0.3.1 철회 -- 계획 N3.12 ④ '버린다'를 따름. 노출은 열린 세션 API, §6.1·§6.4) | -- |
| OB-29 | S3 `variant` 칸 | OS-5에서 구현, 변형 둘 이상 또는 반복 번호 1 이상일 때만(§3.3, 검증 N-4) |
| OB-30 | 단계 B 재사용 | pipeline 수준 캐시 없이 블록 결과 색인만(§6.1, 검증 N-7) |
| OB-31 | 반복 상한 이중 확인 | 채택: OS-L `open_plan_session(iteration_cap=)` 필수 키워드, 사유 `iteration_cap`(§13.4) |
| OB-32 | `derived` 항목 형식 | `ThresholdItem`(authoring 값) + `OffsetBound.threshold` 자리, trim 잔여 문턱은 최상위 항목(§3.4) |
| OB-34 | `constraint_set_fp`와 (다) 평가 키 | `constraint_set_fp`는 문턱 값을 담고 Δ_T 기록 참조는 뺀다. (다) 평가 키는 `constraint_set_fp`(문턱 값 지문)를 쓰고 `cause_fp`는 쓰지 않는다. (다)에서는 평가 키 항목을 놓지 않는다(§3.3, §10.3) |
| OB-35 | 반복 수 정의 | 추가된 변형 수 a(처음 0), a ≥ `iteration_cap`이면 거부(§13.4) |
| OB-36 | V_id* 대조 | v0.3.0 철회(규칙으로 두지 않음). 부호 있는 V_id* 대조 정의는 gain-budget ME-1·VB-1 소관 -- §18.4 PS-2 |
| OB-33 | 변형 추가 거부 reason | `no_threshold_slot`·`threshold_not_tightened`·`threshold_unit`·`iteration_cap`·`duplicate` 등(§13.3) |

(v0.1의 OB-6은 PD-9 승인 문언으로 바뀌어 지웠고, OB-8·OB-10·OB-12·OB-18은 PD-1·PD-8·PD-7·PD-2로 승인되어 기본안 목록에서 뺐다.)

### 18.2 계획과 다른 점

**v0.3.1 -- 정정한 어긋남(정직 기록, 검증 M5)**: v0.3.0의 '계획과 다른 결정 없음'은 틀렸다. v0.3.0에는 계획과 다른 것이 둘 있었고 v0.3.1에서 계획대로 고쳤다.
* **B1(OB-37)**: v0.3.0은 `PlanResult.block_index`로 실행 수명 색인을 `close` 뒤 호출자에게 넘기고 계획 N3.12 ④ '닫기(색인·계수를 버린다)'를 '세션 쪽 참조만 놓는다'로 다시 읽었다(계획 밖 결정, 원래 취지와 다를 수 있었음). 고침: 닫은 뒤 색인에 닿는 길 0, 노출은 열린 세션 API(§6.1·§6.4).
* **B3(OB-20)**: v0.3.0은 출발값 σ 목표를 요구 값 / k로 두고 '계획 무언'으로 멈췄으나, 계획 N3.3(211)·LR6(604)은 '커널 판정 문턱 항목 / k(루프는 조인 문턱 항목)'로 분명히 적는다. 고침: §3.2.
* 그 밖 v0.3.1 정정: §3.7 선행 근거(LA-1/O-44 (1) → DE-1 (c) 사슬), PC-10 문언(계획 475행 인용), 결과 JSON 값 사본 삭제(§8 출력 기록 규칙).

**다른 문서 알림 항목(v0.3.1)**:
* offset-trim design §20.7(G-12 '문턱에 의존하는 블록' 목록): `start_intervals`를 다시 넣는다(§3.2 -- OB-20 정정의 결과, 계획 N3.12 '재사용 범위' ①).
* (닫힘, 계획 v0.7.2) PC-10 문언: 계획 OS-V 행(476)이 O-53 B3·offset-trim G-15와 같은 문언으로 정렬됨(§12).
* (닫힘, 계획 v0.7.2·O-63 (3)·O-65) W-1 노출 문언: 하네스는 열린 세션의 공개 API로 읽고 결과 객체는 색인 참조를 담지 않는다(§6.4).
* 40 design: §17.2 '구조 규칙 M'·'제약 행' 두 행.

v0.3.0 문장(기록): 계획 v0.7.1과 다르게 정한 결정은 두지 않았다(S-7) -- 위 B1·B3로 정정됨. 아래는 v0.2.x 문장이다. 계획 v0.6.1과 다르게 정한 결정은 두지 않았다(S-7). D-25는 T-36으로 결정됐고(master `2c3e740`의 계획 문구도 '결정됨(T-36)'으로 정리됨 -- 이 브랜치 base `194981f`에는 그 전 문구가 남아 있다), 계획이 'D-25 결정 뒤 design이 닫는다'고 한 그대로 §13.1이 인터페이스 서명을 닫았다. 계획 N7.2 OS-L 행의 'D-25 결정' 선행은 충족됐다.

**다른 문서 알림 항목(v0.2.3) -- 반영됨**: offset-trim design v0.3.3(master)에 아래 두 문장이 반영됐다:
* §20.3: `tightened_threshold`의 첫 인자 = base 변형의 처음 문턱 항목(`margin_ref` None). 앞 반복의 조인 문턱을 넣지 않는다(§13.1).
* §20.6·§20.7: 반복 수 = 그 세션에서 추가된 변형 수(처음 0), 추가가 받아들여지는 최대 수 = `iteration_cap`. §20.7 순서 1(세션 열기)에 '`iteration_cap`을 세션 열기에 넘긴다'(§13.4).

### 18.3 원래 취지와 다름

| ID | 내용 |
|---|---|
| OD-1 | 시간 예산 유도 실행은 다변형·추가 변형에서 단독 결과와 비트 동일을 보장할 수 없다(§7.2, DS-U9 열림). 원인은 비트 동일 전제(E_B 선언)다 |
| OD-2 | (닫힘, S-14) DS-1 (가)는 기각됐다. 채택된 (다)의 편차 = 같은 θ의 커널 평가가 문턱 값이 다른 변형마다 남는 것(XS-8 허용 범위, 블록 계산은 색인 공유, §10.3) |
| OD-3 | TR-3~TR-5b 사이 국면 2 탐색 게이트(XS-15 수용됨, 추적만) |
| OD-4 | (승인됨 O-53 A2 = 계획 XS-20, 추적만) S-1의 matching 판정이 한 판정이 아니라 커널 k·σ_in과 front k·σ_in + \|V_id*\| 두 자리로 나뉜다. 그래서 커널 탐색은 V_id* 몫을 모르고 돌고, V_id* 위반 점은 front에서 빠진다(§3.1·§3.7) |

### 18.4 열린 결정·질문

| ID | 질문 | 막는 것 |
|---|---|---|
| DS-1 | **결정됨(S-14, 2026-10-16 "모두 권고대로")**: (다) 키 분리 -- 평가 키에 변형 제약 집합 지문(문턱 값 포함), 실제 계산 공유는 card B 블록 결과 색인(§10) | -- |
| F-1 | **결정됨(S-14)**: (a) current_reuse fixture 유지, OS-2 검증 항목은 front 불필요, current_reuse 층 0 실패는 별도 엔진 조사 card(§16.2) | -- |
| 승인 | **design v0.2.4 사용자 승인(S-14, 2026-10-16 "모두 권고대로")**. 이 판(v0.2.5)은 승인 결정 DS-1·F-1의 기록 반영이다 | -- |
| Q-1 | **결정됨(S-13, 2026-10-16 "모두 권고대로")**: 부분 사슬 test(`test_layer0_boundary_rows`, `test_s0_layer_9circuits`, `u13_hand`, `u13_real`)와 단계 B 없는 test(`test_cell_floor`, `test_blas_env`)는 W-1 대체 범위 밖(OB-22 그대로). **기록할 사실(검증 v0.2.1 N-5)**: PD-8 뒤에는 `run_stage_a`가 `donors`·`counters`를 필수로 받으므로 이 범위 밖 test들은 호출마다 `open_run()`을 불러 넘긴다(card B 규칙 M (M-c), v0.3.1 사실 정정 -- 직접 생성은 (M-b) 위반). 이것은 세션 열기의 일부(실행 경계 객체 만들기)를 test 안에서 두 번째로 부르는 것이다. 엔진 제품 경로의 사슬은 하나(세션)로 남고, 두 번째 구현은 test 쪽 단위 시험 준비에만 있다 | -- |
| Q-2 | (닫힘, v0.2.1) v0.1 검증 비차단 N-1~N-4·N-6·N-7·N-12 원문을 받아 반영했다(history H4) | -- |
| DS-U8 | trim 시험 회로 `offset_in_max_v` 값 | TR-1 뒤 반영 |
| DS-U5 | library spec 이전 | -- |
| DS-U9 | 유도 예산 다변형 규칙 | -- (열림, §7.2) |
| OS-2 병합 순서 대 U17 ② | **닫힘(계획 v0.7.1 N7.1, O-61 P9·O-62)**: OS-2 착수 = U17 ② 병합 + Q8 결정 뒤. 과도기 `EvalResult` 값 칸·결과 JSON 재계산 금지. U17 ② 일부 선행안은 그때 사용자 결정(§3.1 '행 값') | -- |

**계획 무언 -- 멈춤(v0.3.0, 이 design이 정하지 않는다)**:

| ID | 항목 | 막는 것 | 누가 |
|---|---|---|---|
| PS-1 | DEC-74 front 판정 기록의 **이름만** 남음. 종류 = 출력 기록(gb v6.24 `59ecc88e` DEC-74·N3.3 (b), O-68 (3)), 선후 닫힘(U17 ② ⇒ LA-1 ⇒ DE-1, 계획 v0.7.3 선행 칸 명시). **OS-2 착수 조건**(계획 v0.7.3 N7.1) | §3.1 '정의 불가'·§3.7 소비자, §8 `front_judgment`, 완료 조건 10 (b) test 필드 | card DE-1 design·착수 실측(gb 알림) |
| PS-2 | 부호 있는 V_id*의 엔진 대 오라클 대조 정의(옛 OB-36 절댓값 대조 철회) | OS-V 대조, `model_error_offset_sys_mv` | gain-budget ME-1·VB-1 |
| PS-3 | (닫힘, v0.3.1 -- 계획대로 OB-20 정정, §3.2·§18.2) | -- | -- |
| PS-6 | `open_run(s0_sets=B_S0)` 순환(검증 M10): B_S0는 계획에서, 계획은 단계 A spec에서, 단계 A는 `open_run`의 쌍에서. 계획 PD-7·40 '수명' (1) 어디에도 순서를 푸는 문언이 없다(새 장치를 만들지 않는다) | OS-5 `s0_sets` 구현(OS-2는 막지 않음) | 계획 PD-7 또는 40 §2.4.5 개정 |
| PS-7 | 하네스가 평가 결과 전수(`seq` 순)를 읽는 S3 색인 평가 키 부분의 열거 API -- 40 §2.4.5 조회 API는 `get(key)`뿐이고 '순회하지 않는다' | §6.4 평가 목록 행, `nfr4_run_dump.py` 대체. **OS-2 착수 조건**(계획 v0.7.3 N7.1) | U17 ② design(40 §2.4.5) |
| PS-8 | (재분류, v0.3.3 검증 -- 멈춤 아님) 커널 행 ① 거름은 지금 경로(`ss_constraints.py:72-78` → `kernel.py:81` → `eps_sweep.py:37, :44`)로 성립한다(§3.1 '정의 불가'). 남는 의존(갈래 코드 이름 = DE-1, 미측정 자리 = Q8)은 이미 착수 조건 | -- | -- |
| open_run 점검 | 계획 v0.7.3 N7.1 점검 항목(결정 아님): card C 최종 `S3Index` 상한 인자가 단계 A·B보다 먼저 정해져야 하는 순환인지 OS-2 착수 전 확인. 지금 card C 미병합(`open_run()` 인자 없음, `E/search/open_run.py:15-17`) -- **미확인** | OS-2 착수 | 착수 전 확인, 순환이면 design·40 §2.4.5 소유자 |
| W-1 | (닫힘, 계획 v0.7.2 -- O-63 (3)·O-65: 열린 세션 공개 API로 읽기, 결과 객체 색인 참조 0, §6.4) | -- | -- |
| PS-4 | `output_reference`가 DEC-23 기준 종류 셋(값·넷·입력 추종) 가운데 '값'만 덮음. 넷·입력 추종 선언 칸 이름은 DEC-23이 'design'에 맡겼고(gain-budget design 소관) 아직 없다 | §8, L4, OS-V 오라클 입력 | gain-budget design |
| PS-5 | 비교 도구가 matching 여유 한 줄(L − v)을 빼서 낼지(엔진 밖 표시 계산). 엔진 결과에서는 `margin_v`를 지웠다 | §9 칸 | 사용자(OS-3 design 때) |

### 18.5 graph 단일 정본 점검(프로젝트 CLAUDE.md '★graph 단일 정본' 규칙 1~7, v0.3.0 전수)

| 대상 | 판정 | 처리 |
|---|---|---|
| 커널 행 값 (v, L) | graph 필드 `graph/metrics: constraint_rows`, writer = search 제약 블록 하나(§3.1) | 준수 |
| `EvalResult` 값 칸(v0.2.5 이전 (v, L) 보고 칸) | 위반(사본) | v0.2.6에서 철회, v0.3.0 과도기 자리로도 금지(§3.1) |
| 결과 JSON `derived_rows.margin_v` | 위반(결과 JSON을 쓸 때 graph 밖에서 새 값 계산) | **삭제**(§8) |
| 결과 JSON·`PlanResult` `diagnostic` 칸 | 위반(단계 B 보고서 `diagnostic` 칸의 둘째 칸) | **삭제**, 보고서 칸 참조(§6.4·§8) |
| 결과 JSON `output_reference.value_v` | 위반(spec 기준 값 사본) | **삭제**, spec 참조 `ref`로(§8) |
| OS-V의 `offset_sys_mv` `verified_by` 행 | 위반(VB-1과 같은 행의 둘째 생산자) | **삭제**, VB-1 인용(§12·§14.2·§15) |
| 평가 결과 목록 노출 `sctx.cache` | 위반 위험(지울 대상 `sctx.*` 슬롯에 새 소비자) | 열린 세션의 `block_index` 평가 키 부분 API로(§6.4, 열거 API는 PS-7) |
| v0.3.0 `PlanResult.block_index`·`stage_a`·`VariantResult.search_context` | 위반(규칙 2 '실행 수명' 색인이 `close` 뒤로 나감) | **삭제**(§6.1·§6.4) |
| 결과 JSON `requirement` 값 칸·`derived[].k`·`derived[].threshold.value_v` | 위반(spec 값 사본, 계획 N3.3 머리) | **삭제**, 참조만(§8 '출력 기록 규칙') |
| `constraint_rows` writer 입력 버전 | 투영에 `OffsetBound` 투영이 없으면 문턱이 다른 변형이 옛 행을 graft(fail-closed 위반) | 투영에 넣음(§3.1 M2), 평가 키 `constraint_set_fp`와 따로 |
| `start_intervals` extras `offset_start_targets` | 블록 입력 투영(문턱 항목에서 읽음, 사본 아님) | 준수(§3.2) |
| 세션의 `donors`·`counters` 보관 | 구조 규칙 M (M-d) 예외 필요 | 40 개정안(§17.2), 세션 수명 = 실행 하나 |
| front 판정 값 | 판정 자리 하나(DEC-74), σ_in은 커널 행과 같은 `metrics_ss` 필드를 front 점 자신의 스냅샷에서 읽음, 사본 없음(§3.7) | 준수. 자리 실체는 PS-1 |
| 문턱 항목 | 실행 입력(graph 밖), 커널 행·front 판정이 같은 항목 하나를 읽음 | 준수(재계산 0) |
| `OffsetBound.k`·`ThresholdItem.value_v` | 실행 입력의 해석값 + 참조 경로(기존 `ConstraintDecl.value`·`ref` 형식) | 준수(기존 형식, 계획 N3.3) |
| 결과 JSON `requirement`·`derived`(참조 칸) | 출력 전용 기록(계획 FR-S7 '유도 제약과 출처를 싣는다'), 엔진 소비자 없음, 참조만 | 준수(출력 전용 선언) |
| 단계 B 재사용 | 블록 결과 색인만, pipeline 캐시 없음(OB-30) | 준수 |
| DS-1 (다) 평가 키 `constraint_set_fp` | 기존 S3 색인 평가 키의 칸(새 캐시 아님) | 준수 |
| `PlanResult.perf`·`shared.*` 계수 | `RunCounters`·`S3Index` 출력의 참조 | 준수 |
| **새 `SearchContext` 슬롯 하나**(v0.3.3 정직 기록) | `derived`(생성자 인자, 변형의 유도 제약 tuple 참조) + 읽기 속성 `offset_bounds`(그 안의 matching `OffsetBound`를 거르는 property -- `driving`이 `spec.driving_spec`을 읽는 방식, `E/search/search_context.py:128-129`). **실행 입력 참조 슬롯**이고 승인된 전달 자리다(PD-1 '`derived` = `build_search_context` 키워드와 전달 자리', 계획 N7.2 OS-2 행). 계산값·재사용 값을 담지 않으므로 cache·memo가 아니다. 지금 생성자 `SearchContext.__init__(dc, spec, settings, context_fp, code_fp, archive)`(`search_context.py:51`)에 키워드 하나를 더한다 | 준수(승인 자리, 값 사본·계산값 0) |
| `variant_key`(검증 V11) | 슬롯 승인이 없어 `SearchContext` 칸으로 두지 않고 `find_front`의 필수 키워드 인자로 넘긴다(§6.5). 소비자 `run_id` 하나 | 준수(슬롯 0) |
| `offset_start_targets` | `build_search_context` 안의 **지역 변수**(extras 조립용, `start_intervals`에 넘기고 버림) -- `SearchContext` 슬롯이 아니다 | 준수 |
| `PlanResult.perf`(검증 N15) | `RunCounters.snapshot()`의 반환을 싣는 **출력 전용** 칸. 엔진 소비자 0(결과 JSON·하네스 보고만) | 준수(출력 전용 선언) |
| 새 cache·memo·dict | 0. `sctx.*` 슬롯은 위 `derived` 하나뿐 | -- |

### 18.6 실현성 점검(사용자 규칙 2026-10-21: 설계 선택마다 인용 필드·함수의 실재(file:line), 단위, 대표값, 끝까지 경로. 확인 안 되면 '미확인'·멈춤)

기준 `e1a611ec`(이 브랜치 `35e4a7d3` 엔진 코드 동일 범위). 대표값은 F-1 fixture(k = 3, `offset_in_max_v` = 3 × 3.3 mV = 9.9 mV = 0.0099 V, §16.2).

| 설계 선택 | 인용 실재(file:line) | 단위 | 대표값 | 끝까지 경로 | 상태 |
|---|---|---|---|---|---|
| 커널 행 v = k·σ_in, u = `MILLI` | `ss_constraint_rows(bundle, declared, model_error=())` `E/search/ss_constraints.py:62`; 레지스트리 `offset_in_sigma_mv` 단위 `mv`·결과 칸 `sigma_in_mv` `E/metrics/registry.py:56`; `MILLI = 0.001` `E/core/units.py:22` | σ_in mV → V(×`MILLI`), L V, c 무차원 | σ_in = 3.0 mV면 v = 3 × 0.0030 = 0.0090 V ≤ L = 0.0099 V → c > 0(통과); σ_in = 3.5 mV면 v = 0.0105 V(거부) | `run_variant` → `build_search_context(derived=)`(`search_context.py:191`, 키워드 추가) → 커널 요청 `kernel.py:136` → `ss_constraint_rows`(`kernel.py:155`, `bounds` 인자 추가) → `rows`(`kernel.py:158`) → `constraint_rows` 필드 | 함수·단위 실재 확인. **필드 `graph/metrics: constraint_rows`는 지금 없음(U17 ② 몫) -- OS-2 착수 조건** |
| 분해능 s = k·s_σ | 결과 `MetricResult.resolution` 칸 `E/metrics/mna_types.py:370`(클래스 `:363`); 규칙 `ss_constraints.py:15-18` | mV → V | -- | 위와 같음 | 실재 확인 |
| 커널 행 ① σ_in 'A_dc 갈래' fail-closed | None → 행 없음·`unmeasured`에 코드 `E/search/ss_constraints.py:72-78`; `EvalResult.unmeasured` 기록 `E/search/kernel.py:81`; `unmeasured_front` 상태·최종 front 제외 `E/search/eps_sweep.py:37, :44` | -- | σ_in None 점 → 위반 행 0, unmeasured 1 | 커널 → `unmeasured` → `eps_sweep` 상태 → front 제외 | 경로 확인. 갈래 코드 이름(DE-1 (c))·미측정 자리(Q8)는 착수 조건 |
| front 판정 소비자(DEC-74 자리) | DEC-74 front 자리·V_id* 부호값 계산은 엔진에 없음(DE-1 (c) 몫); 지금 `offset_sys_mv`는 크기 근사 `E/metrics/offset_systematic.py:42-47` | V_id* mV → V | V_id* = 0.5 mV, σ_in = 3.0 mV → 0.0090 + 0.0005 = 0.0095 V ≤ 0.0099 V(통과); V_id* = 1.0 mV → 0.0100 V(front 제외) | `find_front`(`find_front.py:64`) 뒤 DEC-74 자리 → 출력 기록(이름 미정) → 결과 JSON `front_judgment` | **미확인 -- 멈춤(PS-1: 이름, DE-1 design 뒤)** |
| 출발값 σ 목표 = 문턱 항목 / k | `matching_bounds` `E/search/iv_matching_l.py:106-107`(`def matching_bounds` :106, `absolute` :107), `share = min(absolute) * MILLI / _SQRT2` `:123`; `start_intervals(projection)` extras `E/search/start_intervals.py:252-253` | V | 0.0099 / 3 = 0.0033 V → share = 0.0033 / √2 ≈ 0.00233 V | `build_search_context` 지역 `offset_start_targets` → `start_intervals` extras → `iv_context` `StartView.sigma_targets_v`(추가) → `matching_bounds` | 함수 실재 확인(`absolute`를 Σ_t로 바꾸는 자리 `:107`·`:123`) |
| `SearchContext` 입력 참조 슬롯 하나(`derived`) | `class SearchContext` `search_context.py:47`, `__init__` `:51`, `driving` property `:128-129` | -- | -- | `build_search_context` → 생성자 키워드 | 실재 확인(추가 자리) |
| `run_id`에 중복 판정 키 -- `find_front` 명시 인자(V11) | `def find_front(sctx, given_starts)` `E/search/find_front.py:64`; `run_id = fp_of((sctx.context_fp, ...))` `:131`(다른 소비자 0); 엔진 소스 호출 0(docstring 3곳), test·하네스 호출 14파일(grep, §6.5 목록) | -- | 요구 없음: `variant_key=None` → `run_id` 지금과 비트 동일 | `PlanSession.run_variant` → `find_front(sctx, starts, variant_key=key)` → `run_id` 튜플 끝 | 실현 가능 확인(호출 갱신 = 같은 변경의 test 수정) |
| 검증 출처 notes rows | `notes.append({"verdict": "verified_by", ...})` `find_front.py:83-85`; 표 `E/metrics/verified_by.py:44-45` | -- | -- | `find_front` notes → 결과 JSON notes | 실재 확인(rows 칸 추가 자리) |
| 진단 표지 참조 | 보고서 `diagnostic` `E/pipeline/stage_b.py:129`, skipped 분기 False `:140-142`, `run_stage_b` `:134` | -- | -- | `run_variant` → `run_stage_b` → `report_paths[0]` → 결과 JSON `stage_b_report` | 실재 확인 |
| 세션 생성 = `open_run` | `open_run()` `E/search/open_run.py:15-17`; `run_stage_a(..., donors, counters, ...)` `E/pipeline/stage_a.py:206` | -- | -- | `open_plan_session` → `open_run` → `run_stage_a` | 실재 확인. card C 서명 순환 점검은 **미확인**(§18.4 'open_run 점검') |
| 평가 결과 열거(하네스 대체) | `S3Index` 메서드 `find`·`register`·`find_failure`·`register_failure`·`entry_count` `E/search/s3_index.py:17-52` -- 평가 키 부분·열거 없음 | -- | -- | 열린 세션 `block_index` → (열거 API) → 하네스 기록 | **미확인 -- 멈춤(PS-7, U17 ② design)** |
| 결과 JSON 참조 칸(출력 기록 규칙) | spec 섹션 지문 `_section_fps` `E/authoring/spec_model.py:324-335`(v0.2 기준 줄, 착수 재측정) | -- | `requirement.ref` = `"human.offset_requirement"` | `close` → `<회로>.run_plan.json` | 칸 형식은 새로 만듦, 출처 함수 줄은 재측정 대기 |

---

## 19. 원문 근거

보관 위치 `skills/analog-gmid-design/assets/technique/sources/<폴더>/source.pdf`. 쪽은 PDF 쪽, 원문 수치 인용 없음. trim 원문은 OT §19가 정본.

| R | 원문 | 웹 | 로컬 PDF | 쪽·위치 | 쓰는 곳 |
|---|---|---|---|---|---|
| R1 | Y. Zhou, A. Kay, 'Offset Correction Methods: Laser Trim, e-Trim, and Chopper', TI SBOT037A, 2017 | [ti.com/lit/SBOT037](https://www.ti.com/lit/SBOT037) | `assets/technique/sources/offset_trim__zhou_2017/source.pdf` | p.1 e-Trim, p.2 Fig.3·Table 1 | §8 compare 한계 문구, 1/f 공통 판정 근거 |
| R2 | A. Kay, 'Op Amp Offset Voltage and Bias Current Limitations', TI SBOA590, 2024 | [ti.com/lit/pdf/sboa590](https://www.ti.com/lit/pdf/sboa590) | `assets/technique/sources/offset_trim__kay_2024/source.pdf` | §1.2 PDF p.7 Figure 1-8 문단 | §8 drift 한계 문구 |
| R3 | H. M. von Staudt, 'Trim DAC Design with Minimum DNL for Self-Trim with Self-Test Schemes', IEEE IMS3TW 2011 | [doi:10.1109/IMS3TW.2011.34](https://doi.org/10.1109/IMS3TW.2011.34) | `assets/technique/sources/offset_trim__staudt_2011/source.pdf` | p.1-2 §II.A | §4.3 k를 trim 보정 구간 배수로 함께 쓰는 근거 |

matching 판정식은 사용자 결정 S-1의 식이고(판정 위치 분리는 O-53 A2), σ_in·V_id*의 정의는 gain-budget DEC-23이다.
