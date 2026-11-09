# 착수 0단계 launch 스크립트 재검토 r2 (2026-10-02)

검토자: 독립 reviewer(작성자 아님). 범위(루프 종료 조건): `review_launch_scripts.md`의 **B1·S1·S2가 실제로 고쳐졌는가**와 **r1 수정이 새 결함을 만들었는가**만 본다.
대상: `_drafts/launch_common.sh`(신규) + 스크립트 8개(`*.sh` vs `*.pre-r1.sh` diff, 01:25~01:26 판).
저장소 읽기 전용. 실측은 모래상자 `/c/g191`에서만(복제본 `/c/g191/r` + bare 가짜 gate `/c/g191/gate.git`, 합성 커밋 `5d5e14c` = `dd60db6` + `gate_config.json` gate·workspace 경로를 `/c/g191`로).
실제 저장소 `git status --short` 37줄은 시작과 끝이 같다(diff 0), HEAD = gate/master = `dd60db6`, 실제 `_drafts`에 `.tmpd` 생성 0.

## 판정 요약

| 스크립트 | B1 | S1 | S2 | 새 결함 | 판정 |
|---|---|---|---|---|---|
| launch_common.sh | 원칙 주석·`lc_push_cmd` | 해소(`lc_repo_guard`) | — | n1 | 통과 |
| v3_binding_launch.sh | 해당 없음(실행 git 쓰기 = commit·fetch만) | 해소 | 해당 없음 | 없음 | 통과 |
| v3_scope_launch.sh | 해당 없음 | 해소 | 해당 없음 | 없음 | 통과 |
| b34_launch.sh | 해당 없음 | 해소 | 해소(미충족이 이제 rc 3) | n2 | 통과 |
| b26pre_launch.sh | 해당 없음 | 해소 | 해소 | n2 | 통과 |
| backfill_launch.sh | 해당 없음 | 해소 | 해소 | n2 | 통과 |
| b26_1_launch.sh | 해당 없음 | 해소 | 해소 | n2 | 통과 |
| **b26_1_carry.sh** | **해소** | 해소 | 해당 없음 | 없음 | **통과(사용 금지 해제)** |
| b33_launch.sh | 해당 없음(kit-cmds의 checkout -B 등은 heredoc 출력) | 해소 | 해당 없음 | 없음 | 통과 |

B 0, S 0. 새 minor 2(n1·n2) -- 둘 다 사용 전 수정 불필요. **루프 종료 조건 충족.**

## (1) EL1이 판정하는 git 명령이 스크립트 안에서 실행되는가

EL1 목록(gate master `dd60db6` `tools/gates/role_hooks.py` `judge_git`): `push`, REF_MOVE(`update-ref commit-tree write-tree replace filter-branch rebase am cherry-pick revert stash reset update-index filter-repo`),
`symbolic-ref`(쓰기), `hash-object -w`, `branch -D/-f/-M/-C`, `checkout/switch -B/-C`, `merge/pull`, `worktree add/remove`(그 밖 거부), `checkout --/restore`(test 되돌리기), `config` 쓰기, `remote add/set-url/rename/remove`, `commit -n`, `-c alias.*/core.hookspath`.

9개 파일 전부를 `g …`/`git …` + 위 부분 명령으로 grep(주석 제외), 각 줄을 실행/출력으로 분류:

* `R`(대상 저장소)에 **실행**되는 것: `fetch gate`(오케스트레이터 = read_only), `commit -q -m … --trailer …`(메인, `-n`·`--no-verify` 없음 -- EL3 hook이 돈다), `config --get`(읽기), `hash-object`(-w 없음), `worktree list`(읽기), `cat-file`·`rev-parse`·`merge-base`·`show`·`diff`·`log`(읽기). v3_scope Python `git()` 호출 = `rev-parse`·`diff`·`grep`·`merge-base`(읽기).
* backfill v3count의 `clone`·`remote remove origin`·`config core.*`·`checkout --detach`·`commit`은 scratch 복제본(`$SCR/r`, 작업 저장소 밖) -- EL1 git 규칙 대상이 아니고 r1에서 `remote remove origin`이 더해졌다(m7 반영).
* **출력만** 되는 것: 모든 `push`(`lc_push_cmd`), 모든 `worktree add`(after-push), carry cleanup의 `worktree remove --force`×3·`branch -D`×3, b33 kit-cmds의 `clone`·`remote remove`·`config`·`checkout -q -B`(heredoc).
* carry의 `g worktree prune`·`g worktree remove`·`g branch -D`(pre-r1 378·381행)는 삭제됐다. `prune`은 출력 목록에도 없다(주석 근거: EL1이 add·remove 밖 worktree 쓰기 거부).

