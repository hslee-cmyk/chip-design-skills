# AskUserQuestion 초안 [T0-V4] (r2t 2026-10-02 -- review_t0_fu T0-B1)

올릴 때: T0 착수 전. 착수 0단계 `step0_v4.sh`가 B26-1 병합본에서 MATCH가 아니면 늘어난 test id를 넣어 문장을 고친 뒤 올린다.
답이 오면 `approval_20261002-p3-t0-v4-s009-exempt.draft.md`의 '사용자 원문'에 jsonl 바이트 그대로 옮겨 Role: doc 커밋·push(T0 test worktree 생성 **전**).

질문(독립 검증 `review_t0_v4.md` §6 '고친 질문(JSON)'을 바이트 그대로 옮김 -- 정정: 선택지 2의 '744행은 고쳐도 FAIL'(거짓, W 식으로 고칠 수 있음), 선택지 3의 '같은 V4 문제가 그 card에서 다시 납니다'(피검 집합에 달림), 선택지 1에 면제가 T0에 묶이지 않음, 본문에 size_transistor는 입력 생성용·base도 FAIL. 사용자 답 없음 -- 열림):

```json
{"question": "[T0-V4] T0 계약 11(unit selftest 3파일 import 출처 3줄)로 test_selftest_sizing_recipe.py가 diff에 들어가면, 파일 전체를 보는 V4가 T0가 손대지 않는 기존 test_s009의 판정 2줄(revalidate 뒤 ID 보존, 원본 ctx 불변)을 규칙 (1) '같은 피검 호출이 양쪽에 있다'로 FAIL합니다. 피검 size_transistor는 입력 소자를 만드는 데만 쓰였고, base 트리에서도 같은 피검으로 재면 같은 FAIL입니다(TS2 때는 피검이 달라 드러나지 않았습니다). 어떻게 할까요?", "header": "T0-V4", "multiSelect": false, "options": [{"label": "test_s009 규칙(1) 면제 (Recommended)", "description": "선례 c9-v4-exempt처럼 decision 승인 기록 하나로 이 test id의 규칙 (1)만 면제합니다. 판정 2줄은 그대로이고 다른 규칙·다른 test는 계속 검사합니다. 기록이 저장소에 있는 동안 이후 card의 V4에도 적용되고, test 이름·경로가 바뀌면 풀립니다. 모래상자: 기록이 있으면 V4 PASS(면제 2, FAIL 0; 미판정 78은 TS2 이관본과 식이 같아 auditor가 basis에 적음)."}, {"label": "T0에서 두 줄을 식 값으로 고침", "description": "719행 기대값을 gm/gm_id 식으로, 744행을 W = L·ID/IDu 식으로 바꾸면 면제 없이 V4·test 모두 PASS입니다(모래상자). 대신 '원래 값 보존·원본 불변' 판정이 '구현과 같은 식의 값'으로 바뀌고, 이 파일은 V5 diff 해시 밖이라 V5가 이 변경을 잡지 못합니다. 계약 11의 '기대값 불변'과 V5 승인 범위를 다시 써야 합니다."}, {"label": "계약 11을 T0에서 빼기", "description": "unit 3파일 import 수정을 별도 test-only card로 옮겨, 이미 고른 [W-1] (가)를 되돌립니다. M4 전에 card가 하나 더 듭니다. 그 card의 피검이 nmcnr_predict_ac_response뿐이면 V4는 이 FAIL을 내지 않습니다(모래상자 PASS). 그러나 이는 test_s009를 판정하지 않기 때문이고, size_transistor를 피검으로 가진 card가 그 파일을 바꾸면 같은 FAIL이 다시 납니다."}]}
```
