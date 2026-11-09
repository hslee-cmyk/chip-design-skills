# 착수 0단계 launch 스크립트 독립 검토 (2026-10-02)

검토자: 독립 reviewer(작성자 아님). 저장소 읽기 전용. 실측은 모래상자 `/c/g176`에서만 했다(실제 저장소 `git status --short` md5 `168fd530…`가 시작과 끝에 같다).
대상: `v3_binding_launch.sh`, `v3_scope_launch.sh`, `b34_launch.sh`, `b26pre_launch.sh`, `backfill_launch.sh`, `b26_1_launch.sh`, `b26_1_carry.sh`, `b33_launch.sh`(모두 `_drafts/`, 2026-10-02 00:24 판).

## 모래상자 구성(재현용)

* `/c/g176/r` = 실제 저장소의 `--no-local --no-hardlinks` 복제본(origin 제거, `core.hooksPath` = 빈 `/c/g176/nohooks`).
* `/c/g176/gate.git` = 복제본에서 만든 bare 가짜 gate(실제 gate 경로는 EL1이 인자로도 거부해서 쓰지 않음).
* 합성 커밋 `68f21c5` = `dd60db6` + `gate_config.json`의 `gate_path`·`workspace_path`를 모래상자로(`cache_dir()`/`load_env`가 실제 gate를 읽지 않게). 가짜 gate master = 이 커밋.
* b26pre 양성 경로용 `8a4107f` = 위 + 판정 기록 자리표시 3개(묶기·범위·B34) + `20261001-b26-phase3-cards` 초안 + `mutate_changed.py`에 `not_targeted` 표지.
* 모든 호출은 `--repo /c/g176/r --state /c/g176/st/<x>`(+ `--render-tmp`/`--wt`/`--archive`/`--launch-state` 해당 시)를 **단계 이름 앞에** 두었다. `TMPDIR=/c/g176/tmp`.
* 결함 재현용으로 스크립트 사본(`/c/g176/copy/*.sh`, `DR=` 한 줄만 `/c/g176/copy/_drafts`로 바꿈)과 '착수 조건' 머리를 깨뜨린 초안 사본을 썼다.

## 판정 요약

| 스크립트 | 판정 | B | S | minor |
|---|---|---|---|---|
| v3_binding_launch.sh | 조건부 통과 | 0 | S1 | m1·m5 |
| v3_scope_launch.sh | 조건부 통과 | 0 | S1 | m1·m5 |
| b34_launch.sh | 조건부 통과(S2 수정 권고) | 0 | S1·S2 | m1·m4·m5·m6 |
| b26pre_launch.sh | 조건부 통과(S2 수정 권고) | 0 | S1·S2 | m2·m3·m5 |
| backfill_launch.sh | 조건부 통과(S2 수정 권고) | 0 | S1·S2 | m2·m3·m5·m7 |
| b26_1_launch.sh | 조건부 통과(S2 수정 권고) | 0 | S1·S2 | m3·m5 |
| **b26_1_carry.sh** | **cleanup 단계 수정 전 사용 금지** | **B1** | S1 | m3 |
| b33_launch.sh | 조건부 통과(S1이 가장 큼) | 0 | S1 | m1·m5·m8 |

## B (사용 전 필수 수정)

### B1. `b26_1_carry.sh cleanup`이 EL1 '정리 전 dispute 보존' 규칙을 우회한다

* design 05 §6.2 표(205·206행, review30 R-16): 오케스트레이터의 `git worktree remove $W/<id>-code`·`git branch -D role/code/<id>`는 code worktree(또는 브랜치)에
  `docs/02-design/disputes/<id>.md`가 있고 그 blob이 메인 HEAD spec card `## dispute 기록`에 없으면 **거부**된다(`role_hooks._dispute_guard`, 851~878행).
* carry는 이 두 명령을 **스크립트 안에서** 실행한다(378·381행). EL1(PreToolUse)은 바깥 명령 문자열 `bash …/b26_1_carry.sh cleanup`만 판정하므로(실측: role_guard에 그 문자열을 넣으면 rc 0)
  dispute 검사는 한 번도 돌지 않는다. git 쪽에도 ref 삭제를 막는 hook이 없다(`.githooks` = commit-msg·pre-commit·pre-merge-commit·pre-push).
