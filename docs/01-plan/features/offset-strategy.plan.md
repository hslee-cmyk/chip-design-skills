---
template: plan
version: 0.1
---

# offset-strategy Planning Document

> **Summary**: spec이 offset을 **수단**(`offset_in_sigma_mv <=` 제약이나 `offset_trim` 선언)이 아니라 **요구**로 쓰게 한다. 요구는 `offset_requirement{offset_in_max_v, coverage_multiple, strategy}` 하나다. 엔진은 요구와 방식(`matching`·`trim`·`compare`)에서 판정 제약을 유도하고, **실행 계획**(변형 목록, 변형 = (topology 변형, 제약 집합))을 만들어 한 실행 안에서 차례로 돈다. 변형들은 단계 A·S0·블록 결과 색인을 공유한다. 이 일은 파이프라인 층 모듈을 다시 쓰는 것이고(S-2), 핵심 층(graph·블록·kernel·search)은 유지한다.
>
> **Project**: chip-design-skills (analog-gmid-design skill) · **Author**: Claude Code
> **Status**: 계획 초안 v0.1 (2026-10-16). 독립 검증·사용자 승인 전이다. 근거는 사용자 결정 S-1~S-4(원문 `wt/_drafts/user_decisions.md` '## offset 방식 선택·실행 계획 (2026-10-16 사용자 "권고대로 해")')다.
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
| F-3 | **S1v 블록 입력에 제약 tuple 전체가 들어간다.** 단계 A가 spec 판정 제약 전체를 `build_s1v`에 넘기고, 블록 `s1v_fields`는 그것을 extras로 받는다(뷰 선언을 읽기 위해). 안정도 제약의 루프 뷰 끊는 넷도 spec 제약에서 온다. 그래서 제약 집합이 다르면 같은 topology라도 S1v 블록의 입력 버전이 다르다 | `E/graph/s1v_build.py:39-42`, `E/graph/s1v_fields.py:249-251`, `E/pipeline/stage_a.py:152-160` |
| F-4 | **탐색 쪽 S0 블록도 spec을 읽는다**: 면적 예산(`area_search_m2 <=`의 최솟값)으로 θ 상자를 닫고, 제약 분류, 출발 구간, 잡음·mismatch LUT 데이터 필수 검사가 spec 제약에서 온다 | `E/search/search_context.py:156-168, :171-196`, `E/pipeline/stage_b.py:153` |
| F-5 | 실행 수명 상태(평가 캐시 `cache`, `computed_keys`, 계수, `eval_budget`, `deadline`)는 `SearchContext` 객체 하나에 있다. S3 기록기는 `S3Archive(root, context_fp, code_fp)`다 | `E/search/search_context.py:53-69, :212` |
| F-6 | `find_front`는 호출마다 벽시계 정지 시각을 정하고, 판정 metric의 검증 출처를 `sctx.ss_constraints`·`sctx.judged_constraints`에서 모은다 | `E/search/find_front.py:75-78, :94` |
| F-7 | 진입점 서명은 `run_stage_a(topology_path, spec_path, lut, *, output_dir, supplies_v=None, structure_path=None)`, `run_stage_b(stage_a, memo, pdk_decl, *, output_dir, settings, diagnostic=False)`다. 엔진 코드에 'trim'은 없다. `trim_approval_path`는 OT §4 design에만 있다 | `E/pipeline/stage_a.py:195`, `E/pipeline/stage_b.py:134`, grep 2026-10-16 |
| F-8 | XRUN-F1 card A·B·C는 base에 병합되지 않았다. 블록 결과 색인(`search/s3_index.py`)·`search_ceiling.py`·`search_stop.py`는 아직 없다. 색인 수명·상한·E_total 규칙은 design(40 §2.4.5, §2.4.9, §2.4.14)이다 | `ls E/search/` 2026-10-16 |
| F-9 | library에서 `offset_in_sigma_mv` 판정 제약을 가진 spec은 하나다. `offset_excess`는 6개 spec에 있다 | `assets/library/current_reuse_telescopic_ota.sizing_spec.json:226`, `folded_cascode…:49`, `ngcc_3stage_ff…:111`, `nmcnr_amplifier…:141`, `sf_pushpull_output_opamp…:131`, `two_stage_ota…:81`, `two_stage_ota_sf…:82` |
| F-10 | 1/f·면적 metric은 레지스트리에 있다: `noise_fc_in_hz`, `noise_out_int_vrms`, `area_search_m2`. offset metric은 `offset_in_sigma_mv`·`offset_excess`(`OffsetAnalysis`), `offset_sys_mv`(`OffsetSystematic`)다 | `E/metrics/registry.py:49, :52, :54, :56-58` |
| F-11 | 승인된 trim design은 2단계 실행에서 S0를 두 벌(원본·파생) 계산하므로 색인 상한을 Σ 분할 수 × (E_total + 2)로 둔다 | OT §10.1 |

