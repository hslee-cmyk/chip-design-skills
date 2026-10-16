---
template: design
version: 0.1
plan: ../../01-plan/features/offset-strategy.plan.md
plan_version: 0.4
---

# offset-strategy Design Document (card OS-0)

> **Summary**: 승인된 계획 `offset-strategy.plan.md` v0.4(사용자 결정 S-1~S-6, XS-1~XS-14 승인, DS-U1~DS-U9 결정)를 엔진 `gmid_engine` 설계로 옮긴다. 계획 N10.3의 G-S1~G-S6을 닫고, 요구 스키마·로더 사유 코드, 실행 계획 `RunPlan`·`build_run_plan`·실행기 `run_plan`의 서명, 변형 제약 집합의 주입 방식, 결과 JSON 칸, 비교 도구, 예산 식, 파일 분할, 배선표, test 목록, card별 완료 조건을 정한다. OS-5 몫(변형 정체 지문·S3 변형 칸·Σ 상한·국면 규칙·승인 로더·낡은 승인 정지)은 형식만 정하고 TR card별 배정을 적는다(검증 메모 N-22). offset-trim design(OT)과 40 design의 개정안, trim 시험 회로 spec 재작성안을 함께 낸다(§15).
>
> **Project**: chip-design-skills (analog-gmid-design skill) · **Author**: Claude Code (design 작성자 역할)
> **Status**: design 초안 v0.1 (2026-10-16). 독립 검증·사용자 승인 전이다. 오케스트레이터 기본안(사용자 결정 아님), 계획과 다른 점, 원래 취지와 다른 점, 열린 결정은 §16에 모았다. 경위는 [offset-strategy.design.history.md](offset-strategy.design.history.md).
> **기준**: 코드 인용은 master `d783efe`(worktree `wt/ostrat-design`)의 `파일:줄`이다. 계획의 인용 기준 `067614c`와 줄이 달라진 곳은 이 문서가 다시 쟀다(history H2). `E/` = `skills/analog-gmid-design/gmid_engine/`. design 인용은 `OT §x`(`offset-trim.design.md` v0.2, 사용자 승인 T-18), `40 §x`(`gain-budget-gmid-sizing.40-engine.design.md`), `41 §x`.
> **전제**: 구현은 XRUN-F1 card A·B·C 병합 뒤다(계획 S-4). `d783efe`에는 card A·B·C가 병합되지 않았다(`E/search/s3_index.py`·`search_ceiling.py`·`search_stop.py` 없음, 2026-10-16 `ls`). 그래서 이 문서는 40 §2.4.4~§2.4.14의 병합 뒤 구조(블록 호출의 `donors`·`counters` 필수 인자, `S3Index`, `RunCounters`, E_total, `search_ceiling`)를 전제로 쓴다.

---

## 0. 문서 안내

* **담는 것**: 규칙, 정의, 값 형식, 함수 서명, 사유 코드, 결과 JSON 칸, 파일 분할, 배선표, test 목록, card별 완료 조건, 다른 문서 개정안.
* **담지 않는 것**: 경위, 검토 과정, 대안 비교의 세부(history H2), 수치 상수. 값은 spec 선언(요구·trim 섹션), 단위 어휘(`E/core/units.py`), 엔진 해석값, LUT, PDK 선언에서만 온다.
* **이름 원칙**: 규칙에 회로·소자·넷 이름을 쓰지 않는다. 회로 이름은 사실 표와 측정·fixture 대상에만 나온다.
* **용어**: 계획 N0.1 그대로(요구, 방식, 변형, 실행 계획, 국면, 공통 판정, 핵심 층, 파이프라인 층, 실행). 이 문서가 더하는 용어는 아래다.

| 용어 | 정의 |
|---|---|
| 유도 제약 | 요구에서 엔진이 만든 판정 제약. spec `constraints`(사용자 선언)와 따로 둔다(§5.3). 값 형식 `OffsetBound`(§3.4) |
| 합성 행 | 두 metric 결과를 읽어 만드는 제약 행 하나. 이 문서에서는 matching 유도 제약의 행 `req:offset_matching<=`(§3.1) |
| 변형 제약 집합 | spec 판정 제약(변형 사이 같은 객체) + 그 변형의 유도 제약 tuple(+ 국면 2면 `trim_decl`, OS-5 형식) |
| 토폴로지 변형 | 실행 계획 한 항목의 topology. 원본 `TopologyDoc`이나 승인된 파생 topology(OT §7) |
| S0 벌 수 | 한 실행 계획 안에서 S0 수준 블록이 서로 다른 입력으로 계산되는 벌의 수(§7.3) |

---

## 1. 입력·원칙

### 1.1 확정 결정(인용)

원문은 `wt/_drafts/user_decisions.md` '## offset 방식 선택·실행 계획'(S-1~S-4), '## offset-strategy 계획 승인'(S-5), '## offset-strategy 세부 결정'(S-6), '## offset-strategy 계획 검증 메모'(N-22)다.

| ID | 내용(요지) | 이 문서 반영 |
|---|---|---|
| S-1 | spec은 요구 `offset_requirement{offset_in_max_v, coverage_multiple, strategy}`로 쓴다. matching: k·σ_in + \|V_sys\| ≤ `offset_in_max_v`. trim: `trim_range`·`trim_residual`, V_res ≤ `offset_in_max_v` 로더 검사. 1/f·면적 공통 | §3.1, §4 |
| S-2 | 파이프라인 층 재작성, 실행 계획 = 변형 목록, 단계 A·S0·블록 결과 색인 공유, `trim_approval_path` 인자 분기 삭제, 핵심 층 유지 | §5, §6, §15.1 |
| S-3 | compare 두 국면, 최종 비교는 읽기 전용 도구, 엔진 입력 경로 없음 | §9, §11 |
| S-4 | 순서 NFR-4 card 2 → XRUN-F1 A → B → C → 실행 계획 → TR-1 | §14 |
| S-5 | XS-1~XS-14 전부 승인. XS-5·XS-8은 '허용 범위' 승인이고 DS-1·DS-2 선택은 M2 뒤 사용자 결정 | §10, §16 |
| S-6 | DS-U1 (가) `offset_excess` 공존 거부, DS-U2 셋 다 거부, DS-U3 k 단일 출처 = 요구, DS-U4 compare는 1/f 판정 하나 이상 + 면적 상한 필수, DS-U5 library 이전은 회로별 사용자 결정, DS-U6 N+1의 m = 같은 집계 규칙, DS-U7 완료 조건 3 약화 안 함, DS-U8 시험 회로 `offset_in_max_v` = 사용자 값, DS-U9 design 조사·정해지기 전 조건 2·NFR-S5 제외 | §4, §7, §11, §15 |
| N-22 | OS-5로 옮긴 세 가지를 TR card별로 배정: TR-2 = '승인 기록 없음 → 국면 1'과 '승인 기록 있으면 국면 2 미구현 fail-closed'만. 로더·낡은 승인 정지·국면 2 분기는 국면 2를 여는 TR card(OT §8 TR-1 로드·§8.3 TR-3 검사와 대조) | §11 |
| 원래 취지 | 사용자 원문(2026-10-15): "계산 재사용은 처음 topology를 실행할 때는 항상 계산하고 그 계산된 값이 나머지 최적화를 진행할 때 재사용되게 한다는 것이 원래 취지였어" | §5.3, §6.2, §10 |

**이어받는 결정**(바꾸지 않는다): U-89(S3는 출력, 실행 사이에 읽지 않음), X-12(색인 수명 = 실행, 단계 A부터), X-17(E_total = E_B + N_T + R), X-7(블록 호출 `donors`·`counters` 필수), T-2·T-7·T-8(파생 topology 승인 뒤 사이징, I_u = θ, θ 하나 = 커널 1회), T-15(TR-2 병합은 U16 뒤), T-19~T-23(단일 출력 회로의 출력 기준 DC는 '출력 기준 DC' 기능 몫), T-24~T-28(trim 시험 회로).

### 1.2 원칙과 이 문서의 강제 장치

| 원칙 | 강제 장치 |
|---|---|
| graph 단일 정본(NFR-S2) | 요구 값은 spec 섹션 한 곳. 유도 제약은 해석된 값과 참조 경로를 함께 담는다(기존 `ConstraintDecl.value`·`ref` 형식과 같은 방식, `E/authoring/spec_model.py:126-138`). 유도 제약·실행 계획은 graph 필드가 아니다 |
| 재사용(NFR-S1, 원래 취지) | 유도 제약을 spec 밖 입력으로 두어(§5.3) 변형 사이에 spec을 읽는 블록의 입력이 같게 한다. S1v 씨앗에 넣지 않는다(§3.1 (e)) |
| topology 무관(NFR-S3) | 뷰는 포트 역할에서, 기준 DC는 `DcInputs`에서, 단위는 레지스트리 단위 칸에서 읽는다. 회로·넷 이름 리터럴 없음 |
| fail-closed(NFR-S4) | §4.2 사유 코드 전부 탐색 전 정지. 단위·뷰·기준이 정해지지 않으면 거부 |
| 결정성(NFR-S5) | 계획 함수는 순수 함수, 변형 순서 고정(§5.2) |
| 상수 발명 금지(NFR-S6) | 합성 행의 문턱·분해능·단위 환산은 정의와 단위 어휘에서(§3.1). 비교 도구에 가중치·문턱 없음(§9) |
| 만들면 배선(NFR-S7) | §13 배선표. 제품 진입점(U16) 미병합 문제는 §16.4 W-1(사용자 승인 요청) |
| 작성자 ≠ 검증자(NFR-S8) | test 기대값은 interface card만 보고 쓴다. 완료 조건 1의 비교 제외 칸(G-S6)은 검증자가 확정·소유한다 |

---

## 2. 엔진 실측 사실(`d783efe`)

계획 N3.0 F-1~F-13을 이 기준에서 다시 확인했고(줄 변화는 history H2), 이 design이 새로 잰 사실을 더한다.