* carry 자체의 확인으로 막히는가: `check`는 code worktree가 깨끗한지(`status --porcelain` 빈 값, 152행)와 T1..K1 커밋 트레일러(Role: code, Change-Id)만 본다.
  gmid-code-author 정의(58~63행)는 dispute를 **`Role: code`·`Change-Id` 트레일러로 커밋하고 멈춘다** -- 즉 커밋된 dispute는 check를 그대로 통과한다.
  archive는 `K1_SD.py`·`T1.patch`만 보관하므로 dispute 본문은 보관되지도 않고, cleanup의 `branch -D`가 마지막 참조를 지운다(되돌릴 수 없음, gc 유예 동안만 객체가 남음).
* 수정안(최소): `stage_check`와 `stage_cleanup` 머리에
  `if g cat-file -e "$K1:docs/02-design/disputes/$ID.md" 2>/dev/null || [ -e "$WT_C/docs/02-design/disputes/$ID.md" ]; then echo "[중단] 1차 시도에 dispute가 있다 -- 사용자 결정 전 운반·정리 금지" >&2; false; fi`.
  더 근본적으로는 push처럼 정리 명령 6개를 **출력만** 하고 오케스트레이터가 단독 호출로 실행하게 하면 EL1이 정상 판정한다(실측: 그 형태는 각각 EL1 rc 0으로 허용됨).
* 일반화 메모: 모든 launch 스크립트가 같은 이유로 EL1 밖에서 git 쓰기를 한다. 커밋은 EL3(.githooks)가 보므로 문제가 작지만, **EL3에 대응 hook이 없는 EL1 전용 규칙**(ref 삭제·worktree 제거·dispute 보존)은 스크립트 안에 넣으면 사라진다. 그런 명령은 스크립트에 넣지 않는 규칙을 권한다.

## S (수정 권고)

### S1. 실제 저장소 판별이 문자열 비교라 경로 별칭이 '모래상자'로 통과한다(8개 공통)

* 판별: `if [ "$R" != "$R_REAL" ]`. 같은 저장소의 다른 표기 -- 끝 `/`, `C:/Users/…`, 대소문자 다른 `/c/users/hslee/…` -- 는 '복제본'으로 분류된다.
* 실측(무동작 단계 이름 `NOSUCHSTAGE`로, 저장소 접근 없이): `b34_launch.sh --repo /c/Users/HSLEE/…/chip-design-skills/ NOSUCHSTAGE` → "--state 필수"(즉 복제본 취급),
  `--state /c/g176/st/alias`를 더하면 가드를 통과해 `== 대상 저장소 R=…chip-design-skills/`를 찍고 단계 분기까지 간다. `C:/…`, 소문자 표기도 같다.
* 영향: 실제 저장소에서 **모래상자 전용 완화**가 열린다 -- `b33 --pred-missing-ok`(선행 판정 기록 없이 진행)·`--draft-spec`(모래상자용 수정 초안이 실제 spec card로 커밋됨),
  `v3_binding --tools-ref`(도구·문서 불변 대조 기준 교체), `v3_scope --drafts`. 실측: `b33 --repo C:/Users/…/chip-design-skills --state … --pred-missing-ok --draft-spec /c/g176/x.md NOSUCH`가 가드를 통과(단계 이름에서만 멈춤).
  또 실제 상태 파일 보호가 무력화된다(실제 저장소에 모래상자 상태 파일). 실제 master에 생긴 로컬 커밋은 EL1이 `reset`을 전부 거부하므로 오케스트레이터가 되돌릴 수 없다.
* 수정안: `R`을 정규화해 비교 -- 예 `rc=$(git -C "$R" rev-parse --path-format=absolute --git-common-dir)`와 실제 common dir을 `cygpath -m`·소문자로 맞춰 비교하거나,
  복제본 모드에서 `git -C "$R" config --get remote.gate.url`이 실제 gate 경로이면 거부. 같은 함수를 8개가 공유하면 의미도 같아진다.

### S2. `conds` 단계가 조건 추출 실패를 '전부 충족(0)'으로 찍는다(b34·b26pre·backfill·b26_1)

