---
id: 20260930-v3-exempt-binding
date: 2026-10-01
target_kind: diff
target: <rev-parse>
diff_base: <rev-parse>
diff_head: <rev-parse>
diff_path: docs/01-plan/features/gain-budget-gmid-sizing.plan.md
diff_path: docs/02-design/features/gain-budget-gmid-sizing.05-role-separation.design.md
diff_path: docs/02-design/features/gain-budget-gmid-sizing.10-test-separation.design.md
diff_path: docs/02-design/specs/20260930-v3-exempt-binding.interface.md
diff_path: docs/02-design/specs/20260930-v3-exempt-binding.spec.md
scope: 게이트 변경 spec card 20260930-v3-exempt-binding(V3 등가 변이 면제 원소 = 변이 id@묶기 해시, head def 묶기 해시가 같을 때만 적용, 해시 없음·다름·형식 오류는 적용하지 않고 exempt_ignored 출력, exempt를 --out에 기록)과 design 05 §10 V3 ⑤·design 10 §6.7 382행·계획 N4.2 V3 면제 문구 개정 승인 -- 강화
---

## 사용자 원문

> 승인 (Recommended)

(AskUserQuestion 질문·답 기록 원문 -- 오케스트레이터 사용자 결정 기록 `_drafts/user_decisions.md` '2026-10-01 A1 (AskUserQuestion 답)' 절 A1-a 항목 그대로:
"A1-a "승인 (Recommended)" -- V3 면제 누수 수정 게이트 변경 `20260930-v3-exempt-binding`(면제 = 변이 id@함수 원본 해시(docstring·데코레이터 포함), 해시 같을 때만 적용; 근거 DF-36 면제 4개가 save_instance_json 변경 뒤 C8 승인 적용). 승인 기록 target_kind diff(spec card + interface card + design 05 문구 커밋). 순서 P9·P10·P10b 뒤, B26-1 전."
AskUserQuestion에 실은 질문 문안은 그 기록과 `_drafts/draft_v3_decision_question.md` '함께 드리는 승인 요청' 절에 남아 있다.)

(질문 2026-10-01 A1-a: V3 면제 누수 수정 게이트 변경 `20260930-v3-exempt-binding` 승인 -- 면제 = 변이 id@함수 원본 해시(docstring·데코레이터 포함), 해시 같을 때만 적용.
근거로 DF-36 판정(`148bd6d`)의 V3 PASS가 `save_instance_json` 변경 뒤에도 적용된 C8 면제 4개에 기댔다는 실측을 함께 알렸다. 결정 질문 문안 `_drafts/draft_v3_decision_question.md` '함께 드리는 승인 요청':
기존 C8 면제 14개는 더는 적용되지 않음(앞으로의 card 기준 무손실), 재시도에서 def를 고치면 시도마다 재승인, Python 판을 올리면 묶인 면제가 풀릴 수 있음(fail-closed).
선택지 '승인 (Recommended)': 승인 기록 target_kind diff(spec card + interface card + design 05 문구 커밋), 순서 P9·P10·P10b 뒤, B26-1 전.)

## 범위 설명

덮는 것:
* spec card `20260930-v3-exempt-binding` 전체(계약 1~11)와 interface card. 강화 -- 면제 적용 범위가 줄고 거부 집합이 넓어진다. 기존 `20260922-ic3-v3-exempt`의 V3 원소 14개(`load_topology` 10,
  `save_instance_json` 4)는 해시가 없어 더는 적용되지 않는다(fail-closed 이행. 기존 승인 기록은 고치지 않는다). 이 14개가 V3 대상 영역의 해시 없는 V3 모양 원소 전부라는 것은 spec card
  '작성 전 실측' 1의 집계 명령(`v3_decision_census.py`)으로 쟀다(measured at gate `master` `0f23786`: decision 기록 13, 원소 36, V3 모양 23 = 대상 영역 14 + 대상 영역 밖 9).
