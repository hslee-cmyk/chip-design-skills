---
template: design
version: 0.2.1
plan: ../../01-plan/features/offset-strategy.plan.md
plan_version: 0.6.1
---

# offset-strategy Design Document (card OS-0)

> **Summary**: 승인된 계획 `offset-strategy.plan.md` v0.6.1(사용자 결정 S-1~S-12, T-34~T-37, O-1)을 엔진 `gmid_engine` 설계로 옮긴다. 계획 N10.3의 G-S1~G-S6을 닫고, 요구 스키마(판정 온도 범위 칸 포함)·로더 사유 코드, 실행 계획 `RunPlan`·`build_run_plan`, 실행 계획 세션과 그것을 쓰는 얇은 진입 `run_plan`(엔진 사슬 진입점 정본, W-1), 변형 유도 제약의 별도 입력 `derived`(PD-1), 결과 JSON 칸, 하네스 노출 목록, 비교 도구, 예산 식, OS-V(matching 오라클 측정)·OS-L(실행 중 변형 추가)의 형식, 파일 분할, 배선표, test 목록, card별 완료 조건을 정한다. offset-trim design(OT)과 40 design의 개정안, trim 시험 회로 spec 재작성안, OS-2 검증 fixture를 함께 낸다.
>
> **Project**: chip-design-skills (analog-gmid-design skill) · **Author**: Claude Code (design 작성자 역할)
> **Status**: design v0.2 (2026-10-16). v0.1(`aef46c7`)이 계획과 다르게 간 점은 계획 v0.5~v0.6.1이 PD-1~PD-9·W-1·F-1·V-1로 받아 사용자 승인을 받았고(S-8~S-11), 이 판은 그 승인 문언과 v0.1 독립 검증(82점)의 차단 B-1·B-2를 반영한다. 계획에 없는 결정은 오케스트레이터 기본안(§18.1)으로 표시했고, 계획과 다른 결정은 두지 않았다(S-7). 독립 검증·사용자 승인 전이다. 경위는 [offset-strategy.design.history.md](offset-strategy.design.history.md).
> **기준**: 코드 인용은 master `194981f`(worktree `wt/ostrat-design-r2`)의 `파일:줄`이다. 엔진 코드는 `d783efe` 이후 바뀌지 않았다(`git diff --stat d783efe 194981f -- skills/analog-gmid-design/gmid_engine` 0). `E/` = `skills/analog-gmid-design/gmid_engine/`, `O/` = `skills/analog-gmid-design/tools/spice_oracle/`. design 인용은 `OT §x`(`offset-trim.design.md` v0.2, T-18), `40 §x`, `41 §x`. 다른 계획 인용은 `OTP Nx`(offset-trim 계획 v0.5.5, 브랜치 `trim-plan-r1` `e8b58cd`, 사용자 승인 T-34~T-37), `OPP Nx`(oracle-portability 계획 v0.4.2, master `d579939`, 사용자 승인 O-1).
> **전제**: 구현은 XRUN-F1 card A·B·C 병합 뒤다(S-4). 이 기준에는 card A·B·C가 없다(`E/search/s3_index.py`·`search_ceiling.py`·`search_stop.py` 없음). 그래서 이 문서는 40 §2.4.4~§2.4.14의 병합 뒤 구조를 전제로 쓴다.

---

## 0. 문서 안내

* **담는 것**: 규칙, 정의, 값 형식, 함수 서명, 사유 코드, 결과 JSON 칸, 노출 목록, 파일 분할, 배선표, test 목록, card별 완료 조건, 다른 문서 개정안.
* **담지 않는 것**: 경위, 검토 과정, 대안 비교의 세부, 버전 이력(history), 수치 상수. 값은 spec 선언, 단위 어휘(`E/core/units.py`), 엔진 해석값, LUT, PDK 선언에서만 온다. 예외는 사용자가 결정한 fixture 값이고 출처와 함께 적는다(계획 N0).
* **이름 원칙**: 규칙에 회로·소자·넷 이름을 쓰지 않는다. 회로 이름은 사실 표와 fixture·측정 대상에만 나온다.
* **용어**: 계획 N0.1 그대로. 이 문서가 더하는 용어는 아래다.

| 용어 | 정의 |
|---|---|
| 유도 제약 | 요구에서 엔진이 만든 판정 제약. spec `constraints`와 따로 두는 별도 입력 `derived`(PD-1). 값 형식 `OffsetBound`(§3.4) |
| 합성 행 | 두 metric 결과를 읽어 만드는 제약 행 하나. matching 유도 제약의 행 `req:offset_matching<=`(§3.1) |
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
| T-34 | 판정 온도 범위 = T-14 범위, spec 한 곳 선언, 모든 소비자가 참조(숫자 사본 금지), 위치 = 요구 안 칸 | §4.1 |
| T-35 | OTP D-24 안 B: 반복 = 같은 실행 안 변형, D-19 반복 상한 = 실행 설정(기본값 없음) | §13 |
| T-36 | OTP D-20 (가), D-25 (c)+(c-2): 출처 무결성, 대조 주체 = 엔진 밖 구동기, 엔진에는 통과한 값만 | §13(인터페이스 서명을 닫는다) |
| O-1 | oracle-portability: 오라클 MC = 시뮬레이터·PDK 네이티브 MC, 크기 확인 = TR-7 엔진 σ 대 오라클 MC σ | §12 |
| 원래 취지 | "계산 재사용은 처음 topology를 실행할 때는 항상 계산하고 그 계산된 값이 나머지 최적화를 진행할 때 재사용되게 한다는 것이 원래 취지였어" | §3.2, §5.3, §6.3, §13 |

**이어받는 결정**: U-89, X-7, X-12, X-17, T-2·T-7·T-8, T-15, T-19~T-23, T-24~T-28(계획 N2 표 그대로).

### 1.2 원칙과 강제 장치

| 원칙 | 강제 장치 |
|---|---|
| graph 단일 정본(NFR-S2) | 요구 값은 spec 섹션 한 곳. 유도 제약은 해석된 값 + 참조 경로(기존 `ConstraintDecl.value`·`ref` 형식, `E/authoring/spec_model.py:125-138`). 판정 온도 범위도 요구 안 한 곳(T-34). Δ_T는 변형 추가 입력 하나로만 들어온다(§13) |
| 재사용(NFR-S1, 원래 취지) | 유도 제약은 spec 밖 입력이다(§5.3). S1v·`achievability`·`constraint_classes`·`search_domain`·`start_intervals`의 입력은 변형 사이에 같다(§3.2·§6.3) |
| topology 무관(NFR-S3) | 뷰는 포트 역할에서, 기준 DC는 `DcInputs`에서, 단위는 레지스트리 단위 칸에서 읽는다 |
| fail-closed(NFR-S4) | §4.2·§13.3 사유 코드 전부 탐색 전 정지(변형 추가 거부는 추가 전) |
| 결정성(NFR-S5) | 계획 함수는 순수 함수, 처음 변형 순서 고정, 추가 변형은 추가 순서(§5.2·§13) |
| 상수 발명 금지(NFR-S6) | 합성 행 문턱·분해능·단위 환산은 정의와 단위 어휘에서(§3.1). 비교 도구에 가중치·문턱 없음 |
| 만들면 배선(NFR-S7) | §15 배선표. OS-L은 TR-TL과 같은 변경(계획 N7.2) |
| 작성자 ≠ 검증자(NFR-S8) | test 기대값은 interface card만 보고 쓴다. 완료 조건 1의 F2·F3 제외 목록은 검증자 소유 |

---

## 2. 엔진 실측 사실(`194981f`)

계획 N3.0 F-1~F-13과 v0.1 E-S1~E-S17은 이 기준에서도 같다(엔진 코드 무변경). 아래는 v0.2에 쓰는 사실이다.

