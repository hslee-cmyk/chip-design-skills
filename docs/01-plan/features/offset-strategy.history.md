---
title: offset-strategy -- 계획 이력
plan: offset-strategy.plan.md
date: 2026-10-16
---

# offset-strategy 계획 이력

> 계획서(`offset-strategy.plan.md`)에 넣지 않는 **경위·결정 원문·측정 조건·버전 이력**을 둔다. 현행 규칙·정의·게이트·완료조건은 계획서가 정본이다.

## H1. 결정 경위

### 2026-10-16 사용자 결정 S-1~S-4

- 원문: `wt/_drafts/user_decisions.md` '## offset 방식 선택·실행 계획 (2026-10-16 사용자 "권고대로 해")'. 원문 그대로:
  - S-1: spec은 수단이 아니라 요구로 쓴다 -- offset_requirement{offset_in_max_v, coverage_multiple k, strategy: matching|trim|compare}. 방식별 판정 제약은 엔진이 요구에서 유도(matching: k·σ_in+|V_sys| <= offset_in_max_v, trim: trim_range·trim_residual, V_res <= offset_in_max_v 로더 검사). 1/f 판정(noise_fc_in_hz 또는 noise_out_int_vrms)과 총면적 area_search_m2 하나를 두 방식 공통. 승인된 D-4 공존 거부를 이 유도로 대체하는 것, N을 {N, N+1}로 여는 것, compare 추가는 '원래 취지와 다름'으로 보고됨 -- 새 기능 계획·design에서 다시 승인받는다.
  - S-2: 아키텍처 = (2) 파이프라인 층 모듈 재작성('실행 계획' = 변형 목록 (topology 변형, 제약 집합), 단계 A·S0·블록 결과 색인 공유, 옛 trim_approval_path 인자 분기 삭제). 핵심(graph·블록·kernel·search) 유지. 엔진 전체 재작성 안 함.
  - S-3: compare는 두 국면(승인 게이트 유지). 국면 2 최종 비교: 사용자에게 권고 없이 두 안을 냈던 항목이라 오케스트레이터 기본안 = 엔진은 이전 실행 결과를 입력으로 받지 않는다. 두 결과 JSON을 읽는 읽기 전용 비교 도구(보고만)로 나란히 놓는다 -- 계산 재사용·엔진 입력 경로 없음. 사용자가 달리 원하면 바꾼다.
  - S-4: 순서 = NFR-4 card 2 병합 -> XRUN-F1 A -> B -> C -> 실행 계획 구현 -> trim TR-1. card A 진행 중 계획 문서와 실측(평가 캐시 키의 제약 의존, matching·trim 1단계 θ 겹침 1회로)을 한다. offset-trim design §4(진입 인자 단계 선택) 개정은 실행 계획 design과 함께 재승인.
- 함께 근거로 쓴 사용자 취지(2026-10-15, 원문 '실행 사이 재사용 제거'): "계산 재사용은 처음 topology를 실행할 때는 항상 계산하고 그 계산된 값이 나머지 최적화를 진행할 때 재사용되게 한다는 것이 원래 취지였어".
- 이어받은 결정: offset trim T-1~T-28(특히 T-2 승인 게이트, T-7·T-8 I_u θ안과 예산 무변경, T-15 TR-2 병합 시점, T-19~T-23 출력 기준 DC, T-24~T-28 시험 회로), XRUN-F1 X-1~X-19(특히 X-12 색인 수명, X-17 E_total 정의), U-89(S3 실행 사이 재사용 제거), 원래 취지와 다른 판단 보고 규칙(2026-10-15).

### 계획 초안 작성 방침(v0.1)

- 결정 원문이 '다시 승인'으로 지정한 네 항목(D-4 대체, {N, N+1}, compare, OT §4 개정)은 계획서 N5에 XS-1~XS-4로 두고, 승인 전 기본안으로 삼지 않았다(2026-10-15 보고 규칙).
- 초안을 쓰며 새로 드러난 '승인된 문서와 다른' 항목 셋(XS-5 핵심 층 변경 가능성, XS-6 k 출처 이동, XS-7 색인 수명 문구)을 같은 절에 더했다.
- 변형별 예산: v0.1은 오케스트레이터 작성 지시(이 계획서 초안 브리핑의 '변형별 예산은 기본안으로')를 따라 기본안 DO-1로 두었다. S-1~S-4 원문에는 변형별 예산에 대한 문장이 없다. v0.2 검증 N-5 지적대로 이것은 40 §2.4.9 E_total 정의의 단위를 바꾸므로 v0.3에서 확인 요청 항목 XS-12로 옮겼다. 근거로 든 X-17 원문('선언 40은 그대로 동작, 판정·test 예산 변경 없음')은 제안 이유로만 남겼다.

### 2026-10-16 v0.1 독립 검증(72/100, 차단 6, 비차단 13) 반영 → v0.2

