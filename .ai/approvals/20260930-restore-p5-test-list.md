---
id: 20260930-restore-p5-test-list
date: 2026-09-30
target_kind: diff
target: 4dcd62889b4facd6fcee26a9a9ce9c5f6831105e5be5f5dd1cf1a940224fb0ba
diff_base: bf407c7430ca7a9a6b1cea5c646de2b975da0167
diff_head: 5db0187aeccf34aea7e7712a6f1260fb3e4a4473
diff_path: skills/analog-gmid-design/assets/tests/contracts/test_d_delete_dead.py
scope: 복원 card 20260930-restore-plan-functions -- P5 계약 test에서 복원하는 두 이름을 삭제 목록에서 빼고 자기 점검 합성 케이스 6개를 남은 삭제 이름으로 바꾸는 DEC-40 승인(V5 발견 4건)
---

## 사용자 원문

> 승인

(질문: 복원 card V5 승인 -- P5 계약 test(test_d_delete_dead.py)에서 복원하는 두 이름(lut_conditions_from_npz·derived_spec)을 삭제 목록에서 빼고, 그 이름을
예시로 쓰던 판정기 자기 점검 케이스 6개를 남은 삭제 이름(slew_rate 등)으로 바꾼 변경(diff_hash 4dcd6288…, 남은 6개 판정과 assert 삭제 0) -- 선택지 '승인'.
앞서 사용자: "1번으로 되살리는 card 만들어서 진행해", 복원 범위 "계획 지정 2개만")

## 범위 설명

덮는 것: 위 diff_path의 base→head blob 변경 -- `_DELETED_FUNCTIONS`에서 두 이름 제거(G-1 dict 값·런타임 레지스트리·GONE AST 판정 대상 8→6), 두 이름을 담은
`_RESTORED_NAMES`로 G-4 미등록 metric type 케이스 id 유지, 자기 점검 합성 케이스 6개의 이름 교체(판정 형태 동일), docstring·주석의 개수 문구.
덮지 않는 것: 남은 6개 이름의 판정 변경, assert·skip·xfail·허용오차 변경, 다른 test 파일, 이 blob과 다른 내용.
diff_head 5db0187은 1차 시도 test 브랜치 끝이다(정리됨, blob은 `docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/v5-carry/20260930-restore-plan-functions/`에 운반).
