---
template: design
version: 3.6
plan_version: 5.19
---

# gain-budget-gmid-sizing -- 05-role-separation Design Document

> **Summary**: Phase 0.5 역할 분리 인프라의 설계. 위협 범위는 계획 N3.12.0(사용자 결정 C)이다: **이력에 있던 자기 은폐 패턴은 막고, 같은 계정 권한으로 게이트를 부수는 의도적 행위는 막지 않고 드러나게 한다.** 겹은 EL1(도구 호출)·EL2(결과)·EL3(커밋)·EL4(로컬 gate 저장소의 `pre-receive`)이고, 무결성 대조가 게이트 훼손을 감지한다. 쓰기 경로표 파싱, 역할 판정, 판정 기록 로더, auditor 검사 도구(V3~V7), interface card·spec card·dispute, 변경 한 건의 명령 시퀀스, 부트스트랩, 공격 재생, agent 정의 3개.
>
> **Project**: chip-design-skills (analog-gmid-design skill) · **Author**: Claude Code (오케스트레이터)
> **Date**: 2026-09-18 · **Status**: **v3.6 승인됨**(2026-09-21, 승인 기록 `20260921-05-role-separation-design` -- 아래 '사용자 승인 대기' 문구는 승인 전 상태 기록이다). v3.6 -- 독립 검증 review30~34를 반영했고, review35는 위협 범위(N3.12.0)로 재분류해 범위 안 항목만 고쳤다(§13.5). 마지막 좁은 확인 review36: **승인 가능**(S1 0·S2 0·S3 4, S3 중 둘을 반영). 문서 검토는 이 판으로 끝내고 남은 우려는 부트스트랩 공격 재생으로 판정한다. 사용자 승인 대기(DEC-51) V4 (2)는 사용자 결정 (c)(확실한 복사 검출기 + auditor oracle 대조). 독립 검증 전, 사용자 승인 대기(DEC-51)
> **Planning Doc**: [gain-budget-gmid-sizing.plan.md](../../01-plan/features/gain-budget-gmid-sizing.plan.md) v5.19 · N3.12.0 위협 범위 · N6.1 `0.5` 행 · **공통 정의**: [00-common](gain-budget-gmid-sizing.00-common.design.md)(v1.7 승인 `20260918-00-common-design`, v1.8 개정은 이 문서의 승인이 덮는다)

Context Anchor: 계획서에 `## Context Anchor` 절이 없어 옮기지 않는다.

---

## 0. 이 문서를 읽는 법

* 정의는 계획서와 `00-common`이 정본이다. 이 문서는 **게이트가 어떻게 동작하는가**만 더한다(N9.4).
* **위협 범위(N3.12.0)가 모든 규정의 전제다.** 규정은 '막는다' 행의 패턴을 막고, '드러나게 한다' 행의 행위는 §3.3 무결성 대조로 감지한다. 어떤 규정이 '드러나게 한다' 행위까지 막겠다고 적으면 그것은 과장이다.
* **기댄 실측**: hook 입력(`role_hook_input_probe.md`), git hook 발동(review28 §0, review30 H1: 병합의 hook 시점), gate `pre-receive` 동작과 우회(review29 §0 G1~G10·W1~W3·B1·A1·C1, review30 I2~I8·B1·J1), V4 (2) 검출기(§10, 실제 e329283 함수와 변환 test 입력). 실측이 없는 전제는 "0.5 실측으로 고정"이라고 표시한다.
* **규정은 산문이고, 게이트가 실제로 거부한다는 증거는 공격 재생의 실행 로그다**(WP-21·WP-02). 규정마다 증명하는 공격 번호를 붙인다(§13).
* 구성안: **B -- 계획서 표 직접 읽기**(사용자 선택) + **EL4 = 로컬 gate `pre-receive`**(사용자 결정) + **위협 범위 C**(사용자 결정).
* 명령의 `$PY`는 `C:\Python314\python.exe`다. **게이트가 부르거나 게이트 판정에 쓰이는 Python 실행 중 `-m`·`-c` 형태**(red 수집·V1의 `-m pytest` 등)는 `$PY -P`로 한다(`PYTHONSAFEPATH`와 같다) -- `-m`은 현재 디렉터리를 `sys.path` 맨 앞에 넣어, 역할 밖 경로에 심은 `merge_gate.py`·`pytest.py`가 캐시 판 게이트 코드와 pytest를 대신한다(review33 M2-01 실측, `-P`에서는 캐시 판이 로드된다). **스크립트 형태**(`$PY <경로>/<이름>.py`: hook 실행기, `gate-runner.py`, `integrity.py`, V3~V7 도구, `00-common` §10 도구)는 `-P`를 쓰지 않는다 -- `-P`는 스크립트 디렉터리까지 빼서 같은 디렉터리 모듈 import가 깨진다(review34 M3-03 실측). **게이트 스크립트**는 경로가 게이트 코드 캐시(`<git-common-dir>/gmid-gate-cache/<커밋 id>/`) 또는 `<gate_path>` 안인 `.py`다. 게이트 판정에 쓰이지 않는 스크립트(`agent-quality/check_agents.py`, 사용자 도구 등)에는 이 절의 규칙이 적용되지 않는다(review35 M4-08).

---

## 1. 범위 (N9.2-1)

| 이 문서 절 | 구현하는 계획서 절·ID |
|---|---|
| §3 구조, 게이트 코드의 판, 무결성 대조 | N3.12.0, N3.12.4 |
| §4 쓰기 경로표 파싱과 경로 판정 | N3.12.2 |
| §5 역할 판정과 worktree 결합 | N3.12.2 hook 판정 범위, U-15(닫힘) |
| §6 EL1 `role_guard.py` | N3.12.4 EL1, DEC-37·38 |
| §7 EL2 `role_diff_guard_{bash,stop}.py` | N3.12.4 EL2 |
| §8 EL3 `.githooks/*`와 `role_commit_gate.py` | N3.12.4 EL3 |
| §9 EL4 gate `pre-receive`, `merge_gate.py`, 판정 기록 로더 | N3.12.4 EL4, N3.12.5, `00-common` §8·§9, CC-1·CC-2 |
| §10 auditor 검사 도구 V3~V7, `import_layering` | N4.2, DEC-39·40 |
| §11 interface card·spec card·dispute | N3.12.3, N3.12.5 |
| §12 변경 한 건의 명령 시퀀스 | N3.12.3 |
| §13 부트스트랩, 공격 재생, 과거 사례 재생 | N3.12.6, N4.3, DEC-41 |
| §14 agent 정의 3개 | N3.12.1, N3.12.6 산출물 |
| §15 `00-common` §17이 넘긴 구현 세부 | `00-common` §17 |
| §16~§20 | N9.2-3~8 |

MG0(N6.1 0.5 행)는 U-39 결정 뒤 그 결정대로 한다(§19).

---

## 2. 구현 주체 분류 (`00-common` §3.2)

부트스트랩 산출물은 N3.12.6 ①~④에서 오케스트레이터가 쓰고, 거부 동작을 사용자가 공격 로그로 확인해 승인한다. 부트스트랩 뒤 이 코드를 바꾸는 것은 N3.12.3 흐름의 게이트 변경이다(구현 `gmid-code-author`, 판정 기준 `gmid-test-author`).

| 항목 | 결과물 | 부류 | 판정 근거(§3.1 순서 번호와 이유) | 고정 수단 | 구현 소유 | 판정 기준 소유 | 산출 spec card 또는 승인 기록 |
|---|---|---|---|---|---|---|---|
| 이 문서 | design 문서 | `AI 직접` | 3 -- 작성 | 독립 검증 → 사용자 승인 | `오케스트레이터` | `독립 검증 agent` | 05 승인 기록 |
| 쓰기 경로표 파서·경로 판정 | `tools/gates/role_paths.py` | `코드` | 2 -- 쓰기 허용 판정 | 공격 1·1b·2·10·10b·11 | `오케스트레이터` | `사용자` | 부트스트랩 승인 기록 |
| EL1·EL2·세션 시작 | `hooks/role_guard.py`, `hooks/role_diff_guard_{bash,stop}.py`, `hooks/role_session_start.py`(실행기)와 `.json`, `tools/gates/role_hooks.py`(판정) | `코드` | 2 -- 거부 판정 | 공격 1·1b·2·4·10·10c·11·17·18·20·24·25 | `오케스트레이터` | `사용자` | 같음 |
| EL3 | `.githooks/{pre-commit,commit-msg,pre-merge-commit}`, `tools/gates/role_commit_gate.py` | `코드` | 2 -- 커밋 차단 | 공격 3·16 (i)(a)(ii)(a)·17·19 | `오케스트레이터` | `사용자` | 같음 |
| EL4 | `tools/gates/gate/{pre-receive,gate-runner.py}`(원본), `tools/gates/merge_gate.py` | `코드` | 2 -- base 반영 판정 | 공격 5·15·16·17·19·20 | `오케스트레이터` | `사용자` | 같음 |
| 무결성 대조 | `tools/gates/integrity.py` | `코드` | 2 -- 훼손 감지 | 공격 21·22 | `오케스트레이터` | `사용자` | 같음 |
| V3~V7, interface card, import 계층 | `tools/gates/{mutate_changed,test_lint,weakening_diff,source_lint,reachability,interface_card,import_layering}.py` | `코드` | 2 -- 검사 판정 | 공격 6~9·23, 사례 5건 | `오케스트레이터` | `사용자` | 같음 |
| 공격·사례 재생 데이터 | `tools/gates/redteam/**` | `코드` | 2 -- 판정 기준 | 사용자 로그 확인 | `오케스트레이터` | `사용자` | 같음 |
| agent 정의의 `tools:` 줄 | `agents/gmid-*.md` frontmatter | `코드` | 2 -- DEC-38 강제 입력(test-author에 Grep 없음) | `check_agents.py` + 공격 18 | `오케스트레이터` | `사용자` | 같음 |
| agent 정의 본문 | `agents/gmid-*.md` | `AI 직접` | 3 -- 작성(권한은 EL1~EL4가 강제) | `check_agents.py` FAIL 0 + 사용자 확인 | `오케스트레이터` | `사용자` | 같음 |

---

## 3. 구조와 무결성

### 3.1 겹의 배치

| 겹 | 어디서 | 무엇을 보나 | 막는 것(N3.12.0 '막는다') |
|---|---|---|---|
| EL1 | Claude Code PreToolUse hook | 도구 호출 하나 | 역할 밖 편집, 검사 끄기, 트레일러 흉내, 흐름 밖 git 명령 |
| EL2 | PostToolUse(Bash)·SubagentStop hook | 역할 worktree 결과, 역할 커밋의 트레일러 | Bash로 우회한 역할 밖 쓰기·커밋 |
| EL3 | git client hook | 커밋 하나 | 동시 변경, 경로 권한, 판정 표·topology·structure 조건, 흐름 밖 병합 |
| EL4 | 로컬 gate 저장소 `pre-receive` | gate `master`로 들어오는 커밋 전부 | 위 모두를 커밋 단위로 다시, 변경 한 건 구조, 판정 기록 |

* **base = gate 저장소의 `master`.** 위치 `C:/Users/HSLEE/Documents/Todoc/fpga/gmid-gate.git`(`gate_config.json`의 `gate_path`). 작업 저장소의 원격 `gate`는 **절대 경로**로 등록한다(상대 URL은 linked worktree에서 실패, review29 W2).
* 작업 저장소 `master`는 gate `master`를 `git merge --ff-only gate/master`로만 받는다(참조 직접 이동 금지).
* GitHub `origin`은 백업이다. gate에 반영된 뒤 사용자가 push한다.
* **EL1~EL4는 N3.12.0 '막는다' 패턴을 막는다. 같은 계정 권한으로 게이트를 부수는 행위(gate 파일·참조 직접 수정, 원격 설정 조작, hook이 보지 못하는 스크립트로 만든 커밋)는 막지 못한다**(review29 G6~G8 실측) -- 그것은 §3.3이 감지한다.

### 3.2 게이트 코드의 판

* EL4는 **gate `master` 판**(push 전 `old`)의 게이트 코드를 쓴다. EL1~EL3도 gate 저장소의 `master` 판을 쓴다(`git --git-dir=<gate_path>` 로 읽어 캐시, §4.4). push되는 커밋이 자기를 검사할 코드 파일을 바꾸지 못한다(review29 G5 실측).
* 트리 추출은 `git archive`가 아니라 `git ls-tree -r -z <commit> <경로>` + `git cat-file blob`로 한다 -- `git archive`는 push된 `.gitattributes`의 `export-ignore`를 따라 파일을 뺀다(review29 A1 실측).
* **gate는 push된 코드를 실행하지 않는다**(N3.12.0). 풀어 쓰는 것은 `old` 판 게이트 코드뿐이고, push된 트리는 데이터로만 읽는다(review29 G6·G7: 실행하면 그 코드가 gate를 바꾼다).

### 3.3 무결성 대조 (`tools/gates/integrity.py`)

'드러나게 한다' 행위를 감지한다. **대조 실패는 모든 게이트가 거부하는 상태**로 만들고 사용자에게 알린다(fail-closed, review29 Q-12).

