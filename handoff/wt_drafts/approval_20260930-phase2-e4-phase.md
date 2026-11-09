---
id: 20260930-phase2-e4-phase
date: 2026-10-01
target_kind: diff
target: <weakening_diff.diff_hash -- 정정 커밋 뒤 계산>
diff_base: <git rev-parse 정정 커밋의 부모>
diff_head: <git rev-parse 정정 커밋>
diff_path: docs/02-design/features/gain-budget-gmid-sizing.20-dead-code-dup.design.md
scope: design 20-dead-code-dup §10 E4(Phase 2 DoD 동작 보존)의 PT 실행을 --gmid-phase=2 실행과 --gmid-dod 실행 두 개로 고정하는 정정 승인 -- Phase 2 완료 판정 착수 조건
---

## 사용자 원문

> phase=2 + dod 실행 (Recommended)

(AskUserQuestion 선택지 답, 2026-10-01. 질문 원문은 대화 기록에 그대로 남아 있지 않아 **재구성**했다 -- 출처는 질문 준비 문서 `_drafts/decision_package.md` A3과
`_drafts/draft_e4_clarify.md` 3항이다. 재구성한 질문: "Phase 2 DoD E4의 `PT`를 `--gmid-phase=2`로 읽고 `--gmid-dod` 실행을 E4에 더하는가? design 20 §10은
10 §10의 PT 정의(`--gmid-phase=1`)를 '그대로' 쓰라고 하는데, phase 값에 따라 xfail 조건과 엄격 집합이 달라지므로 판정 기준을 바꾸는 일이다." 선택지는
"phase=2 + dod 실행"(권고 -- 드라이런 `_drafts/dryrun_phase2_e4.md`에서 두 실행 모두 798 passed·15 xfailed·실패 0, 증거 아님)과 "문언대로 `--gmid-phase=1`"(재지 않음,
Phase 1 DoD용 정의라 Phase 2 검사가 아니고 브리핑과 설계서의 `--gmid-dod` 불일치가 남음)이었다. 같은 커밋에 넣는 절차 보강(스크립트 출처, `-B -P`)은 승인이 필요 없는
명확화로 함께 안내했다. 교체 문안은 `_drafts/patch_e4_phase.py`가 정정 커밋에 그대로 반영한다.)

## 범위 설명

덮는 것: design 20 §10 E4 행의 `PT` 실행 정의 변경 -- 옛 '`PT` 전체'(§10 머리에 따라 10 §10의 `--gmid-phase=1`)를 `PT2`(10 §10 `PT` 정의에서 `--gmid-phase=1`만
`--gmid-phase=2`로 바꾼 것) 전체 실행과 `PT2 --gmid-dod` 전체 실행 두 개로 바꾸고, 통과 기준을 '두 실행 모두 실패 0'으로 바꾼다 -- 판정 기준 변경. 이를 가리키도록
§10 머리 문장에 'E4는 `PT2`로 실행한다' 한 문장을 더한다. 같은 커밋의 절차 명확화(기준 변경 아님): 세 측정 스크립트(e_lib.py·e_inst_df35.py·e_inst_df36.py)는
da03c0e 판에 없으므로 Phase 2 마지막 card 병합본 판에서 `<iso>` 밖으로 복사한 같은 사본(sha256 기록)을 두 판에 쓰고, `<out>`은 `<iso>` 밖, 실행은 `$PY -B -P`.
덮지 않는 것: E0~E3·E5(§10 머리의 `PT` = 10 §10 정의 그대로는 E1·E5에 그대로 남는다), E4의 E-LIB·E-INST 비교 기준(승인 `20260930-phase2-e4-baseline` 그대로),
design 10 §10 `PT` 정의, 계획 N6.2 문장, conftest `--gmid-*` 옵션 동작.
