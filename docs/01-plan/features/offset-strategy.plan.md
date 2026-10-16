---
template: plan
version: 0.3
---

# offset-strategy Planning Document

> **Summary**: spec이 offset을 **수단**(`offset_in_sigma_mv <=` 제약이나 `offset_trim` 선언)이 아니라 **요구**로 쓰게 한다. 요구는 `offset_requirement{offset_in_max_v, coverage_multiple, strategy}` 하나다. 엔진은 요구와 방식(`matching`·`trim`·`compare`)에서 판정 제약을 유도하고, **실행 계획**(변형 목록, 변형 = (topology 변형, 제약 집합))을 만들어 한 실행 안에서 차례로 돈다. 변형들은 단계 A·S0·블록 결과 색인을 공유한다. 이 일은 파이프라인 층 모듈을 다시 쓰는 것이고(S-2), 핵심 층(graph·블록·kernel·search)은 유지한다.
>
> **Project**: chip-design-skills (analog-gmid-design skill) · **Author**: Claude Code
> **Status**: 계획 초안 v0.3 (2026-10-16). v0.1 독립 검증(72/100, 차단 B-1~B-6, 비차단 N-1~N-13)을 반영했다. 재검증·사용자 승인 전이다. 근거는 사용자 결정 S-1~S-4(원문 `wt/_drafts/user_decisions.md` '## offset 방식 선택·실행 계획 (2026-10-16 사용자 "권고대로 해")')다.
> **이력**: 경위, 결정 원문, 측정 조건, 버전 이력은 [offset-strategy.history.md](offset-strategy.history.md)에 있다.
> **상위 계획**: [gain-budget-gmid-sizing.plan.md](gain-budget-gmid-sizing.plan.md)(원칙 N1.4 NFR, N2 결정, N6.3 병합 전 확인). **관련 계획**: [offset-trim.plan.md](offset-trim.plan.md)(trim 방식의 규칙 정본). 충돌하면 상위 계획이 이기고, offset-trim과의 충돌은 N5(원래 취지와 다름)와 N9에 올린다.

---

## N0. 문서 안내

* **담는 것**: 목적·범위, 확정 결정, 요구, 엔진 반영 구조와 규칙, 원래 취지와 다른 항목, 선행 실측(착수 조건), 순서·card 초안, 완료 조건, 위험, 원문 근거, 열린 결정.
* **담지 않는 것**: 경위, 결정 원문 전문, 측정 조건의 세부, 정정 이력. 이것은 history에 둔다.
* **값 원칙**: 이 문서에는 수치 상수를 두지 않는다.
  * `offset_in_max_v`·`coverage_multiple`(k)·방식 선택, 1/f·면적 판정 값, trim 잔여 V_res·온도는 사용자 spec 값이다.
  * 예산은 선언(E_B)이나 정의(E_total, 상위 design 40 §2.4.9)에서 온다.
  * 나머지는 엔진 해석값·LUT·PDK 선언에서 유도한다. 원문 수치는 인용하지 않는다.
* **이름 원칙**: 규칙에 회로·소자·넷 이름을 쓰지 않는다. 회로 이름은 사실 표(N3.0)와 측정 대상(N6 M2)에만 나온다.
* **인용 규칙**: 코드는 `파일:줄`이고 기준은 base `067614c`(worktree `wt/ostrat-plan`)다. 경로에서 `skills/analog-gmid-design/`은 뺐고 `E/` = `gmid_engine/`이다. design 인용은 `40 §x`(`gain-budget-gmid-sizing.40-engine.design.md`), `OT §x`(`offset-trim.design.md` v0.2, 사용자 승인 T-18)다.

### N0.1 용어

| 용어 | 정의 |
|---|---|
| 요구(offset_requirement) | spec의 offset 요구 하나. 입력 환산 offset 한계 `offset_in_max_v`, 분포 배수 k(`coverage_multiple`), 방식 `strategy`(N3.2) |
| 방식(strategy) | `matching`(입력쌍 면적으로 랜덤 offset을 맞춘다), `trim`(offset-trim의 전류 주입 trim), `compare`(두 방식을 모두 돌려 나란히 낸다, N3.8) |
| 변형(variant) | 실행 계획의 한 항목 = (topology 변형, 제약 집합). topology 변형은 원본 topology 또는 승인된 파생 topology(OT §7)이고, 제약 집합은 spec 판정 제약 + 요구에서 유도한 제약이다 |
| 실행 계획(run plan) | 한 실행에서 돌 변형의 순서 있는 tuple과 각 변형의 예산·국면 표지. 결정적 순수 함수가 spec·topology·승인 기록에서 만든다(N3.5) |
| 국면(phase) | trim이 들어간 방식의 단계. 국면 1 = 원본 topology로 후보·추천(OT §9), 국면 2 = 승인된 파생 topology 사이징(OT §10). 국면 사이에 사용자 승인 게이트가 있다(T-2) |
| 공통 판정 | 모든 변형에 똑같이 거는 판정: 1/f(`noise_fc_in_hz` 또는 `noise_out_int_vrms`)와 총면적 `area_search_m2`(S-1) |
| 핵심 층 | graph·계산 블록·kernel·search(S-2). 이 기능은 이 층을 다시 쓰지 않는다. 예외는 N5 승인 항목뿐이다 |
| 파이프라인 층 | `E/pipeline/`(단계 A·B 진입, 결과 기록). S-2의 재작성 범위 |
| 실행(run) | 사용자 호출 한 번. 블록 결과 색인·`RunCounters`의 수명 단위(40 §2.4.5). 이 기능에서는 실행 계획 하나를 끝까지 도는 것이다 |

---

## N1. 목적·범위·요구

### N1.1 목적

지금 spec은 offset을 수단으로 적는다. 랜덤 offset을 면적으로 맞추려면 `offset_in_sigma_mv <=`를 쓰고(`assets/library/current_reuse_telescopic_ota.sizing_spec.json:226`), trim을 쓰려면 승인된 design에서 `offset_trim` 섹션을 쓴다(OT §5.1). 그래서 방식을 바꾸려면 spec의 판정 제약 자체를 바꿔야 하고, 두 방식을 같은 조건으로 비교할 수 없다.

이 기능의 목적은 다음 셋이다.
1. 사용자는 요구(한계·배수·방식)만 쓰고, 방식별 판정 제약은 엔진이 요구에서 유도한다.
2. 방식에 따라 필요한 변형들을 실행 계획 하나로 묶어 한 실행 안에서 돌고, 그 사이에 계산을 공유한다. 사용자 취지 원문은 다음과 같다(사용자 2026-10-15, 원문 `wt/_drafts/user_decisions.md` '실행 사이 재사용 제거').
   > "계산 재사용은 처음 topology를 실행할 때는 항상 계산하고 그 계산된 값이 나머지 최적화를 진행할 때 재사용되게 한다는 것이 원래 취지였어"
3. `compare`에서는 두 방식의 결과를 같은 공통 판정 아래 나란히 놓는다. 권고는 하지 않는다(S-3).

### N1.2 범위

| 포함 | 제외 |
|---|---|
| spec `offset_requirement` 스키마와 로더 규칙(N3.2) | 기존 library spec을 요구 형식으로 옮기는 일. 사용자 몫이다(S-1, DS-U5) |
| 방식별 판정 제약 유도 규칙(N3.3), 공통 판정(N3.4) | trim 후보·추천·DAC 규칙 자체. offset-trim 계획·design이 정본이다 |
| 실행 계획(변형 목록)과 실행기, 단계 A·S0·블록 결과 색인 공유(N3.5, N3.6) | 엔진 전체 재작성(S-2). 핵심 층 변경은 N5 승인 항목만 |
| 변형별 예산(N3.7) | 실행 사이 재사용. 이전 실행 결과를 엔진 입력으로 받지 않는다(S-3, 상위 U-89) |
| `compare` 두 국면과 읽기 전용 비교 도구(N3.8) | 엔진이 방식을 골라 주는 권고·자동 선택(S-3) |
| 옛 경로 삭제: OT §4의 `trim_approval_path` 인자 분기, OT §5.2의 D-4 공존 거부(N3.9) | chopper·auto-zero 같은 동적 offset 제거(offset-trim N1.2 제외 그대로) |
| 요구가 없는 spec의 무동작 증거(완료 조건 1) | held-out 회로 확장(상위 U-75 뒤) |

### N1.3 기능 요구

| ID | 요구 |
|---|---|
| FR-S1 | **요구 스키마**(S-1): spec에 선택 섹션 `offset_requirement`를 둔다. 키는 `offset_in_max_v`, `coverage_multiple`, `strategy`이고 값·출처는 사용자 몫이다(N3.2) |
| FR-S2 | **방식별 제약 유도**(S-1): 엔진이 요구에서 변형별 판정 제약을 만든다. 출처는 요구 선언을 참조하고(사본 금지), 유도한 제약은 결과에 출처와 함께 적는다(N3.3) |
| FR-S3 | **공통 판정**(S-1): 1/f 판정과 총면적 판정은 spec 선언 하나를 모든 변형에 똑같이 건다(N3.4) |
| FR-S4 | **실행 계획**(S-2): 결정적 순수 함수가 (spec, 원본 topology, 승인 기록)에서 변형 tuple을 만든다. 같은 입력이면 같은 계획이다(N3.5) |
| FR-S5 | **실행기**(S-2): 실행 계획을 한 실행 안에서 차례로 돈다. 단계 A·S0·블록 결과 색인·`RunCounters`를 변형 사이에 공유한다(N3.6) |
| FR-S6 | **변형별 예산**: 변형마다 E_total을 둔다(기본안, N3.7) |
| FR-S7 | **결과 기록**: 결과 JSON에 실행 계획(변형 목록·국면·예산), 변형별 결과, 유도 제약과 출처를 싣는다. `compare`에도 권고 문장은 없다 |
| FR-S8 | **비교 도구**(S-3): 결과 JSON 두 개를 읽어 나란히 놓는 읽기 전용 도구. 엔진을 import하지 않고, 엔진 입력 경로가 없다(N3.8) |
| FR-S9 | **옛 경로 삭제**(S-2): OT §4의 `trim_approval_path` 진입 인자 분기와 OT §5.2의 공존 거부 규칙을 이 기능의 규칙으로 바꾸고, 바뀐 규칙만 남긴다(N3.9) |
| FR-S10 | **무동작**: `offset_requirement`가 없는 spec은 지금과 같은 흐름이다(실행 계획 = 원본 topology와 spec 제약의 변형 하나). 결과는 완료 조건 1의 범위에서 base와 비트 동일하다 |

### N1.4 비기능 요구

상위 계획 N1.4 NFR-1~NFR-6과 N2.2 작업 원칙을 그대로 적용한다. 이 기능에서는 특히 다음을 강제한다.

