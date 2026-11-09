# P10b push 직후 실행 절차(runbook) -- 문서 커밋 1 + md 일치 card 커밋 D·승인 기록·spec card → push → test worktree

작성 2026-10-01. 기준 gate `master` = `a796468`(P10b spec card). 저장소 읽기 전용으로 준비했고, 사전 시험은 `C:/g101` 모래상자(복제본 + 가짜 gate)에서 끝까지 돌렸다(§7).
실행 스크립트: `_drafts/post_p10b_runbook.sh`(어느 확인이든 실패하면 멈춤 -- `set -Eeuo pipefail` + `inherit_errexit` + ERR trap).

## 0. 산출물

| 파일 | 내용 |
|---|---|
| `post_p10b_runbook.sh` | 단계 `pre`·`c1`·`d`·`appr`·`card`·`final`(묶음 `local`)과 `after-push`. **push와 worktree 생성은 하지 않는다**(§5·§6 단독 호출 -- EL1 판정 대상으로 남기기 위해) |
| `post_p10b_context_append.py` | `.ai/context.md` 바이너리 append 전용(c1: P10·P10b 완료 + 문서 커밋 줄 4줄, b47: 사용자 결정 1줄). 쓴 뒤 '원래 바이트 + 더한 바이트' 대조, 표지 줄 중복 시 중단 |
| `approval_20261001-b47-md-sync.md` | 승인 기록 초안(decision). '사용자 원문' = 오케스트레이터 B47 보고(15:30 KST, "B47 점검이 끝났습니다." … "처리 방침 (원칙상 기본안이라 따로 여쭙지 않고 진행합니다)" 1·2) 원문 + 답 "응, 그렇게 진행해"(15:32), 검토 요약(16:34) 원문 + 같은 답(16:40). 원문은 세션 기록(jsonl)에서 그대로 뽑았다 |
| `draft_md_sync.final.spec.md` | 커밋할 spec card. `draft_md_sync.reviewed.spec.md`에서 '결정 필요 항목' 3곳만 고침(착수 조건 문장이 실제로 보낸 문안 -- 질문이 아니라 방침 알림 -- 과 맞지 않았다, 묶기 언급 없음, 승인 초안 경로). '관찰 가능한 계약'은 그대로(interface card 0행 불변) |
| `post_p10b_dryrun_setup.sh` | 사전 시험 모래상자 생성 스크립트(재현용) |
| (기존) `patch_design20_231.py`·`patch_template.py`·`patch_history_groupAB.py` + `*.diff.txt` | 문서 커밋 1 패치. 스크립트가 `.diff.txt`의 `index <전>..<후>` 줄로 전·후 blob을 단정한다 |

## 1. 착수 조건(스크립트 `pre`가 전부 단정)

1. **P10b가 PASS 판정으로 gate에 들어가고 정리까지 끝났다.** 주의: 지금(17:00 무렵) `role/audit/20260930-df23-registry-record` 머리 `36a6ec8`은 **1차 판정 V3 FAIL(보충 변이 290 중 생존 45, 비등가 30)·V4 FAIL**(test_lint (2) 6, (4) 1)이다 -- 재시도가 필요하고 sha는 바뀐다.
   그래서 스크립트는 sha가 아니라 gate master 이력에서 제목 접두 `audit: 20260930-df23-registry-record`인 커밋이 **정확히 1개**인지로 확인한다.
   P10b 정리(design 05 §12, 오케스트레이터, 각각 단독 호출):
   ```bash
   git -C /c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills fetch gate
   git -C /c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills merge --ff-only gate/master
   git -C /c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills worktree remove /c/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-df23-registry-record-test
   git -C /c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills worktree remove /c/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-df23-registry-record-code
   git -C /c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills worktree remove /c/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-df23-registry-record-audit
   git -C /c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills branch -D role/test/20260930-df23-registry-record role/code/20260930-df23-registry-record role/audit/20260930-df23-registry-record
   ```
   (재시도 정리라면 `worktree remove --force`, dispute가 있으면 정리 **전에** spec card `## dispute 기록` 커밋 -- §12 재시도 행.)
