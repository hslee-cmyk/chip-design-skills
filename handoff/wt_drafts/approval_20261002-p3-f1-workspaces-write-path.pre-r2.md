---
id: 20261002-p3-f1-workspaces-write-path
date: 2026-10-02
target_kind: plan_tables
target: 31828c5e059dd41ed7a89f4d8757c402f9f7a61340411444d8101855f0623b57
scope: 계획 N3.12.2 쓰기 경로표에 gmid-code-author의 `workspaces/*/**/*.py`(제외 glob 없음, 조건 없음) 행 하나 추가 -- Phase 3 F1(`20261002-p3-callers-update`) code 커밋이 workspaces 하위 폴더 진단 스크립트(모의 16개)의 shim import를 정의 모듈로 고친다([F1] 쓰기 경로 답 (가), review_p3_f12 S2·S3 해소)
---

## 사용자 원문

> (가) 쓰기 경로표에 행 추가 (Recommended)

(AskUserQuestion 한 질문의 답이다. 질문 2026-10-02 14:30 KST(`2026-10-02T05:30:10.108Z`), 답 2026-10-02 14:32 KST(`2026-10-02T05:32:16.443Z`) -- 세션 기록
`63c6146a-ab1d-4035-a169-bae810986922.jsonl`의 tool_use `toolu_01PokFaLT31S8ep6tYfPQJmx`(uuid `c5b9d12d-5d65-4d05-a940-466ba20d30e2`, header `[F1] 쓰기 경로`)와
그 tool_result(uuid `fe2c1b04-1a26-4c79-83ee-af5c68933e35`)에서 프로그램으로 바이트 대조해 옮겼다(아래 따옴표 안은 jsonl 문자열 그대로 -- 고치지 않았다).
같은 header의 AskUserQuestion은 이 세션에 이 한 건뿐이다.)

* 질문 [F1] 쓰기 경로 원문: "[F1] shim 삭제 전에 고쳐야 하는 추적 파일 중 workspaces 하위 폴더 진단 스크립트 16개(current-reuse 12·two-stage 4, 덮어쓰기 계측 2줄 포함)는 계획 쓰기 경로표의 어느 역할에도 없습니다. 게이트상으로는 '역할 밖' 커밋으로 넣을 수 있지만 설계는 역할 밖을 gmid 밖 작업용으로 정했고, analog-grammar(B36)도 같은 공백을 표 개정으로 미뤘습니다. 어떻게 할까요?"
  선택지: "(가) 쓰기 경로표에 행 추가 (Recommended)" -- "계획 N3.12.2에 code-author의 `workspaces/*/**/*.py` 행을 더하는 판정 표 개정을 승인받고, F1 code 커밋이 16개를 함께 고칩니다. 역할 분리와 게이트 검사가 그대로 적용됩니다." /
  "(나) 오케스트레이터 역할 밖 커밋" -- "F1 test 커밋 전에 오케스트레이터가 트레일러 없는 커밋으로 고치고 F1 auditor가 같은 판정기로 잽니다. 표는 그대로지만 구현을 오케스트레이터가 하고 게이트는 그 커밋을 검사하지 않습니다." /
  "(다) 사용자가 직접 수정" -- "F1이 정한 목적지 표와 바꿀 모양을 드리면 세션 밖에서 직접 고칩니다. F1 판정 전에 들어가 있어야 합니다."
  답: "(가) 쓰기 경로표에 행 추가 (Recommended)". multiSelect false, 미리보기 없음, annotations 없음.

## 사용자에게 보인 것

이 기록이 덮는 범위의 근거는 사용자가 실제로 본 아래뿐이다(세션 기록 `63c6146a-…jsonl`, 사이드체인 제외 assistant 텍스트).