| ID | 사실 | 근거 |
|---|---|---|
| E-S1 | offset metric 셋(`offset_in_sigma_mv`·`offset_excess`·`offset_sys_mv`)의 레지스트리 단위는 `mv`, view_kind는 `transfer`다. 레지스트리 metric은 '이미 계산된 값 묶음의 필드 하나'이고 값을 다시 계산하는 함수가 아니다 | `E/metrics/registry.py:5-6, :56-58` |
| E-S2 | view를 적지 않은 transfer metric 제약은 로더가 기본 포트 뷰(`default_views(topology, feedback).port`)를 받는다. 포트 뷰는 입력 포트 역할(차동쌍 하나 또는 단일 하나)과 출력 포트(하나 또는 차동 출력쌍)에서 만들고, 정해지지 않으면 사유 문자열 → `view_required` | `E/authoring/spec_constraints.py:198-204`, `E/authoring/spec_views.py:69-84, :171-184` |
| E-S3 | library의 offset 판정 제약은 view를 적지 않는다(기본 포트 뷰) | `assets/library/current_reuse_telescopic_ota.sizing_spec.json:226-234`, `assets/library/two_stage_ota.sizing_spec.json:81-89` |
| E-S4 | `offset_analysis`·`offset_systematic`은 요청의 `ViewDecl`로 `view_system`을 직접 쓴다. σ_in과 V_sys 계산에 S1v 뷰 씨앗이 필요하지 않다(`offset_excess`만 S1v 입력 셀을 쓴다) | `E/metrics/offset_analysis.py:56-57, :86-93`, `E/metrics/offset_systematic.py:31-33` |
| E-S5 | `offset_sys_mv` 값은 \|오차\|/\|A_dm\|(mv, 크기)이고 부호 있는 오차는 `output_error_v`. 단일 출력 기준은 `targets`(= spec `node_voltage_targets_v`)의 그 출력 넷 값, 없으면 `reference_undeclared` | `E/metrics/offset_systematic.py:1-10, :42-47, :55` |
| E-S6 | `dc_inputs_from_spec`은 결정 대기 노드 목표를 '미선언'으로 투영한다. `metrics_aux`의 `targets`가 이 `DcInputs.node_targets`다 | `E/sizing/dc_inputs.py:7, :11-12, :24-41`, `E/metrics/ss_evaluate.py:103` |
| E-S7 | S1v 전달 뷰 씨앗은 판정 제약의 port·loop·transfer·ratio 뷰에서 만들고, 선언 씨앗이 없을 때만 기본 씨앗을 쓴다. `build_s1v`는 spec 객체 전체가 아니라 `judged_constraints` tuple을 extras로 넘긴다 | `E/graph/views.py:51-63, :77-78`, `E/graph/s1v_build.py:39-42`, `E/graph/s1v_fields.py:249-252` |
| E-S8 | `ss_evaluate`의 요청 목록은 각 항목의 `.metric`·`.view`만 읽는다(`MetricRequest`도 같은 두 칸) | `E/metrics/ss_evaluate.py:50-57`, `E/metrics/ss_types.py:57-61` |
| E-S9 | 커널은 `sctx.ss_constraints`를 `ss_evaluate`에 넘기고 행을 `seal_rows + _spec_rows + ss_rows + ls_rows`로 모은다 | `E/search/kernel.py:130-132, :146-151` |
| E-S10 | 출발값의 제약 목록은 `spec.judged_constraints`의 (metric, op, 값)이고, matching L 하한은 `offset_in_sigma_mv <=` 값 최솟값 × `MILLI` / √2를 입력 셀 몫으로 쓴다 | `E/search/iv_context.py:89`, `E/search/iv_matching_l.py:107, :123` |
| E-S11 | mv → V 환산 정본은 `core.MILLI`이고 단위 계수는 `E/core/units.py` 한 곳에 있다 | `E/core/units.py:13, :22`, 함수 레지스트리 §15 'mv -> V 환산' 행 |
| E-S12 | offset 판정 제약이 값과 함께 있으면 탐색 컨텍스트가 LUT mismatch 데이터를 필수로 확인한다 | `E/search/search_context.py:153, :164-168` |
| E-S13 | 엔진에 단계 A → B → 커널 컨텍스트 → 탐색 컨텍스트 → `find_front`를 잇는 제품 진입점이 없다. `run_gmid_design_pipeline`은 자리만 있고(U16), 사슬은 test 하네스가 만든다 | `E/pipeline/__init__.py:1-4`, `E/tests/integration/nfr4_run_dump.py:376-401` |
| E-S14 | `run_stage_a(topology_path, spec_path, lut, *, output_dir, supplies_v=None, structure_path=None)`. 결과 `StageAResult`에 topology 칸이 없다 | `E/pipeline/stage_a.py:83-95, :199` |
| E-S15 | `find_front`의 `run_id` = `fp_of((context_fp, code_fp, settings, eval_budget, 시작 θ))`. 판정 metric 검증 출처 목록은 `ss_constraints`와 목적 축 제약에서 모은다 | `E/search/find_front.py:97, :142` |
| E-S16 | spec 선택 섹션은 `HUMAN_OPTIONAL`에 이름을 더한다. 섹션별 허용 출처 kind는 `ALLOWED_KINDS` | `E/authoring/spec_schema.py:29-31`, `E/authoring/spec_sources.py:35-` |
| E-S17 | 새 이름 충돌 없음: `offset_requirement`, `OffsetRequirement`, `OffsetBound`, `run_plan`, `RunPlan`, `build_run_plan`, `req:` 행 접두, `offset_matching`, `offset_strategy`, `offset_compare`, `trim_phase2` | grep 2026-10-16(`gmid_engine`·`tools`·`docs`, 계획·design 문서 제외) 0건 |

---

## 3. OS-0 닫을 항목 G-S1~G-S6

### 3.1 G-S1 matching 합성 판정

**결론(오케스트레이터 기본안 OB-1)**: 새 metric을 만들지 않는다. 기존 두 metric(`offset_in_sigma_mv`, `offset_sys_mv`)의 결과를 읽는 **합성 제약 행** 하나를 search 층 `ss_constraint_rows`에 더한다(계획 XS-10이 승인한 범위 'ss_constraint_rows 한 곳').

**새 metric(k를 입력으로 받음)을 택하지 않는 근거**:
1. 레지스트리 metric은 계산된 값 묶음의 필드 하나다(E-S1). k를 metric 안에 넣으면 metric 블록(`metrics_aux`) extras에 spec 값이 들어가 metric 블록 입력이 판정 값에 의존한다. 계획 F-2의 '제약이 metric 블록 입력을 정한다'를 넓히는 방향이다.
2. 합성 행은 이미 요청·계산되는 두 결과를 읽기만 한다. 새 계산 블록이 없고, 같은 값을 다시 계산하지 않는다.
3. 레지스트리·catalog·`verified_by`의 이름 공간을 바꾸지 않는다.

**(a) 행 정의**(유도 제약 `OffsetBound` b 하나마다, 봉인 점에서):

| 항목 | 규칙 |
|---|---|
| 요청 | `MetricRequest(b.sigma_metric, b.view)`, `MetricRequest(b.sys_metric, b.view)`. 커널이 `ss_evaluate`에 `sctx.ss_constraints`와 함께 넘긴다(E-S8: 요청 목록은 `.metric`·`.view`만 읽는다). 같은 (metric, view)를 사용자 제약도 요청하면 `_requests`가 하나로 모은다 |
| 값 | v = k·σ + \|V_sys\| (V). σ = `sigma_in_mv`·u, \|V_sys\| = `sys_mv`·u, u = 단위 환산(아래 (c)) |
| 문턱 | L = `offset_in_max_v`(요구 섹션 값, V). op `<=`만 |
| 분해능 | s = k·s_σ + s_sys. s_x = max(그 metric 결과 `resolution`, 그 metric 모델 오차 선언(있으면))·u. 선형 오차 전파의 상계(\|Δ(kσ + V)\| ≤ k\|Δσ\| + \|ΔV\|)이고, 기존 ss 행의 '분해능 = 결과 resolution, 모델 오차 선언이 있으면 큰 쪽'(`E/search/ss_constraints.py:15-18, :82`)을 항마다 그대로 쓴 것이다. 새 상수 없음 |
| 행 | 이름 `req:offset_matching<=`, c = (L − v)/s, `active` = c ≤ 1(기존 ss 행과 같은 규칙, `ss_constraints.py:19, :86-87`) |
| 봉인 안 된 점 | 행 없음, 미측정 (`offset_matching`, `<=`, `ss_requires_sealed_snapshot`)(기존 ss 규칙과 같은 사유) |
| 정의 불가 | σ나 V_sys 값이 None이면 행 없이 미측정 (`offset_matching`, `<=`, 두 결과의 `Undefined` 코드 합집합을 정렬해 `+`로 이음) |
| 분해능 없음 | 어느 항의 `resolution`이 None이면 `resolution_undefined`, s = 0이면 `resolution_zero_model_error_undeclared`(기존 사유 그대로) |

**(b) 판정 쪽 성질**: 행은 정규화 부등식 c ≥ 0 하나다. 판정 경계 위에 일부러 놓는 점은 만들지 않는다(41 §5.13 대상 아님 -- 탐색이 이 행을 경계로 쓸 뿐이다).

**(c) 단위(오케스트레이터 기본안 OB-2)**: 항 metric의 단위는 레지스트리 서명 단위 칸에서 읽는다(E-S1). 한계 키 `offset_in_max_v`의 접미 `_v`는 V다(DEC-68). 환산 규칙: 항 단위가 `mv`이면 u = `core.MILLI`(함수 레지스트리 §15 'mv -> V 환산' 정본, E-S11). 항 단위가 `mv`가 아니면 유도 제약을 만들 때(§5.2) `offset_requirement_unit_unsupported`(`SchemaRejectedError`, gate `run_plan`)로 거부한다. 숫자 1000·0.001을 새로 쓰지 않는다.

**(d) view 출처(오케스트레이터 기본안 OB-3)**: 유도 제약의 view = **기본 포트 뷰**다. 사용자가 offset 제약에 view를 적지 않았을 때와 같은 규칙이다(E-S2, E-S3). 로더가 요구 섹션을 읽을 때 `default_views(topology, feedback).port`로 정해 `OffsetRequirement.view`에 담는다(§4.1). 포트 뷰가 정해지지 않으면(사유 문자열) 로더가 `offset_requirement_view_required`로 거부한다. 요구 섹션에 view 선언 키는 두지 않는다(요구는 수단이 아니다). 입력 셀 전달 뷰(`metric_structure`)를 쓰지 않는 근거: 그것은 S1v 유도 결과라 로더가 정할 수 없고, 사용자 offset 제약의 기존 뷰 규칙과 달라져 matching 결과가 '요구 이전 spec'과 다른 뷰에서 재진다.

**(e) S1v와의 관계(오케스트레이터 기본안 OB-4)**: 유도 제약은 S1v 뷰 씨앗에 들어가지 않고 `build_s1v` extras에도 들어가지 않는다. 근거: (1) σ_in·V_sys 계산은 요청의 `ViewDecl`만 쓴다(E-S4). (2) S1v 씨앗은 사용자 판정 제약의 구조 뷰이고(E-S7), 유도 제약은 spec `constraints` 밖에 있다(§5.3). 결과: 같은 topology 변형끼리(compare 국면 1의 matching과 trim 국면 1) `build_s1v` 입력이 같아 S1v 블록이 한 번만 계산된다. 이것이 계획 N3.1-3·F-3가 'G-S1이 정한다'고 한 지점의 답이다. DS-2에 미치는 영향은 §3.5·§16.3.

**(f) 이름**: 행 접두 `req:`는 '요구에서 유도한 행'을 뜻하는 고정 문자열이다(기존 접두 `spec:`·`ss:`·`ls:`와 겹치지 않음, E-S17). `offset_matching`은 방식 이름이고 회로 이름이 아니다.

### 3.2 G-S2 matching 출발값

**규칙(오케스트레이터 기본안 OB-5)**: 출발값 σ 목표 집합 Σ_t(V)를 다음 둘의 합집합으로 만든다.
1. 사용자 판정 제약 `offset_in_sigma_mv <=` 값 × `MILLI`(지금 경로, 요구가 없는 spec).
2. 유도 제약 `OffsetBound` b마다 b.limit_v / b.k.

matching L 하한은 지금처럼 입력 셀 몫 σ_share = min(Σ_t)/√2로 계산한다(`E/search/iv_matching_l.py:123`의 식에서 `min(absolute) * MILLI`를 `min(Σ_t)`로 바꾼다). 두 경로가 함께 있는 spec은 로더가 거부하므로(§4.2) 실제로는 한쪽만 있다.

* **b.limit_v / b.k인 근거**: k·σ_in + \|V_sys\| ≤ L이고 \|V_sys\| ≥ 0이므로 σ_in ≤ L/k는 필요조건이다. 출발 시점에는 V_sys를 모르고, 한계를 σ 몫과 V_sys 몫으로 나누는 비율을 만들면 상수 발명이다(계획 N3.10). 그래서 필요조건 중 가장 느슨한 값을 쓴다. 출발값 전용이고 판정은 §3.1 합성 행이 한다(EP-7).
* **요구 없는 spec의 비트 동일**: 양의 계수 곱은 단조라 min(vᵢ·`MILLI`) = min(vᵢ)·`MILLI`가 float에서도 같다. 그래서 1번 경로만 있는 실행의 출발값은 지금과 비트 동일하다.
* **바뀌는 곳**: `E/search/iv_context.py`(`StartView`에 칸 `sigma_targets_v`, :89 옆에서 만든다), `E/search/iv_matching_l.py`(:107·:123이 그 칸을 읽는다), `E/search/start_intervals.py`(:253 extras에 유도 제약 tuple을 더해 `start_view`로 넘긴다), `E/search/search_context.py`(:195 `start_intervals` 호출에 유도 제약을 넘긴다). 가드(`offset_excess`) 경로는 바뀌지 않는다(요구가 있으면 `offset_excess`는 로더가 거부, DS-U1).

### 3.3 G-S3 변형 정체 지문(형식만, OS-5)