| ID | 사실 | 근거 |
|---|---|---|
| E-S1 | offset metric 셋의 레지스트리 단위는 `mv`, view_kind는 `transfer`. 레지스트리 metric은 계산된 값 묶음의 필드 하나다 | `E/metrics/registry.py:5-6, :56-58` |
| E-S2 | view를 적지 않은 transfer metric 제약은 로더가 기본 포트 뷰를 받는다. 정해지지 않으면 `view_required` | `E/authoring/spec_constraints.py:198-204`, `E/authoring/spec_views.py:69-84, :171-184` |
| E-S3 | library offset 제약은 view를 적지 않는다 | `assets/library/current_reuse_telescopic_ota.sizing_spec.json:226-243` |
| E-S4 | σ_in·V_sys 계산은 요청 `ViewDecl`로 `view_system`을 직접 쓴다(S1v 씨앗 불필요) | `E/metrics/offset_analysis.py:56-57`, `E/metrics/offset_systematic.py:31-33` |
| E-S5 | `offset_sys_mv` = \|오차\|/\|A_dm\|(mv). 단일 출력 기준 = `targets`의 출력 넷 값, 없으면 `reference_undeclared` | `E/metrics/offset_systematic.py:42-47, :55` |
| E-S6 | `dc_inputs_from_spec`은 결정 대기 노드 목표를 '미선언'으로 투영하고, `metrics_aux`의 `targets`가 그 `node_targets`다 | `E/sizing/dc_inputs.py:11-12, :24-41`, `E/metrics/ss_evaluate.py:103` |
| E-S7 | `build_s1v`는 spec 전체가 아니라 `judged_constraints` tuple을 extras로 받는다 | `E/graph/s1v_build.py:39-42` |
| E-S8 | `ss_evaluate` 요청 목록은 항목의 `.metric`·`.view`만 읽는다(`MetricRequest`와 같은 두 칸) | `E/metrics/ss_evaluate.py:50-57`, `E/metrics/ss_types.py:57-61` |
| E-S9 | 커널 행 = `seal_rows + _spec_rows + ss_rows + ls_rows` | `E/search/kernel.py:130-132, :146-151` |
| E-S10 | matching L 하한 = `offset_in_sigma_mv <=` 최솟값 × `MILLI` / √2 | `E/search/iv_context.py:89`, `E/search/iv_matching_l.py:107, :123` |
| E-S11 | mv → V 정본 = `core.MILLI` | `E/core/units.py:13, :22`, 함수 레지스트리 §15 |
| E-S12 | 값 있는 판정 제약 가운데 `_OFFSET_METRICS` = (`offset_in_sigma_mv`, `offset_excess`) 둘이 있을 때만 LUT mismatch 데이터를 필수로 확인한다. `offset_sys_mv`는 대상이 아니다(mismatch 데이터를 쓰지 않는다) | `E/search/search_context.py:153, :164-168` |
| E-S13 | 제품 사슬 진입점이 없다. 사슬은 test 하네스가 만든다 | `E/pipeline/__init__.py:1-4` |
| E-S14 | `run_stage_a(topology_path, spec_path, lut, *, output_dir, supplies_v=None, structure_path=None)`, 결과 칸 `exit_code·status·report·report_paths·s1·spec·code_fp` | `E/pipeline/stage_a.py:83-95, :199` |
| E-S15 | `find_front`의 `run_id` 지문과 검증 출처 목록 | `E/search/find_front.py:97, :142` |
| E-S16 | 참조 제약의 `judged`는 참조 해석(`resolve_spec_references`)에서 정해진다. 로더는 그 뒤 최종 거부를 한다 | `E/authoring/spec_constraints.py:263-265`, `E/authoring/spec_load.py:142-145` |
| E-S17 | 검증 출처 표: `offset_in_sigma_mv` = `spice_oracle`(measure `offset_in_sigma_mv`), `offset_sys_mv` = `spice_unverifiable`. 레지스트리 metric마다 표 행이 있어야 한다(없으면 `KeyError`) | `E/metrics/verified_by.py:12, :44-45` |
| E-S18 | **하네스 사슬과 읽는 값**(전수, B-1): `nfr4_run_dump.py`는 (1) `find_front` 모듈 속성 `layer0_start`·`sweep_front`를 감싸 관찰(:314-329) (2) `run_stage_a(...)`(:377) 뒤 `a.code_fp`·`a.report_paths[0]`·`a.status`·`a.s1.snapshot.fp`(:378-384) (3) `LutMemo` 크기 인자를 정해 만들고(:386) `run_stage_b(a, memo, pdk, output_dir, diagnostic=True, settings)`(:387) 뒤 `b.report_paths[0]`·`b.s1.snapshot.fp`·`b.status`(:388-392) (4) 둘 다 `ok`일 때만 커널 컨텍스트 → `build_search_context(kctx, a.spec, settings, s3 루트, pdk, rule, code_fp=a.code_fp)`(:397-400) → `sctx.domain.w_min_m`·`sctx.dc.base`(:401-402) → `find_front(sctx, [])`(:404) → `fr.perf`·`fr` 전체(:406-413) → `sctx.cache.values()`의 `seq`·`evaluation.snapshot`(:414-420) → `sctx.context_fp`로 S3 폴더의 evals·runs 줄(:421-426) (5) 탐색하지 않았으면 S0 스냅샷 = `b.s1` 또는 `a.s1`의 스냅샷(:427-428) | `E/tests/integration/nfr4_run_dump.py:314-428` |
| E-S19 | **수작업 사슬을 가진 test**(2026-10-16 grep `run_stage_a`·`run_stage_b`·`build_kernel_context`·`build_search_context`·`find_front(` 호출 수): 전체 사슬(A → B → 커널 → 탐색 → `find_front`) = `tests/integration/nfr4_run_dump.py`, `test_no_s0_files_written.py`, `test_rerun_s3_independence.py`. 탐색 컨텍스트까지의 부분 사슬(뒤에 층 0 등 내부 함수를 직접 부름) = `test_layer0_boundary_rows.py`, `test_s0_layer_9circuits.py`, `search/u13_hand.py`, `search/u13_real.py`. 단계 B 없는 사슬 = `search/test_cell_floor.py`, `core/test_blas_env.py`(진입점 재확인 test) | grep 결과 |
| E-S20 | 오라클 measure 이름은 `O/oracle_compare.py` MEASURES의 키다(엔진은 이름만 든다). 오라클 재구성 뒤 측정 정의는 오라클 코어 `O/core/`에 있다(OPP N0.1·N3.1) | `E/metrics/verified_by.py:36-38`, OPP N0.1 |

---

## 3. G-S1~G-S6

### 3.1 G-S1 matching 합성 판정

**형식(오케스트레이터 기본안 OB-1, 계획 XS-10·PD-4 범위)**: 새 metric을 만들지 않는다. `ss_constraint_rows`에 인자 `bounds`를 더해 합성 행을 만든다. 근거: (1) metric은 계산된 묶음의 필드라 k(spec 값)를 넣으면 metric 블록 입력이 판정 값에 의존한다(E-S1). (2) 합성 행은 이미 요청되는 두 결과만 읽는다(새 블록·재계산 없음). (3) 레지스트리·`verified_by` 이름 공간을 바꾸지 않는다.

| 항목 | 규칙 |
|---|---|
| 요청 | `MetricRequest(b.sigma_metric, b.view)`, `MetricRequest(b.sys_metric, b.view)`. 커널이 `sctx.ss_constraints`와 함께 `ss_evaluate`에 넘긴다(E-S8) |
| 값 | v = k·σ + \|V_sys\|(V). σ = `sigma_in_mv`·u, \|V_sys\| = `sys_mv`·u |
| 문턱 | L = b.limit_v(요구 `offset_in_max_v`). OS-L 뒤 Δ_T가 있으면 L = OTP G-9 문턱 합성 함수(spec 참조 − Δ_T 입력)의 값이고, 합성은 이 행 계산 한 곳에서만 부른다(OTP NFR-T3, §13.2) |
| 분해능 | s = k·s_σ + s_sys, s_x = max(결과 `resolution`, 그 metric 모델 오차 선언)·u. 선형 오차 전파 상계이고 기존 ss 행 규칙(`E/search/ss_constraints.py:15-18, :82`)을 항마다 쓴 것이다 |
| 행 | 이름 `req:offset_matching<=`, c = (L − v)/s, `active` = c ≤ 1 |
| 봉인 안 된 점 | 미측정 (`offset_matching`, `<=`, `ss_requires_sealed_snapshot`) |
| 정의 불가 | σ·V_sys 중 None이면 미측정, 사유 = 두 결과 `Undefined` 코드 합집합 정렬 `+` 연결 |
| 분해능 없음 | **항마다** 판정한다(기존 ss 행 규칙을 항 단위로 그대로, `E/search/ss_constraints.py:79-85`): 어느 항이든 결과 `resolution`이 None이면 행 없이 미측정 `resolution_undefined`. 어느 항이든 s_x = 0(resolution 0이고 그 metric 모델 오차 선언 없음)이면 **다른 항이 양수여도** 행 없이 미측정 `resolution_zero_model_error_undeclared`. 근거: 한 항의 분해능을 모르는 채 다른 항 분해능만으로 c를 정규화하면 그 항의 불확실성을 0으로 두는 것이 되어 기존 규칙(그 metric 단독이면 미측정)보다 약해진다(fail-closed, OB-28) |
| 일찍 끝나는 분기 | 지금 `ss_constraint_rows`는 `if not declared: return (), ()`로 끝난다(`E/search/ss_constraints.py:63-64`). 요구는 있고 사용자 ss 제약이 없는 spec에서 합성 행이 빠지므로 이 분기를 `if not declared and not bounds`로 바꾼다. 봉인 안 된 점 분기(:65-66)는 bounds의 미측정 줄도 함께 낸다 |
| 보고 칸 | 행과 함께 (v, L)을 `EvalResult`의 합성 행 보고 칸에 둔다(결과 JSON이 옮겨 쓴다, §8. 다시 계산하지 않는다, OB-13) |