1. 위 질문 문안과 세 선택지(라벨·설명).
2. 질문 바로 앞 오케스트레이터 텍스트 메시지는 `2026-10-02T05:18:43.124Z`(uuid `f3a5cc43-a112-4a70-923b-c49c3f095691`) 한 건이고 Phase 4 #2 TS6 보고다(이 질문과 무관 -- 그 뒤 질문까지는 subagent 보고 알림·thinking·도구 호출뿐).
3. 이 사안을 처음 알린 메시지 `2026-10-02T04:56:52.742Z`(uuid `b7855051-7ee7-42a9-be08-2aec3e6f2792`, F1/F2 초안 보고)의 해당 줄, 원문(펜스 안 = jsonl text 블록의 그 줄 그대로):

```text
- **workspaces 스크립트 16개**: 역할 커밋의 쓰기 경로 밖에 있습니다. 초안의 기본안은 F1 전에 제가 역할 밖 커밋으로 고치는 것입니다.
```

사용자에게 제시하지 않은 것: 독립 검토 `_drafts/review_p3_f12.md`(질문 문안의 출처 -- 경로·본문 모두 메시지에 없음), 이 기록의 해시 측정, F1/F2 초안 본문.

## 범위 설명

덮는 것:
* 계획 `docs/01-plan/features/gain-budget-gmid-sizing.plan.md` N3.12.2 쓰기 경로표에 한 행 추가 -- 자리: `| gmid-code-author | \`workspaces/run_harness.py\` | -- | 없음 |` 행 바로 뒤(gate master `4a286f0` 판 602행 뒤). 새 행 원문:
  `` | gmid-code-author | `workspaces/*/**/*.py` | -- | 없음 | ``
  그 밖 바이트 불변(줄 하나 추가). 표의 다른 행·N3.12.2 산문·N3.12.4 5분류 산문은 바꾸지 않는다.
* 그 행이 주는 권한: gmid-code-author가 `workspaces/<하위 디렉터리 하나 이상>/…/*.py`를 쓴다(그 code 커밋은 EL1~EL4의 역할·트레일러·Change-Id·병합 구조 검사를 그대로 받는다).
  `판정 환경` 행이 우선이라(`role_paths.allowed` 첫 검사) `workspaces/*/__init__.py`·`**/conftest.py`·`**/sitecustomize.py` 등은 여전히 사용자만 쓰고,
  `workspaces/*.py`(한 조각, `run_harness.py` 제외)도 `판정 환경` 행 그대로다 -- 새 행 glob은 두 조각 이상이라 `workspaces/run_harness.py`와도 겹치지 않는다(기존 행 그대로).
* 소비 card: F1 `20261002-p3-callers-update` code 커밋(계약 1 대상 중 `workspaces/<하위>/*.py` -- 모의 16파일: current-reuse 12·two-stage 4, D-17 대입 2줄 `diagnose_cmrr_cmfb.py:24`·`diagnose_cmrr_psrr.py:20` 포함).

측정(gate master `4a286f0` 판 `tools/gates/merge_gate.py`, 격리 복제본, 2026-10-02 -- 관찰):
* `plan_tables_hash`(05 §15.2 -- `read_plan_tables` 넷 표 + `role_paths.read_write_paths` 쓰기 경로표): 개정 전 `7167e02839f86c4ecbcd91a63a9833c4d83a8aab8008bfe2d8cfc36206d2596d`(4a286f0 계획 blob `f2f4d2ee2318ec7f6e1dc607a355d3178bf8a995`) → 개정 뒤 **`31828c5e059dd41ed7a89f4d8757c402f9f7a61340411444d8101855f0623b57`** -- **바뀐다**.
  D-11 토큰(`20261002-p3-d11-query-cache-max`, N3.10 MOD1 행)은 해시 입력 밖이라 그 개정이 먼저든 뒤든 같은 값이다(D-11만: `7167e028…` 그대로, 행 + D-11: `31828c5e…`).
