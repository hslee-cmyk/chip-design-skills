# review28 -- `05-role-separation` design v1.0 독립 검증

* 대상: `docs/02-design/features/gain-budget-gmid-sizing.05-role-separation.design.md` v1.0(미커밋, 신규)과 동반 개정(`git diff HEAD -- docs/01-plan docs/02-design/features/gain-budget-gmid-sizing.00-common.design.md`)
* 기준: 계획 v5.19(N0.4, N2.2, N3.10~N3.12, N4.2, N4.3, N6.1·N6.2 0.5, N7.2 U-15/16/38, N9.1·N9.2·N9.4, DEC-37~42), `00-common` v1.7(+v1.8 한 줄 개정) §3·§8·§9·§14·§17, 실제 코드(`install.py`, `.githooks/*`, `hooks/*`, `agent-quality/check_agents.py`), `agent7_self_concealment.md`
* 검증자: 독립 검증 agent(작성자 아님). 파일 수정 없음(이 보고서만). 실측 스크립트는 `$TEMP/rv28/`(저장소 밖)
* 판정 등급: **S1** 승인 차단(틀림·모순·구현 불가) / **S2** 승인 전 수정(구현자가 갈라질 모호함·빈칸) / **S3** 경미

---

## 0. 실측 요약

| # | 실측 | 결과 |
|---|---|---|
| E1 | git 2.52.0.windows.1, 임시 저장소에서 명령별 hook 발동 | `commit`: pre-commit→prepare-commit-msg→commit-msg→post-commit. **`merge --no-ff`(자동 병합 커밋): pre-merge-commit→prepare-commit-msg→commit-msg**(pre-commit 없음, **commit-msg 있음**). 충돌 해결 뒤 `git commit`: pre-commit·commit-msg 모두. `cherry-pick`·`revert`: prepare-commit-msg·post-commit만(pre-commit·commit-msg 없음). `commit-tree`: 없음. `rebase`: pre-rebase. **`am`: applypatch-msg·pre-applypatch만**(pre-commit·commit-msg 없음) |
| E2 | pre-commit 단계 메시지 | pre-commit은 인자 없이 메시지 확정 전에 돈다 → design의 "트레일러는 commit-msg에서"는 옳다 |
| E3 | `git show :<path>` | staged 판을 읽는다(staged=S, 작업 트리=W에서 `S`) |
| E4 | 상대 `core.hooksPath=.githooks` + worktree | worktree에서 커밋하면 **그 worktree의 `.githooks` 사본**이 돈다(MAIN-COPY/WT-COPY 둘 다 기록). 이 저장소의 현재 값은 **절대 경로** `C:\...\chip-design-skills\.githooks` |
| E5 | 체크아웃된 브랜치를 `git update-ref`로 이동 | `git status` = `M  f`(index가 옛 트리로 남아 **되돌리는 변경이 staged**) |
| E6 | §3.1 글자대로 `match_glob` 구현 + v5.19 N3.12.2 표 30행 파싱 | 셀 수 정상, 주체 5·조건 6값. "`<id>`는 change_id와 **정확히 같은 조각**"을 글자대로 읽으면 `docs/02-design/disputes/<id>.md`(code-author)·`.ai/verification/<id>.json`(auditor)가 **맞지 않는다**(거부). 조각 안 치환으로 읽으면 맞는다. 요청된 표본(test-author의 `tests/tools/x.py` 거부, 오케스트레이터 `disputes/_TEMPLATE.md` 허용, 레지스트리 거부)은 두 해석 모두 기대대로 |
| E7 | V4 규칙 (2)(이름→위치 인덱스 치환 `ast.dump`의 BinOp/Call 부분트리 해시)를 e329283 `estimate_area_budget` 본문과 self-test 기대식에 적용 | 함수 부분트리 9, test 부분트리 9, **공통 0** -- test가 `cold_start_alpha` 자리에 리터럴 `0.65`를 쓰므로 동형이 깨진다 |
| E8 | 표 셀 수(이스케이프 안 된 세로선) | 05 design 14표·계획 42표·00-common 16표 모두 불일치 0 |
| E9 | `core.autocrlf` | `true`(시스템 gitconfig). 추적 파일은 현재 `w/lf`지만 worktree 새 체크아웃은 CRLF가 된다 |

과거 사례 표지(`git show <커밋>` grep):

