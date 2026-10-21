---
title: offset-strategy -- design 이력
design: offset-strategy.design.md
date: 2026-10-16
---

# offset-strategy design 이력

> design 본문(`offset-strategy.design.md`)에 넣지 않는 경위·대안 비교·측정 조건을 둔다. 현행 규칙은 본문이 정본이다.

## H1. 버전 경위

| 판 | 커밋 | 내용 |
|---|---|---|
| v0.1 | aef46c7 | card OS-0 초안. 계획 v0.4(사용자 승인 S-5 XS-1~XS-14, S-6 DS-U1~DS-U9) 기준. 독립 검증 82점(차단 B-1·B-2) |
| v0.2 | 8f9b5a8 | 계획 v0.6.1(S-7~S-12, T-34~T-37, O-1) 반영. 세션 인터페이스·하네스 노출·OS-V·OS-L·판정 온도 범위 칸·F-1 fixture. 독립 검증 전 |
| v0.2.1 | 8d60a7f | v0.1 검증 비차단 N-1~N-4·N-6·N-7·N-12 반영(H4). S-13 기록 ddf1b55 |
| v0.2.2 | a2173c0 | 계획 v0.6.2·v0.2.1 검증(84점) 반영(H5) |
| v0.2.3 | ae4b84f | v0.2.2 재검증(92점, 차단 0) 비차단 N-1~N-8 반영(H6) |
| v0.2.6 | (이 커밋) | 초안. 단일 정본 감사(`_drafts/evidence/2026-10-20/single_source_cache_audit.md`) F3·F4 반영. F3: §3.1 '보고 칸' 행을 '행 값' 행으로 -- (v, L) = `graph/metrics: constraint_rows`(40 §2.4.8, writer search 제약 블록) 합성 행 값, 결과 JSON은 점 스냅샷의 그 필드를 읽음(§8·§14·OB-13 같이 고침). 계획 확인: offset-strategy 계획·gain-budget N3.3에 `EvalResult` 칸을 요구하는 문장 없음(계획 F-2·DS-1 문장은 as-built 사실). 선행 열림: `constraint_rows`는 U17 ② 이월·40 Q8 열림 -- OS-2가 ② 앞이면 병합 순서 사용자 결정. F4: E-S18·§6.1 표에서 정본 읽기 = `S3Index` 평가 키 부분, `sctx.cache` = as-built 지울 대상(U17 ②·GC-7). 계획 469행 같은 표기는 계획 소관이라 고치지 않음(다음 계획 개정 몫). O-59 (2) 파생 규칙 점검 줄(§3.1)과 계획 v0.7 O-53 A2 정합 열림 줄(§3.1) 추가 |
| v0.3.3 검증 반영 | (이 커밋) | validator(os design v0.3.3) must-fix와 gap 재분석(`_drafts/evidence/2026-10-21/os_design_v033_plan_gap.md`) 반영. (1) a8758a99의 sed 줄 치환 감사: `iv_matching_l.py:123`→`:122`는 틀린 치환이라 `:123`으로 복구(E-S10·§3.2 두 곳·§18.6, §18.6 `matching_bounds`는 `:106-107`). 나머지 치환(`find_front.py:142→:131`, `:97→:83-85`, `:81→:67`, `:83-84→:83-85`, `search_context.py:214→:206`)은 코드 줄과 대조해 맞음. 이후 줄 수정은 Edit 도구로만. (2) PS-8 재분류: 커널 행 ① 거름은 지금 경로(`ss_constraints.py:72-78` → `kernel.py:81` → `eps_sweep.py:37, :44`, search CONTRACT 107-111행)로 성립, 원인 = 사유 코드 문자열(Q8을 따름), 남는 의존은 이미 착수 조건 -- 그래서 gap의 'PS-8이 착수 조건에 없음' 항목도 사라진다. (3) `open_run.py:15-17`, `mna_types.py:370`. (4) V11: `variant_key`를 `SearchContext` 슬롯 대신 `find_front` 필수 키워드 인자로(graph 규칙 2, 승인 없는 슬롯 금지) -- 실현성: `def find_front` `:64`, 소비자 `run_id` `:131` 하나, 엔진 호출 0, test·하네스 14파일 같은 변경. (5) N14 gb 인용 = v6.24 `59ecc88e`·절/항목 id, 전제 = 계획 v0.7.3. N15 `PlanResult.perf` 출력 전용. V10 두 판정 자리가 같은 정본 A_dc·갈래 필드(gb I-H2). Status 쌓인 문장 정리(N-5) |
| v0.3.3 | a8758a99 | 계획 v0.7.3(O-70 (2), `2dab561b`)·gb v6.24(`59ecc88e`, O-68 (3)) 정합. §3.1 '정의 불가' = A_dc 갈래 fail-closed(원인 참조, 실현 경로 미확인 PS-8), '행 값' 입력 버전 대 평가 키 문장 정정. §3.7 갈래 먼저·미수렴(O-64 (2))·기록 종류 = 출력 기록, 이름은 DE-1. §12 정의 경계 불일치(O-63 (2)). §14.2·§15·§16.1 하네스 문언 = 세션 경로, OS-2 착수 조건 보강(PS-1 이름·PS-7·open_run 점검). §16.3 완료 조건 10 갈래 먼저·정의 불능·미수렴 toy(0/통과·위반 기록 → red). §18.5 `SearchContext` 입력 참조 슬롯 둘 정직 기록, `offset_start_targets` 지역 변수. §18.6 실현성 점검표 신설(사용자 규칙 2026-10-21). 줄 정정: `find_front.py:131`·`:83-85`·`:67`, `iv_matching_l.py:122`, `search_context.py:206` |
| v0.3.2 | 308e293c | 계획 v0.7.2(O-63 (3), 사용자 O-65, master `7675f71b`) 기준. `plan_version` 0.7.2. §6.4 W-1 표지 셋을 병합된 계획 규칙(S-9 126, N3.6 249, N3.12 339·341, N7.2 W-1 485, N11.1 665)으로 바꿈: 열린 세션 공개 API로 읽기, 결과 객체 색인·donors·계수 참조 0, `run_plan` 얇은 진입, OS-2 = 열기·실행·읽기·닫기, OS-L = `add_variant`. §12 PC-10을 계획 476행(O-53 B3·G-15 정렬) 인용으로, PC-10 문언 알림 닫음. §18.2·§18.4 W-1 닫힘 |
| v0.3.1 | 99eb77f6·325ddbff | v0.3.0 독립 검증(design-validator)·계획 gap(`_drafts/evidence/2026-10-21/os_design_v030_plan_gap.md`, 80.6%) 반영, 오케스트레이터 판정대로. B1: OB-37·`PlanResult.block_index`·`stage_a`·`VariantResult.search_context` 삭제, 닫으면 버림(계획 N3.12 ④), 노출 = 열린 세션 API, W-1 문언은 '계획 개정 대기'. B2: `open_run` 생성·규칙 M(M-a 허용 `plan_session.py`, M-c 세션 예외, M-d 예외는 40 개정안), M10 순환 PS-6 멈춤. B3: OB-20 정정(σ 목표 = 커널 판정 문턱 항목 / k), `start_intervals` 문턱 의존, OT §20.7 알림. B4: DEC-74 자리 = DE-1 (c), 사슬 gb 1150·1770·1576, 이름은 DE-1 design 뒤 확정, 계획 549 파일 목록. M1 코드 기준 `e1a611ec`(E-S9·12·14·15·18·21). M2 `constraint_rows` 입력 버전 투영. M3 행 형식 넓힘 알림. M4 완료 조건 10 test. M5 §18.2 정직 기록. M6 출력 기록 규칙(spec 값은 참조만). M7 front 판정 행 verified_by. M9 PC-10 계획 475 인용 + G-15 알림. 비차단: O-34 (1) 행, OS-V 'VB-1과 같은 꼴', '보류' 인용, §14.2 문언. N2: Status 이력을 H7로 |
| v0.3.0 | 5f8562e2 | 계획 v0.7.1(O-62 병합 승인, master `9bd5d7e7`) 기준 개정, 머리 `plan_version` 0.6.2 → 0.7.1. N7.1 'OS-2 착수 조건' 개정 다섯: (1) 커널 행 단일 항 k·σ_in, 분해능 규칙 하나(§3.1, OB-28 대상 소멸) (2) front 판정 자리 = DEC-74 front 전용 예외 자리의 소비자(§3.7 신설) (3) front 판정 값은 front 점 자신의 스냅샷에서 (4) 기호 \|V_sys\| → \|V_id*\|(DEC-23, O-50 G1) (5) 스냅샷 파생 규칙 남는 필드 = O-61 P1 '`ctx.base`에 있는 writer ∪ 그 평가가 부르는 블록'(gb v6.22 N3.3 422행 인용). 확인 둘: 진단 표지 = `stage_b.py:129` 보고서 칸 참조(`PlanResult.diagnostic`·결과 JSON `diagnostic` 삭제), 평가 목록 노출 = `S3Index` 참조 `PlanResult.block_index`(OB-37). 열림 'OS-2 병합 순서 대 U17 ②'를 계획 결정(O-61 P9)으로 닫음. graph 단일 정본 전수 점검(§18.5)으로 `margin_v`·`output_reference.value_v`·OS-V `offset_sys_mv` 행(VB-1 둘째 생산자) 삭제. 계획 v0.7 OS-V 범위(합성 판정 행 결속만)·OS-2 완료 조건 10·base = 실제 base master 반영. 계획 무언 PS-1~PS-5 멈춤(§18.4) |
| v0.2.5 | 2e84bc9 | 사용자 승인 기록(S-14, 2026-10-16 "모두 권고대로"): design v0.2.4 승인. DS-1 = (다)로 §10을 닫고 (가)·(나)는 기각 대안 기록으로 줄임, §6.3·§11·§18 결정 상태 갱신(OB-16·OD-2 정리). F-1 = (a): current_reuse fixture 유지, OS-2 검증은 front 불필요(§16.1·§16.2·§16.3 fixture test), 층 0 실패는 별도 엔진 조사 card. 같은 커밋에 계획 N10.1 DS-1·XS-5·XS-8 행과 계획 history 한 줄 |
| v0.2.4 | da4cff8 | v0.2.3 재확인(95점, 차단 0) 비차단 3건: N-1 OS-V 선행에 오라클 입력 생산자(U16 변환기 정본, 그 전에는 offset-trim 구동기 -- U16 뒤 옮기고 사본 삭제), N-2 §10.1 '(가)면 원인만 다르고 값이 같은 변형이 같은 입력을 다시 계산 -- OD-2 범위', N-3 §12 mV 환산 = core `MV_PER_V`. §18.2 알림 항목은 offset-trim design v0.3.3 반영됨으로 |

