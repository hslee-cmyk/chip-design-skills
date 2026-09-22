---
id: 20260922-ts7-conftest
date: 2026-09-22
target_kind: diff
target: 9feedcc187a2d6d38dfa6e60610d3828f38822d78b592e0d4b2f99cd5a2124b2
diff_base: b3470edfc98e91cffd871e33dfa056abf957bba3
diff_head: 2d31216370d4b24ce51d0c9de243e45bb05c35a7
diff_path: skills/analog-gmid-design/assets/tests/README.md
diff_path: skills/analog-gmid-design/assets/tests/conftest.py
scope: C6 TS7/CC-3 -- tests/conftest.py 신설(--gmid-phase·--gmid-strict·--gmid-dod, gmid_ic 표식, 계획서 N4.1 xfail)과 README 현황 한 줄의 DEC-40 승인
---

## 사용자 원문

> 모두 승인 (Recommended)

(질문: conftest 신설(blob c8c701d9)과 README 한 줄(blob a0e788db), design에 없던 보수적 거부 두 가지 -- 표식 둘 이상, 표식 인자 형식·
phase 범위 -- 와 `--help` 예외를 DEC-40으로 승인하는지. 정상 흐름에서 추가 거부 발동 0을 auditor가 확인.)

## 범위 설명

덮는 것: 위 두 경로의 base -> head blob. 2차 시도는 R1대로 `v5-carry/20260922-ts7-ic-xfail/`의 blob 14개(발견 2 + contracts 12)를 복원한다.
덮지 않는 것: 이후 conftest 변경(C9 셔플·fixture 등은 그때 다시 승인).