| 이름 | 정의 |
|---|---|
| `constraint_set_fp` | `fp_of((spec 섹션 지문 'constraints_fp', 유도 제약 tuple, trim_decl.decl_fp 또는 None))`. spec 섹션 지문은 `SizingSpecDoc.section_fps`의 값(`E/authoring/spec_model.py:280, :311`) |
| `variant_fp` | `fp_of((토폴로지 변형 connectivity_fp, constraint_set_fp))` |
| 계획 함수 검사 | 같은 `variant_fp`가 두 번 나오면 `run_plan_duplicate_variant`(`ValueError` -- 계획 함수 결함) |
| S3 칸(XS-13) | evals·runs 줄 최상위 키 `variant` = `variant_fp`. **실행 계획에 변형이 둘 이상이거나 변형에 유도 제약·trim_decl이 있을 때만** 싣는다. 요구 없는 실행(변형 하나, 유도 제약 없음)의 줄은 지금과 같다(완료 조건 1) |
| 결과 JSON | `run_plan.variants[i].variant_fp`(§8) |

### 3.4 G-S4 유도 제약의 기록 형식

값 형식 `OffsetBound`(search 값 모듈 `E/search/search_values.py`, frozen dataclass):

```python
OffsetBound(name: str,              # "offset_matching" -- 행 이름의 몸통
            sigma_metric: str,      # 레지스트리 metric 이름(σ_in 항)
            sys_metric: str,        # 레지스트리 metric 이름(V_sys 항)
            k: float,               # 요구 coverage_multiple 의 해석된 값
            limit_v: float,         # 요구 offset_in_max_v 의 해석된 값
            view: ViewDecl,         # OffsetRequirement.view(기본 포트 뷰)
            refs: tuple,            # (("k", "human.offset_requirement.coverage_multiple"),
                                    #  ("limit_v", "human.offset_requirement.offset_in_max_v"))
            source_fp: str)         # 요구 섹션 지문(값·출처 kind) -- 출처 칸
```

* 해석된 값 + 참조 경로를 함께 담는 것은 기존 참조 제약(`ConstraintDecl.value`·`ref`, `E/authoring/spec_model.py:126-138`)과 같은 형식이다(`value_from_spec` 계열). spec 파일에 숫자를 복사하지 않는다(NFR-S2).
* 결과 JSON에서는 `{"name", "sigma_metric", "sys_metric", "k", "limit_v", "view", "refs", "source_fp"}`로 싣는다(§8).
* trim 국면 2 유도 제약(`trim_range`·`trim_residual`·`trim_states_saturation`)은 OT §10.6대로 `trim_decl`에서 `trim_constraint_rows`가 만든다. 그 출처 칸은 OT 형식 그대로이고 `OffsetBound`를 쓰지 않는다(k·V_res의 출처만 §15.3으로 바뀐다).

### 3.5 G-S5 S1v 재계산 칸(DS-2 (가)일 때)과 G-S1의 영향

* **G-S1 (e)의 결과**: 이 design에서는 같은 topology 변형끼리 `build_s1v` 입력(판정 제약 tuple)이 같다. 그래서 compare 국면 1(matching + trim 국면 1)에서 S1v 블록은 한 번 계산되고 나머지는 색인 적중이다. 계획 DS-2가 다루던 '같은 topology 변형마다 S1v 재계산'은 이 design에서 생기지 않는다. 다만 DS-2는 사용자 결정 항목이므로 이 문서가 닫지 않는다(§16.3 PD-3).
* **칸 정의(어느 경우든 싣는다, OS-5)**: 결과 JSON `run_plan.shared.s1v_computes` = 실행 계획 안 S1v 블록(`s1v_fields` writer)의 `computes` 합(`RunCounters.snapshot()`의 블록 행에서), `run_plan.shared.s1v_inputs` = S1v 블록이 계산된 서로 다른 입력 버전 수. 같은 topology 변형 둘을 담은 계획에서 두 값이 1이면 공유가 성립한 것이다(완료 조건 4의 근거 칸).

### 3.6 G-S6 완료 조건 1의 비교 제외 칸(초안, 검증자 소유)

비교 = 요구 없는 실행, base(XRUN-F1 card C 병합 뒤 master)의 사슬(`run_stage_a` → `run_stage_b` → 커널 컨텍스트 → `build_search_context` → `find_front`, E-S13의 하네스와 같은 순서) 대 OS-2 병합본의 `run_plan`. 같은 실행 환경, E_B 선언(40 §2.4.13 1차 검사 전제 (가)~(다)). 부류는 OT §3.3과 같은 방식이다.

| 부류 | 칸 | 처리 |
|---|---|---|
| F2 블록 코드 해시에서 온 입력 버전 | `FieldValue.input_version`, 스냅샷 `block_versions`·`fp`, S3 evals `snapshot_fp`, `context_fp`(S3 폴더 이름·runs 줄 `s0`·평가 키 칸) | 뺀다. 바뀐 블록 파일(`start_intervals`·`achievability` 등 spec이나 extras가 바뀐 블록)마다 바뀐다 |
| F3 코드·실행 지문 | `code_fp`·`engine_code_fp`, `run_id` | 뺀다 |
| spec 지문 | `SizingSpecDoc.spec_fp`·`section_fps`(새 섹션이 지문 묶음에 들어간다, §4.1). 결과 칸에 나오면 | 뺀다 |
| 새 출력 N | `<회로>.run_plan.json` 파일(§8) | base에 없다. 비교 밖이고 **내용을 단언**한다: 변형 하나, `strategy` null, 유도 제약 빈 목록, `phase` null |
| 시간 T | 40 §2.4.13 (2) T 부류 | 뺀다 |
| 실행 경계 문구 변경(XS-7)으로 바뀌는 칸 | 예상 없음: 색인·`RunCounters`를 만드는 자리가 `run_plan` 진입으로 옮겨도 그 실행의 블록 호출 집합은 같다. 실제로 바뀌는 칸이 나오면 FAIL로 보고하고 목록에 더할지 검증자가 정한다 | -- |
| 값 V | 그 밖 전부(단계 A·B 보고서 값 칸, 노드 전압·동작점·metric·제약 행·front·ε 기록·`perf` 계수, S3 줄 값 칸) | 비트 동일 |

---

## 4. 요구 스키마와 로더

### 4.1 스키마 `human.offset_requirement`

선택 섹션이다(`HUMAN_OPTIONAL`에 더함, E-S16. 스키마 버전 그대로 -- 선택 키 추가라 기존 spec이 유효하다).

```json
"offset_requirement": {
  "offset_in_max_v":   {"value": <V>,        "source": {<user_spec 출처>}},
  "coverage_multiple": {"value": <k>,        "source": {<user_spec 출처>}},
  "strategy":          {"value": "matching" | "trim" | "compare", "source": {<user_spec 출처>}}
}
```

| 키 | 뜻 | 형식 검사(위반 사유) |
|---|---|---|
| `offset_in_max_v` | 입력 환산 offset 한계(V). matching에서 k·σ_in + \|V_sys\|의 상한, trim에서 V_res의 상한 | 유한 양수(`offset_requirement_value`) |
| `coverage_multiple` | k. σ_in의 배수. matching 상한과 trim 보정 구간이 같은 k를 쓴다(단일 출처, DS-U3) | 유한 양수(`offset_requirement_value`) |
| `strategy` | 방식 | 닫힌 어휘(`offset_requirement_strategy`) |

* 출처는 `user_spec`만(`ALLOWED_KINDS`에 `offset_requirement` = (`user_spec`,)을 더한다). 결정 대기 `{"pending": <ID>}`는 섹션 전체 자리에만 받는다(값 하나만 대기는 `type`). 키 밖은 `_spec_fields.key_hits`(`unknown_key`·옛 이름 구분 그대로). 빠진 키는 `missing_key`.
* 이름은 DEC-68이다: `_v` = V, 무차원 배수는 접미 없음. 새 단위 어휘 없음.
* 로드 결과 값 형식(spec 값 모듈 `E/authoring/spec_model.py`, frozen dataclass): `OffsetRequirement(offset_in_max_v, coverage_multiple, strategy, view, sources)`. `view` = §3.1 (d)의 기본 포트 뷰, `sources` = 키별 `SpecSource`. `SizingSpecDoc`에 칸 `offset_requirement`(`OffsetRequirement` 또는 None)를 더하고 `SECTION_GROUPS`에 `("requirement_fp", ("offset_requirement",))`를 더한다. 섹션이 결정 대기면 칸은 None이고 대기 표지는 기존 수집 경로(`check_spec_schema`)로 `pending`에 모인다(계획 N3.2 마지막 행).

### 4.2 로더·계획 함수 규칙과 사유 코드

사유 코드는 DEC-68 명명 규칙(snake_case, 대상 접두)을 따른다. gate `spec_load` 행은 `load_sizing_spec`이 모든 위반을 모아 한 번에 거부하는 기존 방식(`E/authoring/spec_load.py:15-19`)이고, gate `run_plan` 행은 `build_run_plan`이 던진다. 모두 `SchemaRejectedError`(exit 7)다.

| # | 상황 | 사유 코드 | gate | 구현 card |
|---|---|---|---|---|
| L1 | 키 값 형식 위반 | `offset_requirement_value`·`offset_requirement_strategy`·`type`·`missing_key`·`unknown_key`·출처 규칙 | spec_load | OS-2 |
| L2 | 요구와 `offset_in_sigma_mv`·`offset_sys_mv`·`offset_excess` 제약이 함께 있음(DS-U1·DS-U2). 범위 = `human.constraints` 항목 전부(출처 kind `user_spec`·`pending_spice`·`reference` 모두, OB-6). `pending_constraints`(값 없는 결정 대기 이름 목록)는 거부하지 않는다(판정 값이 없어 두 번째 출처가 아니다, OB-6) | `offset_requirement_conflicts_constraint`(detail = 위치, metric) | spec_load | OS-2 |
| L3 | 포트 뷰가 정해지지 않음(§3.1 (d)) | `offset_requirement_view_required`(detail = `default_views` 사유) | spec_load | OS-2 |
| L4 | matching(또는 compare의 matching 변형)이고 포트 뷰 관측이 단일 출력인데 그 넷이 `dc_inputs_from_spec(spec).node_targets`에 없음(E-S5·E-S6. `offset_systematic`과 같은 출처를 읽는다 -- '출력 기준 DC' 기능이 그 출처를 바꾸면 이 검사도 같은 변경에서 따라간다, OB-7) | `offset_requirement_reference_undeclared`(detail = 넷) | run_plan | OS-2 |
| L5 | 유도 제약 항 metric 단위가 `mv`가 아님(§3.1 (c)) | `offset_requirement_unit_unsupported` | run_plan | OS-2 |
| L6 | `strategy`가 `trim`·`compare`인데 그 경로가 아직 열리지 않음(DO-6) | `offset_strategy_not_open`(detail = strategy) | run_plan | OS-2(거부), TR-2·OS-5(해제) |
| L7 | `strategy`가 `trim`·`compare`인데 `offset_trim` 섹션 없음 | `offset_requirement_trim_undeclared` | spec_load | TR-1 |
| L8 | `strategy`가 `matching`인데 `offset_trim` 섹션 있음 | `offset_requirement_trim_unused` | spec_load | TR-1 |
| L9 | `offset_trim` 섹션은 있는데 요구가 없음(XS-6·XS-9) | `offset_trim_without_requirement` | spec_load | TR-1 |
| L10 | `offset_trim.residual_offset_v` > `offset_in_max_v`(S-1) | `offset_trim_residual_exceeds_requirement`(detail = 두 값) | spec_load | TR-1 |
| L11 | compare인데 공통 판정이 없음(DS-U4): 1/f(`noise_fc_in_hz`·`noise_out_int_vrms` 가운데 하나 이상)와 면적(`area_search_m2 <=`)이 **값이 있는 판정 제약**(`judged` 참이고 값 None 아님)으로 둘 다 있어야 한다 | `offset_compare_common_judgment_missing`(detail = 빠진 쪽) | run_plan | OS-5 |
| L12 | 요구 섹션이 결정 대기 | 사유 없음 -- 요구 없음과 같다(지금 흐름), 대기 표지는 `pending` | -- | OS-2 |

* `offset_trim` 섹션은 TR-1 전에는 로더가 모르는 키(`unknown_key`)다(T-28). 그래서 L7~L10은 TR-1이 `offset_trim` 로더와 함께 구현한다(계획 N3.9 마지막 행).
* L2의 검사 함수는 별도 파일(규칙 A, §12)에 두고 `load_sizing_spec`이 섹션 검사 뒤 부른다. OT §5.2의 `trim_constraint_conflicts`·`trim_demoted_constraints`(강등)는 만들지 않는다(§15.1, XS-1).
* L4·L5·L6·L11을 계획 함수에 두는 근거(OB-7): L4는 `DcInputs`(sizing)를 읽어야 하는데 로더(authoring)는 sizing을 import할 수 없다(층 순서). L5·L6·L11은 방식·국면별 규칙이라 계획 표와 한 자리에 둔다. 넷 다 단계 B·탐색 전이다.