## H6. v0.2.3 -- v0.2.2 재검증(92점) 비차단 반영(2026-10-16)

| 지적 | 반영 |
|---|---|
| N-1 | §1.2·§5.3·§6.3의 '`start_intervals` 입력 같다' 단정을 §3.2 구분(OS-L 반복 사이 같음, compare 국면 1 다름)에 맞춤. §3.2·OB-20·§16.3의 'OT §20.7 정정 필요'는 TR-0T v0.3.1(master `cf2c983`) 반영 사실로 정리. Status v0.2.3 |
| N-2 | `constraint_set_fp`가 문턱 값(`value_v`)을 담고 `margin_ref`는 뺀다 -- 같은 `constraint_set_fp`면 문턱 값이 같다(정의상 사실). 중복 판정 키는 계획대로(원인 지문 포함, 값 지문 추가 없음). (다) 평가 키는 `constraint_set_fp`(문턱 값 지문)를 쓰고 `cause_fp`는 쓰지 않는다 -- 원인만 다르고 값이 같은 변형이 평가를 공유. 그 결과 (다)에서는 평가 키 항목을 놓지 않는다(OB-34). (가) 놓기 근거 문장도 이에 맞춤 |
| N-3 | 반복 수 = 추가된 변형 수(처음 0), a ≥ `iteration_cap`이면 거부(OB-35). TR-0T §20.6·§20.7에 같은 정의와 '세션 열기에 `iteration_cap` 전달'을 두도록 알림 항목(§18.2) |
| N-4 | `tightened_threshold` 첫 인자 = base 변형의 처음 문턱 항목(`margin_ref` None), §13.1 + TR-0T 알림 |
| N-5 | `ThresholdItem.spec_ref` 삭제(`target`이 spec 참조 하나) |
| N-6 | OS-V 착수 조건에 'OP-0 design의 V_sys 출력 키 이름 확정'. V_sys 대조 = 절댓값끼리, 선형화 차이는 `model_error_offset_sys_mv`(OB-36) |
| N-7 | `run_plan.json` `variants[].output_reference` 칸, 엔진 결과 → 오라클 입력 변환(U16 변환기)이 옮김(§8·§12) |
| N-8 | `test_plan_session`을 §6.1 규칙의 두 경우(spec None → `stage_b_unplanned`, spec 있고 단계 A 정지 → 계획 생성)로 |

