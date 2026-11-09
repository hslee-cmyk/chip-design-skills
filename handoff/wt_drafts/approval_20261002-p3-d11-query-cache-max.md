---
id: 20261002-p3-d11-query-cache-max
date: 2026-10-02
target_kind: diff
target: <D-11 문서 커밋 뒤 계산 -- 00-common §8.2 식. 그 커밋의 부모 계획서 blob이 gate master 4a286f0 판 f2f4d2ee2318ec7f6e1dc607a355d3178bf8a995이면 441b80e153a5a9e9174986ab069a50088e687448fbac3167ce864ccf16799a99>
diff_base: <D-11 문서 커밋의 부모 -- rev-parse>
diff_head: <D-11 문서 커밋 -- rev-parse>
diff_path: docs/01-plan/features/gain-budget-gmid-sizing.plan.md
scope: Phase 3 계획 N3.10 MOD1 행 '대표 대상' 칸에 `_QUERY_CACHE_MAX` 토큰 하나 추가(design 30 D-11 -- UD-0 범위 밖 N3.10 개정, [D-11] 답 (가)). 조건: D0b 착수 전 D0b base에서 `move_plan plan`(design 30 §6.3 `MP_ARGS`, D0a 계약 2 바인딩 이름 키)의 `conflicts`·`upward`(원천 무관)·`cycles`·`unassigned`·`import_time_high`·`import_conflicts`가 모두 빈 목록이고 MOD7 파일 밖 MOD7 배정이 0일 때만 이 승인으로 진행(`reg_mismatch`는 제외), 하나라도 비지 않으면 멈추고 다시 묻는다
---

## 사용자 원문

> (가) 계획 표 MOD1에 추가 (Recommended)

(AskUserQuestion 한 번에 올린 두 질문 중 첫째 [D-11]의 답이다. 질문 2026-10-02 13:35 KST(`2026-10-02T04:35:31.525Z`), 답 2026-10-02 13:38 KST(`2026-10-02T04:38:47.216Z`) -- 세션 기록
`63c6146a-ab1d-4035-a169-bae810986922.jsonl`의 tool_use `toolu_01GVLKut4JY6FMvvZJEvhKS4`(uuid `07519f8c-23e0-462e-b199-d6d50664eed9`, headers `[D-11] 표 1건`·`[W-1] shim`)와 그 tool_result(uuid `8b8cfd7b-1483-447d-8c72-fa1cc0623ef3`)에서
바이트 대조해 옮겼다(아래 따옴표 안은 jsonl 문자열 그대로 -- 고치지 않았다). 둘째 답 [W-1] "(가) T0에서 test import 수정 (Recommended)"는 T0의 V5 승인 기록 `20260930-p3-tests-location-free`가 인용한다(이 기록은 덮지 않는다).)

* 질문 [D-11] 원문: "[D-11] 이동 도구를 승인된 규칙대로 돌리면 LUT 조회 캐시 상한 상수 `_QUERY_CACHE_MAX`(사용처는 MOD1 `SemiEmpiricalGmIdLUT._query` 하나)가 레지스트리 277행 목적지 때문에 MOD4로 가서 MOD1→MOD4 역방향 import와 순환이 생깁니다(승인 범위 밖 표 개정). 어떻게 할까요?"
  선택지: "(가) 계획 표 MOD1에 추가 (Recommended)" -- "N3.10 MOD1 대표 대상에 `_QUERY_CACHE_MAX` 한 토큰을 더합니다(`_multilinear_interp_point_multi`·`_kv_table` 선례). 역방향·순환 0, MOD1은 8단위 그대로이고 D0b가 다른 개정을 더 계산하면 그때 다시 묻습니다." /
  "(나) 레지스트리 277행 이름 칸 수정" -- "그 행 함수 칸을 `SemiEmpiricalGmIdLUT.__init__`로 바꿔 상수가 사용처를 따라가게 합니다(계획 표 불변, 결과 같음). 감사 원자료는 그 행이 상수와 `__init__`을 함께 다룬다고 적고 있어 오기 정정이 아니라 배정 변경이며, D0b 전에 레지스트리 수정 card가 하나 더 필요합니다."
  답: "(가) 계획 표 MOD1에 추가 (Recommended)".
* 같은 호출의 둘째 질문 [W-1] 원문(참고 -- 이 기록 범위 밖): "[W-1] M4·M8·M9에서 topology_library·sizing_recipe·design_report가 재수출만 남은 shim이 되면, 단위 selftest 3개가 이 파일들을 거쳐 import하던 비엔진 이름 7개(math·json·np·os·_dc_replace·nmcnr_predict_ac_response)가 사라져 test 수집이 실패합니다. 어떻게 할까요?"
  답: "(가) T0에서 test import 수정 (Recommended)". (질문의 '이름 7개'는 파일별로 센 수다 -- `math`가 TL·SR 두 파일에 있어 서로 다른 이름은 6개. 원문을 고치지 않는다.)