* 원인: `stage_conds`가 `conds_check "$H" || rc=$?`로 부른다. `||` 문맥에서는 `set -e`가 함수 안 전체에서 꺼지므로, `extract_conds`의 Python 실패(또는 b26_1의 토큰 대조 `return 1`)가 무시되고
  비어 있거나 반쯤 쓰인 조건 파일로 계속 간다. `cond_rc`는 명령이 없으면 0을 낸다(b34: `test -n "$cmd"` 실패 무시 후 `bash -c ""` = 0, 나머지: `while … < <(grep …)`가 0회 반복).
* 실측(사본 + '착수 조건' 머리를 깨뜨린 초안, 같은 모래상자 gate):

  | 스크립트 | 실제 초안 출력 | 깨진 초안 출력 | conds rc |
  |---|---|---|---|
  | b34 @68f21c5 | `1:0 2:128 3:128 4:0 5:128` | `1:0 2:0 3:0 4:0 5:0` (+ IndexError) | 0 / 0 |
  | b26pre @68f21c5 | `1:128 2:128 3:0 4:128 5:128` | `1:0 2:0 3:0 4:0 5:0` | 1 / 1(approval 줄 때문) |
  | backfill @8a4107f | (조건 5 = b26pre 판정 기록 없음 → 128이어야 함) | `1:0 … 5:0` | — / **0** |
  | b26_1 @8a4107f | — | `1:0 … 11:0` (+ AssertionError, 토큰 [중단]) | — / 1(approval 줄 때문) |

  b34 `conds`는 정상 초안에서도 조건 미충족을 rc에 반영하지 않는다(요구 번호 없이 호출) -- 출력 표만 근거다. 그 표가 거짓 0이 될 수 있다.
* 영향: `pre`·`card`·`after-push-appr`는 `||` 밖에서 부르므로 실제 커밋 경로는 안전하다(실측: 깨진 초안으로 `pre` → `[중단] …:124` rc 1).
  그러나 spec card '작성 전 실측'이 `conds` 출력을 사실 문장으로 옮기고 있다(예: backfill card "conds -- dd60db6에서 exit 128·128·0·128·128") -- 거짓 측정이 card에 들어갈 수 있다.
* 수정안: `conds_check` 안에서 `extract_conds || return 1`, `cond_rc`는 해당 번호 명령이 0개면(COND_COUNTS가 0인 번호 제외) `E`를 찍고 실패, `stage_conds`는 추출 실패 시 rc≠0.
  (서브셸 `( set -e; … ) || rc=$?`로는 고쳐지지 않는다 -- `||` 문맥의 서브셸도 -e가 무시된다.)

## minor

* m1. after-push 캐시 갱신이 스크립트마다 다르다: b34(after-push-appr)·b26pre·backfill·b26_1·carry는 `cache_dir` 재수령 + `st_set CACHE`, v3_binding·v3_scope·b33·b34(최종 after-push)는 안 한다. 뒤 단계가 캐시를 쓰지 않아 현재는 무해하나 '같은 모양' 주장과 어긋난다.
* m2. b26pre·backfill은 `--wt`가 없어 모래상자 실행에서도 after-push가 실제 `W`(`…/fpga/wt/<id>-test`)로 worktree 명령을 찍는다(실측: `git -C /c/g176/r worktree add /c/Users/…/wt/…-test …`). 복제본 R은 EL1 대상이 아니라 그대로 실행되면 실제 wt 폴더에 모래상자 worktree가 생긴다. b26_1·carry처럼 `--wt` 필수로.
* m3. `mktemp`(conds 단계, `approvals_at`)는 `TMPDIR`(기본 MSYS2 `/tmp`)에 쓴다 -- 모래상자 실행도 모래상자 밖에 쓴다. `approvals_at`은 parse 실패 시 `rm -rf "$t"` 없이 끝난다(errexit). `$STATE.d`처럼 상태 파일 옆으로.
* m4. b34 `stage_doc`의 pytest는 `-c "$R/tools/gates/pytest_gate.ini"`(작업 트리 판)를 쓴다 -- 다른 곳의 '게이트 캐시 절대 경로' 원칙과 다르다(`$(st_get CACHE)/pytest_gate.ini`).
* m5. 자식 bash 환경 손실 대응이 `HOME`·`APPDATA`뿐이다. 실측: Bash 도구의 자식 bash에서 `HOME=/home/HSLEE`, `TEMP`·`TMP`·`TMPDIR` 빈 값 → Python `tempfile.gettempdir()` = `C:\WINDOWS\Temp`
  (검토 harness도 HOME을 안 넣었을 때 `Author identity unknown`으로 커밋 실패 -- 스크립트의 HOME export는 필요하고 맞다). backfill v3count의 mutate_changed·pytest 임시 파일이 시스템 Temp로 간다. b33 kit-cmds는 `TMP/TEMP`를 명시한다 -- 맞출 것.
