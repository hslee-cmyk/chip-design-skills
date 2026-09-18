---
id: 20260918-00-common-design
date: 2026-09-18
target_kind: diff
target: 2539c96baf843a6405a77a6816b30727f19f9b399369769939d33f00690e5951
diff_base: 9f4e3e15591d99feec25fe18309e24ae60854a8f
diff_head: 5b6d985954ae6dd154797318b8289fd6fa57819f
diff_path: .ai/approvals/_TEMPLATE.md
diff_path: .ai/verification/_schema.json
diff_path: docs/01-plan/features/gain-budget-gmid-sizing.history.md
diff_path: docs/01-plan/features/gain-budget-gmid-sizing.plan.md
diff_path: docs/02-design/features/gain-budget-gmid-sizing.00-common.design.md
scope: 00-common design v1.7과 그것이 기댄 계획 v5.19 개정·history·판정 기록 스키마·승인 기록 양식 승인(DEC-51)
---

## 사용자 원문

> 승인할게. 승인 기록 만들고 05로 가자

## 범위 설명

덮는 것: `diff_base`(9f4e3e1, 00-common 착수 직전) → `diff_head`(5b6d985, 00-common v1.7) 사이의 위 다섯 파일 내용.
00-common design v1.7(구성안 C + 판정 표 사본 제거 정정), 계획서 v5.19 개정(SCHEMA_REJECTED, spec card Phase·무동작 판정 입력·
활성화 IC 케이스 필드, DF-35~37, N4.3 공격 15·16, EL3·EL4 판정 표 검사, Phase 4 순서 등), history 기록, `.ai/verification/_schema.json`,
`.ai/approvals/_TEMPLATE.md`.

덮지 않는 것: 이 범위 밖 파일, `diff_head` 뒤의 변경. `00-common` §17이 `05-role-separation` 등으로 넘긴 구현 세부는 각 design의
승인으로 확정한다.

diff 해시는 `00-common` §8.2의 blob 기반 식으로 계산했다(경로별 `path\tbase_blob\thead_blob\n`를 정렬해 이은 UTF-8 바이트의 sha256).
