---
id: 20260923-20-dead-code-dup-design
date: 2026-09-23
target_kind: diff
target: 71e29a4a9973b0c8936680f18fedda46bcc0451ba6fcab96bf90fb85f04cc04d
diff_base: 1e2e243d192b93befacb52647455c02900c9734f
diff_head: 6a900f568018fa28c4c07d961a7c5435db94eff3
diff_path: docs/02-design/features/gain-budget-gmid-sizing.20-dead-code-dup.design.md
scope: Phase 2 design `20-dead-code-dup` v1.1 승인(DEC-51) -- 삭제 판정의 일반성 기준 G-1~G-4와 NEW-TOPO 판정식 포함
---

## 사용자 원문

> 현재에 있는 회로만으로 삭제여부를 결정하지 말고, 향후 추가되는 모든 topology를 커버할 수 있도록 설계되어야 해.

> 승인, 진행해

## 범위 설명

덮는 것: design `20-dead-code-dup` v1.1 전체(6a900f5). 범위·인터페이스·판정식(E-LIB·E-INST·E-AST·DIFF-DUP·GONE·PROBE-DUP·REG·
NEW-TOPO)·실패 경로·spec card 목록 11건(P1~P10, P5b 포함)·DoD 측정 명령(E0~E5)·착수 조건. 실측 원자료는 같은 커밋 계열의
`docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/`(acad7c8).
v1.1의 핵심: 삭제는 §6.4의 G-1~G-4(선언 도달 경로 없음·코드 참조 없음·일반 대체가 있거나 애초에 일반화 불가·삭제 뒤 명시적 거부)를
모두 만족할 때만 하고, 삭제 card는 라이브러리 밖 합성 topology로 NEW-TOPO를 낸다. 선언으로 도달 가능한데 일반 대체가 없는 항목은
현재 회로가 안 쓰더라도 보류한다.
덮지 않는 것: U-02 항목별 처리(별도 기록 `20260923-u02-d-list`), 계획서 DF 표 개정(아직 요청 상태 -- design §11), 동작이 바뀌는 수정.