### N3.1 M1 결과와 그 뜻

M1(평가 캐시 키에 제약 집합이 들어가는가)은 **들어가지 않는다**(F-1). 반면 평가 결과는 제약 집합에 의존한다(F-2). 이것이 이 계획에 주는 뜻은 다음과 같다.

1. **같은 topology 변형끼리 평가 캐시를 그대로 공유하면 틀린다.** matching 변형과 trim 국면 1 변형은 원본 topology가 같아 `context_fp`가 같다. 한 `SearchContext`의 캐시를 함께 쓰면, 한 변형의 제약 행을 담은 `EvalResult`가 다른 변형에 적중으로 돌아간다. 그래서 변형마다 평가 캐시를 따로 두거나(DS-1 (가)), 키에 제약 지문을 넣거나, 평가를 나눠야 한다(DS-1 (나)).
2. **블록 결과 색인은 공유해도 맞다.** 색인 키는 (블록, 분할, 입력 버전)이고 블록은 투영만의 순수 함수다(40 §2.4.5 '결정성'). 그래서 변형이 달라도 입력이 같은 블록은 적중하고 결과는 비트 동일하다.
3. **다만 공유 범위가 제약 쪽에서 끊긴다.** metric 블록은 요청 목록이 extras에 들어가므로(F-2), 두 변형의 요청 목록이 다르면 같은 θ라도 다른 입력이다. S1v 블록도 제약 tuple 전체가 extras라서(F-3) 같은 topology여도 변형마다 한 번씩 계산된다. 이것은 입력 지문이 달라서 생기는 계산이라 40 §2.4.9 판정 1('같은 입력 재계산 0')을 형식상 깨지는 않는다. 하지만 같은 값을 다시 계산하는 것이어서 원래 취지('그 계산된 값이 나머지 최적화를 진행할 때 재사용')와는 거리가 있다.
4. **'평가 = 크기·metric(제약 무관) + 판정(변형별)' 분리는 범위를 kernel까지 넓힌다.** 분리하려면 (i) 커널이 계획 안 모든 변형의 metric 요청 합집합을 한 번에 계산하고(`kernel.py:130`의 요청 출처 변경), (ii) 캐시 값에서 제약 행을 빼서 변형별 판정 단계로 옮기고(`kernel.py:146-151, :159-161`), (iii) S1v 투영을 뷰 선언·루프 끊는 넷으로 좁혀야 한다(`s1v_fields.py:249-251`, graph 층). 셋 다 S-2 '핵심 유지' 밖이다. 그래서 **결정 항목 DS-1**로 둔다(N5 XS-5, N10).

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
| `offset_trim.residual_offset_v`(V_res) > `offset_in_max_v` | 거부(S-1 로더 검사) |
| k의 출처 | 요구의 `coverage_multiple` 하나다. OT §5.1의 `offset_trim.coverage_multiple`은 두 번째 출처가 되므로 없앤다(XS-6, DS-U3) |
| 요구 섹션이 결정 대기 | 요구 없음과 같다(지금 흐름). 대기 표지는 기존 수집 경로로 보고 |