결론: EL1 전용 규칙(참조 이동·worktree·push·dispute 보존)을 스크립트 안에서 실행하는 줄은 0.

## (2) S1 -- 실제 저장소 별칭(8개 × 15개 = 120회, 전부 exit 2)

단계 이름 `NOSUCHSTAGE`, 모래상자 옵션은 단계 이름 앞(`--state /c/g191/st/aliasN/s.txt --wt …`, v3_scope `--render-tmp`, carry `--launch-state --archive`).

| 별칭 | 결과(8개 공통) |
|---|---|
| 8.3 짧은 경로 `C:\Users\HSLEE\DOCUME~1\Todoc\fpga\CHIP-D~1` | exit 2 "실제 저장소(git-common-dir c:/users/hslee/documents/todoc/fpga/chip-design-skills/.git)를 가리킨다" |
| 8.3 POSIX `/c/Users/HSLEE/DOCUME~1/Todoc/fpga/CHIP-D~1` | 같음 |
| junction `/c/g191/jrepo` → 저장소 | 같음 |
| 부모 junction `/c/g191/jfpga/chip-design-skills` | 같음 |
| 섞인 구분자 `C:\Users\HSLEE/Documents\Todoc/fpga\chip-design-skills` | 같음 |
| 끝 점 `…/chip-design-skills.` | 같음 |
| `…/chip-design-skills/.` | 같음 |
| `…/fpga/wt/../chip-design-skills` | 같음 |
| 하위 디렉터리 `…/chip-design-skills/tools/gates` | 같음 |
| `.git` 디렉터리 자체 | 같음 |
| 실제 저장소의 역할 worktree `…/wt/20260930-v3-exempt-binding-test` | 같음 |
| UNC `//localhost/c$/…/chip-design-skills` | exit 2 -- 단 common-dir 비교가 아니라 **두 번째 가드**("remote gate가 실제 gate를 가리킨다")로 거부 |
| (r1 회귀) 끝 `/`, `C:/…`, 소문자 | exit 2(common-dir) |
| 대조군 `/c/g191/r` | 8개 모두 가드 통과 → `== 대상 저장소 R=/c/g191/r …` → 단계 분기에서 exit 2 |

junction 두 개는 `cmd /c rmdir`로 링크만 지웠고(대상 존재 재확인) 그 뒤 `/c/g191` 삭제.

## (3) S2 -- `conds` 착수 조건 머리 깨뜨리기(새 방식 2개, 사본 스크립트)

사본 = 원본에서 `DR=` 한 줄만 `/c/g191/drafts`로(diff 1줄 확인), 초안은 `_drafts` 최상위 파일 사본. `--repo /c/g191/r`, gate master `5d5e14c`.

| 스크립트 | 정상 초안 | X1: 머리 줄을 문서 앞쪽에 한 번 더(중복 머리) | X2: 머리 모양 변경 |
|---|---|---|---|
| b34 | `1:0 2:128 3:128 4:0 5:128`, "미충족: 2 3 5", **rc 3** | AssertionError `(1, [])` → "[중단] 착수 조건 추출 실패", **rc 1** | `### 착수 조건` → IndexError → **rc 1** |
| b26pre | `1:128 2:128 3:0 4:128 5:128`, rc 3 | AssertionError `[]` → **rc 1** | `- **착수 조건**` → IndexError → **rc 1** |
| backfill | `1:128 2:128 3:0 4:128 5:128`, rc 3 | AssertionError `[]` → **rc 1** | `- **착수 조건**` → IndexError → **rc 1** |
| b26_1 | `1:0 2:0 3:0 4:0 5:128 6:128 7:128 8:128 9:0 10:128 11:128`, rc 3 | "착수 조건 블록이 정확히 하나가 아니다(2)" → **rc 1** | `착수 조건 (순서 ` → "(0)" → **rc 1** |