### 4.3 k 단일 출처(DS-U3)

k는 `offset_requirement.coverage_multiple` 하나다. OT §5.1의 `offset_trim.coverage_multiple`은 없앤다(§15.1). trim 쪽 소비자(OT §9.4 추천 입력, §10.4 `i_lower_amp`, §10.6 `trim_range`, §17 식 S)는 요구의 k를 읽는다. 승인 결속(OT §8.3-4)의 지문은 요구 섹션을 포함한다(§15.1 OT §8 행, OB-15).

---

## 5. 실행 계획

### 5.1 값 형식(`E/pipeline/run_plan_values.py`, frozen dataclass)

```python
PlanVariant(index: int,                 # 계획 안 순서(0부터)
            label: str,                 # "baseline" | "matching" | "trim_phase1" | "trim_phase2"
            topology: TopologyDoc,      # 토폴로지 변형(OS-2는 원본뿐)
            derived: tuple,             # OffsetBound tuple(유도 제약, 없으면 ())
            trim_decl: object,          # OS-5: 국면 2면 TrimDecl, 그 밖 None
            variant_fp: str)            # §3.3 (OS-2에서도 계산해 결과 JSON에 싣는다)
RunPlan(strategy: str | None,           # 요구 strategy, 요구 없으면 None
        phase: int | None,              # trim·compare 국면(1|2), 그 밖 None
        requirement: OffsetRequirement | None,
        variants: tuple[PlanVariant, ...],
        budget_unit: str)               # "variant" (XS-12, §7)
VariantResult(variant: PlanVariant, stage_b, search_context_fp: str | None, front, stop: str | None)
PlanResult(plan: RunPlan, stage_a: tuple, variants: tuple[VariantResult, ...], perf, report_path: str)
```

* `label` 어휘는 닫힌 집합이다(회로 이름 아님). OS-2는 `baseline`·`matching`만 만든다.
* `RunPlan`은 graph 필드가 아니라 실행 입력이자 출력이다(NFR-S2).

### 5.2 계획 함수 `build_run_plan`

**서명**: OS-2 `build_run_plan(spec, topology) -> RunPlan`. OS-5(TR-2부터) `build_run_plan(spec, topology, approvals) -> RunPlan`(계획 N3.5 '그 전에는 approvals 입력도 없다'). 결정적 순수 함수이고 파일을 읽거나 쓰지 않는다. 같은 입력이면 같은 계획(NFR-S5, 두 번 불러 `fp_of`가 같음).

| 요구 `strategy` | 승인 기록 | 변형(순서대로) | card |
|---|---|---|---|
| 요구 없음 | -- | (원본, `derived` ()) label `baseline` | OS-2 |
| `matching` | -- | (원본, `derived` = (matching `OffsetBound`,)) label `matching`. 만들기 전 L4·L5 검사 | OS-2 |
| `trim`·`compare` | -- | 거부 L6 | OS-2 |
| `trim` | 없음 | (원본, ()) label `trim_phase1`. 출력 = 후보표·추천 {N, N+1}·파생 topology·승인 초안(OT §9.5 + XS-2, §15.1) | TR-2 |
| `trim` | 있음 | TR-2: 거부 `trim_phase2_not_open`. TR-3부터: 승인된 구성마다 (파생, (), trim_decl) label `trim_phase2` | TR-2 / TR-3(§11) |
| `compare` | 없음 | (원본, matching `OffsetBound`) `matching`, (원본, ()) `trim_phase1`. 만들기 전 L4·L5·L11 | OS-5(DS-1 결정 뒤, OB-16) |
| `compare` | 있음 | 승인된 구성마다 `trim_phase2`(matching은 국면 1 결과 JSON에 있고 다시 돌지 않는다, S-3) | TR-3·OS-5 |

* matching `OffsetBound` 만들기(비공개 함수, 같은 파일): `name` = `offset_matching`, `sigma_metric` = `offset_in_sigma_mv`, `sys_metric` = `offset_sys_mv`, k·limit_v·view·refs·source_fp는 `spec.offset_requirement`에서. metric 이름은 레지스트리 이름이다(회로 이름 아님).
* 변형 순서는 표 순서로 고정한다(DO-3). 순서가 결과를 바꾸지 않음은 완료 조건 2가 본다(OS-5).

### 5.3 변형 제약 집합의 주입(오케스트레이터 기본안 OB-8, 계획과 다른 점 PD-1)

**규칙**: 변형 제약 집합 = spec 판정 제약(로드한 spec 객체 하나를 모든 변형이 같이 쓴다) + 변형의 `derived`(별도 입력). spec 사본을 만들지 않는다. `derived`는 `build_search_context(..., derived=...)`의 키워드 인자로 들어가 다음 셋만 읽는다.

| 소비자 | 읽는 방식 |
|---|---|
| 커널 요청·행(§3.1) | `SearchContext.offset_bounds`(읽기 속성, 참조 칸 `derived` -- `driving`이 `spec.driving_spec`을 읽는 것과 같은 참조 방식, `E/search/search_context.py:129-131`) |
| 출발 구간(§3.2) | `start_intervals` 블록 extras에 `derived`를 더한다(입력 버전에 들어간다) |
| LUT mismatch 데이터 필수 검사(E-S12) | `derived`가 비지 않으면 offset 판정 제약과 같은 검사(fail-closed) |

**근거**(원래 취지와의 관계):
1. 계획 N3.10은 '변형마다 spec의 `constraints`를 바꾼 사본을 `SizingSpecDoc.from_sections`로 만든다'를 기본으로 두었다. 그런데 이 design에서 변형 사이에 바뀌는 것은 사용자 `constraints`가 아니다: 요구가 있으면 offset 수단 제약은 로더가 거부하므로(L2) 사용자 판정 제약은 모든 변형에서 같고, 바뀌는 것은 유도 제약(matching 합성 행)과 국면 2의 `trim_decl`(OT 경로)뿐이다. 합성 행은 `ConstraintDecl`(metric 하나) 형식으로 담을 수 없다(§3.1).
2. spec 객체를 extras로 받는 블록(`achievability`(`E/pipeline/stage_b.py:168`), `start_intervals`(`E/search/search_context.py:195`))은 spec 사본이 바뀌면 입력 버전이 바뀐다. 사본 방식에서는 `achievability`가 유도 제약을 읽지 않는데도 변형마다 다시 계산된다. 별도 입력 방식에서는 유도 제약을 실제로 읽는 블록(`start_intervals`)만 변형마다 계산되고 나머지는 색인 적중이다. 원래 취지('그 계산된 값이 나머지 최적화를 진행할 때 재사용')에 더 가깝다.
3. 함수 레지스트리 확인(2026-10-16): '변형 spec 생성' 개념 행 없음, `from_sections` 호출자는 로더 하나(`E/authoring/spec_load.py:155`). 이 방식에서는 새 spec 생성 함수가 필요 없다.

**대안(계획 문언 그대로, 사용자가 고르면 바꾼다)**: `SizingSpecDoc`에 섹션 `derived_constraints`를 두고 변형마다 `from_sections`로 사본(지문 다시 계산)을 만든다. 바뀌는 점: §5.3 표의 첫 행이 `spec.derived_constraints`를 읽고, `build_search_context` 서명이 바뀌지 않고, `achievability`가 변형마다 다시 계산된다(완료 조건 4·M2 보고에 그 수가 드러난다).

---

## 6. 실행기 `run_plan`

### 6.1 서명과 순서

```python
def run_plan(topology_path, spec_path, lut, memo, pdk_decl, lut_rule_decl, *, output_dir, settings,
             archive_root, supplies_v=None, structure_path=None, given_starts=(), model_error=()) -> PlanResult
```

(`E/pipeline/run_plan.py`, pipeline 층. 인자는 E-S13 하네스 사슬이 쓰는 값 그대로다.)

1. **실행 경계(XS-7)**: 진입에서 `S3Index`(블록 결과 색인 부분)와 `RunCounters`를 한 번 만든다. 이 둘을 모든 변형의 모든 블록 호출에 넘기고, 반환하면 버린다. 실행 사이에 넘기지 않는다.
2. **원본 단계 A**: `run_stage_a(topology_path, spec_path, lut, *, output_dir, donors, counters, supplies_v, structure_path)`. `donors`·`counters`는 필수 키워드(X-7과 같은 규칙 -- 빠지면 `TypeError`, OB-9). 결과에 `topology` 칸을 더한다(로드한 `TopologyDoc`, OB-9). 정지(`stopped`·`review_needed`)면 계획을 만들지 않고 결과 JSON에 단계 A 상태로 끝낸다.
3. **계획**: `build_run_plan(stage_a.spec, stage_a.topology)`. `SchemaRejectedError`면 결과 JSON에 사유를 쓰고 끝낸다(단계 B·탐색 전 정지, NFR-S4, OB-10).
4. **변형마다**(계획 순서):
   * 단계 B: 같은 토폴로지 변형의 단계 B 결과는 한 번만 만든다(실행 안 메모리 사전, 키 = 토폴로지 변형 `connectivity_fp`. 단계 B 입력은 spec·topology·설정이고 `derived`와 무관하다). OS-2는 변형이 하나라 한 번이다.
   * 단계 B가 `ok`가 아니면 그 변형은 `stop` = 단계 B 상태로 끝낸다.
   * 커널 컨텍스트 → `build_search_context(kctx, stage_a.spec, settings, archive_root, pdk_decl, lut_rule_decl, model_error, code_fp=stage_a.code_fp, derived=variant.derived)` → `find_front(sctx, given_starts)`. `given_starts`는 원본 topology 변형에만 넘긴다(OS-5에서 파생 topology 변형은 θ 스키마가 달라 `()`, OB-17).
5. **결과**: `<회로>.run_plan.json`(§8)을 쓰고 `PlanResult`를 돌려준다.

### 6.2 공유 범위(OS-2 / OS-5)

| 대상 | OS-2(변형 하나) | OS-5(변형 둘 이상) |
|---|---|---|
| 블록 결과 색인·`RunCounters` | `run_plan` 진입에서 하나 | 같음. 모든 변형이 같은 객체 |
| 단계 A | 원본 한 번 | 토폴로지 변형마다 한 번(같은 topology는 한 번) |
| 단계 B | 한 번 | 토폴로지 변형마다 한 번 |
| S0 탐색 블록(`search_domain`·`constraint_classes`·…) | 한 번 | 색인 공유. `start_intervals`만 `derived`가 달라 변형마다 계산 |
| S1v | 한 번 | 같은 topology 변형끼리 같은 입력(§3.1 (e)) |
| 평가 캐시(card B 뒤 `S3Index` 평가 키 부분) | 하나 | **DS-1에 따른다**(§10). 지금 키 그대로 공유는 금지(계획 N3.1-1) |

### 6.3 `run_id`(오케스트레이터 기본안 OB-11)

`find_front`의 `run_id` 지문 tuple 끝에 `sctx.offset_bounds`가 비지 않을 때만 `fp_of(sctx.offset_bounds)`를 더한다(`E/search/find_front.py:142`). 비면 지금 식 그대로다(완료 조건 1). 근거: 요구가 있는 spec과 없는 spec은 `DcInputs`가 같아 `context_fp`가 같을 수 있고(F-1), 같은 S3 루트에 쓰면 runs 줄의 `run_id`가 겹친다.

### 6.4 정지 처리

정지는 예외를 삼키지 않는다. 단계 A·B는 지금처럼 보고서와 exit code로 끝나고(`E/pipeline/stage_a.py:97-101`, `stage_b.py:128-131, :146-150`), 계획 함수 거부(`SchemaRejectedError`)는 `run_plan`이 결과 JSON `stop`에 `exc.record.to_json()`을 쓰고 같은 예외 분류의 exit code를 `PlanResult`에 담는다. 넓은 `except`는 두지 않는다(이름으로 `SchemaRejectedError`만).

---

## 7. 예산

### 7.1 변형별 E_total(XS-12 승인)