| ID | 요구 |
|---|---|
| NFR-S1 | **재사용**: 한 실행 안의 모든 변형이 단계 A 결과(같은 topology 변형끼리), S0 수준 블록, 블록 결과 색인(40 §2.4.5)을 공유한다. **같은 입력의 재계산은 실행 전체에서 0**이다(40 §2.4.9 판정 1을 변형 경계를 넘어 적용). 실행 사이 재사용은 없다(상위 U-89, 원래 취지 문장) |
| NFR-S2 | **graph 단일 정본**: 요구 값은 spec 선언 한 곳에만 있다. 유도 제약은 그 선언을 참조하고(`value_from_spec`), 숫자 사본을 만들지 않는다. 실행 계획은 출력·실행 입력이고 graph 필드가 아니다. 새 graph 필드는 writer가 하나다(상위 DEC-83) |
| NFR-S3 | **topology 무관**: 유도 규칙·계획 규칙은 구조와 선언만 읽는다. 회로·소자·넷 이름 리터럴은 금지다. 9회로에서 요구가 없으면 무동작임을 측정해 증거로 낸다 |
| NFR-S4 | **fail-closed**: 요구와 수단 제약이 함께 있거나, 방식에 필요한 선언이 없거나, 유도 제약을 잴 수 없으면(예: 계통 offset 기준 미선언) 탐색 전에 사유 코드로 멈춘다. 조용한 대체·생략은 금지다 |
| NFR-S5 | **결정성**: 같은 입력이면 같은 실행 계획·같은 변형 순서다. 계획 안에서 돈 변형의 결과는 그 변형만 따로 돈 결과와 비트 동일하다. 다를 수 있는 것은 계수·시간 칸(40 §2.4.13 T 부류)뿐이다 |
| NFR-S6 | **상수 발명 금지**: 배수·한계·예산·판정 문턱은 선언이나 정의에서 온다. 비교 도구에 '어느 쪽이 낫다'를 가르는 가중치나 문턱을 두지 않는다 |
| NFR-S7 | **만들면 배선**: 계획 함수·실행기·유도 함수·비교 도구는 진입점의 실제 경로에서 쓰인다. 옛 경로는 같은 변경에서 지운다. 배선이 불가능하면 사용자 승인을 받는다 |
| NFR-S8 | **작성자≠검증자**: design은 독립 검증 agent가 검증한다. test·기대값·판정 기준은 구현자가 소유하지 않는다 |

---

## N2. 확정 결정

| ID | 결정 | 출처 |
|---|---|---|
| S-1 | spec은 수단이 아니라 요구로 쓴다: `offset_requirement{offset_in_max_v, coverage_multiple k, strategy: matching\|trim\|compare}`. 방식별 판정 제약은 엔진이 요구에서 유도한다. matching: k·σ_in + \|V_sys\| ≤ `offset_in_max_v`. trim: `trim_range`·`trim_residual`, V_res ≤ `offset_in_max_v`는 로더 검사. 1/f 판정(`noise_fc_in_hz` 또는 `noise_out_int_vrms`)과 총면적 `area_search_m2` 하나를 두 방식 공통으로 둔다. D-4 공존 거부 대체·N을 {N, N+1}로 여는 것·compare 추가는 '원래 취지와 다름'으로 보고됐고 이 계획·design에서 다시 승인받는다 | 사용자 2026-10-16 "권고대로 해"(원문 `wt/_drafts/user_decisions.md` '## offset 방식 선택·실행 계획') |
| S-2 | 아키텍처 = 파이프라인 층 모듈 재작성. 실행 계획 = 변형 목록 (topology 변형, 제약 집합). 단계 A·S0·블록 결과 색인 공유. 옛 `trim_approval_path` 인자 분기 삭제. 핵심(graph·블록·kernel·search)은 유지하고 엔진 전체는 재작성하지 않는다 | 같음 |
| S-3 | compare는 두 국면이다(승인 게이트 유지). 국면 2의 최종 비교는 오케스트레이터 기본안: 엔진은 이전 실행 결과를 입력으로 받지 않는다. 두 결과 JSON을 읽는 읽기 전용 비교 도구(보고만)로 나란히 놓는다. 계산 재사용·엔진 입력 경로는 없다. 사용자가 달리 원하면 바꾼다 | 같음 |
| S-4 | 순서 = NFR-4 card 2 병합 → XRUN-F1 A → B → C → 실행 계획 구현 → trim TR-1. card A 진행 중에 계획 문서와 실측(평가 캐시 키의 제약 의존, matching·trim 1단계 θ 겹침 1회로)을 한다. OT §4(진입 인자 단계 선택) 개정은 실행 계획 design과 함께 재승인한다 | 같음 |

**이어받는 결정**(바꾸지 않는다):

| ID | 내용 | 이 계획에서 쓰는 곳 |
|---|---|---|
| 실행 사이 재사용 제거 | 실행마다 S0를 계산하고 그 실행 안에서만 재사용한다. 원문은 N1.1 인용 | NFR-S1, N3.6, N3.8 |
| U-89 | S3 기록을 실행 사이에 읽지 않는다. S3는 출력이다 | N3.8 비교 도구가 엔진 밖인 이유 |
| X-12 | 블록 결과 색인 수명 = 실행 하나, 단계 A부터 | N3.6 |
| X-17 | E_total = E_B + N_T + R(R = 2 × `len(sctx.domain.variables)`). 선언 40은 그대로 동작하고 판정·test 예산은 바꾸지 않는다 | N3.7 변형별 예산의 근거 |
| T-2, T-7, T-8 | 파생 topology는 사용자 승인 뒤에만 사이징한다. I_u = θ, θ 하나 = 커널 평가 1회, card C 예산 규칙 변경 없음 | N3.5 국면, N3.7 |
| T-15 | `run_trim_candidates` 제품 경로 배선 때문에 TR-2 병합은 U16 뒤다 | N7 순서 |
| T-19~T-23 | 단일 출력 회로의 출력 기준 DC는 '출력 기준 DC' 기능(XRUN-F1 뒤·TR-6 전)이 정한다 | N3.3 matching 유도의 V_sys 전제 |

---

## N3. 엔진 반영 구조

### N3.0 현황 사실(읽기 확인, base `067614c`)

| ID | 사실 | 근거 |
|---|---|---|
| F-1 | **평가 캐시 키에 제약 집합이 들어가지 않는다.** 평가 키 `EvalKey` = (`context_fp`, `schema_fp`, `cells`, `w_fixed_fp`, θ 값 hex)다. `context_fp` = (`_CONTEXT_WRITERS`의 블록 입력 버전, LUT 손잡이, `DcInputs`) 지문이고, `_CONTEXT_WRITERS` = S1 블록 ∪ 커널 계획 블록(`PLAN_WRITERS`)이다. 제약을 담는 S0 블록 `constraint_classes`와 S1v 블록 `build_s1v`는 여기에 없다. `DcInputs` 칸(레일·입력 DC·노드 목표·원소 값·선형 영역·결정 대기·engine 원소)에도 제약이 없다 | `E/search/eval_key.py:13-22`, `E/search/search_context.py:45-46, :188, :211`, `E/sizing/kernel_context.py:47-48`, `E/sizing/s2_values.py:187-200` |
| F-2 | **평가 결과는 제약 집합에 의존한다.** 커널은 평가 안에서 제약 행을 만든다(`rows = seal_rows + _spec_rows + ss_rows + ls_rows`). `_spec_rows`는 `sctx.judged_constraints`(목적 축 제약)를 읽고, `ss_constraint_rows`는 `sctx.ss_constraints`를 읽는다. 어떤 metric을 계산할지도 제약이 정한다: `ss_evaluate`가 `sctx.ss_constraints`에서 요청 목록을 만들고, 그 목록이 `metrics_ss`·`metrics_aux` 블록의 extras(입력 버전)에 들어간다. 이 행을 담은 `EvalResult`가 그대로 캐시에 들어간다 | `E/search/kernel.py:49-56, :130-133, :146-151, :159-161`, `E/metrics/ss_evaluate.py:50-57, :90-93, :98, :103`, `E/metrics/ss_metrics.py:377-379`, `E/metrics/metrics_aux.py:157-159` |
| F-3 | **S1v 블록 입력에 제약 tuple 전체가 들어간다.** 단계 A가 spec 객체를 `build_s1v`에 넘기고(`stage_a.py:225-227`), `build_s1v`가 판정 제약 tuple을 만들어(`s1v_build.py:39`) 블록 `s1v_fields`의 extras로 넘긴다. 안정도 제약의 루프 뷰 끊는 넷도 spec 제약에서 온다(`_declared_loop_cuts`, `stage_a.py:152-160`). 그래서 제약 집합이 다르면 같은 topology라도 S1v 블록의 입력 버전이 다르다 | `E/pipeline/stage_a.py:152-160, :225-227`, `E/graph/s1v_build.py:39-42`, `E/graph/s1v_fields.py:249-251` |
| F-3a | **S1v 값도 제약 집합에 따라 달라질 수 있다.** 전달 뷰 씨앗은 판정 제약의 `view` 선언(port·loop·transfer·ratio)에서 만들고, 선언이 하나도 없을 때만 기본 뷰를 쓴다. offset metric 셋은 transfer 뷰 metric이다. 그래서 view를 선언한 offset 제약이 빠지거나 더해지면 뷰 집합이 바뀔 수 있다 | `E/graph/views.py:51-63, :77-78`, `E/metrics/registry.py:56-58` |
| F-4 | **spec을 읽는 S0 경로**: 단계 B의 면적 예산과 달성 가능성 블록(`achievability(graph, spec, …)`), 탐색 컨텍스트의 θ 상자(면적 예산), 제약 분류, 출발 구간(`start_intervals(base, spec, …)`), `ss_constraints`(spec 제약을 위치로 고름), 잡음·mismatch LUT 데이터 필수 검사 | `E/pipeline/stage_b.py:153, :168`, `E/search/search_context.py:110-113, :156-168, :171-196`(출발 구간 :195) |
| F-5 | 실행 수명 상태(평가 캐시 `cache`, `computed_keys`, 계수, `eval_budget`, `deadline`)는 `SearchContext` 객체 하나에 있다. S3 기록기는 `S3Archive(root, context_fp, code_fp)`다. **XRUN-F1 card B·U17 ② 뒤에는** `sctx.cache`·`computed_keys`가 S3 메모리 색인(`search/s3_index.py`의 `S3Index`) 하나로 바뀌고, 블록 결과 색인(`find`·`register`)은 그 색인의 한 부분이다(평가 키 조회 `get`·`failure`와 같은 객체) | `E/search/search_context.py:53-69, :212`, 40 §2.4.5(평가 키·블록 결과 색인 API) |
| F-6 | `find_front`는 호출마다 벽시계 정지 시각을 정하고, 판정 metric의 검증 출처를 `sctx.ss_constraints`·`sctx.judged_constraints`에서 모은다 | `E/search/find_front.py:75-78, :94` |
| F-7 | 진입점 서명은 `run_stage_a(topology_path, spec_path, lut, *, output_dir, supplies_v=None, structure_path=None)`, `run_stage_b(stage_a, memo, pdk_decl, *, output_dir, settings, diagnostic=False)`다. 엔진 코드에 'trim'은 없다. `trim_approval_path`는 OT §4 design에만 있다 | `E/pipeline/stage_a.py:195`, `E/pipeline/stage_b.py:134`, grep 2026-10-16 |
| F-8 | XRUN-F1 card A·B·C는 base에 병합되지 않았다. 블록 결과 색인(`search/s3_index.py`)·`search_ceiling.py`·`search_stop.py`는 아직 없다. 색인 수명·상한·E_total 규칙은 design(40 §2.4.5, §2.4.9, §2.4.14)이다 | `ls E/search/` 2026-10-16 |
| F-9 | library에서 `offset_in_sigma_mv` 판정 제약을 가진 spec은 하나다. `offset_excess`는 6개 spec에 있다 | `assets/library/current_reuse_telescopic_ota.sizing_spec.json:226`, `folded_cascode…:49`, `ngcc_3stage_ff…:111`, `nmcnr_amplifier…:141`, `sf_pushpull_output_opamp…:131`, `two_stage_ota…:81`, `two_stage_ota_sf…:82` |
| F-10 | 1/f·면적 metric은 레지스트리에 있다: `noise_fc_in_hz`, `noise_out_int_vrms`, `area_search_m2`. offset metric은 `offset_in_sigma_mv`·`offset_excess`(`OffsetAnalysis`), `offset_sys_mv`(`OffsetSystematic`)다 | `E/metrics/registry.py:49, :52, :54, :56-58` |
| F-11 | 승인된 trim design은 2단계 실행에서 S0를 두 벌(원본·파생) 계산하므로 색인 상한을 Σ 분할 수 × (E_total + 2)로 둔다 | OT §10.1 |
| F-12 | **제약을 읽는 핵심 층 지점**: `SearchContext.ss_constraints`는 `constraint_classes`의 위치 index로 `self.spec.judged_constraints`를 고른다. 출발값 규칙은 `spec.judged_constraints`에서 (metric, op, 값) 목록을 만들고, `iv_matching_l`은 그 목록에서 이름 `offset_in_sigma_mv`(L 하한)·`offset_excess`(부하 가드)를 찾는다. `judged_constraints`는 `SizingSpecDoc.constraints`에서 뽑는 속성이고, spec 객체는 `spec_fp`·`section_fps` 지문을 칸으로 들고 있다 | `E/search/search_context.py:110-113`, `E/search/iv_context.py:89`, `E/search/iv_matching_l.py:40-41, :107-108`, `E/search/start_intervals.py:295, :332`, `E/authoring/spec_model.py:280-281, :287-290` |
| F-13 | **base에서 나오는 측정 칸**: S3 evals 한 줄 = `seq`, `schema_fp`, `cells`, `w_fixed_fp`, `theta_hex`, `theta`, `status`, `ok`, `origin`, (`fail`), (`objectives`), `constraints`, `unmeasured`, (`power_resolution_w`), (`snapshot_fp`)이다. **평가별 시간 칸은 없다**. S3 폴더 이름이 `context_fp`다. `find_front` 결과 `perf`는 실행 합계(계수, `unique_keys`, `eval_time_median_s`, `wall_s`, `block_calls`·`block_reuses`·`block_computes`·`block_recomputes_same_input` 합계)이고 블록별 수는 없다 | `E/search/kernel.py:68-88`, `E/search/archive.py:42-43`, `E/search/find_front.py:127-133` |