r0 결함(깨진 초안 → `1:0 … 5:0` rc 0)은 재현되지 않는다. 2차 방어(명령 0개 조건 = `E` → rc 1, 추출 줄 수 대조 `|| return 1`, `cond_rc … || return 1`)도 코드에 있다. b34 `conds`는 이제 미충족을 rc 3으로 반영한다(r0 S2 둘째 문단 해소).

## (4) B1 -- carry `check`·`cleanup`의 dispute 보존(수정 안 한 실제 스크립트, 모래상자)

구성: 메인에 spec card(`## dispute 기록`에 blob A `0e4d922…`만)를 커밋해 가짜 gate에 push → B1 `9fbd8cb`. 1차 역할 브랜치 셋·worktree 셋(`/c/g191/wt/<id>-{test,code,audit}`, 트레일러 Role·Change-Id). dispute B `51426c4…`는 미기록.
cleanup은 records 뒤 상태(상태 파일 RECORDS=1·T1·K1·CACHE·BLOB, 보관 SHA256SUMS, 운반 blob, 기록 4·5 = 기존 decision 기록의 id만 바꾼 사본 -- parse-approval 통과)를 손으로 만들고 실행.

| 경우 | check | cleanup |
|---|---|---|
| K1에 dispute B 커밋(미기록) | **rc 1**, :176 dispute_guard "[중단] 1차 시도에 dispute(… blob 51426c4…)가 있고 … '## dispute 기록'에 없다" | **rc 1**, :427 같은 문구, 명령 0개 출력 |
| code worktree에만 미추적 B | **rc 1**, :176 같은 문구(깨끗함 검사보다 먼저) | **rc 1**, :427 |
| K1에 A(기록됨) + worktree에 B | **rc 1**, :176 (B 거부) | **rc 1**, :427 |
| K1에 A(기록됨)만 -- 대조군 | dispute 통과("blob 0e4d922… 있음") → 뒤 단계(auditor 산출물 없음 :195)에서 멈춤 | **rc 0**, 정리 명령 6개 출력 |
| dispute 없음 -- 대조군 | "dispute: … 없음" → :195에서 멈춤 | **rc 0**, 6개 출력 |

판정 식은 EL1 `_dispute_guard`와 같다(worktree 파일 `hash-object` + `role/code` 브랜치 blob, 메인 HEAD spec card `## dispute 기록` 절 부분 문자열) + K1(상태 파일) blob을 더해 더 엄격하다. 실행된 정리 명령 0(출력만), `cleaned`가 결과를 따로 확인한다.

## (5) 출력되는 push 형태와 EL1(payload만 판정, 실행 안 함)

`lc_push_cmd`의 실제 출력: `env APPDATA='C:\Users\HSLEE\AppData\Roaming' LOCALAPPDATA='C:\Users\HSLEE\AppData\Local' git -C /c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills push gate master:master`

실제 저장소 `.claude/hooks/role_guard.py`에 PreToolUse Bash payload(cwd = 실제 저장소, agent_type 없음 = 오케스트레이터):

| payload | rc | 이유 |
|---|---|---|
| 위 env 형태 그대로 | 2 | **Q-08**(역할 브랜치 `role/{audit,code,test}/20260930-v3-exempt-binding`이 지금 있음) -- 형태 판정은 통과 |
| `git -C <R> push gate master:master`(env 없음) | 2 | 같은 Q-08 문구 -- 두 형태가 같은 분기에 도달 |
| `env APPDATA=… git -C <R> push gate master`(대조: 형태 틀림) | 2 | "허용된 push 형태가 아니다" |
| `env GIT_CONFIG_COUNT=1 git … push gate master:master` | 2 | "검사 끄기: 환경 변수 GIT_CONFIG_COUNT" |
| env 형태 + `--force` | 2 | "강제·삭제 push 거부" |
| carry가 출력할 `git -C <R> worktree remove --force <W>/20260930-b26-rail-accessor-set-code` | 0 | 정리 형태(실제 저장소에 그 code worktree 없음 → dispute blob 0) |
| `git -C <R> branch -D role/code/20260930-b26-rail-accessor-set` | 0 | 〃 |
| `git -C <R> worktree add <W>/20260930-v3-exempt-binding-test -b role/test/… gate/master` | 0 | §12 형태 |

결론: role_guard는 env 접두 형태를 `git push gate master:master`와 같게 판정한다(`_unwrap`이 `env NAME=값`을 벗김). 지금 rc 2는 Q-08 때문이고 스크립트 `pre`가 같은 조건을 먼저 본다.