* **단위(OB-2)**: 항 단위는 레지스트리 서명 단위 칸에서 읽고, `mv`이면 u = `core.MILLI`(E-S11). 그 밖 단위는 유도 제약을 만들 때 L5로 거부한다. 숫자 1000·0.001을 새로 쓰지 않는다.
* **view 출처(OB-3)**: 기본 포트 뷰. 사용자 offset 제약이 view를 적지 않을 때와 같은 규칙이다(E-S2·E-S3). 로더가 `default_views(topology, feedback).port`로 정해 `OffsetRequirement.view`에 담고, 정해지지 않으면 L3. 요구 섹션에 view 키는 없다.
* **S1v(OB-4, PD-3 근거)**: 유도 제약은 S1v 씨앗·`build_s1v` extras 밖이다(E-S4·E-S7). 그래서 같은 topology 변형끼리 S1v 입력이 같다. DS-2는 '대상 없음'으로 닫혔다(PD-3, S-8). 유도 제약이 뷰 씨앗을 요구하게 되면 DS-2를 다시 연다.
* **이름**: 행 접두 `req:`, 몸통 `offset_matching`은 방식 이름이다(새 이름 충돌 0, v0.1 E-S17).

### 3.2 G-S2 matching 출발값

* **규칙(OB-5)**: 출발값 σ 목표 집합 Σ_t(V) = {사용자 판정 제약 `offset_in_sigma_mv <=` 값 × `MILLI`} ∪ {유도 제약마다 b.limit_v / b.k}. matching L 하한 σ_share = min(Σ_t)/√2(`E/search/iv_matching_l.py:123`의 `min(absolute) * MILLI`를 `min(Σ_t)`로). 두 경로는 로더가 함께 두지 않는다(L2).
* **L/k인 근거**: k·σ_in + \|V_sys\| ≤ L, \|V_sys\| ≥ 0이므로 σ_in ≤ L/k는 필요조건이다. 몫을 나누는 비율을 만들지 않는다. 출발값 전용이다.
* **Δ_T와 무관(OB-20)**: 출발값은 요구 값 L(= `offset_in_max_v`)만 쓰고 Δ_T가 들어간 문턱을 쓰지 않는다. 근거: 문턱 합성은 제약 행 한 곳에서만 한다(OTP NFR-T3). 그 결과 `start_intervals` 입력이 반복 사이에 같아 S0 수준 블록이 모두 색인 적중이다. 이 사실을 OTP G-12 '문턱에 의존하는 블록' 목록의 입력으로 알린다: **matching 쪽 S0 수준 문턱 의존 블록 없음**(문턱은 커널 안 합성 행에서만 읽힌다).
* **전달 형식**: `start_intervals` 블록 extras에는 `OffsetBound` 전체가 아니라 (k, limit_v) 쌍 tuple `offset_start_targets`만 넣는다(`build_search_context`가 `derived`에서 만든다). 그래서 Δ_T 칸(OS-L)이 바뀌어도 이 블록 입력은 같다.
* **요구 없는 spec의 비트 동일**: 양의 계수 곱은 단조라 min(vᵢ·`MILLI`) = min(vᵢ)·`MILLI`.
* **바뀌는 곳**: `E/search/iv_context.py`(`StartView.sigma_targets_v`), `E/search/iv_matching_l.py`(:107·:123), `E/search/start_intervals.py`(:253 extras), `E/search/search_context.py`(:195 호출).

### 3.3 G-S3 변형 정체(OS-5 형식, OS-L 확장)

| 이름 | 정의 |
|---|---|
| `constraint_set_fp` | `fp_of((spec 섹션 지문 'constraints_fp', derived 중 Δ_T 칸을 뺀 형태, trim_decl.decl_fp 또는 None))` |
| `variant_fp` | `fp_of((토폴로지 변형 connectivity_fp, constraint_set_fp, 반복 번호, 원인 지문))`. 반복 번호 = 처음 목록 0, 추가될 때마다 1씩(계획 N3.12). 원인 지문 = Δ_T 입력 지문(처음 목록은 None) |
| 중복 | 같은 `variant_fp`가 계획에 두 번이면 처음 목록은 `ValueError`(계획 함수 결함), 추가는 L-A6 거부(§13.3) |
| S3 칸(XS-13) | evals·runs 줄 최상위 키 `variant` = `variant_fp`. **OS-5에서 구현**(계획 XS-13·N7.2 배정 그대로). 싣는 조건 = 계획의 변형이 둘 이상이거나 반복 번호가 1 이상인 변형(OS-L). 변형 하나인 실행(요구 없음, OS-2 matching 단일 변형)은 칸이 없다 -- 그 실행의 줄은 S3 폴더·runs 줄 `run_id`(§6.5, 유도 제약 지문 포함)와 evals 행 이름 `req:`로 구분된다. 요구 없는 실행의 줄은 그대로(완료 조건 1) |
| `run_id` | §6.5 |

### 3.4 G-S4 유도 제약 기록 형식

`OffsetBound`(search 값 모듈 `E/search/search_values.py`, frozen dataclass):

```python
OffsetBound(name: str,              # "offset_matching"
            sigma_metric: str,      # "offset_in_sigma_mv"(레지스트리 이름)
            sys_metric: str,        # "offset_sys_mv"
            k: float,               # 요구 coverage_multiple 의 해석된 값
            limit_v: float,         # 요구 offset_in_max_v 의 해석된 값
            view: ViewDecl,         # OffsetRequirement.view
            refs: tuple,            # (("k", "human.offset_requirement.coverage_multiple"),
                                    #  ("limit_v", "human.offset_requirement.offset_in_max_v"))
            source_fp: str)         # 요구 섹션 지문
```

* OS-L이 칸 `margin`(Δ_T 입력, 값과 지문, None이면 없음)을 더한다(§13.2). OS-2에서는 빈 자리를 미리 만들지 않는다(계획 N3.11 '순서').
* 결과 JSON에는 같은 칸 이름으로 싣는다(§8).
* trim 국면 2 유도 제약은 OT §10.6대로 `trim_decl`에서 만든다(`OffsetBound` 아님). k·V_res 출처만 §17.1로 바뀐다.

### 3.5 G-S5 S1v 계산 수 칸(사실 확인용)

`run_plan.shared.s1v_computes` = 실행 계획 안 S1v 블록(`s1v_fields` writer) `computes` 합, `s1v_inputs` = S1v 블록이 계산된 서로 다른 입력 버전 수(`RunCounters.snapshot()`에서). DS-2가 닫혔으므로(PD-3) 결정 근거가 아니라 '같은 topology 변형끼리 S1v 입력이 같다'의 확인용이다(완료 조건 4의 근거 칸).

### 3.6 G-S6 완료 조건 1의 비교 제외(PD-5 반영, 목록은 검증자 소유)

비교 = 요구 없는 실행. base = XRUN-F1 card C 병합 뒤 master의 수작업 사슬(E-S18 하네스와 같은 인자·같은 진단 설정, 계획 N7.2 'v0.5 반영'), 대상 = OS-2 병합본의 `run_plan`. 같은 실행 환경, E_B 선언(40 §2.4.13 1차 검사 전제).

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

* matching `OffsetBound`(같은 파일 비공개 함수): `name` = `offset_matching`, metric 이름은 레지스트리 이름, k·limit_v·view·refs·source_fp는 `spec.offset_requirement`에서.
* 처음 순서는 표 순서 고정(DO-3). 변형 정체 중복이면 `ValueError`(§3.3).

### 5.3 변형 제약 주입(PD-1, S-8)

로드한 spec 객체 하나를 모든 변형이 같이 쓰고, 변형의 유도 제약만 `build_search_context(..., derived=...)`로 넣는다. spec 사본을 만들지 않는다. `derived`를 읽는 곳은 셋뿐이다.

| 소비자 | 읽는 방식 |
|---|---|
| 커널 요청·합성 행(§3.1) | `SearchContext.offset_bounds`(참조 칸 `derived`, `driving`이 `spec.driving_spec`을 읽는 방식과 같다, `E/search/search_context.py:129-131`) |
| 출발 구간(§3.2) | `start_intervals` extras `offset_start_targets` = ((k, limit_v), ...) |
| LUT mismatch 필수 검사(E-S12) | `derived`가 비지 않으면 같은 검사(합성 행의 σ 항 `offset_in_sigma_mv`가 mismatch 데이터를 쓴다. V_sys 항은 쓰지 않으므로 검사 근거는 σ 항이다) |

그래서 S1v·`constraint_classes`·`search_domain`·`achievability`·`start_intervals`의 입력은 같은 topology 변형 사이(그리고 OS-L 반복 사이)에 같다.

---

## 6. 실행 계획 세션과 `run_plan`(W-1, XS-17)

### 6.1 세션(`E/pipeline/plan_session.py`)

```python
def open_plan_session(topology_path, spec_path, lut, memo, pdk_decl, lut_rule_decl, *, output_dir, settings,
                      archive_root, supplies_v=None, structure_path=None, given_starts=(), model_error=(),
                      diagnostic=False) -> PlanSession

class PlanSession:
    plan: RunPlan                                   # 지금 목록(읽기 전용, 추가 때 새 값으로 바뀐다)
    stage_a: StageAResult                           # 원본 단계 A(읽기 전용)
    def run_variant(self, index) -> VariantResult   # 변형 하나 실행(같은 index 두 번이면 ValueError)
    def add_variant(self, base_index, margin) -> PlanVariant   # OS-L(§13)
    def close(self) -> PlanResult                   # 결과 JSON을 쓰고 색인·계수를 놓는다
```

