# B34 post-35 사전 실행 -- 병합된 card 35 실제 도구(a17b8bd)로 B34 착수 0단계·V3·변이 전 dry run

작성 2026-10-02. 저장소·audit worktree·기존 `_drafts` 파일 쓰기 없음(이 파일만 새로 씀). scratch `/c/g264`(TMP·TEMP·TMPDIR 그 안, 끝나고 삭제).

## 0. 모래상자

* `r` = 메인 작업 트리 저장소 `git -c core.autocrlf=false clone --no-hardlinks --no-local`, master `4a286f0` → audit worktree에서 `role/audit/20260930-v3-changed-stmt-scope`를 FETCH_HEAD로만 fetch(로컬 role 브랜치 안 만듦) → `merge --ff-only a17b8bd`.
* 합성 audit 커밋 `41a3ac3`(`Role: audit`, `Change-Id: 20260930-v3-changed-stmt-scope`): `gate_config.json` gate·workspace 경로 = 모래상자, `gate/pre-receive` 실행 경로 = 모래상자,
  자리표시 판정 기록 `.ai/verification/20260930-v3-changed-stmt-scope.json`(id 일치, V1~V10 PASS, `DRY_RUN` 표지 -- 실제 판정 기록 아님).
* `gate.git` = bare 가짜 gate, 실제 `pre-receive`·`gate-runner.py`(무결성 + `merge_gate receive` = EL4), accept-log. `r` hooksPath = `.githooks`(EL3), `.claude/hooks` 복사.
* 측정용 복제본 `m`(빈 hooksPath): T = S + `b34_kit/proto_066/test_b34_grammar_explicit.py`, K = T + `b34_kit/mk_head.py`(base만 S로 치환 -- SD blob은 0f23786과 같음), K0 = S + 코드만.
* 도구 = 모래상자 gate master `tools/gates`(= a17b8bd 도구 + 경로 2파일).

## 1. 착수 0단계(`b34_launch.sh --repo /c/g264/r --state /c/g264/state/b34.txt --wt /c/g264/wt`)

| 단계 | 결과 | 키트 기대와 |
|---|---|---|
| `conds` | exit 3, 조건 1:0 2:0 3:0 4:0 5:128, 조건 4 규약 전체 0, `targets_by_def` 개수 **3** | 같음(0·0·0·0·128; 표지 기준 ≥ 1) |
| `local1` = pre → appr → final-appr | 전부 OK. measured `5f643a9` → gate: 줄 인용 대상 차이 0, tools/ 변경 10개. `_approved_ids` 38, plan_tables_hash `7167e028…`, 승인 기록 4414 B, parse-approval decision `Q-B34-PHASE-CARDS-PHASE3`, P = `0a489a9` | 같음(38, 4414 B) |
| push #1(모래상자 gate, 단독) | EL4 통과, accept-log 줄 추가 | 같음 |
| `after-push-appr` | 조건 0·0·0·0·0 | 같음 |
| `local2` = doc → card → final | D: pending 5 → applied → already-applied, numstat 17 16, `test_phase2_stale_refs --gmid-phase=3` 18 passed. S: `parse_spec_card` ('3','red-green','no',[두 승인],[],12), interface 145줄·기존 함수 14 전부 `stick_diagram`. `_approved_ids` 39(+`Q-B34-PHASE-CARDS-PHASE3`), D·S 불변 | 같음 |
| push #2 → `after-push` | EL4 통과, OK(test worktree 명령 출력) | 같음 |

## 2. V3 대상(실제 도구 + 가짜 pytest, `post35_kit/p35_v3count.py`)

S(`7d0505c`)..K와 S..K0 둘 다 같은 값:

| 값 | 실측 | 키트·spec |
|---|---|---|
| 대상(`mutants`) / `not_targeted` / 레코드 | **10 / 45 / 55** | 10 / 45 / 55 -- 같음 |
| def별 [targeted, not_targeted] | `_import_analog_grammar` 3/9, `find_idiom_matches` 2/6, `find_stack_edges` 2/4, `audit_theta_root_direction` 3/26 (합 12·8·6·29) | spec 'V3 계획' 표 12·8·6·29, N2 3·2·2·3 -- 같음 |
| 대상 id | spec 'V3 계획' 표 10 id와 10/10 일치 | 같음 |
| scope_proto N2w(독립) 대칭차 / 순서 | 0 / 일치 | 같음 |
| 출력 키 | 옛 8키 + `not_targeted`, `targets_by_def`(def마다 `targeted`·`not_targeted`·`deleted_statements`·`def_header_changed`) | 계약 5대로 |

## 3. 변이 전 dry run(새 test + 옛 코드, 실제 도구, `--gmid-phase=3 --gmid-strict=`)

