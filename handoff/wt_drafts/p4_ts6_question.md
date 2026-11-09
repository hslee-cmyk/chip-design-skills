# TS6 도구 비교 test 질문 초안 -- F1 V5 질문(QB)과 Phase 4 #2 D1을 하나로 묻는다

상태: **초안 -- 지금 묻지 않는다.** 묻는 시점은 오케스트레이터가 정한다(F1 V5 승인 질문 묶음 -- `review_p3_f12.md` §6 QB를 이 문안으로 대체. #2 D1은 따로 묻지 않고 이 답을 따른다).
근거 측정: `draft_p4_first.spec.md` 결정 필요 항목 D1·계약 8 (A1)~(A3)·'작성 전 실측' 16(r2)·**17(r3)**. r3 = gate `master` `4a286f0`, 격리 복제본 `C:/g235`(측정 전용 모의, 삭제됨). 독립 검증 `review_ts6_pin.md`(S1: r2 문안이 (다+핀) 보호를 과대 표시)를 반영해 다시 썼다(반영 전 사본 `p4_ts6_question.pre-r3.md`).
**r4**: 독립 검증 `review_ts6_ma.md`(S1: (마) 정규형 2 (c)가 중첩 엔진 import까지 빼서 루프 안 import로 호출 대상을 바꾸는 변경을 놓침, minor 1~4) 반영 -- card 계약 8 (A3) 2 (c)를 **모듈 최상위만**으로 좁혔고, (마) description은 독립 검증 §6의 고친 문안 그대로다(나머지 선택지·질문 본문은 그대로). 재측정 = card '작성 전 실측' 18(gate `master` `4a286f0`, 격리 복제본 `C:/g248`, 삭제됨). 반영 전 사본 `p4_ts6_question.pre-r4.md`.
질문 하나, 선택지 4개(원칙상 가장 나은 4개 -- (나) 허용 문장은 (마)보다 모든 축에서 약하고(검출 19/23, #2에서 다시 FAIL, 문구 의존), (라) test 은퇴는 (다)보다 엄격히 약해 뺐다. 사용자는 '기타'로 고를 수 있다).

## AskUserQuestion 문안

* header: `[F1·#2] TS6` (11자)
* multiSelect: false
* question:
  "[F1·#2] Phase 3 F1은 tests/tools/derive_achievable_bounds.py의 `import sizing_recipe as sr`와 `sr.` 속성 줄을, Phase 4 #2는 같은 도구의 사이드카 읽기·쓰기 문장을 바꿉니다. TS6 이동 계약 test(test_moved_tool_matches_base_except_path_lines)는 지금 도구가 2026-09-23 이동 원본과 경로 줄 밖에서 한 글자도 다르지 않기를 요구해 두 card 모두에서 실패합니다(F1 12줄, F1+#2 23줄). 아래 네 안은 **모두 지금 test보다 약합니다**(V5 약화 승인 -- 지금 test는 경로 줄 밖 모든 글자를 고정). '검출'은 선언 기록·계산을 바꾸는 변경 23종 실측입니다. F1 test 커밋에서 이 test를 어떻게 바꿀까요? (한 번만 묻고 #2는 이 답을 따릅니다)"
* options:
  1. label: **"(마) 전체 정규화 핀 (Recommended)"**
     description: "이동 사실은 이동 커밋(9d6800e)을 원본과 비교해 계속 판정하고, 지금 도구는 docstring·출력(emit/print) 호출 인자·최상위 엔진 import 줄·경로 문장(os.path·sys.path 호출이나 절대 경로를 담은 문장 -- 지금 test와 같은 정의)만 빼고 전체 AST를 '핀'(고정 커밋 도구 + 승인된 편집)과 비교합니다. 검출 23/23(+ 이름을 갖지 않은 다른 엔진 모듈로 호출 바꾸기·엔진 아닌 import 바꾸기도 잡음). 잃는 것: docstring·주석·출력 문구(그 안의 식과 부수효과 포함)·엔진 import 줄 모양, 같은 이름을 가진 다른 엔진 모듈로 별칭 바꾸기. V5: F1 = 이 전환 1회, F1의 import 변경은 통과(추가 0). #2 = test 커밋에서 핀 편집 2쌍을 더해 1건(test 먼저 작성 가능). 이후 도구 계산·기록을 바꾸는 card마다 1건."
  2. label: "(다+핀) 이동 커밋 + 6요소 핀"
     description: "이동 사실은 (마)와 같고, 지금 도구는 6요소(achievable_metric_bound 호출 인자, targets·fp 대입, 루프 직속 대입, value·_derived 기록 루프, 선언 파일 쓰기 with)만 AST로 고정합니다. 검출 7/23: 6요소 안 변경 7종만 잡고, 6요소 밖 문장으로 기록을 바꾸는 16종(기록 가드 끄기, 입력 준비 줄, 루프 안 대입 아닌 문장, 문장 순서, 호출 대상 모듈 바꾸기 등)은 하나도 못 잡습니다 -- 그 범위는 사람 diff 검토뿐. V5: F1 = 이 전환 1회, #2 = 0, 이후 6요소를 바꾸는 card만 1건."
  3. label: "(가) 기준선에 F1 치환 반영"
     description: "비교 기준을 '이동 원본 + F1 import 치환'으로 바꾸고 경로 줄 밖을 지금처럼 글자 그대로 고정합니다. 검출 23/23. 그러나 F1 test를 F1 이전 도구에 얹으면 실패(12줄)해 test를 먼저 쓸 수 없고, F1이 from-import 모양을 고르면 치환을 다시 맞춰야 하며(14줄), #2에서 다시 실패(15줄)합니다. V5: F1 = 1회, #2 = 기준선 수정 2건, 이후 문구 한 글자를 바꾸는 card까지 매번."
  4. label: "(다) 이동 커밋끼리만 대조"
     description: "이동 커밋(9d6800e)의 도구만 원본과 비교합니다. 이동 사실 판정은 남지만 지금 도구는 어떤 test도 보지 않습니다(검출 0/23). V5: F1 = 이 전환 1회, 이후 어떤 card도 0. 가장 단순하고 다시 고칠 일이 없습니다."

## 비교표(실측 -- 선택지 설명의 근거, 질문 본문에는 넣지 않는다)

순서 = F1이 항상 먼저(#2는 `phase: 4`라 Phase 3 DoD 전에 병합 불가). 단계: S0 = F1 test만 얹은 F1 base(도구 그대로) / S1 = F1 병합본(도구 F1 모양 -- 목적지 셋이라 `_f1_<목적지>` 별칭 import 셋, `p3kit_f12/f12_f1sim.py` 규칙 (2) 근사) / S1f = F1이 from-import 모양을 고른 경우 / S2 = F1 위 #2 K 병합본(계약 5 전체). 괄호 = 비경로 줄 수.
변이 23종 = 독립 검증 `review_ts6_pin.md`의 7종(sense 강제, 보수값 대신 best 기록, `_derived` 기록 문장 삭제, slsqp_kwargs 무시, sense 기본값 min→max, `book[fp][metric] = r` 제거, 선언 파일 쓰기 제거) + 16종(다른 모듈의 같은 이름 함수 호출, `H.achievable_metric_bound`, 기록 가드 `if wrote and False`, 루프 안 비대입 문장, 루프 사이 `book[fp].clear()`, `cons[:1]`, `n_starts=1`, `if targets:`, `targets[:] =`, `targets +=`, 선언 제약 덮어쓰기, 쓰기 블록 순서, `json.dump`→`H.dump`, `SPECS` 덮기, `dict(…, conservative=-1.0)`, Try 안 결과 덮기) -- 모든 안이 PASS하는 S1 위에서 잼(r3에서 그 설명대로 다시 만듦).

| 안 | S0 | S1 | S1f | S2 | 검출(23종) | 문구·구분선·docstring 변경 | card별 V5 |
|---|---|---|---|---|---|---|---|
| 지금 test(그대로) | PASS | FAIL(12) | FAIL(12) | FAIL(23) | (경로 줄 밖 전부) | FAIL | F1에서 이미 불가 |
| **(마) 전체 정규화 핀** | PASS | PASS | PASS | F1 핀 그대로면 FAIL → #2 T 핀 편집 뒤 PASS(T 트리도 PASS) | **23/23**(+ 중첩 엔진 import 공격 4종 -- r4) | 통과 | F1 전환 1(발견 2), F1 K 0, #2 T 1, 이후 정규형을 바꾸는 card마다 1 |
| (다+핀) | PASS | PASS | PASS | PASS | 7/23 | 통과 | F1 전환 1, #2 0, 6요소를 바꾸는 card만 1 |
| (가) 기준선+F1 치환 | **FAIL(12)** | PASS | FAIL(14) | FAIL(15) | 23/23 | FAIL | F1 1(test-first 불가), #2 다시, 문구 card마다 |
| (나) 허용 문장 추가(선택지 밖) | PASS | PASS | -- | FAIL(13) | 19/23(독립 검증) | FAIL | F1 1, #2 다시, 문구 card마다 |
| (다) 이동 커밋만 | PASS | PASS | PASS | PASS | 0/23 | 통과 | F1 전환 1, 이후 0 |
| (라) test 은퇴(선택지 밖) | -- | -- | -- | -- | 0/23 | -- | 없음, 이동 판정도 사라짐 |

* (마)의 실제 pytest(r3 모의 커밋 열, r4 정정판으로 다시 만든 열도 같음, TS6 파일): base·F1 T·F1 K(별칭 셋·from-import)·#2 T·#2 병합본·순서 I(F1 없이 #2) T·병합본 모두 **33 passed**, T 없이 #2 K만 얹으면 **1 failed**(이 test). 수집 id 33개 정렬 목록 전 단계 같음(새 test id 0) -- 해시 형식: `pytest --collect-only -q`의 `::` 줄(저장소 루트 상대 node id 전체)을 정렬해 줄마다 `\n`을 붙인 UTF-8 바이트의 sha256 앞 12자 `c66e04745a4a`, 같은 집합을 `tests/contracts/` 뒤 문자열로 = `251db052c443`(card '작성 전 실측' 18).
* (마)의 V5(`weakening_diff.py`): F1 T 발견 2(비교 완화·리터럴 변경 -- 전환 자체, 다른 안과 같은 비용), #2 T 발견 1('리터럴 변경' -- 핀 편집 수 정수 0→2). 정수 리터럴 단언이 없으면 #2 T 발견 0(편집 쌍 '삽입'은 V5가 보지 않음) -- 그래서 card 계약 8 (A3)이 단언을 요구한다.
* (마) 추가 표본: 묶지 않는 기존 엔진 모듈 별칭으로 호출(`stick_diagram`) 검출, 엔진 아닌 import 바꾸기 검출(둘 다 (다+핀)은 통과). 독립 검증의 '전체 모듈 정규화'가 놓친 3종(N1·N1b·N11)은 별칭 정규화를 '엔진 모듈이고 그 모듈이 이름을 묶을 때'로 좁혀 닫았다.
* **r4 정정**(독립 검증 `review_ts6_ma.md` S1): r3 정의는 엔진 import 빼기(정규형 2 (c))를 함수·루프 안 문장 목록에도 적용해, 루프 안에 `import stick_diagram as <기존 엔진 별칭>`·`import evil_eng as …`·`from stick_diagram import find_hub_merge_candidates as achievable_metric_bound`·`from evil_eng import achievable_metric_bound`를 넣어 호출 대상을 바꾸는 변경 4종을 통과시켰다(지금 test는 거부). 2 (c)를 **모듈 최상위만**으로 좁혀 4종 모두 검출, 23종·단계·pytest·수용 표본·V5는 그대로(r4 실측). 같은 별칭이 최상위에 두 번 묶이면 뒤 문장이 이긴다(Python 실행 의미 -- 앞이 이기게 하면 `import stick_diagram as <별칭>`을 뒤에 둔 변경이 통과한다).
* (마)가 잃는 것(지금 test 대비): docstring·주석·`emit`/`print` 인자(문구와 그 안의 식 -- 기존 출력 f-string 안에 부수효과 식을 넣으면 통과, r3 실측; 도구의 `def emit` 본문 `print` 인자도 비우므로 거기에 `file=…`를 더해도 통과, r4 실측)·**최상위** 엔진 import 줄 모양의 내용 고정. 같은 이름을 묶는 다른 엔진 모듈로의 **최상위** 별칭 바꾸기(재수출이면 같은 객체, 다른 정의면 R-DEF 위반)와 핀 상태 중 편집 전 모양으로 되돌리기(#2 뒤에는 계약 3 GONE test가 거부)도 기계로 막지 않는다. 함수·루프 안 엔진 import로 호출 대상을 바꾸는 변경은 잃지 않는다(r4).
  경로 문장은 지금 test와 같은 정의로 허용한다: `os.path.*` 호출·`sys.path.insert` 호출·절대 경로 문자열을 **담은** `Assign`/`AnnAssign`/`AugAssign`/`Expr` 문장 전체가 빠지므로, 그런 호출 하나를 담은 **새 계산 문장**(예: `targets = targets[:1] if os.path.isfile(topo) else targets`)도 통과한다(r4 실측 -- 지금 test도 통과).
* (다+핀)이 잃는 것: 위에 더해 핀 6요소 밖 모든 문장(23종 중 16종 -- 기록 가드·입력 준비·루프 안 비대입 문장·순서·호출 대상 모듈). 그 범위는 card 범위 문장 + auditor diff 검토(사람)로만 본다.
* 이동 커밋 구조 확인((마)·(다+핀)·(다) 공통): 부모 정확히 하나·부모 tree에 새 자리 없음(`ls-tree` 성공+빈 출력)·HEAD 조상 -- 거부 표본 `36e170e`·`a574f97` 거부, 얕은 복제 경계에서 닫힘.

## 답별 처리(오케스트레이터용)

* (마): F1 test 커밋이 card 계약 8 (A1)+(A3)(r4 문장)로 고친다(F1 V5 범위 = 그 test 단위 -- 발견 2). 핀 = `pin_commit` `9d6800ef74017dd015f4628e840bdc9d965b42ce`·`pin_edits` `()`·`assert len(pin_edits) == 0`. #2 계약 8 (B): #2 T가 `pin_edits` = E_#2 두 쌍, 정수 0→2(#2 V5에 TS6 1건 -- 목록 7건).
  핀을 고치는 card(#2 포함)의 V5 승인 기록 범위 설명은 **E_#2 편집 쌍 원문(기준·바꿀 문자열 그대로)과 `pin_commit` 값(40자 sha 그대로)**, 정수를 인용한다 -- V5 출력만으로는 정직한 편집·변조된 쌍·가짜 핀 커밋이 같은 발견 문구로 보인다(독립 검증 T3·T4).
* (다+핀)·(다): F1 test 커밋이 그 규칙으로 고친다(F1 V5 범위 = 그 test 단위). #2 계약 8 (B) 무동작, #2 V5에서 TS6 2건 빠짐(8 → 6건).
* (가)·(나): F1 test 커밋이 그 규칙으로 고치고, #2 T가 #2 변경분을 기준선·허용 줄에 더한다(#2 V5에 TS6 단위 남음 -- 8건).
* 기타(예: (라) 은퇴): 답 원문대로 F1 card 결정 필요 항목 1과 #2 계약 8 (B)를 고친다.