* **열기**(실행 경계, XS-7): `S3Index`(블록 결과 부분)와 `RunCounters`를 여기서 한 번 만든다. 원본 단계 A `run_stage_a(..., donors=, counters=)`를 돈다(`donors`·`counters` 필수 키워드, PD-8. 빠지면 `TypeError`). 결과에 칸 `topology`(로드한 `TopologyDoc`)를 더한다. 단계 A가 spec을 로드했으면 `build_run_plan(stage_a.spec, stage_a.topology)`(TR-2부터 `approvals`)로 처음 목록을 만든다. 계획 함수 거부(`SchemaRejectedError`)는 세션을 '거부 상태'로 열어 두고(`plan` = None, 사유 기록) `close`가 결과 JSON에 쓴다 -- 변형 실행은 0이다.
* **변형 실행 `run_variant(i)`**:
  1. 단계 B: 변형마다 `run_stage_b`를 부른다. 별도 pipeline 수준 캐시(토폴로지 지문 키 사전)는 두지 않는다(검증 N-7): 재사용 경로는 블록 결과 색인 하나이고(단계 B 블록은 입력이 `derived`와 무관해 같은 토폴로지 변형끼리 모두 색인 적중), 두 번째 재사용 경로를 만들지 않는다. OS-2는 변형이 하나라 한 번 부른다. `diagnostic`은 그대로 넘긴다: `run_stage_b(stage_a, memo, pdk_decl, output_dir=, settings=, diagnostic=diagnostic)`(`E/pipeline/stage_b.py:134` 서명 그대로, 진단 뜻 = 측정만, 단계 A 상태·exit code 유지).
  2. **탐색 조건**: 단계 A `ok`이고 단계 B `ok`일 때만 커널 컨텍스트 → `build_search_context(kctx, stage_a.spec, settings, archive_root, pdk_decl, lut_rule_decl, model_error, code_fp=stage_a.code_fp, derived=variant.derived)` → `find_front(sctx, given_starts)`. 아니면 `VariantResult.stop` = `stage_a_<상태>` 또는 `stage_b_<상태>`(하네스 :395와 같은 조건).
  3. `given_starts`는 원본 topology 변형에만 넘긴다(파생 topology는 θ 스키마가 달라 `()`, OB-17).
  4. `find_front`는 `gmid_engine.search` 패키지의 함수를 부른다. `find_front` 모듈 안에서 `layer0_start`·`sweep_front`를 모듈 전역 이름으로 부르는 방식(관찰 지점 계약 J-3·J-7)을 바꾸지 않으므로 하네스의 모듈 속성 감싸기가 `run_plan` 경로에서도 그대로 동작한다(E-S18 (1)).
* **닫기**: `<회로>.run_plan.json`(§8)을 쓰고, 색인·계수의 참조를 놓는다. 닫은 세션의 `run_variant`·`add_variant`는 `ValueError`.
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
| 단계 B | 한 번 | 변형마다 호출, 같은 토폴로지 변형끼리 블록은 색인 적중(계산 0). 보고서 파일은 같은 내용으로 다시 쓰인다 |
| S0 탐색 블록 | 한 번 | 같은 topology 변형끼리 모두 적중(§5.3, `start_intervals` 포함 -- §3.2) |
| S1v | 한 번 | 같은 topology 변형끼리 같은 입력 |
| 평가 캐시 | 하나 | **DS-1에 따른다**(§10). 지금 키 그대로 공유 금지 |

### 6.4 하네스 노출(B-1, W-1 요구 전수)

E-S18의 하네스가 읽거나 넘기는 값마다 `run_plan` 경로의 자리다. 새 값을 만들지 않고 이미 있는 객체의 **읽기 전용 참조**를 낸다.

| 하네스가 쓰는 것(E-S18) | `run_plan` 경로의 자리 |
|---|---|
| 입력 `lut`·`LutMemo`(크기 인자는 호출자)·`pdk`·`rule`·`settings`·S3 루트·output_dir·`given_starts` | `run_plan` 인자 그대로(호출자가 만든다) |
| 진단 모드 `diagnostic=True` | `run_plan(..., diagnostic=True)` → 단계 B에 같은 뜻으로. `PlanResult.diagnostic`과 결과 JSON `run_plan.diagnostic`에 표지 |
| `find_front` 모듈 속성 감싸기 | 그대로 동작(§6.1 4) |
| `a.code_fp`·`a.report_paths`·`a.status`·`a.s1.snapshot.fp` | `PlanResult.stage_a`(`StageAResult` 참조) |
| `b.report_paths`·`b.status`·`b.s1.snapshot.fp` | `VariantResult.stage_b`(그 변형의 `StageBResult` 참조) |
| `sctx.domain.w_min_m`·`sctx.dc.base`·`sctx.context_fp`·`sctx.cache`(card B 뒤 `S3Index` 평가 키 부분) | `VariantResult.search_context`(`SearchContext` 참조, 탐색하지 않았으면 None). 평가 결과 목록은 그 객체의 기존 읽기 경로(card B 뒤 `S3Index` 평가 키 부분의 API)로 읽는다 |
| `fr`(`SearchFront`)·`fr.perf` | `VariantResult.front` |
| 탐색하지 않았을 때의 S0 스냅샷(`b.s1` 또는 `a.s1`) | `VariantResult.stage_b.s1` / `PlanResult.stage_a.s1` |
| S3 evals·runs 파일 | `archive_root / VariantResult.search_context.context_fp`(경로 규칙 그대로) |

* 값 형식: `VariantResult(variant, stage_b, search_context, front, stop)`, `PlanResult(plan, stage_a, variants, rejected, diagnostic, perf, report_path, exit_code)`(`E/pipeline/run_plan_values.py`). `perf` = 세션 전체 `RunCounters.snapshot()`.
* **대체 범위(OB-22)**: 계획 W-1이 대체 대상으로 적은 것은 전체 사슬(`run_stage_a` → `run_stage_b` → `build_kernel_context` → `build_search_context` → `find_front`)이다. 그래서 E-S19의 전체 사슬 셋(`nfr4_run_dump.py`, `test_no_s0_files_written.py`, `test_rerun_s3_independence.py`)을 같은 변경에서 `run_plan`으로 바꾸고 옛 수작업 사슬을 지운다. 탐색 컨텍스트까지만 만들고 내부 함수(층 0 등)를 직접 부르는 부분 사슬 test와 진입점 재확인 test는 단계 함수의 단위 시험이라 이 대체 범위에 넣지 않는다. 이 범위 해석은 §18.4 Q-1로 확인받는다.

### 6.5 `run_id`(OB-11)

`find_front`의 `run_id` 지문 tuple 끝에 `sctx.offset_bounds`가 비지 않을 때만 `fp_of(sctx.offset_bounds)`를 더한다(`E/search/find_front.py:142`). 비면 지금 식 그대로(완료 조건 1). OS-L 반복 변형은 `margin`이 `OffsetBound` 안에 있으므로 반복마다 `run_id`가 다르다.

### 6.6 정지 처리

예외를 삼키지 않는다. 단계 A·B는 지금처럼 보고서와 exit code(`E/pipeline/stage_a.py:97-101`, `E/pipeline/stage_b.py:128-131, :146-150`). 계획 함수 거부는 이름으로 `SchemaRejectedError`만 받아 `PlanResult.rejected`(`exc.record.to_json()`)와 exit code에 싣는다. 넓은 `except` 없음.

---

## 7. 예산

### 7.1 변형별 E_total(XS-12)

* E_total,v = E_B + N_T + R_v, R_v = 2 × `len(sctx_v.domain.variables)`(X-17, 40 §2.4.9). E_B는 `SearchSettings.eval_budget`(모든 변형 같은 선언값). 선언이 없으면 변형마다 유도(card C `search_ceiling`).
* 실행 계획 전체 상한 = Σ_v E_total,v. 벽시계 정지는 변형마다(`E/search/find_front.py:81`). 추가 변형도 자기 E_total,v를 받는다(계획 N3.7).
* 반복 수 상한 = OTP D-19 실행 설정 선언값(T-35, 기본값 없음). 선언이 없으면 추가가 없다. 이 값은 구동기가 읽고 세션은 받지 않는다(세션은 추가 요청마다 §13.3 검사만 한다).

### 7.2 DS-U9 조사 결과(열림 유지)

계획 순서·구성과 무관하면서 '계획 안 = 단독' 비트 동일을 주는 시간 유도 규칙은 없다. 비트 동일의 전제가 'E_B 선언'이기 때문이다(40 §2.4.13 1차 검사 전제 (가)). 후보 넷(자기 첫 n_θ + 1 평가, 첫 변형 유도값 공유, 블록 적중 시간 환산, 사전 단독 시험 평가)은 모두 조건 2를 줄 수 없다(history H2). 결정 S-6대로 유도 실행은 조건 2·NFR-S5·조건 9 셋째 항목에서 빼고, `run_plan.notes`에 `{"verdict": "budget_derived", "meaning": "derived_budget_may_differ_from_standalone"}`를 싣는다.