| 단계 | 실측 | 키트(`proto_066/out`) |
|---|---|---|
| red(T = 새 test + 옛 코드 S) | 27 failed, 12 passed. 27/27 `Failed: DID NOT RAISE <class 'ImportError'>`(c1 9, c2 idioms-only 9, c2 netclass-only 9), c8 9·자기 점검 3 PASS | 같음 |
| green(K) | 39 passed | 같음 |
| V3 실제 실행(real pytest, base S, head K) | exit 0, **verdict PASS, mutants 10, killed 10, not_targeted 45**, survivors [], exempt_ignored [], `--out` 55(killed 10, not_targeted 45). 소요 **17분 40초**(19:35:51~19:53:31) | 기대 '전부 killed, 면제 0' -- 같음. 시간은 아래 차이 4 |
| V4 `test_lint.py`(S..K, 모래상자 interface card) | exit 0, PASS, 대상 파일 1, 발견 (2) NO-SUBJECT 15·UNJUDGED 1, FAIL 0 | 같음 |
| 인벤토리(실제 도구 reachability) | S: **160·15·67·4**, K: **164·17·70·6**(k = 4·2·3·2) | **다름** -- 아래 차이 1 |

## 4. 키트·spec과 다른 값(고칠 곳)

1. **인벤토리 기준값 159·15·66·4 → 160·15·67·4**(`_import_analog_grammar` +1, `find_stack_edges` +1). card 35 때문이 아니다: `0f23786`→`5f643a9`(P10b 병합)에서 test
   `tests/contracts/test_reg_check_df23.py::test_p10b_cli_script_ascii_stdout_prints_utf8` 하나가 두 def 인벤토리에 들어왔다(같은 도구로 0f23786 159·15·66·4, 5f643a9·cf26d39·4a286f0·a17b8bd·S 전부 160·15·67·4).
   새 test 포함 K는 164·17·70·6(k = 4·2·3·2 그대로 -- 부풂 없음). auditor 인벤토리 확인 문장이 옛 기준값이면 auditor가 '+1 초과'로 test-author에게 돌려보낼 수 있다.
   * 반드시 고칠 곳(지금 기대값으로 쓰이는 문장):
     - `draft_b34.final.spec.md:236` 'auditor 인벤토리 확인' -- `159·15·66·4 + k` → `160·15·67·4 + k`(measured 판 표기 함께)
     - `b34_briefs.md:241` auditor '인벤토리 확인(V3 전 필수)' -- `159·15·66·4 + k` → `160·15·67·4 + k`
     - `draft_b34.final.spec.md:106` test 모양 문단 '실측 인벤토리 159·15·66·4 + k' -- 기준 판 표기를 붙이거나 160·15·67·4로
     - `draft_b34.final.spec.md:210·212` 'V3 계획' 표 인벤토리 열(`_import_analog_grammar` 159 / 159 + k, `find_stack_edges` 66 / 66 + k) -- 표 머리가 `2d58fd8` 측정이라 값을 바꾸거나 '착수 base 160·67' 주를 단다
   * 판 표기가 붙은 과거 실측(그 판에서는 맞음, 고치지 않아도 됨): spec 99·311(`163·17·69·6` = 0f23786 판 K)·318·338·363, `b34_briefs.md:90·92`(0.4 표 '0f23786'), `b34_briefs.md:99`의 '인벤토리 159 test'.
2. **`targets_by_def` 표지 개수 = 3**(키트 문구는 '≥ 1'/'1 이상'이라 판정 영향 없음). 값을 적은 곳 없음 -- 수정 불필요(참고: `b34_launch.sh:209`, `b34_commit_plan.md:74`, `b34_briefs.md:12`).
3. `b34_briefs.md:253` V3 행 명령에 `--pytest-ini <base 판 pytest_gate.ini>`가 빠져 있다(도구 필수 인자 -- 35 전 `4a286f0`에서도 필수, 35와 무관한 기존 생략). 실행한 명령:
   `mutate_changed.py --root <m> --base <base> --head <M> --pytest-ini <base 판>/pytest_gate.ini --out <…> --gmid-phase=3 --gmid-strict=`.
4. **V3 실행 시간**: N2 10개 실제 실행 17분 40초(기준 실행 포함) -- `b34_briefs.md:99` '상한 0.27 h'(16.2분)를 약간 넘는다. 판정 영향 없음, auditor timeout·시간 안내만 '약 18분'으로.
5. 그 밖의 값(조건 exit, `_approved_ids` 38→39, 4414 B, numstat 17 16, 18 passed, parse_spec_card 튜플, interface 14 함수, red 27/27·green 39, V3 10/45/55·10 id·10 killed, V4 PASS·UNJUDGED 1·NO-SUBJECT 15)은 키트·spec과 같다.
   새로 확인된 값: interface card 145줄, plan_tables_hash `7167e02839f86c4e…`(값을 적은 곳 없음).

## 5. 격리 확인

* 실제 저장소: status·reflog(20)·refs·worktree 목록 시작 때와 같음(끝에 재확인). audit worktree는 fetch 원천으로만 읽음.
* EL1이 `git -c core.hooksPath`와 미해석 리다이렉트를 거부해 측정 복제본 hook 설정·리다이렉트는 scratch 스크립트 안에서 했다(대상은 전부 `/c/g264`).
* 도구 임시 파일은 `/c/g264/tmp`(gmid-v3-*, pytest-of-*)에 생겼다. `C:\Windows\Temp\gmid-redteam*` 없음(redteam 미실행).