| 사례 | 표지 존재 | 비고 |
|---|---|---|
| e329283 | 있음(`estimate_area_budget` 본문 `(1 - cold_start_alpha) * a_1d + cold_start_alpha * a_2d_cold`, self-test `_area_cold_expected = (1 - 0.65) * _a1d_demo + 0.65 * _a2d_cold_expected`) | V4(2)가 글자대로는 못 잡는다(E7) |
| e5fbf92 | 있음, 단 **기준선 `.log` hunk에만**(diff 2233행). 코드(`stick_diagram.py:10165` print)는 이 커밋의 diff hunk가 아니다 | V4는 `.log`를 읽지 않는다 |
| 3250baa | 있음(`_l5c_result = None`, `if _l5c_result is not None:` 2곳) | V4(3)은 변환 절단 방식에 달림 |
| 1b9b4ea | **코드로는 없음** -- `except Exception: return`은 주석·print 문자열에만 있다(결함은 커밋 전에 고쳐졌다, agent7 #29 "같은 커밋 안에서 수정") | 재생은 합성 패치뿐 |
| 2e1944a | 있음(`grid_points_per_theta=1` → `=3`), 단 **소스 파일 `sizing_recipe.py`의 self-test** 안 | V5는 test diff만 본다 |

---

## 1. S1 -- 승인 차단

### P-01 [S1] 메인 세션 판정 범위가 계획과 모순되고, 오케스트레이터의 정상 작업을 전부 막는다
* **위치**: §4.2 첫 행("없으면 메인 세션 = `오케스트레이터`"), §5.1-4("역할 worktree 밖 경로는 거부"), §5.2 표 머리("`gmid-*` 역할과 메인 세션 모두"), 리다이렉트 행.
* **근거**: 계획 N3.12.2 hook 판정 범위는 "`agent_type`이 없고 **대상 경로가 위 표의 경로와 겹치는** 호출만 판정한다. 그 밖은 즉시 통과". design은 메인 세션의 모든 Edit/Write/Bash 쓰기를 `allowed('오케스트레이터', …)`로 판정하므로 표에 없는 경로(다른 skill 디렉터리, RTL, `workspaces/*` 스크래치, `$TEMP` 스크립트 결과 파일(WP-11), `~/.claude/projects/.../memory/*`, `> /dev/null`)는 모두 거부된다. 이 저장소는 analog-gmid-design 외 skill·RTL 작업을 함께 하므로 설치(④) 즉시 메인 세션의 일상 작업이 막힌다.
* **수정**: §5.1에 "메인 세션은 대상 경로가 N3.12.2 표의 어떤 행(주체 무관)의 경로 glob에 맞을 때만 `allowed`로 판정하고, 맞지 않으면 통과"를 명시. §5.2의 "worktree 밖"·리다이렉트 규칙도 메인 세션에는 같은 겹침 조건으로 제한. 공격 10(엔진 소스 거부)과 함께 "표 밖 경로(`$TEMP`, 다른 skill) 쓰기 통과"를 오거부 0 케이스로 추가.

### P-02 [S1] `<id>` 규칙을 글자대로 구현하면 dispute와 판정 기록을 쓸 수 없다
* **위치**: §3.1 `match_glob` 설명("`<id>`는 `change_id`와 정확히 같은 조각").
* **근거**: E6. `docs/02-design/disputes/<id>.md`, `.ai/verification/<id>.json`의 마지막 조각은 `<id>.md`/`<id>.json`이라 "조각 = `<id>`"가 아니다. 글자대로 구현하면 code-author의 dispute(N3.12.3 5)와 auditor의 판정 기록(N3.12.3 6)이 EL1·EL2에서 거부된다. `00-common` §17이 05에 넘긴 첫 항목("EL1 glob('자기 변경 id만')")이 바로 이것이다.
* **수정**: "`<id>`는 조각 안의 부분 문자열 토큰이고 `change_id`로 치환한 뒤 그 조각을 `*` 규칙으로 맞춘다. `change_id`가 없으면 `<id>`를 가진 패턴은 맞지 않는다. `change_id`는 `YYYYMMDD-<slug>` 형식(00-common §8.1)이어야 하고 `*`·`/`를 담지 않는다"로 정의. 공격 1·2 옆에 "`<id>.md` 자기 id 허용 / 남의 id 거부" 케이스를 넣는다.

### P-03 [S1] worktree 명령 시퀀스(§11)를 EL1이 막는다
* **위치**: §5.2 마지막 행("`git -C <역할 worktree 밖>`, 다른 worktree 경로를 쓰는 명령" -- 메인 세션 포함), §11 1·3·4·6·정리, §11 끝 문단.
* **근거**: 메인 세션의 worktree는 메인 저장소다. `git worktree add ../wt/<id>-test …`(1·4·6), `git worktree remove ../wt/…`(정리), `git -C ../wt/<id>-audit merge`(6)는 모두 다른 worktree 경로를 쓰는 명령이다. 예외는 6의 `merge` 하나뿐이라 1·4·정리가 거부된다. 3의 auditor `git -C ../wt/<id>-test rev-parse HEAD`도 auditor 자기 worktree 밖이다(게다가 audit worktree는 6에서야 생긴다 → P-27).
* **수정**: 메인 세션에 허용하는 worktree 관리 명령을 열거(`git worktree add <../wt/<id>-<role>> -b role/<role>/<id> <rev>`, `git worktree remove`, §11-6 병합)하고 패턴으로 판정. 읽기 전용 `git -C … rev-parse/log/show`는 금지 대상에서 뺄지 명시. 공격 재생 ⑤에 "§11 전 과정을 설치 상태에서 한 번 실행"을 오거부 0 케이스로 추가.

### P-04 [S1] §11-6 병합 커밋이 `commit-msg`(EL3)에서 막힌다
* **위치**: §7.2-2·3, §3.2 허용 조합표 `doc` 행("병합 커밋의 트레일러이기도 하다"), §11-6.
* **근거**: E1 -- `git merge --no-ff`는 pre-commit은 안 돌리지만 **commit-msg는 돌린다**. §11-6 명령에는 `-m`이 없어 기본 메시지 "Merge branch …"에 `Role:` 트레일러가 없다 → 역할 경로(소스)가 들어 있으므로 차단. `-m "...Role: doc"`을 줘도 병합 커밋의 첫 부모(test 커밋) 대비 변경은 **소스**인데 `doc`의 허용 분류는 문서·데이터뿐이라 §7.2-3이 차단한다. 충돌이 나서 `git commit`으로 마무리하면 pre-commit까지 돈다. §8.2-4의 "병합 커밋은 두 부모 쪽 커밋을 대신 검사"는 EL4에만 있고 EL3에는 없다.
* **수정**: `commit-msg`/pre-commit이 병합 중(`MERGE_HEAD` 존재 또는 부모 2개)을 감지하면 `Role: doc`만 요구하고 분류 검사는 하지 않는다(EL4가 두 부모 쪽을 검사)는 규칙을 §7.2에 넣고, §11-6 명령에 `-m "<요약>" -m "Role: doc"`을 적는다. 공격 재생에 "§11-6 병합 커밋 통과"(오거부 0)와 "병합이 아닌 커밋의 `Role: doc` + 소스 차단"을 둘 다 넣는다.

### P-05 [S1] merge gate가 가리키는 브랜치가 없고, 브랜치·트레일러 일치 검사는 항상 실패한다
* **위치**: §11-6(`git worktree add ../wt/<id>-audit <test 커밋>` -- `-b` 없음), §11-7(`merge <base> role/audit/<id>`), §8.2-4("브랜치 이름 `role/<역할>/<id>`와 트레일러 역할이 맞는지").
* **근거**: (a) 6은 detached HEAD라 `role/audit/<id>`가 생기지 않는다 → 7이 실패. 또 `change_id`가 브랜치 `role/<역할>/<id>`에서 온다고 계획 N3.12.2가 정의했으므로 audit worktree의 `change_id`가 없어 auditor는 `.ai/verification/<id>.json`을 쓸 수 없다(P-02와 겹쳐 이중 차단). (b) `git rev-list <base>..role/audit/<id>`에는 test 커밋(`Role: test`), code 커밋(`Role: code`), 병합 커밋(`Role: doc`), 판정 기록 커밋(`Role: audit`)이 모두 들어 있다. "브랜치 이름과 트레일러 역할 일치"를 이 목록에 적용하면 audit 외 커밋이 전부 불일치로 거부된다.
* **수정**: 6을 `git worktree add ../wt/<id>-audit -b role/audit/<id> <test 커밋>`으로. §8.2-4를 "커밋마다 소속 구간으로 판정: `base..role/test/<id>` = `Role: test`, `role/test/<id>..role/code/<id>` = `Role: code`, 병합 커밋 = `Role: doc`(부모가 test·code 끝), 그 뒤 = `Role: audit`"처럼 구간 규칙으로 다시 쓴다(세 브랜치가 모두 존재해야 함을 판정 조건에 넣는다).

### P-06 [S1] `update-ref`로 base를 옮기면 메인 저장소 index가 옛 트리로 남아 다음 커밋이 병합을 되돌린다
* **위치**: §8.2-10("audit worktree의 병합 커밋으로 base를 fast-forward(`git update-ref`…)"), §5.2(`git reset --hard` 거부).
* **근거**: E5. base(`master`)는 메인 worktree에 체크아웃돼 있다. `update-ref`는 index·작업 트리를 바꾸지 않으므로 `git status`가 병합 내용을 **되돌리는 staged 변경**으로 보인다. 오케스트레이터의 다음 `git commit`(계획서 개정 등)이 그 되돌림을 함께 커밋한다(EL3가 `Role: doc`+소스로 막으면 이번에는 복구 수단인 `git reset --hard`·`git checkout -- <tests>`·`git restore <tests>`가 EL1에 막혀 교착). 또 EL1/EL2 hook은 `${CLAUDE_PROJECT_DIR}/tools/gates`(메인 작업 트리)를 import하므로 게이트 변경 병합 뒤에도 hook은 옛 코드로 돈다.
* **수정**: 메인 worktree가 base를 체크아웃하고 있으면 merge gate가 `git -C <메인> merge --ff-only <audit head>`(깨끗한 작업 트리 전제, 아니면 거부)로 옮기거나, base를 체크아웃하지 않는 운영(메인 worktree는 별도 브랜치)을 규정. 어느 쪽이든 공격 재생에 "병합 뒤 메인 `git status` 깨끗함"을 넣는다.

### P-07 [S1] EL3·EL4가 분류(5종) 단위로만 검사해 쓰기 경로표의 경로 제약이 병합 시점에 사라진다
* **위치**: §3.2 허용 조합표와 그 주("`read_write_paths` 결과를 5분류로 사상해 계산"), §7.2-3, §8.2-4.
* **근거**: code-author의 행에는 문서 분류 경로(레지스트리, dispute)가 있으므로 `code`는 문서 분류를 허용해야 한다(표는 "(dispute는 문서)"만 적고 레지스트리를 빠뜨렸다). 그러면 `Role: code` 커밋이 `.ai/approvals/**`나 `docs/01-plan/**`(같은 문서 분류)를 바꿔도 §7.2-3은 통과시킨다. §8.2-4는 "§7.2의 트레일러·분류·동시 변경 규칙"만 다시 적용하므로 공격 5(EL1~EL3를 거치지 않은 커밋)로 **승인 기록을 위조한 code 커밋**이 EL4를 통과하고, 그 위조 기록이 §8.2-3(head 판정 표 승인)·§8.2-5(V5·topology 승인)를 만족시킨다. `audit`의 "`.ai/verification/<id>.json`·`<id>/**`만" 제약은 분류가 아니라 경로라 `allowed_classes(role)`로는 계산되지 않는다 -- "표는 계산 결과"라는 주장과 맞지 않는다. 계획 N3.12.4 EL4는 "트레일러·**경로**·브랜치 역할 일치"를 요구한다.
* **수정**: EL3 3과 EL4 4에 "커밋의 모든 변경 경로가 트레일러 역할에 대응하는 주체의 `allowed(actor, path, ctx)`를 만족"을 추가(역할↔주체 대응표: code↔gmid-code-author, test↔gmid-test-author, audit↔gmid-verification-auditor, doc↔오케스트레이터를 명시). 분류 표는 "소스·test 동시 변경 금지" 판정용으로만 남긴다. 공격 5에 "code 커밋이 `.ai/approvals/x.md` 추가" 케이스를 넣는다.

### P-08 [S1] base에 직접 커밋하면 EL4를 통째로 건너뛴다(EL3는 브랜치를 보지 않는다)
* **위치**: §7.2, §4.2 첫 행("`gmid-*`가 아니고 비어 있지 않으면 역할 밖, 즉시 통과"), §12.1 ④ matcher, §8.2-5, §15.
* **근거**: EL4는 병합에서만 돈다. EL3는 트레일러·분류만 보므로 `master`에서 `Role: code` 소스 커밋이 통과한다. 소스를 메인 저장소에 쓰는 경로가 여럿 있다: (a) 오케스트레이터가 `general-purpose` 등 `gmid-*`가 아닌 subagent를 띄우면 §4.2에 따라 hook이 즉시 통과(DEC-37 우회), (b) 공격 11이 통과를 요구하는 RTL agent, (c) 이 환경의 **PowerShell 도구**는 matcher(`Edit|Write|NotebookEdit|Bash|Read`)에 없어 메인 세션이 `Set-Content`로 엔진 소스를 써도 EL1·EL2가 보지 않는다. 같은 이유로 오케스트레이터의 topology(`승인 기록` 조건)·structure(`status 전이만` 조건) 변경은 §15대로 base 직접 커밋이라 §8.2-5 검사를 한 번도 거치지 않는다 -- 그 두 조건은 정상 경로에서 발동하지 않는 게이트다(WP-02).
* **수정**: EL3에 "base 브랜치(`gate_config.base_branch`)에서의 커밋은 `Role: doc`만 허용하고, `doc`의 경로는 P-07의 경로 판정을 받는다. `승인 기록`·`status 전이만` 조건은 EL3가 staged 판에 대해 판정한다(topology diff 해시 승인 기록 탐색, structure.json의 `status` 외 필드 불변)"을 넣는다. matcher에 `PowerShell`(그리고 존재하면 `MultiEdit`)을 추가하고, 메인 세션이 띄운 비-`gmid` agent의 판정은 메인 세션 규칙(P-01의 겹침 조건)을 적용한다고 명시(계획 hook 판정 범위 문구도 같이 고칠 것). 공격 재생에 "master 직접 `Role: code` 커밋 차단", "PowerShell 쓰기 거부", "general-purpose agent의 엔진 소스 Edit 거부"를 넣는다.

### P-09 [S1] hook 실행기의 예외는 Claude Code에서 통과(fail-open)가 된다
* **위치**: §5.1-1(파싱 실패만 exit 2), §6, §12.1 ④(복사본은 얇은 실행기, `${CLAUDE_PROJECT_DIR}/tools/gates`를 import).
* **근거**: Claude Code hook은 **exit 2만 차단**이고 그 밖의 0 아닌 종료는 비차단 오류로 표시만 하고 도구 호출이 진행된다. 얇은 실행기의 `ImportError`(메인 작업 트리에 `tools/gates`가 없거나 깨짐, `CLAUDE_PROJECT_DIR` 미설정), `git` 호출 실패, 판정 로직 예외는 파이썬 기본 exit 1 → 통과한다. 기존 `guard-bash-nul.py`의 fail-open을 지적한 §5.1-1과 같은 결함이 import 단계에 남는다.
* **수정**: 실행기 전체를 `try: … except BaseException: stderr에 사유; sys.exit(2)`로 감싸고(메인 세션 겹침 판정 전의 실패 포함), 공격 재생에 "`tools/gates/role_hooks.py`를 이름만 바꿔 import 실패 → 거부(exit 2)" 케이스를 넣는다.

### P-10 [S1] 역할 ↔ worktree 결합을 구현할 수단이 없다(U-15 기본안 A와 `agent_type` 경로 모두)
* **위치**: §4.2, §5.1-4("그 역할 worktree 루트 기준"), §6-2, §11, §13.
* **근거**: (a) 이 세션의 subagent 실행 규칙상 agent 스레드의 Bash cwd는 호출마다 기본 작업 디렉터리(메인 저장소)로 되돌아간다. 기본안 A(호출자 `cwd`의 worktree 이름으로 역할 판정)는 subagent를 메인 세션(`오케스트레이터`)으로 판정한다. (b) `agent_type`이 있는 경우에도 design은 "그 역할의 worktree 루트"와 `change_id`를 어디서 얻는지 정하지 않았다. cwd가 메인이면 역할이 메인 저장소 경로를 "자기 worktree"로 쓰고, 실제 `../wt/<id>-<role>` 쓰기는 "worktree 밖"으로 거부된다. (c) 이 환경의 `EnterWorktree`(path 전환)는 `.claude/worktrees/` 아래 worktree만 받는다(도구 설명) -- `../wt/`는 대상이 아니고, 계획은 frontmatter `isolation`도 금지한다. 역할을 자기 worktree에 묶는 방법이 문서 어디에도 없다.
* **수정**: ② 실측 항목에 "subagent의 Edit/Write/Bash 호출 시 hook `cwd` 값과 Bash cwd 유지 여부"를 추가하고, 결합 규칙을 명시: 예) worktree를 `.claude/worktrees/<id>-<role>`에 두고 역할 agent는 첫 동작으로 `EnterWorktree(path=…)`, hook은 `agent_type`(역할)과 **대상 경로가 속한 worktree**(`git -C <대상 dir> rev-parse --show-toplevel` + 브랜치 `role/<role>/<id>`)가 같은 역할일 때만 허용. 이 규칙이 U-15 선택지 표와 계획 N3.12.3의 `../wt/` 경로를 바꾸면 계획 개정으로 올린다.