### 7.3 색인 상한과 B_S0(PD-7)

* 상한 = Σ_블록 분할 수 × (Σ_v E_total,v + B_S0). 변형 하나·S0 한 벌이면 40 식 그대로다.
* B_S0 = 변형 수 + (국면 2 계획에 원본 topology 변형이 없으면 구조 비교용 원본 S0 한 벌). 실행 전에 계획만으로 계산되고 '서로 다른 S0 입력 수'보다 크거나 같다(안전 쪽, PD-7).
* **card C `S3Index` 인터페이스**(OS-5): 생성자에 필수 인자 `s0_sets`(B_S0)를 더하고, 변형마다 정해진 E_total,v를 등록하는 메서드 `add_eval_ceiling(e_total)`을 더한다. 등록 시 상한 검사(40 §2.4.5 fail-closed (5))는 그 합을 쓴다. card C test를 같은 변경에서 고치고 기본값 인자로 피하지 않는다.
* **OS-L**: 변형이 추가되면 세션이 `S3Index.grow(s0_sets=1)`로 B_S0를 하나 늘리고 그 변형의 E_total,v를 `add_eval_ceiling`으로 더한다('늘리는' API, 계획 N3.7). 줄이는 API는 없다.
* 결과 JSON: `run_plan.shared.block_index_entries`·`block_index_bound`·`b_s0`. 각 변형 runs 줄 `perf.block_index_bound`에도 그때의 계획 전체 값을 싣는다.

---

## 8. 결과 JSON 칸(`<회로>.run_plan.json`, 최상위 키 `run_plan`)

| 칸 | 내용 | card |
|---|---|---|
| `strategy`, `phase`, `diagnostic` | 계획 값·진단 표지 | OS-2 |
| `requirement` | `{offset_in_max_v, coverage_multiple, strategy, view, judgment_temperature_range_c, sources}` 또는 null | OS-2 |
| `rejected` | 계획 함수 거부 사유(`exc.record.to_json()`) 또는 null | OS-2 |
| `variants[]` | `{index, label, iteration, cause_fp, topology_fp, variant_fp, derived: [OffsetBound 칸], budget: {eval_budget, eval_budget_source, e_total, gate_reserve}, stage_a_status, stage_b_status, run_id, s3_dir, stop, front_points}` | OS-2(OS-5·OS-L에서 여러 개) |
| `variants[].front_points[]` | `{point_id, power_w, area_m2, derived_rows: [{name, c, active, value_v, limit_v, margin_v}]}`. `margin_v` = limit_v − value_v(보고). 값은 커널 결과의 합성 행 보고 칸을 옮겨 쓴 것 | OS-2 |
| `variants[].memory` | OS-L: 그 변형 끝의 색인 항목 수, 프로세스 최대 메모리(XS-19) | OS-L |
| `shared` | `{block_index_entries, block_index_bound, b_s0, s1v_computes, s1v_inputs, kernel_calls_total}` | OS-2(OS-5 다변형 의미) |
| `notes[]` | matching 변형이 있으면 `{"verdict": "final_acceptance_is_oracle_range_judgment"}`(계획 N3.11 '합격 표기', T-29). `budget_derived`(§7.2). compare 국면 1이면 `{"verdict": "not_a_recommendation"}`와 R1·R2 한계 문구. 합성 행 검증 출처 `{"verdict": "verified_by", "rows": [["req:offset_matching", 종류, 항 metric별 종류]]}`(§12) | OS-2 / OS-5 / OS-V |

* 권고·판정 문장은 싣지 않는다(FR-S7).

---

## 9. 비교 도구(OS-3)

* **위치(DO-7, OB-14)**: `skills/analog-gmid-design/tools/offset_compare/`(`compare.py` 진입점 `compare_offset_results(result_paths) -> ComparisonTable` + CLI `main(argv)`, `README.md`, `tests/test_compare.py`). 엔진 import 0(AST test). 엔진은 이 도구 출력을 입력으로 받지 않는다.
* **입력**: `<회로>.run_plan.json` 둘 이상(국면 1의 matching 변형, 국면 2의 trim 변형).
* **칸**: 출처(경로, `run_id`, `code_fp`, `variant_fp`, label, iteration), 공통 판정 선언(1/f metric·op·값, `area_search_m2` 상한), 요구 값(`offset_in_max_v`, k, 판정 온도 범위), front 점별 (전력, 면적), offset 한계 대비 여유(matching = `margin_v`, trim = `offset_in_max_v` − `residual_bound_v`), 유도 제약 판정(c, active), 공통 판정 행 c.
* **불일치 표시**: `code_fp`·공통 판정 선언·요구 값이 다르면 표 머리에 그 사실을 쓴다.
* **금지**: 판정·권고 문장, 가중치, 문턱.

---

## 10. DS-1 조건부 절(열린 결정 -- 하나를 고르지 않는다)

DS-1은 M2 뒤 사용자가 고른다(S-5). 필요한 시점은 OS-5(compare)와 OS-L(보정 루프는 같은 θ를 다시 밟을 가능성이 크다, 계획 N3.12). 공통 전제(**이 design의 전제에서는** -- 유도 제약이 S1v 씨앗·extras 밖이고(OB-4) 요구가 있으면 사용자 판정 제약이 변형 사이에 같다(L2), 이것이 PD-3 근거다): 같은 topology 변형끼리 spec 판정 제약·S1v·S0 입력이 같고, 다른 것은 유도 제약(합성 행·그 metric 요청)과 OS-L의 문턱(Δ_T)뿐이다.

### 10.1 (가) 평가 키 부분만 변형별

* 바뀌는 곳: card B `S3Index`를 블록 결과 부분과 평가 키 부분 두 객체로 나눈다. 세션은 블록 결과 부분 하나를 모든 변형에, 평가 키 부분은 변형마다 `build_search_context`가 새로 만든다.
* 완료 조건 3: 같은 topology 변형이 같은 θ를 밟으면 같은 평가 키가 변형마다 다시 계산된다 -- 모순. **DS-U7(조건 3 약화 안 함, S-6)과 충돌**하므로 (가)를 고르려면 DS-U7도 다시 결정해야 한다(§18.3 OD-2).
* 놓기(계획 N9 메모리 행): 끝난 변형의 평가 키 부분은 다시 쓰이지 않으므로 그 변형이 끝나면 놓을 수 있다(같은 정체 재추가는 거부되므로 같은 입력이 다시 오지 않는다). 블록 결과 부분은 놓지 않는다.

### 10.2 (나) 평가 분리

* 바뀌는 곳: (i) 커널 요청 = 계획 안 모든 변형 요청의 합집합(세션이 만들어 모든 변형 `SearchContext`에 같은 값으로 넘긴다. OS-L 추가 변형은 문턱만 다르므로 요청이 같다) (ii) 평가 캐시 값(봉인·metric·spec 행·ls 행)은 변형과 무관, `S3Index` 하나를 공유 (iii) 합성 행(`req:`)은 변형별 판정 단계가 캐시 값의 묶음에서 만든다(`ss_constraint_rows`의 bounds 부분을 커널 밖 변형별 함수로 분리). `EvalResult`는 변형 무관 부분과 변형별 행으로 나뉜다.
* 이 design에서 범위: spec 판정 제약이 변형 사이에 같으므로 (iii)은 합성 행 하나다. 이 design의 전제(OB-4·L2)에서는 S1v 투영을 좁힐 대상이 없다(PD-3으로 DS-2가 '대상 없음'으로 닫힌 근거와 같다). 그 전제가 깨지면(유도 제약이 뷰 씨앗을 요구하게 되면) DS-2를 다시 연다.
* 완료 조건 3: 지킨다. S3: evals 줄은 평가 키마다 한 줄 + 변형별 행 칸 `rows_by_variant`(XS-13 범위).
* 놓기: 끝난 변형의 변형별 행은 놓을 수 있다. 공유 평가 키 부분은 놓지 않는다(다음 반복이 같은 θ를 밟으면 재사용).

### 10.3 (다) 키 분리

* 바뀌는 곳: `EvalKey`에 칸 `constraint_set_fp`와 OS-L 문턱 지문을 더하거나 `context_fp` 지문에 넣는다(`E/search/eval_key.py`, `E/search/search_context.py:214`). `S3Index` 하나를 공유한다. 요구 없는 실행은 칸을 넣지 않아 완료 조건 1을 지킨다.
* 완료 조건 3: 형식상 지킨다. 같은 θ의 커널 평가가 변형마다 남고, 크기 결정 블록은 색인 적중, offset metric 블록은 요청이 같아도(OS-L) 행이 달라 커널은 돈다(XS-8).
* 놓기: 끝난 변형 키의 평가 키 항목은 다시 오지 않으므로 놓을 수 있다. 블록 결과 부분은 놓지 않는다.

