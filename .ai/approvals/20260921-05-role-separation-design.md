---
id: 20260921-05-role-separation-design
date: 2026-09-21
target_kind: diff
target: 3bc389ec4004c75b363016cd55e2fea77b110e9aaa91352b8666c12618590afd
diff_base: e2a8f032b3304acd5da47c42d5dfffdab14d9428
diff_head: 545801172733097cd668662fd2fb6b9dcc330734
diff_path: docs/01-plan/features/gain-budget-gmid-sizing.history.md
diff_path: docs/01-plan/features/gain-budget-gmid-sizing.plan.md
diff_path: docs/02-design/features/gain-budget-gmid-sizing.00-common.design.md
diff_path: docs/02-design/features/gain-budget-gmid-sizing.05-role-separation.design.md
scope: 05-role-separation design v3.6과 그것이 기댄 00-common v1.8·계획 v5.19 개정·history 승인(DEC-51)
---

## 사용자 원문

> U-39는 기본안대로 하고 05 승인할게

## 범위 설명

덮는 것: `diff_base`(e2a8f03, 00-common 승인 기록 커밋) → `diff_head`(5458011, 05 v3.6 마감) 사이의 위 네 파일 내용.
05-role-separation design v3.6(위협 범위 C, EL1~EL4 배치와 EL4 = 로컬 gate `pre-receive`, 무결성 대조, 역할-worktree 결합,
변경 한 건의 명령 시퀀스, auditor 검사 도구 V3~V7, 부트스트랩 ①~⑤와 공격 재생 28건, 알려진 한계 §13.5),
00-common v1.8 개정(05에 따른 §8·§9 개정), 계획서 v5.19에 이 기간 들어간 개정(N3.12.0 위협 범위, 쓰기 경로표,
EL1~EL4, N4.3 공격 목록, WP-22 등), history 기록.

덮지 않는 것: 이 범위 밖 파일(`docs/03-analysis/**` 검증 원자료 포함), `diff_head` 뒤의 변경. 부트스트랩 ③의 승인 기록 두 개
(부트스트랩 산출물, 최초 판정 표)는 공격 재생 로그를 본 뒤 따로 만든다. `gmid-*` `agent_type` 값은 ③·⑤ 실측으로 확정한다.

diff 해시는 `00-common` §8.2의 blob 기반 식으로 계산했다(경로별 `path\tbase_blob\thead_blob\n`를 정렬해 이은 UTF-8 바이트의 sha256).