2. 메인 체크아웃 `master`, HEAD = `gate/master`(fetch 뒤), `refs/heads/role/` 비어 있음, P10b worktree 없음, 인덱스 비어 있음, 대상 경로(`design 20`·양식·history·`.ai/context.md`·library·`.ai/approvals`·`docs/02-design/specs`) 변경 없음, 새로 만들 세 파일 없음.
3. `a796468` 뒤 library·`topology_to_markdown.py`·`stick_diagram.py` 불변(기대 blob `711a5910…`/`2a3e67a5…`의 전제 -- 비지 않으면 멈추고 blob과 card 계약 9 값을 다시 잰다). P10b가 바꾸는 것은 레지스트리·`tests/tools/reg_check.py`·새 test 하나라 걸리지 않는다(1차 병합본 실측).
4. 패치 세 개의 기준 blob = `.diff.txt` 작성 때 blob(`94e5151`·`5e9a952`·`54c273d` -- a796468에서 일치 확인).
5. 게이트 캐시 `<git-common-dir>/gmid-gate-cache/<gate master 전체 sha>`(hook과 같은 `role_paths.ensure_cache`)가 있고 그 이름 = `git rev-parse gate/master`. `plan_tables_hash`를 이 캐시의 `merge_gate.py`로 재서 상태 파일에 둔다.

## 2. 실행(로컬 커밋 4개) -- 한 번의 단독 Bash 호출

```bash
bash /c/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/post_p10b_runbook.sh local
```

* 선택: P10b 재시도 경위 등 확인한 사실을 context P10b 줄 끝에 덧붙이려면 실행 전에 `_drafts/p10b_context_note.txt`(UTF-8 한 줄)를 만든다. 없으면 판정 기록 커밋 제목만 인용한다(수치를 지어내지 않음).
* 상태 파일 `_drafts/post_p10b_state.txt`(GATE_BASE·PLAN_HASH·CACHE·C1·MEASURED_AT·D·APPR·CARD)와 `…state.txt.appr.json`(승인 기록 파싱 결과)이 남는다.
* 중단 뒤에는 원인을 고치고 그 단계부터 `… post_p10b_runbook.sh <단계>`로 이어 한다(각 단계는 HEAD가 앞 단계 커밋인지부터 단정한다).
* 이 스크립트는 MSYS2 자식 bash로 돈다. 자식 bash는 `HOME`·`APPDATA`와 호출 쪽 환경 변수를 잃는다(실측: `HOME=/home/HSLEE` → git `user.email` 없음, `APPDATA` 없음, `R=… bash …` 전달 안 됨, python stdout cp949) -- 스크립트 머리에서 `HOME`·`APPDATA`·`PYTHONIOENCODING=utf-8`을 다시 정하고, 경로는 옵션으로만 바꾼다.

### 단계별 내용과 단정