**놓기 공통 규칙**(계획 N9): 위 '놓을 수 있다'는 DS-1 결정 뒤 design 개정에서 구현 여부를 정하고 검증한다. 어느 경우든 θ 무관 블록(단계 A·S0·커널 안 크기 결정 블록)은 놓지 않는다. 메모리 한도 위험이 실측되면 사용자에게 올린다(조용히 비우지 않음).

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
| compare 다변형·공유·정체 칸·Σ 상한·공통 판정 | OS-5 | DS-1 결정 뒤. 미결이면 compare는 L6 거부 유지, trim 단독(단일 변형)만 TR-2에서 연다(OB-16) |
| 최종 비교 | OS-3 | TR-6 뒤 |

---

## 12. OS-V: matching 합성 판정의 오라클 측정(V-1, S-11)

**범위**: matching 합성 판정 k·σ_in + \|V_sys\| ≤ 문턱의 검증 출처를 붙인다. **판정 조건 하나**(LUT 측정 조건 `temp_c`·`corner` = 엔진 합격 조건)의 측정만이다. 판정 온도 범위의 온도 점으로 넓히는 몫은 offset-trim TR-TL이 맡는다(OTP TR-TL 행 '소유 경계').

**경계**(OPP O-1, oracle-portability 3층 구조):

| 층 | OS-V가 하는 일 | 하지 않는 일 |
|---|---|---|
| 오라클 코어(`O/core/`) | 측정 정의 둘: (1) σ_in -- 기존 measure `offset_in_sigma_mv`를 그대로 쓴다(네이티브 MC, O-1). (2) V_sys -- 입력 차 0에서 DC 동작점의 출력 오차(차동 = 두 출력 차, 단일 = 출력 − 선언 기준 DC)를 A_dm으로 나눈 값. 엔진 `offset_systematic`과 같은 정의(E-S5)이고 measure 이름 `offset_sys_mv`. 기준 DC 값은 오라클 입력(엔진이 넘기는 spec 노드 목표)에서 읽는다. 합성 값 k·σ̂ + \|V̂_sys\|를 코어 비교 수학으로 만든다(k는 오라클 입력의 요구 값) | 방언 토큰·PDK 이름(OPP FR-P1), MC 방법 정의(어댑터·기술자 몫), 표본 수 규칙의 새 정의(코어의 기존 표본 수 규칙을 쓴다) |
| 어댑터·기술자 | 바꾸지 않는다(DC 동작점·네이티브 MC는 이미 요구되는 능력) | -- |
| 엔진 | `E/metrics/verified_by.py` 표의 `offset_sys_mv` 행을 `spice_oracle`(measure `offset_sys_mv`)로 바꾼다. 합성 행의 검증 출처는 항 metric의 종류에서 정한다: 두 항이 모두 `spice_oracle`이면 행도 `spice_oracle`, 아니면 `spice_unverifiable`(규칙 = `find_front` notes의 `verified_by` 기록에 `rows`를 더하는 자리, `E/search/find_front.py:97`). 엔진은 오라클을 import하지 않는다 | 엔진 판정 값을 바꾸지 않는다 |

* **OS-V 전까지**: `offset_sys_mv`가 `spice_unverifiable`이므로 합성 행 검증 출처도 `spice_unverifiable`이고 결과 notes에 실행 전부터 나간다(DEC-90 (3), OT §10.6 선례).
* **크기 확인**: σ의 크기 일관은 OS-V 몫이 아니다. TR-7 §17-1의 엔진 σ_in 대 오라클 MC σ_in 비교가 맡는다(O-1 (2)).
* **모델 오차**: 오라클 대조 결과는 `model_error_offset_in_sigma_mv`·`model_error_offset_sys_mv`(DEC-72)로 기록되고, 합성 행 분해능(§3.1)이 항마다 그 값을 바닥으로 쓴다.
* **선행**: OS-2, oracle-portability 코어(OP card, OPP N5.1). OS-V는 TR-TL의 선행이다.

---

## 13. OS-L: 실행 중 변형 추가(T-35, XS-16~XS-19, TR-TL과 같은 변경)

### 13.1 서명(D-25 결정 T-36으로 닫음)

```python
PlanSession.add_variant(base_index: int, margin) -> PlanVariant
```

* `margin` = 구동기가 출처 무결성 대조(D-25 (c)+(c-2))를 통과시킨 Δ_T 입력 하나다. 형식은 OTP G-9(offset-trim design TR-0T)가 정하고, 엔진이 읽는 칸은 둘이다: Δ_T 값(V, 문턱과 같은 단위)과 그 지문. 엔진은 대조하지 않고 오라클 결과 파일을 읽지 않는다(XS-18 = X-23 수용).
* 결과: 새 `PlanVariant`(base 변형과 같은 topology·같은 `trim_decl`, `derived`의 각 `OffsetBound`에 `margin`을 단 것, `iteration` = 지금 최대 + 1, `cause_fp` = margin 지문). 세션의 `plan`이 새 값으로 바뀐다. 실행은 `run_variant(새 index)`로 따로 부른다.
* 부르는 주체는 엔진 밖 구동기뿐이다(엔진 안 search·kernel·블록은 부르지 않는다 -- 호출 grep으로 확인).

### 13.2 문턱 경로(Δ_T가 들어가는 길은 하나)

구동기 → `add_variant(margin)` → `OffsetBound.margin` → 합성 행(§3.1)이 OTP G-9 문턱 합성 함수(spec 참조 − Δ_T)를 한 번 부른다 → 행 c. spec 측정 선언 절·오라클 결과 파일 읽기·출발값(§3.2)·S0 블록으로는 들어가지 않는다. trim 변형의 문턱(V_res − Δ_T(잔여))은 OT 경로(`trim_constraint_rows`)에서 같은 합성 함수를 부르고, `margin`은 그 변형의 trim 유도 입력으로 들어간다(세부는 offset-trim design).

### 13.3 추가 허용 범위(fail-closed, 사유 코드 `run_plan_variant_add_rejected`, detail `reason`)

| reason | 상황 |
|---|---|
| `session_closed` | 닫힌 세션 |
| `session_rejected` | 계획 함수가 거부한 세션 |
| `base_unknown` | base index가 계획에 없음 |
| `no_threshold_bound` | base 변형에 문턱을 가진 유도 제약(matching `OffsetBound` 또는 trim 국면 2 유도 입력)이 없음 |
| `margin_unit` | Δ_T 값의 단위가 문턱 단위와 다름 |
| `duplicate` | 같은 `variant_fp`가 이미 있음 |

topology·사용자 판정 제약·요구·`strategy`·국면은 서명상 바꿀 수 없다(입력이 margin 하나라 base 값을 그대로 쓴다). 그래서 계획 N3.12의 '다른 topology·판정 제약 변경' 거부는 서명으로 보장되고, test는 그런 추가를 시도할 입력 자리가 없음을 확인한다.

### 13.4 예산·메모리

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

값 형식 자리: `OffsetRequirement` → `E/authoring/spec_model.py`, `OffsetBound` → `E/search/search_values.py`.

### 14.2 고치는 파일

| 파일 | card | 범위 |
|---|---|---|
| `E/authoring/spec_schema.py`, `spec_load.py`(섹션 호출, L2 자리 :142 뒤), `spec_model.py`(`OffsetRequirement`, 칸, `OPTIONAL_SECTION_GROUPS`, `_section_fps`), `spec_sources.py`, `__init__.py` | OS-2 | 부분 |
| `E/search/search_values.py`(`OffsetBound`, `EvalResult` 합성 행 보고 칸), `ss_constraints.py`(bounds, :63-64 일찍 끝나는 분기를 `not declared and not bounds`로), `kernel.py`(:130 요청, :148 bounds), `search_context.py`(`derived` 키워드·`offset_bounds`·mismatch 검사·`offset_start_targets`), `start_intervals.py`, `iv_context.py`, `iv_matching_l.py`, `find_front.py`(:97 rows, :142 `run_id`) | OS-2 | 부분(PD-4 범위: 계산 규칙 두 곳 + 전달 다섯 + 값 형식 하나) |
| `E/pipeline/stage_a.py`(`donors`·`counters` 필수, `StageAResult.topology`), `pipeline/__init__.py` | OS-2 | 부분 |
| `E/metrics/ss_evaluate.py` docstring(`MetricRequest`도 받음) | OS-2 | 문구 |
| `E/tests/integration/nfr4_run_dump.py`, `test_no_s0_files_written.py`, `test_rerun_s3_independence.py` | OS-2 | 사슬을 `run_plan`으로(옛 사슬 삭제) |
| `E/search/s3_index.py`(`s0_sets` 필수 인자, `add_eval_ceiling`) + card C test | OS-5 | 부분 |
| `E/search/kernel.py` `_record`, `find_front.py` runs 줄(`variant` 칸) | OS-5 | 부분 |
| DS-1 선택지 파일(§10) | OS-5 | 선택에 따름 |
| `E/search/s3_index.py`(`grow`), `pipeline/plan_session.py`(`add_variant`), `search_values.py`(`OffsetBound.margin`), `ss_constraints.py`(문턱 합성 호출) | OS-L | 부분 |
| `E/metrics/verified_by.py`(`offset_sys_mv` 행), `find_front.py`(notes rows), `O/core/`(V_sys·합성 측정 정의) | OS-V | 부분 |
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
| `run_plan` | 엔진 사슬 진입점 정본(W-1). 하네스·test 전체 사슬 셋(§6.4)이 같은 변경에서 부른다. U16 `run_gmid_design_pipeline`은 나중에 이것을 부른다(계약에 적는다) | 하네스·test의 수작업 사슬 |
| `ss_constraint_rows`의 bounds | `kernel.evaluate` | -- |
| `build_search_context(derived=)`·`offset_bounds`·`offset_start_targets` | `PlanSession.run_variant` | -- |
| `StartView.sigma_targets_v` | `matching_bounds` | `iv_matching_l.py:107, :123`의 mv 목록 |
| `run_stage_a(donors=, counters=)` | `open_plan_session` | card B의 '`run_stage_a`가 두 객체를 만든다'(PD-8, §17.2) |
| `PlanSession.add_variant`, `S3Index.grow` | 엔진 밖 구동기(OTP G-12) -- **TR-TL과 같은 변경**에서 병합 | -- |
| `verified_by` `offset_sys_mv` 행, notes rows | `find_front` notes | `offset_sys_mv` = `spice_unverifiable` |
| `compare_offset_results` | 사용자 CLI(OS-3) | -- |

