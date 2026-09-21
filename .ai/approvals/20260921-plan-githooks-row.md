---
id: 20260921-plan-githooks-row
date: 2026-09-21
target_kind: plan_tables
target: 7167e02839f86c4ecbcd91a63a9833c4d83a8aab8008bfe2d8cfc36206d2596d
scope: 계획 N3.12.2 쓰기 경로표에 gmid-code-author의 tools/gates/githooks/** (게이트 변경) 행 추가 -- dispute D-9 해소
---

## 사용자 원문

> 승인

(질문: N3.12.2에 `| gmid-code-author | tools/gates/githooks/** | -- | 게이트 변경 |` 행 추가와 N3.12.6 산출물 '게이트·검사 도구'
행에 `tools/gates/githooks/{pre-commit,commit-msg,pre-merge-commit,gmid_gate.py}` 추가, 판정 표 해시 `cec77b63…` -> `7167e028…`를
승인하는지. 선택지 '승인'을 골랐다.)

## 범위 설명

덮는 것: 위 판정 표 값(쓰기 경로표 한 행 추가)과 같은 커밋의 N3.12.6 산출물 문구. 계기는 게이트 변경
`20260921-gate-output-utf8` §12 2차 시도의 code-author dispute(blob `51c743d95a17f8a0a92f651b830f51d3b77955f8`).

덮지 않는 것: `.githooks/**`(설치 사본)의 쓰기 주체 -- 계속 사용자만. D-7·D-3·D-8 수정(다음 게이트 변경).