| 단계 | 커밋 | 바뀌는 파일 | 트레일러 | 단정(하나라도 어긋나면 멈춤) |
|---|---|---|---|---|
| `c1` | 문서 커밋 1 | design 20(§11-1 231행 1줄 교체), `_TEMPLATE.spec.md`(+6), history(+14: H1 6+7, H2 1), `.ai/context.md`(+4) | `Role: doc` (Change-Id 없음) | 패치 출력이 `적용:`(이미 적용·중단이면 멈춤), 스테이징 blob = `.diff.txt` 뒤 blob(`027b7af`·`deb05b8`·`5d7e5eb`), numstat 1/1·6/0·14/0·4/0(context 삭제 0줄), `plan_tables_hash` 전후 동일, 스테이징 경로 정확히 4개 |
| `d` | 문서 커밋 D | `library/folded_cascode.topology.md`·`current_reuse_telescopic_ota.topology.md` | `Role: doc`, `Change-Id: 20261001-topology-md-sync` | cwd = assets, `python -B topology_to_markdown.py library/<n>.topology.json`(2개 제자리), 나머지 4개는 리터럴 임시 폴더로 렌더링해 `diff --strip-trailing-cr` 차이 0, 스테이징 blob `711a59108bd53891ea410963e235617a6955b416`·`2a3e67a5ccef1aae8829688bedaa3098b57d74e2`, numstat 5/5·12/6, library 다른 변경·pycache 0, D^ = c1(= card `measured_at`) |
| `appr` | 승인 기록 커밋 | `.ai/approvals/20261001-b47-md-sync.md`(새), `.ai/context.md`(+1) | `Role: doc` (Change-Id 없음 -- card 계약 9 범위 밖) | 게이트 캐시 `merge_gate.py parse-approval` → id·date·`target_kind: decision`·`target_list == ['B47-MD-SYNC']`, context 1/0, Change-Id 트레일러 없음 |
| `card` | spec card 커밋 | `docs/02-design/specs/20261001-topology-md-sync.spec.md`·`.interface.md` | `Role: doc`, `Change-Id: 20261001-topology-md-sync` | 캐시 이름 = gate master 전체 sha(그사이 안 움직임), `parse_spec_card` → (`2`, `test-only`, `no`, `[20261001-b47-md-sync]`), `phase 2 ∈ read_plan_tables().phase_order`, interface card = **게이트 캐시의 `interface_card.py` --root <R>** 출력, 표 행 0 |
| `final` | -- | -- | -- | `GATE_BASE..HEAD` 4커밋·병합 없음·제목 순서, card 계약 9 미리보기(이 Change-Id 커밋 경로 합집합 − spec/interface = md 2개, `measured_at..HEAD` library·렌더러 diff = md 2개), context 삭제 0줄, `plan_tables_hash` 불변, 대상 경로 깨끗 |

커밋 메시지는 모두 `-m` 문단 + `--trailer`(heredoc `-F -` 쓰지 않음 -- `b47_regen_commands.md` 5단계 메시지 본문을 문단으로 옮김). `Co-Authored-By`도 트레일러.

## 3. 커밋 순서의 근거

* 문서 커밋 1 → D → 승인 기록 → spec card. D와 spec card만 `Change-Id: 20261001-topology-md-sync`(card 계약 9가 이 Change-Id 커밋만 본다). 승인 기록·사용자 결정 줄은 Change-Id 없는 별도 커밋(card '의도'·'결정 필요 항목' 문단).
  card `measured_at` = D^ = 문서 커밋 1.
* 사용자에게 보인 순서와 다른 점(보고 때 한 줄): 15:32 답 직후 메시지(06:32Z)는 "md 2개 재생성"을 하나의 문서 커밋에 넣는다고 했고, 16:40 답 직전 메시지(07:40Z)는 "1 P10b push 2 문서 커밋 3 Phase 2 완료 판정 4 md 일치 card(재생성 커밋과 승인 기록 함께)" 순서였다.
  이 runbook은 지시대로 md card 커밋(D·승인·spec card)을 **Phase 2 완료 판정 전**에 넣는다(spec card 기본안 "P10b 정리 직후·DoD 전" -- DoD E4 `PT2`에 새 test가 들어가도 기준 불변). 재생성을 문서 커밋 1에 넣지 않은 이유는 card 계약 8·9(승인 기록 범위 설명에 적음).

## 4. 실패했을 때

* 커밋 전 단계에서 멈췄으면(작업 트리·인덱스만 바뀜): EL1은 `reset`을 막는다. 대신 바뀐 파일만 되돌린다 -- `git -C <R> restore --staged -- <경로…>` 뒤 `git -C <R> checkout -- <경로…>`, 새 파일(`.ai/approvals/20261001-b47-md-sync.md`, spec·interface card)은 리터럴 경로로 `rm`. 그다음 같은 단계부터 다시.
  `.ai/context.md`는 append만 했으므로 `checkout -- .ai/context.md`로 되돌린다(다시 실행하면 표지 줄 검사로 중복 append를 막는다).