### P-11 [S1] V4 규칙 (2)의 알고리즘은 자신이 인용한 사례 e329283을 잡지 못한다
* **위치**: §9 V4 행, §12.3 e329283 행("V4 규칙 (2)").
* **근거**: E7. self-test 기대식은 `cold_start_alpha` 자리에 리터럴 `0.65`, `a_1d` 자리에 `_n_fingers_demo * 1.0` 결과 변수를 쓴다. "이름을 위치 인덱스로 치환한 `ast.dump`" 동형은 Name과 Constant가 달라 부분트리 해시가 하나도 겹치지 않는다(공통 0/9). 따라서 원 결함을 그대로 옮긴 재생은 V4 PASS가 되고, 재생을 통과시키려면 패치를 검출기에 맞게 고쳐 써야 한다(작성자=검증자 은폐, WP-13).
* **수정**: 규칙 (2)의 정규화를 "Name과 Constant를 모두 잎 자리표시자로 치환(값 무시), 피검 함수의 지역 대입을 인라인 전개한 뒤 반환식 부분트리와 비교"처럼 정의하고, e329283 원식을 **리터럴 그대로** 옮긴 재생이 FAIL함을 0.5 증거로 요구한다. 계획 N4.2 V4 (2) 문구가 바뀌면 계획 개정으로 올린다.