### N3.1 M1 결과와 그 뜻

M1(평가 캐시 키에 제약 집합이 들어가는가)은 **들어가지 않는다**(F-1). 반면 평가 결과는 제약 집합에 의존한다(F-2). 이것이 이 계획에 주는 뜻은 다음과 같다.

1. **같은 topology 변형끼리 평가 캐시를 그대로 공유하면 틀린다.** matching 변형과 trim 국면 1 변형은 원본 topology가 같아 `context_fp`가 같다. 한 `SearchContext`의 캐시를 함께 쓰면, 한 변형의 제약 행을 담은 `EvalResult`가 다른 변형에 적중으로 돌아간다. 처리 선택지는 셋이다(DS-1, 아래 표).
2. **블록 결과 색인은 공유해도 맞다.** 색인 키는 (블록, 분할, 입력 버전)이고 블록은 투영만의 순수 함수다(40 §2.4.5 '결정성'). 그래서 변형이 달라도 입력이 같은 블록은 적중하고 결과는 비트 동일하다.
3. **다만 공유 범위가 제약 쪽에서 끊긴다.** metric 블록은 요청 목록이 extras에 들어가므로(F-2), 두 변형의 요청 목록이 다르면 같은 θ라도 다른 입력이다. S1v 블록도 제약 tuple 전체가 extras라서(F-3) 같은 topology여도 변형마다 한 번씩 계산된다. 이것은 입력 지문이 달라서 생기는 계산이라 40 §2.4.9 판정 1('같은 입력 재계산 0')을 형식상 깨지는 않는다. **그 결과 값이 같은지는 정해져 있지 않다**: 뷰는 제약의 view 선언에서 만들어지므로(F-3a) 변형 제약 집합에 view를 선언한 제약이 다르면 S1v 값도 다르다(이때는 재계산이 맞다). view 선언이 같으면 값이 같은데도 다시 계산하는 것이어서 원래 취지('그 계산된 값이 나머지 최적화를 진행할 때 재사용')와 거리가 있다. 어느 쪽인지는 유도 제약의 view 출처(G-S1)와 변형별 view 선언 집합으로 정해진다.
4. **'평가 = 크기·metric(제약 무관) + 판정(변형별)' 분리는 범위를 kernel까지 넓힌다.** 분리하려면 (i) 커널이 계획 안 모든 변형의 metric 요청 합집합을 한 번에 계산하고(`kernel.py:130`의 요청 출처 변경), (ii) 캐시 값에서 제약 행을 빼서 변형별 판정 단계로 옮기고(`kernel.py:146-151, :159-161`), (iii) S1v 투영을 뷰 선언·루프 끊는 넷으로 좁혀야 한다(`s1v_fields.py:249-251`, graph 층). 셋 다 S-2 '핵심 유지' 밖이다. 그래서 **결정 항목 DS-1**로 둔다(N5 XS-5, N10).

**DS-1 선택지와 완료 조건 3**(완료 조건 3 = 실행 계획 전체에서 같은 입력의 블록 재계산 0, 같은 평가 키 재계산 0. 이 조건은 약화하지 않는다). 이 기능은 XRUN-F1 card B 뒤에 구현되므로 선택지는 **card B 뒤 구조**로 쓴다: 평가 캐시와 블록 결과 색인은 S3 메모리 색인 `S3Index` 한 객체의 두 부분이다(평가 키 조회 `get`·`failure`, 블록 결과 `find`·`register`, F-5, 40 §2.4.5).

| 선택지 | 내용 | 바뀌는 층 | 블록 재계산 0 | 같은 평가 키 재계산 0 | 원래 취지와의 관계 |
|---|---|---|---|---|---|
| (가) 평가 키 부분만 변형별 | 변형마다 평가 키 부분(`get`·`failure`)을 따로 두고, 블록 결과 부분(`find`·`register`)만 실행 계획 전체에서 공유한다. 키는 지금 그대로다. `S3Index`가 한 객체이므로 두 부분의 수명을 가르는 변경이 `search/s3_index.py`에 필요하다(card B 전 구조라면 변형별 `SearchContext`만으로 되지만, 구현 시점은 card B 뒤다) | search(`S3Index` 수명 분리) + pipeline | 지킨다(블록 결과 부분 공유) | **모순**. 같은 topology 변형은 `context_fp`가 같으므로(F-1) 두 변형이 같은 θ를 밟으면 **같은 평가 키**가 실행 안에서 두 번 계산된다 | 같은 실행 안에서 변형 사이의 커널 평가 재계산을 받아들인다(XS-8). card B 뒤에는 핵심 층(search)도 바뀐다(XS-5) |
| (나) 평가 분리 | 커널이 계획 안 모든 변형의 metric 요청 합집합을 한 번 계산하고, 평가 키 부분의 값은 제약 무관이다. 판정 행은 변형별 단계가 만든다. `S3Index` 하나를 실행 계획 전체에서 공유한다. S1v 투영을 좁히는 것(DS-2 (나))과 같이 간다 | kernel·`ss_evaluate` 호출(search·metrics), graph(S1v) | 지킨다 | 지킨다(같은 θ는 실행 안에서 한 번 평가) | 재사용 취지는 맞는다. 대신 S-2 '핵심 유지'와 다르다(XS-5) |
| (다) 키 분리 | 평가 키(또는 `context_fp`)에 변형 제약 집합 지문을 넣는다. `S3Index` 하나를 실행 계획 전체에서 공유한다 | search(`eval_key`·`context_fp`) | 지킨다 | 형식상 지킨다(변형마다 키가 다르다). 실제로는 같은 θ가 변형마다 커널을 한 번씩 거치고, 크기 결정 블록은 블록 결과 적중, 요청이 다른 metric 블록은 다시 계산된다 | 같은 값의 계산이 변형 사이에서 남는다(XS-8). 핵심 층(search) 변경이다(XS-5) |

* (가)를 고르고 완료 조건 3을 '변형 안 0 + 변형 사이 수는 보고'로 바꾸는 것은 **기준 약화**다. 사용자 승인 없이는 하지 않는다(N10 DS-U7).
* 결정은 M2 숫자(같은 θ를 얼마나 밟는가, N6)와 함께 받는다. 기본안은 두지 않는다(N5 XS-5·XS-8).

### N3.2 요구 스키마 `offset_requirement`(TR-1과 함께 로더 확장)

spec 사람 선언의 선택 섹션이다. 형식은 기존 spec 값 칸(`value` + `source`, 출처 kind는 `user_spec`만)을 따른다. 정확한 스키마·사유 코드 이름은 design(OS-0)이 DEC-68 명명 규칙으로 정한다.

| 키 | 뜻 | 형식 검사 |
|---|---|---|
| `offset_in_max_v` | 입력 환산 offset 한계(V). matching에서는 k·σ_in + \|V_sys\|의 상한, trim에서는 V_res의 상한(N3.3) | 유한 양수 |
| `coverage_multiple` | k. 랜덤 offset 분포 σ_in의 배수. matching 상한과 trim 보정 구간이 같은 k를 쓴다 | 유한 양수 |
| `strategy` | `matching` \| `trim` \| `compare` | 닫힌 어휘 |