| 대조 대상 | 기준값 | 언제 |
|---|---|---|
| gate `hooks/pre-receive`, `gate-runner.py` | gate `master` 트리의 `tools/gates/gate/*` blob과 바이트 동일(eol 필터 적용 `git hash-object --path`) | EL1이 `git push gate`를 허용하기 직전, EL3 매 실행, `gate-runner.py` 시작 |
| 작업 저장소 git 설정 | 메인과 역할 worktree 각각에서 `git config --show-origin --get-regexp <패턴>`을 패턴 `^remote\.gate\.`, `^url\.`, `^core\.hookspath$` 세 번 돌려 **모든 범위**(system·global·local·worktree·include 파일)를 읽는다(review30 I2~I4). 허용: `remote.gate.url`(= `gate_path` 절대 경로)·`remote.gate.fetch`·`core.hooksPath`(= `.githooks` 절대 경로)이고 셋 다 출처가 작업 저장소 `.git/config`. 그 밖의 `remote.gate.*`(`receivepack`·`pushurl`·`uploadpack`), 값이 `remote.gate.url`의 접두인 `url.<base>.insteadOf`·`url.<base>.pushInsteadOf`(gate URL을 바꾸는 것만 -- gate와 무관한 전역 `url.*` 설정은 보지 않는다, review31 N-13), 다른 출처의 이 키들은 실패 | 같음 |
| gate `master` 참조 | `<gate_path>/gmid-accept-log`: 줄마다 `<old> <new> <시각>`, 첫 줄은 ④(b)에서 사용자가 쓴 `<baseline_commit> <baseline_commit> <시각>`. (가) **사슬**: 첫 줄의 old = new = `baseline_commit`, 각 줄 old = 앞 줄 new, 마지막 줄 new = 현재 gate `master`. (나) **구간 재판정**(review30 I6b): 줄마다 `old..new`를 그 `old` 판 게이트 코드의 `merge_gate.py receive --old <old> --new <new>`로 **데이터만** 다시 판정(§9.1-3과 같은 방식 -- 실행하는 코드는 이미 반영된 게이트 코드뿐). **재판정 통과 캐시**(2026-09-29 개정, spec card `20260929-rejudge-cache`): 재판정을 통과한 `(old, new)` 쌍을 `<git-common-dir>/gmid-gate-cache/rejudged`에 한 줄씩 적고, 다음 세션부터는 캐시에 있는 쌍을 건너뛴다. 단 **로그 마지막 줄은 캐시에 있어도 항상 재판정**하고, 실패한 쌍은 적지 않으며, 캐시는 현재 로그에 있는 쌍만 남긴다(상한 = 로그 줄 수). 개정 근거: 전 구간 재판정 비용이 로그 길이에 비례해 86구간에서 세션 시작 348초(2026-09-29 실측, hook 기본 제한 600초의 58%)가 됐다. 캐시 한 줄로 마지막이 아닌 위조 구간의 재판정을 건너뛰게 하는 공격(review31 N-06)은 같은 계정의 의도적 공격이라 §13.5 알려진 한계로 둔다(N3.12.0 '드러나게 한다'의 범위 조정, WP-22 기준). 표지 뒤 로그가 없거나 비면 실패(review30 I6c) | (가) EL1 `git push gate` 직전·`gate-runner.py` 시작, (가)(나) 세션 시작 |
| gate `hooks/` 디렉터리의 다른 파일(`*.sample` 포함), gate 쪽 `core.hooksPath`(`git --git-dir=<gate_path> config --show-origin --get core.hooksPath` -- global·system까지 읽는다) | 없어야 한다 | EL1 `git push gate` 직전, EL3 매 실행, `gate-runner.py` 시작, 세션 시작(review30 I8: gate `core.hooksPath`가 있으면 `gate-runner.py`가 돌지 않아 그 시작 시점 대조는 한 번도 돌지 않는다) |
| 설치된 Claude Code hook | `.claude/hooks/role_*.py`와 gate `master`의 `hooks/role_*.py`(eol 필터) 동일, `.claude/settings.json`의 역할 hook **네** 항목(PreToolUse·PostToolUse·SubagentStop·SessionStart)의 `event`·`matcher`가 `hooks/role_*.json`과 같다 | 세션 시작, EL1 `git push gate` 직전 |
| 부트스트랩 완료 표지 | gate `master` 트리의 `tools/gates/gate_config.json`에 `"bootstrapped": true`가 있으면 gate·hook이 **없는 것도 실패**(부재 = 허용이 되지 않게, review29 Q-12) | 모든 겹 |

* `accept-log`도 같은 계정이 고칠 수 있다(N3.12.0 한계). 그래서 행 3은 로그만 믿지 않고 구간마다 **커밋 자체를 다시 판정**한다 -- 참조를 옮긴 뒤 로그에 줄을 덧붙여도 그 구간의 트레일러 없는 커밋·구조 위반이 드러난다. 드러나게 하는 장치이지 적대적 행위자를 막는 경계가 아니다. 감사 로그는 사용자가 볼 수 있게 세션 시작 때 마지막 N줄을 출력한다(N = `gate_config.json`의 `audit_tail_lines`, 사용자가 정한다).
* **세션 시작 hook** `hooks/role_session_start.py`(`hooks/role_session_start.json`의 `"event": "SessionStart"`, review30 R-10): 행 1~6 대조, `status-*.json` 잔여 삭제(§7), 감사 로그 출력. SessionStart의 exit 코드가 무엇을 막는지는 재지 않았다 -- 그래서 대조 실패는 `<git-common-dir>/gmid-gate-cache/integrity-failed` 표지 파일로 남기고, EL1·EL3는 이 파일이 있으면 판정 범위의 모든 호출·커밋을 거부한다.
* **`integrity.py check [--scope session|push|commit|gate]`**(review30 R-22): 범위에 해당하는 행을 대조해 행마다 한 줄 JSON `{"row", "ok", "expected", "actual"}`을 출력한다. 전부 일치 0 / 불일치 1 / 입력 오류 2(§17). `--scope session`이 전부 일치하면 `integrity-failed` 표지를 지운다(복구 확인의 유일한 경로). 겹마다의 `--scope`: 세션 시작 `session`, EL1 push 직전 `push`, EL3 `commit`, `gate-runner.py` `gate`.
* 무결성 실패 메시지는 무엇이 기준과 다른지와 복구 절차(사용자가 세션 밖에서 확인·복구한 뒤 `integrity.py check --scope session`)를 적는다.

---

## 4. 쓰기 경로표 파싱과 경로 판정 (N3.12.2)

### 4.1 함수 (`tools/gates/role_paths.py`)

```python
@dataclass(frozen=True)
class PathRule:
    actor: str        # "gmid-code-author" | "gmid-test-author" | "gmid-verification-auditor" | "오케스트레이터" | "사용자"
    glob: str
    exclude: str | None
    condition: str    # "없음" | "자기 변경 id" | "게이트 변경" | "부트스트랩" | "승인 기록" | "status 전이만" | "판정 환경" | "판정 트리"

def read_write_paths(plan_text: str) -> tuple[PathRule, ...]: ...
def match_glob(pattern: str, rel_path: str, change_id: str | None) -> bool: ...
def allowed(actor: str, rel_path: str, ctx: WriteContext) -> Verdict: ...     # Verdict(ok, reason, rule)
def overlaps_any(rel_path: str) -> bool: ...
```

* 표 읽기(절 제목 `#### N3.12.2 `, 이스케이프 안 된 `|`, 셀 수 검사)는 `merge_gate.read_plan_tables`와 **같은 함수**다. '주체'·'조건' 값 집합 밖이면 표 파손과 같이 거부.
* **`match_glob`**: `<id>`는 조각 안의 부분 문자열 토큰 -- `change_id`로 치환(없으면 그 패턴은 맞지 않음). `change_id`는 `00-common` §8.1 `id` 형식. 조각 나누기는 `/`, `**`는 0개 이상 조각, 나머지 조각은 `fnmatch.fnmatchcase`. **패턴과 경로 모두 `casefold` 뒤에 대조한다**(review33 M2-02: Windows 파일 시스템은 대소문자를 무시해 pytest가 `Pytest.ini`를 설정으로 읽는데, 대소문자 구분 대조에서는 `**/pytest.ini` 행에 맞지 않아 역할 밖이 됐다 -- 실측에서 실패 test 종료 코드 1 → 0). EL3·EL4는 추가로 **casefold하면 기존 트리 경로와 같아지는 다른 경로**(`Skills/…` 대 `skills/…`)를 더하는 커밋을 거부한다.
* **상대 경로 기준**(review29 Q-11, 계획 N3.12.2 "해당 worktree 루트"): 대상 경로가 속한 worktree의 루트 기준. 루트는 `git -C <대상의 가장 가까운 존재하는 조상 디렉터리> rev-parse --show-toplevel`. 루트와 대상의 접두 비교는 `os.path.normcase` 뒤에 한다(Windows는 대소문자를 무시, review29 B1). 어느 worktree에도 속하지 않는 경로(`$TEMP` 등)는 `overlaps_any` 거짓 -- 그래서 격리 복제본 **바깥**의 pytest 설정 파일이 판정에 끼지 못하게 판정 실행 쪽에서 막는다(§12-7 `-c`·`--confcutdir`, review34 M3-02). `판정 트리` 안의 경로는 행에 맞지 않아도 `overlaps_any` 참.
* **`allowed`**: 그 주체의 행 중 하나에 경로 glob으로 맞고 제외 glob에 맞지 않으며 조건이 참이면 허용.
  * `부트스트랩`: 부트스트랩 완료 표지(§3.3)가 있으면 거짓.
  * `승인 기록`·`status 전이만`: EL1은 허용하고 EL3·EL4가 내용으로 판정(§8.2-5).
* **`판정 트리` 기본 거부**(review34 M3-01): 경로가 조건 `판정 트리`인 행(주체 `사용자`, glob `skills/analog-gmid-design/**`)에 맞고 **다른 조건의 행 어디에도 맞지 않으면** `allowed`는 `사용자` 외 모두 거짓이다 -- 판정 트리 안에는 '역할 밖'이 없다. `-P` 뒤에도 역할 밖 경로에 둔 패키지(`assets/numpy/__init__.py`가 서드파티를, `assets/eng/__init__.py`가 같은 디렉터리의 `eng.py`를 가림)가 트레일러 없는 커밋으로 판정을 뒤집던 결함(실측 종료 1 → 0)을 이름 목록이 아니라 기본 거부로 막는다. 대가: 판정 트리에 새 종류의 파일을 두려면 먼저 쓰기 경로표를 개정한다(판정 표 변경 승인). 판정 트리 밖에서 import될 수 있는 것(`workspaces/*.py`·`workspaces/*/__init__.py`, 어디서든 `__pycache__/**`·`*.pyc`·`*.pyd`·`*.so`)은 `판정 환경` 행이 덮는다.
* **`판정 환경` 행 우선**(review30 J1): 경로가 조건 `판정 환경`인 행(주체 `사용자`)의 경로 glob에 맞고 제외 glob에 맞지 않으면, 다른 주체의 행에 맞아도 `allowed`는 거짓이다(`사용자` 외). pytest는 rootdir부터 test 디렉터리까지의 모든 `conftest.py`와 위로 가장 먼저 찾은 ini 파일을 읽으므로 판정 환경 파일은 어느 디렉터리에 있어도 판정을 바꾼다. `overlaps_any`는 이 행에도 참이다.

### 4.2 역할 ↔ 주체 ↔ 트레일러

| `agent_type` | 주체 | 트레일러 `Role:` |
|---|---|---|
| `gmid-code-author` | `gmid-code-author` | `code` |
| `gmid-test-author` | `gmid-test-author` | `test` |
| `gmid-verification-auditor` | `gmid-verification-auditor` | `audit` |
| 그 밖(메인 세션 포함) | `오케스트레이터` | `doc` |
| -- (사용자가 세션 밖에서) | `사용자` | `user` |

### 4.3 경로 5분류

정의는 계획 N3.12.4 EL3(v5.19)가 정본이다. 분류는 **소스·test 동시 변경 판정**과 **test-author 소스 열람 거부**(§6.4)에만 쓴다. 경로 권한은 §4.1 `allowed`로 판정한다. 어느 분류에도 들지 않는 경로가 '역할 밖'이다.

### 4.4 계획서·게이트 코드를 읽는 판과 캐시

* 모든 겹은 gate `master`의 계획서를 읽는다(EL4는 `old`).
* 파싱 결과와 풀어 둔 게이트 코드는 gate `master` 커밋 id를 키로 `<git-common-dir>/gmid-gate-cache/<커밋 id>/`에 둔다. 사용할 때마다 디렉터리 안 파일마다 `git hash-object`로 blob id를 다시 계산해 gate 트리 blob id와 대조하고(캐시 훼손 감지, review29 Q-11), 다르면 지우고 다시 푼다. 쓰기는 임시 이름 + 원자적 이름 바꾸기, 상한은 커밋 id 하나(WP-10).
* **모든 겹**(EL1~EL4, 세션 시작, `integrity.py`)의 git 호출에 `GIT_NO_REPLACE_OBJECTS=1`을 둔다(review30 R-20: gate의 `refs/replace/*`가 푸는 게이트 코드를 바꾸지 못하게).

---

## 5. 역할 판정과 worktree 결합

실측(`role_hook_input_probe.md`): subagent는 모든 관련 이벤트에 `agent_type`·`agent_id`를 주고 메인 세션은 주지 않는다(U-15 닫힘). subagent의 hook 입력 `cwd`는 세션 시작 디렉터리이고 subagent Bash의 `cd`는 호출 사이에 유지되지 않는다. **메인 세션은 `cd`가 다음 호출까지 유지되고 hook 입력 `cwd`도 따라 바뀐다**(review30 R-18). 상대 경로 대상은 hook 입력 `cwd` 기준으로 해석한다.

| hook 입력 | 주체 | 판정 범위 |
|---|---|---|
| `agent_type` ∈ {`gmid-code-author`, `gmid-test-author`, `gmid-verification-auditor`} | 그 역할 | 모든 쓰기 |
| `agent_type` 없음·`gmid-*` 아님·빈 값 | `오케스트레이터` | 대상이 `overlaps_any`이거나 **역할 worktree 안**일 때 판정, 아니면 통과(계획 N3.12.2 hook 판정 범위) |
| `gmid-`로 시작하는데 위 셋이 아님 | 거부 | 알 수 없는 역할 |

### 5.1 worktree 결합

* 역할은 자기 worktree의 **절대 경로**로 파일을 쓰고 git은 `git -C <자기 worktree>`로만 부른다(§14). Bash 복합 명령에서 `cd` 뒤의 상대 경로 대상은 해석하지 않고 거부한다(hook은 `cd` 결과를 모른다, review29 Q-24).
* 쓰기 대상의 worktree 루트(§4.1)의 브랜치(`git -C <루트> symbolic-ref --short HEAD`)가 `role/<역할 짧은 이름>/<id>`여야 하고, 그때 `change_id = <id>`. 아니면 거부. detached HEAD도 거부.
* **오케스트레이터는 역할 worktree에 쓰지 못한다**(판정 기록 초안은 auditor가 쓴다, review29 Q-04·Q-11). 예외는 §12-6 병합 명령 하나.

---

## 6. EL1 `hooks/role_guard.py` (PreToolUse)

matcher: `Edit|Write|MultiEdit|NotebookEdit|Bash|PowerShell|Read|Grep|Glob`.

### 6.1 흐름

1. **실행기 전체를 `try: … except BaseException: → exit 2`**(Claude Code는 exit 2로만 막는다 -- 실측). 게이트 코드 import 실패, git 실패, 무결성 실패도 exit 2.
2. 무결성 대조(§3.3) 중 '모든 겹' 항목과 표지 확인.
3. 주체 판정(§5). 오케스트레이터 규칙에서 판정 범위 밖이면 exit 0.
4. 도구별 대상: `Edit`·`Write`·`MultiEdit`·`NotebookEdit`는 `file_path`(`notebook_path`). `Read`·`Grep`·`Glob`은 §6.4에만. `Bash`·`PowerShell`은 §6.2.
5. `allowed` 판정. 거부 메시지: 주체·대상·판정 행(없으면 "맞는 행 없음")·조건·그 주체가 쓸 수 있는 glob 목록.

### 6.2 명령 판정 (Bash·PowerShell)