## H5. v0.2.2 -- v0.2.1 검증(84점) 반영(2026-10-16, base `30e287d` = master 계획 v0.6.2·offset-trim v0.5.6 병합)

| 지적 | 반영 |
|---|---|
| B-1 정체 키 | §3.3: 중복 판정 키 = (topology, `constraint_set_fp`, `cause_fp` = Δ_T 기록 지문), 반복 번호는 표시 칸, 같은 원인 지문 재추가 거부. §6.5 `run_id`에 키(`variant_key`). §10 놓기 근거를 이 키로 다시 씀((다)는 키 지문을 평가 키에 넣어야 근거 성립) |
| B-2 문턱 자리 | §3.4 `derived` 항목 형식(`ThresholdItem` + `OffsetBound.threshold` 자리, trim 잔여는 최상위 항목). §13.1 `add_variant(base_index, threshold_item)`, 항목은 구동기가 OT §20.3 `tightened_threshold`를 한 번 불러 만든다. 커널·`ss_constraint_rows`는 합성하지 않는다. `tightened_threshold_nonpositive`는 구동기 거부. `wt/trim-design-r1` `5c93cb6` §20.3('형식은 offset-strategy `derived` 항목 형식')·§20.7(구동기 순서 11)과 대조 일치 |
| B-3 OS-V 경계 | §12: OP-5 공칭 표본 offset 출력(PC-10)과 G-15(OT §20.1) V_sys 정의 재사용, `O/core` 파일 안 만듦, 엔진은 `verified_by`·합성 행 결속만. '어댑터 무변경' 문장은 확인 근거가 없어 뺐다. measure 이름 = OP-5 출력 키(확인 대기) |
| N-1 | §3.2: `start_intervals` 입력이 같은 범위를 OS-L 반복 사이(출발 구간이 문턱을 안 읽음)로 한정, compare 국면 1은 입력이 다름 |
| N-2 | §3.2: OT §20.7 목록의 `start_intervals`는 문턱 무관 -- **OT 쪽 목록 정정 필요**로 보고 |
| N-3 | §13.4·OB-31: `iteration_cap` 채택(OS-L 필수 키워드, 사유 `iteration_cap`) |
| N-4 | §6.1 계획 생성 조건 하나(`stage_a.spec is not None`), spec 없으면 `run_stage_b`(skipped) 한 번 → `stage_b_unplanned`. §6.4 노출표에 행 |
| N-5 | §18.4 Q-1 행에 '부분 사슬 test가 `S3Index`·`RunCounters`를 직접 만든다(세션 열기 일부의 두 번째 구현, test 쪽)' 사실 |
| N-6 | §1.1에 T-29~T-33 행 |
| N-7 | §12: `model_error_offset_sys_mv` 이름은 규칙(`verified_by.py:22, :59`)으로 확인, 값을 만드는 주체·경로는 확인 대기 |
| N-8 | §3.4·§13.3: 단위 = V(`target` 키 접미 `_v`, Δ_T 기록 `temp_margin_<metric>_v`), 위반 `threshold_unit` |
| N-9 | §16.2: `offset_in_max_v` record에 유도식과 두 출처 |