* m6. 선행 card '병합' 판정 의미가 다르다: b34·b26pre·backfill·v3_scope = 판정 기록 파일 존재(`cat-file -e`), b26_1 = `chk`(id·10개·PASS/N/A), b33 = id·PASS/N/A(개수 없음 -- `"checks":{}`도 통과). 같은 질문에 세 가지 기준.
* m7. backfill v3count 복제본은 origin(= 실제 저장소)을 지우지 않는다(b33 kit-cmds는 `remote remove origin`). 현재 push 경로는 없지만 격리 규칙을 맞출 것.
* m8. measured rev 단일 출처의 '첫/마지막' 규약이 다르다: b34·b26pre·backfill·b26_1·v3_binding = 문서에서 **첫** 일치, b33 = **마지막** '(착수…' 문단. 현재 초안들은 앵커가 각 1개라 무해(실측: 각 초안 1건)하나, b33 방식(문단 덧붙이기)을 다른 card에 쓰면 옛 rev가 선택된다.

## 확인 결과(통과한 것)

### (1) 실제 저장소·상태 파일 보호, 파괴적 명령

* 옵션 파싱: 8개 모두 "단계 이름 뒤 옵션"·"--repo만"·"--state만"·"값 빠짐"을 exit 2로 거부(실측 7개 × 4 + carry `--archive` 누락 exit 2). 단 S1(별칭).
* `cd`: carry의 `( cd "$ADIR" && … )` 서브셸뿐(ADIR은 복제본 모드에서 실제 값 금지).
* 파괴적 명령 목록과 가드: `rm -f "$STATE"`(실제/모래상자 분리 + 모든 스크립트에서 `test ! -e F_SPEC` 뒤에 있어 커밋 뒤 재실행으로 상태가 지워지지 않음),
  `rm -rf "$t"`(mktemp), backfill `rm -rf "$SCR"`(정규식 `^/c/g[0-9]+(/…)?$` + 시작 시 미존재 + 스크립트가 만든 것만; 실측 F5~F8 전부 거부),
  carry `rm -rf "$STATE.d"`·`rm -f` 미추적 기록만·`worktree remove --force`·`branch -D`(상태 사슬 CHECK_OK→ARCHIVED→RECORDS + sha256 재대조, 단 B1).
  `checkout --`·`restore`·`reset`·`cherry-pick`·`apply`는 어느 스크립트에도 없다(backfill의 `checkout --detach`는 scratch 복제본).
* 게이트 캐시: `ensure_cache`는 `R`의 common dir에 쓰고, `gate_path`는 `R` HEAD의 `gate_config.json`에서 읽는다. 복제본에서 gate_path를 안 바꾸면 실제 gate를 **읽기만** 하고 `basename = gate/master` 대조가 어긋나면 멈춘다(안전 쪽).

### (2) 문서화된 전제 실패 시 멈춤(모래상자 실측, 전부 rc ≠ 0)

