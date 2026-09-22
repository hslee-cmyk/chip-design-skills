---
id: 20260922-10-test-separation-design
date: 2026-09-22
target_kind: diff
target: 64875c305528510d0cc02b9e7d51f7ee55afad114863e8ab1001596cbe0641ed
diff_base: 89d257c3c332158697389c9b10195b210f2ae03b
diff_head: 475c6476b3a447de34cb5a5dbfcfb16265a093be
diff_path: docs/01-plan/features/gain-budget-gmid-sizing.history.md
diff_path: docs/01-plan/features/gain-budget-gmid-sizing.plan.md
diff_path: docs/02-design/features/gain-budget-gmid-sizing.00-common.design.md
diff_path: docs/02-design/features/gain-budget-gmid-sizing.05-role-separation.design.md
diff_path: docs/02-design/features/gain-budget-gmid-sizing.10-test-separation.design.md
scope: design 10-test-separation v1.2 승인(DEC-51)과 그것이 기댄 개정(계획 P1~P5·U-41~U-43, 00-common C1·C2, 05 R1·R2)
---

## 사용자 원문

> 승인 + U 기본안 (Recommended)

> 진행해

(질문: design `10-test-separation` v1.2와 개정 요청, 열린 질문 U-41~U-43을 어떻게 할지 -- 검토 기록 review1·review2.)

## 범위 설명

덮는 것: design v1.2 전체(spec card C1~C11과 순서), 계획 N3.11 TS1·TS0·TS5 행과 트리 `tooling/`, N3.12.3 test 전용 목록, N6.1 `1`
행 판정 유형 문구, N7.2 U-41(데모 18개 삭제)·U-42(V5 승인 운반 채택)·U-43(C5 뒤 사용자가 `.gitignore` 3줄 삭제), `00-common` §5
`없음(배치)`·§14 CC-3 유형, `05` §12 'V5 승인 운반' 행·§18 test-only 게이트 변경 문구, history 한 줄. 판정 표 해시 불변(`7167e028…`).

덮지 않는 것: 각 spec card의 V5 기준 약화 승인(DEC-40 -- card마다 따로), `.gitignore` 삭제 자체(사용자 커밋).