---

## 2. S2 -- 승인 전 수정

### P-12 [S2] 기존 pre-commit의 조기 `exit 0` 때문에 "그 뒤에 부른다"는 역할 검사가 안 돈다
* **위치**: §7.1("기존 agent 검사는 그대로 두고, 그 뒤에 `role_commit_gate.py`를 부른다").
* **근거**: `.githooks/pre-commit` 10~11행 `changed=$(… agents/*.md …)`; `[ -z "$changed" ] && exit 0`. 글자대로 뒤에 붙이면 agent 정의를 바꾸지 않는 모든 커밋에서 역할 검사가 skip된다(WP-02). 파이썬 탐색도 agent 분기 안에 있다.
* **수정**: 파이썬 탐색(실패 시 exit 1)을 맨 앞으로, agent 검사는 `changed`가 있을 때만, 역할 검사는 항상 실행하는 구조를 §7.1에 적는다. ⑤ 재생에 실제 `git commit`으로 공격 3을 넣는다(P-13).

### P-13 [S2] EL3 배선이 설치 뒤에 증명되지 않고, 어느 판의 게이트 코드가 도는지 정해지지 않았다
* **위치**: §12.1 ③·④·⑤, §16 '설치 후 거부' 행.
* **근거**: ⑤는 공격 1·2·4·10·11만 실제 호출로 재현한다. `.githooks/pre-commit`·`commit-msg`의 실제 발동(공격 3, 16 (i)(a)·(ii)(a))은 ③의 함수 직접 호출로만 증명된다(WP-01: 배선 미증명). 또 E4: 현재 `core.hooksPath`는 절대 경로(메인 `.githooks`)인데 ④는 "`git config core.hooksPath .githooks` 확인"이라 적어 상대 경로로 바꿀 여지가 있고, 상대 경로면 worktree 자기 사본이 돈다. 어느 쪽이든 pre-commit 안의 `tools/gates/role_commit_gate.py` 상대 호출은 **역할 worktree의 사본**(게이트 변경 중인 code-author가 고칠 수 있는 판)을 실행한다. EL1·EL2는 메인 작업 트리 판, EL4는 base 판을 쓰므로 세 판이 어긋난다.
* **수정**: `core.hooksPath` 값을 절대/상대 중 하나로 확정하고, `.githooks/*`는 게이트 코드를 `git -C <메인> show <base>:tools/gates/…`로 얻거나 메인 저장소 절대 경로의 판(깨끗함 확인)을 import하도록 규정. ⑤에 공격 3·16 (i)(a)를 실제 `git commit`으로 추가.