### N3.3 방식별 판정 제약 유도

유도 제약은 변형의 제약 집합에 spec 판정 제약과 함께 들어간다. 값은 요구 선언을 참조하고(`value_from_spec` 계열), 숫자를 복사하지 않는다(NFR-S2).

| 방식·국면 | 유도 제약 | 근거·전제 |
|---|---|---|
| matching | k·σ_in + \|V_sys\| ≤ `offset_in_max_v`. σ_in = `offset_in_sigma_mv`(F-10), V_sys = `offset_sys_mv`(크기) | S-1. 이 합성 판정을 새 metric(k를 입력으로 받음)으로 둘지, 두 metric을 읽는 합성 제약 행으로 둘지는 design G-S1이다. V_sys는 선언 출력 기준 DC가 있어야 정의된다(`offset_systematic`의 `reference_undeclared`). 그 기준이 없는 회로는 탐색 전에 멈춘다(fail-closed). 단일 출력 회로의 기준은 '출력 기준 DC' 기능(T-19~T-23)이 정한다(N7 의존) |
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
* 변형 순서는 위 표 순서로 고정한다(결정성, NFR-S5). 순서가 결과 값을 바꾸지 않음은 완료 조건 2가 확인한다.
* trim·compare 변형은 TR card가 그 경로를 만든 뒤에만 실행된다. 그 전에는 계획 함수가 `strategy`를 거부한다(fail-closed, 조용한 생략 금지). 거부 사유 코드는 design이 정한다.

### N3.6 실행기와 공유 범위

**함수**: `run_plan(plan, ...)`(pipeline 층, 이름은 design). 한 실행 = 실행 계획 하나다.

| 대상 | 공유 규칙 | 근거 |
|---|---|---|
| 블록 결과 색인·`RunCounters` | 실행 계획 진입에서 한 번 만들고, 모든 변형의 모든 블록 호출에 같은 객체를 넘기고, 실행이 끝나면 버린다. 40 §2.4.5 '수명'의 실행 경계 문구('`run_stage_a` 진입')를 '실행 계획 진입'으로 고친다. 실행 사이에는 넘기지 않는다 | X-12, 원래 취지 문장, XS-7 |
| 단계 A(S1·S1v·structure 사실·보고) | 같은 topology 변형끼리 공유한다. S1은 topology와 선언만의 함수라 변형 사이에 같은 입력이다. S1v는 제약 tuple이 extras라 변형마다 입력이 다르면 다시 계산된다(F-3). 이 몫을 받아들일지 투영을 좁힐지는 DS-2 | F-3 |
| S0 수준 탐색 블록(`search_domain`·`constraint_classes`·출발 구간 등) | 블록 결과 색인으로 공유한다. 입력이 같으면 적중, 다르면 계산 | F-4 |
| 평가 캐시·`SearchContext` | 변형마다 따로 둔다(기본안 DS-1 (가)). 같은 topology 변형끼리 `context_fp`가 같아 공유하면 틀린 결과가 적중한다(N3.1-1) | F-1, F-2 |
| 커널 안 블록(봉인·GB5·metric) | 블록 결과 색인으로 공유한다. 같은 θ의 크기 결정 블록은 변형 사이에 적중한다. metric 블록은 요청 목록이 같을 때만 적중한다(N3.1-3) | F-2 |
| S3 기록 | 변형마다 줄에 변형 정체를 싣는다. 같은 topology 변형은 `context_fp`가 같아 줄만으로 구분되지 않기 때문이다(F-5). S3는 출력이고 실행 사이에 읽지 않는다(U-89) | F-5 |

### N3.7 예산