## H4. v0.2.1 -- v0.1 검증(82점) 비차단 원문 반영(2026-10-16, 오케스트레이터 전달)

| 지적 | 내용 | 반영 |
|---|---|---|
| N-1 | E-S12 '값 있는 offset 판정 제약 전체'는 부정확 -- mismatch 필수 검사 대상은 `_OFFSET_METRICS`(`offset_in_sigma_mv`, `offset_excess`)뿐(`search_context.py:153`) | E-S12 정정, §5.3 mismatch 행의 근거를 σ 항으로 |
| N-2 | 합성 행 분해능: '항마다 기존 규칙'과 '합 s = 0일 때만 사유'가 어긋남 | 항마다 판정, 한 항이라도 0(모델 오차 없음)·None이면 미측정(OB-28), test 추가 |
| N-3 | `ss_constraint_rows`가 `if not declared: return (), ()`로 일찍 끝나 사용자 ss 제약 없는 spec에서 합성 행이 빠짐 | §3.1 '일찍 끝나는 분기' 행, §14.2 범위, test 추가 |
| N-4 | S3 `variant` 칸 조건(유도 제약 있으면)과 구현 card(OS-5)가 어긋남 | OS-5 구현으로 하나로: 변형 둘 이상 또는 반복 번호 1 이상일 때만(OB-29) |
| N-6 | L2 순서와 meta 불일치 때 L3 | L2는 v0.2부터 참조 해석 뒤(확인). meta 불일치(`topo` = None)면 포트 뷰 유도·L3 판정 안 함, 로드는 meta 위반으로 거부(§4.2), test 추가 |
| N-7 | 단계 B 메모 사전은 색인과 나란한 두 번째 재사용 경로이고 OS-2에서 안 쓰임 | 뺐다. 재사용은 블록 결과 색인 하나(OB-30) |
| N-12 | §10 'S1v 투영 좁히기는 필요 없다' 단정 | '이 design의 전제(OB-4·L2)에서는'으로 한정하고 PD-3 근거와 같음을 적음 |