### P-14 [S2] ④의 순서·hook 반영 시점·`install.py` 부수효과가 비어 있다
* **위치**: §12.1 ②·④·⑤.
* **근거**: (a) ④는 hook 설치 뒤 `.githooks` 갱신을 적는데, 계획 N3.12.2 문단은 사용자 경로 쓰기를 "④ 단계(**hook 설치 전**)"로 한정한다. 설치된 EL1이 반영되면 `.githooks/**`에 오케스트레이터 행이 없어 거부된다. (b) Claude Code가 세션 중 settings의 hook 변경을 언제 반영하는지(재시작·`/hooks` 검토 필요 여부)가 ②·⑤의 전제인데 확인 절차가 없다(숨은 열린 질문). ② 임시 agent 정의가 세션 중 인식되는지도 같다. (c) `install.py _register_hook`은 `tag`(파일 이름 stem) 부분 문자열로 중복을 판정해 **이미 등록된 hook의 matcher를 갱신하지 않는다** -- matcher를 바꾼 재설치가 조용히 무시된다. (d) ② 더미 hook의 settings 등록을 지우는 단계가 없다(파일만 지움 → 없는 스크립트를 부르는 hook). (e) `--only hooks`는 `hooks/*.py` 전부(`guard-bash-nul`, `guard-submodule-formal`, `kb-preflight-nudge`)를 프로젝트 settings에도 등록한다.
* **수정**: ④ 순서를 `.githooks` 갱신 → 커밋 → hook 설치로 바꾸고, ②·⑤ 앞에 "세션 재시작(또는 `/hooks` 반영) 후 probe로 활성 확인"을 넣는다. 등록 검증(§12.1 둘째 점)을 "matcher·event 불일치면 settings에서 해당 항목을 지우고 재등록"으로, ② 정리에 settings 항목 삭제를 추가. 부수 등록 hook을 허용할지 사용자 확인 항목으로 적는다.

### P-15 [S2] EL1의 우회 git 명령 목록이 불완전하다
* **위치**: §5.2, §14 첫 행.
* **근거**: base 참조를 hook 없이 옮기거나 hook을 끄는 명령이 목록 밖에 있다: `git branch -f`, `git checkout -B`/`git switch -C`, `git reset --soft|--mixed <rev>`(`--hard`만 거부), 배관 `git hash-object -w`·`update-index --cacheinfo`·`write-tree`, `git -c alias.x=commit-tree x`, 환경 변수 `GIT_CONFIG_COUNT/GIT_CONFIG_KEY_0=core.hooksPath/GIT_CONFIG_VALUE_0`, `git replace`(merge gate의 git 읽기를 바꾼다). E1: `am`은 applypatch-msg·pre-applypatch만 돌린다(목록에 있으나 근거는 "pre-commit을 거치지 않음"만 적힘). 계획은 EL4를 "앞 겹을 모두 우회한 커밋"의 방어로 두지만 P-08대로 base 직접 이동에는 EL4가 없다.
* **수정**: 목록을 "참조 이동(`branch -f`, `checkout -B`, `switch -C`, `reset <rev>` 전부, `update-ref`, `symbolic-ref`), 배관 커밋 생성, `-c`/환경 변수로 설정 주입, `replace`"로 확장하고, merge gate의 git 호출에 `GIT_NO_REPLACE_OBJECTS=1`을 명시. 목록은 완전할 수 없으므로 P-08의 EL3 base 규칙이 최종 방어임을 적는다.

### P-16 [S2] EL2의 메인 세션 적용 여부가 없고, 메인 저장소에는 항상 역할 밖 변경이 있다
* **위치**: §6-1·2·3.
* **근거**: §4.2로 메인 세션도 역할(`오케스트레이터`)이 되는데 §6은 "그 역할 worktree"의 `git status`를 본다. 메인 저장소는 도구가 계속 쓰는 파일로 늘 더럽다(이 세션 시작 git status: `.bkit/audit/*.jsonl`, `.bkit/state/*`, `skills/analog-gmid-design/assets/.bkit/runtime/*` 수정·미추적). `.gitignore`는 `.bkit/runtime/`만 무시한다. 적용하면 모든 Bash 뒤 exit 2가 난다.
* **수정**: EL2는 `gmid-*` 역할에만 적용한다고 명시하거나, 메인 세션은 P-01의 겹침 경로만 대조. 역할 worktree에서 도구 부산물(`.bkit/**` 등)이 생기는지도 ② 실측 항목에 넣는다.

### P-17 [S2] test-author의 소스 열람을 Grep 도구로 할 수 있다
* **위치**: §5.3, §13 `gmid-test-author` tools(`Read, Edit, Write, Glob, Grep, Bash`).
* **근거**: DEC-38은 소스 경로 Read 거부다. Grep 도구는 일치 줄 내용을 돌려주므로 소스 본문을 읽을 수 있고 matcher에 없다(Bash `cat`은 계획이 한계로 인정했지만 Grep은 언급 없음).
* **수정**: test-author tools에서 Grep을 빼거나 matcher에 `Grep|Glob`을 넣고 `path`가 소스 분류면 거부. 한계 문장에 남는 경로(Bash)만 적는다.

