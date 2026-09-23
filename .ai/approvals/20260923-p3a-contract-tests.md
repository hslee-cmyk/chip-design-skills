---
id: 20260923-p3a-contract-tests
date: 2026-09-23
target_kind: diff
target: 26a7059d056e39fdc06e287c50bfe4c39326841dd75ded8b6751aceba1407b23
diff_base: 23d03faea4f8582c411c61d94a1223c9e67a8a8a
diff_head: 586f93df2237a3ed8d1cc355518def9d624161f4
diff_path: skills/analog-gmid-design/assets/tests/contracts/test_ts6_dead_probes.py
diff_path: skills/analog-gmid-design/assets/tests/contracts/test_ts6_probe_relocate.py
scope: P3a -- P1·P2 계약 test 2개의 기대값을 승격 이름 규칙에서 유도하도록 바꾸는 DEC-40 승인(V5 발견 3건)
---

## 사용자 원문

> 규칙에서 유도하게 (Recommended)

## 범위 설명

덮는 것: 두 계약 test가 **승격 전 probe 집합을 기대값으로 굳혀 둔 것**을 규칙 유도로 바꾼다.
* `test_ts6_dead_probes.py::test_dead_probe_files_are_absent`: 잔존 probe 수를 `42 - 3`(=39)으로 박던 것을 `42 - 3 - 승격 완료분`으로. 승격 완료분은 이름 규칙(`A/tests/unit/test_<probe 이름>.py`)으로 센다 -- 승격한 수를 파일에 박지 않으므로 P3b 이후에도 그대로 성립한다.
* `test_ts6_probe_relocate.py::test_only_promotion_candidates_remain_in_tests_root`: 기대 집합을 승격 후보 7개 고정에서 `후보 - 승격 완료분`으로.
* 두 파일 모두 **양방향 배타 판정**이 새로 들어간다(승격본이 있으면 원본이 없어야 하고 그 반대도 성립) -- '옮기다 만 상태'를 잡는 판정이라 순 효과는 강화다. 합성 반례 test 2개가 그 판정이 실제로 거부하는 것을 보인다.
* auditor 측정(base 판 `weakening_diff.py`, 2026-09-23): 발견 3건(리터럴 변경 1 + docstring 교체 2), `diff_hash` 위 `target` 값, `diff_paths` 위 두 경로. 해시는 blob 기반이라 base를 옮겨도 두 파일 내용이 같으면 그대로다.

**계약 7-a**: spec card `20260923-probe-promote-clean`은 원래 "다른 probe·test도 바뀌지 않는다"였다. 승격이 앞선 card의 파일 집합 사실을 거짓으로 만들기 때문에 그 문언을 계약 7-a로 고쳤고, 이 승인이 그 예외를 덮는다.

덮지 않는 것: 판정 약화(없다 -- auditor가 발견마다 대조한다), 다른 test 파일, 엔진 소스, probe 승격 자체(U-02 승인 `20260923-u02-d-list`가 덮는다).

## 재검토

P3b·P3c에서 승격이 더 일어나도 이 두 test는 규칙 유도라 다시 고칠 필요가 없다. 규칙 자체(이름 규칙 `unit/test_<probe 이름>.py`)를 바꾸려면 그때 다시 승인받는다.
