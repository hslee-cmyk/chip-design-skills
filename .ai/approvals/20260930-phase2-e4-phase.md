---
id: 20260930-phase2-e4-phase
date: 2026-10-01
target_kind: diff
target: 611dbc399db7d919d4d6bbf639c5cf091beb68c190d770a002ef424284d1d484
diff_base: b8d4c4d4cf3043f83fc82d67eb2e371126db67be
diff_head: fe638abbdc5f18195a846738d9c4c76c2f65cf94
diff_path: docs/02-design/features/gain-budget-gmid-sizing.20-dead-code-dup.design.md
scope: design 20-dead-code-dup §10 E4(Phase 2 DoD 동작 보존)의 PT 실행을 --gmid-phase=2 실행과 --gmid-dod 실행 두 개로 고정하는 정정 승인 -- Phase 2 완료 판정 착수 조건
---

## 사용자 원문

> phase=2 + dod 실행 (Recommended)

(AskUserQuestion 질문 원문, 2026-10-01: "[A3] Phase 2 완료 판정 E4의 전체 test(PT)를 어느 Phase 옵션으로 돌릴까요? 설계서 20이 인용하는 PT 정의에는
--gmid-phase=1이 박혀 있지만, Phase 2 완료 판정이므로 --gmid-phase=2로 읽고 --gmid-dod 실행을 하나 더하는 것이 기본안입니다. 사전 점검에서는 두 실행 모두
798 passed, 15 xfailed였습니다. 판정 기준 문구가 바뀌므로 승인 기록이 필요합니다. 스크립트 출처와 python -B -P 옵션을 명시하는 절차 보강도 같은 커밋에
넣습니다." 선택지: "phase=2 + dod 실행 (Recommended)" / "phase=1 그대로".)

## 범위 설명

덮는 것: design 20 §10 머리에 "E4는 `--gmid-phase=1`만 `--gmid-phase=2`로 바꾼 `PT2`로 실행한다" 한 문장 추가, E4 행의 명령·통과 기준을 `PT2` 전체와
`PT2 --gmid-dod` 전체 두 실행(모두 실패 0)으로 고정, 절차 명확화(세 측정 스크립트를 병합본 판에서 `<iso>` 밖으로 복사해 sha256 기록 후 두 판에 같은 사본 사용,
`<out>`도 `<iso>` 밖, `C:\Python314\python.exe -B -P`) -- 판정 기준 변경.
덮지 않는 것: E0~E3·E5(이들은 design 10 §10 `PT` 그대로), E4의 E-LIB·E-INST 기준(승인 `20260930-phase2-e4-baseline`), design 10 §10, 계획 N6.2.