**로더 규칙**(fail-closed, NFR-S4):

| 상황 | 처리(기본안) |
|---|---|
| 요구와 수단 제약(`offset_in_sigma_mv`·`offset_sys_mv`·`offset_excess`의 판정 제약)이 같은 spec에 있음 | 거부. 사유 코드는 design이 정한다. 한 spec에 offset 판정의 출처가 둘이면 어느 쪽이 판정인지 모호하다(단일 정본). 이 규칙은 OT §5.2(D-4: `offset_in_sigma_mv`만 거부, 나머지는 보고로 내림)를 대체한다(XS-1). `offset_excess`를 matching에서 구조 가드로 남길지는 DS-U1, 거부 범위는 DS-U2 |
| `strategy`가 `trim`·`compare`인데 `offset_trim` 섹션이 없음 | 거부(trim 선언 값 V_res·온도가 없다) |
| `strategy`가 `matching`인데 `offset_trim` 섹션이 있음 | 거부(쓰이지 않는 선언이 조용히 무동작이 되지 않게) |
| `offset_trim` 섹션은 있는데 `offset_requirement`가 없음 | 거부(사유 후보 `offset_trim_without_requirement`, 이름은 design). 이유: 이 기능 뒤 trim은 방식(`strategy`)의 한 값이고, k와 한계(`offset_in_max_v`)는 요구에만 있다(XS-6). 요구 없이 trim 선언만 있으면 k가 없어 보정 구간 제약을 유도할 수 없다. OT §5.1(요구 없이 `offset_trim` 단독)과 T-27·T-28 시험 회로 spec에 영향이 있다(XS-9) |
| `offset_trim.residual_offset_v`(V_res) > `offset_in_max_v` | 거부(S-1 로더 검사) |
| k의 출처 | 요구의 `coverage_multiple` 하나다. OT §5.1의 `offset_trim.coverage_multiple`은 두 번째 출처가 되므로 없앤다(XS-6, DS-U3) |
| 요구 섹션이 결정 대기 | 요구 없음과 같다(지금 흐름). 대기 표지는 기존 수집 경로로 보고 |

### N3.3 방식별 판정 제약 유도

유도 제약은 변형의 제약 집합에 spec 판정 제약과 함께 들어간다. 값은 요구 선언을 참조하고(`value_from_spec` 계열), 숫자를 복사하지 않는다(NFR-S2).

| 방식·국면 | 유도 제약 | 근거·전제 |
|---|---|---|
| matching | k·σ_in + \|V_sys\| ≤ `offset_in_max_v`. σ_in = `offset_in_sigma_mv`(F-10), V_sys = `offset_sys_mv`(크기). 두 metric은 mV, 한계는 V라서 단위 환산 규칙과 유도 제약의 view 출처가 필요하다(G-S1) | S-1. 이 합성 판정을 새 metric(k를 입력으로 받음)으로 둘지, 두 metric을 읽는 합성 제약 행으로 둘지는 design G-S1이다. V_sys는 선언 출력 기준 DC가 있어야 정의된다(`offset_systematic`의 `reference_undeclared`). 그 기준이 없는 회로는 탐색 전에 멈춘다(fail-closed). 단일 출력 회로의 기준은 '출력 기준 DC' 기능(T-19~T-23)이 정한다(N7 의존) |
| matching의 출발값 | `iv_matching_l` L 하한은 지금 `offset_in_sigma_mv <=`가 있을 때만 켜진다(offset-trim 계획 F-4). 유도 제약이 그 역할을 받도록 출발값 규칙의 입력을 바꾼다. 판정은 바뀌지 않는다(출발값 전용) | design G-S2 |
| trim 국면 1 | 랜덤 offset 판정 제약을 두지 않는다(σ_in은 덮을 분포이고 보고한다). 후보·추천은 OT §9 그대로이고, 입력 k·V_res는 요구·`offset_trim`에서 읽는다 | OT §10.8, S-1 |
| trim 국면 2 | `trim_range`(보정 구간이 [−k·σ_in, +k·σ_in]을 덮음)·`trim_residual`(Δ_max/2 ≤ V_res)·`trim_states_saturation` | OT §10.6. V_res ≤ `offset_in_max_v`는 로더가 이미 확인했다(N3.2) |
| compare | matching 변형과 trim 변형 각각의 제약. 두 방식에 같은 k·같은 공통 판정을 쓴다 | S-1, N3.8 |

### N3.4 공통 판정

* 1/f 판정(`noise_fc_in_hz` 또는 `noise_out_int_vrms`, 사용자가 spec에 선언한 것)과 총면적 `area_search_m2 <=`는 spec 판정 제약 그대로 **모든 변형에 똑같이** 들어간다. 엔진은 값을 만들지 않는다.
* trim 변형의 면적·잡음에는 DAC 소자가 자동으로 들어간다(offset-trim N3.6). 그래서 같은 면적 상한과 같은 1/f 판정이 두 방식의 대가(입력쌍 면적 대 DAC 면적, 작은 입력쌍의 1/f 증가)를 같은 기준으로 드러낸다. offset trim은 1/f와 drift를 보정하지 않는다(N8 R1·R2).
* `compare`에서 1/f 판정이나 면적 상한이 없으면 두 결과를 같은 기준으로 놓을 수 없다. 기본안은 탐색 전 거부다(DS-U4). `matching`·`trim` 단독은 지금처럼 선언된 것만 판정한다.

### N3.5 실행 계획

**함수**: `build_run_plan(spec, topology, approvals) -> RunPlan`(이름은 design). 결정적 순수 함수이고 파일을 쓰지 않는다. `approvals`는 정해진 위치(OT §8.1 `<circuit>.trim.json`, structure.json과 같은 규칙)에서 로더가 읽은 승인 기록이다. 국면은 **승인 기록 유무로** 정한다. 진입 인자로 단계를 고르는 분기는 두지 않는다(S-2, N3.9).

| 요구 `strategy` | 승인 기록 | 변형 목록(순서대로) |
|---|---|---|
| 요구 없음 | -- | (원본 topology, spec 제약). 지금 흐름 그대로(FR-S10) |
| `matching` | -- | (원본, spec 제약 + matching 유도 제약) |
| `trim` | 없음(국면 1) | (원본, spec 제약 + trim 국면 1 규칙). 출력 = 후보표, 추천 구성 {N, N+1}의 파생 topology와 connectivity 표, 승인 초안(OT §9.5 + XS-2) |
| `trim` | 있음(국면 2) | 승인된 파생 topology마다 (파생, spec 제약 + trim 국면 2 유도 제약). N과 N+1을 둘 다 승인했으면 변형 둘이다(XS-2) |
| `compare` | 없음(국면 1) | (원본, matching 변형), (원본, trim 국면 1). 두 변형은 같은 topology라 단계 A·S0 계산을 공유한다(N3.6) |
| `compare` | 있음(국면 2) | 승인된 파생 topology마다 trim 국면 2 변형. matching 결과는 국면 1의 결과 JSON에 있다. 엔진은 그것을 다시 읽지 않고, 다시 계산하지도 않는다(S-3). 최종 비교는 비교 도구(N3.8) |

* 변형의 정체 = (topology 변형 지문 `connectivity_fp`, 제약 집합 지문). 같은 정체가 계획에 두 번 나오면 계획 함수가 거부한다.
* **승인 기록이 낡았거나 맞지 않을 때**: 승인 기록이 있으면 국면 2 규칙을 쓴다. 결속 검사(OT §8.3: 파생 지문·변환 규칙 해시·spec trim 섹션 지문 대조)에 실패하면 OT §8.3대로 `trim_approval_stale` 등으로 **정지**한다(fail-closed). 국면 1로 조용히 돌아가지 않는다. 승인되지 않은 회로를 사이징하거나 사용자 모르게 다른 국면을 도는 일을 막기 위해서다.
* **승인 파일이 있는 상태에서 국면 1을 다시 돌기**: 국면은 승인 기록 유무로만 정하므로, 사용자가 승인 기록 파일을 정해진 위치에서 치우면(이름 바꾸기·옮기기) 국면 1이 돈다. 엔진은 승인 파일을 지우거나 고치지 않는다. 진입 인자로 국면을 강제하는 길은 두지 않는다(S-2 인자 분기 삭제). 이 방법은 DO-9(오케스트레이터 기본안)다.
* 변형 순서는 위 표 순서로 고정한다(결정성, NFR-S5). 순서가 결과 값을 바꾸지 않음은 완료 조건 2가 확인한다.
* trim·compare 변형은 TR card가 그 경로를 만든 뒤에만 실행된다. 그 전에는 계획 함수가 `strategy`를 거부한다(fail-closed, 조용한 생략 금지). 거부 사유 코드는 design이 정한다.

### N3.6 실행기와 공유 범위

**함수**: `run_plan(plan, ...)`(pipeline 층, 이름은 design). 한 실행 = 실행 계획 하나다.

| 대상 | 공유 규칙 | 근거 |
|---|---|---|
| 블록 결과 색인·`RunCounters` | 실행 계획 진입에서 한 번 만들고, 모든 변형의 모든 블록 호출에 같은 객체를 넘기고, 실행이 끝나면 버린다. 40 §2.4.5 '수명'의 실행 경계 문구('`run_stage_a` 진입')를 '실행 계획 진입'으로 고친다. 실행 사이에는 넘기지 않는다 | X-12, 원래 취지 문장, XS-7 |
| 단계 A(S1·S1v·structure 사실·보고) | 같은 topology 변형끼리 공유한다. S1은 topology와 선언만의 함수라 변형 사이에 같은 입력이다. S1v는 제약 tuple이 extras라 변형마다 입력이 다르면 다시 계산된다(F-3). 이 몫을 받아들일지 투영을 좁힐지는 DS-2 | F-3 |
| S0 수준 탐색 블록(`search_domain`·`constraint_classes`·출발 구간 등) | 블록 결과 색인으로 공유한다. 입력이 같으면 적중, 다르면 계산 | F-4 |
| 평가 캐시·`SearchContext`(card B 뒤 `S3Index`의 평가 키 부분) | 지금 키 그대로 하나의 캐시를 공유하는 것은 금지다(같은 topology 변형끼리 `context_fp`가 같아 틀린 결과가 적중한다, N3.1-1). 어떻게 나눌지는 DS-1((가)·(나)·(다), 기본안 없음)이다 | F-1, F-2 |
| 커널 안 블록(봉인·GB5·metric) | 블록 결과 색인으로 공유한다. 같은 θ의 크기 결정 블록은 변형 사이에 적중한다. metric 블록은 요청 목록이 같을 때만 적중한다(N3.1-3) | F-2 |
| S3 기록 | 변형마다 줄에 변형 정체를 싣는다. 같은 topology 변형은 `context_fp`가 같아 줄만으로 구분되지 않기 때문이다(F-5). S3는 출력이고 실행 사이에 읽지 않는다(U-89) | F-5 |