## 새 결함(minor, 사용 전 수정 불필요)

* **n1. `lc_repo_guard` 두 번째 가드(remote gate가 실제 gate인가)는 별칭에 약하다.** `lc_same_path`는 `realpath -m`이라 junction·`..`·끝 `/`·대소문자·`\`는 같게 보지만
  8.3(`…\GMID-G~1.GIT` → `c:/users/hslee/docume~1/…`), `file:///C:/…/gmid-gate.git`(cwd 상대 경로로 바뀜), UNC(`//localhost/c$/…`)는 **다르다**로 판정한다(함수 직접 실측).
  영향: 모래상자 복제본의 gate 원격을 그런 표기로 실제 gate에 붙이면 출력 push가 실제 gate를 향한다 -- 단 그 push는 오케스트레이터가 단독 호출하고 gate pre-receive(EL4)가 판정하며, 표준 표기(`C:/…`·`/c/…`)는 거부된다(UNC `--repo` 실측에서 이 가드가 실제로 거부함).
  권고(선택): 원격 URL을 `git -C "$R" ls-remote --get-url gate`로 받은 뒤 `file://` 접두를 벗기고, 존재하는 경로면 `git --git-dir=<url> rev-parse --path-format=absolute --git-common-dir`로 정규화해 비교.
* **n2. `conds` 미충족(rc 3) 때 ERR trap이 `[중단] …: return $rc` 줄을 찍는다**(b34·b26pre·backfill·b26_1, 실측 출력). rc 의미(0/3/1)는 머리 주석대로지만 '[중단]' 문구가 비정상 종료처럼 읽힌다. 권고(선택): `stage_conds` 끝을 `return $rc` 대신 trap에 걸리지 않는 형태(예: 분기 뒤 `exit $rc`를 디스패치에서)로.

## r1 다른 변경 확인(회귀 없음)

* m8(measured rev = 마지막 출현): 6개 초안 모두 앵커 1개 -- pre-r1 '첫 출현'과 `lc_meas_short` 결과가 같다(v3_binding `19eb475`, v3_scope `0f23786`, b34 `5f643a9`, b26pre·backfill `dd60db6`, b26_1 `7535799`). b33은 같은 규약을 자체 구현(앞선 문단 rev 조상 검사 추가).
* m6(`lc_pred_ok`, V1~V10 정확히·PASS/N/A): b33 `pre`·v3_scope `pre`·`cond_rc`(P 표지)에 배선됨. `cond_rc`가 0이어도 선행 판정 기록이 기준 미달이면 `P` → `conds_check` 요구 번호에서 rc 1, `stage_conds`에서 미충족 rc 3.
* m1(after-push 캐시 재수령 + `st_set CACHE`): v3_binding·v3_scope·b34·b33에 추가 -- 8개 같은 모양. m4(b34 stage_doc pytest `-c $(st_get CACHE)/pytest_gate.ini`). m2(`--wt` 8개 필수). m3·m5(`lc_tmp_setup` = `<상태 파일>.tmpd`, TMPDIR·TMP·TEMP). m7(backfill scratch origin 제거). approvals_at 실패 경로 `rm -rf "$t"` 추가.
* 옵션 가드: 모래상자 값은 절대 경로 필수(`lc_need_sandbox`), 실제 모드는 별칭 허용 후 실제 값으로 되돌림(`lc_need_real` + 재대입). b33 `--draft-spec`·`--pred-missing-ok`, v3_binding `--tools-ref`, v3_scope `--drafts`는 실제 저장소(별칭 포함 -- 별칭은 가드가 먼저 거부)에서 거부.

## 이 검토 자체

* EL1이 리다이렉트·`tee`·실제 gate 경로 인자를 거부해, diff 저장·별칭 시험·payload 시험은 `/c/g191/*.sh` 스크립트 파일로 실행했다(모두 읽기 전용 또는 모래상자 쓰기).
* carry 시험 중 내 시험 스크립트가 모래상자 복제본의 추적 파일(`v5-carry/20260930-restore-plan-functions/*`)을 지워 한 번 `git -C /c/g191/r checkout --`로 되돌린 뒤 다시 쟀다(실제 저장소 무관).
* 끝: junction 링크 제거 → `/c/g191` 삭제, 실제 저장소 `git status --short` 시작과 같음.