## 사용자에게 보인 것

이 기록이 덮는 범위의 근거는 사용자가 실제로 본 아래뿐이다(세션 기록 `63c6146a-…jsonl`에서 확인, 사이드체인 제외 assistant 텍스트).

1. 위 AskUserQuestion의 [D-11] 문안과 두 선택지(라벨·설명). 미리보기 없음.
2. 질문 바로 앞 오케스트레이터 메시지(`2026-10-02T04:34:39.310Z`, uuid `845a9ec0-ac3f-42e2-94d1-c93f059c7eda`), 원문(펜스 안 = jsonl text 블록 그대로):

```text
Card 35 (V3 scope) step 0 has been pushed and its test-author is running. I'm keeping parallel work at six or more and preparing two Phase 3 follow-up questions for you.
```

3. 그 앞의 관련 보고 두 건(요약 -- 원문은 jsonl. 큰따옴표 안은 jsonl text 블록 바이트 그대로, 굵게 표시 `**` 포함):
   * `2026-10-02T04:03:33.161Z`(uuid `ce687938-a12d-47a9-817a-ee6cc87b58ea`) -- M1 모의 결과와 "**(M1-2) 상수 `_QUERY_CACHE_MAX`의 배정**: 규칙대로 배정하면 MOD4로 가면서 MOD1과 순환이 생깁니다. 막으려면 계획서 MOD1 행에 이 이름을 더하는 개정이 필요합니다."
   * `2026-10-02T04:20:54.703Z`(uuid `cd90c928-e2c9-4ef7-85cd-0a74cf0923ba`) -- D0a 독립 검토 결과: 계약 키(바인딩 이름)로 재면 `_QUERY_CACHE_MAX` 때문에 상향 의존 1건·순환 1건, 해소안 ①(N3.10 MOD1 토큰, D-11 승인)과 ②(레지스트리 277행 이름표 정정).
     그 메시지는 "원칙상 ②를 기본안으로 삼습니다. 다만 277행이 정말 이름표 오류인지 먼저 확인합니다. 오류가 아니면 ①을 Phase 3 후속 질문 묶음에 넣어 여쭙겠습니다"라고 적었다 --
     그 뒤 확인(`_drafts/p3_followup_questions.md` §1.1 -- 감사 원자료 `agent1_sizing_1_3021.md:22`가 상수와 `__init__`을 한 행에 묶었다)으로 ②는 오기 정정이 아니라 배정 변경임이 드러나 질문의 (나) 설명에 그대로 적었다.

사용자에게 제시하지 않은 것: 질문 준비 문서 `_drafts/p3_followup_questions.md`(경로·본문 모두 질문·메시지에 없음), 측정 키트 `_drafts/p3fq_kit/`·`_drafts/p3ud6_kit/`.

## 범위 설명

덮는 것:
* 계획 `docs/01-plan/features/gain-budget-gmid-sizing.plan.md` N3.10 표 MOD1 행(gate master `4a286f0` 기준 521행) 한 줄 교체 -- `'대표 대상'` 칸의 `` `_multilinear_interp_point_multi`, `` 뒤에 `` `_QUERY_CACHE_MAX`, ``를 넣는다(그 밖 바이트 불변, 줄 수 불변). 문안은 질문 준비 문서 §1.4 그대로:
  * 현재: `` | MOD1 | `gmid_lut.py` | LUT 인터페이스·보간·역산·곡선 검사·보간 오차 | `GmIdLUT`, `SemiEmpiricalGmIdLUT`, `_multilinear_interp`, `_multilinear_interp_point_multi`, `_solve_vgs`, `lut_conditions_from_npz`, gmb 유도(`∂ID/∂VSB`) | ``
  * 새 문안: `` | MOD1 | `gmid_lut.py` | LUT 인터페이스·보간·역산·곡선 검사·보간 오차 | `GmIdLUT`, `SemiEmpiricalGmIdLUT`, `_multilinear_interp`, `_multilinear_interp_point_multi`, `_QUERY_CACHE_MAX`, `_solve_vgs`, `lut_conditions_from_npz`, gmb 유도(`∂ID/∂VSB`) | ``
  * 효과(design 30 §6.2 A-1): 상수 `sizing_recipe.py::_QUERY_CACHE_MAX`가 레지스트리 277행 칸(MOD4)이 아니라 A-1로 MOD1 `gmid_lut.py`에 배정된다 -- 사용처 `SemiEmpiricalGmIdLUT._query`(MOD1)와 같은 모듈. MOD1 단위 7 → 8, MOD4 105 → 104.
  * 단위 수 키 구분(review_ud6 m2): 위 'MOD1 단위 7 → 8'은 계약 키(D0a 계약 2 바인딩 이름 -- `_QUERY_CACHE_MAX`가 단위 하나)로 센 수이고, 선택지 (가) 설명의 'MOD1은 8단위 그대로'는 질문 때 시제품의 해시 키(`hash_q` -- `_QUERY_CACHE_MAX`가 이름 단위로 서지 않는다)로 센 수다. 키가 달라 둘 다 사실이며 서로 모순이 아니다.