* **기본안: 변형마다 E_total을 둔다.** 변형 v의 E_total,v = E_B + N_T + R(X-17 정의 그대로, R = 2 × 그 변형의 `len(sctx.domain.variables)`). 근거: E_total은 '실행 하나의 커널 평가 수 상한'으로 정의되고(40 §2.4.9) 변형마다 `find_front`가 한 번 돈다. X-17은 '선언 40은 그대로 동작, 판정·test 예산 변경 없음'을 지키려고 정해졌다. 변형마다 두면 변형 하나의 탐색이 지금 단독 실행과 같은 예산을 받아 NFR-S5(계획 안 결과 = 단독 결과)가 성립한다. 한 E_total을 변형들이 나누는 안은 변형별 탐색 품질과 결과가 계획 구성에 따라 바뀌어 NFR-S5를 깬다.
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
| XS-2 (b) | **N을 {N, N+1}로 연다**: OT §3.4·§9.4는 front 집계로 추천 N 하나(가능한 최소 N)를 낸다. 이 계획은 국면 1이 N과 N+1 두 구성의 파생 topology를 내고, 사용자가 승인한 것마다 국면 2 변형을 만든다. N+1은 LSB가 작아 잔여 조건에 여유가 생기는 대신 셀 수·면적이 는다. 이 교환을 사용자가 보게 하려는 것이다 | OT §9.4(사용자 T-18 승인) | **필요** |
| XS-3 (c) | **compare 추가**: 방식 하나를 고르는 대신 두 방식을 같은 공통 판정으로 돌려 나란히 낸다. 엔진은 권고하지 않는다 | offset-trim 계획은 trim 선언 회로만 다룸 | **필요** |
| XS-4 (d) | **OT §4 개정**: 진입 인자(`trim_approval_path`)로 단계를 고르던 승인된 흐름을 실행 계획의 국면 규칙(승인 기록 유무)으로 바꾼다 | OT §4(사용자 T-18 승인) | **필요**(S-4: 실행 계획 design과 함께 재승인) |
| XS-5 | **DS-1 (나)·DS-2 (나)를 고르면 핵심 층 변경**: 평가를 크기·metric과 판정으로 나누면 kernel·`ss_evaluate` 호출이, S1v 투영을 좁히면 graph 층이 바뀐다(N3.1-4). S-2 '핵심 유지'와 다르다 | S-2 | (나)를 고를 때만 **필요** |
| XS-6 | **k 출처 이동**: `offset_trim.coverage_multiple`(OT §5.1, 시험 회로 값 T-25)을 요구의 `coverage_multiple`로 옮긴다. 승인된 스키마와 T-25의 기록 형식이 바뀐다(값은 같음) | OT §5.1, T-25 | **필요** |
| XS-7 | **색인 수명 경계 문구**: 40 §2.4.5의 '실행 경계 = `run_stage_a` 진입'을 '실행 계획 진입'으로 바꾼다. 수명 단위('실행 하나, 실행 사이에 넘기지 않음')는 그대로라서 원래 취지와 맞는다고 보지만, 승인된 design 문구를 바꾸므로 보고한다 | X-12, 원래 취지 문장 | 확인 요청 |

**사용자 몫(이 계획이 하지 않음)**: 기존 library spec을 요구 형식으로 옮기는 것(DS-U5).

---

## N6. 선행 실측(착수 조건)

### M1. 평가 캐시 키에 제약 집합이 들어가는가 -- **실측 완료(2026-10-16, base `067614c`, 읽기)**

* **결과**: 들어가지 않는다. 사실과 근거는 N3.0 F-1(키), F-2(결과의 제약 의존), F-3(S1v 입력)이다.
* **결정 항목**: 평가를 '크기·metric(제약 무관) + 판정(변형별)'로 나누려면 범위가 kernel(`E/search/kernel.py:130, :146-151, :159-161`)과 graph(`E/graph/s1v_fields.py:249-251`)로 넓어진다. 이것을 DS-1로 올린다(N10). 기본안은 DS-1 (가)다(핵심 층 불변, S-2 그대로). (나)는 M2 결과와 함께 사용자 결정으로 올린다.

### M2. matching과 trim 국면 1이 같은 θ를 얼마나 밟는가 -- **측정 방법만(이번에는 재지 않음)**

