---
id: 20261002-p3-f1-workspaces-write-path
date: 2026-10-02
target_kind: plan_tables
target: 16b899d1c745ddd0d305b2a977eecc74b0c830d89507d7eb3476b7323a08aec1
scope: 계획 N3.12.2 쓰기 경로표에 gmid-code-author의 `workspaces/current-reuse-telescopic-ota-report/*.py`·`workspaces/two-stage-ota-report/*.py`(제외 glob 없음, 조건 없음) 두 행 추가 -- Phase 3 F1(`20261002-p3-callers-update`) code 커밋이 그 두 gmid 작업 폴더 바로 아래 진단 스크립트(모의 대상 16개)의 shim import를 정의 모듈로 고친다([F1] 쓰기 경로 답 (가)를 [F1] 경로 재확인 답 'gmid 폴더로 좁힘'이 대체, review_p3_f12 S2·S3 · review_p3_f12_r1 B1 해소)
---

## 사용자 원문

> gmid 폴더로 좁힘 (Recommended)

(AskUserQuestion 두 번의 문답이다. 이 기록의 결정은 **둘째 답**이고, 첫째 답 "(가) 쓰기 경로표에 행 추가 (Recommended)"를 대체한다 -- 첫째 질문이 행의 부수 효과를 보이지 않아
독립 검토(review_p3_f12_r1 B1)가 다시 묻게 했다. 두 문답 모두 세션 기록 `63c6146a-ab1d-4035-a169-bae810986922.jsonl`(사이드체인 아님)의 tool_use 입력과 tool_result에서
프로그램으로 바이트 대조해 옮겼다(`_drafts/p3kit_f12/verify_approval_f1wp.py` -- 아래 따옴표 안은 jsonl 문자열 그대로, 고치지 않았다). 각 header의 AskUserQuestion은 이 세션에 한 건씩뿐이다.)

### 첫째 문답 -- header `[F1] 쓰기 경로`(대체됨)

질문 2026-10-02 14:30 KST(`2026-10-02T05:30:10.108Z`, tool_use `toolu_01PokFaLT31S8ep6tYfPQJmx`, uuid `c5b9d12d-5d65-4d05-a940-466ba20d30e2`),
답 2026-10-02 14:32 KST(`2026-10-02T05:32:16.443Z`, tool_result uuid `fe2c1b04-1a26-4c79-83ee-af5c68933e35`).

* 질문 원문: "[F1] shim 삭제 전에 고쳐야 하는 추적 파일 중 workspaces 하위 폴더 진단 스크립트 16개(current-reuse 12·two-stage 4, 덮어쓰기 계측 2줄 포함)는 계획 쓰기 경로표의 어느 역할에도 없습니다. 게이트상으로는 '역할 밖' 커밋으로 넣을 수 있지만 설계는 역할 밖을 gmid 밖 작업용으로 정했고, analog-grammar(B36)도 같은 공백을 표 개정으로 미뤘습니다. 어떻게 할까요?"
* 선택지: "(가) 쓰기 경로표에 행 추가 (Recommended)" -- "계획 N3.12.2에 code-author의 `workspaces/*/**/*.py` 행을 더하는 판정 표 개정을 승인받고, F1 code 커밋이 16개를 함께 고칩니다. 역할 분리와 게이트 검사가 그대로 적용됩니다." /
  "(나) 오케스트레이터 역할 밖 커밋" -- "F1 test 커밋 전에 오케스트레이터가 트레일러 없는 커밋으로 고치고 F1 auditor가 같은 판정기로 잽니다. 표는 그대로지만 구현을 오케스트레이터가 하고 게이트는 그 커밋을 검사하지 않습니다." /
  "(다) 사용자가 직접 수정" -- "F1이 정한 목적지 표와 바꿀 모양을 드리면 세션 밖에서 직접 고칩니다. F1 판정 전에 들어가 있어야 합니다."
* 답: "(가) 쓰기 경로표에 행 추가 (Recommended)". multiSelect false, 미리보기 없음, annotations 없음.

### 둘째 문답 -- header `[F1] 경로 재확인`(이 기록의 결정)

질문 2026-10-02 17:16 KST(`2026-10-02T08:16:33.022Z`, tool_use `toolu_01QeEYjVgV4ChhaRaJcxgouH`, uuid `2dd719f8-7d40-4cfa-aeff-835d8c50cc84`),
답 2026-10-02 17:18 KST(`2026-10-02T08:18:56.717Z`, tool_result uuid `c2a335c6-b4fc-42a1-bdac-4d834585f82d`).

