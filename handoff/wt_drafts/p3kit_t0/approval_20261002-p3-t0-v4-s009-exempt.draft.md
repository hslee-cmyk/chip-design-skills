---
id: 20261002-p3-t0-v4-s009-exempt
date: 2026-10-02
target_kind: decision
target: skills/analog-gmid-design/assets/tests/unit/test_selftest_sizing_recipe.py::test_s009_revalidate_finger_override
scope: Phase 3 T0 20260930-p3-tests-location-free -- 계약 11(import 출처 3줄)로 V4 대상이 된 이관본 test 1개를 V4 규칙 (1)에서 면제(불변식 2줄, T0가 바꾸지 않는 기존 줄)
---

## 사용자 원문

> test_s009 규칙(1) 면제 (Recommended)

(AskUserQuestion [T0-V4]의 답이다. 질문 2026-10-02 19:52 KST(`2026-10-02T10:52:43.807Z`), 답 2026-10-02 19:54 KST(`2026-10-02T10:54:13.036Z`) -- 세션 기록
`63c6146a-ab1d-4035-a169-bae810986922.jsonl`의 tool_use `toolu_01KVccUdWPjUbVW8oUx2DvZs`(uuid `45dbaa0d-aa4f-4c09-8819-e911249e55dd`, header `T0-V4`)와 그 tool_result(uuid `48af7b3d-bd39-444d-b95f-2225b30b0e16`, `toolUseResult.answers`)에서
바이트 대조해 옮겼다(따옴표 안은 jsonl 문자열 그대로 -- 고치지 않았다). 답은 첫째 선택지 라벨과 같다. 같은 문안의 앞선 게시는 답 없이 설명 요청으로 끝났다 -- 아래 '사용자에게 보인 것' 2~5.)

질문 원문: "[T0-V4] T0 계약 11(unit selftest 3파일 import 출처 3줄)로 test_selftest_sizing_recipe.py가 diff에 들어가면, 파일 전체를 보는 V4가 T0가 손대지 않는 기존 test_s009의 판정 2줄(revalidate 뒤 ID 보존, 원본 ctx 불변)을 규칙 (1) '같은 피검 호출이 양쪽에 있다'로 FAIL합니다. 피검 size_transistor는 입력 소자를 만드는 데만 쓰였고, base 트리에서도 같은 피검으로 재면 같은 FAIL입니다(TS2 때는 피검이 달라 드러나지 않았습니다). 어떻게 할까요?"

## 사용자에게 보인 것

이 기록이 덮는 범위의 근거는 사용자가 실제로 본 아래뿐이다(세션 기록 `63c6146a-…jsonl`에서 확인, 사이드체인 제외 assistant 텍스트).
질문 문안·선택지는 `p3kit_t0/ask_t0_v4.md`의 JSON(독립 검증 `review_t0_v4.md` §6 고친 질문)과 객체 단위로 같다(프로그램 대조).

1. 위 AskUserQuestion [T0-V4] 문안과 세 선택지(라벨·설명) -- 미리보기 없음. 질문 원문은 위 '질문 원문', 선택지는 아래 그대로(따옴표 안 = jsonl 문자열):
   * 선택지 1 "test_s009 규칙(1) 면제 (Recommended)" -- "선례 c9-v4-exempt처럼 decision 승인 기록 하나로 이 test id의 규칙 (1)만 면제합니다. 판정 2줄은 그대로이고 다른 규칙·다른 test는 계속 검사합니다. 기록이 저장소에 있는 동안 이후 card의 V4에도 적용되고, test 이름·경로가 바뀌면 풀립니다. 모래상자: 기록이 있으면 V4 PASS(면제 2, FAIL 0; 미판정 78은 TS2 이관본과 식이 같아 auditor가 basis에 적음)."
   * 선택지 2 "T0에서 두 줄을 식 값으로 고침" -- "719행 기대값을 gm/gm_id 식으로, 744행을 W = L·ID/IDu 식으로 바꾸면 면제 없이 V4·test 모두 PASS입니다(모래상자). 대신 '원래 값 보존·원본 불변' 판정이 '구현과 같은 식의 값'으로 바뀌고, 이 파일은 V5 diff 해시 밖이라 V5가 이 변경을 잡지 못합니다. 계약 11의 '기대값 불변'과 V5 승인 범위를 다시 써야 합니다."
   * 선택지 3 "계약 11을 T0에서 빼기" -- "unit 3파일 import 수정을 별도 test-only card로 옮겨, 이미 고른 [W-1] (가)를 되돌립니다. M4 전에 card가 하나 더 듭니다. 그 card의 피검이 nmcnr_predict_ac_response뿐이면 V4는 이 FAIL을 내지 않습니다(모래상자 PASS). 그러나 이는 test_s009를 판정하지 않기 때문이고, size_transistor를 피검으로 가진 card가 그 파일을 바꾸면 같은 FAIL이 다시 납니다."
