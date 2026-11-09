---
id: 20261007-b26-v4-exempt
date: 2026-10-07
target_kind: decision
target: skills/analog-gmid-design/assets/tests/unit/test_selftest_stick_diagram.py::test_s133_refine_differential_and_mirror_relations, skills/analog-gmid-design/assets/tests/unit/test_selftest_stick_diagram.py::test_s134__propose_vertical_stack_ids, skills/analog-gmid-design/assets/tests/unit/test_selftest_stick_diagram.py::test_s135_section, skills/analog-gmid-design/assets/tests/unit/test_selftest_stick_diagram.py::test_s159_apply_device_roles_gap_fill
scope: B26-1(spec card 20260930-b26-rail-accessor-set) -- 계약 12로 바뀌는 SD selftest의 기존 이관 test 4개를 V4 규칙 (1)에서 면제(같은 피검 출력 안 두 값 비교 7건, B1에 이미 있던 판정), 재검토 줄 포함
---

## 사용자 원문

> (가′) 면제 + 재검토 줄 (Recommended)

(질문 2026-10-07 14:59 KST, 답 2026-10-07 15:00 KST(세션 jsonl `63c6146a-ab1d-4035-a169-bae810986922` AskUserQuestion `toolu_01MGv1L1nfGzLcPrjMTk5A44`, 질문 2개 중 [B26-1 V4]). 질문 원문(고치지 않고 그대로): "[B26-1 V4 면제] unit/test_selftest_stick_diagram.py의 기존 이관 test 4개(test_s133_refine_differential_and_mirror_relations · test_s134__propose_vertical_stack_ids · test_s135_section · test_s159_apply_device_roles_gap_fill)를 V4 규칙 (1)에서 면제하는 decision 기록을 받고, 기록에 재검토 줄(T1에서 id가 바뀔 때 4개 각각 리터럴 기대값으로 고칠 수 있으면 고치고, 정당한 불변식만 면제를 다시 받는다)과 백로그 항목을 넣습니다. 이대로 진행할까요?"
선택지: "(가′) 면제 + 재검토 줄 (Recommended)" -- "지금은 면제 기록으로 B26-1을 진행하고, T1에서 고칠지/면제를 다시 받을지 test별로 정한다." / "(나) B26-1에서 고침" -- "card 계약 개정 + V5 승인으로 4개 test 단언을 지금 고친다(범위 커짐).".)

## 범위 설명

근거: 네 test는 B26-1이 만든 기대값이 아니라 C9(`20260922-ts2-pytest-split`)가 이관본 `legacy/selftest_stick_diagram.py`(원본 `stick_diagram.py`의 `if __name__ == "__main__":` 블록)의 판정을 그대로 옮긴 것이다(파일 머리 docstring "새 기대값은 없다").
B26-1 계약 12는 이 파일의 계약 4 함수 호출 49곳에 `rails=`를 더하고 로드 경로 픽스처 3곳에 `supply_nets`를 더한다(판정·기대값은 바꾸지 않는다). V4(`test_lint.py`)는 base..head에서 바뀐 test 파일을 **파일 전체** lint하므로,
그 파일에 있던 규칙 (1) 발견(지역 대입 인라인 뒤 판정 양쪽에 같은 피검 호출이 남음 -- 한 번 부른 피검 출력 안의 두 값을 서로 비교)이 B26-1의 V4 FAIL로 잡힌다.
실측(gate `6df4bd7` 판 `test_lint.py`, interface card `20260930-b26-rail-accessor-set.interface.md`): B1 `6df4bd7`의 그 파일 줄 `test_s133_refine_differential_and_mirror_relations` 3090·3092·3094·3096, `test_s134__propose_vertical_stack_ids` 3129,
`test_s135_section` 3153, `test_s159_apply_device_roles_gap_fill` 3926 -- 1차 시도 test 커밋 T1(`c247a76`)에서는 같은 일곱 발견이 3120·3122·3124·3126·3159·3183·3956(입력 갱신으로 줄만 밀림, 2026-10-07 모래상자 측정). 그 밖 바뀐 test 파일의 규칙 (1) FAIL 0
(`unit/test_selftest_sizing_recipe.py`의 `test_s052_compensation`·`test_s054_section`은 기존 승인 `20260923-c9-v4-exempt`로 이미 `exempt`).
첫 질문(같은 세션 `toolu_01PjnFQKcAdM5hJ6uKNj4LNh`, 2026-10-07 14:01 KST)은 사용자가 되물어 답 없이 끝났고, 재검토 줄과 백로그를 넣은 위 질문으로 다시 받았다.
덮는 것: 위 네 test id의 **규칙 (1)** 발견만(면제 경로는 C13 `20260923-v4-decision-exempt` -- head 트리의 decision 기록 target 목록에 `<파일>::<test 이름>`이 있으면 그 발견의 output을 FAIL 대신 `exempt`로). 발견은 `output: exempt`로 출력 JSON과 판정 기록에 남는다.
덮지 않는 것: 다른 test, 같은 test의 다른 규칙((2)~(5)), B26-1이 새로 쓰거나 판정을 바꾼 줄에서 나는 발견, 이름·경로가 바뀐 뒤의 같은 판정(그때는 면제가 저절로 풀린다).

## 재검토

T1(test 재배치)에서 이 네 test의 id가 바뀌어 면제가 풀릴 때 test별로 다시 본다: 리터럴 기대값으로 고칠 수 있으면 고치고(그 수정은 V5 승인 대상), 정당한 관계 불변식(같은 출력 안 두 값이 같아야 한다는 것 자체가 계약인 경우)만 새 id로 면제를 다시 받는다. 백로그 B67.