---

## 16. card 범위·완료 조건·test

공통: design 승인 → test(interface card만) → code → 독립 판정. 완료 조건마다 (a) 배선 증거 (b) 상위 N6.3 확인 (c) gap 분석. 기능 완료 조건 번호는 계획 N7.2.

### 16.1 card

| card | 범위 | 선행 | 완료 조건 |
|---|---|---|---|
| **OS-2** | §4 L1~L6·L12, §3.1·§3.2, §5(요구 없음·matching, 거부), §6(세션·`run_plan`·노출·진단), §8(OS-2 칸), XS-7·PD-8, §6.5, 하네스 사슬 대체, F-1 fixture | OS-0 승인, XRUN-F1 card C, PD-8 (ii) 확인(§17.2) | 1, 5, 7, 8. 더해 fixture 실행이 front 점마다 `req:offset_matching<=` 행과 `derived_rows`를 낸다, 색인·`RunCounters`가 세션당 하나, 하네스가 `run_plan`으로 같은 기록을 만든다(E-S18 항목 전부) |
| **OS-V** | §12 | OS-2, oracle-portability 코어 | 합성 행 검증 출처가 `spice_oracle`이 된다, 오라클 코어 측정 정의가 방언·PDK 이름 0(OPP 완료 조건 1의 검사 대상), 엔진 import 0 |
| **OS-5** | §3.3 S3 칸, §7, §10 DS-1 구현, §11 TR-2 몫, compare 국면 1·L11, card C 인터페이스 | OS-2, TR-2(U16 뒤), DS-1 결정 | 2, 3, 4 |
| **TR-3·TR-5b 몫** | §11 | OT 선행 그대로 | TR-3: 낡은 승인 다섯 경로 정지, 국면 2 변형 단계 A 뒤 `trim_phase2_search_not_open`. TR-5b: 그 정지 삭제 확인(XS-15) |
| **OS-L** | §13, §7.3 `grow` | OS-5, OS-V, TR-7, DS-1 결정 -- **TR-TL과 같은 변경** | 9. 더해 반복당 색인 크기 측정 기록 |
| **OS-3** | §9 | OS-2, OS-5, TR-6 | 6 |

### 16.2 F-1 fixture(사용자 승인 S-9·S-11)

* 위치: `skills/analog-gmid-design/assets/fixture/offset_strategy/`(저장소 안·library 밖, T-28 선례 `assets/fixture/` 계열).
* topology: library `current_reuse_telescopic_ota.topology.json`의 사본(연결 그대로, `connectivity_fp` 같음).
* spec: library spec 사본에 다음만 바꾼다. `meta.origin` = `fixture`. offset 판정 제약 둘(`offset_in_sigma_mv`, 그것을 참조하는 `offset_sys_mv`)을 지우고 `offset_requirement` = {`strategy`: `matching`, `coverage_multiple`: 3, `offset_in_max_v`: 3 × 3.3 mV를 V로 적은 값}. 각 `source` = `user_spec`, record = S-9(2026-10-16) 결정 원문, 3.3 mV는 2026-10-08 Q3 (2) 유래. `judgment_temperature_range_c`는 넣지 않는다(OS-2에 소비자가 없다, OB-21).
* structure 사실: fixture에 `structure.json` 사본을 두지 않는다. 실행은 `structure_path` = library `current_reuse_telescopic_ota.structure.json`을 넘긴다(승인 사실의 사본을 만들지 않음, OB-23. 연결이 같아 `connectivity_fp` 결속이 성립한다).
* library spec은 바꾸지 않는다. **비교 한계**(계획 N7.1): fixture 결과는 library 기준선과 비교하지 않는다. OS-2 완료 조건(유도 제약·로더·출발값이 실제 경로에서 동작)에만 쓴다.

### 16.3 test 목록(독립 oracle)

