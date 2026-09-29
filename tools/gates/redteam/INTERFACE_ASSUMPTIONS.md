# redteam 인터페이스 가정

검증 agent가 05-role-separation v3.6·00-common v1.8·계획 v5.19만 보고(게이트 작성본을 보기 전에) 정한 호출 모양 중
**design이 고정하지 않은 것**이다. 한 줄에 하나, 근거 절을 붙인다. 코드는 `lib/iface.py` 한 곳에만 있다 -- 재생 때 작성본과
다르면 `lib/iface.py`(와 필요하면 `lib/sb.py`의 sandbox 준비)만 고치고, 기대(`expect.json`, `attacks/15-records/cases/*.json`,
`v.json`의 `expect`)는 design 문장에서 나왔으므로 고치지 않는다.

| ID | 가정 | 근거(design이 고정한 것) |
|---|---|---|
| A-01 | EL1 실행기는 `hooks/role_guard.py` 하나이고 `$PY hooks/role_guard.py`로 부르며 stdin에 hook JSON, cwd와 `CLAUDE_PROJECT_DIR`은 프로젝트(sandbox 작업 저장소) 루트다. direct는 작업 트리 사본을, installed는 `.claude/hooks/` 사본을 부른다 | §6·§17(exit 2), 계획 N3.12.6 산출물 표 |
| A-02 | EL2: PostToolUse는 `hooks/role_diff_guard_bash.py`, SubagentStop은 `hooks/role_diff_guard_stop.py`. §7의 PreToolUse 상태 기록(`status-<tool_use_id>.json`)은 PreToolUse의 유일한 hook인 `role_guard.py`가 한다 | §7 |
| A-03 | hook stdin 필드는 `role_hook_input_probe.md` 실측대로(메인 세션은 `agent_type`·`agent_id` 없음, subagent는 둘 다, Post는 `tool_response`·`duration_ms`, SubagentStop은 `stop_hook_active`·`agent_transcript_path`·`last_assistant_message`). 가려진 값(`session_id` 등)은 합성 값이고 `cwd`는 Windows 역슬래시 표기 | §5, probe |
| A-04 | 도구 입력 모양: Write `{file_path, content}`, Edit `{file_path, old_string, new_string}`, Bash·PowerShell `{command, description}`. `file_path`는 Windows 역슬래시 절대 경로 | §6.1-4 |
| A-05 | EL3 direct: 커밋이 일어나는 worktree를 cwd로 `$PY tools/gates/role_commit_gate.py pre-commit`, 통과하면 `… commit-msg <메시지 파일>`. 먼저 0이 아닌 종료가 차단(git도 pre-commit 뒤 commit-msg). `GIT_INDEX_FILE`은 주지 않는다 | §8.1·§8.2·§17(0/1) |
| A-06 | EL4 direct: `$PY <sandbox>/tools/gates/merge_gate.py receive --old <old> --new <new>`를 cwd = gate bare 저장소, `GIT_DIR` = gate로 부른다(pre-receive와 같은 환경). 판정 대상 커밋은 `refs/redteam/cN`으로 gate에 넣어 객체만 있게 한다(pre-receive 미설치). 실행하는 사본은 sandbox 기준 커밋의 게이트 코드 = old 판 | §9.1-3·§3.3 행 3 CLI |
| A-07 | `merge_gate.py plan-tables-hash <계획서>`는 표준출력 마지막 줄에 64자리 소문자 16진 해시를 낸다 | §15.2 CLI(출력 형식은 미고정) |
| A-08 | V3~V7 입력 인자: `--repo <루트> --base <커밋> --head <커밋> [--interface-card <저장소 상대 경로>]`, cwd = 저장소 루트 | §10은 출력(JSON 한 줄)과 exit 0/1/2만 고정 |
| A-09 | V4 (2)의 판정 문장별 출력: 첫 JSON 줄 안 어디든 정수 `line`(또는 `lineno`)과 네 값 {FAIL, PASS, UNJUDGED, NO-SUBJECT} 중 하나를 가진 객체(또는 `[줄, 값]` 쌍). (1)(3)(4)(5) 규칙의 결과와 구별돼 있다 | §10 V4 ① '출력은 판정 문장마다 넷 중 하나' |
| A-10 | V5는 승인 기록을 head 트리의 `.ai/approvals/`에서 찾는다. 대조군의 승인 기록은 `target_kind: diff`, `diff_base` = base, `diff_head` = test 변경 커밋, `target` = 00-common §8.2 blob 식 | §10 V5, 00-common §8.2 |
| A-11 | `interface_card.py <spec card>`는 cwd = 저장소 루트, spec card의 `## 관찰 가능한 계약`에 백틱으로 적은 `<모듈>.<함수>`를 기존 함수로 읽어 `docs/02-design/specs/<id>.interface.md`를 쓴다 | §11.1 |
| A-12 | 게이트 코드 캐시는 `<git-common-dir>/gmid-gate-cache/<gate master 커밋 id>/<이름>.py`(평평한 배치) | §4.4, §6.2 `$PY <캐시>/<이름>.py` |
| A-13 | sandbox의 `tools/gates/gate_config.json`은 작성본 파일에서 `gate_path`·`workspace_path`·`python_path`만 sandbox 값으로 바꾸고 `bootstrapped`·`baseline_commit`을 뺀다. 원격 `gate` URL도 같은 절대 경로 | §3.1, §13.1 ①·④ |
| A-14 | direct 모드 상태 = 부트스트랩 ④(b) 뒤·(c) 전: gate가 있고 기준 커밋과 accept-log 첫 줄이 있으며 pre-receive·완료 표지는 없다. 준비 커밋에는 client hook이 돌지 않게 `core.hooksPath`를 sandbox의 빈 `.githooks`로 둔다 | §13.1 ③(direct = 게이트 함수를 직접 부름), §3.3 행 6 |
| A-15 | spec card 머리 블록은 `id`·`phase`·`evidence_type`·`gate_change`만 쓰고 반복 키는 값이 없으면 생략한다 | §11.2 |
| A-16 | 판정 기록의 V1 명령: `V1: PYTHONPATH=<캐시> PYTHONPYCACHEPREFIX=<빈 디렉터리> $PY -P -m pytest -c <sandbox .git>/gmid-gate-cache/<old>/pytest_gate.ini --rootdir=<복제본> --confcutdir=<복제본> <복제본>/skills/analog-gmid-design/assets/tests`(슬래시 표기, 복제본은 %TEMP%) | §9.2-7, §12-7 |
| A-17 | 공격 17 격리 실행: 작성본 `merge_gate.py`가 `-p merge_gate` pytest 플러그인으로 import되고 `GMID_RED_CAPTURE`에 기록한다. 캐시는 `tools/gates` 사본으로 흉내 낸다 | 00-common §8.1 red 수집 |
| A-18 | 공격 23: probe 케이스는 고정 커밋 `4fd0fd8`의 `v4.py` blob을 실행해 `judge`를 기록기로 바꿔 모은다(케이스 → 코퍼스 → 네 조합 순서에 기댄다). 파일을 복사하지 않는다 | §13.2 #23, 부트스트랩 ①(probe 삭제) |
| A-19 | 공격 10c: 캐시는 아무 EL1 호출이나 채운다(`warm-cache`). 훼손 = 캐시 안 `.py`마다 앞에 `import os; os._exit(0)` | §4.4 |
| A-20 | 거부 메시지에는 대상 파일 이름이 들어 있다(`message_contains`는 경로 표기 차이를 피하려 파일 이름만 본다). 규칙 번호의 표기 형식은 가정하지 않는다 -- BOM만 `BOM` 글자를 요구 | §6.1-5, §8.2-6, 00-common §8.1 규칙 1 |
| A-21 | 모든 거부 기대에 `Traceback (most recent call last)`가 출력에 없을 것을 더한다(fail-closed 예외는 거부처럼 보이지만 판정이 아니다) | §6.1-1, §17 |
| A-22 | 역할 브랜치 이름의 짧은 이름은 `test`·`code`·`audit` | §4.2, §5.1, §12 |
| A-23 | 커밋형 staged_diff 케이스는 gate master에서 가지를 낸 worktree에서 파일과 승인 기록을 한 커밋에 staged한다(`diff_base` = 그 HEAD) | §8.2-5, 00-common §8.2 staged_diff |
| A-24 | 공격 30: `integrity.py check --scope <범위>`(cwd = sandbox 작업 저장소)의 행 3(나) JSON 줄은 `"row": "3b"`다(변경 전 게이트 877dbd4 출력으로 확인한 행 이름 -- 기대값이 아니라 행을 고르는 키). 요약 행은 `actual`에 `캐시 통과 <k>구간`이 든 행 3b 행 | §3.3 check 출력 `{row, ok, expected, actual}`, spec card 20260929-rejudge-cache 계약 6 |