### P-18 [S2] 분류·쓰기 경로표 개정이 계획과 어긋나거나 빈칸을 남긴다
* **위치**: §3.2 분류 표, §2 마지막 문단, §3.1 `부트스트랩` 조건, 계획 N3.12.2 표.
* **근거**: (a) 계획 N3.12.4 EL3의 5분류는 도구 = `assets/tests/tools/**`, `tools/**`, 문서 = `docs/**`, `.ai/**`다. design은 `hooks/role_*.py`를 도구에, `agents/gmid-*.md`를 문서에 더했다(계획 미개정, N9.4 "재서술 필요하면 정본을 고친다" 위반). (b) `hooks/role_*.json`(install.py sidecar -- matcher·event를 정한다), `tools/gates/gate_config.json`(`base_branch`, `reachability_roots`), `tools/gates/requirements.txt`는 부트스트랩 뒤 **어느 주체도 쓸 수 없다**(code-author 행은 `tools/gates/*.py`, `hooks/role_*.py`뿐). §2는 "부트스트랩 뒤 게이트 변경은 N3.12.3 흐름"이라 하지만 이 파일들은 흐름으로도 못 바꾼다. (c) 계획의 `부트스트랩` 조건은 "N3.12.6 ① 단계 한정"인데 design §3.1은 "hook 설치(④) 뒤 거짓" -- ③에서 공격이 실패해 게이트를 고치는 경우의 권한이 두 문서에서 다르다.
* **수정**: 계획 N3.12.4 5분류에 두 경로를 넣거나 design에서 빼고, 쓰기 경로표에 `hooks/role_*.json`·`tools/gates/*.json`·`tools/gates/requirements.txt`(code-author, 게이트 변경) 행을 추가(승인 기록 필요). `부트스트랩` 구간을 ①~④ 전으로 계획·design 한 곳에서 같게 정한다.

### P-19 [S2] `00-common` §9.1의 '변경' 정의가 개정되지 않아 해시 정의와 어긋난다
* **위치**: `00-common` v1.8 §9.1 "판정 표 변경 검사: … **파싱 값**(`v_intro`, `ic_parts`, `ic_test`, `phase_order`)이 다르면 변경", design §17-2.
* **근거**: v1.8 한 줄 개정은 §8.2(해시 입력)만 바꿨다. §9.1을 따라 구현하면 쓰기 경로표만 바꾼 계획 개정은 '변경 아님'이 되어 EL3·EL4가 승인을 요구하지 않는다 -- 계획 N3.12.4·N4.3 공격 16 (i)(v5.19 개정)과 모순. 머리 Status에도 "승인 뒤 개정"과 "사용자 승인 대기"가 함께 적혀 있다.
* **수정**: §9.1 해당 문장에 `write_paths`를 추가(또는 "비교 대상 = §14.2 해시 입력 객체 전체"로)하고 Status 문구를 정리. design §17의 개정 목록에 §9.1을 추가.

### P-20 [S2] 과거 사례 재생의 원천·변환 규칙이 사례와 맞지 않는다
* **위치**: §12.3 표와 두 문단.
* **근거**(§0 표): e5fbf92의 표지는 기준선 `.log` hunk에만 있다 -- "`git show <커밋> -- <파일>`에서 표지 hunk"를 고르면 V4 입력이 될 코드가 없다(코드는 `stick_diagram.py` 파일 내용, 도입은 e329283). 1b9b4ea는 결함 코드가 커밋에 없다(주석·print에만) -- 재생은 공격 9와 같은 합성 패치가 되어 독립 증거가 아니다. 2e1944a는 소스 파일 self-test 안의 변경이라 "test diff"만 보는 V5 입력이 아니며, §12.3의 변환 규칙은 V4 (5)·(3)만 다룬다. 변환(인라인 self-test → `tests/` 함수)의 절단·치환을 작성자(오케스트레이터)가 정하므로, P-11처럼 검출기에 맞춰 패치를 바꾸는 것을 막을 규칙이 없다(WP-13).
* **수정**: 사례마다 원천(커밋:파일:행)을 표로 고정하고, 변환 규칙을 기계적으로 정의(원 식·리터럴·조건 구조를 그대로 유지하고 `if __name__` 섹션 경계 = test 함수 하나, 10-test-separation TS2 매핑과 같은 규칙). 1b9b4ea는 "원 커밋에 결함 코드 없음 → 결함 설명(주석)으로 재구성"임을 표에 적고 사용자 확인 항목으로. 2e1944a는 변환 규칙과 V5 '격자' 판정 입력(P-22)을 함께 적는다.

### P-21 [S2] V3 인벤토리가 직접 호출 test만이라 내부 함수 변경은 항상 FAIL한다
* **위치**: §9 V3 ③·④.
* **근거**: "그 함수 이름을 부르는 test 함수"만 실행하면 `_hr_*` 같은 내부 함수의 변이는 어떤 test도 실행하지 않아 모두 살아남고 FAIL이다(DEC-37 흐름의 대부분 변경이 내부 함수). 등가 변이 면제의 "변이 id" 형식도 정의가 없어 승인 기록과 대조할 수 없다.
* **수정**: 인벤토리를 "정적 호출 그래프(V7과 같은 그래프)에서 그 함수에 도달하는 test"로, 변이 id를 `<모듈>:<함수>:<연산자>:<AST 노드 경로>`처럼 결정론적으로 정의하고 `redteam/v3_survivor`에 내부 함수 케이스를 넣는다.

### P-22 [S2] V5 8패턴의 판정 입력이 비어 있다
* **위치**: §9 V5 행.
* **근거**: '허용오차 확대'·'격자 확대'·'픽스처 입력 리터럴 변경'은 어떤 이름·인자가 허용오차/격자/픽스처 입력인지 알아야 AST로 판정된다. 목록을 구현자가 임의로 정하면 WP-03(임의 상수)이고 구현자마다 달라진다. 2e1944a(`grid_points_per_theta`)가 그 예다.
* **수정**: 패턴별 AST 판정식을 적고, 이름 목록이 필요하면 선언 위치(예: 계획 또는 `gate_config.json`의 한 곳)와 변경 권한을 정한다.

