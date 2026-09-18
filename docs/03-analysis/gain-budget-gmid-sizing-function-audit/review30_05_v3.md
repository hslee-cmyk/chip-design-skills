# review30 -- `05-role-separation` design v3.0 독립 검증

* 대상: `docs/02-design/features/gain-budget-gmid-sizing.05-role-separation.design.md` v3.0(커밋 f1c41b8)
* 기준: 위협 범위 C(계획 v5.19 N3.12.0), review29(Q-01~Q-28), 계획 v5.19(N0.4, N2.2, N3.10~N3.12, N4.2, N4.3, N6.1·N6.2 0.5, N7.2 U-15/16/38/39, N9.1·N9.2·N9.4, DEC-37~42), `00-common` v1.8(§3·§8·§9·§15·§17), `role_hook_input_probe.md`와 가린 원자료, `v4_rule_probe/`, 코드(`install.py`, `.githooks/*`, `hooks/*`), history 2026-09-18 절
* 검증자: 독립 검증 agent(작성자 아님). 저장소 파일 수정 없음(이 보고서만). 실측 스크립트·임시 저장소는 전부 `%TEMP%\rv30\`(저장소 밖)
* 판정 기준(과제 지시): "같은 계정의 의도적 공격이 X를 우회한다"는 v3가 그것을 **막는다고 주장**하거나, 그 공격이 N3.12.0 **'막는다' 패턴**이거나, §3.3 무결성 대조로 **드러나지 않을** 때만 결함으로 센다.
* 등급: **S1** 승인 차단(틀림·모순·구현 불가·'막는다' 패턴 통과) / **S2** 승인 전 수정(모호함·빈칸·감지 누락) / **S3** 경미

---

## 0. 실측 요약 (git 2.52.0.windows.1, Python 3.14, pytest 9.0.2, 전역 `core.autocrlf=true`)

실측 모델(`%TEMP%\rv30\m\`): bare `gate.git` + `hooks/pre-receive`(§9.1 그대로 `exec "C:/Python314/python.exe" "<gate>/gate-runner.py"`) + `gate-runner.py`(§9.1: §3.3 gate 쪽 대조 행 1·3·4, master 외 참조·삭제·non-ff·old=0 거부, **old 판** `tools/gates`를 `ls-tree -r -z`+`cat-file blob`으로 풀어 실행, 통과 시 `gmid-accept-log` 한 줄) + `tools/gates/merge_gate.py` 모델(§9.2-3 커밋 전수 트레일러·경로, §8.2-3 병합 트리 = 둘째 부모 트리, §9.2-4 변경 한 건 구조, §9.2-5 판정 기록 T·K 대조. push된 트리는 데이터로만 읽음). 작업 저장소 이력: 트레일러 없는 과거 커밋 3개 + 부트스트랩 ① → `baseline_commit`(pre-receive 설치 전 push) → ④(c) `bootstrapped` 커밋. 이후 §12 명령 순서 그대로(0 spec card push → 1·3·4 worktree → 2·5 커밋 → 6 병합 → 7 audit 커밋 → 8 `git -C <audit> push gate role/audit/<id>:master` → fetch·`merge --ff-only`). 결과 `m\results.txt`, `m\integ_results.txt`.

| # | 실측 | 결과 |
|---|---|---|
| B1 | ④(b) 그대로(`git init --bare` → 복사) 뒤 ④(c) push | **거부**: §3.3 행 4 "hooks/의 다른 파일" -- `git init --bare`가 만든 `*.sample` 14개 |
| B2 | 샘플 삭제 뒤 ④(c) push, `gmid-accept-log` 비어 있음(비었을 때 통과로 둔 모델) | 반영. 비었을 때 거부로 두면 ④(c)가 영구 거부 -- design은 빈 로그 동작을 정하지 않았다 |
| C1 | 정상 red-green(T → K → M → A) | 반영 |
| C2 | 정상 equivalence(test 커밋 없음, T = old) | 반영 |
| C3 | 정상 test-only | 반영 |
| C4 | §12-6을 `-m "Role: doc" -m "Change-Id: …"`(문단 분리)로 | 거부(Role 트레일러 없음) -- v3의 한 `-m` 두 줄 형태는 C1에서 통과 |
| E2 | §7 SubagentStop 규칙("역할 worktree의 `gate/master..HEAD` 커밋마다 `Role: <그 역할>`")을 C1에 적용 | code worktree: `Role: test` 커밋(test-author의 T)이 범위에 들어 위반. audit worktree: T·K·M 모두 위반 -- **정상 흐름이 매번 걸린다** |
| A19a | `merge --no-ff --no-commit` 뒤 test 약화를 넣은 M | 거부(트리 ≠ 둘째 부모) |
| A19b | 역할 커밋 없는 push: 기준 커밋에서 갈라진 `Role: doc` 문서 커밋 S + M(`Role: doc`, `Change-Id`, `read-tree --reset -u S`로 트리 = S 트리) | 병합 커밋 경로 검사 면제로 읽으면 **반영** -- 결과 master는 이미 반영된 test 4개 삭제, 엔진 소스 되돌림, `tools/gates/gate_config.json`(부트스트랩 표지) 삭제. 경로 검사를 병합에도 적용하면 거부되지만 그때는 C5 |
| C5 | 병합 커밋에도 §8.2-4 경로 검사 적용(§9.2-3 "커밋마다 §8.2의 2~5") 상태로 정상 red-green | **거부**(`skills/a/eng.py not allowed for Role doc`) |
| A20 | code worktree에서 `Role: test`·같은 id 커밋 T'(고정된 test를 `assert True`로 약화) → `Role: code` K | '첫 부모 사슬 순서' 모양을 역할 개수·조상 관계로 읽으면 **반영**. "M^1..M^2는 전부 `Role: code`" 규칙을 더하면 거부 |
| A20c | 한 push에 `Change-Id` 둘 | 거부 |
| R1 | A19a 거부 뒤 §12 '정리' 형태로 지우고 같은 id로 1부터 | 반영(spec card는 이미 gate에 있어 0은 생략) |
| H1 | `git merge --no-ff side -m "merge x" -m "Role: doc<LF>Change-Id: x"`에서 각 hook의 상태 | **pre-merge-commit 시점에 `MERGE_HEAD`가 없다**(`git rev-parse -q --verify MERGE_HEAD` 빈 값, `git diff --cached --quiet MERGE_HEAD` → `unknown revision`). 대신 환경 변수 `GITHEAD_<sha>=side`가 있다. commit-msg 시점에는 `MERGE_HEAD` 있음, 트레일러 `Role: doc;Change-Id: …` 파싱됨. `--no-commit` 뒤 `git commit`은 pre-commit·commit-msg가 돌고 둘 다 `MERGE_HEAD`를 본다 |
| P1 | §6.2 분해 순서(`;`·`&&`·`\|\|`·`\|`·줄바꿈으로 나눈 뒤 `shlex.split`)로 §12-6 명령 | 두 조각 모두 `No closing quotation` → "분해 실패는 거부" -- **EL1이 유일한 허용 병합 형태를 거부**. 따옴표를 아는 `shlex(punctuation_chars)`는 §12-6을 바르게 읽지만 `echo a<LF>git push gate x:master`를 명령 하나(`echo …`)로 합친다. `$'…\n…'` 형태는 `shlex`가 `$Role…`로 읽는다 |
| P2 | `shlex.split(r'cp a C:\Users\x\wt\id-code\skills\t.py')` | `C:Usersxwtid-codeskillst.py` -- 역슬래시 경로가 망가진다 |
| J1 | 판정 환경 파일(pytest 9.0.2, `--rootdir=<root> skills/analog-gmid-design/assets/tests`, test는 `assert f(1) == 10`이고 실제는 0) | 기준 `1 failed`. `skills/analog-gmid-design/pytest.ini`(`addopts = -k "not test_f"`) → `1 deselected` / `assets/tests/pytest.ini` → `1 deselected` / **루트 `conftest.py`**(hookwrapper로 실패를 통과로) → `1 passed` / `skills/conftest.py` → `1 passed` / `assets/tests/conftest.py` → `1 passed` |
| V1 | V4 (2)를 **실제 e329283 함수 본문**(`git show e329283:…/sizing_recipe.py`의 `estimate_area_budget`, return 둘)과 §13.3 변환 test에 적용, 문서가 정하지 않은 두 매개변수(피검 지역 인라인 여부, test 지역 인라인 여부)를 네 조합으로 | 문서 문구(피검만 인라인, X = assert가 가리키는 변수의 식)는 **통과 = 거짓 음성**. FAIL은 (둘 다 인라인 안 함) 또는 (둘 다 인라인)일 때만, 그리고 **두 번째 return**에서만. `v4_rule_probe/v4.py`는 인라인하지 않은 문자열을 손으로 넣어 잰 것이라 문구를 구현한 실측이 아니다 |
| V2 | 같은 규칙, 다른 식들(네 조합 모두 같은 결과) | FAIL: `0.5*k*vov*vov` 대 `0.5*2e-4*0.2*0.2`, `2*x*x` 대 `2*3.0*3.0`, `2*w+2*l` 대 `2*1e-6+2*0.5e-6`, `r1*r2/(r1+r2)` 대 `1e3*2e3/(1e3+2e3)`, `v*i1+v*i2` 대 `1.8*10e-6+1.8*20e-6`. 통과: 같은 제곱 법칙을 `vov**2`로 쓴 경우, `gm*ro` 대 `2e-3*50e3`, 독립 oracle(`1/(1/1e3+1/2e3)`, KCL 총합 `1.8*(10e-6+20e-6)`). e329283 복사의 교환(`a*(1-α)`), `1.0*(…)` 감싸기는 네 조합 모두 통과, test 임시 변수(`_k = 1 - 0.65`)는 한 조합에서만 FAIL |
| I1~I9 | §3.3 대조 행을 tamper마다(아래 표) | 아래 §0.1 |
| T1 | 표 셀 수(이스케이프 안 된 `\|`, 코드 펜스 제외) | 05 v3 19표·계획 43표·`00-common` 16표 불일치 0 |
| L1 | `role_hook_probe_logs/*.json` 식별자 | `session_id`·`transcript_path`·`permission_mode` 35/35, `tool_use_id` 30, `agent_id` 16 모두 `<redacted>`. UUID 패턴 0, 사용자 이름 0 |

### 0.1 §3.3 무결성 대조 실측 (`m\integ.py`, 각 경우 새 모델에서 tamper → 트레일러 없는 소스+tests 커밋 push)

"EL 쪽 행"은 design이 EL1(`git push gate` 직전)·EL3에서 도는 행 1·2, 행 2는 두 구현(`--file .git/config` / 병합된 설정)으로 쟀다. 행 3은 design상 `gate-runner.py` 시작·세션 시작, 행 4는 `gate-runner.py` 시작에서만.

| # | tamper | 나쁜 push | EL 쪽 행 1·2 | 행 3(accept-log) | 행 4 |
|---|---|---|---|---|---|
| I1 | 작업 저장소 `.git/config` `remote.gate.receivepack` | 반영 | 행 2 감지(두 구현 모두) | 감지 | -- |
| I2 | 전역 설정(`GIT_CONFIG_GLOBAL`로 대체한 임시 파일, 실제 `~/.gitconfig`는 건드리지 않음)의 `remote.gate.receivepack` | 반영 | `.git/config` 구현: **못 봄**. 병합 구현: 그 전역 파일을 보는 프로세스에서만 감지 | 감지 | -- |
| I3 | `.git/config`의 `include.path` → receivepack 든 파일 | 반영 | `.git/config` 구현: **못 봄** | 감지 | -- |
| I4 | `extensions.worktreeConfig` + linked worktree `config.worktree`에 receivepack, 그 worktree에서 push | 반영 | 메인 worktree에서: **두 구현 모두 못 봄**(그 worktree 안에서 병합 구현으로만 보임) | 감지 | -- |
| I5 | gate `hooks/pre-receive`를 `exit 0`으로 | 반영 | 행 1 감지 | 감지 | -- |
| I6a | gate `master`를 `pre-receive` 밖에서 이동(`git --git-dir=<gate> fetch <w> master:refs/heads/master`) | -- | 못 봄(행 3만 이 대상) | 감지 | -- |
| I6b | I6a + accept-log에 한 줄 덧붙임 | -- | 못 봄 | **못 봄** | -- |
| I6c | I6a + accept-log 삭제 | -- | 못 봄 | 빈 로그 동작 미정 | -- |
| I7 | gate `hooks/reference-transaction` 추가 | 거부 | -- | -- | 감지(gate-runner 시작) |
| I8 | gate 설정 `core.hooksPath` | 반영 | 못 봄 | 감지(세션 시작에서만) | **평가 안 됨**(gate-runner가 돌지 않는다) |
| I9 | CRLF로 바꾼 `pre-receive`(autocrlf 체크아웃에서 복사한 경우) | 정상 문서 push 반영 | 행 1 일치(`hash-object --path`가 eol 정규화) | -- | -- |

결론: 행 1·행 3은 주장대로 동작한다. 행 2는 적힌 범위(`.git/config`)로는 I2~I4를 못 보고, 행 4는 I8에서 한 번도 평가되지 않으며, gate `master` 이동의 유일한 감지(행 3)는 로그 한 줄로 무력화된다(I6b). CRLF `pre-receive`는 문제없다(I9).

스크립트: `%TEMP%\rv30\m\{run.py,integ.py,template\tools\gates\gate\gate-runner.py,template\tools\gates\merge_gate.py}`, `%TEMP%\rv30\h\`(H1), `%TEMP%\rv30\el1split.py`(+`.out.txt`), `%TEMP%\rv30\pe\`(J1), `%TEMP%\rv30\v4x.py`(+`v4x.out.txt`), `%TEMP%\rv30\cells.py`.

---

## 1. review29 Q-01~Q-28 해소 표 (위협 범위 C 기준)

| ID | 등급(29) | v3 판정 | 근거 |
|---|---|---|---|
| Q-01 | S1 | C 범위 밖(감지 확인) | v3는 막는다고 하지 않는다(§3.1 끝 점, N3.12.0). EL1이 `git config`·`git remote` 쓰기와 `<git-common-dir>/**`를 거부(§6.2·§6.3), `.git/config` 변형은 행 2가 감지(I1). 전역·include·worktree 설정 변형은 행 2가 못 보고 행 3만 감지(I2~I4) -- R-10 |
| Q-02 | S1 | 부분 | design은 닫았다: gate는 old 판 코드만 풀어 실행하고 push된 트리는 데이터로 읽는다(§3.2·§9.2-6, 모델에서 확인). 그러나 `00-common` §8.1이 여전히 "merge gate가 … 다시 실행해 대조"라고 적는다(R-13). 실행 위치를 auditor 격리 복제본으로 옮긴 결과 그 코드가 gate를 바꿀 수 있는 것은 그대로다(R-09) |
| Q-03 | S1 | 부분 | `--no-commit` 뒤 내용 추가(A19a)는 거부. 역할 커밋 없는 `Role: doc` 병합으로 조상 트리를 되돌리는 형태(A19b)는 통과하거나, 막으면 정상 병합이 막힌다(C5) -- R-01 |
| Q-04 | S1 | 부분 | EL1 명령 형태, EL4 한 push 한 id(A20c 거부)·spec card 필요. 그러나 SubagentStop 범위가 정상 흐름을 막고(E2, R-03), code 쪽 `Role: test` 커밋은 EL4 모양 규칙에서 정의되지 않는다(A20, R-07) |
| Q-05 | S1 | 부분 | 계획 표에 `assets/conftest.py` 제외와 사용자 행(`pytest.ini`·`pyproject.toml`·`setup.cfg`·`tox.ini`·`**/.gitattributes`)이 들어왔다. 그러나 루트·중간 디렉터리의 `conftest.py`, 루트가 아닌 `pytest.ini` 등은 어느 행에도 없어 트레일러 없이 EL3·EL4를 통과한다(J1, R-04) |
| Q-06 | S1 | 부분 | `baseline_commit`, pre-receive 설치 전 push, 최초 push 거부, 표지 -- 모델에서 동작(B2). 적힌 ④(b) 그대로면 `*.sample` 때문에 첫 판정 push가 거부되고(B1, R-11), 빈 accept-log 동작이 없다(R-09) |
| Q-07 | S1 | 부분 | `Role: user` + `target_kind: diff` 승인 기록 규칙이 생겼다. 그러나 커밋 전에 있어야 할 승인 기록이 그 커밋 id를 `diff_head`로 적을 수 없다(R-14) |
| Q-08 | S1 | 해소 | §12-0에서 interface card를 worktree 생성 전에 반영, 역할 브랜치가 있는 동안 문서 push 거부(§6.2), 재시도 절차(R1 반영) |
| Q-09 | S1 | 부분 | git 쪽은 해소(한 `-m` 두 줄 → 트레일러 둘, C1·H1). EL1의 명령 분해 규칙이 그 명령을 거부한다(P1, R-08) |
| Q-10 | S1 | 미해소 | 규칙을 '식 전체 동형 + 잎 대응 + 반복 잎'으로 바꿨지만 문구대로 구현하면 실제 e329283을 놓친다(V1, R-05). 거짓 양성은 표기에 따라 남는다(V2, R-06) |
| Q-11 | S2 | 해소 | §4.1 worktree 루트 기준·`normcase`, §5.1 오케스트레이터의 역할 worktree 쓰기 거부, §6.3 `<git-common-dir>/**`, §4.4 캐시 blob 대조 |
| Q-12 | S2 | 해소 | 부트스트랩 표지가 있으면 gate·hook 부재 = 실패(§3.3 끝 행). 표지를 병합으로 지우는 경로는 R-01 |
| Q-13 | S2 | 부분 | T = M^1, K = M^2, equivalence T = old, 모양 "정확히", 재시도 -- C1~C3·R1 동작. code 쪽 커밋의 역할 제한이 없다(A20, R-07), 역할 커밋 없는 병합(R-01) |
| Q-14 | S2 | 해소 | §7 (경로, 상태, blob) 집합 저장, 비교 뒤 삭제. '세션 시작 때 지운다'의 hook은 R-10 |
| Q-15 | S2 | 부분 | 비-`.py` test 파일 무조건 승인, N0.4 8패턴 ↔ AST 표. `for`/`while`/`with` 아래로의 assert 이동과 비-리터럴 격자·허용오차 변경(`range(n)`→`range(2*n)`에서 새 `Constant`가 '리터럴 변경'인지)은 여전히 판정식이 없다 |
| Q-16 | S2 | 부분 | 계획 N4.2 V3, N3.12.6 ④ 순서·산출물, N3.12.2 `hooks/role_*.json`, N3.12.3 1·3·6은 맞췄다. N3.12.3 7은 옛 문안 그대로다(R-15) |
| Q-17 | S2 | 해소 | `tools/gates/gate/` 원본, sidecar로 한 번에 등록, 복구는 사용자. 단 원본 경로의 쓰기 행이 없다(R-12) |
| Q-18 | S2 | 해소 | §3.2 `ls-tree -r -z` + `cat-file blob`(모델로 확인) |
| Q-19 | S2 | 해소 | §9.2-7 AST 판정식 |
| Q-20 | S3 | 해소 | gate가 test를 실행하지 않아 대상이 없어졌다 |
| Q-21 | S3 | 해소 | `00-common` §8.2·§9.1이 05 §4·§15.2를 인용, §9.3 `=` 형식 |
| Q-22 | S3 | 해소 | 원자료 35개, PostToolUse 등록 matcher 명시 |
| Q-23 | S3 | 해소 | N6.1 0.5 행 U-39, N4.3 공격 11 "RTL 파일", N3.12.4 EL1 도구 목록, "주체가 `사용자`인 경로" |
| Q-24 | S3 | 해소 | `normcase`, `cd` 뒤 상대 대상 거부, §6.4 어느 worktree든. 단 R-18 |
| Q-25 | S3 | 해소 | `tools:` 줄 `코드` 분류, U-38 승인 기록 id |
| Q-26 | S3 | 해소 | 절대 경로, `pre-push` 상호작용(§8.1) |
| Q-27 | S3 | 해소 | `modes` 열, §19와 ⑤ 목록 일치 |
| Q-28 | S3 | 해소 | L1 |

집계: **해소 16**(Q-08·11·12·14·17~28) / **부분 10**(Q-02·03·04·05·06·07·09·13·15·16) / **미해소 1**(Q-10) / **C 범위 밖(감지 확인) 1**(Q-01).

---

## 2. 새 결함 -- S1

### R-01 [S1] 역할 커밋 없는 `Role: doc` 병합이 조상 트리로 되돌려도 EL4를 통과한다 -- 막으면 정상 병합이 막힌다
* **위치**: §8.2-3, §9.2-3("커밋마다 첫 부모 대비로 §8.2의 2~5 … 병합 커밋은 §8.2-3"), §9.2-4("역할 커밋이 있으면"), §13.2 공격 19("역할 커밋 없는 `Role: doc` 병합 → EL3 차단, EL4 거부"), §16 병합 커밋 행.
* **근거**: A19b·C5. 병합 규칙은 "트리 = 둘째 부모 트리" 하나뿐이다. 둘째 부모를 **오래된 조상에서 갈라진 문서 커밋**으로 두면 트리 조건을 만족하면서 첫 부모 쪽에 쌓인 변경을 전부 되돌린다. 역할 커밋이 없으니 §9.2-4 구조 검사와 판정 기록은 발동하지 않는다. 결과(실측): 이미 반영된 test 4개 삭제, 엔진 소스 되돌림, `gate_config.json` 삭제 -- 마지막은 부트스트랩 표지를 지워 `부트스트랩` 조건을 다시 참으로 만들고(오케스트레이터가 `tools/gates/**`를 쓸 수 있게 됨) gate·hook 부재 = 실패 규칙(§3.3 끝 행)도 끈다. N3.12.0 '막는다'의 흐름 밖 병합과 기준 약화(test 삭제)다. 반대로 §9.2-3을 글자대로(병합 커밋에도 §8.2-4 경로 검사) 읽으면 A19b는 거부되지만 **정상 §12-6 병합도** `Role: doc`이 소스를 바꾼 것으로 거부된다(C5). EL3도 같다: 트리 = `MERGE_HEAD` 트리이므로 통과한다(H1의 `--no-commit` + 커밋 경로). EL1은 `git merge`를 막지만 `read-tree`는 §6.2 목록에 없고, 스크립트 경로는 어차피 EL4가 최후 겹이다.
* **수정**: 병합 커밋은 **변경 한 건의 M으로만** 허용한다 -- `Change-Id`의 역할 커밋이 같은 push에 있어야 하고, M^2 = 그 id의 마지막 `Role: code` 커밋, M^1 = 그 id의 test 끝(없으면 `old`), M^2가 M^1의 후손이며, 그 밖의 병합 커밋은 거부. 경로 검사는 병합 커밋에서 면제한다고 명시(K까지의 커밋이 이미 검사됨). 공격 19에 A19b 형태(조상에서 갈라진 문서 부모)를 넣고 기대를 EL4 거부로.

### R-02 [S1] pre-merge-commit 시점에는 `MERGE_HEAD`가 없어 §8.2-3 병합 검사가 구현되지 않는다
* **위치**: §8.1 `.githooks/pre-merge-commit`, §8.2-3("`MERGE_HEAD` 존재 또는 pre-merge-commit 단계 … `git diff --cached --quiet MERGE_HEAD`").
* **근거**: H1. 충돌 없는 `git merge --no-ff`는 pre-commit을 돌리지 않고 pre-merge-commit·commit-msg를 돌린다. pre-merge-commit 안에서 `MERGE_HEAD`는 없고(`unknown revision`) 병합 대상은 환경 변수 `GITHEAD_<sha>`로만 보인다. 적힌 명령대로면 정상 §12-6 병합이 매번 차단되거나(fail-closed), 구현자가 검사를 빼게 된다(fail-open). commit-msg 시점에는 `MERGE_HEAD`가 있다.
* **수정**: 병합 트리 대조를 commit-msg 단계(모든 병합 경로에서 `MERGE_HEAD`가 있음)로 옮기거나, pre-merge-commit에서는 `GITHEAD_*` 환경 변수의 sha를 쓰도록 명시. ⑤ 설치 후 재생에 §12-6 실제 명령을 넣는다.

### R-03 [S1] EL2 SubagentStop 범위 `gate/master..HEAD`에는 다른 역할의 커밋이 들어 있어 정상 흐름이 매번 걸린다
* **위치**: §7 셋째 점, §13.2 공격 20 기대(EL2 SubagentStop 거부).
* **근거**: E2. code worktree는 `role/test/<id>`에서 만들므로(§12-4) `gate/master..HEAD`에 test-author의 T(`Role: test`)가 있다. audit worktree는 T·K·M(`Role: doc`)을 가진다. 규칙대로면 code-author·auditor의 모든 종료가 exit 2이고, 실측(probe)에서 SubagentStop exit 2는 종료를 막는다 -- 역할 agent가 끝나지 못한다.
* **수정**: 역할별 범위를 정한다: code = `role/test/<id>..HEAD`, test = `gate/master..HEAD`, audit = `HEAD^..HEAD`(audit 커밋만) 또는 `M..HEAD`. 범위 안 커밋은 그 역할·id만. 공격 20·⑤에 정상 종료(오거부 0) 케이스를 넣는다.

### R-04 [S1] 판정 환경 파일이 쓰기 경로표의 몇 경로만 보호되어, 나머지는 트레일러 없이 EL3·EL4를 통과한다
* **위치**: 계획 N3.12.2 사용자 행(`skills/analog-gmid-design/assets/conftest.py`, `pytest.ini`, `pyproject.toml`, `setup.cfg`, `tox.ini` -- `**/.gitattributes`만 `**`), design §9.2-3("역할 밖 경로만 바꾼 커밋은 통과"), §13.2 공격 17.
* **근거**: J1. pytest는 rootdir부터 test 디렉터리까지의 모든 `conftest.py`와, 인자 디렉터리에서 위로 가장 먼저 찾은 ini 파일을 쓴다. 루트 `conftest.py`, `skills/conftest.py`(→ `1 passed`), `skills/analog-gmid-design/pytest.ini`(`addopts = -k …` → `1 deselected`, V1의 `-k` 금지는 명령줄만 본다)는 **어느 행에도 없어** `overlaps_any` 거짓 → 트레일러 없는 커밋도 EL3·EL4 통과. N3.12.0 '막는다'의 판정 환경 조작 그대로다. test-author 경로 안의 `assets/tests/conftest.py`·`assets/tests/pytest.ini`도 같은 효과를 내는데, CC-3에서 `tests/conftest.py`는 정당한 산출물이라 행 제외로는 못 막는다(V5·V1이 볼 대상).
* **수정**: 사용자 행을 `**/conftest.py`(단 `assets/tests/conftest.py`는 test-author 행에 두고 V5 입력에 conftest diff 포함), `**/pytest.ini`, `**/pyproject.toml`, `**/setup.cfg`, `**/tox.ini`, `**/sitecustomize.py`, `**/*.pth`로. 판정 표 변경이므로 `plan_tables` 승인. 공격 17에 J1 다섯 형태를 넣는다.

### R-05 [S1] V4 (2)는 문구대로 구현하면 실제 e329283을 놓친다 -- 실측이 문구를 구현하지 않았다
* **위치**: §10 V4 행("피검 함수의 지역 대입을 반환식에 인라인 전개한 식 E와 test 기대식 X"), 계획 N4.2 V4 (2), §13.3 e329283 행.
* **근거**: V1. 실제 `estimate_area_budget`은 return이 둘이고, 반환식의 `a_1d`·`a_2d_cold`는 지역 대입이다. 문구대로 E를 인라인하면 `(1-α)*(n_fingers*finger_pitch_area) + α*((n_fingers*finger_pitch_area)/α)`가 되고, 변환 test의 X(`_area_cold_expected`의 식)는 `(1-0.65)*_a1d_demo + 0.65*_a2d_cold_expected`라 동형이 아니다 → **통과**. FAIL이 나는 것은 양쪽 모두 인라인하지 않거나 양쪽 모두 인라인할 때, 그리고 두 번째 return을 E로 고를 때뿐이다. `v4_rule_probe/v4.py`는 인라인하지 않은 반환식 문자열을 손으로 넣은 측정이다(WP-17). 즉 이력에 실제로 있던 자기참조 사례(N3.12.0 '막는다')를 정본 규칙이 막는다는 증거가 없다.
* **수정**: (i) test 쪽도 같은 규칙으로 지역 대입을 인라인한다(X = assert 비교 상대의 식을 test 함수 지역 대입으로 끝까지 전개) (ii) return이 여럿이면 각 return마다 E를 만들어 하나라도 맞으면 FAIL (iii) V4 실측을 **실제 함수 본문과 §13.3 변환 test를 입력으로 하는 도구 코드**로 다시 재고, 네 조합 결과를 §10에 적는다.

---

## 3. 새 결함 -- S2

### R-06 [S2] V4 (2)의 '반복 잎'은 독립성이 아니라 표기를 가른다
* **위치**: §10 V4 행, §16 V4 행, 계획 N4.2 V4 (2).
* **근거**: V2. 같은 제곱 법칙이 `vov*vov`로 쓰이면 손계산 기대값이 FAIL, `vov**2`로 쓰이면 통과. `gm*ro` 대 `2e-3*50e3`(계획이 '독립 oracle'로 통과를 요구)과 `r1*r2/(r1+r2)` 대 `1e3*2e3/(1e3+2e3)`는 같은 성격(식 재서술)인데 앞은 통과, 뒤는 FAIL. 거꾸로 e329283 복사를 교환(`_a1d_demo*(1-0.65)+…`)하거나 `1.0*(…)`로 감싸면 모든 조합에서 통과한다. 계획 oracle 정의(N3.12.3: (b)는 "다른 방법의 폐형식")와 규칙이 무엇을 자기참조로 보는지 대응하지 않는다.
* **수정**: 규칙의 목적을 계획 문구로 먼저 정한다(피검 식과 같은 식의 재서술은 전부 자기참조인가, 이력 패턴만인가). 전자면 '반복 잎' 조건을 빼고 교환·결합 정규화(피연산자 정렬)를 넣고 gm·ro 예를 자기참조로 바꾼다. 후자면 한계(재배열로 빠짐)를 §10에 적고 V3(뮤테이션)가 보완한다고 명시. V2의 식들을 redteam `23`에 기대와 함께 넣는다.

### R-07 [S2] code 쪽에 끼운 `Role: test` 커밋을 EL4가 거부한다는 규칙이 없다
* **위치**: §9.2-4 모양 표("첫 부모 사슬 순서"), §13.2 공격 20 기대("EL4 거부").
* **근거**: A20. T' 는 M^1(T)의 후손이자 M^2(K)의 조상이라 '첫 부모 사슬'에 없다. 모양을 역할 개수와 조상 관계로 읽으면 통과하고, 그 결과 병합본의 test는 auditor가 3에서 고정한 T가 아니라 code-author가 고친 T'이다(V5는 base 대비라 새 test 약화를 못 본다). EL1·EL2가 막는 경로는 도구 호출 경로뿐이고, 스크립트로 만든 커밋은 EL4가 최후 겹이다.
* **수정**: 모양에 "M^1..M^2의 커밋은 전부 `Role: code`, `old..M^1`의 첫 부모 사슬은 전부 `Role: test`"를 명시(모델에서 이 규칙으로 거부 확인). 공격 20에 T' 형태를 넣는다.

### R-08 [S2] EL1 명령 분해 규칙이 §12-6 명령을 거부하고, 따옴표를 아는 분해는 줄바꿈 명령을 합친다
* **위치**: §6.2 첫 문단, §12-6.
* **근거**: P1. 줄바꿈으로 먼저 나누면 §12-6의 두 줄 `-m` 인자가 잘려 분해 실패 → 거부. `shlex(punctuation_chars)`는 §12-6을 읽지만 따옴표 밖 줄바꿈을 공백으로 봐 `echo a<LF>git push …`를 `echo` 명령 하나로 만든다(push 판정 누락). `$'…'` 형태는 `shlex`가 읽지 못한다. P2: POSIX `shlex`는 `C:\…` 경로의 역슬래시를 지운다.
* **수정**: 분해기를 명시한다 -- 따옴표·이스케이프를 추적하며 **따옴표 밖** `;`·`&&`·`||`·`|`·줄바꿈에서만 나누고, `$'`·heredoc·명령 치환(`$(`·백틱)이 있으면 거부. 경로 인자에 역슬래시가 있으면 거부(역할 정의에 슬래시 경로 사용을 적는다). §12-6 명령과 위 예를 공격 재생 케이스로.

### R-09 [S2] gate `master` 이동의 유일한 감지(행 3)는 로그 한 줄로 무력화되고, 빈 로그 동작이 없다
* **위치**: §3.3 행 3과 첫 점, §9.1-4, §13.2 공격 22.
* **근거**: I6b(한 줄 덧붙이면 감지 안 됨), I6c·B2(빈 로그: 통과로 두면 로그 삭제 = 감지 끔, 거부로 두면 ④(c)가 막힘). design은 "accept-log도 같은 계정이 고칠 수 있다"고 인정하지만 N3.12.0은 이 행위를 **드러나게** 해야 한다. 또 v3는 증거 실행을 auditor 격리 복제본으로 옮겼는데, 그 안에서 도는 코드(code-author의 소스, test-author의 test -- '막는다' 대상 행위자의 산출물)는 같은 계정 권한으로 G6·G7 형태와 로그 위조를 함께 할 수 있다(복제본의 `origin`도 작업 저장소를 가리킨다 -- 실측). 로그와 무관한 감지가 이미 가능하다: 세션 시작마다 `baseline_commit..master`의 각 반영 구간을 `merge_gate.py`로 **데이터만** 다시 판정하면 I6a·I6b 모두 드러난다(트레일러 없는 커밋, 구조 위반).
* **수정**: (i) 행 3에 "세션 시작 때 accept-log의 구간 사슬(old = 이전 줄 new) 연속성 + 각 구간 재판정(데이터만)"을 더한다 (ii) 빈 로그 규칙: ④(b)에서 사용자가 `<baseline> <baseline> <시각>` 첫 줄을 쓰고, 표지 뒤 빈 로그 = 실패 (iii) auditor 격리 복제본에서 `git remote remove origin` 뒤 실행을 §12-7에 적는다. 공격 22에 I6b·I6c를 넣는다.

### R-10 [S2] 행 2의 대상 범위, 행 4의 대조 시점, 세션 시작 hook의 부재
* **위치**: §3.3 행 2·4·5, §2 표, 계획 N3.12.6 산출물, §13.2 공격 21·22 기대.
* **근거**: (a) 행 2가 "작업 저장소 `.git/config`"만 보면 전역 설정(I2)·`include.path`(I3)·`config.worktree`(I4)를 못 본다. 모두 행 3에서 늦게 감지된다. (b) 행 4는 `gate-runner.py` 시작에서만 도는데 gate `core.hooksPath`(I8)면 gate-runner가 돌지 않아 **한 번도 평가되지 않는다** -- 감지는 세션 시작의 행 3뿐. (c) 행 3·행 5·§7 status 파일 정리·감사 로그 출력이 모두 "세션 시작(SessionStart hook)"에 기대는데 그 hook 파일은 §2 표·계획 N3.12.6 hook 목록에 없고, 행 5는 "역할 hook **세** 항목"이라 적는다. `install.py`는 스크립트 하나에 이벤트 하나이므로 `hooks/role_session_start.py`+`.json`(`"event": "SessionStart"`)이 별도로 필요하다(WP-01). (d) 공격 22 기대 "EL1(push 직전)·EL3 … 대조 실패"는 master 이동에 대해 틀렸다 -- 행 3은 EL1·EL3 시점에 돌지 않는다(I6a).
* **수정**: 행 2는 `git config --show-origin --get-regexp` 로 **모든 범위**(system·global·local·worktree·include)를, 모든 역할 worktree 각각에서 본다. 행 4를 EL1 push 직전·EL3·세션 시작에도 둔다(`git --git-dir=<gate> config --get core.hooksPath`는 전역까지 읽는다). SessionStart hook을 §2·N3.12.2(`hooks/role_*.py`에 맞는 이름)·N3.12.6 산출물·행 5에 넣는다. 공격 21·22에 I2~I4·I8을 넣고 기대 시점을 표와 맞춘다.

### R-11 [S2] 부트스트랩 ④(b)가 `hooks/*.sample`을 남겨 첫 판정 push가 거부된다
* **위치**: §13.1 ④(b), §3.3 행 4.
* **근거**: B1. `git init --bare`는 `hooks/`에 샘플 14개를 만든다. 적힌 순서대로면 ④(c)가 행 4로 거부된다.
* **수정**: ④(b)에 "`hooks/*.sample` 삭제(또는 `git init --bare --template=<빈 디렉터리>`)"와 accept-log 첫 줄(R-09)을 넣는다.

### R-12 [S2] gate 원본 `tools/gates/gate/**`의 쓰기 행이 없고, 게이트 변경 뒤 재설치 절차가 없다
* **위치**: 계획 N3.12.2(code-author `tools/gates/*.py`·`*.json`은 한 조각만), design §2 EL4 행, §3.3 행 1·5, §13.1 ⑤("이후 게이트 변경은 N3.12.3 흐름").
* **근거**: `tools/gates/gate/gate-runner.py`·`pre-receive`는 부트스트랩 뒤 어느 주체의 행에도 맞지 않아 흐름으로 고칠 수 없다. 또 `tools/gates/gate/*`나 `hooks/role_*.py`를 바꾼 게이트 변경이 반영되면 설치된 사본이 새 gate master blob과 달라져 행 1·5가 실패하고, 그 뒤 모든 push·세션이 fail-closed가 된다 -- 사용자가 무엇을 다시 복사·설치하는지 절차가 없다.
* **수정**: 계획 표에 `gmid-code-author | tools/gates/gate/** | -- | 게이트 변경` 행(승인 기록). §13에 "게이트 변경 반영 직후 사용자 재설치 절차(gate 사본 복사, `install.py --only hooks`, `integrity.py check`)"를 두고, 반영 push와 재설치 사이의 fail-closed 상태를 정상으로 명시.

### R-13 [S2] `00-common` §8.1은 여전히 merge gate가 증거를 재실행한다고 적는다
* **위치**: `00-common` §8.1 `failure_hashes` 소비자("merge gate가 freeze 커밋 worktree에서 `red.test_ids`를 base에 대해 다시 실행"), `outputs_hash` 소비자("merge gate가 base·병합본에서 같은 명령을 다시 실행"), "auditor가 기록할 때와 merge gate가 재계산할 때"; design §9.2-6, §20(v1.8 개정 목록에 이 변경 없음).
* **근거**: N3.12.0 "게이트는 push된 코드를 실행하지 않는다"와 모순. 05 승인이 `00-common` v1.8을 덮는다고 적었으므로 정본 둘이 서로 다르다(N9.4). 또 §9.2-6의 "`auditor_run.commands`에 격리 실행 명령이 들어 있는지만 본다"는 auditor가 쓴 문자열의 존재 검사라 무엇도 증명하지 않는다.
* **수정**: `00-common` §8.1 소비자를 "auditor가 격리 복제본에서 계산·기록, merge gate는 형식만"으로 고치고 §20 개정 목록에 올린다. §9.2-6은 형식 검사임을 명시하고, 필요하면 세션 시작 재판정(R-09)처럼 사용자 쪽 재현 명령을 둔다.

### R-14 [S2] 커밋 전에 있어야 할 `diff` 승인 기록이 `diff_head`를 적을 수 없다
* **위치**: design §8.2-5(`승인 기록` topology, `Role: user`: "HEAD→staged … blob 식 … 승인 기록이 index나 HEAD 트리에"), `00-common` §8.2(`diff_head` 40자리 필수, V5는 `diff_base`·`diff_head`로 다시 계산).
* **근거**: 승인 기록은 그 커밋에 같이 들어가거나 먼저 있어야 하는데 `diff_head`는 아직 없는 그 커밋의 id다. design은 `target`만 HEAD·staged로 대조한다고 해 `diff_head`에 무엇을 적는지, 로더가 `diff_head` 존재를 검사하는지 정하지 않는다(숨은 열린 질문).
* **수정**: 이 두 조건에 한해 `target_kind: diff`의 `diff_head`를 생략(또는 새 `target_kind: staged_diff` -- `diff_base`와 경로만)하도록 `00-common` §8.2를 고치고 EL3·EL4가 각각 (HEAD, staged)·(첫 부모, 커밋)으로 다시 계산함을 적는다.

### R-15 [S2] 계획 ↔ design 불일치
* **위치와 근거**:
  * 계획 N3.12.3 7: "audit worktree의 **병합 커밋**을 push … EL4는 병합 커밋 대신 두 부모 쪽 커밋들의 트레일러·경로를 검사" -- design §12-8(audit 브랜치 끝 push)·§8.2-3(트리 = K)과 다르다. §20은 N3.12.3 "1·3·6"만 고쳤다고 적는다.
  * 공격 번호·개수: 계획 N4.3 "공격 16건"(1~16), N6.2 "0.5 대상 13건", N9.1 05 행 "공격 16건"인데 design §13.2·§19 DoD는 1b·10b·10c·17~23을 더한다. N3.12.0 '막는다'(흐름 밖 병합, 트레일러 흉내, 판정 환경)와 '드러나게'의 증거가 계획의 DoD에는 없다(N9.4: 정의는 계획이 정본).
  * 계획 N3.12.6 ④(b)는 "기준 커밋 → pre-receive 설치 → 원격 등록" 순서, design은 "원격 등록 → push → 복사"이고 표지 커밋 단계(design ④(c))가 계획에 없다.
  * 계획 N3.12.2 `부트스트랩` 조건("gate 저장소와 hook 설치가 끝나면") 대 design §4.1(표지 커밋이 gate에 반영되면) -- 표지는 ④(d) hook 설치 **전**이다.
* **수정**: 계획을 design과 같게 개정하고(N4.3에 17~23과 이번 R 케이스, N6.2 개수, N3.12.3 7, N3.12.6 ④, `부트스트랩` 조건 정의 한 곳) §20 목록에 올린다.

### R-16 [S2] 재시도 정리가 dispute를 지운다
* **위치**: §12-5("dispute를 쓰고 멈춘다"), §12 재시도("정리 형태로 세 worktree·브랜치를 지우고 같은 id로 1부터"), §11.3.
* **근거**: dispute(`docs/02-design/disputes/<id>.md`)는 code worktree에만 있고(커밋해도 `role/code/<id>`에만) gate로 가는 경로가 없다. 정리(`worktree remove`, `branch -D`)가 그것을 지운다. 사용자 결정의 근거 기록이 남지 않는다.
* **수정**: dispute가 나오면 오케스트레이터가 정리 전에 그 파일을 읽어 spec card 개정·승인 기록에 인용하는 단계, 또는 dispute만 담은 code 커밋을 gate에 반영하는 전용 모양(`evidence_type` 밖, 역할 커밋 `Role: code` + 경로 `disputes/<id>.md`만)을 정한다.

---

## 4. 새 결함 -- S3

* **R-17** 숨은 열린 질문(N9.2-8): §13.1 ④(d) "`--only hooks`가 `hooks/*.py` 전부를 등록하는 것을 허용할지 ④ 전에 사용자 확인" -- `install.py`는 `hooks/`와 `bkit/hooks/`의 모든 `.py`(현재 `guard-bash-nul`, `guard-submodule-formal`, `kb-preflight-nudge` 등)를 프로젝트 설정에 등록한다. §20 열린 질문에 없다. 또 `install.py`의 sidecar 파싱은 `except Exception: pass`라 `.json`이 깨지면 조용히 `PreToolUse`/`Write|Edit`로 등록된다(행 5가 감지하지만 설치 로그에는 성공으로 나온다) -- U로 올리거나 역할 hook만 설치하는 옵션을 부트스트랩 산출물에 넣는다.
* **R-18** §5 머리 "hook 입력 `cwd`는 세션 시작 디렉터리로 고정" -- probe는 **메인 세션**의 `cd`가 다음 호출까지 유지되고 hook `cwd`도 바뀐다고 기록했다. 오케스트레이터의 상대 경로 해석 기준을 hook `cwd`로 명시.
* **R-19** §12-3 auditor가 red 확인 결과를 "기억"한다 -- subagent 호출 사이에는 기억이 없다. 7에서 다시 재는지, `.ai/verification/<id>/`에 커밋 없이 두는지 정한다. §12-7 `git clone …`은 `git -C`가 없는 git 명령이라 §6.2 "역할의 메인 worktree git 쓰기" 행과 충돌할 수 있다(쓰기 git 명령의 목록이 없다).
* **R-20** §4.4 캐시와 EL1~EL3의 gate 읽기에 `GIT_NO_REPLACE_OBJECTS=1`이 없다(§9.1은 gate-runner에만). gate의 `refs/replace/*`가 EL1~EL3가 푸는 게이트 코드를 바꾼다. 캐시 대조가 `hash-object`로 blob id를 다시 계산하면 드러나므로 그 방식을 명시하고 환경 변수를 모든 겹에 둔다.
* **R-21** WP-13: 부트스트랩의 게이트 코드와 공격 기대(`expect.json`)를 같은 주체(오케스트레이터)가 쓴다. 사용자 로그 확인이 보완이지만, 기대값 파일은 독립 검증 agent가 쓰거나 검토하도록 §2에 적는 것이 N3.12.1 취지에 맞다.
* **R-22** §19 DoD `integrity.py check`의 하위 명령·출력 형식이 §3.3·§17 어디에도 정의되지 않았다(§17은 코드만).

---

## 5. 점검 항목별 결론

| 점검 | 결론 |
|---|---|
| 1 Q-01~Q-28 | 해소 16 / 부분 10 / 미해소 1 / C 범위 밖(감지 확인) 1 (§1) |
| 2(a) gate·§9.2-4 | 정상 세 모양·재시도·한 push 두 id 거부·악성 병합(`--no-commit`) 거부는 동작(C1~C3, R1, A20c, A19a). 역할 커밋 없는 병합 되돌리기(A19b)는 통과 또는 정상 병합 차단(C5) -- R-01. code 쪽 `Role: test`(A20) -- R-07. EL3 pre-merge-commit의 `MERGE_HEAD` 부재(H1) -- R-02. SubagentStop 범위(E2) -- R-03 |
| 2(b) §3.3 | 행 1(pre-receive 덮어쓰기 I5)·행 2(`.git/config` I1)·행 3(master 이동 I6a)·행 4(추가 hook I7)는 적힌 시점에 감지. 같은 부류 미감지·지연: 전역·include·worktree 설정(I2~I4, 행 3으로만), gate `core.hooksPath`(I8, 행 4 평가 안 됨), 로그 위조(I6b, 감지 없음), 빈 로그(I6c, 미정), `*.sample`(B1, 오거부) -- R-09·R-10·R-11 |
| 2(c) §12-6 | 한 `-m` 두 줄은 `interpret-trailers --parse`로 `Role`·`Change-Id` 둘 다 읽힌다(C1·H1). EL1 분해 규칙이 그 명령을 거부(P1) -- R-08 |
| 2(d) V4 | 실제 e329283 함수로는 문구대로 거짓 음성(V1) -- R-05. 표기 의존 거짓 양성·재배열 우회(V2) -- R-06 |
| 3 정합성 | 계획 N3.12.3 7, N4.3·N6.2·N9.1 공격 개수(16/13 대 17~23), N3.12.6 ④ 순서·표지 단계, `부트스트랩` 조건 -- R-15. `00-common` §8.1 증거 재실행 -- R-13. N3.12.2 필요 행: `tools/gates/integrity.py`(`tools/gates/*.py`에 맞음), `.githooks/pre-merge-commit`(`.githooks/**` 사용자), `hooks/role_*.json`(있음)은 충족. `tools/gates/gate/**` 없음(R-12), SessionStart hook 산출물 없음(R-10), 판정 환경 `**/` 형태 없음(R-04). 주체·소유(§2)는 계획 N3.12.1과 일치 |
| 4 WP | WP-01: SessionStart 대조 미배선(R-10), gate 원본 수정 경로 없음(R-12). WP-02: 빈 로그·표지 삭제·병합 면제의 fail-open(R-01·R-09), 판정 환경 통과(R-04). WP-03: 수치 없음(§16, `audit_tail_lines`만 사용자 값) -- 결함 없음. WP-13: §2 두 소유 칸은 모든 행에서 다름, 공격 기대 작성 주체(R-21). WP-17: V4 실측이 문구를 구현하지 않음(R-05), ④(b) 절차 미실측(R-11). WP-21: 판정은 모두 코드. N9.2: 1~8 절 있음(3 §16, 4 §17, 5 §18, 6 §19, 7·8 §20). 숨은 열린 질문: 병합 경로 검사 면제 여부(R-01), SubagentStop 범위(R-03), V4 인라인 깊이·return 선택(R-05), 빈 accept-log(R-09), `diff_head`(R-14), `install.py` 전부 등록(R-17), 쓰기 git 명령 목록(R-19). 표 셀 수 불일치 0(T1) |

---

## 6. 집계와 판정

| 구분 | 건수 | 항목 |
|---|---|---|
| review29 해소 | 16 | Q-08·11·12·14·17·18·19·20·21·22·23·24·25·26·27·28 |
| review29 부분 | 10 | Q-02·03·04·05·06·07·09·13·15·16 |
| review29 미해소 | 1 | Q-10 |
| review29 C 범위 밖(감지 확인) | 1 | Q-01 |
| 새 S1 | 5 | R-01 ~ R-05 |
| 새 S2 | 11 | R-06 ~ R-16 |
| 새 S3 | 6 | R-17 ~ R-22 |

**판정: 수정 후 승인** -- v3는 위협 범위 C를 구조에 반영했고 v2의 핵심 결함(클라이언트 설정 우회의 과장, gate의 push 코드 실행, 최초 push, 트레일러 형식, worktree 순서)은 닫혔거나 C 범위 밖으로 정직하게 옮겨졌다. 실측에서 gate 모델은 정상 세 모양과 재시도를 받아들이고 주요 위반을 거부했으며 무결성 행 1~4는 적힌 대상을 감지했다. 남은 S1 다섯은 모두 국소 규칙의 결함이라 구조를 다시 짤 필요는 없다: 병합 커밋 허용 조건(R-01), 병합 검사 hook 단계(R-02), SubagentStop 범위(R-03), 판정 환경 경로 행(R-04, 계획 표 개정 + `plan_tables` 승인), V4 인라인·return 규칙과 실제 함수 재측정(R-05). 다만 S1 다섯이 모두 '막는다' 패턴의 통과이거나 정상 흐름 차단이므로 고친 뒤 해당 케이스(A19b, H1, E2, J1, V1)를 공격 재생 데이터에 넣어 재검증해야 한다.