* 질문 원문: "[F1 쓰기 경로 재확인] 앞서 '(가) 쓰기 경로표에 행 추가'를 고르셨는데, 그 질문에서 빠진 부수 효과가 독립 검토에서 나왔습니다. `workspaces/*/**/*.py` 행은 그 아래 추적 .py 38개(gmid와 무관한 verilog-rtl-workspace 2개 포함)와 앞으로 생길 하위 .py 전부를 code-author 전용으로 잠가, 사용자 본인 커밋(Role: user·트레일러 없음)·메인 세션·비 gmid agent의 수정이 게이트에서 거부됩니다. 어떻게 할까요?"
* 선택지: "gmid 폴더로 좁힘 (Recommended)" -- "행 glob을 F1이 고칠 gmid 작업 폴더(current-reuse-telescopic-ota-report 등 실측된 하위 폴더)로만 한정합니다. F1은 그대로 code-author 커밋으로 고치고, 다른 workspaces 폴더는 지금처럼 사용자가 씁니다." /
  "그대로 수용" -- "workspaces/*/**/*.py 전체를 code-author 전용으로 둡니다. 이후 그 아래 .py(verilog-rtl 포함)는 사용자도 직접 커밋할 수 없고 gmid card로만 바뀝니다." /
  "같은 glob에 사용자 행 추가" -- "code-author 행과 함께 같은 glob의 사용자 행도 둡니다. 사용자는 계속 쓸 수 있지만, 두 역할이 겹치는 경로라 역할 분리 검사가 그 범위에서 느슨해집니다."
* 답: "gmid 폴더로 좁힘 (Recommended)". multiSelect false, 미리보기 없음, annotations 없음.

## 사용자에게 보인 것

이 기록이 덮는 범위의 근거는 사용자가 실제로 본 아래뿐이다(세션 기록 `63c6146a-…jsonl`, 사이드체인 제외 assistant 텍스트).

1. 위 두 질문 문안과 각 세 선택지(라벨·설명).
2. **부수 효과로 보인 것은 둘째 질문 문안과 선택지 설명이 전부다**: 넓은 행(`workspaces/*/**/*.py`)이 추적 `.py` 38개(verilog-rtl-workspace 2개 포함)와 앞으로 생길 하위 `.py` 전부를
   code-author 전용으로 잠가 사용자 본인 커밋(`Role: user`·트레일러 없음)·메인 세션·비 gmid agent의 수정이 게이트에서 거부된다는 것, 그리고 좁힘 안의 설명
   "F1이 고칠 gmid 작업 폴더(… 실측된 하위 폴더)로만 한정", "다른 workspaces 폴더는 지금처럼 사용자가 씁니다".
   좁힌 행이 **그 두 폴더 안에서도** 같은 잠금을 만든다는 것(아래 '범위 설명'의 22파일·막히는 주체)은 문안에 숫자로 나오지 않았다 -- '그 폴더로만 한정'의 직접 결과로 이 기록에 적는다.
3. 둘째 질문 바로 앞 오케스트레이터 텍스트 메시지는 `2026-10-02T08:15:38.969Z`(uuid `d9afd326-85fd-479c-9bfa-de5f086e90d1`, 결정 패키지 v7 보고)이고 이 사안과 무관하다
   (그 뒤 질문까지는 독립 검토 r1의 subagent 보고 알림 `3d7f5993-…`(`08:15:51.478Z` -- 사용자 입력 아님)뿐). 답 뒤 `2026-10-02T08:19:58.614Z`(uuid `f3c7a869-c255-4455-951e-53a98aad33a0`)에서
   "앞서 고르신 \"(가) 쓰기 경로표에 행 추가\"를 이 답으로 대체합니다"라고 알렸다.