2. 같은 질문의 첫 게시(`2026-10-02T10:22:22.010Z`, tool_use `toolu_01SbLs1H4zGCJ61Nij3gxKmZ`, uuid `952bd4cb-4f8b-43b5-a096-781cd57cb1ea` -- 입력 JSON이 위 답한 호출과 완전히 같음, 프로그램 대조)에 사용자는 답하지 않고 설명을 요청했다
   (tool_result uuid `b2005a09-e89c-4712-9909-beea66369b55`, `2026-10-02T10:32:57.026Z`: "The user wants to clarify these questions." … "(No answer provided)"). 이어 사용자 입력(`2026-10-02T10:33:04.577Z`, queued_command, attachment uuid `a0140c80-e000-49f5-aff4-d50c3fa7f2bc`, origin human), 원문(따옴표 안 jsonl 그대로 -- 앞 작은따옴표가 빠진 것도 원문):
   "원래 값 보존·원본 불변' 판정이 무슨 뜻이야?"
3. 그 물음에 대한 오케스트레이터 설명(`2026-10-02T10:35:01.527Z`, uuid `0da15560-7333-4e22-94d0-8c4067f30b46`), 원문(펜스 안 = jsonl text 블록 그대로):

```text
'원래 값 보존·원본 불변'은 test_s009에 있는 두 단정을 가리킵니다. 두 단정 모두 `revalidate_finger_override()`라는 함수를 검사합니다. 이 함수는 소자의 W를 강제로 바꿨을 때 회로가 여전히 constraint를 만족하는지 다시 확인합니다.

**test 흐름**
1. 먼저 `size_transistor()`로 M1~M3 소자 값(ID·W·gm 등)을 만들어 입력(ctx)을 준비합니다.
2. M1의 W를 10% 줄이고 `revalidate_finger_override()`를 부릅니다. 40% 줄인 경우도 한 번 더 부릅니다.
3. 그 결과를 아래 두 줄로 단정합니다.

**① "원래 값 보존" (현재 파일 714행 근처)**
```python
assert abs(new_gm / new_gm_id - _l4_r1.ID) < 1e-15, "ID가 보존되지 않음 -- W가 바뀌어도 ID는 topology로 고정이어야 한다"
```
- W를 바꿔도 소자 전류 ID는 회로가 정하므로 그대로여야 한다는 원칙을 봅니다.
- 그래서 재검증 뒤의 ID(gm ÷ gm_id)가 처음 넣은 ID와 같은지 확인합니다.

**② "원본 불변" (현재 파일 739행 근처)**
```python
assert _l4_ctx.sized["M1"]["W"] == _l4_r1.W, "revalidate_finger_override()가 원본 ctx를 변형했다"
```
- 이 함수는 "W를 바꾸면 어떻게 되나"를 시험해 보기만 해야 합니다. 입력으로 받은 원본 회로 상태(ctx)를 고쳐 쓰면 안 됩니다.
- 그래서 호출 뒤에도 원본의 M1 W가 처음 값 그대로인지 확인합니다.

**V4가 이 두 줄을 FAIL로 보는 이유**
- 기대값 `_l4_r1.ID`·`_l4_r1.W`는 `size_transistor()`를 불러서 얻은 값입니다.
- V4 규칙 (1)은 "피검 함수의 출력을 기대값으로도 쓰면, 같은 계산을 양쪽에 놓은 동어반복일 수 있다"는 검사입니다. T0의 interface card에서는 `size_transistor`가 피검으로 잡혀 있어서 이 규칙에 걸렸습니다.
- 그런데 이 test에서 `size_transistor`는 입력을 만드는 데만 쓰였습니다. 실제 검사 대상은 `revalidate_finger_override()`입니다.
- 비교도 "처음 넣은 값 = 나중에 나온 값"이라 동어반복이 아닙니다. 그래서 기계 규칙이 오탐한 경우로 봤고, 면제를 추천안으로 두었습니다.

**선택지 2 "두 줄을 식 값으로 고침"이 약화인 이유**
- ①의 기대값을 `_l4_r1.ID` 대신 gm/gm_id 같은 식으로, ②를 W = L·ID/IDu 식으로 다시 계산해 넣으면 V4는 통과합니다.
- 하지만 판정 뜻이 바뀝니다.
  - 지금: "처음 넣은 바로 그 값이 보존되었나"
  - 바꾼 뒤: "구현과 같은 식으로 다시 계산한 값과 같은가"
- 그러면 구현과 test가 같은 식을 공유하게 되어, 식 자체가 틀려도 잡지 못합니다.
- 이 파일은 V5 감시 범위 밖이라 이런 의미 변화를 게이트가 잡지 못합니다. 그래서 권하지 않았습니다.

더 궁금한 점이 없으시면 같은 질문을 다시 올리겠습니다. 문구를 바꿨으면 하는 부분이 있으면 말씀해 주십시오.

지금 8개 작업이 진행 중입니다:
- card 35 감사 7단계
- card 35 병합 뒤 재측정 스크립트
- B26-1 운반 스크립트 독립 검토
- F1 r3
- B34 사전 실행
- b26pre·backfill 사전 실행
- M2~M9 수정
- T0-V4 초안 사실 정정
```