| card | test | 내용 |
|---|---|---|
| OS-2 | `tests/authoring/test_spec_offset_requirement.py` | L1(판정 온도 범위의 `lo` ≥ `hi`·비유한·키 밖 포함), meta 불일치 spec에서 요구 섹션이 포트 뷰를 유도하지 않고 로드가 meta 위반으로 거부됨, 섹션 대기 → None + `pending`, 값 하나 대기 → `type`, L3, 포트 뷰 = view 없는 offset 제약이 받는 뷰, **요구 없는 spec의 `section_fps`·`spec_fp`가 칸 추가 전과 같음**(test가 지문 식을 같은 방식으로 재계산하지 않고, 칸 추가 전 커밋에서 잰 값을 픽스처로 고정 -- 검증자가 제공) |
| OS-2 | `tests/authoring/test_spec_offset_conflicts.py` | L2: metric 셋 × (`user_spec`, 판정 대상 `reference`) 거부, `pending_spice` 항목·그것을 가리키는 `reference`·`pending_constraints`는 통과, 참조 해석 뒤에 판정되는지(참조 대상만 바꾼 두 픽스처) |
| OS-2 | `tests/search/test_ss_constraints.py`(추가) | 합성 행: 손 계산 c, 모델 오차 바닥, None·분해능 사유, **한 항 resolution 0(모델 오차 없음)·다른 항 양수 → 미측정 `resolution_zero_model_error_undeclared`**, **사용자 ss 제약 없음(`declared` 빈 tuple) + bounds 있음 → 합성 행이 나온다**, 봉인 안 된 점, bounds 비면 지금 행과 같음 |
| OS-2 | `tests/search/test_kernel.py`(추가) | bounds 있으면 두 metric 요청, 없으면 지금과 같음 |
| OS-2 | `tests/search/test_iv_matching_l.py`(추가) | (가) `offset_in_sigma_mv <= x` spec과 (나) L/k = x(V 환산) 유도 제약이 같은 L 하한, 요구 없는 경로 비트 동일 |
| OS-2 | `tests/search/test_search_context.py`(추가) | `derived` 있고 mismatch 데이터 없음 → 거부, 요구 없는 spec에서 `offset_sys_mv` 판정 제약만 있으면 mismatch 검사 대상 아님(지금 그대로), `offset_start_targets`는 (k, limit_v)만(같은 k·limit에 다른 `OffsetBound` 이름·refs를 주어도 `start_intervals` 입력 버전 같음) |
| OS-2 | `tests/search/test_find_front.py`(추가) | bounds 없으면 `run_id` 지금 식, 있으면 다름 |
| OS-2 | `tests/pipeline/test_run_plan_build.py` | 요구 없음·matching·L4(단일 출력 노드 목표 없음/있음/차동 출력)·L5(단위 바꾼 가짜 서명)·L6, 두 번 불러 같음 |
| OS-2 | `tests/pipeline/test_plan_session.py` | 열기에서 색인·계수 하나, 단계 A 정지 → 계획 없음·변형 실행 0, 계획 거부 → 단계 B·탐색 호출 0(관찰), 진단 모드: 단계 A `review_needed`면 단계 B는 진단으로 돌고 탐색 0·`stop` = `stage_a_review_needed`, 같은 index 두 번 실행 `ValueError`, 닫은 뒤 실행 `ValueError`, `run_stage_a`에 `donors` 빠지면 `TypeError` |
| OS-2 | `tests/pipeline/test_run_plan.py` | `run_plan` = 세션 사용(세션 함수 호출 관찰), 결과 JSON 칸(§8), `PlanResult`·`VariantResult` 노출 칸이 E-S18 목록을 모두 덮음 |
| OS-2 | `tests/integration/test_run_plan_baseline_9circuits.py` | 완료 조건 1(비교 제외는 검증자 소유) -- 판정은 auditor 격리 복제본 |
| OS-2 | `tests/integration/test_run_plan_matching_fixture.py` | F-1 fixture 실행: `req:` 행, `derived_rows` c = S3 evals 행 c, notes `final_acceptance_is_oracle_range_judgment` |
| OS-V | `E/tests/metrics/test_verified_by.py`(추가), 오라클 `O/core/` test(OPP 규칙) | `offset_sys_mv` = `spice_oracle`, 합성 행 출처 규칙(항 하나라도 unverifiable이면 행 unverifiable), stub 어댑터에서 V_sys 측정 = 손 회로 값 |
| OS-5 | `tests/pipeline/test_run_plan_multi.py`, `tests/integration/test_run_plan_compare_phase1.py` | 완료 조건 2(순서 뒤집기 포함), 3, 4, L11, `variant` 칸, `S3Index` 상한 B_S0 |
| OS-L | `tests/pipeline/test_plan_session_add.py`, `tests/integration/test_run_plan_iteration.py` | §13.3 reason마다 거부를 먼저 확인, Δ_T가 들어가는 길 하나(호출 grep + 실행 경로), 추가 변형에서 θ 무관 블록 계산 0(OTP G-12 목록 밖 S0 블록 계산이면 FAIL -- matching 목록은 비어 있음, §3.2), 새 세션 단독 추가 실행과 비트 동일(E_B 선언), `grow` 상한 늘어남, memory 칸 |
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
| §2.4.5 '전달'(PD-8) | "세션이 만든 `donors`·`counters`를 `run_stage_a`가 필수 키워드로 받는다(만들지 않는다)". **(ii) 먼저 확인**: card B가 코드 착수 전이면 card B design 개정으로 넣어 서명을 한 번만 바꾼다. 착수했으면 OS-2가 바꾸고 card B·C의 `run_stage_a` 호출 test를 같은 변경에서 고친다 |
| §2.4.5 '상한'·§2.4.9 증거 집합 | Σ_블록 분할 수 × (Σ_v E_total,v + B_S0). `S3Index` 생성자 필수 인자 `s0_sets`, `add_eval_ceiling`, OS-L `grow` |
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
| OB-1 | G-S1 형식 | 합성 제약 행(`ss_constraint_rows` bounds) |
| OB-2 | 단위 | 레지스트리 `mv` → `core.MILLI`, 그 밖 L5 |
| OB-3 | view | 기본 포트 뷰, 로더가 정함 |
| OB-4 | S1v | 유도 제약은 S1v 밖(PD-3의 전제) |
| OB-5 | G-S2 | σ 목표 L/k |
| OB-7 | 검사 위치 | L4·L5·L6·L11은 계획 함수 |
| OB-9 | 경계 구현 | `run_stage_a` 필수 키워드, `StageAResult.topology`(PD-8 승인 범위의 세부) |
| OB-11 | `run_id` | 유도 제약이 있을 때만 지문에 더함 |
| OB-13 | 합성 행 보고 칸 | `EvalResult`에 (v, L) |
| OB-14 | 비교 도구 | `tools/offset_compare/compare.py` |
| OB-15 | 승인 결속 지문 | 요구 섹션 포함 |
| OB-16 | compare와 DS-1 | DS-1 미결이면 compare 거부 유지 |
| OB-17 | `given_starts` | 원본 topology 변형에만 |
| OB-19 | 승인 형식 | 구성 목록 |
| OB-20 | 출발값과 Δ_T | 출발값은 요구 값만, 문턱 합성은 행 한 곳(→ matching S0 문턱 의존 블록 없음) |
| OB-21 | 판정 온도 범위 칸 | 선택 칸, 필요한 소비자가 없으면 거부. 값 모양 `{"lo", "hi"}` |
| OB-22 | 사슬 대체 범위 | 전체 사슬 셋만(§6.4) -- Q-1로 확인 |
| OB-23 | fixture structure 사실 | 사본 없이 `structure_path`로 library 파일 |
| OB-24 | 세션 형식 | `open_plan_session`·`PlanSession`(`run_variant`·`add_variant`·`close`), 계획 거부 시 '거부 상태' 세션 |
| OB-25 | 변형 추가 사유 코드 | `run_plan_variant_add_rejected` + detail `reason`(§13.3) |
| OB-26 | card C 인터페이스 이름 | `s0_sets`·`add_eval_ceiling`·`grow` |
| OB-27 | OS-V 합성 행 검증 출처 | 항이 모두 `spice_oracle`이면 행도 `spice_oracle` |
| OB-28 | 합성 행 분해능 0·None | 항마다 판정, 한 항이라도 0(모델 오차 미선언)·None이면 행 없이 미측정(§3.1, 검증 N-2) |
| OB-29 | S3 `variant` 칸 | OS-5에서 구현, 변형 둘 이상 또는 반복 번호 1 이상일 때만(§3.3, 검증 N-4) |
| OB-30 | 단계 B 재사용 | pipeline 수준 캐시 없이 블록 결과 색인만(§6.1, 검증 N-7) |

(v0.1의 OB-6은 PD-9 승인 문언으로 바뀌어 지웠고, OB-8·OB-10·OB-12·OB-18은 PD-1·PD-8·PD-7·PD-2로 승인되어 기본안 목록에서 뺐다.)

### 18.2 계획과 다른 점

없음. 계획 v0.6.1과 다르게 정한 결정은 두지 않았다(S-7). D-25는 T-36으로 결정됐고(master `2c3e740`의 계획 문구도 '결정됨(T-36)'으로 정리됨 -- 이 브랜치 base `194981f`에는 그 전 문구가 남아 있다), 계획이 'D-25 결정 뒤 design이 닫는다'고 한 그대로 §13.1이 인터페이스 서명을 닫았다. 계획 N7.2 OS-L 행의 'D-25 결정' 선행은 충족됐다.

### 18.3 원래 취지와 다름

| ID | 내용 |
|---|---|
| OD-1 | 시간 예산 유도 실행은 다변형·추가 변형에서 단독 결과와 비트 동일을 보장할 수 없다(§7.2, DS-U9 열림). 원인은 비트 동일 전제(E_B 선언)다 |
| OD-2 | DS-1 (가)는 같은 평가 키를 변형마다 다시 계산하고(XS-8 허용 범위), 이미 결정된 DS-U7과 충돌한다(§10.1) |
| OD-3 | TR-3~TR-5b 사이 국면 2 탐색 게이트(XS-15 수용됨, 추적만) |

### 18.4 열린 결정·질문

| ID | 질문 | 막는 것 |
|---|---|---|
| DS-1 | 평가 캐시 (가)/(나)/(다)(§10) | OS-5 compare, OS-L |
| Q-1 | W-1 대체 범위: 부분 사슬 test(E-S19, 탐색 컨텍스트까지 만들고 내부 함수 직접 호출)를 대체 대상에서 빼는 해석(OB-22)이 맞는가. 넣으려면 세션에 '탐색 전까지 준비' 동작을 더해야 하고 이것은 공개 동작 추가라 계획 개정(S-7)이 필요하다 | OS-2 범위 |
| Q-2 | (닫힘, v0.2.1) v0.1 검증 비차단 N-1~N-4·N-6·N-7·N-12 원문을 받아 반영했다(history H4) | -- |
| DS-U8 | trim 시험 회로 `offset_in_max_v` 값 | TR-1 뒤 반영 |
| DS-U5 | library spec 이전 | -- |
| DS-U9 | 유도 예산 다변형 규칙 | -- (열림, §7.2) |

---

## 19. 원문 근거

보관 위치 `skills/analog-gmid-design/assets/technique/sources/<폴더>/source.pdf`. 쪽은 PDF 쪽, 원문 수치 인용 없음. trim 원문은 OT §19가 정본.

| R | 원문 | 웹 | 로컬 PDF | 쪽·위치 | 쓰는 곳 |
|---|---|---|---|---|---|
| R1 | Y. Zhou, A. Kay, 'Offset Correction Methods: Laser Trim, e-Trim, and Chopper', TI SBOT037A, 2017 | [ti.com/lit/SBOT037](https://www.ti.com/lit/SBOT037) | `assets/technique/sources/offset_trim__zhou_2017/source.pdf` | p.1 e-Trim, p.2 Fig.3·Table 1 | §8 compare 한계 문구, 1/f 공통 판정 근거 |
| R2 | A. Kay, 'Op Amp Offset Voltage and Bias Current Limitations', TI SBOA590, 2024 | [ti.com/lit/pdf/sboa590](https://www.ti.com/lit/pdf/sboa590) | `assets/technique/sources/offset_trim__kay_2024/source.pdf` | §1.2 PDF p.7 Figure 1-8 문단 | §8 drift 한계 문구 |
| R3 | H. M. von Staudt, 'Trim DAC Design with Minimum DNL for Self-Trim with Self-Test Schemes', IEEE IMS3TW 2011 | [doi:10.1109/IMS3TW.2011.34](https://doi.org/10.1109/IMS3TW.2011.34) | `assets/technique/sources/offset_trim__staudt_2011/source.pdf` | p.1-2 §II.A | §4.3 k를 trim 보정 구간 배수로 함께 쓰는 근거 |

matching 합성 판정식은 사용자 결정 S-1의 식이고 σ_in·V_sys는 엔진 해석 값이다.