* 이미 커밋한 뒤 멈췄으면: 되돌리지 않는다(EL1이 `reset`·`revert` 거부). 원인을 고치는 문서 커밋을 더하고 `final`의 '4커밋' 단정은 수동 확인으로 대신한다 -- 사용자에게 보고.
* EL3 hook 거부(`[EL3 차단]`): 메시지대로. `integrity-failed` 표지가 생기면 사용자 몫(§13.4) -- 오케스트레이터가 지우지 않는다.

## 5. push -- 단독 호출, 전체 출력 확인(병렬·`tail` 금지)

```bash
git -C /c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills push gate master:master
```

EL1 `_judge_push`: 인자가 정확히 `gate master:master`이고 `refs/heads/role/`이 비어 있어야 한다(P10b 정리 뒤), push 범위 무결성 대조 통과. 거부되면 gate에 흔적이 없다 -- 메시지를 보고 고친 뒤 다시.
출력에서 `a..b  master -> master`를 확인한 뒤에만:

```bash
bash /c/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/post_p10b_runbook.sh after-push
```

(fetch → `gate/master` = card 커밋 = HEAD 단정, 다음 명령 출력.)

## 6. test worktree(design 05 §12 순서 1) -- 단독 호출

```bash
git -C /c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills worktree add /c/Users/HSLEE/Documents/Todoc/fpga/wt/20261001-topology-md-sync-test -b role/test/20261001-topology-md-sync gate/master
```

이어서 gmid-test-author(입력 = spec card + interface card, 새 파일 `skills/analog-gmid-design/assets/tests/contracts/test_topology_md_sync.py`, 이름 접두 `test_mdsync_`/`_mdsync_`, `dup_`·`new_topology` 금지)
→ auditor(test-only: 계약 6·8·9, `measured_at` = D^ = 상태 파일 `MEASURED_AT`) → audit push → 정리. 그 뒤 Phase 2 완료 판정.

## 7. 사전 시험(2026-10-01, `C:/g101`, 끝에 삭제)

모래상자: 메인 체크아웃을 `--no-hardlinks --no-local`로 복제 → P10b 1차 병합본 `4294048`까지 ff(레지스트리·reg_check·새 test 반영 -- P10b 실제 변경과 겹침 확인용) → **합성 audit 커밋**
(제목 `audit: 20260930-df23-registry-record …(DRY-RUN 합성…)`, 바꾼 것은 `gate_config.json`의 `gate_path`·`workspace_path`와 `gate/pre-receive` 실행 경로뿐 -- hook이 실제 gate 대신 가짜 gate를 보게) →
그 복제본에서 bare 가짜 gate(`pre-receive`·`gate-runner.py`·accept-log 설치, 실제 gate와 같은 모양)를 뜨고 `remote gate`·`core.hooksPath`·`.claude/hooks` 사본을 배선. 재현: `post_p10b_dryrun_setup.sh`.
실행: `post_p10b_runbook.sh --repo /c/g101/r --render-tmp /c/g101/b47_render --state /c/g101/state.txt --wt /c/g101/wt <단계>`.