### N3.7 예산

* **제안(확인 요청 XS-12): 변형마다 E_total을 둔다.** 변형 v의 E_total,v = E_B + N_T + R(X-17 식 그대로, R = 2 × 그 변형의 `len(sctx.domain.variables)`). 이유: X-17은 '선언 40은 그대로 동작, 판정·test 예산 변경 없음'을 지키려고 정해졌고, 변형마다 두면 변형 하나의 탐색이 지금 단독 실행과 같은 예산을 받아 NFR-S5(계획 안 결과 = 단독 결과)가 성립한다. 한 E_total을 변형들이 나누는 안은 변형별 탐색과 결과가 계획 구성에 따라 바뀌어 NFR-S5를 깬다.
* **이 제안은 승인된 정의를 바꾼다**: 40 §2.4.9의 E_total은 '실행 하나의 커널 평가 수 상한'이고 그 문서의 유일한 정의다. §2.4.5 색인 상한 식도 '실행 하나' 단위다. 한 실행에 변형이 여럿이면 '실행 하나의 상한'은 Σ_v E_total,v가 되고 E_total은 변형 단위 양이 된다. 그래서 오케스트레이터 기본안으로 두지 않고 XS-7처럼 확인 요청 항목(XS-12)으로 둔다. 확인 전에는 다변형 실행(OS-5)을 시작하지 않는다.
* 시간 예산에서 유도하는 실행(X-17 후반)은 변형마다 같은 규칙으로 유도한다. 벽시계 정지도 변형마다 정한다(F-6). 실행 전체 시간은 변형 시간의 합이다.
* **색인 상한**: Σ_블록 분할 수 × (Σ_v E_total,v + S0 계산 벌 수). S0 계산 벌 수는 계획 안 서로 다른 S0 입력의 수다(OT §10.1의 +2 일반화). card C의 등록 시 fail-closed 검사는 이 식을 쓴다.

### N3.8 compare 두 국면과 읽기 전용 비교 도구

1. **국면 1**(승인 기록 없음): matching 변형과 trim 국면 1 변형을 한 실행에서 돈다. 결과 JSON에 matching front와 trim 후보표·추천·파생 topology를 싣는다.
2. **승인**: 사용자가 파생 topology(N, N+1 중 고른 것)를 승인한다(T-2 게이트 유지).
3. **국면 2**(승인 기록 있음): 승인된 파생 topology의 trim 국면 2 변형을 돈다. matching은 다시 돌지 않는다.
4. **최종 비교**(S-3 기본안): 읽기 전용 도구가 국면 1 결과 JSON(matching)과 국면 2 결과 JSON(trim)을 읽어 같은 칸(공통 판정 값, 전력·면적 front, offset 한계 대비 여유, 유도 제약의 판정, 출처 실행 id·code_fp)을 나란히 낸다.
   * 도구는 엔진 밖(`tools/`)에 두고 엔진을 import하지 않는다. 엔진은 도구 출력을 입력으로 받지 않는다. 두 결과의 계산 재사용도 없다.
   * 도구는 판정·권고 문장을 만들지 않는다. 두 결과의 `code_fp`나 공통 판정 선언이 다르면 그 사실을 표에 적는다(조용히 비교하지 않음).
   * 도구 위치와 이름은 design이 정한다.

### N3.9 옛 경로 삭제와 다른 문서의 개정

| 대상 | 바뀌는 것 | 시점 |
|---|---|---|
| OT §4 흐름 | 진입 인자 `trim_approval_path`로 단계를 고르는 문장, `trim_approval_without_decl` 사유를 지운다. 국면은 실행 계획(N3.5)이 승인 기록 유무로 정한다 | OS-0 design과 함께 재승인(S-4). 코드에는 아직 없으므로(F-7) 코드 삭제는 없다 |
| OT §5.1 | `coverage_multiple`을 요구 섹션으로 옮긴다(XS-6) | 같음 |
| OT §5.2(D-4) | 공존 거부 규칙을 N3.2 로더 규칙으로 대체한다(XS-1) | 같음 |
| OT §9.4·§9.5 | 추천을 N 하나에서 {N, N+1}로 연다(XS-2) | 같음 |
| OT §10.1 색인 상한 | N3.7 일반식으로 대체 | 같음 |
| 40 §2.4.5 수명 | 실행 경계 = 실행 계획 진입(XS-7) | OS-0, XRUN-F1 card B 병합 뒤 |
| offset-trim 계획 TR-1 범위 | spec trim 섹션 로더는 요구 섹션 로더와 함께 정의된다 | OS-0 |

### N3.10 층 분류(파이프라인만으로 되는가)

S-2는 '파이프라인 층 재작성, 핵심(graph·블록·kernel·search) 유지'다. 이 계획의 각 일이 어느 층을 건드리는지 F-1~F-3·F-12로 분류한다. authoring(spec 로더)은 S-2가 핵심으로 꼽지 않은 층이라 확장 대상으로 본다.

| 일 | 필요한 변경 | 분류 | S-2와의 관계 |
|---|---|---|---|
| 변형별 제약 집합 주입 | 변형마다 spec 객체의 `constraints`를 바꾼 사본을 만들어 단계 A·`build_search_context`에 넘긴다. 그러면 `ss_constraints`(`search_context.py:110-113`)·`_s0_blocks`(`:156-196`)·출발값(`iv_context.py:89`)이 변형 제약을 그대로 읽는다. 단, spec 객체는 `spec_fp`·`section_fps`를 칸으로 들고 있으므로(`spec_model.py:280-281`) 사본의 지문을 다시 계산하는 생성 함수가 authoring에 필요하다 | pipeline + authoring 확장. 핵심 층 무변경 | 맞음. 지문을 다시 계산하지 않고 `dataclasses.replace`만 쓰는 것은 금지(옛 지문이 남는 값 사본) |
| 유도 제약을 기존 metric으로 표현할 수 있는 경우(trim 국면 2의 `trim_range`·`trim_residual`, 공통 판정) | 위 주입으로 끝난다. trim metric 자체는 TR card 몫이다 | pipeline(+TR card) | 맞음 |
| G-S1 matching 합성 판정 k·σ_in + \|V_sys\| ≤ `offset_in_max_v` | 지금 레지스트리에 이 양의 metric이 없다(F-10). (i) k를 입력으로 받는 새 metric을 레지스트리에 더하거나(metrics), (ii) 두 metric을 읽는 합성 제약 행을 `ss_constraint_rows`에 더해야 한다(search). 한계를 σ와 V_sys 몫으로 나눠 기존 metric 두 개로 쓰는 것은 나누는 비율을 발명해야 해서 택하지 않는다(NFR-S6) | **핵심 층 확장**(metrics 또는 search) | 다름 → XS-10 |
| G-S2 matching 출발값 | `iv_matching_l`은 이름 `offset_in_sigma_mv`로 L 하한을 켠다(`iv_matching_l.py:40, :107`). 합성 판정만 있으면 L 하한이 꺼진다. 합성 판정에서 σ 목표를 읽게 하려면 `iv_matching_l`(search)을 고친다. 출발값 전용이라 판정은 바뀌지 않는다 | **핵심 층 확장**(search 출발값) | 다름 → XS-10 |
| 실행 계획·실행기·결과 기록 | pipeline 모듈 신설·재작성 | pipeline | 맞음 |
| 블록 결과 색인 수명 경계 | 색인을 만드는 자리를 `run_stage_a` 진입에서 실행 계획 진입으로 옮긴다. 색인 자체(search)는 바꾸지 않는다 | pipeline(+design 문구, XS-7) | 맞음 |
| DS-1 (가)·(나)·(다), DS-2 (나) | N3.1 표. (가)도 card B 뒤에는 `S3Index`의 두 부분 수명을 가르는 search 변경이다 | **핵심 층 변경** | 다름 → XS-5 |

---

## N4. 9회로·요구 적용 판정

판정은 규칙으로 하고, 단계마다 '해당 없음'은 사유 코드로 남긴다.

1. spec에 요구가 없으면 → 무동작(완료 조건 1).
2. 요구와 수단 제약이 함께 있으면 → 로더 거부(N3.2).
3. matching인데 계통 offset 기준이 정의되지 않으면 → 탐색 전 정지(N3.3).
4. trim·compare는 → offset-trim N4 판정을 그대로 따른다(단일 입력 회로 정지 등).

**지금 library**: 9회로 spec에 요구 섹션이 없다. 그래서 이 기능 병합 뒤에도 library 결과는 바뀌지 않는다(완료 조건 1). 요구를 쓰는 검증은 `origin: fixture` spec으로 한다(offset-trim T-24·T-28의 시험 회로 경로와 같은 규칙). library spec을 요구 형식으로 옮길지는 사용자 몫이다(DS-U5).

---

## N5. 원래 취지와 다름(따로 보고, 각각 승인 필요)

사용자 규칙(2026-10-15 '원래 취지와 다른 판단 보고 규칙')에 따라, 승인 전에는 아래 항목을 기본안으로 삼지 않는다. (a)~(d)는 S-1·S-4가 '이 계획·design에서 다시 승인'으로 지정한 것이다.