* 사용자 결정 S-13(2026-10-16 "모두 권고대로"): Q-1 = 부분 사슬·단계 B 없는 test는 W-1 대체 범위 밖. §18.4 Q-1을 '결정됨'으로 고쳤다(본문 규칙 변화 없음).
* 같은 판에서 §18.2의 D-25 문구를 master `2c3e740` 계획 정리(결정됨 T-36)에 맞췄다.

## H3. v0.2 개정 경위(2026-10-16, worktree `wt/ostrat-design-r2`, base `b3be138` = master `194981f` + v0.1)

### 계획 결정으로 바뀐 v0.1 문장

| v0.1 | v0.2 | 근거 |
|---|---|---|
| §4.2 L2 '`human.constraints` 항목 전부, 출처 kind 무관 거부'(OB-6) | 판정 제약(`judged` 참)만 거부, `pending_spice`·`pending_constraints` 허용, 검사 자리 = 참조 해석 뒤 | PD-9 (가), S-10 |
| §4.1 '`SECTION_GROUPS`에 `requirement_fp`를 더한다'(늘) | 요구 섹션이 있을 때만 묶음에 넣는다(`OPTIONAL_SECTION_GROUPS`). §3.6 비교 제외에서 spec 지문을 뺐다 | PD-5, S-8 (v0.1 검증 B-2) |
| §6 `run_plan` 하나 | 세션(`open_plan_session`·`PlanSession`) + 얇은 진입 `run_plan`, 진단 모드 전달, 하네스 노출표 | W-1 (i) S-9, 계획 N3.6·N3.12 XS-17, v0.1 검증 B-1 |
| §16.4 W-1·F-1 열린 결정 | 승인 반영: §6.4·§16.2 | S-9, S-11 |
| §10.4 DS-2 열림·PD-3 확인 요청 | 닫힘('대상 없음'), §3.5 칸은 사실 확인용 | PD-3, S-8 |
| §16.2 PD-1~PD-4 | 승인되어 본문 규칙으로(§5.3, §11, §14.2) | S-8 |
| OB-8·OB-10·OB-12·OB-18 | 기본안 목록에서 뺐다(PD-1·PD-8·PD-7·PD-2로 승인) | S-8 |
| (없음) | §4.1 `judgment_temperature_range_c` 칸 | T-34, 계획 N3.2 |
| (없음) | §12 OS-V, §13 OS-L, §7.3 `grow` | V-1 S-11, T-35, S-12 |
| §7.3 '`S3Index` 생성자가 B_S0를 받는다' | 필수 인자 `s0_sets`·`add_eval_ceiling`, card C test 같은 변경 | PD-7 |

