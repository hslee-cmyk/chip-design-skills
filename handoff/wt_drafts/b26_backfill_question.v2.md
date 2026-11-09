# 사용자 결정 질문 초안 -- `interdig_ok` backfill 불일치(U-BF)

작성 2026-10-01. 근거: 독립 검토 `_drafts/review_b26pre.md` §1 B1·B2, 재측정 `_drafts/b26pre_v2_scripts/`(scratch C:/g106, 측정 뒤 삭제), card 초안 `_drafts/draft_b26_backfill_audit.spec.md`.
오케스트레이터가 AskUserQuestion으로 물을 때 아래 문안을 쓴다. 이 결정은 엔진의 관찰 가능한 반환값을 바꾸므로 사용자 몫이다(공유 엔진 코드는 승인 후).

---

## Q. [U-BF] 핑거증가 루프가 돌려주는 `interdig_ok`가 같은 결과의 감사(audit)와 어긋나는 경우가 있습니다. 고칠까요?

**배경(사실만)**:
- 함수: `run_matching_safety_with_finger_growth`(sizing_recipe.py). gm/ID 예산 때문에 핑거증가를 못 하면 그 매칭 쌍을 '인접배치로 완화'하고, 반환 `relaxed_pairs` 항목에 `interdig_ok`(완화 뒤 3b 인접배치 판정)를 적습니다.
- 코드 주석(11784~11786, 원문): "이 함수의 **모든** 반환 지점에서 최종 rows/ctx를 내보내기 전에 반드시 이 euler 정리를 거치고 그 결과로 audit을 다시 계산한다 -- 그래야 반환되는 audit이 실제로 저장/보고될 최종 물리 구조와 항상 일치한다".
- 실제 동작: `interdig_ok`는 **euler 정리 전** audit으로 먼저 채워지고(11800 루프 안, 11879 루프 뒤), 정리 뒤 audit으로는 덮어쓰지 않습니다(이미 채운 항목은 건너뜀).
- 재현(합성 입력, 현재 gate `a796468`과 B34 적용본 둘 다 같음): 한 행에 `Ma(n2→n1)`·`Mb(n4→n2)`·`Mp(n2→n5)`, 매칭 `Ma/Mb` offset, gm/ID 범위 11.9~12.1.
  - 반환 `interdig_ok` = **False**
  - 같은 반환의 `audit`에서 `3b. interdigitation[Ma/Mb]` = **True**
  - 반환 `rows` = `{seg1_seg0: [Mp], seg1_seg1: [Mb, Ma]}` -- 정리가 행을 나눠 Ma·Mb가 따로 한 행이 됐습니다. False는 나누기 전 행(Mp가 끼어 있던 행)의 판정입니다.
- 영향 범위: 이 값을 읽어 분기하는 운영 코드는 없습니다(`git grep`: 엔진 자신과 selftest의 `is not None` 단언 1곳). `optimize_full_circuit_budget`이 `pipeline_result["relaxed_pairs"]`로 그대로 보고합니다. library 9회로에서 실제로 달라지는지는 아직 재지 않았습니다(card의 auditor E-LIB 측정 몫).
- 경위: 완화·`interdig_ok`는 세션17, euler 정리(`_finalize`)는 세션31에 들어왔습니다. 세션17 기록(`.ai/context.md` 1558~1561)은 "`interdig_ok`가 False로 나오는 실제 사례는 아직 self-test로 확인 안 함"이라고 적었습니다.
- 왜 지금 묻는가: B26-1의 변이 검사에서 이 두 줄(11800·11879)을 지운 변이가 살아남습니다. 그런데 지운 쪽이 오히려 반환 audit과 맞는 값을 냅니다. 그래서 '지금 동작을 고정하는 test'로 죽이면 이 불일치를 정답으로 박게 됩니다.

**선택지**:
1. **(Recommended) 결함으로 고친다 -- red-green code card 1건을 b26pre test card 뒤, B26-1 앞에 둔다**
   - test: '반환 `interdig_ok`는 반환 audit의 3b 판정과 같다'(루프 안·루프 뒤 두 경로). 지금 엔진에서 실패하고(red), 고치면 통과합니다(green).
   - 수정 후보(사전 측정): 정리 전 backfill 두 줄을 지우고 정리 뒤 호출만 남김. 사본에서 red 2 failed → green 2 passed, `A/tests` 전체 회귀 없음(888 passed·15 xfailed, 실패 2개는 `.git` 없는 사본의 기존 환경 실패).
   - 효과: B26-1 변이 검사에서 이 두 줄의 생존 몫이 사라집니다(문장이 없어짐). 바뀌는 관찰값은 이 경우의 `interdig_ok` 하나입니다(행·audit·사유는 그대로).
   - 원칙 근거: 코드 주석에 적힌 의도와 반환값을 맞춤, 판정 기준 약화 없음, 거짓 기준값 금지.
2. 지금 동작을 그대로 고정한다(test로 `interdig_ok == False`를 박음) -- **권하지 않음**: 반환 audit과 어긋난 값을 정답으로 고정합니다.
3. 백로그로 두고, B26-1 변이 검사에서 이 두 변이를 '알려진 결함 생존'으로 남긴다 -- 별도 사용자 결정 기록이 필요하고(등가가 아니므로 '등가 면제' 문구는 쓸 수 없음), 불일치는 남습니다.

**1번이면 남길 승인 기록 문안**:
```
id: 20261001-b26-backfill-interdig-fix
date: <답한 날>
target_kind: decision
target: U-BF-BACKFILL-INTERDIG
scope: 결정 U-BF -- run_matching_safety_with_finger_growth의 relaxed_pairs[i]["interdig_ok"]를 반환 audit(euler 정리 뒤 최종 물리 구조)의 3b 판정으로 채우도록 수정(관찰 가능한 반환값 변경, spec card 20261001-b26-backfill-interdig-final-audit), 순서 b26pre 뒤·B26-1 앞
```
(본문) 사용자 원문 / 질문 / 덮는 것: 위 값 하나의 의미 변경과 그 card의 순서 / 덮지 않는 것: 완화 정책 자체(3c 요구 유지, `audit.ok` 판정), `relaxed_pairs`의 다른 키, V3·V7 면제 / 재검토: library 회로에서 값이 달라지는 사례가 나오면 판정 기록에 회로·쌍·전후 값을 적는다.