| ID | 내용 | 원래 결정·취지 | 승인 |
|---|---|---|---|
| XS-1 (a) | **D-4 공존 거부 대체**: 승인된 D-4(`offset_in_sigma_mv`와 trim 선언 공존만 거부, `offset_excess`·`offset_sys_mv`는 보고로 내림, OT §5.2)를 '요구가 있으면 offset 수단 제약 전부 거부 + 방식별 유도'로 바꾼다 | offset-trim 계획 D-4(사용자 T-6 승인) | **필요** |
| XS-2 (b) | **N을 {N, N+1}로 연다**: OT §3.4·§9.4는 front 집계로 추천 N 하나(가능한 최소 N)를 낸다. 이 계획은 국면 1이 N과 N+1 두 구성의 파생 topology를 내고, 사용자가 승인한 것마다 국면 2 변형을 만든다. N+1은 LSB가 작아 잔여 조건에 여유가 생기는 대신 셀 수·면적이 는다. 이 교환을 사용자가 보게 하려는 것이다. N+1의 m 규칙은 DS-U6 | OT §9.4(사용자 T-18 승인) | **필요** |
| XS-3 (c) | **compare 추가**: 방식 하나를 고르는 대신 두 방식을 같은 공통 판정으로 돌려 나란히 낸다. 엔진은 권고하지 않는다 | offset-trim 계획은 trim 선언 회로만 다룸 | **필요** |
| XS-4 (d) | **OT §4 개정**: 진입 인자(`trim_approval_path`)로 단계를 고르던 승인된 흐름을 실행 계획의 국면 규칙(승인 기록 유무)으로 바꾼다 | OT §4(사용자 T-18 승인) | **필요**(S-4: 실행 계획 design과 함께 재승인) |
| XS-5 | **DS-1 (가)·(나)·(다), DS-2 (나)는 핵심 층 변경**: card B 뒤 `S3Index`의 평가 키 부분과 블록 결과 부분의 수명을 가르면 search가(가), 평가를 크기·metric과 판정으로 나누면 kernel·`ss_evaluate` 호출이(나), 평가 키에 제약 지문을 넣으면 search의 `eval_key`·`context_fp`가(다), S1v 투영을 좁히면 graph 층이(DS-2 (나)) 바뀐다(N3.1). S-2 '핵심 유지'와 다르다 | S-2 | **필요**(결정은 M2 숫자와 함께) |
| XS-6 | **k 출처 이동**: `offset_trim.coverage_multiple`(OT §5.1, 시험 회로 값 T-25)을 요구의 `coverage_multiple`로 옮긴다. 승인된 스키마와 T-25의 기록 형식이 바뀐다(값은 같음) | OT §5.1, T-25 | **필요** |
| XS-8 | **DS-1 (가)·(다), DS-2 (가)는 같은 실행 안 변형 사이 재계산을 받아들이는 편차**: (가)는 같은 topology 변형이 같은 θ를 밟으면 같은 평가 키를 변형마다 다시 계산한다(완료 조건 3과 모순, N3.1 표). (다)는 키를 나눠 형식상 조건 3을 지키지만, 같은 θ의 커널 평가와 요청이 다른 metric 블록 계산이 변형마다 남는다. DS-2 (가)는 같은 topology의 S1v를 변형마다 다시 계산한다. 셋 다 '처음 계산한 값을 나머지 최적화에서 재사용'과 거리가 있다 | 원래 취지 문장(N1.1) | **필요**(결정은 M2 숫자와 함께) |
| XS-9 | **trim 시험 회로 spec 영향**: 승인된 T-27은 시험 회로 spec에 `offset_excess` 제약을 유지한다(강등 경로 확인용). T-28은 그 spec(`offset_trim` 섹션 = residual_offset_v·coverage_multiple·trim_temperature_c, T-25)을 TR-1 병합 뒤 `assets/fixture/trim/`에 둔다. 이 계획의 로더 규칙에서는 (1) 요구 없는 `offset_trim` 단독은 거부(N3.2), (2) 요구와 `offset_excess` 공존은 거부(DS-U2), (3) k는 요구로 옮긴다(XS-6). 그래서 그 spec은 요구 섹션(`strategy: trim`, k, `offset_in_max_v` ≥ V_res)으로 다시 써야 하고, '강등 경로 확인'이라는 T-27의 목적은 대상이 사라진다. `offset_in_max_v` 값은 사용자 몫이다 | T-25·T-27·T-28 | **필요**(재승인) |
| XS-10 | **matching 합성 판정과 출발값은 핵심 층 확장**: G-S1(새 metric 또는 합성 제약 행)과 G-S2(`iv_matching_l`이 합성 판정에서 σ 목표를 읽게 함)는 metrics·search 층을 고친다(N3.10). S-2 '핵심 유지'와 다르다. 확장 없이 기존 `offset_in_sigma_mv`·`offset_sys_mv` 두 제약으로 쓰려면 한계를 나누는 비율을 발명해야 해서 택하지 않는다 | S-2 | **필요** |
| XS-11 | **S-4 순서 문구를 나눈다**(권고안, N7.1): '실행 계획 구현 → TR-1'에서 TR-1 앞에는 단일 변형 실행 계획(matching)과 trim 단계 선택 흐름 대체까지만 구현한다. 다변형 공유·변형 정체 칸·Σ 상한은 trim·compare를 처음 여는 TR card에 묶어 그때 배선한다. 이유: 다변형 경로는 TR card 전에는 제품 경로에서 쓰이는 변형이 없어 '만들면 배선'을 지킬 수 없다. 대안 (ii): 다변형 경로를 TR-1 앞에 다 구현하고, TR card 전까지는 fixture spec으로만 실행하는 것을 승인받는다 | S-4 | **필요** |
| XS-12 | **변형별 E_total**(N3.7): 40 §2.4.9 E_total('실행 하나의 커널 평가 수 상한', 유일한 정의)과 §2.4.5 색인 상한 식의 '실행 하나' 단위를 '변형 하나' 단위로 바꾸고, 실행 전체 상한은 Σ_v E_total,v가 된다. 식(E_B + N_T + R)은 X-17 그대로다 | X-17, 40 §2.4.9·§2.4.5 | 확인 요청 |
| XS-13 | **S3 evals·runs 줄에 변형 정체 칸 추가**: 같은 topology 변형은 `context_fp`가 같아 줄만으로 구분되지 않는다(F-5). S3 줄 형식 변경은 앞서 사용자 승인으로 처리했던 종류다(X-10: 실패 줄 `snapshot_fp` 칸) | X-10 선례 | 확인 요청 |
| XS-7 | **색인 수명 경계 문구**: 40 §2.4.5의 '실행 경계 = `run_stage_a` 진입'을 '실행 계획 진입'으로 바꾼다. 수명 단위('실행 하나, 실행 사이에 넘기지 않음')는 그대로라서 원래 취지와 맞는다고 보지만, 승인된 design 문구를 바꾸므로 보고한다 | X-12, 원래 취지 문장 | 확인 요청 |

**사용자 몫(이 계획이 하지 않음)**: 기존 library spec을 요구 형식으로 옮기는 것(DS-U5).

---

## N6. 선행 실측(착수 조건)

### M1. 평가 캐시 키에 제약 집합이 들어가는가 -- **실측 완료(2026-10-16, base `067614c`, 읽기)**

* **결과**: 들어가지 않는다. 사실과 근거는 N3.0 F-1(키), F-2(결과의 제약 의존), F-3(S1v 입력)이다.
* **결정 항목**: 평가를 '크기·metric(제약 무관) + 판정(변형별)'로 나누려면 범위가 kernel(`E/search/kernel.py:130, :146-151, :159-161`)과 graph(`E/graph/s1v_fields.py:249-251`)로 넓어진다. 처리 선택지 (가)·(나)·(다)와 완료 조건 3과의 관계는 N3.1 표다. 셋 다 원래 취지와 다르거나(XS-8) 핵심 층을 바꾸므로(XS-5) 기본안을 두지 않고, M2 숫자와 함께 사용자 결정으로 올린다(DS-1).

### M2. matching과 trim 국면 1이 같은 θ를 얼마나 밟는가 -- **측정 방법만(이번에는 재지 않음)**

메모리 제약 때문에 이번 계획 작성에서는 재지 않는다. 다음 방법을 OS-M card로 한다. 엔진 코드는 바꾸지 않는다.

1. **대상 회로 1개**: library에서 `offset_in_sigma_mv` 판정 제약을 가진 spec(F-9 기준 하나). 이 제약이 있어야 matching 쪽 L 하한 출발값이 켜져(offset-trim 계획 F-4) 두 변형의 출발이 실제로 갈린다.
2. **spec 두 개**(저장소 밖, 측정 agent 전용 임시 경로에 둔다. library spec은 고치지 않는다):
   * A(matching 대리) = 원본 spec 그대로.
   * B(trim 국면 1 대리) = A에서 offset 판정 제약(`offset_in_sigma_mv`·`offset_sys_mv`·`offset_excess`)을 뺀 것. OT §10.8의 국면 1 의미 전환(σ_in 판정 없음, 나머지는 보고)과 같은 제약 집합이다. 지금 엔진은 trim 경로가 없으므로 이 대리가 국면 1의 탐색 궤적을 대신한다. 한계는 결과와 함께 적는다(DAC 관련 계산은 국면 1에 없으므로 대리와 실제의 차이는 후보 계산 블록뿐이다).
3. **측정 base 고정**: XRUN-F1 card A 병합 뒤의 master 커밋 하나에 고정한다(측정 agent가 측정 시작 때 해시를 기록하고, A·B 두 실행이 같은 해시·같은 worktree를 쓴다). card A가 θ 좌표 왕복(ln↔exp)을 고치므로(X-1 (1)) 그 전 base의 θ 키는 비교 근거로 쓰지 않는다.
4. **실행**: 같은 `SearchSettings`(선언 E_B, 같은 BLAS 스레드 설정), 같은 LUT로 A, B를 **별도 프로세스에서 차례로 한 번씩** 돈다(동시 실행 금지). 각 실행은 자기 S3 루트에 evals를 쓴다.
5. **측정값**(base에서 실제로 나오는 칸만, F-13. 읽기 전용 스크립트가 케이스마다 결과 파일에 append):
   * `context_fp`: 두 실행의 S3 폴더 이름(`archive.py:42-43`)이 같은지. M1을 실행으로 다시 확인한다.
   * θ 키 집합 T = (`schema_fp`, `cells`, `w_fixed_fp`, `theta_hex`)(S3 evals 줄, `kernel.py:71-72`)의 |T_A|, |T_B|, |T_A ∩ T_B|.
   * 겹친 키의 `seq` 분포: 각 실행에서 겹친 키가 나온 `seq` 목록(출발 직후 연속 구간인지, 탐색 중간에 흩어지는지).
   * `perf` 합계(`find_front.py:127-133`): `kernel_calls`, `unique_keys`, `block_computes`, `block_recomputes_same_input`, `wall_s`, `eval_time_median_s`. 겹친 키 수 × `eval_time_median_s`로 겹침의 시간 규모를 어림한다(평가별 시간은 base에 없다).
6. **card B 뒤로 미루는 측정**: 평가별 커널 시간과 블록별 계산 수, 블록 결과 색인 키 집합의 교집합은 base에 칸이 없다(F-13, F-8). XRUN-F1 card B(색인·`RunCounters`) 병합 뒤 같은 방법으로 다시 잰다.
7. **보고**: 숫자만 보고하고 판정 문턱을 두지 않는다(NFR-S6). DS-1 (가)·(나)·(다), DS-2 선택은 이 숫자와 각 선택지의 범위(N3.1 표)를 함께 사용자에게 올린다.
8. **시점**: 방법·스크립트·대리 spec 준비는 S-4대로 XRUN-F1 card A 진행 중에 한다. 실제 실행은 위 3의 base(card A 병합 뒤)에서 한다. 엔진은 바꾸지 않고 출력만 읽는다. 다른 무거운 실행과 겹치지 않게 순서를 잡는다.

---

## N7. 순서·의존·card 초안

### N7.1 순서(S-4)