오케스트레이터 지시(차단 처리 방식 지정)대로 고쳤다.

| 지적 | v0.1 | v0.2 반영 |
|---|---|---|
| B-1 | DS-1·DS-2 기본안 = (가) | 기본안 삭제. (가)는 같은 실행 안 변형 사이 재계산을 받아들이는 편차(XS-8), (나)는 핵심 층 변경 편차(XS-5)로 N5에 올림. 결정은 M2 숫자와 함께 |
| B-2 | DS-1 선택지 둘, 완료 조건 3과의 관계 없음 | (다) 키 분리 추가. N3.1에 선택지별 완료 조건 3 표: (가)는 같은 평가 키가 변형마다 계산돼 모순(같은 topology 변형은 `context_fp`가 같음), (나)·(다)는 지킴. 조건 3은 그대로이고, '변형 안 0 + 변형 사이 보고'로 바꾸는 것은 기준 약화 DS-U7(사용자 승인)로만 표시 |
| B-3 | 변형 제약 주입·G-S1·G-S2의 층을 따지지 않음 | N3.10 층 분류표와 F-12(`search_context.py:110-113`, `iv_context.py:89`, `iv_matching_l.py:40-41, :107-108`, `spec_model.py:280-281, :287-290`). 주입은 pipeline + authoring(지문 재계산), G-S1·G-S2는 핵심 층 확장 → XS-10 |
| B-4 | `offset_trim`만 있고 요구가 없는 spec의 처리 없음 | N3.2 로더 거부 행 추가. T-27(`offset_excess` 유지)·T-28 시험 회로 spec 영향 XS-9(재승인), 값 DS-U8 |
| B-5 | M2에 base에 없는 칸(평가별 시간, 블록별 수) | F-13(S3 evals 칸·`perf` 합계)로 base 칸만 남김: `context_fp`, θ 키 집합, `seq`, `perf` 합계. 시간·블록별 수·색인 교집합은 card B 뒤 2차 측정. 측정 base = card A 병합 뒤 master 한 커밋 고정(N-11) |
| B-6 | OS-2가 다변형 경로 전부를 TR-1 앞에 구현 | 권고안: TR-1 앞에는 단일 변형 실행 계획(matching)과 단계 선택 흐름 대체만(OS-1·OS-2). 다변형 공유·변형 정체 칸·Σ 상한은 trim·compare를 처음 여는 TR card에 묶음(OS-5). S-4 문구를 나누는 것이라 XS-11, 대안 (ii)(fixture로만 실행 승인) 병기. 옛 OS-4는 OS-5에 합침. 완료 조건별 적용 card 표기 |
| 비차단 | -- | 지시 문구에 내용이 있던 것만 반영: N-8(N+1의 m 규칙 → DS-U6), N-9(DS-U4에 '있음'의 정의), N-11(M2 base 고정). N-1~N-7·N-10·N-12·N-13은 지적 원문을 받지 못해 이 판에서는 반영하지 못했다(N-5·N-13은 확인 요청 항목으로 다루라는 지시만 받음) |

### 2026-10-16 v0.1 검증 비차단 N-1~N-13 반영 → v0.3

v0.2 때 받지 못한 비차단 지적 원문을 받아 반영했다(N-8·N-9·N-11은 v0.2에서 반영).

| 지적 | v0.3 반영 |
|---|---|
| N-1 | F-3 근거에 `stage_a.py:225-227`(spec 객체를 넘기는 `build_s1v` 호출)을 더하고, `:152-160`은 `_declared_loop_cuts`, tuple 생성은 `s1v_build.py:39`로 구분 |
| N-2 | F-4에 `stage_b.py:168` `achievability(graph, spec, …)`, `search_context.py:195` `start_intervals(base, spec, …)`, `:110-113` 추가 |
| N-3 | F-3a 신설(`views.py:51-63, :77-78`, `registry.py:56-58`): 뷰는 제약의 view 선언에서 만들어지므로 제약 집합이 다르면 S1v 값도 다를 수 있다. N3.1-3의 '같은 값을 다시 계산' 단정을 고치고, 유도 제약의 view 출처를 G-S1에 넣음 |
| N-4 | G-S1·N3.3에 단위 환산(mV 대 V)을 단위 어휘에서 읽는 규칙으로 |
| N-5 | 변형별 E_total을 기본안(DO-1)에서 확인 요청 XS-12로. H1의 '결정 지시대로' 문장 정정 |
| N-6 | 완료 조건 2를 선언 E_B 실행으로 한정하고, 유도 실행 규칙은 DS-U9 |
| N-7 | F-5에 card B 뒤 구조(`S3Index` 한 객체의 평가 키 부분과 블록 결과 부분)를 적고 DS-1 표를 그 구조로 다시 씀. (가)도 card B 뒤에는 search 변경(XS-5에 포함) |
| N-10 | N3.5: 낡은 승인은 국면 1로 돌아가지 않고 OT §8.3대로 정지, 국면 1 재실행은 사용자가 승인 파일을 치우는 방법(DO-9) |
| N-12 | OS-3 = TR-6 뒤, OS-5 = TR-1 뒤(TR-2와 함께), OS-0·OS-M·OS-1·OS-2 = TR-1 앞 명시 |
| N-13 | S3 줄 변형 칸을 기본안(DO-5)에서 확인 요청 XS-13으로(X-10 선례) |