### 새로 정한 것의 경위

* **출발값과 Δ_T(OB-20)**: OS-L에서 Δ_T가 `OffsetBound` 안에 들어오면 `start_intervals`가 `OffsetBound` 전체를 extras로 받을 경우 반복마다 입력이 바뀐다. offset-trim 계획 NFR-T3('문턱 합성은 제약 행 한 곳')과 원래 취지(S0 재사용)를 함께 지키려고 출발값은 요구 값(k, limit_v)만 extras로 받게 했다. 그 결과 matching 쪽 S0 수준 문턱 의존 블록은 없다. 이 사실은 offset-trim G-12 목록의 입력이다.
* **D-25 닫힘**: 계획 v0.6.1 본문은 D-25를 대기로 적었지만 사용자 결정 T-36(2026-10-16)으로 (c)+(c-2)가 정해졌다. 계획이 'D-25 결정 뒤 design이 서명을 닫는다'고 했으므로 §13.1이 서명을 닫았다. 계획과 다른 결정은 아니다.
* **하네스 전수 읽기(B-1)**: `nfr4_run_dump.py:286-445`를 읽어 E-S18 목록을 만들었다. 수작업 사슬 test는 grep으로 분류했다(E-S19). 부분 사슬 test를 대체 범위에서 뺀 해석(OB-22)은 계획 문언(전체 사슬 다섯 단계)을 따른 것이고, 넣으려면 세션 공개 동작을 더해야 해서 계획 개정이 필요하다(Q-1).
* **판정 온도 범위 칸 선택성(OB-21)**: 계획 N3.2는 필수 여부를 정하지 않았다. OS-2에는 소비자가 없고(소비자 = TR-7·보정 루프·OS-V 범위 몫은 TR-TL) F-1 승인 값에도 이 칸이 없어서 선택 칸으로 두고, 필요한 소비자가 없으면 거부하게 했다.
* **v0.1 검증 비차단 지적**: 계획 history(v0.5 경위)에 따르면 B-1 → W-1, B-2 → PD-5, N-5 → PD-9, N-8 → PD-7, N-9 → T-30 연결, N-10 → PD-6, N-11 → PD-8로 처리됐다. N-1~N-4·N-6·N-7·N-12의 원문은 이 작업에서 찾지 못했다(`wt/_drafts`·계획 history 검색). design §18.4 Q-2.
* **oracle-portability 경계**: OPP N0.1·N3.1(코어 = `O/core/`, 방언·PDK 이름 없음)과 O-1(네이티브 MC, 크기 확인은 TR-7)을 읽고 OS-V를 '코어 측정 정의 + 엔진 검증 출처 표'로 한정했다. 판정 온도 범위로 넓히는 몫은 OTP TR-TL 행의 소유 경계대로 TR-TL이다.

## H2. 작성 경위와 대안 비교(v0.1)

### 인용 기준 다시 재기(2026-10-16, master `d783efe`)