4. 첫째 질문 앞: 질문 바로 앞 텍스트 메시지 `2026-10-02T05:18:43.124Z`(uuid `f3a5cc43-a112-4a70-923b-c49c3f095691`, Phase 4 #2 TS6 보고 -- 무관). 이 사안을 처음 알린 메시지
   `2026-10-02T04:56:52.742Z`(uuid `b7855051-7ee7-42a9-be08-2aec3e6f2792`, F1/F2 초안 보고)의 해당 줄, 원문(펜스 안 = jsonl text 블록의 그 줄 그대로):

```text
- **workspaces 스크립트 16개**: 역할 커밋의 쓰기 경로 밖에 있습니다. 초안의 기본안은 F1 전에 제가 역할 밖 커밋으로 고치는 것입니다.
```

사용자에게 제시하지 않은 것: 독립 검토 `_drafts/review_p3_f12.md`·`_drafts/review_p3_f12_r1.md`(질문 문안의 출처), 이 기록의 해시·`allowed` 측정, F1/F2 초안 본문.

## 범위 설명

덮는 것:
* 계획 `docs/01-plan/features/gain-budget-gmid-sizing.plan.md` N3.12.2 쓰기 경로표에 **두 행** 추가 -- 자리: `| gmid-code-author | \`workspaces/run_harness.py\` | -- | 없음 |` 행 바로 뒤(gate master `4a286f0` 판 602행 뒤), 이 순서. 새 행 원문:
  `` | gmid-code-author | `workspaces/current-reuse-telescopic-ota-report/*.py` | -- | 없음 | ``
  `` | gmid-code-author | `workspaces/two-stage-ota-report/*.py` | -- | 없음 | ``
  그 밖 바이트 불변(줄 둘 추가). 표의 다른 행·N3.12.2 산문·N3.12.4 5분류 산문은 바꾸지 않는다.
* glob을 고른 근거(실측, 가장 좁은 폴더 단위): F1 모의 대상 workspaces 하위 16파일(current-reuse 12·two-stage 4)이 **모두 두 폴더 바로 아래**(`workspaces/<폴더>/<파일>.py`, 하위 디렉터리 0)라
  폴더마다 한 조각 `*.py` 한 행이 이 둘을 덮는 가장 좁은 폴더 glob이다(파일 단위 16행은 '폴더로 한정' 답보다 좁고 F1 base에서 대상이 바뀌면 다시 묻게 되어 고르지 않았다).
* 그 행이 주는 권한과 **부수 효과**(gate master `4a286f0` `role_paths`, 개정 판 실측 -- 대상 16, 행이 덮는 추적 `.py` **22**):
  * gmid-code-author가 두 폴더 바로 아래 `*.py`를 쓴다(그 code 커밋은 EL1~EL4의 역할·트레일러·Change-Id·병합 구조 검사를 그대로 받는다). 16 대상 모두 code-author만 허용, test-author·auditor·오케스트레이터·사용자 거부.
  * 덮는 추적 `.py` 22 = 대상 16 + 대상 아닌 current-reuse 6(`build_html.py`·`build_report.py`·`probe_crossover_pairing_alternatives.py`·`probe_d1_verify.py`·`probe_group_split_reassembly.py`·`probe_l3_groups.py`).
    이 22파일과 앞으로 두 폴더 바로 아래 생길 `.py`(추적되지 않는 `smoke_run_harness_session18_save.py` 포함 -- 커밋하면)는 `overlaps_any` 참이 되어
    **사용자 본인 커밋(`Role: user` -- 맞는 행 없음, 트레일러 없는 커밋 -- 트레일러 필수)·메인 세션·비 gmid agent(EL1 오케스트레이터 규칙)의 쓰기가 게이트에서 거부되고 gmid code card로만 바뀐다**.
  * 그대로인 것: 두 폴더의 하위 디렉터리(current-reuse `spice/` 14파일), `workspaces/verilog-rtl-workspace/**`(2파일), 그 밖 workspaces 폴더 -- 행 밖 추적 `.py` 17개 모두 개정 전과 `allowed`(5주체)·`overlaps_any`가 같다(넓은 행 대비 16파일 해방).
    `판정 환경` 행이 우선이라(`role_paths.allowed` 첫 검사) `workspaces/*/__init__.py`·`**/conftest.py`·`**/sitecustomize.py` 등은 여전히 사용자만 쓰고, `workspaces/*.py`(한 조각, `run_harness.py` 제외)도 `판정 환경` 행 그대로다.
    새 행은 세 조각이라 `workspaces/run_harness.py`(기존 행)와 겹치지 않는다. `classify` = None(5분류 밖 -- 변화 없음).
* 소비 card: F1 `20261002-p3-callers-update` code 커밋(계약 1 대상 중 두 폴더 바로 아래 `.py` -- 모의 16파일, D-17 대입 2줄 `diagnose_cmrr_cmfb.py:24`·`diagnose_cmrr_psrr.py:20` 포함).
  F1 base에서 대상이 이 두 행 밖(하위 디렉터리·다른 폴더)에 나오면 F1 착수 조건이 멈추고 묻는다(F1 계약 4).

측정(gate master `4a286f0` 판 `tools/gates/merge_gate.py`·`role_paths.py`, 격리 복제본, 2026-10-02 -- 관찰, `_drafts/p3kit_f12/wp_narrow.py` → `out/wp_narrow.json`):
* `plan_tables_hash`(05 §15.2 -- `read_plan_tables` 넷 표 + `role_paths.read_write_paths` 쓰기 경로표): 개정 전 `7167e02839f86c4ecbcd91a63a9833c4d83a8aab8008bfe2d8cfc36206d2596d`(4a286f0 계획 blob `f2f4d2ee2318ec7f6e1dc607a355d3178bf8a995`) → 개정 뒤 **`16b899d1c745ddd0d305b2a977eecc74b0c830d89507d7eb3476b7323a08aec1`** -- **바뀐다**.
  (대체된 넓은 행 판의 해시 `31828c5e…`는 이 기록의 대상이 아니다.)
  **`plan_tables_hash` 기준으로만** D-11 토큰(`20261002-p3-d11-query-cache-max`, N3.10 MOD1 행) 개정과의 순서가 무관하다(N3.10은 해시 입력 밖 -- D-11만: `7167e028…` 그대로, 두 행 + D-11: `16b899d1…`).
  D-11 승인의 `diff` 해시(`compute_diff_hash` -- base·head blob)는 이 두 행이 먼저 들어가는지에 따라 달라진다(D-11 초안은 '커밋 뒤 계산'으로 감쌌다).
* `merge_gate.read_plan_tables`(N4.1·N4.2·N6.1)의 값은 **바뀌지 않는다**(개정 전·후 `PlanTables` 같음). 바뀌는 것은 `read_write_paths` 행 수 68 → 70뿐이다.
* 그래서 이 기록은 `target_kind: plan_tables`, `target` = 개정 **뒤** 해시다 -- EL3·EL4(`merge_gate.py` 868행)가 판정 표 해시가 바뀐 계획 커밋에 `target_kind == "plan_tables" and target == h_after`인 기록을 요구하고,
  `plan_tables` 머리에는 `diff_*` 키를 둘 수 없다(같은 파일 248행). 선례 `20260921-plan-githooks-row`(`49e5f65`, 쓰기 경로표 한 행 추가)와 같은 모양이다.
  receive의 '상태 기반 판정 표 검사'(1079행 -- old 트리에 old 해시의 `plan_tables` 기록)도 이 기록이 들어간 뒤 새 base에서 성립한다.

커밋 시점·자리(오케스트레이터 문서 커밋):
* 이 기록 파일(`.ai/approvals/20261002-p3-f1-workspaces-write-path.md`)과 계획 두 줄 개정을 **한 커밋**으로 넣는다(EL3 '같은 커밋이나 그 전에'):
  트레일러 **`Role: doc`** 하나(`git commit --trailer "Role: doc"`), Change-Id 없음 -- `docs/01-plan/**`·`.ai/approvals/**`는 오케스트레이터 행과 겹쳐 트레일러가 필수다
  (트레일러 없는 커밋은 `judge_trailers({})` = "트레일러 `Role: code|test|audit|doc|user`가 정확히 하나가 아니다([])"로 거부 -- 실측). 선례 `49e5f65`(같은 종류의 쓰기 경로표 행 + `plan_tables` 승인 기록, 트레일러 `Role: doc`).
* 시점: card 35(`20260930-v3-changed-stmt-scope`)의 역할 브랜치(`role/test|code|audit/…`)를 정리한 **뒤**, F1 spec card 커밋(F1 순서 1) **전**. F1 code 커밋이 gate에 들어갈 때 gate master 계획이 이 두 행을 갖고 있어야 EL1·EL4가 허용한다.
  M1~T1 card 진행 중에 넣어도 판정에는 영향이 없다(그 card들은 이 경로를 쓰지 않는다) -- 다만 진행 중인 역할 브랜치가 없을 때 넣는다(병합 base 해시 변화가 그 card의 판정 기록 사슬과 섞이지 않게).
* 커밋 뒤 확인: `python tools/gates/merge_gate.py`의 `plan_tables_hash` 출력(1288행 경로)이 `16b899d1…`이고 `.ai/approvals/`에서 이 기록이 파싱되는지(`parse_approval_header`).

덮지 않는 것:
* 16파일의 **내용 변경 자체**와 그 판정(F1 card 계약 1~8, F1 판정 기록) -- 이 기록은 쓰기 권한만 덮는다.
* 두 폴더의 하위 디렉터리·그 밖 workspaces 폴더(verilog-rtl-workspace 포함)의 쓰기 주체 -- 그대로(사용자·역할 밖).
* `workspaces/` 밖의 다른 게이트 공백(analog-grammar -- B36), N3.12.4 5분류 산문(`classify`에 workspaces 하위를 넣는 변경)과 05 design 정정 -- 필요하면 따로.
* 추적되지 않는 `workspaces/current-reuse-telescopic-ota-report/smoke_run_harness_session18_save.py`의 내용(UD-1 (가) '깨지게 둠' 그대로 -- 행이 덮는 것은 커밋할 때의 쓰기 주체뿐).
* test-author·오케스트레이터에게 workspaces 하위 쓰기를 주는 것.

## 재검토

F1이 끝난 뒤 이 두 행을 쓰는 card가 F1 하나뿐이면 행을 남길지(진단 스크립트 정리 백로그 §11-10과 함께) 그때 정한다 -- 행 삭제도 `plan_tables` 승인이다.
개정 커밋에서 해시가 `16b899d1…`가 아니면(같은 커밋에 다른 판정 표 변경이 섞임) 이 기록으로 진행하지 않는다.
