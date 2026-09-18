# review29 -- `05-role-separation` design v2.0 독립 검증

* 대상: `docs/02-design/features/gain-budget-gmid-sizing.05-role-separation.design.md` v2.0(커밋 e218ad7)
* 기준: review28(P-01~P-36), 계획 v5.19(N0.4, N2.2, N3.10~N3.12, N4.2, N4.3, N6.1·N6.2 0.5, N7.2 U-15/16/38/39, N9.1·N9.2·N9.4, DEC-37~42), `00-common` v1.8(§3·§8·§9·§15·§17), 코드(`install.py`, `.githooks/*`, `hooks/*`, `agent-quality/check_agents.py`), history 2026-09-18 머리 절, `role_hook_input_probe.md`와 `role_hook_probe_logs/`
* 검증자: 독립 검증 agent(작성자 아님). 저장소 파일 수정 없음(이 보고서만). 실측 스크립트·임시 저장소는 전부 `%TEMP%\rv29\`(저장소 밖)
* 등급: **S1** 승인 차단(틀림·모순·구현 불가·우회 가능) / **S2** 승인 전 수정(구현자가 갈라질 모호함·빈칸) / **S3** 경미

---

## 0. 실측 요약 (git 2.52.0.windows.1, Python 3.14, pytest 9.0.2)

실측 모델: `%TEMP%\rv29\a\gate.git`(bare) + `hooks/pre-receive`(design §9.1 그대로 `exec "C:/Python314/python.exe" <gate>/gate-runner.py`) + `gate-runner.py`(§9.1 1~3: master 외 참조 거부, 삭제 거부, `merge-base --is-ancestor`로 non-ff 거부, `git archive <old> tools/gates`로 old 판 검사 코드를 풀어 실행, old=0이면 new 판) + 작업 저장소 `tools/gates/merge_gate.py` 모델(§9.2-3 커밋 전수 트레일러·역할별 경로, §8.2-3 병합 커밋은 경로 검사 없음, §9.2-6 증거 재계산 = push된 트리를 `git archive`로 풀어 test 실행).

| # | 실측 | 결과 |
|---|---|---|
| G1 | 최초 push(old=0), 트레일러 없는 과거 커밋 1개 | `rev-list new` 전체가 검사 대상 → **거부**. 실제 저장소는 커밋 337개, 엔진 소스를 건드린 커밋 110개, `Role:` 트레일러 0개 |
| G2 | non-ff 강제 push / `--no-verify --force` | 둘 다 `REJECT: non-fast-forward`(서버 쪽이라 `--no-verify` 무관) -- design 주장 확인 |
| G3 | 삭제 push(`:master`) | 거부. 이때 `GIT_QUARANTINE_PATH` 없음 |
| G4 | `refs/heads/other`, 태그 push | 둘 다 거부 |
| G5 | push 커밋이 `tools/gates/merge_gate.py`를 `exit 0`으로 바꾸고 + code 역할로 tests 쓰기 | **old 판 검사 코드로 거부**(runner.log `checker from <old>`) -- 검사 코드 파일 자체의 자기 변경은 막힌다(design 주장 확인) |
| G6 | push된 test 코드(§9.2-6 증거 재계산이 실행)가 `<gate>/hooks/pre-receive`를 `exit 0`으로 덮어씀 | 그 push는 거부됐지만 **hook이 바뀌었고, 다음 push(트레일러 없음, src+tests 동시 변경)가 그대로 반영됐다** |
| G7 | push된 test 코드가 격리 영역 객체를 gate 본 객체 저장소로 복사하고 `GIT_*`를 지운 환경에서 `git update-ref refs/heads/master <new>` | pre-receive는 거부(exit 1)를 돌려줬는데 **gate `master`가 그 커밋으로 옮겨졌다**(`update-ref rc=0`) |
| G8 | 작업 저장소 `git config remote.gate.receivepack "git -c core.hooksPath=/nonexistent receive-pack"` 뒤 **EL1 허용 형태 그대로** `git push gate master:master` | 같은 커밋이 설정 전에는 거부, 설정 뒤에는 **`a61065e..68654ac master -> master` 반영**(pre-receive가 돌지 않음) |
| G9 | `git merge --no-ff --no-commit side` 뒤 src·tests 내용을 더해 `Role: doc`+`Change-Id` 병합 커밋(side는 docs 한 줄) | §8.2-3(병합은 경로 검사 없음) 모델에서 **반영**. 병합 커밋의 둘째 부모 대비 diff = `src/eng.py`, `tests/t.py` |
| G10 | `git commit -m "merge x" -m "Role: doc" -m "Change-Id: …"`(design §12-6 형태) | `git interpret-trailers --parse` 결과 **`Change-Id`만**. `Role: doc`은 앞 문단이라 트레일러가 아니다 |
| W1 | §12 순서대로: 0 spec push → 1 `worktree add … -b role/test/x gate/master` → interface card 커밋·gate push → 2~7 | test worktree에 interface card **없음**(`x.spec.md`만). 8 `git -C <audit wt> push gate role/audit/x:master` → **non-fast-forward 거부** |
| W2 | 같은 흐름에서 1의 중간 push가 없을 때 | 8 push **성공**(원격 URL이 절대 경로일 때. 상대 URL `../gate.git`은 linked worktree에서 `does not appear to be a git repository`) |
| W3 | 메인 `master`에 gate에 없는 로컬 커밋이 있을 때 `git merge --ff-only gate/master` | `Not possible to fast-forward, aborting`. 로컬 커밋이 없고 무관한 추적 파일만 더러우면 성공 |
| B1 | linked worktree 안 파일의 부모 디렉터리에서 `rev-parse --show-toplevel`·`symbolic-ref --short HEAD` | worktree 루트·`role/code/<id>`가 정확히 나온다. 없는 하위 디렉터리는 `cannot change to` → 가장 가까운 조상으로 구하면 정확. `.git` 안은 `must be run in a work tree`, detached HEAD는 `not a symbolic ref`, 대문자로 바꾼 경로도 정규 대소문자 루트를 돌려준다 |
| A1 | push 트리의 `.gitattributes`에 `tests/test_new.py export-ignore` | bare gate의 `git archive master`에서 **그 파일이 빠진다** |
| C1 | `skills/analog-gmid-design/assets/conftest.py`(code-author 경로 `assets/*.py`에 맞음)에 `pytest_runtest_makereport` hookwrapper로 실패를 통과로 바꿈, `assets/tests/test_x.py`는 `assert 1 == 2` | `pytest --rootdir=<root> skills/.../assets/tests` → **`1 passed`** |
| V4 | design §10 V4 (2)를 글자대로 구현(지역 대입 인라인, Name·Constant를 같은 자리표시자로, 깊이 ≥ 2 BinOp/Call 부분트리 해시) | e329283: 공통 4 → FAIL(참 양성). **독립 리터럴 oracle**: `gm * ro` 대 `2e-3 * 50e3` 공통 1 → FAIL, `i1 + i2` 대 `10e-6 + 20e-6` 공통 1 → FAIL(거짓 양성) |
| T1 | 표 셀 수(이스케이프 안 된 세로선, 코드 펜스 제외) | 05 v2 17표·계획 42표·`00-common` 16표 불일치 0 |

스크립트: `%TEMP%\rv29\a\gate-runner.py`, `…\a\work\tools\gates\merge_gate.py`(모델), `…\rv29\v4_2.py`(+`.out.txt`), `…\rv29\cells.py`.

---

## 1. review28 P-01~P-36 해소 표

| ID | 등급(28) | v2 판정 | 근거 |
|---|---|---|---|
| P-01 | S1 | 해소 | §5 표(비-`gmid`·빈 값·메인 = 오케스트레이터, `overlaps_any`일 때만), 공격 10b. 단 상대 경로 기준이 계획과 다르다(Q-11) |
| P-02 | S1 | 해소 | §4.1 `match_glob` 1(조각 안 토큰 치환, id 형식 검사), 공격 1b |
| P-03 | S1 | 해소 | §6.2 worktree·push·merge 예외 형태, §13.1 ⑤ "§12 전 과정 한 번(오거부 0)" |
| P-04 | S1 | 부분 | §8.2-3 병합 규칙과 §12-6 `-m`은 들어왔으나 §12-6 명령 그대로면 `Role`이 트레일러로 읽히지 않는다(G10, Q-09) |
| P-05 | S1 | 해소 | §12-3 `-b role/audit/<id>`, §9.2-4 Change-Id 구간 규칙. 구간 규칙 자체의 결함은 Q-04·Q-13 |
| P-06 | S1 | 구조로 대체 | `update-ref` 대신 `git merge --ff-only gate/master`(W3: 로컬 커밋 없을 때 동작). 새 교착은 Q-08 |
| P-07 | S1 | 부분 | §8.2-4·§9.2-3 경로마다 `allowed`, 역할↔주체 표(§4.2), 공격 5 변형. 그러나 병합 커밋은 경로 검사 면제라 같은 위조가 병합 커밋으로 통과(G9, Q-03) |
| P-08 | S1 | 구조로 대체 | base = gate master, PowerShell·MultiEdit matcher, 비-`gmid` agent = 오케스트레이터 규칙. 단 EL4가 클라이언트 설정으로 우회된다(G8, Q-01) |
| P-09 | S1 | 해소 | §6.1-1 `except BaseException → exit 2`, 공격 10c. 실측(probe)과 일치 |
| P-10 | S1 | 부분 | §5.1 대상 경로의 worktree로 결합 -- 실측(B1)으로 동작 확인. 그러나 Bash 복합 명령의 상대 대상(`cd X && … > f`), 오케스트레이터가 역할 worktree에 쓰는 경우, 트레일러와 역할의 결합이 없다(Q-04·Q-11·Q-24) |
| P-11 | S1 | 해소(새 결함) | 새 정규화로 e329283 참 양성(V4 실측). 대신 독립 리터럴 oracle을 거짓 양성으로 FAIL시킨다(Q-10) |
| P-12 | S2 | 해소 | §8.1 pre-commit 구조(파이썬 → 역할 검사 항상 → agent 검사 조건부) |
| P-13 | S2 | 해소 | §3.2 gate master 판, §8.1 `core.hooksPath` 절대 경로, ⑤ 실제 `git commit`. gate 부재 시 대체 경로는 Q-12 |
| P-14 | S2 | 부분 | (a) design은 `.githooks` 먼저로 고쳤으나 계획 N3.12.6 ④는 여전히 `.githooks/pre-commit 갱신`이 마지막(Q-16) (b) probe로 즉시 반영 확인 (c) matcher 재등록을 적었으나 등록 직후 EL1이 `.claude/settings.json` 편집을 막는다(Q-17) (d) probe 원복 기록 있음 (e) 사용자 확인 항목으로 둠 |
| P-15 | S2 | 해소 | §6.2 목록 확장(`branch -f`, `checkout -B`, `reset` 전부, 배관, `-c`/환경 변수, `replace`), `GIT_NO_REPLACE_OBJECTS=1`. 목록 밖 `remote.*.receivepack`은 Q-01 |
| P-16 | S2 | 해소 | §7 `gmid-*`에만 적용 |
| P-17 | S2 | 해소 | §14 test-author tools에서 Grep 제외, matcher에 `Grep`·`Glob`, §6.4 |
| P-18 | S2 | 부분 | (a) 계획 EL3 5분류에 `hooks/role_*`·`agents/gmid-*.md` 반영 (b) 계획 표에 code-author의 `hooks/role_*.json`·`tools/gates/*.json`·`requirements.txt` 행 추가 -- 그러나 부트스트랩 오케스트레이터 행에 `hooks/role_*.json`이 없다(Q-16) (c) `부트스트랩` 조건: 계획 "gate 저장소와 hook 설치가 끝나면" 대 design §4.1 "gate가 있고 `pre-receive`가 설치돼 있으면 거짓"(④(b) 중간에 거짓이 된다, Q-06) |
| P-19 | S2 | 해소 | `00-common` v1.8 §9.1에 `write_paths` 포함. 남은 교차 참조 번호 오류는 Q-21 |
| P-20 | S2 | 해소 | §13.3 원천·기계적 변환 규칙·재구성 표시·2e1944a의 V5 입력 |
| P-21 | S2 | 부분 | design §10 V3 인벤토리 = 호출 그래프 도달 test, 변이 id 정의. 계획 N4.2 V3는 여전히 "그 함수를 호출하는 test만"(N9.4 위반, Q-16) |
| P-22 | S2 | 부분 | 이름 목록 없이 구조로 판정(좋음). 그러나 N0.4 8패턴과의 대응이 없고 비-`.py` test 파일(기준선 `.log`)이 빠진다(Q-15) |
| P-23 | S2 | 부분 | `00-common` §8.1·design §15는 `=` 한 토큰. `00-common` §9.3은 여전히 `--gmid-phase <Phase>`·`--gmid-strict <IC:case,...>` 공백 형식(Q-21) |
| P-24 | S2 | 해소 | §16·§17·§18, §13.3 기대 메시지 열 |
| P-25 | S2 | 해소 | U-39로 계획 N7.2에 올림, §19 MG0 행은 U-39 결정 대기. N6.1 0.5 행 착수 조건에 U-39 누락(Q-23) |
| P-26 | S2 | 해소 | ③ "1~11·15·16", 12는 6a(계획 N4.3과 일치) |
| P-27 | S2 | 해소 | §12-3 audit worktree 생성과 초안 위치. 단 계획 N3.12.3 6은 옛 문안(Q-16) |
| P-28 | S2 | 해소 | §9.2-10 `git hash-object --path` |
| P-29 | S3 | 해소 | §14·§19 모두 FAIL 0 |
| P-30 | S3 | 부분 | EL2 두 이름·N4.3 12행 6a는 반영. EL1 도구 목록에 Glob·MultiEdit 없음, N3.12.2 문단 "'사용자만' 경로" 표기 잔존(Q-23) |
| P-31 | S3 | 해소 | §4.4 `--git-common-dir`, 원자적 이름 바꾸기. 캐시 무결성은 Q-11 |
| P-32 | S3 | 구조로 대체 | U-15 행 삭제(닫힘). agent 정의 행 분류는 Q-25 |
| P-33 | S3 | 해소 | matcher에 MultiEdit |
| P-34 | S3 | 해소 | §3.3 첫 점. 트레일러 위조 한계는 빠져 있다(Q-04) |
| P-35 | S3 | 해소 | §9.2-11 |
| P-36 | S3 | 부분 | design §12-8은 audit 브랜치 끝 push, §9.2-5는 A 트리. 계획 N3.12.3 7은 여전히 "audit worktree의 **병합 커밋**을 push"(Q-16) |

집계: **해소 23**(P-01·02·03·05·09·11·12·13·15·16·17·19·20·24·25·26·27·28·29·31·33·34·35) / **부분 10**(P-04·07·10·14·18·21·22·23·30·36) / **미해소 0** / **구조로 대체 3**(P-06·08·32).

---

## 2. 새 결함 -- S1

### Q-01 [S1] EL4는 클라이언트 설정 한 줄로 건너뛸 수 있다 -- "서버 쪽이라 우회 불가"는 틀렸다
* **위치**: §3.1 EL4 행과 첫 점("클라이언트 쪽 우회로 건너뛸 수 없다"), §3.3 셋째 점, §6.2(push 예외·게이트 무력화 행), history 2026-09-18 (2), 계획 N3.12.4 EL4.
* **근거**: G8. gate는 같은 사용자 계정의 로컬 디렉터리이고, `git push gate`의 receive-pack은 **push하는 쪽 설정**으로 실행된다. `remote.gate.receivepack`(또는 `url.<gate>.insteadOf`, `remote.gate.url`/`pushurl`, `git remote set-url`)을 바꾸면 EL1이 허용하는 **정확한 형태** `git push gate master:master`로 pre-receive 없이 반영된다. §6.2가 막는 설정은 `core.hooksPath`·`alias.*`·`GIT_CONFIG_*`뿐이다. 또 `.git/config`는 쓰기 경로표 어느 행에도 겹치지 않으므로(§5 `overlaps_any` 거짓) 오케스트레이터의 `Edit`이 그대로 통과한다. 더 근본적으로 gate의 `hooks/pre-receive`·`refs/`·`objects/`는 같은 계정의 모든 프로세스가 쓸 수 있고, EL1이 스스로 "완전할 수 없다"(§3.3)고 한 Bash/파이썬 스크립트 쓰기가 그 경로를 막지 못한다. 즉 EL4의 신뢰는 EL1과 같은 계층에 있다.
* **수정**: (1) 신뢰 경계를 문서에 사실대로 적는다: "gate는 같은 계정의 프로세스를 막지 못한다 -- EL4는 흐름을 지키는 AI의 실수·지름길을 막는 장치이지 적대적 우회를 막는 경계가 아니다"를 §3.3에 넣고 사용자 확인을 받거나, (2) 실제 경계를 만든다: gate 디렉터리를 다른 로컬 계정 소유로 두고 작업 계정에는 읽기만(Windows ACL), push는 그 계정의 receive-pack을 부르는 경로(ssh localhost 등)로만. (3) 어느 쪽이든 EL1에 `git config`의 쓰기 전부(`remote.*`, `url.*`, `core.*`, `include*`)·`git remote set-url|add|remove`·`--receive-pack`/`--exec` 거부와 고정 규칙 `<git-common-dir>/**` 쓰기 거부를 넣고, 공격 재생에 "receivepack 설정 뒤 허용 형태 push"를 넣는다(기대: EL1 거부, 그리고 (2)를 택하면 EL4 거부).

### Q-02 [S1] pre-receive가 push된 코드를 실행한다 -- 그 코드가 gate hook을 바꾸고 gate master를 직접 옮긴다
* **위치**: §9.2-6(red 재실행·equivalence `commands` 재실행), §3.2 "push되는 커밋이 자기를 검사할 코드를 바꾸지 못한다", history 2026-09-18 (2).
* **근거**: G6·G7. red 재실행은 T의 test와 conftest를, equivalence는 **판정 기록의 `commands` 문자열**(auditor가 쓴 임의 명령)을 gate 안에서 사용자 권한으로 실행한다. 실측에서 그 코드가 (a) `<gate>/hooks/pre-receive`를 `exit 0`으로 덮어써 다음 push의 검사를 끄고, (b) 격리 객체를 본 저장소로 복사한 뒤 `update-ref`로 **거부된 push의 커밋을 gate master로 만들었다**. 검사 코드 파일의 자기 변경(G5)은 막히지만 "push가 자기 검사를 바꾸지 못한다"는 결론은 성립하지 않는다.
* **수정**: pre-receive 안에서 push된 코드를 실행하지 않는다 -- 증거 재계산은 auditor 단계로 두고 gate는 기록·해시·구조만 판정하거나, 재계산을 쓰기 권한 없는 별도 계정·복사본에서 돌린다(Q-01 (2)와 같은 경계). 최소한 gate-runner가 시작·끝에서 자기 hook 파일 해시와 `refs/heads/master` 값을 대조하고 달라지면 복구·경보. 공격 재생에 G6·G7을 그대로 넣는다.

### Q-03 [S1] 병합 커밋은 경로 검사를 받지 않아 "악성 병합"이 EL3·EL4를 통과한다
* **위치**: §8.2-3("병합 커밋 … 경로 검사는 하지 않는다 -- 두 부모 쪽 커밋을 EL4가 검사"), §9.2-3("병합 커밋은 §8.2-3"), §9.2-4(구조 검사는 "역할 커밋이 들어 있으면"만).
* **근거**: G9. 병합 커밋의 트리는 두 부모와 무관한 내용을 담을 수 있다(`--no-commit` 뒤 수정). (i) 역할 커밋이 없는 병합(`Role: doc` 문서 부모 + 임의 트리)은 구조 검사가 발동하지 않고 경로 검사도 없어 소스·tests·`.ai/approvals/**`를 무엇이든 들인다. (ii) 정상 변경의 M도 "M 트리 = K 트리"를 요구하지 않아 T..K 밖의 내용을 M에 섞을 수 있다(K가 T의 후손이므로 정상 M은 K 트리와 같아야 한다). EL3 commit-msg도 같은 면제를 쓴다.
* **수정**: 병합 커밋 규칙을 "Change-Id 구조의 M이어야 하고(부모 = T, K), `git diff <K> <M>`이 비어야 한다. 그 밖의 병합 커밋은 거부"로. EL3 pre-merge-commit/commit-msg도 `MERGE_HEAD` 대비 staged 트리 동일을 검사. 공격 5에 악성 병합 두 형태를 추가.

### Q-04 [S1] 트레일러는 자기 신고라서 역할 결합이 없다 -- 한 역할이 다른 역할의 커밋·판정 기록을 만들 수 있다
* **위치**: §5.1, §6.2(git 명령 판정에 커밋 메시지 검사 없음), §7(EL2는 커밋 안 된 `git status`만), §8.2-2·4, §9.2-4, §3.3.
* **근거**: EL1은 `git commit`의 `Role`·`Change-Id`가 호출한 `agent_type`·worktree id와 같은지 보지 않는다. EL2는 커밋된 내용을 보지 못한다(커밋하면 status가 깨끗하다). EL4의 구조 검사는 `Change-Id`별이고 "그 id 커밋"만 구간에 묶는다. 그래서 code-author가 자기 worktree에서 `Role: test`·`Change-Id: <다른 id>` 커밋과 `Role: audit`·`<다른 id>` 판정 기록 커밋을 만들면 그 다른 id는 test-only 모양(§9.2-4 둘째 점)이 되고, test-only는 재계산할 증거도 없다(`checks.V2.basis`). 본 id의 T..K 구간 규칙은 다른 id 커밋을 세지 않는다. 오케스트레이터도 `git -C $W/<id>-code commit`(§6.2에 금지 규칙 없음)으로 `Role: code` 커밋을 만들 수 있어 DEC-37(메인 세션은 엔진 소스를 쓰지 못한다)이 EL4에서 검출되지 않는다. §3.3은 이 한계를 적지 않았다.
* **수정**: EL1에서 역할의 `git -C <wt> commit`은 메시지(`-m`/`-F`/`--trailer`)를 파싱해 `Role` = 자기 역할, `Change-Id` = 자기 worktree id가 아니면 거부, 오케스트레이터의 역할 worktree 커밋은 §12-6 병합 외 거부. EL2 SubagentStop은 `gate/master..HEAD`의 커밋마다 트레일러가 그 역할·id인지도 본다. EL4는 (a) 각 `Change-Id`의 spec card가 `old` 트리에 있어야 하고(`evidence_type`도 spec card에서 읽는다) (b) 한 push의 역할 커밋은 한 `Change-Id`만 (c) 다른 id의 커밋이 구간 안에 끼면 거부. 남는 한계(같은 계정이면 트레일러 위조를 완전히 막지 못함)를 §3.3에 적는다.

### Q-05 [S1] code-author 경로가 `assets/conftest.py`를 포함해 test 결과를 뒤집을 수 있고, 판정 환경 파일은 어느 행에도 없다
* **위치**: 계획 N3.12.2 `gmid-code-author | skills/analog-gmid-design/assets/*.py`, 계획 N3.12.4 EL3("code 커밋이 … conftest를 바꾸면 차단"), design §4.1·§8.2-4(경로 권한은 `allowed`만으로 판정).
* **근거**: C1. `assets/conftest.py`는 `assets/*.py`에 맞아 code-author가 쓸 수 있고(분류도 '소스'), pytest는 rootdir과 test 디렉터리 사이의 conftest를 읽으므로 hookwrapper 하나로 FAIL이 PASS가 된다(실측 `1 passed`). 계획 EL3의 conftest 차단은 design의 `allowed` 판정에 구현돼 있지 않다. 또 루트·상위의 `conftest.py`, `pytest.ini`, `pyproject.toml`, `setup.cfg`, `tox.ini`, `.gitattributes`(A1), `sitecustomize.py`·`*.pth`는 어느 행에도 겹치지 않아 `overlaps_any` 거짓 → **트레일러 없이도** EL3·EL4를 통과한다(§9.2-3 "역할 밖 경로만 바꾼 커밋은 통과").
* **수정**: 계획 표에 code-author 제외 glob `skills/analog-gmid-design/assets/conftest.py`(그리고 `**/conftest.py`), '판정 환경' 행(위 파일 목록, 주체 `사용자` 또는 `게이트 변경`)을 더한다(판정 표 변경이므로 승인 기록). 공격 재생에 C1과 "루트 `pytest.ini` 추가"를 넣는다.

### Q-06 [S1] 부트스트랩 최초 push(④(b))의 판정 규칙이 없고, 글자대로면 스스로 거부된다
* **위치**: §9.1-2 끝("최초 push(`old`가 0)는 … `new` 판 코드를 쓴다"), §9.2 전체, §4.1 `부트스트랩` 조건, §13.1 ①·④.
* **근거**: G1. old=0이면 `rev-list <old>..<new>`가 전체 이력이다: 커밋 337개 중 엔진 소스를 건드린 110개가 트레일러 0개라 §9.2-3에서 거부된다. 그 밖에도 (a) ① 커밋(`tools/gates/**`, `hooks/role_*.py`, `agents/gmid-*.md`)은 `부트스트랩` 조건에 기대는데 design §4.1은 "gate가 있고 pre-receive가 설치돼 있으면 거짓"이라 바로 그 push에서 거짓 (b) ①의 `.gitignore`와 ④(a)의 `.githooks/*`는 `사용자` 경로인데 어떤 `Role`도 `사용자`에 대응하지 않는다(§4.2) (c) §9.2-2는 `old` 트리의 `plan_tables` 승인 기록을 요구하는데 old가 없다 (d) §9.2-10은 설치된 hook 사본을 요구하는데 설치는 ④(c)로 그 뒤다. 무엇을 건너뛰는지 정하지 않으면 구현자가 임의로 면제를 만들게 된다(WP-02·WP-21).
* **수정**: 최초 push의 규칙을 명시한다. 예: gate 초기화와 첫 반영은 **pre-receive 설치 전에 사용자가** 하고(시드 커밋 = 부트스트랩 승인 기록의 `diff_head`), 그 커밋 id를 `gate_config.json`의 `baseline_commit`으로 둬 §9.2-3은 그 뒤 커밋만 본다. 그다음 pre-receive 설치. §9.2-10은 ④(c) 뒤부터 적용. `부트스트랩` 조건의 끝을 계획과 같게("④ 완료 = gate·hook 설치 둘 다 끝남") 한 곳에서 정의.

### Q-07 [S1] `사용자` 경로 변경이 gate에 들어갈 길이 없다
* **위치**: §4.2(역할 ↔ 주체 표에 `사용자` 없음), §8.2-2·4, §9.2-3, 계획 N3.12.2 `사용자` 행.
* **근거**: `.gitignore`, `install.py`, `.githooks/**`, `agents/gmid-*.md`는 `사용자` 행에만 있다. 커밋에는 `Role`이 필요하고(겹치므로) 어느 `Role`도 `사용자`로 대응하지 않아 `allowed`가 거짓 → EL3 차단, EL4 거부. 사용자가 `--no-verify`로 커밋해도 gate가 거부한다. 부트스트랩 뒤 `install.py`·`.githooks`·agent 정의를 고칠 방법이 없다(DEC-41·N3.12.6 산출물 유지보수 불가).
* **수정**: `Role: user` 트레일러 + 그 커밋의 diff를 덮는 `target_kind: diff` 승인 기록(같은 커밋이나 old 트리) 요구를 EL3·EL4 규칙으로 정의. 승인 기록도 오케스트레이터가 쓰므로(§3.3) 한계를 함께 적는다.

### Q-08 [S1] §12 순서는 interface card와 gate 이동 때문에 8에서 non-ff로 막힌다
* **위치**: §12-1(worktree 생성 **뒤** interface card 커밋·gate push), §12-8, §12 끝 점(오케스트레이터 문서 커밋도 gate push), §6.2(rebase·merge 금지).
* **근거**: W1. 1을 적힌 순서대로 하면 test worktree에는 interface card가 없고(test-author의 유일한 입력, DEC-38), gate master가 test 브랜치의 base보다 앞서 8의 push가 non-fast-forward로 거부된다. 같은 일이 변경 도중의 모든 gate push(다른 문서 커밋, 병렬 변경)로 생긴다. 역할 브랜치를 새 base 위로 옮길 수단은 EL1이 막는다(rebase·cherry-pick·merge 금지). 메인 `master`에 gate에 없는 커밋이 있으면 `merge --ff-only`도 실패한다(W3) -- 오케스트레이터는 스스로 복구할 수 없다.
* **수정**: 1을 "interface card 생성·커밋·gate push → fetch → worktree add"로 순서를 바꾼다. "변경 한 건이 진행 중이면(역할 브랜치 존재) gate push는 그 변경의 8만" 규칙(EL1)과, 막혔을 때의 정의된 절차(정리 후 재생성, 또는 오케스트레이터의 `git -C <audit> merge --no-ff gate/master` 허용 형태 + §9.2-4 구조에 통합 병합 규칙)를 둔다. 공격 재생 ⑤에 W1을 넣는다.

### Q-09 [S1] §12-6 병합 명령의 트레일러가 읽히지 않는다
* **위치**: §12-6 `-m "merge <id>" -m "Role: doc" -m "Change-Id: <id>"`, §6.2("형태가 조금이라도 다르면 거부").
* **근거**: G10. `-m`마다 문단이 되고 `git interpret-trailers --parse`는 마지막 문단만 트레일러로 읽는다 → `Role` 없음 → §8.2-2·§8.2-3 차단, §9.2-3 거부. EL1이 이 형태를 정확히 요구하므로 모든 변경이 6에서 멈춘다(review28 P-04와 같은 결과).
* **수정**: `-m "merge <id>" -m "Role: doc<LF>Change-Id: <id>"` 또는 `--trailer "Role: doc" --trailer "Change-Id: <id>"`로 고치고, 역할 커밋 명령 예(§12-2·5·7, agent 정의)도 같은 형식으로 적는다. ③에 트레일러 파싱 케이스를 넣는다.

### Q-10 [S1] V4 (2)의 새 정규화는 독립 리터럴 oracle을 거짓 양성으로 FAIL시킨다
* **위치**: §10 V4 행("Name과 Constant를 모두 같은 자리표시자 … 깊이 2 이상 부분트리 일치가 1개 이상이면 FAIL"), §16 마지막 문단, 계획 N4.2 V4 (2).
* **근거**: V4 실측. 깊이 2 = 잎 둘을 가진 BinOp 하나라서, 피검 함수에 `a * b`가 있으면 기대값에 곱셈 하나만 있어도 FAIL이다(`gm * ro` 대 `2e-3 * 50e3`, `i1 + i2` 대 `10e-6 + 20e-6`). oracle (a)(물리 불변식·합성 입력)와 (b)(폐형식)는 대개 산술식이라 정상 test 대부분이 막히고, 작성자는 기대값을 계산 없는 리터럴로 바꾸도록 떠밀린다(그 자체가 검증 가능성을 낮춘다). '깊이 2'는 거짓 양성률을 재지 않고 정한 상수다(WP-03).
* **수정**: 부분트리가 아니라 **인라인 전개한 반환식 전체(또는 깊이가 반환식의 일정 비율 이상인 부분트리)**와 기대식 전체의 동형으로 판정하고, 문턱은 e329283 참 양성 + 독립 oracle 거짓 양성 0을 동시에 만족하는 규칙으로 유도한다. redteam에 거짓 양성 케이스(위 두 식, `KCL` 합, 단조성)를 '오거부 0'으로 넣는다. 계획 N4.2 V4 (2) 문구도 함께 고친다.

---

## 3. 새 결함 -- S2

### Q-11 [S2] 오케스트레이터 규칙의 상대 경로 기준이 계획과 다르고, `.git/**`가 보호되지 않는다
* **위치**: design §6.1-4("오케스트레이터 규칙이면 **작업 저장소 루트** 기준"), 계획 N3.12.2 문단("대상 경로를 **해당 worktree 루트** 기준 상대 경로로"), §4.1 `match_glob` 3(`..` 거부), §4.4 캐시.
* **근거**: 역할 worktree(`../wt/<id>-code/skills/.../x.py`)에 대한 오케스트레이터(또는 general-purpose agent) 쓰기는 작업 저장소 기준 `../wt/...`가 되어 (i) 겹침 없음 → 통과(DEC-37 우회, Q-04와 결합) 또는 (ii) `..` → 거부이면 `$TEMP` 쓰기(공격 10b 통과 요구)와 충돌한다. 어느 쪽인지 문서가 정하지 않는다. 또 `.git/config`(Q-01), `.git/hooks`, `<git-common-dir>/gmid-gate-cache/**`(EL1·EL2가 import하는 게이트 코드)가 어느 행에도 없어 오케스트레이터의 Edit이 통과하고, 캐시를 고치면 역할 hook 판정이 바뀐다.
* **수정**: 모든 주체의 대상 경로를 §5.1과 같은 방식으로 **자기 worktree 루트** 기준으로 바꾸고(계획과 일치), 저장소 밖 경로는 "겹침 없음"으로 명시. 오케스트레이터의 역할 worktree 쓰기는 거부(판정 기록 초안은 auditor가 쓴다). 고정 규칙에 `<git-common-dir>/**` 쓰기 거부, 캐시는 사용할 때 gate tree 해시와 대조.

### Q-12 [S2] 부재가 곧 허용이 되는 경로(fail-open)
* **위치**: §8.1 끝("gate 저장소가 아직 없으면 작업 저장소 판 게이트 코드로 실행하고 경고"), §4.1 `부트스트랩`("gate가 있고 pre-receive가 설치돼 있으면 거짓"), §4.4(gate를 못 읽을 때 EL1 동작 미정).
* **근거**: "아직 없음"과 "옮겨짐·지워짐·hook 이름 바뀜"을 구별하지 않는다. `hooks/pre-receive` 이름만 바꾸면 EL4가 모든 push를 받고, 동시에 `부트스트랩` 조건이 참이 되어 오케스트레이터가 `tools/gates/**`·`hooks/role_*.py`를 쓸 수 있고, EL3는 worktree 판 코드(수정 가능)로 경고만 내고 돈다.
* **수정**: 부트스트랩 완료 표지(예: gate master 트리의 `tools/gates/gate_config.json` `bootstrapped: true`, 또는 작업 저장소 `.git/config`의 고정 값)가 있으면 gate·hook 부재는 거부(EL1 exit 2, EL3 exit 1). EL1·EL3가 매번 `pre-receive`·`gate-runner.py` 해시를 승인된 값과 대조. 공격 재생에 "pre-receive 이름 변경 → 거부"를 넣는다.

### Q-13 [S2] Change-Id 구조 규칙(§9.2-4)이 실제 이력에서 잘 정의되지 않는다
* **위치**: §9.2-4, §9.2-5, §12.
* **근거**(점검 (d)):
  * **여러 test 커밋·여러 code 커밋**: 구간 규칙으로 문제없다.
  * **병합 충돌**: K가 T의 후손이면 `merge --no-ff`는 충돌하지 않는다. 충돌이 생기는 유일한 경우는 gate 통합(Q-08)인데 그 규칙이 없다.
  * **equivalence(test 커밋 불변, 계획 N3.12.3·V2)**: `Role: test` 커밋이 없으면 T가 정의되지 않는다(`test_commit` = base? freeze 무의미).
  * **모양 선택**: M이 없으면 test-only로 보는데, red-green 변경이 M 없이 `T, K, A`로 오면 "test 커밋들 뒤에 A"로 읽혀 통과할 수 있다(“그 id의 역할 커밋이 이 모양 밖에 없다”는 조건이 없다). 판정 기록 `evidence_type`과 spec card `evidence_type`의 일치 검사도 없다.
  * **재시도**: auditor FAIL·dispute 뒤의 절차가 없다. M 뒤 code 커밋은 구조 위반이고, 브랜치를 다시 만드는 형태(`branch -D` 후 `worktree add -b`)는 §6.2가 '정리'에서만 허용한다.
  * **T·K 식별**: "부모 둘 = T와 K"에서 순서(첫 부모 = T)를 정하지 않았다.
* **수정**: T = M의 첫 부모, K = 둘째 부모, `evidence_type`은 `old` 트리의 spec card에서 읽고 기록과 대조, 모양마다 "그 id의 역할 커밋이 정확히 이것뿐"을 명시, equivalence의 T(test 커밋 없음 = base 커밋) 정의, 재시도 절차와 EL1 허용 형태를 §12에 추가. 합성 이력 케이스(여러 커밋, M 없는 red-green, 순서 뒤바뀐 부모, 재시도)를 redteam에 넣는다.

### Q-14 [S2] EL2의 메인 worktree 검사는 해시만 저장해서 "새로 생긴 경로"를 구할 수 없다
* **위치**: §7 넷째 점.
* **근거**: PreToolUse에서 `git status` **해시**를 저장하고 PostToolUse에서 "새로 생긴 경로 중 쓰기 경로표와 겹치는 것만" 본다고 했는데, 해시로는 경로 집합의 차이를 구할 수 없다. 또 `status-<tool_use_id>` 파일은 호출마다 생겨 §4.4 "상한: 커밋 id 하나"와 맞지 않는다.
* **수정**: 겹치는 경로의 (경로, 상태, blob) 집합을 저장하고 PostToolUse에서 비교 뒤 삭제. 저장 위치의 상한 규칙을 적는다.

### Q-15 [S2] V5가 비-`.py` test 파일과 N0.4 패턴 일부를 보지 않는다
* **위치**: §10 V5 행, 계획 N0.4 '기준 약화'(8패턴)·N4.2 V5.
* **근거**: V5 입력은 test 함수 단위 AST 대조라서 test 분류의 기준선 `.log`(e5fbf92 박제의 실제 위치), JSON 픽스처는 판정되지 않는다. N0.4 8패턴과 ①~⑥의 대응이 없고, 리터럴이 아닌 격자·허용오차 변경(`range(n)` → `range(2*n)`, `tol` → `tol*10`), `for`/`with`/`while` 아래로의 assert 이동, 기대값 리터럴을 식으로 바꾸는 변경은 어느 패턴에도 걸리지 않는다.
* **수정**: test 분류의 비-`.py` 파일 변경은 무조건 승인 기록 요구. N0.4 8패턴마다 AST 판정식과 대응 번호를 표로 적고, 위 우회 예를 redteam 케이스로.

### Q-16 [S2] 계획 v5.19와 design이 어긋난 채 남은 곳(N9.4 위반)
* **위치와 근거**:
  * 계획 N3.12.3 6: `git worktree add ../wt/<id>-audit <test 커밋>`(6에서, `-b` 없음) / 7: "audit worktree의 **병합 커밋**을 push" -- design §12-3·8과 다름(P-05·P-27·P-36의 수정이 계획에 안 들어감). design §20은 "N3.12.3 7"만 고쳤다고 적는다.
  * 계획 N4.2 V3: "변이마다 그 함수를 호출하는 test만" -- design §10 V3(호출 그래프 도달)와 다름.
  * 계획 N3.12.6 ④ 순서: gate → install → `.githooks/pre-commit` 갱신(마지막) -- design §13.1 ④ (a)가 먼저. 산출물 표에 `pre-merge-commit`·`gate-runner.py`·`pre-receive` 없음.
  * 계획 N3.12.2: 부트스트랩 오케스트레이터 행에 `hooks/role_*.json` 없음 -- `install.py`는 옆 `.json`이 없으면 `PreToolUse`/`Write|Edit`(`HOOK_DEFAULT`)로 등록하므로 EL2 두 hook에는 sidecar가 필수다.
  * 계획 N3.12.4 EL4: "브랜치 역할 일치"(gate는 브랜치 이름을 받지 않는다), "`05-role-separation` §3.2 '역할 밖'"(v2 §3.2는 판 절).
* **수정**: 계획을 design과 같게 개정하고 §20 목록에 모두 올린다(판정 표 행 추가는 `plan_tables` 승인 대상).

### Q-17 [S2] 부트스트랩 ④(c)의 설정 복구가 EL1에 막히고, gate-runner의 소재·판이 없다
* **위치**: §13.1 ④(c), §6.3, §3.3 셋째 점, §2 EL4 행.
* **근거**: probe 실측대로 hook은 등록 직후부터 돈다. `install.py --only hooks` 직후 오케스트레이터가 `.claude/settings.json`의 matcher를 "지우고 다시 등록"하려 하면 §6.3(`.claude/**` 사용자 경로)이 거부한다. `gate-runner.py` 초안은 ①에서 쓴다고 했지만 저장소 안 경로가 없고(§2·계획 N3.12.6 산출물에 없음), gate에 설치된 판은 어떤 트리에도 없어 리뷰·재현·변경 이력이 남지 않는다.
* **수정**: 설정 대조와 복구를 hook 등록 **전**(sidecar로 matcher를 정해 한 번에 등록)이나 사용자 몫으로. `gate-runner.py`·`pre-receive` 원본을 `tools/gates/gate/`에 두고 설치된 파일의 해시를 승인 기록에 적어 EL1·EL3가 대조(Q-12).

### Q-18 [S2] `git archive`는 push된 `.gitattributes`를 따른다
* **위치**: §9.1-2, §9.2-6.
* **근거**: A1. 증거 재계산용 트리에서 `export-ignore` 파일이 빠지고 `export-subst`는 내용을 바꾼다. `.gitattributes`는 어느 행에도 없어 아무 커밋이나 추가할 수 있다(Q-05).
* **수정**: 트리를 `git ls-tree -r` + `git cat-file blob`으로 그대로 풀거나 attributes를 무력화한 방법으로 추출하고, `.gitattributes`를 판정 환경 파일로 보호.

### Q-19 [S2] "CC-3 병합 전" 예외의 판정식이 없다
* **위치**: §9.2-7("CC-3 병합 전 예외"), `00-common` §9.3.
* **근거**: gate가 이 조건을 무엇으로 참/거짓으로 정하는지 없다(구현자가 고르면 WP-21 위반, 잘못 고르면 엄격 집합 대조가 영구히 꺼진다).
* **수정**: 기계 판정식을 정한다(예: `old` 트리 conftest가 `--gmid-phase` 옵션을 등록하는지 -- `pytest --help` 출력 또는 AST로). 판정 결과를 거부 메시지에 싣고 케이스로 고정.

---

## 4. 새 결함 -- S3

* **Q-20** §9.2-6 재계산(전체 red·equivalence 명령)이 pre-receive 안에서 제한 시간 없이 돈다. push가 무기한 막히고 임시 디렉터리 정리 실패(Windows 파일 잠금) 처리가 없다. 제한 시간과 초과 = 거부를 적는다.
* **Q-21** 교차 참조 오류: `00-common` §8.2·§9.1이 `05-role-separation` §3·**§14.2**를 인용하지만 v2의 해시 절은 §15.2, 표 읽기는 §4다(design §15.2는 "00-common이 이 식을 인용한다"고 적음). `00-common` §9.3은 `--gmid-phase <Phase>`·`--gmid-strict <IC:case,...>` 공백 형식이 남았다(P-23 잔여). `00-common` Status가 "승인 … 뒤 개정"과 "사용자 승인 대기"를 함께 적는다.
* **Q-22** `role_hook_input_probe.md`: "원자료 `*.json`(36개)"는 JSON 35개 + `probe.py`다. "PostToolUse(Bash, PowerShell, **Write**)에 `agent_type`"은 근거 파일이 없다(PostToolUse 등록 matcher가 `Bash|PowerShell`, 원자료 PostToolUse 13개 모두 Bash·PowerShell). design §9.1의 gate 실측은 원자료가 커밋돼 있지 않다(이 보고서 G2·G5·A1 등이 같은 동작을 재현했다).
* **Q-23** 계획 N6.1 0.5 행 착수 조건에 U-39 없음. N4.3 공격 11 "RTL agent가 **임의 파일** Edit → 무동작"은 v5.19 판정 범위(비-`gmid` agent도 겹치면 판정)와 모순 -- design처럼 "RTL 파일"로. N3.12.4 EL1 도구 목록에 Glob·MultiEdit 없음. N3.12.2 문단의 "'사용자만' 경로" 표기.
* **Q-24** §5.1·§6.2: (a) 대상 경로 대소문자 -- `rev-parse`는 정규 대소문자 루트를 돌려준다(B1)이므로 상대 경로를 만들 때 대소문자 무시 접두 비교가 필요하다 (b) Bash 복합 명령의 `cd` 뒤 상대 대상 해석 규칙 없음(hook `cwd`는 세션 시작 디렉터리) (c) §6.4 test-author 열람 거부에서 '소스 분류'를 어느 루트 기준으로 계산하는지(메인·code worktree의 소스 경로 포함) 명시.
* **Q-25** §2 agent 정의 행: `tools:`(test-author에서 Grep 제외)는 DEC-38 강제의 입력이라 `00-common` §3.1 3번 주(입력으로 쓰이는 부분은 2번)에 따라 그 부분은 `코드`다. §20 착수 조건에 U-16·U-38의 승인 기록 id가 없다(N9.2-7은 "승인 기록 id"를 요구; U-38은 `20260918-u38-jsonschema`).
* **Q-26** ④(b) `git remote add gate <gate_path>`는 **절대 경로**여야 한다(상대 URL은 linked worktree에서 실패, W2). 기존 `.githooks/pre-push`(kb 색인 eval 게이트)가 모든 `git push gate`에서 돈다 -- 상호작용(차단 시 절차)을 적는다.
* **Q-27** §19 "`--mode installed` … 대상 케이스 전부"와 §13.1 ⑤의 설치 후 재생 목록(부분집합)이 다르다. 공격 6~9·15의 installed 모드 의미를 정하거나 DoD 문구를 ⑤ 목록으로.
* **Q-28** 커밋된 `role_hook_probe_logs/`의 개인정보·보안 범주: 로컬 절대 경로(사용자 이름 포함), `session_id`·`transcript_path`·`prompt_id`·`agent_id`·`tool_use_id`, `permission_mode: bypassPermissions`, 조수 최종 메시지 발췌(`last_assistant_message`), 도구 표준출력(디렉터리 목록), `background_tasks` 설명. **토큰·키·비밀번호·이메일 주소는 없다**(정규식 검색 0건). 저장소가 GitHub `origin`으로 push되므로 세션·transcript 식별자는 가리거나 필요한 키만 남긴 요약본으로 바꾸는 것을 권한다.

---

## 5. 점검 항목별 결론

| 점검 | 결론 |
|---|---|
| 1 P-01~P-36 | 해소 23 / 부분 10 / 미해소 0 / 구조로 대체 3 (§1) |
| 2(a) gate 모델 | non-ff·삭제·master 외 참조 거부, `--no-verify` 무관, 검사 코드 파일 자기 변경 불가 -- 주장대로(G2~G5). 최초 push는 규칙 없음·자기 거부(G1, Q-06). push된 코드 실행으로 hook 교체·ref 직접 이동(G6·G7, Q-02). 클라이언트 설정 우회(G8, Q-01). 악성 병합(G9, Q-03) |
| 2(b) worktree 흐름 | `git -C <audit wt> push gate role/audit/<id>:master`는 원격 URL이 절대 경로면 동작, `merge --ff-only gate/master`는 메인에 로컬 커밋이 없으면 동작(W2·W3). 적힌 순서대로면 interface card 누락·non-ff(W1, Q-08). §12-6 트레일러 파싱 실패(G10, Q-09) |
| 2(c) §5.1 결합 | 동작 확인(B1). 없는 하위 디렉터리는 조상 규칙으로 해결, `.git` 안·detached는 오류 → 거부로 처리하면 됨. 대소문자·Bash 상대 경로는 미정(Q-24) |
| 2(d) Change-Id 구조 | 정상 여러 커밋은 문제없음. 병합 충돌은 구조상 없음. equivalence T 미정, M 없는 red-green 수용 가능성, 재시도 절차 없음(Q-13). 다른 id 끼워 넣기로 위조 test-only 수용(Q-04), 악성 병합 수용(Q-03) |
| 3 정합성 | 계획 N3.12.3 6·7, N4.2 V3, N3.12.6 ④·산출물, N3.12.2 부트스트랩 `hooks/role_*.json` 행, EL4 교차 참조(Q-16). `00-common` §8.2·§9.1 절 번호, §9.3 옵션 표기(Q-21). 공격 번호·개수(16건, 0.5 대상 13건 = 1~11·15·16, 12~14는 6a)는 세 문서가 일치. U-15 닫힘은 N7.2와 일치, U-39는 N7.2에 있으나 N6.1 착수 조건에 없음(Q-23). **④가 쓰는 경로**: (a) `.githooks/*`는 표상 `사용자`만 -- 계획 문단의 "④(hook 설치 전) 한 번" 예외로 EL1은 통과하지만 EL3·EL4 규칙에는 그 예외가 없다(Q-06·Q-07). (c)의 `.claude/**`는 `install.py`가 쓰고(명령 형태라 EL1 판정 밖) 이후 복구는 EL1 거부(Q-17) |
| 4 WP | WP-01: gate-runner 원본 소재 없음(Q-17), `conftest` 차단 규정 미구현(Q-05). WP-02 fail-open: gate·hook 부재(Q-12), 병합 면제(Q-03), 역할 밖 판정 환경 파일(Q-05), CC-3 예외(Q-19). WP-03: V4 깊이 2(Q-10). WP-13: §2 표 두 소유 칸은 모든 행에서 다르고 허용 값 안 -- 결함 없음. 실측 없이 사실로 적은 전제: "서버 쪽이라 우회 불가"(Q-01), "push가 자기 검사를 못 바꾼다"(Q-02) |
| 5 원자료 보안 | 비밀·토큰·이메일 없음. 경로·세션 식별자·권한 모드·메시지 발췌 범주만(Q-28) |
| 6 N9.2 | 1~8 절 모두 있음(3 §16, 4 §17, 5 §18, 6 §19, 7·8 §20). 7은 승인 기록 id 누락(Q-25). 숨은 열린 질문: 최초 push 규칙(Q-06), 사용자 경로 변경 경로(Q-07), 동시 진행·재시도(Q-08·Q-13), CC-3 판정식(Q-19), gate 신뢰 경계(Q-01·Q-02). 표 셀 수 불일치 0(T1) |

---

## 6. 집계와 판정

| 구분 | 건수 | 항목 |
|---|---|---|
| review28 해소 | 23 | §1 |
| review28 부분 | 10 | P-04·07·10·14·18·21·22·23·30·36 |
| review28 미해소 | 0 | -- |
| review28 구조로 대체 | 3 | P-06·08·32 |
| 새 S1 | 10 | Q-01 ~ Q-10 |
| 새 S2 | 9 | Q-11 ~ Q-19 |
| 새 S3 | 9 | Q-20 ~ Q-28 |

**판정: 재작성 필요** -- v2는 review28의 규칙 결함 대부분을 닫았고, §4(표 파싱·`match_glob`), §5(역할 판정, 실측과 일치), §6.1 fail-closed, §8.1 hook 구조, §13.3 사례 재생, §15.2 해시는 수정 후 유지할 수 있다. 그러나 새 구조의 핵심 주장 두 가지 -- "gate `pre-receive`는 클라이언트 쪽 우회로 건너뛸 수 없다", "push되는 커밋은 자기 검사를 바꾸지 못한다" -- 가 실측으로 틀렸다(G6~G8). 따라서 §3(신뢰 경계), §9(EL4: 병합 규칙, 구조 규칙, 증거 재계산 위치, 최초 push), §12(순서·트레일러 형식·재시도), §13.1 ④는 규칙을 다시 짜야 한다. 역할 결합(Q-04)과 판정 환경 파일(Q-05)은 계획 N3.12.2 표 개정이 함께 필요하다.