4. 다시 올리기 전 오케스트레이터 메시지 세 건 -- 모두 "앞서 드린 설명에 더 궁금한 점이 없으시면 다시 올리겠습니다" 취지로 끝난다(원문은 jsonl; `10:42:25.466Z` uuid `03341473-74aa-4367-bfc5-795f30944134`는 질문 초안 사실 정정(744행도 식으로 고칠 수 있음·피검 집합 의존·면제가 이후 card에도 적용)을 요약,
   `10:45:05.459Z` uuid `84d1e06d-e333-437f-9846-91bb1179b70f`, `10:46:58.155Z` uuid `589a505f-95ab-4b68-89aa-d15b57341f26`은 백로그 B58 "V4가 diff에 걸린 파일 전체를 검사해, 손대지 않은 기존 test까지 FAIL로 만드는 문제"를 적었다).
5. 사용자 입력(`2026-10-02T10:52:13.871Z`, uuid `98e1085a-2d76-4e59-ad29-c3623c1fc921`), 원문: "응, 질문 다시 올려" -- 그 뒤 위 질문을 같은 문안으로 다시 올렸고 답이 왔다.

첫 게시부터 답까지 사용자 입력은 위 2·5의 두 건뿐이다(사이드체인 제외 human 입력 전수, 프로그램 확인).
사용자에게 제시하지 않은 것: 독립 검증 `_drafts/review_t0_v4.md`, 이 기록의 초안, 질문 초안 `p3kit_t0/ask_t0_v4.md`, spec card 초안 `draft_p3_t0.spec.md` [T0-V4] 항목 (i)~(iv)의 본문(경로·본문 모두 질문·메시지에 없음 -- 위 4의 요약만 보였다).

## 범위 설명