* **조건(답의 설명 "D0b가 다른 개정을 더 계산하면 그때 다시 묻습니다")**: D0b 착수(D0b spec card 순서 0) 전에 오케스트레이터가 D0b base(B34·b26pre·backfill·B26-1·B33·G1·FU·D0a 병합 + 이 개정)에서 D0a 도구 `plan`을 design 30 §6.3 `MP_ARGS`로 돌려
  `conflicts`·`upward`·`cycles`·`unassigned`·`import_time_high`·`import_conflicts`가 모두 빈 목록이고 MOD7 파일 밖 MOD7 배정이 0인지 확인한다(`reg_mismatch`는 D0b가 고치는 red라 제외 -- D0b 계약 8 (f)).
  하나라도 비지 않으면(이 개정 밖의 N3.10 개정 필요 -- D0b 계약 8 (a)·(c)·(e)) **D0b를 멈추고 사용자에게 다시 묻는다**. 이 승인은 그 추가 개정을 덮지 않는다.
  확인 대조값(사전 측정, 관찰 -- 기대값 근거 아님): 이 개정이 없으면 `upward` 1(`sizing_recipe.py::SemiEmpiricalGmIdLUT -> sizing_recipe.py::_QUERY_CACHE_MAX`, 원천 A-1)·`cycles` 1(`gmid_lut.py`↔`gmid_sizing_engine.py`), 있으면 둘 다 0.
* 판정 표 불변: 바뀐 줄(N3.10 표)은 `plan_tables_hash` 입력 밖이다 -- 사전 측정 개정 전·후 모두 `7167e02839f86c4ecbcd91a63a9833c4d83a8aab8008bfe2d8cfc36206d2596d`(gate master `4a286f0` 판 `tools/gates/merge_gate.py`). 바뀌었다면 이 기록이 아니라 `plan_tables` 승인이 필요하다.

덮지 않는 것:
* 레지스트리 277행(`` `_QUERY_CACHE_MAX` `` 함수 칸)의 수정 -- 선택지 (나)는 고르지 않았다. 277행 '이관 목적지' 칸은 D0b 재생성(code-author)이 도구 출력 `gmid_lut`로 다시 쓴다(D0b 계약 6 -- 손으로 쓰지 않는다).
  M1 독립 검토가 지적한 같은 모양의 291·293행(함수 칸 = 앞 상수, 책임 칸 = 뒤 함수)도 고치지 않는다 -- 사전 측정에서 그 두 행은 `upward`·`cycles`를 만들지 않는다(개정 적용 판 판정 목록 여섯 모두 0). 칸 모양 정정은 백로그.
* D0b가 자기 base에서 새로 계산하는 그 밖의 N3.10 개정(위 조건) -- 위임 없음, 나오면 따로 묻는다(UD-0 승인 기록 `20260930-30-module-split-design` '덮지 않는 것'과 같은 원칙).
* D0a 계약 2 문언(단위 키 = 바인딩 이름, 레지스트리 이름 칸은 첫 백틱 토큰 -- 질문 준비 문서 §5 명확화, 기준 변경 아님)과 [W-1] 답(T0 V5 승인 기록 `20260930-p3-tests-location-free`가 덮는다).
* D0b·M1의 판정(판정 기록), M1 단위 집합 자체(이관표는 D0b `plan` 출력이 정한다).

## 재검토

D0b 판정 기록의 `plan`(D0b base)에서 `_QUERY_CACHE_MAX` 배정이 `gmid_lut.py`·`A-1`이 아니거나 위 조건의 목록이 비지 않으면 이 기록의 조건이 깨진 것이다 -- D0b를 멈추고 다시 묻는다.
Phase 4에서 LUT 조회 캐시 상한을 바꾸거나 지우는 card는 N3.10 MOD1 토큰도 같은 card에서 함께 고친다(토큰만 남아 A-1이 빈 이름을 가리키지 않게).
