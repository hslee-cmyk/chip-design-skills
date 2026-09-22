---
id: 20260922-ts5-baseline-retire
date: 2026-09-22
target_kind: diff
target: ff0e5addf1d4538f3ddaa513b041b9e9d9eb2756bf2ba61879e48f0b9c8ab047
diff_base: 7781bde50cfe67802359e5ebf05b35640c5606e1
diff_head: 7a4bab94b50c6004aee426bba556d7cc9f84c10f
diff_path: skills/analog-gmid-design/assets/tests/README.md
diff_path: skills/analog-gmid-design/assets/tests/baseline/README.md
diff_path: skills/analog-gmid-design/assets/tests/baseline/sizing_recipe.selftest.baseline.log
diff_path: skills/analog-gmid-design/assets/tests/baseline/stick_diagram.selftest.baseline.log
scope: C5 TS5 -- stdout 기준선 3파일 삭제와 tests/README.md 추가의 DEC-40 승인(V5 발견 4건)
---

## 사용자 원문

> 승인, 드리프트는 DF 안 함 (Recommended)

## 범위 설명

덮는 것: `tests/baseline/` 세 파일 삭제(README 160줄, sizing 기준선 361줄, stick 기준선 1257줄)와 `tests/README.md` 추가(blob 6af3d27c).
sizing 기준선은 HEAD 출력과 45줄 어긋난 채 갱신되지 않은 드리프트를 담고 있었고 그 사실을 승인 요청에 적었다 -- 사용자는 DF로 올리지
않기로 했다(판정은 assert가 한다, 대조할 기준선이 없어진다). 2차 시도는 R1대로 README blob을 `v5-carry/20260922-ts5-baseline-retire/`에서 복원한다.
덮지 않는 것: `.gitignore` 기준선 예외 3줄 삭제(U-43, 사용자 `Role: user` 커밋), references 실행 안내 수정(오케스트레이터, 정리 뒤).