| 스크립트 | F1 HEAD ≠ gate/master | F2 role/ 브랜치 | F3 staged 변경 | 추가 상태 |
|---|---|---|---|---|
| v3_binding | :151 | :152 | `diff --cached --quiet` | 자연 상태(card 이미 병합) :156 `test ! -e F_SPEC` |
| v3_scope | :202 | :203 | 〃 | :215 묶기 병합 산출물 없음; `--render-tmp` 누락·`--drafts` 단독 exit 2 |
| b34 | :180 | :181 | 〃 | 착수 조건 2 미충족(128) |
| b26pre | :215 | :216 | 〃 | 조건 1 미충족; 양성 경로 pre→card→final→(push)→after-push 전부 OK 뒤 주입: state 없이 card :239, gate 이동 뒤 card :239, F_SPEC 미추적 존재 :245, 추가 커밋 뒤 final :284, push 없이 after-push :306, 조건 5 기록 제거 :225 |
| backfill | :225 | :226 | 〃 | 조건 1 미충족; v3count scratch 없음·이미 있음·`/tmp/x`·local scratch 없음 모두 거부 |
| b26_1 | :285 | :286 | 〃 | 조건 5 미충족; `--wt` 없이 `--repo` exit 2 |
| b26_1_carry | launch 상태 없음 :113 | B1 ≠ gate :118 | role 브랜치 ≠ 정확히 셋 :123 | worktree 없음 :127, RECORDS 없이 cleanup → 멈춤(브랜치 3개 그대로), CLEANED 없이 commit → 멈춤 |
| b33 | :232 | :233 | 〃 | 선행 판정 기록 없음; `--pred-missing-ok`면 :263 V7 그래프 입력 차이로 멈춤 |

### (3) 일관성

* 같은 것: 옵션 가드 문구·위치, `set -Eeuo pipefail` + `inherit_errexit` + ERR trap, `st_set/st_get`, `cache_dir`(basename = gate master 전체 sha), push 미실행·단독 호출 명령 출력, 승인 기록 바이트 단정(Python).
* 다른 것: m1(캐시 갱신), m6(선행 병합 기준), m8(measured rev 첫/마지막), m2(`--wt` 유무), S2는 conds가 있는 4개 공통.
* measured rev: 각 스크립트는 한 출처만 읽는다(초안별 앵커 1건 실측). b26pre·backfill·b34는 그 rev 이후 인용 대상 경로 변경을 막거나(Change-Id 허용 목록) 멈춘다 -- 실측 b26pre 양성 경로에서 동작.

### (4) EL1·role_guard

* 스크립트 안에 EL1 금지 형태(cherry-pick, apply, reset, 강제·삭제 push, `remote` 쓰기, `config` 쓰기, `--no-verify`, `commit -n`)는 없다.
* 오케스트레이터 단독 Bash 호출 판정(role_guard에 payload만 넣어 판정, 실행 안 함):
  `bash …/b34_launch.sh local1` rc 0, `bash …/b26pre_launch.sh --repo /c/g176/r --state … pre` rc 0,
  출력되는 `git -C <R> worktree add <W>/<id>-test -b role/test/<id> gate/master` rc 0, b33 kit-cmds의 `git -C C:/g999/r checkout -q -B master <sha>`·`remote remove origin` rc 0(작업 저장소 밖),
  출력되는 `git -C <R> push gate master:master`는 **지금은** rc 2 -- 실제 저장소에 `role/test/20260930-v3-exempt-binding`이 있어서(review29 Q-08). 스크립트 `pre`가 같은 조건을 먼저 본다(정상).
  모래상자 `--wt`를 실제 R과 섞은 `worktree add /c/g176/wt/…` 형태는 rc 2(§12 형태 아님) -- 실제 실행에서 섞일 일은 없다.
* 이 검토 자체에서: 실제 gate 경로를 인자로 쓴 첫 모래상자 구성 명령이 EL1에 거부돼(저장소 내부 인자) 복제본에서 가짜 gate를 만들었다. `$dr` 리다이렉트 명령도 EL1이 해석 불가로 거부해 스크립트 파일로 실행했다. 모래상자 구성 중 한 번 `cd /c/g176/r`을 썼다(모래상자 안, 이후 명령은 전부 `git -C` 절대 경로).

## 결론

실제 커밋 경로(pre→…→final)는 8개 모두 문서화된 전제가 깨지면 그 자리에서 멈춘다. 사용 전 필수 수정은 **B1(carry cleanup의 dispute 보존 우회)** 하나다.
S1(경로 별칭)은 운영 실수 한 번으로 모래상자 완화가 실제 저장소에 적용되는 경로라 공통 함수로 고칠 것을 권하고, S2(conds 거짓 0)는 card 사실 문장의 측정 출처라 고칠 것을 권한다.