계획은 `067614c` 기준으로 인용했다. 그 뒤 NFR-4 card 2가 병합되어(6be811b) 다음 줄이 달라졌다. design은 `d783efe`로 다시 쟀다.

| 계획 인용(`067614c`) | `d783efe` |
|---|---|
| `E/pipeline/stage_a.py:152-160`(`_declared_loop_cuts`) | `:156-165` |
| `E/pipeline/stage_a.py:225-227`(`build_s1v` 호출) | `:230-232` |
| `E/pipeline/stage_a.py:195`(`run_stage_a` 서명) | `:199` |
| `E/search/find_front.py:75-78`(정지 시각) | `:77-81` |
| `E/search/find_front.py:94`(검증 출처) | `:97` |
| `E/search/find_front.py:127-133`(`perf`) | `:131-140` |
| `E/search/find_front.py:138`(`run_id`) | `:142` |

그 밖 F-1~F-13 인용(`search_context.py`, `kernel.py`, `eval_key.py`, `iv_context.py:89`, `iv_matching_l.py:40-41, :107-108`, `start_intervals.py:295, :332`, `spec_model.py:280-302`, `registry.py:49-58`)은 같은 줄이다.

### G-S1 대안 비교(본문 §3.1 결론의 경위)

* (i) k를 입력으로 받는 새 metric: `metrics_aux` extras에 k(spec 값)가 들어가 metric 블록 입력이 판정 값에 의존한다. 레지스트리의 'metric = 계산된 묶음의 필드 하나' 규칙(`E/metrics/registry.py:5-6`)에도 맞지 않는다. 기각.
* (ii) 합성 제약 행: 두 metric 요청 결과를 읽기만 한다. 채택(OB-1). 처음에는 새 파일(`search/offset_bound_rows.py`)을 검토했으나 계획 N9·XS-10의 승인 범위('ss_constraint_rows 한 곳')에 맞춰 기존 함수의 인자 `bounds`로 넣었다.
* 한계를 σ 몫과 V_sys 몫으로 나눠 기존 두 제약으로 쓰는 안: 비율 발명(계획 N3.10에서 이미 기각).

### 변형 제약 주입 방식(PD-1 경위)

* 계획 N3.10은 변형마다 spec 사본(`SizingSpecDoc.from_sections`, 지문 재계산)을 기본으로 두었다.
* 조사 결과: 요구가 있으면 사용자 offset 제약은 로더가 거부하므로(L2) 변형 사이에 사용자 `constraints`는 같다. 바뀌는 것은 합성 행(`ConstraintDecl` 형식에 담을 수 없음)과 국면 2 `trim_decl`뿐이다.
* spec을 extras로 받는 블록: `achievability`(`E/pipeline/stage_b.py:168`), `start_intervals`(`E/search/search_context.py:195`). S1v는 spec 전체가 아니라 판정 제약 tuple을 받는다(`E/graph/s1v_build.py:39-42`). 사본 방식에서는 `achievability`가 유도 제약을 읽지 않는데도 변형마다 다시 계산된다.
* 그래서 별도 입력 `derived`를 오케스트레이터 기본안으로 하고, 계획 문언 방식은 대안으로 본문 §5.3에 남겼다.

### view 출처(G-S1 (d)) 경위

* 후보 셋(계획 N10.3): 입력 셀 전달 뷰(`metric_structure`), 기본 뷰, 사용자 선언.
* library offset 제약은 view를 적지 않아 기본 포트 뷰를 쓴다(`current_reuse_telescopic_ota.sizing_spec.json:226-234`, `two_stage_ota.sizing_spec.json:81-89`). 같은 규칙을 쓰면 요구 형식으로 옮긴 spec이 같은 뷰에서 재진다.
* `metric_structure`는 S1v 유도 결과라 로더 시점에 없다. 사용자 선언 view는 요구가 '수단'을 담지 않는다는 S-1 취지와 어긋난다.
* σ_in·V_sys 계산은 S1v 씨앗을 쓰지 않는다(`E/metrics/offset_analysis.py:56-57`, `offset_systematic.py:31-33`). 그래서 유도 제약을 S1v 씨앗에서 빼도 계산이 성립하고, 같은 topology 변형의 S1v 입력이 같아진다(PD-3).