메모리 제약 때문에 이번 계획 작성에서는 재지 않는다. 다음 방법을 OS-M card로 한다. 엔진 코드는 바꾸지 않는다.

1. **대상 회로 1개**: library에서 `offset_in_sigma_mv` 판정 제약을 가진 spec(F-9 기준 하나). 이 제약이 있어야 matching 쪽 L 하한 출발값이 켜져(offset-trim 계획 F-4) 두 변형의 출발이 실제로 갈린다.
2. **spec 두 개**(저장소 밖, 측정 agent 전용 임시 경로에 둔다. library spec은 고치지 않는다):
   * A(matching 대리) = 원본 spec 그대로.
   * B(trim 국면 1 대리) = A에서 offset 판정 제약(`offset_in_sigma_mv`·`offset_sys_mv`·`offset_excess`)을 뺀 것. OT §10.8의 국면 1 의미 전환(σ_in 판정 없음, 나머지는 보고)과 같은 제약 집합이다. 지금 엔진은 trim 경로가 없으므로 이 대리가 국면 1의 탐색 궤적을 대신한다. 한계는 결과와 함께 적는다(DAC 관련 계산은 국면 1에 없으므로 대리와 실제의 차이는 후보 계산 블록뿐이다).
3. **실행**: 같은 `SearchSettings`(선언 E_B, 같은 BLAS 스레드 설정), 같은 LUT로 A, B를 **별도 프로세스에서 차례로 한 번씩** 돈다(동시 실행 금지). 각 실행은 자기 S3 폴더에 evals를 쓴다.
4. **측정값**(읽기 전용 스크립트, 케이스마다 결과 파일에 append):
   * 두 실행의 `context_fp`가 같은지(M1을 실행으로 다시 확인).
   * θ 키 T = (`schema_fp`, `cells`, θ hex) 집합(S3 evals 줄의 평가 키에서 `context_fp`를 뺀 부분)의 |T_A|, |T_B|, |T_A ∩ T_B|, 그리고 겹친 키가 처음 나오는 seq 구간(출발 직후 몇 평가가 같은가).
   * 겹친 θ의 커널 시간 합이 각 실행 커널 시간 합에서 차지하는 몫(S3 줄 시간 칸).
   * `perf.blocks`의 블록별 계산 수. XRUN-F1 card B가 병합된 뒤라면 블록 결과 색인 키 집합의 교집합도 같은 방식으로 센다(그 전에는 θ 수준만).
5. **보고**: 숫자만 보고하고 판정 문턱을 두지 않는다(NFR-S6). DS-1 (가)/(나) 선택은 이 숫자와 (나)의 범위(N3.1-4)를 함께 사용자에게 올린다.
6. **시점**: S-4대로 XRUN-F1 card A 진행 중에 할 수 있다(엔진 무변경, 출력만 읽음). 다른 무거운 실행과 겹치지 않게 순서를 잡는다.

---

## N7. 순서·의존·card 초안

### N7.1 순서(S-4)

NFR-4 card 2 병합 → XRUN-F1 card A → B → C → **실행 계획 구현(OS-1·OS-2)** → trim TR-1. 이 계획 문서(OS-0 전 단계)와 M2(OS-M)는 card A 진행 중에 한다.

추가 의존:
* matching 유도 제약의 V_sys는 단일 출력 회로에서 '출력 기준 DC' 기능(T-19~T-23, XRUN-F1 뒤·TR-6 전)이 있어야 정의된다. 그 전에는 해당 회로가 N4-3 사유로 멈춘다(fail-closed). OS-1의 검증 fixture는 기준이 이미 정의되는 회로로 고른다.
* trim·compare 변형은 TR card(TR-1 → … → TR-6)가 경로를 만든 뒤에 열린다(N3.5 마지막 항목). TR-2 병합은 U16 뒤다(T-15).

### N7.2 card 초안