* 변형 v의 E_total,v = E_B + N_T + R_v, R_v = 2 × `len(sctx_v.domain.variables)`(X-17 식 그대로, 40 §2.4.9). E_B는 `SearchSettings.eval_budget`(모든 변형에 같은 선언값)이고, 선언이 없으면 변형마다 시간 예산에서 유도한다(card C `search_ceiling`, 변형마다 `SearchContext`가 다르므로 그대로 변형별).
* 실행 계획 전체의 커널 평가 상한 = Σ_v E_total,v. 벽시계 정지도 변형마다(`find_front` 진입에서 `deadline`, `E/search/find_front.py:81`). 실행 전체 시간은 변형 시간의 합이다.
* OS-2(변형 하나)에서는 지금 정의와 같다.

### 7.2 DS-U9 조사: 시간 예산 유도 실행의 다변형 규칙

**결론: 계획 순서·구성과 무관하면서 완료 조건 2(계획 안 결과 = 단독 결과, 비트 동일)를 지키는 규칙은 없다. DS-U9는 열림으로 남기고, 결정 S-6대로 유도 실행은 조건 2·NFR-S5에서 빼고 결과에 표기한다.**

| 후보 | 순서·구성 무관 | 조건 2(비트 동일) | 판단 |
|---|---|---|---|
| (a) 변형마다 자기 첫 n_θ + 1개 평가 시간으로 유도 | 아니다: 앞 변형의 블록 결과 적중으로 뒤 변형 평가 시간이 짧아진다 | 아니다 | 기각 |
| (b) 첫 변형의 유도값을 모든 변형에 | 아니다(계획 N10.1 DS-U9) | 아니다 | 기각 |
| (c) 블록 적중 시간을 원 계산 시간으로 되돌려 더한 '단독 환산 시간'으로 유도 | 근사로만(커널 안 블록 밖 시간은 되돌릴 수 없다) | 아니다 | 기각 |
| (d) 계획 진입 전에 변형마다 단독 시험 평가로 유도 | 구성 무관 | 아니다 | 기각(시험 평가가 색인을 채워 같은 문제가 남고, 계산을 더한다) |

**근거(결정적)**: 비트 동일의 전제가 이미 'E_B 선언'이다. 40 §2.4.13 1차 검사 전제 (가)(`E/search/find_front.py`의 `eval_budget_source`가 선언을 가리킴)는 시간 유도 실행을 비트 동일 판정 밖에 둔다. 시간 측정은 같은 변형을 단독으로 두 번 돌려도 달라지므로, 어떤 다변형 규칙도 '단독 결과'와의 비트 동일을 줄 수 없다. 그래서 이 제외는 다변형 때문에 생긴 약화가 아니라 기존 전제의 범위 표기다.

**표기**: 결과 JSON `run_plan.variants[i].budget.eval_budget_source`가 `derived_once:...`이면 `run_plan.notes`에 `{"verdict": "budget_derived", "meaning": "derived_budget_may_differ_from_standalone"}` 한 줄을 싣는다(OS-5).

### 7.3 색인 상한과 S0 벌 수(OS-5 형식)

* 상한 = Σ_블록 분할 수 × (Σ_v E_total,v + B_S0). 40 §2.4.5·§2.4.9 식의 일반화이고, 변형 하나·S0 한 벌이면 40 식 그대로다(B_S0 = 1).
* **B_S0(오케스트레이터 기본안 OB-12)** = 계획의 변형 수 + (국면 2 계획에 원본 topology 변형이 없으면 구조 비교 전용 원본 S0 한 벌, OT §10.1). OT §10.1의 '+2'(파생 S0 한 벌 + 원본 S0 한 벌)는 이 식에서 변형 하나인 국면 2 계획의 값이다.
* card C의 등록 시 fail-closed 검사(40 §2.4.5 fail-closed (5))는 이 식을 쓴다. `S3Index` 생성자가 B_S0를 받고(OT §14.2의 'S0 벌 수를 인자로' 행과 같은 자리), `run_plan`이 계획에서 계산해 넘긴다. E_total,v는 변형마다 정해지는 순간 색인에 더한다(E_total 미정이면 정해지는 순간 한 번 확인 -- 40 §2.4.5 (5) 규칙 그대로).
* 결과 JSON: `run_plan.shared.block_index_entries`·`block_index_bound`(계획 전체 값). 각 변형 runs 줄 `perf.block_index_bound`에도 같은 계획 전체 값을 싣는다.

---

## 8. 결과 JSON 칸

파일 `<회로>.run_plan.json`(`output_dir`, 단계 A·B 보고서와 같은 폴더). 최상위 키 `run_plan`.

| 칸 | 내용 | card |
|---|---|---|
| `strategy`, `phase` | 계획 값(없으면 null) | OS-2 |
| `requirement` | `{offset_in_max_v, coverage_multiple, strategy, view, sources}` 또는 null | OS-2 |
| `variants[]` | `{index, label, topology_fp, variant_fp, derived: [OffsetBound 칸(§3.4)], budget: {eval_budget, eval_budget_source, e_total, gate_reserve}, stage_b_status, run_id, s3_dir, stop, front_points}` | OS-2(OS-5에서 여러 개) |
| `variants[].front_points[]` | front 점마다 `{point_id, power_w, area_m2, derived_rows: [{name, c, active, value_v, limit_v, margin_v}]}`. `margin_v` = limit_v − value_v(보고, 판정은 c) | OS-2 |
| `stop` | 계획 함수 거부·단계 A 정지 사유(`exc.record.to_json()`) | OS-2 |
| `shared` | `{block_index_entries, block_index_bound, b_s0, s1v_computes, s1v_inputs, kernel_calls_total}` | OS-2(값), OS-5(다변형 의미) |
| `notes[]` | `budget_derived`(§7.2), compare 국면 1이면 `{"verdict": "not_a_recommendation"}`와 R1·R2 한계 문구(offset trim은 1/f·drift를 보정하지 않음) | OS-5 |

* `derived_rows`의 c·active는 S3 evals 줄 `constraints`의 `req:offset_matching<=` 행과 같은 값이다(같은 `EvalResult`에서 읽는다 -- 사본이 아니라 출력 칸).
* `value_v`·`margin_v`를 내기 위해 커널 결과에서 다시 계산하지 않는다: 합성 행 함수가 행과 함께 (v, L)을 `EvalResult` 보고 칸으로 남기고(OB-13, §3.1 행 정의와 같은 계산의 결과), `run_plan`이 front 점의 그 칸을 옮겨 쓴다.
* 권고·판정 문장은 싣지 않는다(FR-S7).

---

## 9. 비교 도구(OS-3)

* **위치(DO-7, OB-14)**: `skills/analog-gmid-design/tools/offset_compare/`(엔진 밖, 기존 `tools/spice_oracle/`과 같은 구조). 파일 `compare.py`(진입점 `compare_offset_results(result_paths) -> ComparisonTable`과 CLI `main(argv)`), `README.md`, test `tests/test_compare.py`.
* **입력**: `<회로>.run_plan.json` 둘 이상(국면 1 결과의 matching 변형, 국면 2 결과의 trim 변형). 엔진을 import하지 않는다(`gmid_engine` import 0, test가 AST로 확인). 엔진은 이 도구의 출력을 입력으로 받지 않는다.
* **칸**(변형마다 한 열): 출처(파일 경로, `run_id`, `code_fp`, `variant_fp`, label), 공통 판정 선언(1/f metric·op·값, `area_search_m2` 상한 -- 두 결과의 spec 판정 제약에서), 요구(`offset_in_max_v`, k), front 점별 (전력, 면적), offset 한계 대비 여유(matching = `margin_v`, trim = `offset_in_max_v` − `residual_bound_v`(OT §10.4)), 유도 제약 판정(c, active), 공통 판정 행의 c.
* **불일치 표시**: 두 결과의 `code_fp`가 다르면, 공통 판정 선언·요구 값이 다르면 표 머리에 그 사실을 쓴다(조용히 비교하지 않는다, 계획 N3.8).
* **금지**: 판정·권고 문장, 가중치, 문턱, '어느 쪽이 낫다'. 출력은 표(JSON + md)뿐이다.

---

## 10. DS-1·DS-2 조건부 절(열린 결정 -- 하나를 고르지 않는다)

DS-1·DS-2는 M2 뒤 사용자가 고른다(S-5). 아래는 선택지마다 이 design이 바뀌는 지점이다. 모두 OS-5 범위다. 공통 전제: 이 design에서는 같은 topology 변형끼리 spec 판정 제약·S1v 입력이 같고(§3.1 (e)·§5.3), 변형 사이에 다른 것은 유도 제약(합성 행과 그 metric 요청)뿐이다.

### 10.1 DS-1 (가) 평가 키 부분만 변형별

* **바뀌는 곳**: `E/search/s3_index.py`(card B 산출) -- 블록 결과 부분(`find`·`register`·`find_failure`·`register_failure`)과 평가 키 부분(`get`·`failure`·…)을 두 객체로 나눈다. `run_plan`은 블록 결과 부분 하나를 모든 변형에 넘기고, 평가 키 부분은 변형마다 `build_search_context`가 새로 만든다.
* **완료 조건 3**: 같은 topology 변형이 같은 θ를 밟으면 같은 평가 키가 변형마다 다시 계산된다 -- 조건 3과 모순. **DS-U7 결정('완료 조건 3 약화 안 함', S-6)과 충돌**하므로 (가)를 고르려면 둘 중 하나를 다시 결정해야 한다(§16.4).
* **S3**: `variant` 칸으로 줄을 구분한다(§3.3).

### 10.2 DS-1 (나) 평가 분리

* **바뀌는 곳**: (i) 커널 요청 = 계획 안 모든 변형의 요청 합집합(`ss_constraints` 요청 ∪ 모든 변형의 `OffsetBound` 요청). `run_plan`이 합집합을 만들어 모든 변형의 `SearchContext`에 같은 값으로 넘긴다. (ii) 평가 캐시 값(봉인·metric·spec 행·ls 행)은 변형과 무관하고 `S3Index` 하나를 계획 전체에서 공유한다. (iii) 합성 행(`req:`)은 변형별 판정 단계(`ss_constraint_rows`의 bounds 부분을 커널 밖 변형별 함수로 분리)가 캐시 값의 묶음에서 만든다. `EvalResult`는 변형 무관 부분과 변형별 행으로 나뉜다.
* **이 design에서 줄어드는 범위**: spec 판정 제약이 변형 사이에 같으므로 (iii)은 합성 행 하나다. S1v 투영 좁히기(DS-2 (나))는 필요 없다(§3.1 (e)).
* **완료 조건 3**: 지킨다. **S3**: evals 줄은 평가 키마다 한 줄(변형 무관 부분) + 변형별 행 칸 `rows_by_variant`(형식 변경, XS-13 범위).

### 10.3 DS-1 (다) 키 분리

* **바뀌는 곳**: `EvalKey`에 칸 `constraint_set_fp`(§3.3)를 더하거나 `context_fp` 지문 tuple에 넣는다(`E/search/eval_key.py`, `search_context.py:214`). `S3Index` 하나를 공유한다.
* **완료 조건 3**: 형식상 지킨다. 같은 θ가 변형마다 커널을 한 번씩 거치고, 크기 결정 블록은 색인 적중, offset metric 블록은 요청 목록이 달라 다시 계산된다(XS-8). 요구 없는 실행은 `constraint_set_fp`를 넣지 않는 규칙이어야 완료 조건 1이 지켜진다(변형 하나·유도 제약 없음이면 칸 없음).

### 10.4 DS-2

* (가) 받아들임 / (나) S1v 투영 좁히기. 이 design(§3.1 (e))에서는 같은 topology 변형끼리 S1v 입력이 같아 두 선택지의 차이가 생기지 않는다. 국면 2 파생 topology는 topology가 달라 어느 쪽이든 계산된다(정상). 그래서 DS-2를 '대상 없음'으로 닫을지 사용자에게 확인을 받는다(§16.3 PD-3). 확인 전에는 §3.5의 칸(`s1v_computes`·`s1v_inputs`)을 그대로 내서 사실을 보인다.

---

## 11. 국면 규칙·승인 기록(OS-5 형식, TR card 배정 -- N-22)

### 11.1 국면 규칙