**분해기**(review30 P1·P2 -- `shlex`는 쓰지 않는다: 따옴표 밖 줄바꿈을 공백으로 보고 `$'…'`를 못 읽는다): 따옴표와 이스케이프 상태를 추적하며 **따옴표 밖의** `;`·`&&`·`||`·`|`·`&`·줄바꿈에서만 단순 명령으로 나눈다. 단 리다이렉트 연산자 안의 `&`는 구분자가 아니다(review31 N-08): `>&`, `<&`, `&>`, `&>>`, `N>&M`, `N<&M`(예: `2>&1`, `>&2`). `|&`(bash의 `2>&1 |`)는 파이프 구분자 하나다(review32 M-11). 리다이렉트 연산자 전체는 `>`, `>>`, `>|`, `<`, `<<`(heredoc), `<<-`, `<<<`, `&>`, `&>>`와 앞에 붙는 파일 기술자 번호이고, 대상 토큰은 연산자 바로 뒤 토큰(`&M` 형태는 대상 없음). 따옴표 안의 줄바꿈은 인자의 일부다(§12-6의 두 줄 `-m`). 이스케이프 규칙은 셸을 따른다 -- Bash: 따옴표 밖 역슬래시는 다음 문자를 그대로(그래서 따옴표 없는 `C:\…`는 bash에서도 역슬래시가 사라진다), 작은따옴표 안은 모두 그대로, 큰따옴표 안은 `$`·백틱·`"`·역슬래시·줄바꿈 앞에서만 이스케이프. **역슬래시-줄바꿈(줄 이음)은 따옴표 밖과 큰따옴표 안에서 둘 다 지운다**(bash와 같다, review31 N-08). PowerShell: 이스케이프는 백틱, 역슬래시는 그대로. 토큰의 경로는 `\`를 `/`로 바꾼 뒤 판정한다.
* 명령 치환 `$(…)`·백틱·프로세스 치환 `<(…)`·`>(…)`, PowerShell `$(…)`·`@(…)`는 안쪽을 같은 분해기로 재귀 분해해 판정한다. heredoc(`<<`, `<<-`)은 구분자 줄까지를 데이터로 건너뛴다(따옴표 없는 구분자의 본문은 명령 치환만 재귀 판정).
* 거부(분해하지 않음): `$'…'`, 닫히지 않은 따옴표·괄호, 구분자를 찾지 못한 heredoc. 거부 메시지는 분해하지 못한 위치를 적는다.

| 규칙 | 주체 | 거부 대상 |
|---|---|---|
| 검사 끄기 | 전부 | `--no-verify`, `git commit -n`, `core.hooksPath` 변경 전부, `GIT_CONFIG_*`·`GIT_CONFIG_PARAMETERS` 환경 변수, `git -c alias.*` |
| git 설정 쓰기 | 전부 | `git config`의 쓰기 전부(`--get*`·`--list` 외), `git remote add/set-url/rename/remove` -- 부트스트랩 ④(b)의 `git remote add gate` 한 번은 hook 설치 전이다(review29 Q-01) |
| 저장소 내부 | 전부 | `<git-common-dir>/**`, `<gate_path>/**`를 가리키는 인자·`--git-dir`·리다이렉트·도구 대상. 예외(review31 N-07): 게이트 코드 캐시 `<git-common-dir>/gmid-gate-cache/<커밋 id>/`를 **읽기·실행**하는 두 형태 -- `$PY <캐시>/<이름>.py …`의 스크립트 인자와 `PYTHONPATH` 환경 값의 **첫 원소**가 캐시인 것 -- hook은 원소를 `;`로만 자른다(Windows Python의 `os.pathsep`). POSIX식 `:` 목록(`/c/…:/c/…` -- MSYS bash는 이것을 `;` 목록으로 바꿔 넘긴다)은 hook이 자르지 않으므로 첫 원소가 캐시로 보이지 않아 거부된다(안전 쪽, review34 M3-09). 캐시 경로 비교는 `C:\…`·`C:/…`·`/c/…` 표기를 같은 절대 경로로 정규화한 뒤 `normcase`로 한다. 형태: bash `PYTHONPATH=<캐시>`·`PYTHONPATH='<캐시>;<기존>'`, PowerShell `$env:PYTHONPATH = '<캐시>'`·`'<캐시>;<기존>'`(review32 M-09). `-m`·`-c` 실행이면 `$PY -P`, 캐시 스크립트 실행(`$PY <캐시>/<이름>.py`)이면 `-P` 없이(§0 -- review35 M4-04: 여기서 둘 다 `-P`라고 적어 §0과 모순이었다)(§12-0·§12-7, `00-common` §8.1). 캐시를 쓰기 대상으로 가리키는 것(리다이렉트, `cp`·`mv`·`rm` 대상, 도구 쓰기)은 거부 |
| push | 전부 | `git push` 전부. 예외: 오케스트레이터의 `git push gate master:master`(문서 커밋)와 `git -C <audit worktree> push gate role/audit/<id>:master`(§12-8). 강제(`+`, `--force*`) 제외. **진행 중인 변경이 있으면**(역할 브랜치 존재) 문서 커밋 push는 거부한다(review29 Q-08: 도중에 gate가 움직이면 §12-8이 non-ff로 막힌다) |
| 참조 이동·hook 없는 커밋 생성 | 전부 | `update-ref`, `symbolic-ref`(쓰기), `branch -f`/`-M`, `branch -D`(§12 정리·재시도 형태 외), `checkout -B`, `switch -C`, `reset` 전부, `commit-tree`, `write-tree`, `hash-object -w`, `update-index`(쓰기), `replace`, `filter-branch`, `rebase`, `am`, `cherry-pick`, `revert`, `stash`(apply·pop 포함) |
| 정리 전 dispute 보존 | 오케스트레이터 | `git worktree remove $W/<id>-code`, `git branch -D role/code/<id>`: code worktree에 `docs/02-design/disputes/<id>.md`가 있고 그 blob id(`git -C $W/<id>-code hash-object <그 파일>`)가 메인 worktree HEAD의 spec card `## dispute 기록` 절에 없으면 거부(review30 R-16, §12 재시도) |
| 병합 | 전부 | `git merge` -- 예외: §12-6 형태, §12-8의 `git merge --ff-only gate/master`(메인 worktree) |
| worktree 관리 | 역할 | `git worktree` 전부. 오케스트레이터는 §12의 `add`·`remove` 형태만 |
| 커밋 트레일러 | 역할 | `git -C <자기 worktree> commit`은 `--trailer "Role: <자기 역할>" --trailer "Change-Id: <자기 worktree id>"`를 **정확히 이 형태로** 가져야 한다. `-F`·에디터 메시지·다른 값은 거부(review29 Q-04) |
| 역할 worktree 커밋 | 오케스트레이터 | 역할 worktree 안의 `commit`은 거부(§12-6 병합만) |
| test 되돌리기 | 전부 | `git checkout -- <tests 경로>`, `git restore <tests 경로>` |
| 쓰기 대상 명령 | 전부 | 리다이렉트(`/dev/null` 제외), `tee`, `sed -i`, `cp`·`mv`·`rm`·`touch`·`mkdir` 대상, PowerShell `Set-Content`·`Add-Content`·`Out-File`·`New-Item`·`Remove-Item`·`Copy-Item`·`Move-Item`의 대상 -- 대상마다 §6.1-5 판정 |
| 역할의 메인 worktree git 쓰기 | 역할 | `git -C`가 없는 쓰기 git 명령. 예외: auditor의 §12-7 `git clone --no-hardlinks --no-local <자기 audit worktree> <TEMP>/<id>-iso`와 `git -C <TEMP>/<id>-iso …`(review30 R-19) |
| PowerShell | 역할 | 역할은 PowerShell을 쓰지 않는다(agent 정의 tools에 없음) |

* 목록은 완전할 수 없다(N3.12.0). 빠진 경로는 EL2·EL3·EL4가 커밋과 결과로 잡고, 게이트 자체를 부수는 경로는 §3.3이 감지한다.

### 6.3 고정 규칙

* `<gate_path>/**`, `<git-common-dir>/**`, `.claude/hooks/**`, `.claude/settings*.json`, `.githooks/**`는 모든 주체의 도구 쓰기를 거부(주체가 `사용자`인 경로와 저장소 내부).

### 6.4 test-author의 소스 열람 거부 (DEC-38)

역할이 `gmid-test-author`이고 `Read`의 `file_path`, `Grep`·`Glob`의 `path`(없으면 대상 worktree 루트 전체)가 **어느 worktree든**(메인·code worktree 포함) 소스 분류를 가리키거나 포함하면 거부. interface card는 허용. test-author의 tools에는 Grep이 없다(§14). Bash 읽기는 막지 못한다(N3.12.4 한계) -- 결과는 V3·V4가 잡는다.

---

## 7. EL2 `role_diff_guard_bash.py`(PostToolUse `Bash`)·`role_diff_guard_stop.py`(SubagentStop)

* `gmid-*` 역할에만 적용(메인 저장소는 도구 부산물로 늘 더럽다).
* 역할 worktree(`role/<역할>/*` 체크아웃) 각각의 `git status --porcelain=v1 -z --untracked-files=all`에서 무시 목록(`git check-ignore` 참 + `__pycache__/`·`.pytest_cache/`)을 빼고 남은 경로마다 `allowed`. **다른 역할의 worktree**는 그 경로가 **그 worktree 주인 역할**에게 `allowed`(그 worktree의 변경 id)이면 호출 역할의 위반으로 세지 않는다 -- §12-3이 audit worktree에 미커밋으로 두는 `base_check.json`이 다음 역할을 막던 오거부(⑤ 재생 D-7, 게이트 변경 `20260921-gate-flow-liveness`).
* **메인 worktree에 역할이 만든 변경**: PreToolUse에서 `tool_use_id`별로 메인 worktree의 (경로, 상태, blob) 중 쓰기 경로표와 겹치는 것의 집합을 `<git-common-dir>/gmid-gate-cache/status-<tool_use_id>.json`에 쓰고, PostToolUse에서 다시 구한 집합과의 차이(새로 생기거나 바뀐 것)가 있으면 위반. 비교 뒤 파일 삭제. 남은 파일은 세션 시작 때 지운다(상한, review29 Q-14).
* **SubagentStop**: `agent_type`의 역할 worktree(브랜치 `role/<역할 짧은 이름>/<id>`)에서 **역할별 범위**의 커밋이 전부 `Role: <그 역할>`·`Change-Id: <id>`이고 병합 커밋이 아닌지 본다(도구 호출 밖에서 만든 커밋도 여기서 드러난다, review29 Q-04). 범위(review30 E2 -- 다른 역할의 커밋을 넣지 않는다): test = `gate/master..HEAD`, code = `role/test/<id>..HEAD`, audit = M이 있으면 `M..HEAD`, 없으면 `role/test/<id>..HEAD`(M = `git rev-list --merges -n 1 HEAD`이고 `role/test/<id>` 끝의 후손일 때 -- equivalence(test 커밋 0개)에서는 `role/test/<id>` 끝 = `old`이고 `old`가 역할 밖 병합일 수 있다 -- 그때 M = `old`로 잡혀도 두 범위(`M..HEAD`와 `role/test/<id>..HEAD`)가 같아 결과가 같다(review33 M2-08). test-only는 병합이 없다). audit 범위의 커밋은 **최대 1개**다(review31 N-02: v3.1은 병합이 없으면 '비어 있어야 한다'고 적어 test-only의 auditor 종료를 매번 거부했다). 정상 흐름의 오거부 0은 공격 20 (e)(세 판정 유형 각각)와 ⑤가 보인다.
* 위반이면 stderr에 경로·커밋과 사유, exit 2. 실행기 전체 fail-closed.

---

## 8. EL3 git client hook

### 8.1 `core.hooksPath`와 `.githooks/*`

* `core.hooksPath` = 작업 저장소 `.githooks`의 **절대 경로**(모든 worktree가 같은 파일을 쓴다).
* `.githooks/pre-commit`: ① 파이썬 찾기, 없으면 exit 1 ② 무결성 대조(§3.3, `--scope commit`) ③ gate `master` 판 `role_commit_gate.py pre-commit`을 **항상**(`MERGE_HEAD`가 있으면 -- `merge --no-commit` 뒤 `git commit` -- §8.2-4 경로 검사는 하지 않는다, §8.2-3) ④ staged `agents/*.md`가 있을 때만 `check_agents.py`.
* `.githooks/commit-msg`: `role_commit_gate.py commit-msg <파일>`. **병합 판정은 여기서 한다**: 모든 병합 경로(`merge --no-ff`, `merge --no-commit` 뒤 `git commit`)에서 이 시점에는 `MERGE_HEAD`가 있다(review30 H1 실측).
* `.githooks/pre-merge-commit`: 무결성 대조만(`merge --no-ff`는 pre-commit 대신 이것과 commit-msg를 돌린다, review28 E1). 이 시점에는 `MERGE_HEAD`가 없고 병합 대상은 환경 변수 `GITHEAD_<sha>`로만 보이므로 병합 판정을 두지 않는다(review30 H1).
* 기존 `.githooks/pre-push`(kb 색인 eval 게이트)는 kb 경로가 push될 때만 돈다 -- gate push도 대상이 되므로, 그것이 막으면 사용자에게 보고하고 기존 절차를 따른다.
* 부트스트랩 완료 표지 전에는 작업 저장소 판 게이트 코드로 돌고 경고를 출력한다. 표지 뒤에는 gate가 없으면 차단(§3.3).

### 8.2 `role_commit_gate.py` 판정

1. staged 경로를 §4.3으로 분류. **병합 아닌 커밋**에서 역할 밖 경로만이면 통과(트레일러 불필요 -- gmid 밖 작업, review31 N-01). 병합 커밋은 3으로.
2. **트레일러**(commit-msg): `git interpret-trailers --parse`로 읽은 트레일러에 `Role: code|test|audit|doc|user` 정확히 하나. `code`·`test`·`audit`과 변경 한 건의 병합 커밋(3 (나))은 `Change-Id` 정확히 하나. 역할 밖 병합(3 (라))과 역할 밖 경로만 바꾼 병합 아닌 커밋(1)에는 트레일러를 요구하지 않는다(review32 M-06). 트레일러는 **메시지 마지막 문단**이어야 한다(`-m "요약" -m "Role: …" -m "Change-Id: …"`처럼 나누면 앞 문단은 트레일러가 아니다 -- review29 G10; 명령은 `--trailer` 형식으로 쓴다).
3. **병합 커밋**(commit-msg에서 `MERGE_HEAD`가 있을 때): (가) 트레일러 `Role: doc`·`Change-Id: <id>` (나) 현재 worktree 브랜치 = `role/audit/<id>`, `HEAD` = `role/test/<id>` 끝, `MERGE_HEAD` = `role/code/<id>` 끝 (다) **staged 트리 = `MERGE_HEAD` 트리**(`git diff --cached --quiet MERGE_HEAD`) -- 병합 커밋이 code 끝(K)과 다른 내용을 들일 수 없다(review29 G9·Q-03). (라) **역할 밖 병합**(review31 N-01): 위 (나)에 해당하지 않는 병합은 (1) 부모가 정확히 둘(부모 셋 이상인 병합은 차단, review32 M-07) (2) **`HEAD`가 `gate/master`와 같거나 그 후손**(review32 M-01: 오래된 조상 위에서 `merge -s ours master`로 부모를 뒤집으면 첫 부모 비교를 통과하면서 트리 전체를 조상으로 되돌린다) (3) staged 트리와 `HEAD` 트리가 `overlaps_any` 경로 전부에서 같다 -- 셋 다일 때만 통과(트레일러 불필요 -- 다른 skill·RTL 작업의 병합. 둘째 부모는 오래된 조상에서 갈라져도 된다). 그 밖의 병합은 차단(review30 A19b: 조상에서 갈라진 문서 부모로 되돌리는 병합은 역할 경로를 첫 부모와 다르게 만든다). 병합 커밋에는 4의 경로 권한을 적용하지 않는다 -- 트리가 K와 같고 K까지의 커밋은 커밋마다 검사됐다(review30 C5: 적용하면 정상 병합이 `Role: doc`의 소스 변경으로 막힌다).
4. **경로 권한**: staged 경로마다 `allowed(트레일러 역할의 주체, 경로, change_id)`. 소스와 test 함께면 차단.
5. **조건 판정**(staged 판):
   * `승인 기록`(topology): HEAD→staged 변화 중 `.ai/approvals/**`를 뺀 경로의 blob 식 값을 `target`으로 가진 `target_kind: staged_diff` 승인 기록(`00-common` §8.2 v1.8 -- 아직 없는 커밋 id를 적지 않는다, review30 R-14)이 index나 HEAD 트리에 있어야 한다.
   * `status 전이만`(structure.json): `status`를 뺀 나머지가 HEAD 판과 같아야 한다.
   * **계획서 판정 표**: `plan_tables_hash`(§15.2)가 바뀌면 staged 판 해시의 `plan_tables` 승인 기록이 index나 HEAD 트리에 있어야 한다. staged 판을 못 읽으면 차단.
   * **`Role: user`**: 그 커밋이 바꾼 경로 중 `.ai/approvals/**`를 뺀 전부를 덮는 `target_kind: staged_diff` 승인 기록(`diff_base` = HEAD)이 index나 HEAD 트리에 있어야 한다(review29 Q-07). EL4는 같은 식을 (첫 부모, 그 커밋)으로 다시 계산한다. 승인 기록은 오케스트레이터가 쓰므로 사용자 확인은 커밋 이력으로 한다(N3.12.0).
6. 차단 메시지: 위반 경로·주체·판정 행·필요한 승인 기록의 `target` 값.

---

## 9. EL4 gate `pre-receive`

### 9.1 `pre-receive`와 `gate-runner.py`

원본은 작업 저장소 `tools/gates/gate/{pre-receive,gate-runner.py}`이고, gate 저장소에는 부트스트랩 ④(b)에서 사용자가 복사한다(§3.3이 매번 바이트 동일을 대조). `pre-receive`는 `exec "C:/Python314/python.exe" "<gate_path>/gate-runner.py"`.

`gate-runner.py`: 실행 전체를 `try/except → exit 1`로 감싸고(fail-closed), 모든 git 호출에 `GIT_NO_REPLACE_OBJECTS=1`.

1. 무결성 대조(§3.3의 gate 항목).
2. stdin `<old> <new> <ref>` 줄마다: `ref`가 `refs/heads/master`가 아니면 거부. 삭제·non-ff 거부(review29 G2~G4 실측).
3. `old` 판 게이트 코드를 §3.2 방식(`ls-tree`+`cat-file`)으로 임시 디렉터리에 풀고 `merge_gate.py receive --old <old> --new <new>`를 실행. push된 트리는 그 안에서 데이터로만 읽는다.
4. 통과하면 `gmid-accept-log`에 한 줄 쓰고 exit 0.

**기준 커밋(review29 Q-06·G1)**: gate는 사용자가 부트스트랩 ④(b)에서 **`pre-receive` 설치 전에** 현재 master를 push해 만든다. 그 커밋 id가 `gate_config.json`의 `baseline_commit`이고, `merge_gate.py`는 `baseline_commit`의 조상 커밋을 검사하지 않는다(트레일러 없는 과거 337커밋). 최초 push(`old`가 0)는 `pre-receive`가 있으면 거부한다.

### 9.2 `merge_gate.py receive` 판정 (실패는 모두 모아 출력하고 거부)

1. **old 계획서**를 파싱(실패면 판정하지 않고 거부).
2. **상태 기반 판정 표 검사**: `plan_tables_hash(old)` 대응 `plan_tables` 승인 기록이 `old` 트리에 있어야 한다(최초 기준 승인은 부트스트랩 ③).
3. **커밋 전수**(`git rev-list --reverse <old>..<new>`, `baseline_commit`의 조상 제외): **병합 아닌** 커밋마다 첫 부모 대비로 §8.2의 2·4·5를 다시 적용(역할 밖 경로만 바꾼 커밋은 통과). **병합 커밋은 4의 M이거나 역할 밖 병합(부모 정확히 둘, 첫 부모가 `old`와 같거나 그 후손(`git merge-base --is-ancestor <old> <병합^1>`), 병합 트리와 첫 부모 트리가 `overlaps_any` 경로 전부에서 같다 -- §8.2-3 (라), review32 M-01·M-07)일 때만 허용**하고 그 밖의 병합은 모두 거부한다(review30 A19b: 역할 커밋 없는 `Role: doc` 병합이 조상 트리로 되돌려 test·`gate_config.json`을 지운 실측 -- 역할 경로가 첫 부모와 달라 역할 밖 병합이 아니다). M에는 경로 권한을 적용하지 않는다(트리 = K, K까지 커밋마다 검사됨 -- review30 C5).
4. **변경 한 건 구조**(review29 Q-03·Q-04·Q-13, review30 R-01·R-07): 역할 커밋(`Role` ∈ {code, test, audit})이 없는 push는 3으로만 판정한다(병합 아닌 커밋은 트레일러와 경로로, 병합은 역할 밖 병합일 때만 -- review31 N-01). 역할 커밋이 있는 push에는 역할 밖 병합이 끼지 못한다. 역할 커밋이 있으면 그 `Change-Id`는 **정확히 하나**이고, `old` 트리에 `docs/02-design/specs/<id>.spec.md`가 있어야 한다. `evidence_type`은 spec card에서 읽는다. `old..new`의 커밋 집합이 아래 모양과 **정확히** 같아야 한다(다른 커밋이 끼면 거부):

   | `evidence_type` | 모양 | T, K |
   |---|---|---|
   | red-green | ① `old..M^1`은 첫 부모 사슬이고 전부 `Role: test`(1개 이상) ② `M^1..M^2`는 전부 `Role: code`(1개 이상, 병합 없음)이고 M^2는 M^1의 후손 ③ M: 부모 둘(M^1, M^2), `Role: doc`, 트리 = M^2 트리 ④ `new`는 부모가 M인 `Role: audit` 1개(판정 기록 추가) | T = M^1, K = M^2 |
   | equivalence | 같음, 단 ①의 `Role: test`가 0개면 M^1 = `old` | 같음 |
   | test-only | `old..new^`는 첫 부모 사슬이고 전부 `Role: test`(1개 이상), `new`는 `Role: audit` 1개, 병합 없음 | T = `new^`, K 없음 |

   ②가 code 쪽에 끼운 `Role: test` 커밋 T'(M^1의 후손이자 M^2의 조상, review30 A20)를 거부한다 -- 그것을 두면 병합본의 test가 auditor가 3에서 고정한 T가 아니게 된다.

5. **판정 기록**: audit 커밋 트리의 `.ai/verification/<id>.json`을 `00-common` §8.1 로더 규칙 1~10으로 읽고, `test_commit` = T, `code_commit` = K(test-only면 `null`), `evidence_type` = spec card 값, `base_commit`이 `old`이거나 그 조상.
6. **증거**: gate는 증거를 다시 실행하지 않는다(§3.2). 판정 기록의 `red.failure_hashes`·`equivalence.outputs_hash`는 auditor가 **격리 복제본**(§12-7)에서 잰 값이고, gate는 로더 규칙(형식·길이)만 판정한다. **이 항목은 형식 검사이지 증거의 증명이 아니다**(review30 R-13) -- 증거의 신뢰는 측정 주체가 작성자와 다르다는 것(N3.12.1)과 V1~V10이 격리 복제본에서 돈다는 것(§12-7)에 기댄다.
7. **V1 명령 형태**(형식 검사 -- 6과 같이 auditor가 적은 문자열을 보고 실제 실행을 증명하지 않는다, review34 M3-08): `auditor_run.commands`의 `V1: ` 원소를 `shlex.split`해 앞의 `NAME=값` 환경 대입(`PYTHONPATH`·`PYTHONPYCACHEPREFIX`)을 건너뛴 첫 토큰이 `$PY` 글자 그대로이거나 `gate_config.json`의 `python_path`와 같고(비교는 둘 다 `\`를 `/`로 바꾸고 `normcase` 뒤 -- review36 S3), 이어 `-P`, `-m`, `pytest`이며, `-c <값>`(값의 파일 이름이 `pytest_gate.ini`이고 그 디렉터리가 `gmid-gate-cache/<old>/` -- 두 토큰 형태)·`--rootdir=<값>`·`--confcutdir=<값>`(`=` 한 토큰 형태, 두 값이 같다)을 가지며 test 경로 인자는 정확히 하나 `<복제본 루트>/skills/analog-gmid-design/assets/tests`(절대 경로)다 -- pytest는 현재 디렉터리가 rootdir와 같을 때만 `testpaths`를 쓰므로(review36 실측: 복제본 밖에서 실행하면 실행 위치 전체를 수집), 수집 범위를 현재 디렉터리에 맡기지 않는다. `norecursedirs = tools`는 경로 인자와 무관하게 `tests/tools/`를 뺀다. auditor는 이 명령의 경로를 **슬래시 표기**로 적는다(`shlex`의 POSIX 규칙이 따옴표 없는 역슬래시를 지우므로 -- review35 M4-07). **엄격 집합**(`00-common` §9.3): 같은 Phase의 병합된 spec card `activated_ic_case` ∪ 이번 필드와 `auditor_run.commands`의 `V1: ` 원소(정확히 하나) 대조. **CC-3 병합 전 판정식**(review29 Q-19): `old` 트리의 `skills/analog-gmid-design/assets/tests/conftest.py`가 AST에서 `addoption("--gmid-phase", …)` 호출을 가지면 CC-3 병합 뒤다.
8. **auditor 판정**: `checks`에 FAIL 없음, N/A는 로더 규칙 10.
9. **승인이 필요한 변경**: V5 기준 약화 승인 기록(auditor가 `checks.V5`에 적은 diff 해시가 승인 기록 `target`과 같음), topology·structure·계획서 판정 표·`Role: user` 조건(§8.2-5, `staged_diff`는 (첫 부모, 그 커밋)으로 다시 계산).
10. **의존성**: `importlib.metadata.version("jsonschema")`와 `importlib.metadata.version("pytest")`가 `tools/gates/requirements.txt`의 고정 판과 같다(pytest 판이 바뀌면 `판정 환경` 행 후보 대조(공격 17)의 기준이 달라진다, review32 M-08).

### 9.3 판정 기록 로더·승인 기록 파서·red 플러그인·판정 표 읽기 (CC-1·CC-2)

* `load_verification_record`: `00-common` §8.1 로더 규칙 1~10, 규칙마다 함수 하나, 메시지에 규칙 번호.
* `parse_approval_header`: `00-common` §8.2(`target_kind` ∈ {`diff`, `decision`, `plan_tables`}). 대상은 이름이 `_`로 시작하지 않는 `.md`, 줄 끝 `\r?\n`.
* `red_failure_hash`와 pytest 플러그인: `00-common` §8.1(수집 단계 `pytest_exception_interact`의 `__cause__`, 신규 심볼 (모듈, 심볼) 쌍 -- §15).
* `read_plan_tables`·`plan_phase_tokens`: `00-common` §9.1·§9.2. 표 읽기 함수는 §4.1과 공유.
* 의존성 선언(U-38): `tools/gates/requirements.txt`에 `jsonschema==<부트스트랩 ① 시점 설치 판>`과 `pytest==<같은 시점 설치 판>`(`판정 환경` 행 후보 대조의 기준 판, 공격 17 -- review31 N-05)(WP-20 정책을 낮추지 않는다).

---

## 10. auditor 검사 도구 (N4.2)

판정은 JSON 한 줄로 표준출력, exit 0 PASS / 1 FAIL / 2 실행 오류(auditor는 FAIL로 적는다). 모두 **격리 복제본**(§12-7)에서 돈다.

| 도구 | 검사 | 알고리즘 |
|---|---|---|
| `mutate_changed.py`(V3) | 뮤테이션 | ① 대상 = diff가 닿은 `def` 중 `ast.dump`(docstring 제외) 해시가 base와 다른 것. 새 def는 본문 전체, 기존 def는 base와 문장 단위로 맞춘 바뀐 문장·감싸는 제어문·바꾸거나 지운 문장 자리 바로 뒤 문장·바뀌거나 지운 문장이 바꾸는 이름을 같은 블록 뒤쪽(반복문 본문이면 그 본문 전체)에서 읽는 문장·def 머리가 바뀌면 그 자기 필드(기본값·데코레이터 인자·주석)와 바뀐 매개변수를 읽는 문장, 그리고 `early_return`(정의: spec card `20260930-v3-changed-stmt-scope` 계약 1). 대상 밖 변이는 실행하지 않고 수와 id를 출력한다(판정 제외) ② 연산자: 비교 뒤집기, 산술 교체(`+↔-`, `*↔/`), 상수 변경(정수 ±1, 실수는 표기된 마지막 자릿수 한 단위 ±), 문장 삭제, 조기 `return`, `except` 본문 삭제 ③ 인벤토리 = 정적 호출 그래프(V7과 같은 그래프)에서 그 함수에 도달하는 test 함수(계획 N4.2 V3 v5.19) ④ 변이마다 `--head` 커밋의 격리 복제본(`git clone --no-hardlinks --no-local`, 이력 포함, origin 없음 -- §12-7과 같은 형태, 끝나면 지운다)에서 그 test만. 인벤토리의 변이 없는 기준 실행이 실패하면 그 변이를 생존으로 세지 않고 `ERROR`(exit 2, 실패 인벤토리 출력) ⑤ 살아남은 변이가 있으면 FAIL. 변이 id = `<모듈>:<함수 qualname>:<연산자>:<AST 노드 경로>`. 등가 변이 면제는 `target_kind: decision`, `target` 원소 = `<변이 id>@<묶기 해시>`(승인할 때 head def 노드 원본 -- docstring 포함 -- 의 `ast.dump` sha256, 정의: spec card `20260930-v3-exempt-binding`)인 승인 기록 -- head의 그 def 묶기 해시가 같을 때만 적용. 해시가 없거나 다르거나 형식이 틀린 원소는 적용하지 않고 출력 `exempt_ignored`에 싣는다. 자체 AST 변이기(DEC-39) |
| `test_lint.py`(V4) | 자기참조 | 계획 N4.2 V4 (1)~(5). **(2) 확실한 복사 검출**(사용자 결정 (c), review30 R-05·R-06): ① assert 비교(`abs(a - b) <`·`<= tol`, 상대 오차 `abs((a - b) / c) <`·`<= tol`, `==`(어느 쪽이든 `pytest.approx`), `math.isclose`(어느 순서든))에서 피검 함수(interface card 심볼) 호출이 든 쪽과 기대식 X를 가른다. 양쪽 모두 test 함수의 지역 대입(`Assign`·`AnnAssign`)을 **그 assert 시점의 값으로**(본문 순서대로) 인라인한다. 판정 문장은 **본문 전체를 재귀로** 찾는다(`for`·`while`·`with`·`if`·`try`·`try … except*`·`match` 안 포함. 피검 호출이나 피검 불투명 이름을 담은 값·반복 대상에서 나온 이름과, 그런 값을 첨자·속성으로 받거나(`out[g] = f(g)`, `res.v = f(…)`) 메서드 인자로 넘긴(`rs.append(f(…))`) 밑 이름은 **어디서 대입되든 피검 불투명 이름**(review34 M3-04), 중첩 함수·클래스·lambda·comprehension의 지역 이름은 바깥 이름을 가리지 않는다(M3-05), 그 밖에 루프 변수와 블록 안에서 바뀐 이름은 불투명 이름 -- review33 M2-03. test 안 중첩 함수·클래스와 다루지 않는 복합 문장 안의 판정 문장은 `UNJUDGED`. test 함수는 `def`·`async def` 모두)와 호출 이름이 `assert`로 시작하는 호출문(`np.testing.assert_allclose`, `self.assertAlmostEqual` 등 -- 앞 두 인자가 비교 쌍), test 쪽 누적 대입(`AugAssign`)도 인라인한다(review32 M-04). 출력은 판정 문장마다 넷 중 하나: `FAIL`·`PASS`·`UNJUDGED`(피검 호출이나 피검 불투명 이름이 걸렸는데 판정하지 못함 -- 비교 쌍을 못 만듦, `**kw`처럼 인자를 결합하지 못함, 피검 호출이 식 안에 있음, 튜플 풀기·블록·루프 대상으로 받은 피검 결과, 중첩 함수 안)·`NO-SUBJECT`(피검 호출도 피검 불투명 이름도 없는 판정 문장, V4 (2) 대상 아님 -- 쌍을 못 만든 것 포함, review33 M2-04). 게이트 구현에서 도구 자신의 예외는 exit 2(§10 머리, auditor는 FAIL로 적는다) ② 피검 함수의 return마다 그 경로의 지역 대입을 인라인하고 test의 호출 인자를 매개변수에 결합(기본값 포함)해 E_i를 만든다. 분기 안에서 바뀐 이름·루프·튜플 대입은 불투명 이름으로 둔다 ③ 같은 모듈 함수 호출은 양쪽 모두 재귀 인라인하되 **return이 하나인 함수만** -- return이 여럿인 함수의 호출은 불투명 호출로 둔다(여럿을 조합으로 펼치면 변형 수가 곱으로 늘어 실제 엔진 함수에서 끝나지 않았다, F8). 식이 너무 깊어 펼치지 못하면(`RecursionError`) `UNJUDGED` ④ 정규화: 덧셈·뺄셈·곱셈·나눗셈 평탄화와 피연산자 정렬, 정수 거듭제곱(음수 지수 포함) → 곱, 항등원(`+0`·`*1`·`/1`) 제거, **부호는 밖으로**(음수 숫자 인자와 단항 마이너스를 곱 전체의 부호로 모은다), 숫자는 정확한 유리수(`Fraction(repr(float))`), 곱의 숫자 인자는 **곱하지 않고 정렬한 다중집합**으로 두고 나눗셈의 숫자 인자만 역수로(`x/2` = `x*0.5`, 순서 무관 -- review32 M-03: 계수를 부동소수로 곱하면 판정이 곱하는 순서와 반올림에 달렸다), 합 위의 단항 마이너스는 항마다 나눈다(`-(b + c)` = `-b - c`). **숫자끼리 곱하거나 더해 접지 않는다**(접으면 재서술 `2e-3*50e3`가 리터럴과 구별되지 않고, 올바른 리터럴 기대값이 전부 FAIL) ⑤ **입력을 그대로 돌려주지 않는** E_i 중 정규화한 X와 같은 것이 있으면 FAIL -- 정규형이 잎 하나(매개변수·상수)이거나 **그 return 식에 나오는 매개변수에 결합된 인자 식 하나의 정규형과 같은** E_i는 비교하지 않는다(쓰이지 않는 인자로 제외를 맞추지 못한다, review33 M2-06. 피검 안 중첩 함수·클래스·lambda의 return은 바깥 함수의 return 변형에 넣지 않는다)(review31 N-03, review32 M-02: `clamp(5, 0, 10) == 5`, `area(0) == 0.0`, `vin = 0.5 * vdd`인 `clamp(vin, 0.0, vdd) == approx(vin)`, 단위 이득 같은 명세 리터럴·무발동 값이 FAIL이 되던 거짓 양성. 그런 경로의 복사는 V3가 맡는다). **FAIL은 확실한 복사이고 PASS는 독립의 증거가 아니다.** 알려진 놓침: F1 손으로 계산한 리터럴·계수(`135.0`, 명세 계수 `6.0*y` 대 `x*k1*k2`), F2 분배·약분 등 대수 변형, F3 모듈 밖 함수·자료구조(`sum([...])`, 사전 조회, 튜플 반환 풀기)를 거친 식, F4 입력을 그대로 돌려주는 return 경로의 복사, F5 `UNJUDGED` assert, F6 블록(`if`·`with`·`try`·루프) 안에서 만든 기대식(블록 밖에서는 불투명 이름이 된다, review34 M3-05), F7 누적·주석 대입·`setattr`·walrus로 받은 피검 결과와 `nonlocal`로 바뀐 이름(review35 M4-05·M4-06 -- 위협 범위 밖 검출기 한계, §13.5), F8 return이 여럿인 같은 모듈 보조 함수를 거친 복사. 피검이 중첩 def·class를 호출해 돌려주는 경로는 불투명 호출로 남아 비교되지 않는다(예외 없음, review35 M4-03) -- auditor의 oracle 대조(`checks.V4.basis`의 `oracle 대조:` 줄, `UNJUDGED` assert 전부 포함, `00-common` §8.1 로더 규칙 10)와 V3(뮤테이션)가 맡는다. **실측**(`docs/03-analysis/gain-budget-gmid-sizing-function-audit/v4_rule_probe/v4.py` -- 입력은 `git show e329283`의 실제 `estimate_area_budget` 본문과 §13.3 규칙으로 변환한 실제 self-test 섹션, 결과 `v4.out.txt`): 케이스 67개 모두 **첫 판정 문장**의 출력이 기대와 같다(probe가 스스로 대조해 `기대 불일치 0개`를 적는다. 둘째 이후 판정 문장은 출력만 기록하고 대조하지 않는다 -- review34 M3-07). FAIL 34: 실제 e329283 첫 assert와 그 변형 6(교환 재배열, `1.0*` 감싸기, `<=`, 상대 오차, `approx` 왼쪽, 주석 달린 대입), `vov*vov` 대 `0.2**2`와 그 반대, `gm*ro` 대 `2e-3*50e3`(재서술 -- 계획 N4.2 V4 (2) 목적), 병렬 저항 같은 식, KCL 합, 같은 모듈 보조 함수 경유, 단항 마이너스 두 위치, 합 위 단항 마이너스, `a - b*c` 대 `-b*c + a`, `x/2` 대 `x*0.5`(이름·숫자 모두), `1/x` 대 `x**-1`, 교환 재배열 `a*b*c*x`, 키워드 전용 기본값, assert 뒤 재대입, test 쪽 누적 대입, `for`·`with`·`match`·`except*` 안의 재서술, `np.testing.assert_allclose` 재서술, inf 리터럴(예외 없음), `async def` test, 쓰지 않는 인자로 통과 경로를 흉내 낸 기대식, comprehension·중첩 `def`의 지역 이름이 바깥 기대 이름을 가리지 않음; PASS 11: `gm*ro` 대 리터럴 `100.0`, 병렬 저항 대 컨덕턴스 합(다른 폐형식), `clamp` 통과·하한 리터럴, `area(0) == 0.0`, 단위 이득, 인자가 식인 `clamp` 통과 경로·단위 이득·항등 함수, 피검 안 중첩 함수의 return(바깥 return에 섞지 않음), 중첩 클래스를 돌려주는 경로(예외 없음); known_limit 8(F1 접은 리터럴·명세 계수 둘, F2 α 상쇄 풀어 쓰기, F3 `sum()`·중첩 함수 경유(`return inner(x)`), F6 블록 안에서 만든 기대식 -- 이상 PASS, F3 튜플 풀기 -- `UNJUDGED`); `UNJUDGED` 12(`**kw`, 식 안의 피검 호출, 표 구동 `zip` 루프, 피검 결과 리스트를 도는 루프, `if`·`with`·`try` 블록 안에서 받은 결과, test 안 중첩 함수, 쌍 없는 피검 assert, 첨자 `out[g] = f(g)`·속성·`append`로 받은 결과); `NO-SUBJECT` 2(피검 없는 비교, 쌍 없는 피검 없는 assert). **누적 회귀 코퍼스**(`v4_rule_probe/regression_cases.json`): 검증자들(review32~35)이 만든 V4 케이스 94개를 모아 3bf0100 판의 출력(review36에서 회귀 0 확인)으로 고정했고, `v4.py`가 실행마다 전부 다시 돌려 `회귀 코퍼스 94개, 출력 변화 0개`를 적는다. 출력을 일부러 바꾼 시험에서 변화 1개를 잡는 것을 확인했다(WP-02). 출력이 바뀌는 수정은 그 변경이 의도인지 history에 적고 다시 고정한다(WP-22). **실제 엔진 전수**(`v4_rule_probe/sweep_engine.py` → `sweep_engine.out.txt`, review35 M4-03 뒤 내 케이스 밖 재측정): `skills/analog-gmid-design/assets/*.py`의 최상위 함수 344개를 모두 피검으로 넣어 예외 0, 전체 수 초. 이 확인에서 두 결함이 먼저 나와 고쳤다 -- 깊은 식의 `RecursionError`(→ `UNJUDGED`), return이 여럿인 같은 모듈 함수를 조합으로 펼쳐 한 함수에서 끝나지 않던 것(→ ③을 return이 하나인 함수만 인라인하도록). R-05의 네 조합: test 쪽을 인라인하지 않으면 실제값이 변수라 피검 호출을 찾지 못하고, 피검 쪽을 인라인하지 않으면 PASS -- 둘 다 인라인할 때만 FAIL. e329283의 두 번째 assert(`_a1d_demo / 0.731` 대 사전 조회를 거친 첫 return)는 F3로 PASS다. 부트스트랩 ①에서 probe의 규칙 함수를 `test_lint.py`로 옮기고 probe는 지운다(WP-01) |
| `weakening_diff.py`(V5) | 기준 약화 | 입력: test 분류 파일 diff, TS1 전에는 소스의 `if __name__ == "__main__":` 블록 diff. **test 분류의 `.py` 아닌 파일**(기준선 `.log` 등)과 **`conftest.py`**(test-author 경로 안의 `assets/tests/conftest.py` -- pytest hook으로 수집·판정을 바꿀 수 있어 8패턴으로 보이지 않는다, review30 J1)가 바뀌면 무조건 승인 기록 요구(review29 Q-15). 그 밖의 `.py`는 아래 표의 판정식 |
| `source_lint.py`(V6) | 소스 | 계획 N4.2 V6. '새' = base 대비 AST 차이 |
| `reachability.py`(V7) | 배선 | 새 `def`가 `gate_config.json`의 `reachability_roots`에서 정적 호출 그래프(문자열 레지스트리 포함)로 도달하는지 |
| `interface_card.py` | interface card | §11.1 |
| `import_layering.py` | import 계층 | MOD 번호(N3.10) 그래프에서 큰 번호로의 import·순환 FAIL |

**V5 판정식**(N0.4 '기준 약화' 8패턴 ↔ AST, test 함수 단위, 이름 목록 없이 구조로):

| N0.4 패턴 | 판정식 |
|---|---|
| assert 삭제 | 함수 안 `Assert`·`pytest.raises`·`pytest.approx` 수 감소, 또는 test 함수 삭제 |
| 비교 완화 | `Compare` 연산자 변화, `approx`의 `rel`·`abs` 인자 추가·변경 |
| 허용오차 확대 | 리터럴 변경에 포함(아래) |
| skip/xfail 추가 | `pytest.mark.skip*`·`xfail` 표식이나 `pytest.skip`·`pytest.xfail` 호출 추가 |
| 기대값 리터럴 변경 | 숫자·문자열 `Constant` 값 변경 전부 |
| 픽스처 입력 리터럴 변경 | 같음(픽스처 함수 포함) |
| 격자 확대 | 같음 |
| assert를 조건문·try 아래로 이동 | `Assert`의 조상에 새 `If`·`Try` |

거부 증명: V3 → `redteam/v3_survivor`, V4 → 공격 6·7·23(판정 경계 -- known_limit 케이스는 PASS 기대로 한계를 고정), 사례 e329283·e5fbf92·3250baa, V5 → 공격 8·17(`tests/conftest.py`), 사례 2e1944a, V6 → 공격 9, 사례 1b9b4ea, V7 → `redteam/v7_unwired`.

---

## 11. interface card·spec card·dispute

### 11.1 interface card (`tools/gates/interface_card.py <spec card>`)

출력 `docs/02-design/specs/<id>.interface.md`: '관찰 가능한 계약'에 나온 기존 함수의 AST 시그니처 + docstring 첫 단락, '신규 시그니처' 절. 신규 심볼은 (모듈, 심볼) 쌍 표. 본문 코드는 넣지 않는다(DEC-38).

### 11.2 spec card 양식 (`docs/02-design/specs/_TEMPLATE.spec.md`)

게이트가 읽는 필드는 머리 블록(`key: value`, 모르는 키 거부), 나머지는 본문 절. 필드 목록의 정본은 N3.12.3.

```
---
id: YYYYMMDD-<slug>
phase: <계획서 N6.1에서 읽은 Phase 순서의 원소>
evidence_type: red-green | equivalence | test-only
gate_change: yes | no
activated_ic_case: <IC:case>                             # 반복
activated_ic_case_rename: <옛 IC:case> -> <새 IC:case>   # 반복
noop_activation_id: <ID>                                 # 반복
approval: <승인 기록 id>                                  # 반복
---
## 의도
## 관찰 가능한 계약
## 신규 시그니처
## 판정 유형 근거
## oracle 종류와 출처
## 거부해야 할 입력
## library 회로 적용 여부
## 무동작 판정 입력(무발동 값)
## 재현할 수치
## 결정 필요 항목
## dispute 기록          # dispute가 있었을 때만: 원문 인용 + blob id(§12 재시도)
```

### 11.3 dispute 양식 (`docs/02-design/disputes/_TEMPLATE.md`)

머리 블록 `id`, `spec_card`, `test_id`(반복). 본문 `## 문제의 test`, `## 근거(oracle 또는 사용자 원문)`, `## 요청`.

---

## 12. 변경 한 건의 명령 시퀀스 (N3.12.3)

`W=<작업 저장소의 형제 wt 디렉터리의 절대 경로>`. 트레일러는 `git commit`에서는 `--trailer "Role: …" --trailer "Change-Id: <id>"`, `git merge`에서는 §12-6 형태. **한 번에 변경 하나**만 진행한다(역할 브랜치가 있는 동안 문서 커밋의 gate push는 EL1이 거부).

| 순서 | 주체 | 명령 |
|---|---|---|
| 0 | 오케스트레이터 | spec card·interface card(`$PY <게이트 코드>/interface_card.py …`)를 작업 저장소 `master`에 커밋(`--trailer "Role: doc"`) → `git push gate master:master` → `git fetch gate` → `git merge --ff-only gate/master`(review29 Q-08·W1: interface card를 worktree 생성 **전에** 반영) |
| 1 | 오케스트레이터 | `git worktree add $W/<id>-test -b role/test/<id> gate/master` |
| 2 | test-author | `$W/<id>-test` 절대 경로로 test 작성, `git -C $W/<id>-test commit --trailer "Role: test" --trailer "Change-Id: <id>" -m "<요약>"` |
| 3 | 오케스트레이터 → auditor | `git worktree add $W/<id>-audit -b role/audit/<id> role/test/<id>` → auditor가 freeze(T 해시)와 base 대비 red/equivalence 확인을 **격리 복제본**(아래 7)에서 하고 결과를 `$W/<id>-audit/.ai/verification/<id>/base_check.json`에 쓴다(커밋은 7에서 -- subagent 호출 사이에는 기억이 없다, review30 R-19) |
| 4 | 오케스트레이터 | `git worktree add $W/<id>-code -b role/code/<id> role/test/<id>` |
| 5 | code-author | `$W/<id>-code`에서 구현, `--trailer "Role: code" --trailer "Change-Id: <id>"` 커밋. test가 틀렸다고 보면 dispute(`$W/<id>-code/docs/02-design/disputes/<id>.md`)를 쓰고 같은 트레일러로 커밋한 뒤 멈춘다 |
| 6 | 오케스트레이터 | `git -C $W/<id>-audit merge --no-ff role/code/<id> -m "merge <id>" -m "<두 줄: Role: doc / Change-Id: <id>>"` -- 두 번째 `-m`은 한 인자 안에 두 줄이다. **실측(2026-09-18, git 2.52)**: `git merge`에는 `--trailer`가 없고(`unknown option`), 두 줄을 한 `-m`에 넣으면 `git interpret-trailers --parse`가 둘 다 읽는다. 병합 트리 = code 끝 트리 |
| 7 | auditor | **격리 복제본**: `git clone --no-hardlinks --no-local <audit worktree 경로> <TEMP>/<id>-iso` → `git -C <TEMP>/<id>-iso remote remove origin`(복제본의 `origin`이 작업 저장소를 가리킨다 -- review30 R-09 실측) 후 그 안에서 V1~V10과 증거 측정(red 재현·equivalence 명령). 게이트 코드(red 수집 플러그인 포함)는 복제본의 것이 아니라 base 판(§4.4 캐시)을 `PYTHONPATH` 맨 앞에 두고 `$PY -P`로 쓴다(`-P`가 없으면 복제본 루트가 캐시보다 앞선다, review33 M2-01). pytest 실행은 `-c <캐시>/pytest_gate.ini --rootdir=<복제본 루트> --confcutdir=<복제본 루트>`로 설정 파일과 conftest 탐색을 복제본 안으로 가두고(review34 M3-02: 복제본 부모 `%TEMP%`의 `pytest.ini`가 설정이 되어 종료 1 → 0), `PYTHONPYCACHEPREFIX=<빈 임시 디렉터리>`로 커밋된 `__pycache__`를 읽지 않는다(review34 M3-01 (3)). `auditor_run.commands`에 `V1: …`와 격리 명령을 적는다. 판정 기록을 `$W/<id>-audit/.ai/verification/<id>.json`에 쓰고 `--trailer "Role: audit" --trailer "Change-Id: <id>"` 커밋 |
| 8 | 오케스트레이터 | `git -C $W/<id>-audit push gate role/audit/<id>:master`(gate `pre-receive`가 §9.2로 판정) → `git fetch gate` → 메인 worktree에서 `git merge --ff-only gate/master` |
| 정리 | 오케스트레이터 | `git worktree remove [--force] $W/<id>-{test,code,audit}`, `git branch -D role/{test,code,audit}/<id>`. EL3에 막혀 병합 상태가 남으면 `git -C $W/<id>-audit merge --abort`. `--force`는 이 세 경로에만(§12-3 미커밋 기록·중단된 병합이 남은 재시도 정리, ⑤ 재생 D-3) |
| 재시도 | 오케스트레이터 | auditor FAIL·dispute·push 거부 뒤에는 정리 형태로 세 worktree·브랜치를 지우고 같은 id로 1부터 다시 한다(거부된 push는 gate에 흔적이 없다). 부분 되돌리기(`reset`·`rebase`)는 쓰지 않는다. **dispute가 있으면 정리 전에**(review30 R-16: dispute는 code worktree에만 있어 정리가 지운다) 오케스트레이터가 그 파일을 읽어 메인 worktree의 spec card 개정에 `## dispute 기록` 절(원문 인용 + blob id)로 남겨 커밋하고, 사용자 결정은 `target_kind: decision` 승인 기록으로 받는다. 이 커밋 전에는 EL1이 code worktree 정리를 거부한다(§6.2). spec card 개정의 gate push는 정리 뒤에 한다(진행 중 push 거부) |
| V5 승인 운반 | 오케스트레이터 | test 내용이 정해진 뒤 받는 V5(기준 약화) 승인은 병합 판정이 head 트리에서 찾으므로 1차 시도에서 2차 시도로 운반한다(2026-09-22 `10-test-separation` R1, U-42): (1) 1차 시도 순서 1~3, auditor가 `weakening_diff.py` 출력을 `base_check.json`에 남기고 V5 FAIL로 멈춘다 (2) 정리 **전에** 발견 경로마다 `git -C $W/<id>-test cat-file blob <T>:<path> > docs/03-analysis/<feature>-<design>/v5-carry/<id>/<blob id>.blob`(파일 이름은 blob id -- 판정 환경 이름 회피)와 대응표 `v5-carry/<id>/paths.tsv`(`<path>` 탭 `<blob id>`), 사용자 승인 뒤 승인 기록(`diff`, `diff_base` = base, `diff_head` = T, `diff_path` = 발견 경로, `target` = diff 해시) -- 정리 뒤 `Role: doc` 커밋·gate push (3) 2차 시도에서 test-author가 `paths.tsv`대로 `.blob`을 `cp`로 원래 경로에 두어 같은 blob을 만든다(diff 해시는 blob id라 같다, `00-common` §8.2) (4) 그 card 병합 뒤 운반 디렉터리 삭제(`Role: doc`) |

---

## 13. 부트스트랩과 거부 증명 (N3.12.6, N4.3)

### 13.1 부트스트랩 ①~⑤

| 단계 | 할 일 | 산출 |
|---|---|---|
| ① | **작성 agent**(오케스트레이터가 맡긴다)가 §3~§11의 코드, `gate_config.json`(`gate_path`, `workspace_path`, `python_path`(§9.2-7), `reachability_roots`, `audit_tail_lines`는 사용자가 정할 자리, `bootstrapped`는 아직 없음), `requirements.txt`, `pytest_gate.ini`(판정 실행의 유일한 pytest 설정 -- `[pytest]` 절에 `testpaths = skills/analog-gmid-design/assets/tests`, `norecursedirs = tools`: test-author 경로 밖과 code-author의 `tests/tools/`는 test로 수집하지 않는다, review35 M4-01), `tools/gates/gate/*`, 양식, agent 정의 3개, `hooks/role_*.json`을 쓴다. **`redteam/` 데이터(§13.2·§13.3)는 검증 agent가** 이 문서만 보고(작성본을 보기 전에) 쓰고, 작성본이 나온 뒤 `--mode direct`로 재생해 결과를 보고한다. 오케스트레이터는 결과를 N3.12.0으로 분류해 범위 안 결함만 작성 agent에게 수정 지시하고(직접 고치지 않는다), 종료 조건(공격·사례 전부 기대대로, 정상 흐름 오거부 0, 범위 안 S1 0, 수정 지시가 만든 회귀 0)에서 멈춘다(WP-22). `.gitignore`에 `library/*.search_archive/`, `runs/`(사용자 승인). 커밋(`Role: doc`) | 커밋 |
| ② | hook 입력 실측 -- 했다(`role_hook_input_probe.md`) | -- |
| ③ | 공격 재생(§13.2 `--mode direct`: 게이트 함수를 직접 불러)과 사례 5건 재생을 실행해 로그를 사용자에게 제시. 사용자 확인 뒤 승인 기록 두 개: 부트스트랩 승인(`diff`, ① 산출 전부) + 최초 판정 표 승인(`plan_tables`) | 거부 로그, 승인 기록 |
| ④ | (a) `.githooks/{pre-commit,commit-msg,pre-merge-commit}` 갱신 커밋(사용자 경로 -- 승인 기록과 함께 한 번) (b) **사용자가**: `git init --bare <gate_path>` → `<gate_path>/hooks/*.sample` 삭제(review30 B1: 남으면 행 4가 첫 판정 push를 거부) → 작업 저장소에 `git remote add gate <gate_path 절대 경로>` → `git push gate master:master`(`pre-receive` 없음 -- 이 커밋이 `baseline_commit`) → `<gate_path>/gmid-accept-log`에 첫 줄 `<baseline_commit> <baseline_commit> <시각>`(§3.3 행 3) → `tools/gates/gate/*`를 gate에 복사(`hooks/pre-receive`, `gate-runner.py`) (c) `gate_config.json`에 `baseline_commit`과 `"bootstrapped": true`를 적은 문서 커밋을 gate로 push(이제 `pre-receive`가 판정한다). **실행 순서는 (d) → (c)다**(2026-09-21 ④ 실행에서 확인): §3.3 행 6은 표지가 있으면 `.claude/hooks`가 이미 있기를 요구하고, 무결성 대조는 표지를 gate `master`뿐 아니라 작업 저장소 HEAD의 `gate_config.json`에서도 읽는다. 그래서 (d) 전에 표지 커밋을 만들면 그 즉시 행 6이 실패해 `integrity-failed` 표지가 생기고 모든 게이트가 막힌다(실측: 표지 커밋 뒤 첫 gate push가 행 6으로 거부, (d) 설치 뒤 `--scope session` 전부 일치로 표지 해제, 같은 push 통과) (d) **gmid agent 3개(`agents/gmid-*.md`)를 `.claude/agents/`로, 역할 hook 4개(`hooks/role_*.py`)를 `.claude/hooks/`로 직접 복사하고 `.claude/settings.json`에 역할 hook 네 항목만 등록한다**(2026-09-21 사용자 결정, R-17). `install.py --only agents|hooks --project .`는 쓰지 않는다 -- 전역(`~/.claude`)에 이미 있는 verilog agent 10개와 전역 hook 2개까지 프로젝트에 복사해, hook이 두 번 돌고 프로젝트 사본이 전역 agent를 가린다(실측 2026-09-21). 전역 설정은 건드리지 않는다. 옆 `.json`으로 event·matcher가 한 번에 정해지게 하고, 등록 뒤 `.claude/settings.json`을 대조해 다르면 **사용자가 고친다**(hook 등록 뒤에는 EL1이 `.claude/**` 쓰기를 거부한다, review29 Q-17). `--only hooks`가 `hooks/*.py` 전부를 프로젝트 설정에 등록하는 것을 허용할지 ④ 전에 사용자 확인 | 설치 로그, 대조 결과 |
| ⑤ | 설치 상태에서 **실제 도구 호출과 실제 git 명령으로** §13.2 `--mode installed` 목록을 재생, §12 전 과정 한 번(§12-6의 실제 병합 명령과 세 역할의 SubagentStop 포함, 오거부 0), `gmid-*` agent의 `agent_type` 값 확인 | 설치 후 로그 |

### 13.2 공격 시나리오 (N4.3 + 이 문서가 더한 것)

`tools/gates/redteam/attacks/<번호>-<이름>/`에 `setup.sh`, `run.sh`, `expect.json`(`{"layer", "exit", "message_contains", "modes"}`). 실행기 `run_all.py --mode direct|installed`가 결과를 `redteam/logs/<시각>.jsonl`에 케이스마다 append(WP-11). `modes`가 그 케이스를 어느 방식으로 돌리는지 정한다(review29 Q-27).

| # | 공격 | 기대 | modes |
|---|---|---|---|
| 1 | code-author가 tests 경로 `Write` | EL1 exit 2 | direct, installed |
| 1b | code-author의 자기 id / 남의 id dispute | 허용 / EL1 거부 | direct, installed |
| 2 | code-author가 Bash로 tests 파일 생성 | EL2 exit 2 | direct, installed |
| 3 | 한 커밋에 소스+tests | EL3 차단, EL4 거부 | direct, installed |
| 4 | `git commit --no-verify` | EL1 exit 2 | direct, installed |
| 5 | `commit-tree`로 만든 커밋(트레일러 없음 / `Role: code`가 `.ai/approvals/x.md` 추가) push | EL4 거부 | direct, installed |
| 6~9 | V4 (1)·(3), V5, V6 | 각 검사 FAIL | direct |
| 10 | 메인 세션 엔진 소스 `Edit` / PowerShell `Set-Content` / `general-purpose` agent 엔진 소스 `Edit` | EL1 exit 2 | direct, installed |
| 10b | 메인 세션이 `$TEMP`·다른 skill 디렉터리 쓰기 / 트레일러 없는 역할 밖 커밋과 역할 밖 병합의 gate push(review31 N-01) -- 역할 밖 = `판정 트리` 밖 | 통과(오거부 0). 단 `판정 환경` 행의 이름(`conftest.py`·`pyproject.toml` 등)은 저장소 어디서나 사용자만 쓴다 -- 다른 skill에서도 통과가 아니다(review31 N-12) | direct, installed |
| 10c | 게이트 코드 import 실패(캐시 파일 훼손) / 캐시를 읽기·실행하는 §12-0·§12-7 명령(허용) / 캐시로 리다이렉트·`cp`(거부)(review31 N-07) | 캐시 대조가 다시 풀거나 EL1 exit 2 / 허용 / EL1 exit 2 | direct, installed |
| 11 | RTL agent가 RTL 파일 `Edit` | hook 출력 없음, exit 0 | installed |
| 15 | 판정 기록·승인 기록 형식 위반(케이스 `attacks/15-records/cases/*.json`, 각 `expect`) | EL4 로더 거부 / 올바른 기록 3종 통과 | direct |
| 16 | (i) 승인 없는 판정 표·쓰기 경로표 변경 (a) 직접 커밋 (b) push (ii) 깨진 표 (a)(b) (iii) 흐름 밖에서 깨진 old | (a) EL3 차단 (b) EL4 거부 (iii) EL4 판정 거부. 오거부 0: 승인 있는 개정, 표 값이 안 바뀌는 문장 수정 | direct, installed |
| 17 | 판정 환경 조작(review29 C1·A1, review30 J1): code-author가 `assets/conftest.py`로 실패를 통과로 / 루트 `conftest.py` / `skills/conftest.py` / `skills/analog-gmid-design/pytest.ini`(`addopts = -k …`) / `assets/tests/tools/conftest.py` / `sitecustomize.py`·`*.pth` / `.gitattributes`에 `export-ignore` / test-author가 `assets/tests/pytest.ini` 추가 / test-author가 `assets/tests/conftest.py` 변경 | 앞 여덟: EL1 거부(`판정 환경` 행 우선), 트레일러 없는 커밋으로도 EL3 차단·EL4 거부. 마지막: V5 FAIL(승인 기록 없음). 더해 `pytest.toml`·`.pytest.toml`·`.pytest.ini`(review31 N-05, pytest 9.0.2 실측 `1 deselected`)와 **후보 대조**: `requirements.txt`에 고정한 pytest 판의 `_pytest/config/findpaths.py` `locate_config` 안 `config_names` 리스트의 원소(docstring 등 다른 문자열 상수는 넣지 않는다, review32 M-08)가 모두 `판정 환경` 행의 파일 이름에 있어야 한다(실행 중인 pytest 판이 고정 판과 같아야 하는 것은 §9.2-10). 재생 데이터는 이 이름의 파일을 저장소에 둘 수 없으므로(판정 환경 우선) 실행 중 임시 저장소에 만든다(review31 N-12). 더해 (review33) 대소문자 변형 `Pytest.ini`(`--deselect <실패 test>`)·`PYTEST.INI`·`Setup.cfg`(EL1 거부·EL3 차단·EL4 거부 -- casefold 대조), casefold 충돌 경로 `Skills/…`(EL3·EL4 거부), 복제본 루트의 `merge_gate.py`·`pytest.py`(`$PY -P`에서 캐시 판이 쓰임을 로그로 보인다, V1 명령에 `-P`가 없으면 EL4 거부). 더해 (review34) `assets/numpy/__init__.py`·`assets/eng/__init__.py`(판정 트리 기본 거부 -- EL1 거부·EL3 차단·EL4 거부), 트레일러 없이 `git add -f`로 넣은 `.pyc`(`판정 환경` -- 같음, 그리고 격리 실행의 `PYTHONPYCACHEPREFIX`로 읽히지 않음을 로그로), `workspaces/<이름>.py`(`판정 환경`), 복제본 부모 디렉터리의 `pytest.ini`·`conftest.py`(`-c`·`--confcutdir`로 읽히지 않음을 로그로) | direct, installed |
| 18 | test-author가 `Read`·`Grep`·`Glob`로 소스 열람(메인·code worktree) | EL1 exit 2 | installed |
| 19 | 흐름 밖 병합: (a) `merge --no-commit` 뒤 내용 추가 (b) 역할 커밋 없는 `Role: doc` 병합(review29 G9) (c) 조상에서 갈라진 문서 커밋을 둘째 부모로 둔 병합 -- test 삭제·엔진 되돌림·`gate_config.json` 삭제(review30 A19b) (d) §12-6 정상 병합 (e) 역할 밖 병합(두 부모가 역할 밖 경로만 바꿈, 오래된 조상에서 갈라진 RTL 브랜치 포함) (f) 부모를 뒤집은 되돌림 병합: 조상 위에서 `merge --no-ff -s ours master` 뒤 `--ff-only`(새 커밋은 병합 하나, review32 M-01) (g) 부모 셋 이상인 역할 밖 병합(M-07) | (a)~(c)(f)(g) EL3 차단(commit-msg), EL4 거부 / (d)(e) 통과(오거부 0) | direct, installed |
| 20 | 트레일러·역할 흉내: (a) code-author가 `Role: test`·남의 `Change-Id` 커밋 (b) 오케스트레이터가 역할 worktree에서 `Role: code` 커밋 (c) 한 push에 id 둘 (d) code 쪽에 `Role: test` 커밋 T' 끼우기(review30 A20) (e) 세 역할의 정상 종료 -- auditor는 red-green·equivalence·test-only 각각(review31 N-02) | (a)(b) EL1 거부, EL2(SubagentStop) 거부 / (a)~(d) EL4 거부 / (e) 통과(오거부 0) | direct, installed |
| 21 | 원격 설정 조작 뒤 `git push gate`: (a) `git config remote.gate.receivepack …`(review29 G8) (b) `.git/config` 직접 편집 (c) global 설정·`include.path` 파일·`config.worktree`에 같은 키(review30 I2~I4) | (a) EL1이 `git config` 쓰기 거부 / (b)(c) EL1 push 직전·EL3의 행 2 대조 실패 → 거부 | installed |
| 22 | gate 훼손: (a) gate `pre-receive` 덮어쓰기(review29 G6·G7 형태) (b) gate `master` 직접 이동(review30 I6a) (c) 이동 뒤 accept-log에 줄 덧붙이기(I6b) (d) accept-log 비우기(I6c) (e) gate `core.hooksPath`(I8) (f) (c) 뒤 캐시·보조 파일에 그 구간을 적어 두기(review31 N-06) | (a) 행 1: EL1 push 직전·EL3·`gate-runner.py` 시작 (b) 행 3(가): EL1 push 직전·`gate-runner.py`·세션 시작 (c) 행 3(나): 세션 시작 재판정 (d) 행 3 빈 로그 (e) 행 4: EL1 push 직전·EL3·세션 시작 (f) 위조 구간이 로그 마지막 줄이면 (c)와 같음(마지막 줄은 캐시와 무관하게 재판정, 2026-09-29 개정). 마지막이 아닌 위조 구간을 `rejudged`에 적어 두면 행 3(나)가 건너뛴다 -- §13.5 알려진 한계, 기록 케이스 -- (a)~(e)와 (f)의 마지막 줄 형태는 대조 실패 → 모든 게이트 거부, 사용자 알림 | installed |
| 23 | V4 (2) 판정 경계: `v4_rule_probe/v4.py`의 케이스 67개 전부(§10 실측) -- FAIL 기대 34, PASS 기대 11(입력을 그대로 돌려주는 경로의 명세 리터럴·무발동 값 7 포함), known_limit 8(PASS 7·`UNJUDGED` 1), `UNJUDGED` 12, `NO-SUBJECT` 2. 그리고 누적 회귀 코퍼스 94개 출력 변화 0, 실제 엔진 최상위 함수 전수에서 검출기 예외 0(`sweep_engine.py`) | 기대대로(probe 자체 대조 `기대 불일치 0개`) | direct |
| 24 | EL1 명령 분해(review30 P1·P2, review31 N-08): (a) §12-6 두 줄 `-m` 병합 (b) `echo a` 줄바꿈 `git push gate …` (c) `$(git push gate …)` 안쪽 (d) heredoc 본문의 `git push` 글자 (e) `$'…'` 인자 (f) `git status 2>&1 \| head` (g) 줄 이음 뒤 대상 `cp a \`⏎`<엔진 소스>` | (a)(d)(f) 허용 / (b)(c) push 규칙으로 판정·거부 / (e) 거부 / (g) 대상을 엔진 소스로 판정해 거부 | direct, installed |
| 25 | dispute 기록 없이 code worktree 정리(review30 R-16) | EL1 거부 / 기록 뒤 정리 허용 | direct, installed |
| 12·13·14 | GB0 로드 게이트 | 6a(계획 N4.3) | -- |

* **direct 재생의 gate**: ③은 ④(b)의 gate 생성보다 앞이지만 게이트 코드 캐시(§3.2·§4.4)와 `gate/master` 기준 판정(공격 10c·19·20)은 gate `master`가 있어야 한다. 그래서 `run_all.py --mode direct`는 케이스마다 **임시 gate 저장소**(pre-receive·완료 표지 없음, ④(b) 뒤·(c) 전 상태)를 만들어 쓴다(부트스트랩 재생 감사 F7).
* 공격 20 (b)(오케스트레이터가 역할 worktree에서 `Role: code` 커밋)의 EL2 기대는 해당 없음이다 -- SubagentStop은 subagent에만 오고 오케스트레이터 호출에는 오지 않는다. (b)는 EL1 거부로 판정한다 -- EL4는 커밋 주체를 트레일러로만 알므로 오케스트레이터가 `Role: code`로 흉내 낸 커밋을 code-author 커밋과 구별하지 못한다(검증 agent 지적). 오케스트레이터가 역할 worktree에 쓰는 것 자체를 EL1이 막는 것이 이 공격의 방어선이다(§5.1). `Role: doc` 형태로 끼운 커밋은 EL4가 거부한다(부트스트랩 재생 감사 F7).
* 공격 21·22는 **막는 증거가 아니라 드러내는 증거**다(N3.12.0). 기대는 "표의 그 시점에 대조가 실패하고 무엇이 다른지 적는다"이다.
* 공격 15의 승인 기록 케이스에 `target_kind: staged_diff`(형식 위반, `.ai/approvals/**` 포함한 경로, 올바른 기록)를 넣는다(review30 R-14).

### 13.3 과거 사례 재생

사례마다 원천을 고정하고 재현 패치를 기계적 변환 규칙으로 만든다(원 식·리터럴·조건 구조 그대로).

| 사례 | 원천 | 변환 규칙 | 기대 거부 | 재생 Phase |
|---|---|---|---|---|
| 면적 식 α 상쇄 | e329283:`sizing_recipe.py` `estimate_area_budget` 본문과 self-test `_area_cold_expected = (1 - 0.65) * _a1d_demo + 0.65 * _a2d_cold_expected` | 표지 줄의 self-test 섹션 하나를 test 함수 하나로(본문·리터럴·`print` 그대로) | V4 FAIL 규칙 (2) | 0.5 |
| Test 16 FAIL 박제 | e5fbf92: 기준선 `.log` hunk + 그 시점 `stick_diagram.py` Test 16 섹션 | 섹션을 test 함수로(원형 그대로). 기준선 `.log` 변경은 V5 '비-`.py` 파일' 규칙 대상 | V4 FAIL 규칙 (5), V5(기준선 변경) | 0.5 |
| assert를 조건문 아래로 | 3250baa:`sizing_recipe.py` L5c 섹션 | 섹션을 test 함수로(조건 구조 그대로) | V4 FAIL 규칙 (3) | 0.5 |
| NameError를 삼킨 게이트 | 1b9b4ea: 원 커밋에 결함 코드 없음(agent7 #29) | 주석 설명대로 재구성한 패치 -- ③에서 사용자 확인 항목 | V6 FAIL | 0.5 |
| 격자 확대로 제약 통과 | 2e1944a:`sizing_recipe.py` self-test `grid_points_per_theta=1` → `=3` | 원 diff 그대로(TS1 전 `if __name__` 블록이 V5 입력) | V5 FAIL | 0.5 |
| 재검증 누락 기대값 박제 | caa970b | -- | V2(red 부재) | 1 |
| KVL 위반 동작점 기준값 | 5dc4679 | -- | V9 | 6b |

### 13.4 게이트 변경 뒤 재설치 (review30 R-12)

게이트 변경(`tools/gates/**`, `hooks/role_*`)이 gate에 반영되면 설치된 사본(gate `hooks/pre-receive`·`gate-runner.py`, `.claude/hooks/role_*`)이 새 gate `master` blob과 달라져 §3.3 행 1·5가 실패하고, 그 뒤 모든 게이트가 거부한다 -- **반영 push와 재설치 사이의 fail-closed는 정상 상태다.** 사용자가 세션 밖에서: ① `tools/gates/gate/*`를 gate에 복사 ② `python install.py --only hooks --project .` -- `install.py`는 태그가 이미 있는 항목을 건너뛰므로(review31 N-14), `hooks/role_*.json`의 event·matcher가 바뀐 변경이면 `.claude/settings.json`의 그 항목을 사용자가 고친다 ③ `$PY tools/gates/integrity.py check --scope session`(전부 일치해야 `integrity-failed` 표지가 지워진다). 게이트 변경의 spec card '의도'에 이 재설치 절차를 적는다.

### 13.5 위협 범위 밖으로 분류한 지적 -- 알려진 한계 (review35 재분류)

review30~35 여섯 회차 동안 독립 검증의 S1을 위협 범위(계획 N3.12.0)와 대조하지 않고 그대로 받아 규칙을 넓혔고, 넓힌 규칙이 매 회차 새 결함을 만들었다(사용자 지적 "언제까지 결함을 만들거지?"). 그래서 review35부터 지적을 N3.12.0으로 먼저 가른다: **'막는다' = 이력(`agent7_self_concealment.md`)에 있던 자기 은폐 패턴과 정상 흐름의 오거부**만 설계 규칙으로 고치고, **같은 계정이 의도적으로 설계한 공격**은 아래 한계로 적어 부트스트랩 ③·⑤의 공격 재생에서 실제 코드로 다룬다(막는 규칙을 더하지 않는다). **05 문서 검토는 v3.6으로 끝낸다** -- 남은 우려는 문서 검토가 아니라 공격 재생 로그로 판정한다(WP-21).

| 지적 | 내용 | 분류 | 처리 |
|---|---|---|---|
| review35 M4-01 | code-author 경로(`assets/tests/tools/`)의 `test_*.py`가 수집돼 판정을 바꾼다 | 막는다(판정 환경 조작과 같은 부류) | `pytest_gate.ini`의 `testpaths`·`norecursedirs`(§13.1 ①) |
| review35 M4-02 | `workspaces/numpy.pyw` 등 이름 목록 밖 접미사로 서드파티 모듈 가림 | 의도적 공격(이력에 없음) | 알려진 한계. 공격 재생에 '기록' 케이스로 넣어 동작을 로그로 남긴다 |
| review35 M4-03 | V4 검출기 예외(중첩 def·class 호출) | 정상 흐름 오거부(내 수정이 만든 것) | probe 수정 + 실제 엔진 함수 전수 예외 확인(§10) |
| review35 M4-04·M4-07·M4-08 | 문서 사이 `-P` 규칙 모순, V1 형식 검사의 오거부, 게이트 스크립트 판별식 | 정상 흐름 오거부 | §0·§6.2·§9.2-7 문구 |
| review35 M4-05·M4-06 | V4 (2)가 누적·주석 대입·`setattr`·walrus로 받은 결과를 놓침, `nonlocal`로 바뀐 이름의 거짓 FAIL | 검출기 한계(F 목록) | F7로 적는다. auditor oracle 대조가 덮는다 |
| review35 M4-09 | 판정 트리 안 새 로그 파일(`assets/*.log`)이 사용자 전용 | 판정 트리 기본 거부의 선언된 대가 | 새 파일 종류는 쓰기 경로표 개정으로(§4.1) |
| review31 N-06 (2026-09-29 재분류) | 재판정 통과 캐시 `rejudged`에 마지막이 아닌 위조 구간을 적어 행 3(나) 재판정을 건너뛰게 함 | 의도적 공격(이력에 없음). review35 기준 전의 수정(생략 캐시 제거)이 세션 시작을 348초로 만들었다 | 알려진 한계. 마지막 줄은 항상 재판정(공격 22 c·f의 기록된 형태는 계속 드러남), 공격 22 (f)는 기록 케이스 |
| review34 V1~V3 이전 회차의 의도적 공격(`-s ours` 병합, 모듈 이름 가림 등) | 이미 반영된 규칙은 두되 같은 부류의 새 변형은 위 기준으로 가른다 | -- | -- |

---

## 14. agent 정의 3개 (`agents/gmid-*.md`)

`check_agents.py` FAIL 0(WARN은 기록). frontmatter에 `isolation`을 쓰지 않는다.

| agent | model | tools | 본문 필수 절 |
|---|---|---|---|
| `gmid-code-author` | sonnet | Read, Edit, Write, Glob, Grep, Bash | 입력(spec card, interface card, 자기 worktree 절대 경로), 파일은 자기 worktree 절대 경로(슬래시 표기)로만·git은 `git -C <자기 worktree>`로만·`cd` 금지, 커밋은 `--trailer "Role: code" --trailer "Change-Id: <id>"` 형태, 쓸 수 있는 경로(N3.12.2 인용), dispute로 멈추는 조건, 금지(tests·기준선·픽스처·`conftest.py`·판정 환경 파일, PowerShell), 보고 형식 |
| `gmid-test-author` | opus | Read, Edit, Write, Glob, Bash | 입력은 interface card뿐(소스 열람 금지, Grep 없음), 같은 worktree·커밋 규칙(`Role: test`), oracle 4종과 선택 기준(N3.12.3 인용), 금지(피검 함수로 기대값, 승인 없는 기준 약화), 보고 형식 |
| `gmid-verification-auditor` | opus | Read, Glob, Grep, Bash, Write | 입력(audit worktree, spec card), **격리 복제본에서만 실행**(§12-7), V1~V10 순서(N4.2 인용), 판정 기록 작성(`00-common` §8), 커밋 규칙(`Role: audit`), 금지(작성자 보고를 증거로, 판정 기록 밖 쓰기), 보고 형식 |

---

## 15. `00-common` §17이 넘긴 구현 세부

| 항목 | 정한 것 |
|---|---|
| hook을 거치지 않는 git 명령 | EL1 거부 목록(§6.2). 빠진 것은 EL2(SubagentStop 트레일러)·EL4(커밋 전수)가 잡고, 게이트 훼손은 §3.3이 감지 |
| `PlanTables` 해시 형식 | §15.2 |
| 승인 기록을 찾는 곳 | EL3: index와 HEAD 트리. EL4: `old`(상태 기반)·각 커밋 트리. 작업 트리는 보지 않는다 |
| 옛 승인 표로 되돌리는 변경 | 해시가 같으면 옛 승인 기록으로 통과. 막으려면 사용자가 옛 기록을 지운다 |
| V1 명령 식별 | `auditor_run.commands`의 `V1: `로 시작하는 원소 정확히 하나 |
| `--gmid-strict`·`--gmid-phase` 표기 | 항상 `=` 한 토큰(`00-common` §8.1 v1.8). 비교는 `shlex.split` 뒤 토큰 단위 |
| 신규 심볼 판정의 세 형태 | 신규 하위 모듈 `ModuleNotFoundError.name` → (그 이름, `*`) / 클래스 속성 `AttributeError.obj`가 클래스면 (`<모듈>.<클래스>`, `name`) / 인스턴스 속성은 신규 심볼 아님 |
| EL3 판정 표 검사의 구현 주체 | 부트스트랩 ① 오케스트레이터, 이후 게이트 변경 |

### 15.2 `plan_tables_hash`

* 입력: 계획서 한 판을 `read_plan_tables`와 `read_write_paths`로 파싱한 객체 `{"v_intro", "ic_parts": {IC: [[phase, sub], …]}, "ic_test", "phase_order", "write_paths": [[actor, glob, exclude, condition], …]}`(리스트는 계획서 행 순서).
* 직렬화: `json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))`의 UTF-8 바이트, `sha256` 소문자 16진.
* CLI: `$PY <게이트 코드>/merge_gate.py plan-tables-hash <계획서 파일>`.
* `00-common` §8.2·§9.1(v1.8)이 이 절을 인용한다.

---

## 16. 판정식 모음 (N9.2-3)

| 판정 | 식 | 절 |
|---|---|---|
| 경로 허용 | 주체 행 중 (glob 일치 ∧ 제외 불일치 ∧ 조건 참)이 있음 | §4.1 |
| 오케스트레이터 판정 범위 | `overlaps_any` ∨ 역할 worktree 안 | §5 |
| worktree 결합 | 대상 worktree 브랜치 = `role/<역할>/<id>` | §5.1 |
| 병합 커밋 | 변경 한 건의 M(부모 = (T 끝, K), 트리 = K 트리)이거나 역할 밖 병합(아래 행). 그 밖의 병합 거부 | §8.2-3, §9.2-3·4 |
| 판정 환경 우선 | 경로가 `판정 환경` 행에 맞음 ∧ 주체 ≠ `사용자` → 거부 | §4.1 |
| 판정 트리 기본 거부 | 경로가 `판정 트리` 행에 맞음 ∧ 다른 조건의 행에 안 맞음 ∧ 주체 ≠ `사용자` → 거부 | §4.1 |
| SubagentStop 범위 | test `gate/master..HEAD`, code `role/test/<id>..HEAD`, audit `M..HEAD`(병합 없으면 `role/test/<id>..HEAD`, 최대 1개) | §7 |
| 역할 밖 병합 | 부모 = 2 ∧ 첫 부모가 `old`(EL3는 `gate/master`)와 같거나 그 후손 ∧ 병합 트리 = 첫 부모 트리 (`overlaps_any` 경로 전부에서) ∧ 같은 push에 역할 커밋 없음 | §8.2-3 (라), §9.2-3 |
| 판정 표 변경 | `plan_tables_hash(앞) ≠ plan_tables_hash(뒤)` | §15.2 |
| 변경 한 건 구조 | spec card `evidence_type`의 모양과 커밋 집합이 정확히 같음 | §9.2-4 |
| 무결성 | §3.3 표의 대조 전부 일치 | §3.3 |
| V4 (2) | 정규화(X) ∈ {정규화(E_i) : 정규화(E_i)가 잎이 아니고, 그 return 식에 나오는 매개변수에 결합된 인자 식의 정규형과도 다름} -- X와 E_i는 인라인·인자 결합·같은 모듈 인라인 뒤, 숫자끼리 접지 않음 | §10 |
| V5 | 판정식 표의 한 줄 이상 ∧ 대응 승인 기록 없음 | §10 |

수치 임계값은 없다. 사용자가 정하는 값은 `audit_tail_lines` 하나다(표시 줄 수, 판정에 쓰지 않는다).

---

## 17. 실패 경로 (N9.2-4)

게이트 코드라 N3.14 실패 클래스를 쓰지 않는다.

| 대상 | 코드 |
|---|---|
| Claude Code hook(EL1·EL2) | 0 통과 / 2 거부(예외도 2) |
| git client hook(EL3) | 0 통과 / 1 차단 |
| gate `pre-receive`(EL4) | 0 반영 / 1 거부(예외 포함) |
| 검사 도구(V3~V7) | 0 PASS / 1 FAIL / 2 실행 오류(auditor는 FAIL로 적는다) |
| `merge_gate.py`·`integrity.py` 하위 명령 | 0 통과 / 1 거부 / 2 입력 오류 |

---

## 18. 역할별 산출물 (N9.2-5)

Phase 0.5는 부트스트랩이라 spec card가 없다(산출물은 §13.1의 커밋과 승인 기록). ⑤ 뒤 게이트 변경은 spec card로 한다(red-green, oracle (a) -- 공격 케이스는 구성으로 정답이 정해진 합성 입력. 판정 기준 데이터만 바꾸는 게이트 변경 -- `tools/gates/redteam/**`만 바꾸고 code 커밋이 없는 것 -- 은 test-only, 2026-09-22 `10-test-separation` R2 개정).

---

## 19. DoD 측정 명령 (N9.2-6, N6.2 0.5)

| 완료 조건 | 명령 | 통과 기준 |
|---|---|---|
| 공격 재생 | `$PY tools/gates/redteam/run_all.py --phase 0.5 --mode direct` 와 `--mode installed` | 각 케이스의 `modes`에 든 방식 전부 기대와 일치. 계획 N4.3·N6.2의 '0.5 대상 25건'(12·13·14 제외) |
| 사례 5건 | `$PY tools/gates/redteam/run_all.py --cases 0.5` | 5건 모두 기대 검사 FAIL |
| hook 입력 실측 | `role_hook_input_probe.md` | 있음 + ⑤의 `gmid-*` `agent_type` 확인 |
| agent 정의 | `$PY agent-quality/check_agents.py agents/gmid-*.md` | FAIL 0 |
| 설치·무결성 | `$PY tools/gates/integrity.py check --scope session` | 모든 행 `ok`, exit 0, `bootstrapped` 표지 있음 |
| MG0 | U-39 결정 뒤 그 결정의 JSON 파싱 기준 명령 | U-39 결정대로 |

---

## 20. 착수 조건과 열린 질문 (N9.2-7·8)

* 착수 조건: U-16(계획 N7.2 확정 -- 승인 기록 이전의 결정), U-38(확정, 승인 기록 `20260918-u38-jsonschema`), U-15(닫힘 -- 실측), `00-common` 승인(`20260918-00-common-design`). U-39는 MG0 착수 전에만 필요.
* 이 문서의 승인 기록이 함께 덮는 개정(계획 v5.19, 이 문서 작성 중 반영): N3.12.0 위협 범위 신설, N3.12.2 표(기계 판독·설정 파일·`판정 환경` 조건과 행·`tools/gates/gate/**` 행·부트스트랩 조건 정의), hook 판정 범위, N3.12.3 1·3·5·6·7, N3.12.4 EL1·EL2·EL3·EL4, N3.12.6 ④ 순서·⑤·산출물(세션 시작 hook), N4.2 V3·V4 (2)(확실한 복사 + oracle 대조)·V5, N4.3 공격 목록(28건, 1b·10b·10c·17~25), N6.1 0.5 행, N6.2 0.5 문구(25건), N7.2 U-15 닫힘·U-39, N9.1 05 행, `00-common` v1.8(§8.1 증거 소비자·red 플러그인 위치·로더 규칙 10의 V4 oracle 대조, §8.2 `staged_diff`, CC-1 행). review31 반영(v3.2): N3.12.2 `판정 환경` 행 3개 추가, N4.2 V4 (2) 문구, N4.3 공격 24, N7.2 U-15 `cwd` 기술. review32 반영(v3.3): N3.12.3 7·N3.12.4 EL4(역할 밖 병합), N4.2 V4 (2) 문구, N4.3 공격 10b·19·23, N7.2 U-38(pytest 고정). review33 반영(v3.4): N3.12.2 경로 대조를 casefold로(문단), N4.2 V4 (2) 정규화 괄호, `00-common` §8.1 red 수집 명령 `$PY -P`. review36 뒤(v3.6 마감): 계획 N2.2 WP-22(수정이 결함을 늘리지 않게). review34 반영(v3.5): N3.12.2 조건 `판정 트리`와 그 행, 판정 트리 안 기존 파일의 행(엔진 데이터·기준값·문서·bkit 상태), `판정 환경` 행(`workspaces/*.py`·`__init__.py`, 컴파일 산출물), `tools/gates/pytest_gate.ini` 행, hook 판정 범위, N3.12.6 산출물, N4.2 V4 (2) 통과 경로 문구, `00-common` §8.1 red 수집 명령(`-c`·`--confcutdir`·`PYTHONPYCACHEPREFIX`).
* 열린 질문: U-39(계획 N7.2). "0.5 실측으로 고정" 전제 하나 -- `gmid-*` `agent_type` 값 -- 는 ③·⑤가 실측을 겸하고, 다르면 이 문서를 고친다. review30 S3 중 남은 것(이 판에서 R-18·R-19·R-20·R-22는 반영): **R-17** ④(d) `install.py --only hooks`가 `hooks/`·`bkit/hooks/`의 모든 `.py`를 등록하고 sidecar `.json` 파싱 실패를 조용히 기본값으로 둔다 -- 역할 hook만 설치하는 옵션을 ① 산출물에 넣을지 ④ 전에 사용자 확인. **R-21** 부트스트랩의 게이트 코드와 공격 기대(`expect.json`)를 같은 주체가 쓴다 -- 기대값 파일을 독립 검증 agent가 검토하게 할지 ③ 전에 정한다.