| 항목 | 결과 |
|---|---|
| `pre` | 통과. `plan_tables_hash` = `7167e02839f86c4ecbcd91a63a9833c4d83a8aab8008bfe2d8cfc36206d2596d`(실제 a796468 계획서로 잰 값과 같음) |
| `c1` | 세 패치 모두 `적용:`(충돌 없음 -- 대상 파일이 서로 다르고 history 기준 줄 A2 행·DEC-60 행 각 1회), 결과 blob = `.diff.txt` 기대 blob, numstat 1/1·6/0·14/0·4/0, plan hash 불변, **EL3 pre-commit·commit-msg 통과** → `ab63e82` |
| `d` | 2개 재생성 blob `711a5910…`·`2a3e67a5…` 일치(P10b 1차 병합 위에서도), 나머지 4개 차이 0, numstat 5/5·12/6, EL3 통과 → D `d8d38b8`, D^ = `ab63e82` |
| `appr` | `parse_approval_header`(게이트 캐시 `merge_gate.py parse-approval`) 통과 -- decision, `target_list ['B47-MD-SYNC']`(decision은 해시 키 없음 -- 채울 해시 없음), context +1/0, EL3 통과 → `c0ed8c2` |
| `card` | 캐시 `gmid-gate-cache/<gate master 전체 sha>`, `parse_spec_card` (2, test-only, no, [20261001-b47-md-sync], 절 11), interface card 기존 함수 0·신규 0행, EL3 통과 → `9110b42` |
| `final` | 4커밋·병합 없음·제목 순서, 계약 9 미리보기 = md 2개, context 삭제 0, plan hash 불변 |
| push | `git -C /c/g101/r push gate master:master` → 가짜 gate `pre-receive`(실제 `gate-runner.py` 사본 → 무결성 gate 범위 + `merge_gate.py receive`, **EL4**)가 받아들임, accept-log `d492b0f → 9110b42` 한 줄 |
| `after-push` + worktree | 통과, `worktree add … -b role/test/20261001-topology-md-sync gate/master` → `9110b42` |
| 멈춤 확인 | 끝난 뒤 `pre` 재실행 → `refs/heads/role/` 비지 않음에서 멈춤(exit 1), `c1` 재실행 → HEAD ≠ GATE_BASE에서 멈춤(exit 1). 첫 시도에서 python cp949 출력·`.claude/hooks` 부재(모래상자 한정)에서도 각각 멈췄다 |

사전 시험 뒤 gate `master`가 `0f23786`으로 움직였다(`d6a9778` 승인 기록 `20261001-p10b-v3-equiv`, `0f23786` P10b spec card 재시도 개정). 바뀐 파일은 그 두 개뿐이라
패치 세 대상 blob(`94e5151`·`5e9a952`·`54c273d`)·library·렌더러·계획서는 그대로다(다시 확인) -- 이 runbook과 기대값은 유효하다.

패치 사이 충돌: **없음**. 세 패치는 서로 다른 파일만 쓰고, context append는 끝에 붙이며, P10b 1차 병합본이 바꾼 파일(레지스트리·reg_check·새 test)과도 겹치지 않는다. 재시도 P10b가 이 세 문서·library를 바꾸면 `pre`의 기준 blob 단정에서 멈춘다.

## 8. 주의·남은 확인

* EL1(PreToolUse)은 `bash <스크립트>` 안의 명령을 보지 않는다. 그래서 push·worktree·정리 명령은 스크립트 밖 단독 호출로 두었다. 스크립트 안 커밋은 EL3(git hook)·EL4(gate)가 그대로 판정한다.
* `b47_regen_commands.md` 6단계 `push gate master`는 EL1 거부 형태다(리뷰 B1) -- 이 runbook §5가 대신한다.
* 승인 기록 '사용자 원문'은 15:30 보고 전체(진행 중 작업 목록 포함)와 16:34 요약 전체를 고치지 않고 인용했다. 15:30 보고는 질문이 아니라 "따로 여쭙지 않고 진행"한다는 알림이었다는 점을 괄호에 적었다.
* 작업 트리 CRLF 경고(`LF will be replaced by CRLF`)는 새 md 파일에서 나오는 정상 출력이다(커밋 blob은 LF).
* 사전 시험 첫 실행에서 자식 bash가 `R=` 환경 변수를 받지 못해 `pre`가 **실제 저장소**를 대상으로 돌았다: 실행된 것은 `git fetch gate`(gate master가 이미 `a796468`이라 참조 변화 없음)와 읽기 확인뿐이고, P10b 판정 기록이 없어 멈췄다(파일·커밋·상태 파일 변경 없음 -- `git status`·`rev-parse` 확인). 그 뒤 옵션 방식으로 바꿨다.