근거: T0 계약 11이 unit selftest 3파일 24행의 import 출처만 바꾸지만, V4(`tools/gates/test_lint.py`, gate `4a286f0` 판 718~721행 선택·723~726행 lint)는 `--diff-filter=AM` 파일을
**파일 전체** lint한다(705~709행 `read`가 head 트리의 파일 전체를 읽는다 -- hunk만 보는 경로 없음). 그래서 `test_selftest_sizing_recipe.py` 전체가 interface card 피검(`sizing_recipe.size_transistor` 등 기존 함수 6)으로 판정되고,
`test_s009_revalidate_finger_override`의 두 판정 문장이 규칙 (1)에 걸린다(base 트리에서도 같은 FAIL -- T0가 만든 판정이 아니다):
* 719행 `abs(_l4_du_pass["new_gm"] / _l4_du_pass["new_gm_id"] - _l4_r1.ID) < 1e-15` -- `revalidate_finger_override()` 뒤 ID 보존(불변식). `_l4_r1 = size_transistor(...)`가 입력 소자를 만들어 양쪽에 남는다.
* 744행 `_l4_ctx.sized["M1"]["W"] == _l4_r1.W` -- 원본 ctx를 바꾸지 않음(불변식). 같은 이유.
둘 다 이관본 S009(oracle (c), docstring '판정을 그대로 옮겼다')의 판정이고 피검 출력을 리터럴로 박은 복사가 아니다. 선례 `20260923-c9-v4-exempt`(불변식·재현성 2건)와 같은 종류다.
피검 `size_transistor`는 입력 소자를 만드는 데만 쓰였다(시험 대상은 `revalidate_finger_override`). base 트리의 같은 파일도 같은 피검으로 재면 같은 두 줄(base 714·739행)이 FAIL이다.
T0에서 두 줄을 고치는 대안: 두 줄 모두 면제 없이 고칠 수는 있다(719행 기대값을 gm/gm_id 식 값으로, 744행을 W = L·ID/IDu 식으로 -- 모래상자 V4·test PASS; 744행을 스냅숏 지역 변수로 바꾸는 것만은 V4 인라인이 꿰뚫어 FAIL).
그러나 그러면 판정이 '원래 값 보존·원본 불변'에서 '구현과 같은 식의 값'으로 바뀌는 판정 기준 변경이고, 이 파일은 V5 `diff_paths` 밖이라 V5가 그 변경을 잡지 못한다 -- 하지 않는다.
덮는 것: 위 test id의 **규칙 (1)** 발견만(면제 경로 C13 `20260923-v4-decision-exempt`, `test_lint.py` 727~734행). 발견은 `output: exempt`로 출력 JSON과 판정 기록에 남는다.
덮지 않는 것: 다른 test, 같은 test의 규칙 (2)~(5), 이름·경로가 바뀐 뒤의 같은 판정(그때는 면제가 저절로 풀린다 -- F1·M card에서 파일이 옮겨지면 다시 본다).
다른 card 범위로 한정하지 않는다: V4는 head 트리의 `.ai/approvals` 전체를 읽으므로(`reachability._approved_ids`), 이 기록이 저장소에 남아 있는 동안 T0 뒤 모든 card의 V4에도 적용된다(test 이름·경로가 바뀌면 풀린다).
측정(모래상자, base `4a286f0`, 모의 T = 계약 1~4 시제품 + 계약 11): 이 기록 없이 `--interface-card` 단독 FAIL exit 1(규칙 (1) 2), 이 기록을 head 트리에 두면 PASS exit 0(exempt 2, UNJUDGED 78, FAIL 0).
UNJUDGED 78은 TS2 병합본 `caac910` 같은 파일의 assert 식(메시지 포함)과 `ast.unparse` 문자 단위로 같다 -- auditor basis에는 "TS2 전수 대조 식과 같음"으로 적는다(TS2 때 UNJUDGED는 26개였고 이 78개는 전수 대조로 덮였다).
착수 0단계(`p3kit_t0/step0_v4.sh`) B26-1 병합본 재측정 = <MATCH 결과 줄 -- B26-1 병합 뒤 착수 0단계 (아)의 `v4_summary.txt` 판단 줄을 커밋 전에 그대로 옮긴다. MATCH(FAIL id = 위 test id 하나)가 아니면 이 기록을 커밋하지 않고 멈추고 보고한다 -- 사용자 답은 위 test id 하나만 덮는다. 이 자리표시자가 남은 기록은 `t0_launch.sh` pre·card가 거부한다>.

## 재검토

Phase 4에서 `test_selftest_sizing_recipe.py`의 판정을 다른 oracle로 쓸 수 있는지 `20260923-c9-v4-exempt` 재검토(백로그 B9)와 함께 본다.