* 국면은 승인 기록 유무로만 정한다(DO-2). 정해진 위치 = topology 파일과 같은 폴더의 `<circuit>.trim.json`(OT §8.1). 진입 인자로 국면을 고르지 않는다(S-2, `trim_approval_path` 인자 없음).
* 승인 파일이 있는데 국면 1을 다시 돌려면 사용자가 파일을 그 위치에서 치운다(DO-9). 엔진은 승인 파일을 고치지 않는다.
* 낡은 승인(OT §8.3 결속 불일치)은 국면 1로 돌아가지 않고 `trim_approval_stale`로 정지한다.

### 11.2 TR card별 배정(N-22, 오케스트레이터 기본안 OB-18)

| 일 | card | 내용 | OT 원래 배정과 대조 |
|---|---|---|---|
| 승인 기록 없음 → 국면 1 | TR-2(+OS-5) | `build_run_plan` trim 행 국면 1(단일 변형), `run_trim_candidates`를 `run_plan`의 trim 국면 1 변형 뒤에 부른다 | OT §10.3a 방향(pipeline → search·metrics) 그대로 |
| 승인 기록 있음 → 국면 2 미구현 fail-closed | TR-2 | `run_plan`이 정해진 위치에 파일이 있는지만 본다(읽지 않는다). 있으면 `build_run_plan(..., approvals=<경로 표지>)`가 `trim_phase2_not_open`(`SchemaRejectedError`, gate `run_plan`)으로 거부 | OT에는 없던 정지(국면 규칙이 새로 생겨서) |
| 승인 기록 로더 `load_trim_approval` | **TR-3** | 정해진 위치의 파일을 읽어 `approvals`로 넘긴다 | OT §14.1은 TR-1. **옮긴다**(계획과 다른 점 PD-2): TR-1에서는 부르는 곳이 없어 만들면 배선을 못 지킨다 |
| 결속 검사·낡은 승인 정지(`bind_trim`) | TR-3 | OT §8.3 1~5 그대로 | OT §8.3 TR-3 그대로 |
| 국면 2 분기(파생 topology 변형의 단계 A, 원본 S0 비교 벌) | TR-3 | 계획의 국면 2 행이 생기고 `run_plan`이 파생 topology로 단계 A를 돈다. 구조 동일 검사(`compare_trim_structure`)는 TR-4 | OT §4·§14.4의 '`run_stage_a`(2단계)' 자리를 `run_plan` 국면 2 행으로 바꾼다 |
| 국면 2 변형의 단계 B·탐색 | TR-5b | TR-5b 전에는 국면 2 변형이 단계 A 뒤 `trim_phase2_search_not_open`으로 멈춘다(fail-closed). TR-5b가 이 정지를 지운다 | OT §15 TR-5b '시험 회로에서 2단계 front 생성'과 같은 시점 |
| compare 국면 1(다변형), 변형 사이 공유, 변형 정체 칸, Σ 상한, 변형별 예산 칸 | OS-5 | DS-1 결정 뒤. DS-1 미결이면 compare 행은 L6 거부를 유지하고 trim 단독(단일 변형)만 TR-2에서 연다(OB-16) | -- |
| 최종 비교 | OS-3 | TR-6 뒤 | -- |

### 11.3 `approvals` 형식(OS-5)

* TR-2: `approvals` ∈ {None, `ApprovalFilePresent(path)`}(파일 존재 표지, 내용 없음).
* TR-3부터: `approvals` ∈ {None, `TrimApprovals`(OT §8.1 형식을 §15.1의 XS-2 개정대로 읽은 값)}. `ApprovalFilePresent`는 TR-3에서 지운다(옛 경로 삭제).

---

## 12. 파일 분할

### 12.1 새 파일(규칙 A: 파일당 진입점 하나)

| 파일(`E/` 기준, 도구는 skill 기준) | 진입점 | 층 | card |
|---|---|---|---|
| `authoring/spec_offset_requirement.py` | `offset_requirement_declaration(raw, topology, feedback)` | authoring | OS-2 |
| `authoring/spec_offset_conflicts.py` | `offset_requirement_conflicts(requirement, constraints)` | authoring | OS-2 |
| `pipeline/run_plan_values.py` | (값 형식 모듈: `PlanVariant`·`RunPlan`·`VariantResult`·`PlanResult`) | pipeline | OS-2 |
| `pipeline/run_plan_build.py` | `build_run_plan(spec, topology)`(OS-5부터 `approvals`) | pipeline | OS-2 |
| `pipeline/run_plan.py` | `run_plan(...)` | pipeline | OS-2 |
| `tools/offset_compare/compare.py` | `compare_offset_results(result_paths)`(+ CLI) | 도구 | OS-3 |

값 형식은 writer 층에 둔다: `OffsetRequirement`는 로더가 만들므로 `authoring/spec_model.py`, `OffsetBound`는 search가 소비하고 pipeline이 만드므로 search 값 모듈 `search/search_values.py`(층 순서상 pipeline은 search를 import할 수 있다).

### 12.2 고치는 파일(범위)

| 파일 | card | 범위 |
|---|---|---|
| `authoring/spec_schema.py`(`HUMAN_OPTIONAL`), `spec_load.py`(섹션·충돌 검사 호출, `sections`에 칸), `spec_model.py`(`OffsetRequirement`, `SizingSpecDoc.offset_requirement`, `SECTION_GROUPS`), `spec_sources.py`(`ALLOWED_KINDS`), `__init__.py` | OS-2 | 부분 |
| `search/search_values.py`(`OffsetBound`) | OS-2 | 부분 |
| `search/ss_constraints.py`(`ss_constraint_rows(bundle, declared, model_error=(), bounds=())` -- 합성 행, §3.1) | OS-2 | 부분 |
| `search/kernel.py`(:130 요청에 bounds 요청, :148 bounds 전달, 합성 행 보고 칸) | OS-2 | 부분 |
| `search/search_context.py`(`build_search_context(..., derived=())` 키워드, 참조 칸·`offset_bounds` 속성, mismatch 검사, `start_intervals` 호출) | OS-2 | 부분 |
| `search/start_intervals.py`(extras), `search/iv_context.py`(`sigma_targets_v`), `search/iv_matching_l.py`(σ 목표) | OS-2 | 부분 |
| `search/find_front.py`(:97 검증 출처에 bounds metric, :142 `run_id`) | OS-2 | 부분 |
| `search/search_values.py`(`EvalResult` 합성 행 보고 칸) | OS-2 | 부분 |
| `pipeline/stage_a.py`(`donors`·`counters` 필수 키워드, `StageAResult.topology`), `pipeline/__init__.py` | OS-2 | 부분 |
| `metrics/ss_evaluate.py` docstring(`constraints`에 `MetricRequest`도 받음 -- 코드 무변경, E-S8) | OS-2 | 문구 |
| `search/s3_index.py`(B_S0 인자 -- card C 상한 식) | OS-5 | 부분 |
| S3 `variant` 칸(`search/kernel.py` `_record`, `search/find_front.py` runs 줄) | OS-5 | 부분 |
| DS-1 선택지의 파일(§10) | OS-5 | 선택에 따름 |
| CONTRACT(`authoring`·`SPEC_CONTRACT`·`search`·`pipeline`·`metrics`), `_module_map.py`, 함수 레지스트리 §2 | 각 card | 갱신 |

* **XS-10 범위 확인**: 계획 N9는 matching 확장을 '`ss_constraint_rows` 한 곳과 `iv_matching_l` 한 곳'으로 design이 닫는다고 했다. 이 design의 실제 search 변경은 그 둘에 더해 입력을 나르는 자리(`kernel.py` 요청·호출, `search_context.py` 키워드·속성, `start_intervals.py`·`iv_context.py` 전달, `find_front.py` 기록)다. 계산 규칙이 생기는 곳은 그 두 곳뿐이고 나머지는 전달이다. 범위 표기가 계획 문언보다 넓어 계획과 다른 점 PD-4로 보고한다.

### 12.3 층·모듈 지도·test·레지스트리

* 층 순서(규칙 C) 그대로: authoring < … < search < pipeline. 역방향 import 없음. 도구는 엔진 밖.
* `_module_map.py`: 새 엔진 파일마다 `ModuleEntry(경로, "entry", 진입점, 설명, (계획 근거))`.
* test 1:1(규칙 H): `E/tests/<패키지>/test_<파일>.py`. 9회로 실행은 `E/tests/integration/`.
* 함수 레지스트리 §2(2026-10-16 확인: 아래 개념 행 없음): 'offset 요구 → 실행 계획(변형 목록)' = `pipeline.build_run_plan`, '실행 계획 실행기(단계 A~탐색 사슬)' = `pipeline.run_plan`, 'matching 합성 offset 판정 행' = `search.ss_constraint_rows`(bounds), 'offset 결과 나란히 보기(출력 조회, 엔진 밖)' = `tools/offset_compare`. 대체하는 옛 함수는 없다(엔진에 사슬 함수가 없었다, E-S13).

---

## 13. 배선표(만들면 배선)

| 새 함수·칸 | 호출 경로 | 옛 경로 대체 |
|---|---|---|
| `offset_requirement_declaration`·`offset_requirement_conflicts` | `load_sizing_spec`(섹션 검사 뒤) | -- |
| `build_run_plan` | `run_plan` 3단계 | -- |
| `run_plan` | 엔진 사슬 진입점. **제품 호출자(U16 `run_gmid_design_pipeline`)가 아직 없다** -- §16.4 W-1(승인 요청). 같은 변경에서 수작업 사슬을 쓰는 하네스·test(`E/tests/integration/nfr4_run_dump.py:376-401`과 card B·C의 `test_g10_no_recompute_9circuits`)를 `run_plan`으로 바꾼다 | 하네스의 수작업 사슬 |
| `ss_constraint_rows`의 bounds | `kernel.evaluate` | -- |
| `SearchContext.offset_bounds`, `build_search_context(derived=)` | `run_plan` 4단계 → 커널·출발 구간·mismatch 검사 | -- |
| `StartView.sigma_targets_v` | `matching_bounds` | `iv_matching_l.py:107, :123`의 mv 목록 |
| `run_stage_a(donors=, counters=)` | `run_plan` 2단계 | card B의 '`run_stage_a` 진입에서 생성'(XS-7, §15.2) |
| `compare_offset_results` | 사용자 CLI(국면 2 결과가 생긴 뒤, OS-3) | -- |

---

## 14. card 범위·완료 조건·test 목록

공통: 순서 = design 승인 → test(interface card만 보고) → code → 독립 판정. 완료 조건마다 (a) 배선 증거(§13 행의 호출 grep + 실행 경로 test), (b) 상위 N6.3 graph 정본·재계산 계수·파일 분할 확인, (c) design 대 구현 gap 분석을 넣는다. test 기대값은 피검 함수를 부르지 않는다. 기능 완료 조건 번호는 계획 N7.2다.

| card | 범위 | 선행 | 완료 조건 |
|---|---|---|---|
| **OS-2** | §4 L1~L6·L12, §3.1·§3.2(G-S1·G-S2), §5(요구 없음·matching 행, trim·compare 거부), §6(단일 변형), §8(OS-2 칸), XS-7 실행 경계, `run_id`(§6.3), 하네스 사슬 대체 | OS-0 승인, XRUN-F1 card C 병합, W-1 승인, F-1 값(§16.4) | 기능 조건 1(요구 없는 9회로 비트 동일, §3.6 제외), 5(L1~L6 거부 test가 실제로 거부), 7(배선), 8. 더해: matching fixture 실행이 front 점마다 `req:offset_matching<=` 행과 `run_plan.json` `derived_rows`를 낸다, `RunCounters`·색인 인스턴스가 계획당 하나다 |
| **OS-5** | §3.3 S3 칸, §7.1·§7.3, §10 DS-1·DS-2 선택지 구현, §11(TR-2 몫), compare 국면 1·L11 | OS-2, TR-2 함께(U16 뒤, T-15), DS-1 결정(compare 몫) | 기능 조건 2(E_B 선언 실행 한정, §7.2), 3, 4 |
| **TR-3 몫** | §11.2 로더·결속·국면 2 분기·탐색 게이트 | OT TR-3 선행 그대로 | 낡은 승인 다섯 경로 정지, 국면 2 변형이 단계 A 뒤 `trim_phase2_search_not_open`으로 멈춤 |
| **TR-5b 몫** | 탐색 게이트 삭제 | OT TR-5b 선행 | 시험 회로 국면 2 front(OT §15 그대로) |
| **OS-3** | §9 | OS-2, OS-5, TR-6 | 기능 조건 6(엔진 import 0, 권고 문장 0, 불일치 표시) |