### P-23 [S2] `--gmid-strict` 비어 있지 않은 집합의 표기가 정해지지 않았다
* **위치**: §14 '빈 엄격 집합' 행, `00-common` §8.1(`--gmid-strict <집합>` 공백 형식)·§9.3.
* **근거**: design은 빈 집합만 `--gmid-strict=`로 정했다. merge gate는 V1 명령 문자열을 대조하므로 `--gmid-strict=a,b`와 `--gmid-strict a,b` 중 하나로 고정돼야 한다(공백 형식은 빈 값일 때 다음 토큰을 값으로 먹는다).
* **수정**: "항상 `--gmid-strict=<정렬·쉼표 구분>` 한 토큰, 비교는 `shlex.split` 뒤 토큰 단위"로 고정하고 `00-common` §8.1 예시 명령도 맞춘다.

### P-24 [S2] N9.2 필수 절 3·4·5가 없고, 사례 기대 메시지가 없다
* **위치**: 문서 전체(§1 범위 표에 해당 절 없음), §12.3.
* **근거**: N9.2-3 판정식(예: V3 상수 변이 단위, 캐시 상한 같은 규칙을 한 절에 모음), N9.2-4 실패 경로(N3.14 클래스·exit code -- 게이트 도구는 0/1/2, hook은 2를 쓰는데 N3.14와의 관계 미기술), N9.2-5 역할별 산출물(spec card 목록 -- 0.5는 spec card가 없다면 "없음, 부트스트랩 ①~③"이라고 명시해야 함)이 절로 없다. N9.1 05 행의 "사례 5 재생 절차와 **기대 메시지**"는 §12.3에 규칙 번호만 있다.
* **수정**: 세 절을 추가(없으면 "해당 없음 + 이유")하고 §12.3 표에 기대 메시지 열을 넣는다.

### P-25 [S2] MG0 DoD가 기계 판정이 아니고 계획 안의 모순을 DoD 문장으로 덮는다
* **위치**: §15, §16 MG0 행.
* **근거**: N6.2 0.5는 "5회로의 `_paper_target_spec` 컨테이너명 0"인데 N3.16 MG0 행은 "문헌 `supply_v` → `_paper_target_spec.supplies_v`"로 `_paper_target_spec`을 남긴다(현재 5회로 모두 `grep -c` = 2). design은 "대상은 사용자 확정 스펙을 담던 컨테이너 -- 대조 목록은 MG0 반영 커밋의 net 표와 함께 적는다"로 판정을 사람 서술에 넘겼다. `grep -c '"vs"'`는 안내문이 `"vs"`를 인용만 해도 걸린다.
* **수정**: 계획 N6.2·N3.16 모순을 N7(또는 계획 개정)로 올리고, DoD를 JSON 파싱 기준 명령(예: "5회로에서 `_declared_target_spec` 키 존재, `_paper_target_spec` 안에 사용자 확정 필드 0")으로 고정.