NFR-4 card 2 병합 → XRUN-F1 card A → B → C → **실행 계획 구현(OS-1·OS-2)** → trim TR-1. 이 계획 문서(OS-0 전 단계)와 M2 준비(OS-M)는 card A 진행 중에 한다.

**권고안(XS-11, 승인 필요)**: S-4의 '실행 계획 구현'을 둘로 나눈다.
* **TR-1 앞(OS-1·OS-2)**: 단일 변형 실행 계획(요구 없음·`matching`)과, OT §4의 단계 선택 흐름을 실행 계획의 국면 규칙으로 대체하는 것까지. 이 범위는 병합 즉시 제품 경로(`matching` 요구 spec, 요구 없는 spec)에서 쓰인다.
* **trim·compare를 처음 여는 TR card에 묶음(OS-5)**: 다변형 실행(변형 사이 공유), 변형 정체 칸(S3·결과 JSON), Σ 색인 상한(N3.7), DS-1·DS-2 처리. 이 경로를 쓰는 변형은 trim·compare뿐이라 TR card 전에 만들면 쓰는 곳이 없다(만들면 배선, NFR-S7).
* **대안 (ii)**: 다변형 경로를 TR-1 앞에 다 구현하고, TR card 전까지는 fixture spec으로만 실행하는 것을 사용자 승인으로 받는다.

추가 의존:
* matching 유도 제약의 V_sys는 단일 출력 회로에서 '출력 기준 DC' 기능(T-19~T-23, XRUN-F1 뒤·TR-6 전)이 있어야 정의된다. 그 전에는 해당 회로가 N4-3 사유로 멈춘다(fail-closed). OS-1의 검증 fixture는 기준이 이미 정의되는 회로로 고른다.
* trim·compare 변형은 TR card(TR-1 → … → TR-6)가 경로를 만든 뒤에 열린다(N3.5 마지막 항목). TR-2 병합은 U16 뒤다(T-15).

### N7.2 card 초안

**공통 착수 조건**: N7.1 순서. design 문서 `docs/02-design/features/offset-strategy.design.md`가 있고 독립 검증과 사용자 승인을 받았다(bkit PDCA). 그 card가 읽는 N10 결정이 닫혀 있다.

| card | 범위 | 선행 | 읽는 결정 |
|---|---|---|---|
| OS-0 (문서) | design: 요구 스키마·사유 코드·유도 제약의 metric/행 형식(G-S1)·출발값 규칙(G-S2)·변형 spec 생성(지문 재계산)·`RunPlan` 형식·계획 함수와 실행기 서명·결과 JSON 칸·비교 도구 위치와 칸·예산 식·파일 분할·배선표·test 목록. OS-5 몫(변형 정체 지문·S3 변형 칸·Σ 상한)은 형식만 정한다. OT §4·§5.1·§5.2·§9.4·§9.5·§10.1과 40 §2.4.5 수명 문구 개정안, T-27·T-28 시험 회로 spec 재작성안(XS-9)을 같이 낸다. 독립 검증 | 이 계획 승인, M2 결과 | XS-1~XS-13, DS-1·DS-2, DS-U1~DS-U9 |
| OS-M (측정) | N6 M2. 엔진 무변경, 읽기 전용 스크립트와 임시 spec(저장소 밖). 2차 측정(평가별 시간·블록별 수)은 card B 뒤 | 준비: 이 계획(초안이어도 됨). 실행: card A 병합 | -- |
| OS-1 | 요구 스키마 로더(N3.2, `offset_trim` 단독 거부 포함), matching 유도 제약(N3.3, G-S1 핵심 층 확장), 출발값(G-S2), 공통 판정 검사(N3.4). 요구 없는 spec 무동작 | OS-0, XRUN-F1 C | XS-1·XS-6·XS-9·XS-10, DS-U1~DS-U4 |
| OS-2 | 파이프라인 층 재작성(단일 변형): `build_run_plan`(요구 없음·`matching`, 국면 규칙), 실행기, 변형 spec 생성, 블록 결과 색인·`RunCounters` 수명을 실행 계획 진입으로, 결과 JSON. 옛 진입 흐름은 같은 변경에서 지운다. trim·compare 요청은 fail-closed 거부 | OS-1 | XS-4·XS-7·XS-11 |
| OS-3 | 읽기 전용 비교 도구(N3.8). **TR-1 뒤, trim 국면 2(TR-6) 병합 뒤**에 한다. 비교 입력인 trim 국면 2 결과 JSON은 TR-6 뒤에야 생기기 때문이다(그 전에 만들면 쓰는 곳이 없다) | OS-2, OS-5, TR-6 | XS-3 |
| OS-5 (TR card에 묶음) | **TR-1 뒤**, trim 국면 1을 처음 제품 경로에 여는 TR card(TR-2, U16 뒤, T-15)와 함께: 다변형 실행(compare 국면 1 = matching + trim 국면 1), 변형 사이 공유, DS-1·DS-2 처리(모든 선택지가 핵심 층 변경을 포함), 변형 정체 칸, Σ 색인 상한, 변형별 예산 | OS-2, TR-2, DS-1·DS-2 결정, XS-12·XS-13 확인 | XS-5·XS-8·XS-11·XS-12·XS-13 |

**TR-1 앞/뒤**: OS-0·OS-M·OS-1·OS-2는 TR-1 앞, OS-5는 TR-1 뒤(TR-2와 함께), OS-3은 TR-6 뒤다.
| (TR 연결) | TR card가 trim 국면 1·2 변형을 계획에 연결하고 거부를 푼다. 범위 조정은 OS-0의 OT 개정안이 정한다 | 각 TR card 선행 그대로 | XS-2·XS-4 |

완료 조건이 걸리는 card: 1·5·7·8은 OS-1·OS-2부터, 2·3·4는 OS-5부터(변형이 둘 이상인 계획이 생길 때), 6은 OS-3.

**완료 조건**(기능 전체):
1. **요구가 없는 실행**에서 9회로 결과가 base와 비트 동일하다. base는 XRUN-F1 card C 병합 뒤 기준선이다. 비교에서 빼는 칸은 계수·시간 칸(40 §2.4.13 T 부류)과, 실행 경계 문구 변경으로 바뀌는 칸이 있으면 그 목록이다(design이 정하고 검증자가 소유).
2. **계획 안 결과 = 단독 결과**: 변형이 둘 이상인 계획에서 각 변형의 결과가 그 변형만 담은 계획으로 돈 결과와 비트 동일하다(T 부류 제외). 변형 순서를 바꿔도 같다. **범위는 E_B를 선언한 실행이다.** 시간 예산에서 E_B를 유도하는 실행(X-17 후반)은 유도값이 평가 시간 중앙값에 의존하고(`kernel.py:153-158`, card C 뒤 `search_ceiling`), 앞 변형의 블록 결과 적중으로 뒤 변형의 평가 시간이 짧아지면 유도 E_B가 달라진다. 벽시계 정지(F-6)도 같다. 이런 실행에서 비트 동일을 요구하려면 유도 규칙을 따로 정해야 한다(예: 계획 안 첫 변형의 유도값을 모든 변형에 쓰는 규칙). 그 규칙은 DS-U9로 두고, 정해지기 전에는 유도 실행을 조건 2에서 빼고 결과에 '유도 예산 -- 단독과 다를 수 있음'을 적는다. 이 제외는 기준 약화가 아니라 범위 표기이고, 검증자가 확인한다.
3. **재계산 0**: 실행 계획 전체에서 같은 입력의 블록 재계산 0, 같은 평가 키 재계산 0(40 §2.4.9 판정 1을 실행 전체에).
4. **공유 증거**: 같은 topology 변형 둘을 담은 계획에서 S1 블록 계산 수가 변형 하나일 때와 같다. 블록 결과 색인 적중 수와 S1v 재계산 수(DS-2)를 결과에 낸다.
5. **fail-closed 증거**: N3.2 로더 규칙과 N3.3 정지 조건마다 거부 test가 실제로 거부한다(통과가 아니라 거부를 먼저 확인).
6. **비교 도구**: 엔진 import 0, 권고 문장 0, `code_fp`·공통 판정 불일치 표시.
7. 모든 새 함수가 진입점에서 호출된다(배선 증거). 옛 진입 흐름이 남지 않는다.
8. 상위 N6.3의 graph 단일 정본·재계산 계수·파일 분할 확인과 design 대 구현 gap 분석을 통과한다.

---

## N8. 원문 근거표

* 보관 위치: `skills/analog-gmid-design/assets/technique/sources/<폴더>/`(`source.pdf`·`paper.md`, 목록은 그 폴더 `README.md`). 쪽 렌더는 skill 폴더에서 `python tools/pdf_to_md.py ensure`로 만든다.
* 쪽 번호는 PDF 쪽이다. 수치는 인용하지 않는다. trim 규칙 자체의 원문은 offset-trim 계획 N8이 정본이다.