* `merge_gate.read_plan_tables`(N4.1·N4.2·N6.1)의 값은 **바뀌지 않는다**(개정 전·후 `PlanTables` 같음). 바뀌는 것은 `read_write_paths` 행 수 68 → 69뿐이다.
* 그래서 이 기록은 `target_kind: plan_tables`, `target` = 개정 **뒤** 해시다 -- EL3·EL4(`merge_gate.py` 868행)가 판정 표 해시가 바뀐 계획 커밋에 `target_kind == "plan_tables" and target == h_after`인 기록을 요구하고,
  `plan_tables` 머리에는 `diff_*` 키를 둘 수 없다(같은 파일 248행). `target_kind: diff`(D-11·UD-0 선례 모양)로는 게이트를 통과하지 못한다 -- 선례 `20260921-plan-githooks-row`(쓰기 경로표 한 행 추가)와 같은 모양이다.
  receive의 '상태 기반 판정 표 검사'(1079행 -- old 트리에 old 해시의 `plan_tables` 기록)도 이 기록이 들어간 뒤 새 base에서 성립한다.
* `role_paths.allowed`(개정 판): `workspaces/current-reuse-telescopic-ota-report/diagnose_cmrr_cmfb.py` -- gmid-code-author 허용(새 행), gmid-test-author·오케스트레이터 거부('맞는 행 없음').
  개정 전 = 모든 주체 '맞는 행 없음'(역할 밖). `workspaces/a/__init__.py`·`workspaces/a/conftest.py`·`workspaces/x.py` = `판정 환경` 행 우선 거부. `classify` = None(5분류 밖 -- 소스·test 동시 변경 검사 대상 아님, 변화 없음).

커밋 시점·자리(오케스트레이터 문서 커밋):
* 이 기록 파일(`.ai/approvals/20261002-p3-f1-workspaces-write-path.md`)과 계획 한 줄 개정을 **한 커밋**(오케스트레이터, 트레일러 없음 -- `docs/01-plan/**`·`.ai/approvals/**` 행)으로 넣는다(EL3 '같은 커밋이나 그 전에').
* 시점: card 35(`20260930-v3-changed-stmt-scope`)의 역할 브랜치(`role/test|code|audit/…`)를 정리한 **뒤**, F1 spec card 커밋(F1 순서 1) **전**. F1 code 커밋이 gate에 들어갈 때 gate master 계획이 이 행을 갖고 있어야 EL1·EL4가 허용한다.
  M1~T1 card 진행 중에 넣어도 판정에는 영향이 없다(그 card들은 이 경로를 쓰지 않는다) -- 다만 진행 중인 역할 브랜치가 없을 때 넣는다(병합 base 해시 변화가 그 card의 판정 기록 사슬과 섞이지 않게).
* 커밋 뒤 확인: `python tools/gates/merge_gate.py`의 `plan_tables_hash` 출력(1288행 경로)이 `31828c5e…`이고 `.ai/approvals/`에서 이 기록이 파싱되는지(`parse_approval_header`).

덮지 않는 것:
* 16파일의 **내용 변경 자체**와 그 판정(F1 card 계약 1~8, F1 판정 기록) -- 이 기록은 쓰기 권한만 덮는다.
* `workspaces/` 밖의 다른 게이트 공백(analog-grammar -- B36), N3.12.4 5분류 산문(`classify`에 workspaces 하위를 넣는 변경)과 05 design 정정 -- 필요하면 따로.
* 추적되지 않는 `workspaces/current-reuse-telescopic-ota-report/smoke_run_harness_session18_save.py`(UD-1 (가) '깨지게 둠' 그대로).
* test-author·오케스트레이터에게 workspaces 하위 쓰기를 주는 것.

## 재검토

F1이 끝난 뒤 이 행을 쓰는 card가 F1 하나뿐이면 행을 남길지(진단 스크립트 정리 백로그 §11-10과 함께) 그때 정한다 -- 행 삭제도 `plan_tables` 승인이다.
개정 커밋에서 해시가 `31828c5e…`가 아니면(같은 커밋에 다른 판정 표 변경이 섞임) 이 기록으로 진행하지 않는다.