### P-26 [S2] 공격 12의 0.5 처리와 소재가 비어 있다
* **위치**: §12.1 ③("공격 1~12·15·16"), §12.2 12행, §16 첫 행.
* **근거**: ③은 공격 12를 0.5 재생 대상으로 적어 v5.19 개정(12는 6a, 0.5는 xfail 선언만)과 모순. "거부 test의 xfail 선언"을 어디에(tests/** 는 부트스트랩 중에도 오케스트레이터 경로가 아니고, `redteam/`은 pytest 수집 대상이 아니다) 누가 쓰는지, `run_all.py --phase 0.5`가 xfail 선언을 어떻게 "확인"하는지 없다. 계획 N6.2 문구("xfail 선언의 거부 로그")도 뜻이 맞지 않는다.
* **수정**: ③을 "1~11·15·16"으로, 12의 선언 위치·작성 주체(예: Phase 1 CC-3과 함께 test-author)와 0.5 DoD의 확인 명령을 정하거나, 0.5 DoD에서 12를 빼고 6a로 넘긴다(계획 N6.2 문구도 수정).

### P-27 [S2] §11-3 freeze 단계의 auditor 실행 위치가 없다
* **위치**: §11-3.
* **근거**: audit worktree는 6에서 생긴다. 3에서 auditor는 `../wt/<id>-test`에서 실행해야 하는데 U-15 A로는 그 worktree의 역할 = test로 판정된다. auditor가 쓰는 판정 기록 초안의 위치(어느 worktree, 커밋 여부)도 없다.
* **수정**: 3 전에 audit worktree를 만들거나(`role/audit/<id>`를 test 커밋에서 분기) freeze를 merge gate가 test 브랜치 끝에서 계산하도록 바꾸고 초안 위치를 적는다.

### P-28 [S2] `.claude/hooks` 사본과 base blob의 바이트 비교는 줄 끝 변환에 흔들린다
* **위치**: §12.1 셋째 점("`.claude/hooks/role_*.py`와 base의 `hooks/role_*.py` 바이트 해시가 같은지").
* **근거**: E9 `core.autocrlf=true`. `install.py`는 작업 트리 파일을 `shutil.copy2`로 복사하므로 작업 트리가 CRLF 체크아웃이면 사본은 CRLF, base blob은 LF다 → 정상 설치도 거부.
* **수정**: 비교를 `git hash-object --path=hooks/<name> .claude/hooks/<name>`(eol 필터 적용) 대 `git rev-parse <base>:hooks/<name>`으로 정의.

---

## 3. S3 -- 경미

* **P-29** §13 "`check_agents.py` 규칙을 모두 PASS" vs §16 "FAIL 0". `check_agents.py`의 FAIL 규칙은 name·description·model·tools·R4-scope뿐이고 나머지는 WARN. 둘 중 하나로 통일.
* **P-30** 동반 개정의 계획 내부 불일치: N3.12.4 EL2 행은 아직 `hooks/role_diff_guard.py`(단일), EL1 행 도구 목록에 Read 없음(design은 matcher에 Read 추가), N3.12.2 문단은 '사용자만' 경로라 부르지만 표 주체는 `사용자`, N4.3 12행에 '실행 Phase = 6a' 표기 없음.
* **P-31** §3.1 캐시 `.git/gmid-gate-cache/`: 역할 worktree에서 `.git`은 파일이다 → `git rev-parse --git-common-dir` 기준으로. 병렬 hook의 "옛 파일 삭제" 경합(원자적 쓰기·삭제 실패 무시 규칙) 명시.
* **P-32** §2 'U-15' 행 부류 `AI 제안→사람 확정`: `00-common` §3.1 1번은 "구조로 가를 수 없는 회로 해석"에 한정된다. 사용자 결정(N7.2)은 승인 기록 항목으로 적는 편이 양식에 맞다. '실측 기록'을 `코드`로 둔 것도 고정 수단이 '실행 로그 원문'뿐이라 3.1의 '정본 구현 + test'와 맞지 않는다.
* **P-33** matcher에 `MultiEdit` 없음(기존 `hooks/kb-preflight-nudge.json`은 `Edit|Write|MultiEdit`). 도구가 존재하면 추가.
* **P-34** 신뢰 가정 미기술: 오케스트레이터는 `.ai/approvals/**`를 조건 없이 쓸 수 있으므로(계획 N3.12.5 "오케스트레이터만 쓴다") `plan_tables` 게이트는 "사용자 승인"이 아니라 "승인 기록 파일 존재"를 증명한다. 이 한계를 §14에 적는다.
* **P-35** `tools/gates/requirements.txt`의 고정 판(현재 설치 4.26.0)을 실제 실행 환경과 대조하는 곳이 없다(WP-01). merge gate 시작 시 `importlib.metadata.version("jsonschema")` 대조를 넣는다.
* **P-36** §8.2-10 "audit worktree의 **병합 커밋**으로 fast-forward" -- 판정 기록 커밋이 그 위에 있으므로 대상은 audit 브랜치 끝이다. §8.2-6 판정 기록을 읽는 트리(head)도 명시.

---

## 4. 점검 항목별 결론

| 점검 | 결론 |
|---|---|
| 1 커버리지(N9.1 05 행, N6.2 0.5 DoD, `00-common` §17) | 항목은 모두 절이 있다. 실질 결함: EL1 `<id>` 규칙(P-02), 허용 조합표(P-07), 우회 명령 전수(P-15), 사례 기대 메시지(P-24), MG0 DoD(P-25), 공격 12(P-26) |
| 2 모순(계획·00-common) | hook 판정 범위(P-01), 5분류(P-18a), `부트스트랩` 구간(P-18c), ④ 순서(P-14a), 공격 12(P-26), 00-common §9.1(P-19). **새 N3.12.2 표 대 옛 산문 표**(`git show HEAD:` 대조): 잃은 경로·조건 없음. 추가: 오케스트레이터 `agents/gmid-*.md`·`hooks/role_*.py`·`tools/gates/**`의 `부트스트랩` 행(옛 판에서는 N3.12.6 ①에만 암시), auditor `자기 변경 id` 조건 명시, auditor의 `_schema.json` 제외가 `<id>` 형식으로 대체됨. 빠진 행: `hooks/role_*.json`, `tools/gates/*.json`·`requirements.txt`의 부트스트랩 뒤 주체(P-18b) |
| 3a git hook | E1~E3. design의 "pre-commit은 메시지를 못 읽는다 → commit-msg"는 옳다. 그러나 commit-msg가 merge에서 돈다는 점을 놓쳐 §11-6이 막힌다(P-04). `am`은 applypatch-msg·pre-applypatch만 |
| 3b glob | E6: `<id>` 해석에 따라 핵심 두 경로 허용/거부가 갈린다(P-02). 요청 표본 3건은 기대대로 |
| 3c 분류 표 | 두 분류에 드는 경로는 명시 우선·제외 문구로 해소된다(`.ai/verification/_schema.json`, `tests/tools/**`). 허용 조합표는 쓰기 경로표에서 '계산'되지 않는다(`code`의 레지스트리, `audit`의 경로 제약, 부트스트랩 행 처리 규칙 없음) -- P-07 |
| 3d EL1 교착 | worktree 명령(P-03), 병합 커밋(P-04), update-ref 뒤 복구 불가(P-06), 메인 세션 일상 쓰기(P-01) |
| 3e hook 사본·worktree | 사본은 `${CLAUDE_PROJECT_DIR}`(메인 작업 트리) 판을 import, EL3는 역할 worktree 판, EL4는 base 판 -- 세 판(P-06·P-13). import 실패는 fail-open(P-09) |
| 3f 상태 기반 판정·최초 승인 | ③의 최초 `plan_tables` 승인으로 첫 병합의 §8.2-2는 통과 가능. 계획 개정 + 승인 기록을 같은 커밋에 넣는 직접 커밋은 EL3를 통과한다(승인 기록 index 탐색). 단 §8.2-4·§11의 결함(P-04·P-05)으로 첫 실제 병합 자체가 현재 문안으로는 성립하지 않는다 |
| 4 WP | WP-01: EL3 설치 배선 미증명(P-13), `requirements.txt` 미배선(P-35). WP-02: pre-commit 조기 exit(P-12), hook fail-open(P-09), `승인 기록`·`status 전이만` 조건이 정상 경로에서 발동 안 함(P-08). WP-03: V5 이름 목록(P-22). WP-13: §2 표 두 소유 칸은 모든 행에서 서로 다르고 허용 값 안이다. 다만 재생 패치 변환을 작성자가 정한다(P-11·P-20) |
| 5 사례 재생 | §0 표. 검출 가능: 3250baa(V4 (3), 절단 규칙 전제). 글자대로는 불가: e329283(P-11). 원천 불일치: e5fbf92·1b9b4ea·2e1944a(P-20) |
| 6 N9.2 | 1·2·6·7·8 있음, 3·4·5 없음(P-24). 숨은 열린 질문: hook 반영 시점·세션 재시작(P-14b), 역할↔worktree 결합 수단(P-10), MG0 컨테이너 모순(P-25) |
| 7 표 셀 수 | E8 -- 불일치 0 |

---

## 5. 집계와 판정

| 등급 | 건수 | 항목 |
|---|---|---|
| S1 | 11 | P-01 ~ P-11 |
| S2 | 17 | P-12 ~ P-28 |
| S3 | 8 | P-29 ~ P-36 |

**판정: 재작성 필요** -- 역할 판정과 worktree 결합(§4·P-10), EL1 적용 범위(§5·P-01·P-03), EL3/EL4의 경로 판정과 base 직접 커밋(§7·§8.2·P-07·P-08), 병합 흐름(§8.2-4·§8.2-10·§11·P-04~P-06)은 부분 수정이 아니라 규칙을 다시 짜야 한다. V4 (2)(P-11)는 계획 N4.2 문구 개정이 함께 필요하다. 나머지 절(§3 표 파싱·해시 §14.2, §9 V6·V7, §10 양식, §13 agent 정의)은 수정 후 유지할 수 있다.