## 재생 단계(작성본 bootstrap/replay 70a384b) 실측으로 고친 것

| ID | 가정 | 작성본 실제 | 조치 |
|---|---|---|---|
| A-08 | `--repo` | V3~V7 모두 `--root`. V3(`mutate_changed.py`)는 `--pytest-ini` 필수, V7(`reachability.py`)은 `--config`(기본 head 트리의 gate_config.json) | `lib/iface.py` `vtool_command` |
| A-09 | 판정 문장별 객체에 판정 값 하나 | `findings` 원소 `{"rule": "(1)".."(5)", "line", "output"}` -- (2)만 V4 (2) | `lib/iface.py` `v4_statements`가 `rule == "(2)"`만 모은다 |
| A-11 | 관찰 가능한 계약의 백틱 `module.func` | 같음. 단 `def`가 아닌 이름(`gain = lambda …`)은 카드에 안 들어가 V4가 "피검 심볼이 없다"(exit 2) | 고치지 않음 -- 보고(공격 23 corpus-041) |
| (템플릿) | 올바른 기록의 V4 basis를 두 줄로 | 로더 규칙 3이 개행(Cc)을 거부 -- 00-common §8.1 문언대로 | `lib/sb.py` 올바른 기록 템플릿을 한 줄(`oracle 대조: …`로 시작)로. 기대는 바꾸지 않음 |