* 묶기 해시 = head def 노드 원본(docstring·데코레이터 포함)의 `ast.dump(annotate_fields=True, include_attributes=False, indent=None, show_empty=False)` sha256, gate 인터프리터(3.14)로 잰다.
  인터프리터 판을 올려 해시가 바뀌면 묶인 면제는 `hash_mismatch`로 풀리고, 필요한 면제는 다시 승인한다.
* 운영 비용: 승인한 def를 재시도에서 고치면(docstring만 고쳐도) 면제가 풀려 시도마다 재승인이 필요하다(의도된 동작).
* 실수 상수 변이의 등가 승인은 표기와 무관한 경우에만 한다(묶기 해시는 같은 노드를 보장하고, 변이 값은 원문 표기 단위에서 나온다 -- card 계약 11).
* 출력 변경: V3 출력 JSON에 `survivor_bindings`·`exempt_ignored`, `exempt` 결과의 `--out` 기록(WP-11 기록 누락 수정).
* redteam `lib/rt.py` 실행 동작 두 개 추가(test-author, 선례 C10 `20260923-caa970b-replay`): 자리표시자 `@bindhash(<base|head>:<경로>:<qualname>)`(피검 모듈 import 없이 표준 라이브러리로 계산),
  관찰 `"observe": "out_jsonl"`(`--out` 파일의 줄 수와 killed·survived 아닌 결과별 id 목록). 새 케이스 `attacks/34-v3-exempt-binding/`(D-18 배정 번호).
* 문서: design 05 §10 V3 행 ⑤ 면제 문구, design 10 §6.7 IC3(C8) 항목 382행 끝 문장(원소 형식을 design 05 ⑤로 넘김), 계획 N4.2 V3 행 "등가 변이 면제는 승인 기록으로만(변이 id와 그 def의 AST 묶기
  해시에 묶임)", `mutate_changed.py` 모듈 docstring ⑤.

덮지 않는 것:
* V3 대상 선택(①)·연산자·인벤토리 -- 범위 정책은 별도 승인 `20260930-v3-changed-stmt-scope`.
* V4(`test_lint.py`)·V7(`reachability.py`) 면제의 묶기, `reachability._approved_ids` 동작 -- 바꾸지 않는다(백로그).
* auditor 보충 뮤테이션 면제(V3 대상 영역 밖 파일 -- 예 `20261001-p10b-v3-equiv`의 `tests/tools/reg_check.py` 변이 id 9개): 도구가 그 변이를 만들지 않으므로(`reachability._is_source` 밖) 이 card의
  규칙이 닿지 않고 출력에도 실리지 않는다. 그 기록은 고치지 않고, 적용은 그 기록 범위 설명대로 auditor 판정이다. 묶는 규칙은 백로그.
* 이미 내려진 DF-36 V3 판정(`148bd6d`) -- 바꾸지 않는다. `save_instance_json` 면제 id 4개의 실제 실행 확인은 백로그 B41.
* 판정 표(`plan_tables_hash` 입력) -- N4.2 V3 칸은 입력이 아니다(`v_intro`는 '도입' 칸만). 바뀌면 이 승인이 아니라 `plan_tables` 승인이 필요하다.

<!-- 오케스트레이터: target·diff_base·diff_head는 문서 커밋 뒤 rev-parse와 00-common §8.2 diff 해시 명령으로 채운다. diff_path는 그 커밋에서 실제로 바뀐 경로만 남긴다(바뀌지 않은 경로는 파서가 거부).
     집계 문장('덮는 것' 첫 항목): 승인 기록 커밋 직전에 `C:/Python314/python.exe -B <wt>/_drafts/v3_scripts/v3_decision_census.py --repo <R> --rev "$(git -C <R> rev-parse gate/master)" --out <scratch>/census.txt`를
     다시 돌린다. 수치가 달라졌으면 `0f23786`과 13·36·23·14·9를 그 rev 앞 7자와 출력으로 바꾼다(`fill_v3_approval.py`는 이 문장을 검사하지 않는다 -- 손으로 맞춘다).
     대상 영역 수가 14가 아니거나 `@` 접미사 원소가 생기면 spec card 이행 근거부터 고친다. -->