**공통 착수 조건**: N7.1 순서. design 문서 `docs/02-design/features/offset-strategy.design.md`가 있고 독립 검증과 사용자 승인을 받았다(bkit PDCA). 그 card가 읽는 N10 결정이 닫혀 있다.

| card | 범위 | 선행 | 읽는 결정 |
|---|---|---|---|
| OS-0 (문서) | design: 요구 스키마·사유 코드·유도 제약의 metric/행 형식(G-S1)·출발값 규칙(G-S2)·`RunPlan` 형식·계획 함수와 실행기 서명·변형 정체 지문·S3 줄 변형 칸·결과 JSON 칸·비교 도구 위치와 칸·예산과 색인 상한 식·파일 분할·배선표·test 목록. OT §4·§5.1·§5.2·§9.4·§9.5·§10.1과 40 §2.4.5 수명 문구 개정안을 같이 낸다. 독립 검증 | 이 계획 승인, M2 결과 | XS-1~XS-7, DS-1·DS-2, DS-U1~DS-U5 |
| OS-M (측정) | N6 M2. 엔진 무변경, 읽기 전용 스크립트와 임시 spec(저장소 밖) | 이 계획(초안이어도 됨) | -- |
| OS-1 | 요구 스키마 로더(N3.2), matching 유도 제약(N3.3), 공통 판정 검사(N3.4). 요구 없는 spec 무동작 | OS-0, XRUN-F1 C | XS-1·XS-6, DS-U1~DS-U4 |
| OS-2 | 파이프라인 층 재작성: `build_run_plan`, `run_plan` 실행기, 변형별 `SearchContext`, 블록 결과 색인·`RunCounters` 실행 계획 수명, S3 변형 칸, 결과 JSON, 변형별 예산·색인 상한. 옛 진입 흐름은 같은 변경에서 지운다. trim·compare는 fail-closed 거부 상태로 둔다 | OS-1 | XS-7, DS-1·DS-2 |
| OS-3 | 읽기 전용 비교 도구(N3.8). 결과 JSON 형식은 OS-2 것 | OS-2 | XS-3 |
| OS-4 (조건부) | DS-1 (나)가 승인되면: 평가 분리(요청 합집합, 캐시 값에서 판정 행 분리, S1v 투영 축소) | OS-2, DS-1 (나) 승인 | XS-5 |
| (TR 연결) | TR card가 trim 국면 1·2 변형을 계획에 연결하고 거부를 푼다. 범위 조정은 OS-0의 OT 개정안이 정한다 | 각 TR card 선행 그대로 | XS-2·XS-4 |

**완료 조건**(기능 전체):
1. **요구가 없는 실행**에서 9회로 결과가 base와 비트 동일하다. base는 XRUN-F1 card C 병합 뒤 기준선이다. 비교에서 빼는 칸은 계수·시간 칸(40 §2.4.13 T 부류)과, 실행 경계 문구 변경으로 바뀌는 칸이 있으면 그 목록이다(design이 정하고 검증자가 소유).
2. **계획 안 결과 = 단독 결과**: 변형이 둘 이상인 계획에서 각 변형의 결과가 그 변형만 담은 계획으로 돈 결과와 비트 동일하다(T 부류 제외). 변형 순서를 바꿔도 같다.
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
| 같은 topology 변형이 평가 캐시를 공유해 다른 변형의 제약 행이 적중한다(F-1·F-2) | 변형마다 `SearchContext`·평가 캐시(DS-1 (가)). 완료 조건 2(계획 안 = 단독)가 잡는다 |
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

기본안은 원칙으로 정한 것이고 사용자가 바꿀 수 있다. N5의 XS-1~XS-7 승인도 사용자 몫이다.