| R | 원문 | 웹 | 로컬 PDF | 쪽·위치 | 이 계획에서 쓰는 곳 |
|---|---|---|---|---|---|
| R1 | Y. Zhou, A. Kay, 'Offset Correction Methods: Laser Trim, e-Trim, and Chopper', TI SBOT037A, 2017 | [ti.com/lit/SBOT037](https://www.ti.com/lit/SBOT037) | `offset_trim__zhou_2017/source.pdf` | p.1 e-Trim, p.2 Fig.3·Table 1(chopper가 1/f와 시간·온도 drift를 없앤다) | trim은 1/f를 보정하지 않으므로 1/f를 두 방식 공통 판정으로 둔다(N3.4) |
| R2 | A. Kay, 'Op Amp Offset Voltage and Bias Current Limitations', TI SBOA590, 2024 | [ti.com/lit/pdf/sboa590](https://www.ti.com/lit/pdf/sboa590) | `offset_trim__kay_2024/source.pdf` | §1.2 PDF p.7 Figure 1-8 문단 | CMOS offset trim은 drift를 보정하지 않는다. compare 보고에 이 한계를 그대로 싣는다(N3.8) |
| R3 | H. M. von Staudt, 'Trim DAC Design with Minimum DNL for Self-Trim with Self-Test Schemes', IEEE IMS3TW 2011 | [doi:10.1109/IMS3TW.2011.34](https://doi.org/10.1109/IMS3TW.2011.34) | `offset_trim__staudt_2011/source.pdf` | p.1-2 §II.A | trim 보정 구간이 미보정 분포를 덮어야 한다는 조건. 요구의 k를 trim 보정 구간 배수로 쓰는 근거(N3.2, N3.3) |

matching 유도식 k·σ_in + |V_sys| ≤ `offset_in_max_v`는 사용자 결정 S-1의 식이고, σ_in·V_sys는 엔진 해석(`offset_analysis`·`offset_systematic`)의 값이다. 원문 수치나 관례 배수는 쓰지 않는다.

---

## N9. 위험과 대응

| 위험 | 대응 |
|---|---|
| 같은 topology 변형이 평가 캐시를 공유해 다른 변형의 제약 행이 적중한다(F-1·F-2) | 지금 키 그대로의 공유는 금지(N3.6). 나누는 방식은 DS-1. 완료 조건 2(계획 안 = 단독)가 잡는다 |
| DS-1 (가)를 고르면 완료 조건 3(같은 평가 키 재계산 0)과 모순된다 | 조건을 약화하지 않는다. 약화는 DS-U7로 사용자 승인을 받을 때만 |
| matching 합성 판정·출발값이 핵심 층을 건드린다(N3.10) | XS-10 승인 뒤에만 OS-1 착수. 범위는 metrics 레지스트리 또는 `ss_constraint_rows` 한 곳과 `iv_matching_l` 한 곳으로 design이 닫는다 |
| S1v·metric 블록이 제약 extras 때문에 변형마다 다시 계산돼 공유 효과가 줄어든다(F-2·F-3) | 완료 조건 4로 수를 드러내고 M2와 함께 DS-1·DS-2로 사용자에게 올린다. 숨기지 않는다 |
| 실행 계획 전체로 색인 수명이 길어져 메모리가 는다 | 상한 식(N3.7)으로 등록 때 fail-closed. M2의 θ 겹침 수와 블록 수로 미리 잰다. 변형 수는 방식 표(N3.5)로 닫혀 있다 |
| 실행 전체 시간이 변형 시간의 합이 된다 | 변형별 예산(N3.7)을 결과에 낸다. 시간 예산 유도는 변형마다 |
| 단일 출력 회로에서 V_sys 기준이 없어 matching 유도 제약을 잴 수 없다 | 탐색 전 정지(N4-3). '출력 기준 DC' 기능 뒤에 열린다(N7.1) |
| 요구와 수단 제약이 섞인 spec이 조용히 한쪽만 판정된다 | 로더 거부(N3.2) |
| compare 표가 권고로 읽힌다 | 도구에 판정·권고 문장 금지(N3.8). 보고에 '권고 아님'과 R1·R2 한계를 싣는다 |
| 국면 2만 돈 compare에서 matching 결과가 다른 코드·다른 선언으로 만든 것이다 | 비교 도구가 `code_fp`·공통 판정 선언 불일치를 표에 적는다(N3.8) |
| 승인된 offset-trim design(§4·§5.1·§5.2·§9.4·§10.1)을 고쳐 TR-1 착수가 늦어진다 | OS-0이 개정안을 같이 내고 한 번에 재승인받는다(S-4). TR-M·TR-L처럼 영향 없는 card는 그대로 진행 |
| library spec이 요구 형식이 아니어서 기능이 library에서 쓰이지 않는다 | 검증은 fixture spec으로 한다(N4). 옮기는 것은 사용자 몫(DS-U5)이고 보고에 적는다 |
| 계획 안 변형 순서가 결과를 바꾼다(숨은 상태) | 블록 순수성(40 §2.4.5 결정성)과 변형별 캐시. 완료 조건 2의 순서 뒤집기 test |

---

## N10. 열린 결정

### N10.1 사용자 결정 필요

기본안은 원칙으로 정한 것이고 사용자가 바꿀 수 있다. N5의 XS-1~XS-13 승인·확인도 사용자 몫이다.

| ID | 질문 | 기본안 |
|---|---|---|
| DS-1 | M1 결과(제약이 평가 키 밖, 결과는 제약 의존)에 대한 처리. (가) `S3Index`의 평가 키 부분은 변형별, 블록 결과 부분만 공유(card B 뒤에는 search 변경, 완료 조건 3과 모순, XS-5·XS-8). (나) 평가를 크기·metric(계획 안 요청 합집합)과 변형별 판정으로 나눈다(kernel·graph 변경, XS-5). (다) 평가 키에 변형 제약 지문을 넣어 키를 나눈다(search 변경, XS-5·XS-8). 선택지별 완료 조건 3 관계는 N3.1 표 | **기본안 없음**. M2 숫자와 함께 결정받는다. 필요한 시점은 OS-5 |
| DS-2 | S1v 블록이 제약 tuple 전체를 extras로 받아(F-3) 같은 topology 변형마다 다시 계산되는 몫. (가) 받아들인다(입력 지문이 달라 판정 1 형식 위반은 아니지만 같은 값의 재계산, XS-8). (나) S1v 투영을 뷰 선언·루프 끊는 넷으로 좁힌다(graph 층 변경, XS-5) | **기본안 없음**. M2(card B 뒤 2차)의 S1v 계산 수와 함께 결정받는다 |
| DS-U1 | matching에서 `offset_excess`(구조 가드)를 요구와 함께 둘 수 있게 할지 | 두지 않는다(N3.2 거부). 요구가 offset 판정의 유일한 출처 |
| DS-U2 | 요구와 수단 제약 공존 거부의 범위: `offset_in_sigma_mv`·`offset_sys_mv`·`offset_excess` 셋 다인가 | 셋 다(XS-1) |
| DS-U3 | k의 출처를 요구 하나로 옮기는 것(`offset_trim.coverage_multiple` 삭제) | 옮긴다(XS-6, 단일 정본) |
| DS-U4 | compare에서 공통 판정이 없을 때. '있음'의 정의: 1/f는 `noise_fc_in_hz`나 `noise_out_int_vrms` 가운데 하나 이상이 값이 있는(결정 대기 아님) 판정 제약으로 선언됨, 면적은 `area_search_m2 <=`가 값이 있는 판정 제약으로 선언됨. 둘 다 있어야 한다 | 하나라도 없으면 탐색 전 거부(같은 기준 없이는 나란히 놓을 수 없음). `matching`·`trim` 단독은 요구하지 않는다 |
| DS-U6 | N+1 구성의 m 규칙(XS-2). OT §3.4 집계는 추천 N 하나에 대해 m = min_p m_max,p(N)이다 | N+1에도 같은 집계 규칙을 그대로 쓴다: m = min_p m_max,p(N+1). 어떤 집계 점에서 m_max,p(N+1)이 정의되지 않으면 N+1 구성은 내지 않고 사유를 후보표에 적는다(새 상수 없음) |
| DS-U7 | (DS-1 (가)를 고를 때만) 완료 조건 3을 '변형 안 같은 평가 키 재계산 0 + 변형 사이 수는 보고'로 바꾸는 것 | 바꾸지 않는다. **기준 약화**라 사용자 승인 없이는 하지 않는다 |
| DS-U9 | 시간 예산에서 E_B를 유도하는 실행의 다변형 규칙(완료 조건 2) | 계획 안 첫 변형의 유도 규칙으로 정한 평가 수를 같은 계획의 모든 변형에 쓴다(새 상수 없음, 유도 근거가 결과에 남음). 정해지기 전에는 유도 실행을 조건 2에서 빼고 결과에 표기 |
| DS-U8 | trim 시험 회로 spec을 요구 형식으로 다시 쓸 때 `offset_in_max_v` 값과 `offset_excess` 처리(XS-9) | 사용자 몫. `offset_excess`는 DS-U2 기본안대로 빼고, `offset_in_max_v` ≥ 승인된 V_res(T-25) 조건만 로더가 본다 |
| DS-U5 | 기존 library spec(특히 `offset_in_sigma_mv`를 가진 spec, F-9)을 요구 형식으로 옮길지와 그 값 | 사용자 몫. 이 기능은 옮기지 않는다 |

### N10.2 오케스트레이터 기본안(원칙으로 확정, 사용자가 바꿀 수 있음)

| ID | 항목 | 기본안과 근거 |
|---|---|---|
| DO-2 | 국면 결정 방식 | 승인 기록 유무(정해진 위치). 진입 인자 분기 없음(S-2) |
| DO-3 | 변형 순서 | N3.5 표 순서 고정. 결과 무관은 완료 조건 2가 확인 |
| DO-4 | 블록 결과 색인·`RunCounters` 수명 | 실행 계획 하나(XS-7 확인 요청) |
| DO-6 | TR card 전 trim·compare 요청 | 계획 함수가 fail-closed 거부 |
| DO-7 | 비교 도구 위치 | 엔진 밖 `tools/`, 엔진 import 금지. 정확한 경로는 design |
| DO-8 | M2 대리 spec 위치 | 저장소 밖 측정 agent 전용 임시 경로. library 무변경 |
| DO-9 | 승인 파일이 있을 때 국면 1 재실행 방법 | 사용자가 승인 기록 파일을 정해진 위치에서 치운다. 엔진은 승인 파일을 고치지 않고, 국면 강제 인자는 두지 않는다. 낡은 승인은 국면 1로 돌아가지 않고 정지(N3.5) |

변형별 예산(옛 DO-1)과 S3 줄 변형 칸(옛 DO-5)은 승인된 정의·형식을 바꾸므로 확인 요청 항목 XS-12·XS-13으로 옮겼다(N5).

### N10.3 OS-0 design에서 닫을 기술 항목

| ID | 항목 |
|---|---|
| G-S1 | matching 합성 판정의 형식: k를 입력으로 받는 새 metric인가, `offset_in_sigma_mv`·`offset_sys_mv`를 읽는 합성 제약 행인가. 분해능 규칙(기존 ss 제약 행 규칙과 정합). 그리고 다음 둘:<br>• **단위**: σ_in·V_sys metric은 mV 단위(`registry.py:56-58`의 단위 칸 `mv`), `offset_in_max_v`는 V다. 환산은 숫자 1000을 쓰지 않고 단위 어휘(레지스트리 단위 칸과 키 접미 `_v`, core 단위 접두 정의, 예: `iv_matching_l.py`가 쓰는 core `MILLI`)에서 읽는 규칙으로 정한다<br>• **view 출처**: offset metric은 transfer 뷰 metric인데(F-3a) 요구 섹션에는 view 선언이 없다. 유도 제약의 view를 어디서 가져오는지(입력 셀 전달 뷰 = `metric_structure`, 기본 뷰, 사용자 선언 중 하나)를 정한다. 이 선택이 변형별 S1v 값이 같은지(N3.1-3)를 정한다 |
| G-S2 | matching 출발값(`iv_matching_l` L 하한)의 입력을 유도 제약으로 바꾸는 규칙 |
| G-S3 | 변형 정체 지문(topology `connectivity_fp` + 제약 집합 지문)의 정의와 S3·결과 JSON 칸 |
| G-S4 | 변형 제약 집합의 기록 형식: 유도 제약을 spec 판정 제약과 같은 형식으로 만들 때 출처 칸(`value_from_spec` 계열) |
| G-S5 | DS-2 (가)일 때 S1v 재계산 수를 결과 JSON에 내는 칸과 계수 정의(완료 조건 4) |
| G-S6 | 완료 조건 1의 비교 제외 칸 목록(검증자 소유) |