## H2. 측정 근거

### M1 (2026-10-16, 읽기 확인, base `067614c`, worktree `wt/ostrat-plan`)

- 방법: 엔진 코드를 읽기만 했다(실행 없음). 읽은 곳:
  - 키: `E/search/eval_key.py:13-22`(`EvalKey` 구성), `E/search/search_context.py:45-46`(`_CONTEXT_WRITERS` = S1 블록 ∪ `PLAN_WRITERS`), `:211`(`context_fp` = 블록 입력 버전·LUT 손잡이·`DcInputs`), `E/sizing/kernel_context.py:47-48`(`PLAN_WRITERS` 일곱), `E/sizing/s2_values.py:187-200`(`DcInputs` 칸, 제약 없음).
  - 제약이 키 밖 블록에만 있음: `E/search/search_context.py:188`(`constraint_classes` 블록, `_CONTEXT_WRITERS`에 없음), `E/search/constraint_classes.py:23-43`.
  - 결과의 제약 의존: `E/search/kernel.py:49-56`(`_spec_rows`), `:130-133`(`ss_evaluate`에 `sctx.ss_constraints`), `:146-151`(평가 안 제약 행), `:159-161`(행을 담은 `EvalResult` 캐시 저장), `E/metrics/ss_evaluate.py:50-57, :90-93`(요청 목록), `E/metrics/ss_metrics.py:377-379`·`E/metrics/metrics_aux.py:157-159`(요청 목록이 블록 extras).
  - S1v의 제약 의존: `E/graph/s1v_build.py:39-42`, `E/graph/s1v_fields.py:249-251`, `E/pipeline/stage_a.py:152-160`.
- 결론: 제약 집합은 평가 캐시 키(`context_fp` 포함)에 들어가지 않는다. 평가 결과(제약 행·계산하는 metric)는 제약 집합에 의존한다. 그래서 같은 topology 변형이 한 평가 캐시를 공유하면 틀린 결과가 적중한다(계획서 N3.1).
- 부수 확인: XRUN-F1 card A·B·C 산출 파일(`search/s3_index.py`·`search_ceiling.py`·`search_stop.py`)이 base에 없다(`ls`), 엔진 코드에 'trim' 없음(grep), library에서 `offset_in_sigma_mv` 판정 제약은 `current_reuse_telescopic_ota.sizing_spec.json:226` 하나(grep).

### v0.2 추가 읽기(2026-10-16, base `067614c`)

- 변형 제약 주입 경로: `E/search/search_context.py:110-113`, `E/search/iv_context.py:89`, `E/search/iv_matching_l.py:40-41, :107-108`, `E/search/start_intervals.py:295, :332`, `E/authoring/spec_model.py:280-281, :287-290`.
- 측정 칸: `E/search/kernel.py:68-88`(S3 evals 줄 칸, 시간 없음), `E/search/archive.py:42-43`(폴더 = `context_fp`), `E/search/find_front.py:127-133`(`perf` 합계).

### M2

- 이번 초안에서는 재지 않았다(메모리 제약, 오케스트레이터 지시). 방법은 계획서 N6 M2.

## Version History

| 버전 | 날짜 | 변경 |
|---|---|---|
| 0.3 | 2026-10-16 | 비차단 N-1~N-7·N-10·N-12·N-13 반영: F-3·F-4·F-5 근거 보강, F-3a 신설, DS-1 표를 card B 뒤 구조로, XS-12·XS-13(확인 요청), DS-U9, DO-9, 완료 조건 2 범위, G-S1 단위·view 출처, card 시점. 재검증·사용자 승인 전 |
| 0.2 | 2026-10-16 | 독립 검증 72점 차단 B-1~B-6 반영: DS-1·DS-2 기본안 삭제, DS-1 (다) 추가와 완료 조건 3 표, 층 분류표 N3.10, F-12·F-13, `offset_trim` 단독 거부, XS-8~XS-11, DS-U6~DS-U8, M2 측정 칸 축소·base 고정, card 재구성(OS-5). 비차단은 N-8·N-9·N-11만 반영. 재검증·사용자 승인 전 |
| 0.1 | 2026-10-16 | 초안: 계획서·history 신설. 사용자 결정 S-1~S-4 반영, M1 실측(읽기) 결과, M2 방법, XS-1~XS-7, DS-1·DS-2·DS-U1~DS-U5, DO-1~DO-8, card OS-0·OS-M·OS-1~OS-4. 독립 검증·사용자 승인 전 |