| ID | 질문 | 기본안 |
|---|---|---|
| DS-1 | M1 결과(제약이 평가 키 밖, 결과는 제약 의존)에 대한 처리. (가) 변형마다 평가 캐시를 두고 블록 결과 색인만 공유(핵심 층 불변). (나) 평가를 크기·metric(계획 안 요청 합집합)과 변형별 판정으로 나눈다(kernel·graph 변경, XS-5) | (가). (나)는 M2 숫자와 함께 다시 올린다 |
| DS-2 | S1v 블록이 제약 tuple 전체를 extras로 받아(F-3) 같은 topology 변형마다 다시 계산되는 몫. (가) 받아들인다(입력 지문이 달라 판정 1 위반은 아님, 변형마다 S0 수준 한 번). (나) S1v 투영을 뷰 선언·루프 끊는 넷으로 좁힌다(graph 층 변경, XS-5와 같은 승인 대상) | (가). 완료 조건 4로 수를 낸 뒤 다시 올린다 |
| DS-U1 | matching에서 `offset_excess`(구조 가드)를 요구와 함께 둘 수 있게 할지 | 두지 않는다(N3.2 거부). 요구가 offset 판정의 유일한 출처 |
| DS-U2 | 요구와 수단 제약 공존 거부의 범위: `offset_in_sigma_mv`·`offset_sys_mv`·`offset_excess` 셋 다인가 | 셋 다(XS-1) |
| DS-U3 | k의 출처를 요구 하나로 옮기는 것(`offset_trim.coverage_multiple` 삭제) | 옮긴다(XS-6, 단일 정본) |
| DS-U4 | compare에서 1/f 판정·면적 상한이 없을 때 | 탐색 전 거부(같은 기준 없이는 나란히 놓을 수 없음) |
| DS-U5 | 기존 library spec(특히 `offset_in_sigma_mv`를 가진 spec, F-9)을 요구 형식으로 옮길지와 그 값 | 사용자 몫. 이 기능은 옮기지 않는다 |

### N10.2 오케스트레이터 기본안(원칙으로 확정, 사용자가 바꿀 수 있음)

| ID | 항목 | 기본안과 근거 |
|---|---|---|
| DO-1 | 변형별 예산 | 변형마다 E_total,v = E_B + N_T + R(X-17 정의 그대로). 근거 N3.7 |
| DO-2 | 국면 결정 방식 | 승인 기록 유무(정해진 위치). 진입 인자 분기 없음(S-2) |
| DO-3 | 변형 순서 | N3.5 표 순서 고정. 결과 무관은 완료 조건 2가 확인 |
| DO-4 | 블록 결과 색인·`RunCounters` 수명 | 실행 계획 하나(XS-7 확인 요청) |
| DO-5 | S3 줄 변형 정체 칸 | 추가(같은 `context_fp` 변형 구분, 출력 형식 변경) |
| DO-6 | TR card 전 trim·compare 요청 | 계획 함수가 fail-closed 거부 |
| DO-7 | 비교 도구 위치 | 엔진 밖 `tools/`, 엔진 import 금지. 정확한 경로는 design |
| DO-8 | M2 대리 spec 위치 | 저장소 밖 측정 agent 전용 임시 경로. library 무변경 |

### N10.3 OS-0 design에서 닫을 기술 항목

| ID | 항목 |
|---|---|
| G-S1 | matching 합성 판정의 형식: k를 입력으로 받는 새 metric인가, `offset_in_sigma_mv`·`offset_sys_mv`를 읽는 합성 제약 행인가. 분해능 규칙(기존 ss 제약 행 규칙과 정합) |
| G-S2 | matching 출발값(`iv_matching_l` L 하한)의 입력을 유도 제약으로 바꾸는 규칙 |
| G-S3 | 변형 정체 지문(topology `connectivity_fp` + 제약 집합 지문)의 정의와 S3·결과 JSON 칸 |
| G-S4 | 변형 제약 집합의 기록 형식: 유도 제약을 spec 판정 제약과 같은 형식으로 만들 때 출처 칸(`value_from_spec` 계열) |
| G-S5 | DS-2 (가)일 때 S1v 재계산 수를 결과 JSON에 내는 칸과 계수 정의(완료 조건 4) |
| G-S6 | 완료 조건 1의 비교 제외 칸 목록(검증자 소유) |
