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
| v0.1 | (이 커밋) | card OS-0 초안. 계획 v0.4(사용자 승인 S-5 XS-1~XS-14, S-6 DS-U1~DS-U9) 기준. 독립 검증 전 |

## H2. 작성 경위와 대안 비교

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
