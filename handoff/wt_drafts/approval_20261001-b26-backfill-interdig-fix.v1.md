---
id: 20261001-b26-backfill-interdig-fix
date: 2026-10-01
target_kind: decision
target: U-BF-BACKFILL-INTERDIG
scope: 결정 U-BF -- run_matching_safety_with_finger_growth의 relaxed_pairs[i]["interdig_ok"]를 반환 audit(euler 정리 뒤 최종 물리 구조)의 3b 판정으로 채우도록 수정(관찰 가능한 반환값 변경, spec card 20261001-b26-backfill-interdig-final-audit), 순서 b26pre 뒤·B26-1 앞
---

## 사용자 원문

> 결함으로 고침 (Recommended)

(AskUserQuestion 답, 2026-10-01 19:19 KST. 사용자에게 보인 질문은 준비 문서 `_drafts/b26_backfill_question.md` [U-BF]를 줄인 문안이다 -- 질문 원문(2026-10-01 19:17 KST, 고치지 않고 그대로): "[U-BF] 핑거증가 루프 run_matching_safety_with_finger_growth가 돌려주는 relaxed_pairs[i]["interdig_ok"]가 같은 결과의 audit과 어긋납니다. interdig_ok는 euler 정리(행 나누기) 전 audit으로 채워지고 정리 뒤 audit으로 덮어쓰지 않습니다. 합성 재현(Ma·Mb offset 쌍 + 사이에 끼인 Mp, gm/ID 11.9~12.1): interdig_ok=False인데 같은 반환의 audit 3b(참고용 체크)는 True입니다. 코드 주석 11784~11786은 '반환 audit = 최종 물리 구조', 11769~11770은 'interdig_ok는 audit의 3b로 채운다'라고 적어 두 주석을 합치면 결함입니다. audit.ok는 3c 실패로 어느 쪽이든 False이고 바뀌는 것은 보고되는 interdig_ok 값 하나입니다. 이 값으로 분기하는 운영 코드는 없고, 기존 test 전체에서 어긋난 호출은 0회입니다(library 회로 영향은 card의 auditor가 쟽니다). B26-1 변이 검사에서 이 두 줄을 지운 변이가 살아남는데, 지운 쪽이 오히려 audit과 맞는 값을 냅니다. 어떻게 할까요?"
선택지: "결함으로 고침 (Recommended)" -- "red-green code card 1건을 b26pre test card 뒤, B26-1 앞에 둡니다. test: '반환 interdig_ok = 반환 audit의 3b'(루프 안·뒤 두 경로). 수정 후보(정리 전 backfill 두 줄 삭제)는 사본에서 red→green, 전체 test 회귀 없음. B26-1 수치는 그 병합본에서 다시 쟽니다." /
"지금 동작 고정" -- "test로 interdig_ok == False를 박습니다. audit과 어긋난 값을 정답으로 고정하므로 권하지 않습니다." /
"백로그로 둠" -- "B26-1 변이 검사에서 이 두 변이를 '알려진 결함 생존'으로 남깁니다. 별도 결정 기록이 필요하고 불일치는 남습니다."
배경 사실 전체(주석 원문·재현 입력·영향 범위·경위)는 준비 문서 `_drafts/b26_backfill_question.md`(근거: 독립 검토 `_drafts/review_b26pre.md` §1 B1·B2, `_drafts/review2_b26pre.md` §3·§8, gate `0f23786`). 줄 번호는 gate `0f23786`의 sizing_recipe.py 기준.)

## 범위 설명

덮는 것: 반환 `relaxed_pairs[i]["interdig_ok"]` 값 하나의 의미 변경 -- euler 정리 전 audit이 아니라 반환 audit(정리 뒤 최종 물리 구조)의 3b 판정으로 채운다 -- 과 그 red-green code card(`20261001-b26-backfill-interdig-final-audit`)를 b26pre test card 뒤·B26-1 앞에 두는 순서. 이 답이 그 card test의 판정 기준(oracle (d) 사용자 결정)이다.
덮지 않는 것: 완화 정책 자체(3c 요구 유지, `audit.ok` 판정), `relaxed_pairs`의 다른 키, 행·audit·사유 값, V3·V7 면제.

## 재검토

library 회로에서 값이 달라지는 사례가 나오면 그 card의 판정 기록에 회로·쌍·전후 값을 적는다.