### DS-U9 조사 경위

* 40 §2.4.13 1차 검사 전제 (가)는 'E_B 선언'이다. 시간 유도 E_B는 같은 변형을 단독으로 두 번 돌려도 같지 않을 수 있다(평가 시간 측정). 그래서 다변형 규칙의 후보 넷(본문 §7.2 표)이 모두 조건 2를 줄 수 없다.
* 결론: 열림 유지, S-6대로 제외 + 표기(OD-1).

### N-22 배정 경위

* OT §14.1은 `load_trim_approval`을 TR-1, `bind_trim`을 TR-3에 두었다. 국면 규칙이 실행 계획으로 옮겨 오면서, TR-1 시점에는 승인 기록을 읽는 호출자가 없다(국면 2 경로가 없음). '만들면 배선'에 맞춰 로더를 결속 검사와 같은 TR-3으로 옮겼다(PD-2).
* TR-3 시점에는 국면 2 변형의 단계 B·탐색 경로(off 소자 처리 TR-5a, trim 값 TR-5b)가 없다. 그래서 단계 A 뒤 fail-closed 게이트를 두고 TR-5b에서 지운다(OD-3).

### 제품 진입점(W-1) 확인

* 2026-10-16 grep: `run_stage_a`·`find_front`를 부르는 엔진 비test 파일은 정의·재수출·docstring뿐이다. 사슬은 `E/tests/integration/nfr4_run_dump.py:376-401` 같은 하네스가 만든다. `run_gmid_design_pipeline`은 `E/pipeline/__init__.py:1` 자리 문구뿐이다(U16).

## H7. 본문 Status 문단 이력(v0.3.1에서 본문에서 옮김, 검증 N2)

* v0.3.0 (2026-10-21): 승인된 계획 v0.7.1(사용자 O-62 병합 승인, master `9bd5d7e7`) N7.1 'OS-2 착수 조건'의 design 개정 다섯 항목과 확인 두 항목을 반영했다: matching 판정을 커널 행(단일 항 k·σ_in, §3.1)과 front 판정(gain-budget DEC-74 front 전용 예외 자리의 소비자, §3.7)으로 나누고, 기호를 \|V_id*\|(gain-budget DEC-23, O-50 G1)로 바꾸고, 스냅샷 파생 규칙 인용을 O-61 P1로 바꾸고, 단계 B 진단 표지를 `stage_b.py:129` 보고서 칸 참조로, 평가 결과 노출을 `S3Index` 참조로 했다(§6.4). OS-2 병합 순서 열림 항목은 계획 결정(O-61 P9)으로 닫았다. 계획이 정하지 않은 항목은 §18.4 '계획 무언'에 멈춤으로 올렸다.
* v0.2.6 (2026-10-20): 단일 정본 감사(`_drafts/evidence/2026-10-20/single_source_cache_audit.md`) F3·F4를 반영했다.
* v0.2.3 (2026-10-16): v0.2.2 재검증(92점, 차단 0) 비차단 N-1~N-8을 반영했다(H6).
* v0.2 (2026-10-16): v0.1(`aef46c7`)이 계획과 다르게 간 점은 계획 v0.5~v0.6.1이 PD-1~PD-9·W-1·F-1·V-1로 받아 사용자 승인을 받았고(S-8~S-11), 이 판은 그 승인 문언과 v0.1 독립 검증(82점)의 차단 B-1·B-2를 반영한다. 계획에 없는 결정은 오케스트레이터 기본안(§18.1)으로 표시했고, 계획과 다른 결정은 두지 않았다(S-7).
* v0.2.x 기준 문장: 코드 인용은 master `194981f`(worktree `wt/ostrat-design-r2`). 엔진 코드는 `d783efe` 이후 바뀌지 않았다. 전제 문장: 이 기준에는 card A·B·C가 없다(`s3_index.py`·`search_ceiling.py`·`search_stop.py` 없음).