### 14.1 test 목록(독립 oracle)

| card | test 파일 | 내용 |
|---|---|---|
| OS-2 | `tests/authoring/test_spec_offset_requirement.py` | L1 위반 픽스처마다 사유 코드, 섹션 결정 대기 → `offset_requirement` None + `pending` 표지, 값 하나 대기 → `type`, 출처 kind `pending_spice`·`reference` 거부, L3(입력 포트 둘이 단일 역할인 손 topology → `offset_requirement_view_required`), 포트 뷰 값 = 같은 topology에서 view 없는 offset 제약이 받는 뷰(손으로 쓴 `ViewDecl`과 대조) |
| OS-2 | `tests/authoring/test_spec_offset_conflicts.py` | L2: metric 셋 × 출처 kind 셋 각각 거부, `pending_constraints`의 offset 이름은 거부 안 함, 요구 없으면 offset 제약 그대로 통과 |
| OS-2 | `tests/search/test_ss_constraints.py`(추가) | 합성 행: 손으로 정한 σ_mv·sys_mv·resolution·k·L에서 c를 test 안 산식(십진 손 계산, `MILLI` 대신 단위 정의 문장으로 쓴 값)과 대조, 모델 오차 바닥, None → 미측정 코드 합집합, resolution None·0 사유, 봉인 안 된 점, bounds 비면 행 목록이 지금과 같음 |
| OS-2 | `tests/search/test_kernel.py`(추가) | bounds가 있으면 두 metric 요청이 `ss_evaluate`로 간다(관찰: `metrics_aux` extras 요청 목록), 없으면 요청 목록이 지금과 같음 |
| OS-2 | `tests/search/test_iv_matching_l.py`(추가) | 같은 손 회로에서 (가) `offset_in_sigma_mv <= x` spec과 (나) 요구 L, k(L/k = x V 환산)인 유도 제약이 같은 L 하한 Bound를 낸다, 요구 없는 경로는 지금 값과 비트 동일 |
| OS-2 | `tests/search/test_search_context.py`(추가) | `derived` 비지 않고 LUT mismatch 데이터 없음 → 거부, `offset_bounds` 속성이 넘긴 tuple 그대로 |
| OS-2 | `tests/pipeline/test_run_plan_build.py` | 요구 없음 → 변형 하나(`baseline`, `derived` ()), matching → `OffsetBound` 칸이 spec 요구 값·참조 경로와 같음, trim·compare → L6, L4(단일 출력·노드 목표 없음 → 거부, 노드 목표 있음 → 통과, 차동 출력 → 검사 없음), L5(레지스트리 단위를 바꾼 가짜 서명 주입 → 거부), 두 번 불러 `fp_of` 같음 |
| OS-2 | `tests/pipeline/test_run_plan.py` | 색인·`RunCounters`가 실행당 하나(생성 계수), 단계 A 정지 → 계획 없음·보고서 상태, 계획 거부 → 단계 B·탐색 호출 0(관찰), `run_plan.json` 칸(§8), `run_stage_a`에 `donors` 빠지면 `TypeError` |
| OS-2 | `tests/search/test_find_front.py`(추가) | bounds 없으면 `run_id`가 지금 식과 같음(test 안에서 같은 식으로 계산), 있으면 다름 |
| OS-2 | `tests/integration/test_run_plan_baseline_9circuits.py` | 기능 조건 1: base 하네스 결과 대 `run_plan` 결과(§3.6 제외 목록은 검증자 소유) -- 판정은 auditor가 격리 복제본에서 |
| OS-2 | `tests/integration/test_run_plan_matching_fixture.py` | matching fixture spec(origin fixture, §16.4 F-1) 실행: front 점마다 `req:` 행, `derived_rows`의 c가 S3 evals 행과 같음 |
| OS-5 | `tests/pipeline/test_run_plan_multi.py`, `tests/integration/test_run_plan_compare_phase1.py` | 기능 조건 2(변형마다 단독 계획 결과와 비트 동일, 순서 뒤집기), 3(`recomputes_same_input` 0, 같은 평가 키 재계산 0), 4(S1 계산 수 = 변형 하나일 때, `s1v_computes`·`s1v_inputs`), L11, `variant` 칸, 상한 식(B_S0) |
| OS-3 | `tools/offset_compare/tests/test_compare.py` | AST로 `gmid_engine` import 0, 출력 문자열에 권고 어휘 없음(어휘 목록은 test 작성자 소유), `code_fp`·공통 판정·요구 값 불일치 표시, 손으로 만든 결과 JSON 두 개에서 칸 대조 |

---

## 15. 다른 문서 개정안(OS-0과 함께 재승인 -- S-4·XS 승인 범위)

### 15.1 offset-trim design(OT) 개정안

| OT 절 | 지금 | 개정안 | 근거 |
|---|---|---|---|
| §4 흐름 | 진입 인자 `trim_approval_path`로 1·2단계 선택, `trim_approval_without_decl` | 흐름 그림을 다음으로 바꾼다: `run_plan(topology, spec)` → 원본 단계 A → `build_run_plan(spec, topology, approvals)`(approvals = 정해진 위치 `<circuit>.trim.json`이 있으면 읽은 값) → 국면 1(승인 없음): 원본 변형 탐색 → `run_trim_candidates` / 국면 2(승인 있음): `bind_trim` → 파생 topology 변형 단계 A(+ 원본 S0 비교 벌) → 단계 B → 탐색. 진입 인자 분기와 `trim_approval_without_decl`을 지운다. '선언이 없으면 새 블록은 하나도 불리지 않는다'는 '요구가 없거나 `strategy`가 `matching`이면'으로 | XS-4, S-2, §11 |
| §5.1 스키마 | `offset_trim` = {`residual_offset_v`, `coverage_multiple`, `trim_temperature_c`} | `coverage_multiple`을 지운다. k는 `offset_requirement.coverage_multiple`(§4.3). `TrimSpec`(§6.1)의 `coverage_multiple` 칸은 요구에서 채운다(값 형식 그대로, 출처가 바뀐다) | XS-6, DS-U3 |
| §5.2 로더(D-4) | `offset_in_sigma_mv` 공존 거부, `offset_excess`·`offset_sys_mv` 강등 | 표 전체를 이 design §4.2 L2·L7~L10으로 바꾼다. 강등(`trim_demoted_constraints`)과 `trim_constraint_conflicts`·`spec_trim_conflicts.py`를 지운다 | XS-1, DS-U1·U2 |
| §8.1 승인 형식(딸린 개정) | 구성 하나(`derived_connectivity_fp` 하나, `selections`) | `configurations: [{derived_connectivity_fp, selections:[...]}]`(승인한 구성마다 하나, N과 N+1을 둘 다 승인하면 둘). 국면 2 변형 = 구성마다 하나 | XS-2의 결과(OB-19) |
| §8.1·§8.3-4 `spec_trim_fp`(딸린 개정) | spec `offset_trim` 섹션 지문 | `fp_of((offset_trim 섹션, offset_requirement 섹션))`. k·한계가 바뀌면 재승인(X-T11 취지 그대로) | XS-6의 결과(OB-15) |
| §9.4 추천 | 추천 N 하나(가능한 최소 N), m = min_p m_max,p(N) | 추천 구성 둘: N_rec(지금 규칙)과 N_rec + 1. N_rec + 1의 m = min_p m_max,p(N_rec + 1)(같은 집계 규칙, DS-U6). 집계 대상 어떤 점에서 m_max,p(N_rec + 1)이 정의되지 않으면 N_rec + 1 구성은 내지 않고 후보표에 사유 `trim_config_next_undefined`를 적는다. 새 상수 없음 | XS-2, DS-U6 |
| §9.5 출력 | (쌍, 극성)마다 추천 하나의 파생 topology·표·승인 초안 | 구성마다(N_rec, N_rec + 1) 파일 셋: `<circuit>.trim_d<순위>_n<N>.topology.json`·`.topology.md`·`.approval_draft.json`. 승인 초안은 §8.1 개정 형식 | XS-2 |
| §10.1 색인 상한 | Σ 분할 수 × (E_total + 2) | 이 design §7.3 식 Σ 분할 수 × (Σ_v E_total,v + B_S0). 국면 2 변형 하나·원본 비교 벌 하나면 '+2'와 같다 | XS-12, §7.3 |
| §10.4·§10.6·§17(딸린 개정) | k = spec `offset_trim.coverage_multiple` | k = 요구 `coverage_multiple` | XS-6 |
| §10.8 의미 전환 표(딸린 개정) | `offset_in_sigma_mv` 공존 거부, 강등 | '요구가 있으면 offset 수단 제약 셋 다 로더 거부(§4.2 L2)'. `iv_matching_l` L 하한 끔은 trim 변형에 유도 제약이 없어서 자연히 꺼진다(§3.2: 유도 제약이 없고 사용자 offset 제약도 없다) | XS-1 |
| §13 결과 JSON(딸린 개정) | `trim.demoted_constraints`, `trim.mode` | `demoted_constraints` 삭제. `mode`는 `run_plan.phase`와 같은 값(사본 대신 `run_plan.json` 참조) | XS-1, S-2 |
| §14.1·§14.2·§14.4(딸린 개정) | `spec_trim_conflicts.py`, `load_trim_approval` TR-1, `stage_a.py`의 `trim_approval_path` 인자 | `spec_trim_conflicts.py` 삭제, `load_trim_approval`은 TR-3(§11.2, PD-2), `stage_a.py` 인자 행 삭제(국면 분기는 `run_plan`) | S-2, N-22 |
| §15 TR-1 행(딸린 개정) | D-4 공존 처리·강등 test | L7~L10 거부 test로 바꾼다. 승인 로더 test는 TR-3으로 | XS-1, PD-2 |
| §16.1 시험 회로 요구 조건(딸린 개정) | `offset_in_sigma_mv` 없음, `offset_trim`(V_res·k·온도) | offset 수단 제약 셋 다 없음, 요구 섹션(`strategy` = `trim`, k, `offset_in_max_v` ≥ V_res), `offset_trim`(V_res·온도) | XS-9 |
| §18.2(딸린 개정) | X-T11 | X-T11 문구에 '요구 섹션 포함'을 더한다 | OB-15 |

### 15.2 40 design 개정안(XS-7·XS-12)

| 40 절 | 지금 문구 | 개정안 |
|---|---|---|
| §2.4.5 '수명' 행 | "실행 하나(…단계 A부터 -- S1·S1v 블록 포함). 실행 경계(`run_stage_a` 진입)에서 `RunCounters`(§2.4.9)와 함께 새로 만들고, 그 실행의 모든 블록 호출에 같은 객체를 넘기며, 실행이 끝나면 버린다." | "실행 하나(사용자 결정 X-12: 단계 A부터). 실행 = 실행 계획 하나(offset-strategy design §6). 실행 경계(`run_plan` 진입)에서 `RunCounters`와 함께 새로 만들고, 실행 계획의 모든 변형의 모든 블록 호출에 같은 객체를 넘기며, `run_plan`이 반환하면 버린다. `run_stage_a`는 두 객체를 필수 키워드로 받는다(만들지 않는다). 실행 사이에 넘기지 않는다(§2.4.3)." |
| §2.4.5 '전달' 행 | "단계 A는 … 단계 결과(`StageAResult`)에 참조로 싣는다" | "`run_plan`이 만든 두 객체를 단계 A가 받아 … 단계 결과에 참조로 싣는다" |
| §2.4.5 '상한' 행 | "… ≤ Σ_블록 분할 수 × (E_total + 1) …" | "… ≤ Σ_블록 분할 수 × (Σ_v E_total,v + B_S0)(offset-strategy design §7.3; 변형 하나·S0 한 벌이면 (E_total + 1))" |
| §2.4.9 E_total 정의 | "실행 하나의 커널 평가 수 상한" | "**변형 하나**의 커널 평가 수 상한(XS-12). 실행(= 실행 계획) 전체 상한은 Σ_v E_total,v. 변형 하나인 실행에서는 둘이 같다" |
| §2.4.9 `RunCounters` 문단 | "실행 경계 = `run_stage_a` 진입" | "실행 경계 = `run_plan` 진입(§2.4.5 '수명')" |
| §2.4.9 증거 집합 상한 | "(+1 = S0 수준 계산 한 번)" | "(+B_S0 = S0 수준 계산 벌 수, offset-strategy design §7.3)" |

### 15.3 trim 시험 회로 spec 재작성안(XS-9, 값은 사용자 자리)

T-24(회로 = library `two_stage_ota` 연결 사본 `trimfx_two_stage_ota`), T-25(V_res·k·온도 값), T-27(two_stage_ota spec 결정값 재사용), T-28(위치 `assets/fixture/trim/`, TR-1 병합 뒤 반영)에서 바뀌는 것만 적는다.

```json
"human": {
  "offset_requirement": {
    "offset_in_max_v":   {"value": "<사용자 값 -- DS-U8, 로더 조건: ≥ residual_offset_v>", "source": {"kind": "user_spec", "record": "<결정 기록>", "decided": "<날짜>"}},
    "coverage_multiple": {"value": "<T-25의 k 값 그대로>", "source": {"kind": "user_spec", "record": "T-25(2026-10-15) -- offset_trim.coverage_multiple 에서 옮김(XS-6)", "decided": "2026-10-15"}},
    "strategy":          {"value": "trim", "source": {"kind": "user_spec", "record": "<결정 기록>", "decided": "<날짜>"}}
  },
  "offset_trim": {
    "residual_offset_v":  {"value": "<T-25 값 그대로>", "source": "<T-25 출처 그대로>"},
    "trim_temperature_c": {"value": "<T-25 값 그대로>", "source": "<T-25 출처 그대로>"}
  },
  "constraints": "<two_stage_ota spec 판정 제약(T-27) 그대로, 단 offset_excess 항목은 뺀다(DS-U2)>"
}
```

* `meta.origin` = `fixture`, `meta.topology_fp` = 사본 topology의 `connectivity_fp`(T-24).
* T-27의 'offset_excess 유지(강등 경로 확인용)'는 강등 경로가 없어져(XS-1) 대상이 사라진다. 이 사실을 재승인 때 함께 올린다.
* `strategy` 값 `trim`은 시험 회로의 목적(2단계 검증, T-9)에서 나오는 값이지만 spec 값이므로 사용자 승인 대상이다.
* 반영 시점: TR-1 병합 뒤(T-28 그대로). 그 전에는 쓰지 않는다.

---

## 16. 결정 상태

### 16.1 오케스트레이터 기본안(사용자 결정 아님 -- 원칙 근거, 사용자가 바꿀 수 있음)

| ID | 항목 | 기본안과 근거 |
|---|---|---|
| OB-1 | G-S1 형식 | 합성 제약 행(`ss_constraint_rows`). 새 metric 아님(§3.1 근거 1~3) |
| OB-2 | 단위 환산 | 레지스트리 단위 `mv` → `core.MILLI`, 그 밖 단위는 거부 L5(§3.1 (c)) |
| OB-3 | 유도 제약 view | 기본 포트 뷰(사용자 offset 제약이 view를 안 적을 때와 같은 규칙), 로더가 정함(§3.1 (d)) |
| OB-4 | S1v | 유도 제약은 S1v 씨앗·extras 밖(§3.1 (e)) |
| OB-5 | G-S2 σ 목표 | L/k(필요조건 중 가장 느슨한 값, 분할 비율 발명 없음)(§3.2) |
| OB-6 | 공존 거부 범위 | `constraints` 항목은 출처 kind와 무관하게 거부, `pending_constraints`는 거부 안 함(§4.2 L2) |
| OB-7 | 검사 위치 | 기준 DC(L4)·단위(L5)·미개방(L6)·compare 공통 판정(L11)은 계획 함수(층 순서와 방식별 규칙)(§4.2) |
| OB-8 | 변형 제약 주입 | spec 사본 대신 별도 입력 `derived`(§5.3) -- 계획과 다른 점 PD-1 |
| OB-9 | 실행 경계 구현 | `run_stage_a`에 `donors`·`counters` 필수 키워드, `StageAResult.topology` 칸(§6.1) |
| OB-10 | 실행 순서 | 원본 단계 A → 계획 함수(계획 거부는 단계 A 뒤·단계 B 전)(§6.1) |
| OB-11 | `run_id` | 유도 제약이 있을 때만 지문에 더함(§6.3) |
| OB-12 | B_S0 | 변형 수 + 국면 2 원본 비교 벌(§7.3) |
| OB-13 | 합성 행 보고 칸 | `EvalResult`에 (v, L) 보고 칸, 결과 JSON은 옮겨 쓴다(§8) |
| OB-14 | 비교 도구 | `tools/offset_compare/compare.py`(§9) |
| OB-15 | 승인 결속 지문 | `spec_trim_fp`에 요구 섹션 포함(§15.1) |
| OB-16 | compare와 DS-1 | DS-1 미결이면 compare는 L6 거부 유지, trim 단독은 TR-2에서 연다(§11.2) |
| OB-17 | `given_starts` | 원본 topology 변형에만(§6.1) |
| OB-18 | N-22 배정 | 승인 로더·결속·국면 2 분기 = TR-3, 탐색 게이트 해제 = TR-5b(§11.2) |
| OB-19 | 승인 형식 | 구성 목록(N, N+1 둘 다 승인 가능)(§15.1) |

### 16.2 계획과 다른 점(승인 필요)

| ID | 내용 | 계획 문언 |
|---|---|---|
| PD-1 | 변형 제약 집합을 spec 사본(`from_sections`)이 아니라 별도 입력 `derived`로 넣는다(§5.3). 원래 취지(재사용)와는 더 가깝다: spec을 받는 블록(`achievability`)이 변형마다 다시 계산되지 않는다. 대안(계획 문언 방식)도 §5.3에 적었다 | N3.10 첫 행 |
| PD-2 | 승인 기록 로더를 OT TR-1에서 TR-3으로 옮긴다(§11.2). TR-1에서는 부르는 곳이 없어 '만들면 배선'을 못 지킨다. OT §14.1(사용자 승인 T-18)의 배정을 바꾼다 | N-22, OT §14.1 |
| PD-3 | G-S1 (e)로 같은 topology 변형의 S1v 입력이 같아져 DS-2의 대상이 사라진다. DS-2를 '대상 없음'으로 닫을지 사용자 확인(§10.4) | N3.1-3, F-3, N10.1 DS-2 |
| PD-4 | XS-10 범위 표기: 계산 규칙은 `ss_constraint_rows`·`iv_matching_l` 두 곳이지만 입력 전달 때문에 search 파일 다섯이 더 바뀐다(§12.2) | N9 '한 곳과 한 곳' |

### 16.3 원래 취지와 다름(따로 보고)

| ID | 내용 |
|---|---|
| OD-1 | **시간 예산 유도 실행의 다변형 결정성**(DS-U9 조사, §7.2): 계획 순서·구성과 무관하게 '계획 안 = 단독' 비트 동일을 주는 규칙은 없다. 원인은 다변형이 아니라 비트 동일 전제(E_B 선언, 40 §2.4.13 (가))다. 유도 실행은 S-6대로 조건 2·NFR-S5에서 빼고 표기한다. 변형 사이 결과가 계획 구성에 따라 달라질 수 있다는 점(유도 E_B가 앞 변형의 적중에 따라 달라짐)을 보고한다 |
| OD-2 | **DS-1 (가)와 DS-U7의 충돌**(§10.1): (가)는 같은 실행 안에서 같은 평가 키를 변형마다 다시 계산한다(원래 취지와 다름, XS-8 허용 범위). 그런데 DS-U7(조건 3 약화 안 함)이 이미 결정됐으므로 (가)를 고르려면 DS-U7을 다시 결정해야 한다 |
| OD-3 | **국면 2 탐색 게이트**(§11.2): TR-3~TR-5b 사이에 국면 2 변형이 단계 A까지만 돌고 멈춘다. 승인된 회로를 사이징하지 못하는 기간이 생긴다(fail-closed 때문). OT 원래 흐름에는 없던 정지라 보고한다 |

### 16.4 열린 결정(사용자)

| ID | 질문 | 막는 것 | 기본안 |
|---|---|---|---|
| DS-1 | 평가 캐시 처리 (가)/(나)/(다)(§10) | OS-5 compare 행 | 없음(M2 뒤) |
| DS-2 | S1v (가)/(나), 또는 '대상 없음'으로 닫기(PD-3) | OS-5 완료 조건 4 해석 | 없음(M2 뒤) |
| W-1 | **제품 진입점 배선**: 엔진에 사슬 진입점이 없다(E-S13, U16 미병합). OS-2의 `run_plan`을 (i) 그대로 사슬 진입점으로 병합하고 하네스·test의 수작업 사슬을 대체하며, U16 `run_gmid_design_pipeline`은 `run_plan`을 부르도록 계약에 적는다, 또는 (ii) U16과 함께 병합한다. (i)은 병합 즉시 제품 CLI에서 쓰이지 않는다 -- '만들면 배선' 원칙상 승인이 필요하다 | OS-2 착수 | (i)(근거: 하네스 사슬이 지금 실제로 쓰이는 유일한 사슬이고, 대체하면 옛 수작업 사슬이 사라진다) -- **사용자 승인 필요** |
| F-1 | OS-2 matching 검증 fixture spec의 값(`offset_in_max_v`, k)과 회로. 차동 출력 회로여야 L4 없이 돈다(library 차동 출력 회로는 하나, OT E-13). 값은 사용자 값이다(T-9와 같은 절차: 오케스트레이터 초안 → 사용자 승인) | OS-2 완료 조건(matching fixture 실행) | 없음 |
| DS-U8 | trim 시험 회로 `offset_in_max_v` 값(§15.3) | TR-1 뒤 시험 회로 반영 | 사용자 값 |
| DS-U5 | library spec 요구 형식 이전(회로별) | -- | 사용자 몫 |
| DS-U9 | 시간 유도 예산 다변형 규칙 | -- | 조사 결과 후보 없음(§7.2). 열림 유지 |

---

## 17. 원문 근거

보관 위치는 `skills/analog-gmid-design/assets/technique/sources/<폴더>/source.pdf`(목록 `README.md`). 쪽은 PDF 쪽이다. 원문 수치는 인용하지 않는다. trim 규칙 자체의 원문은 OT §19가 정본이다.

| R | 원문 | 웹 | 로컬 PDF | 쪽·위치 | 쓰는 곳 |
|---|---|---|---|---|---|
| R1 | Y. Zhou, A. Kay, 'Offset Correction Methods: Laser Trim, e-Trim, and Chopper', TI SBOT037A, 2017 | [ti.com/lit/SBOT037](https://www.ti.com/lit/SBOT037) | `assets/technique/sources/offset_trim__zhou_2017/source.pdf` | p.1 e-Trim, p.2 Fig.3·Table 1 | §8 compare 보고 한계 문구(trim은 1/f·drift를 보정하지 않음), 공통 판정에 1/f를 두는 근거(계획 N3.4) |
| R2 | A. Kay, 'Op Amp Offset Voltage and Bias Current Limitations', TI SBOA590, 2024 | [ti.com/lit/pdf/sboa590](https://www.ti.com/lit/pdf/sboa590) | `assets/technique/sources/offset_trim__kay_2024/source.pdf` | §1.2 PDF p.7 Figure 1-8 문단 | §8 compare 보고 drift 한계 문구 |
| R3 | H. M. von Staudt, 'Trim DAC Design with Minimum DNL for Self-Trim with Self-Test Schemes', IEEE IMS3TW 2011 | [doi:10.1109/IMS3TW.2011.34](https://doi.org/10.1109/IMS3TW.2011.34) | `assets/technique/sources/offset_trim__staudt_2011/source.pdf` | p.1-2 §II.A | §4.3 k를 trim 보정 구간 배수로 함께 쓰는 근거 |

matching 합성 판정식 k·σ_in + |V_sys| ≤ `offset_in_max_v`는 사용자 결정 S-1의 식이고 σ_in·V_sys는 엔진 해석(`offset_analysis`·`offset_systematic`)의 값이다. 관례 배수나 원문 수치는 쓰지 않는다.
