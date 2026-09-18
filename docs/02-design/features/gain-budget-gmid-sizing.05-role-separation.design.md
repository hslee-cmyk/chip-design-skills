---
template: design
version: 3.2
plan_version: 5.19
---

# gain-budget-gmid-sizing -- 05-role-separation Design Document

> **Summary**: Phase 0.5 역할 분리 인프라의 설계. 위협 범위는 계획 N3.12.0(사용자 결정 C)이다: **이력에 있던 자기 은폐 패턴은 막고, 같은 계정 권한으로 게이트를 부수는 의도적 행위는 막지 않고 드러나게 한다.** 겹은 EL1(도구 호출)·EL2(결과)·EL3(커밋)·EL4(로컬 gate 저장소의 `pre-receive`)이고, 무결성 대조가 게이트 훼손을 감지한다. 쓰기 경로표 파싱, 역할 판정, 판정 기록 로더, auditor 검사 도구(V3~V7), interface card·spec card·dispute, 변경 한 건의 명령 시퀀스, 부트스트랩, 공격 재생, agent 정의 3개.
>
> **Project**: chip-design-skills (analog-gmid-design skill) · **Author**: Claude Code (오케스트레이터)
> **Date**: 2026-09-18 · **Status**: Draft v3.2 -- v3.0 독립 검증(review30)의 S1·S2 16건, v3.1 독립 검증(review31, 수정 후 승인)의 S1·S2·S3 14건을 반영했다. V4 (2)는 사용자 결정 (c)(확실한 복사 검출기 + auditor oracle 대조). 독립 검증 전, 사용자 승인 대기(DEC-51)
> **Planning Doc**: [gain-budget-gmid-sizing.plan.md](../../01-plan/features/gain-budget-gmid-sizing.plan.md) v5.19 · N3.12.0 위협 범위 · N6.1 `0.5` 행 · **공통 정의**: [00-common](gain-budget-gmid-sizing.00-common.design.md)(v1.7 승인 `20260918-00-common-design`, v1.8 개정은 이 문서의 승인이 덮는다)

Context Anchor: 계획서에 `## Context Anchor` 절이 없어 옮기지 않는다.

---

## 0. 이 문서를 읽는 법

* 정의는 계획서와 `00-common`이 정본이다. 이 문서는 **게이트가 어떻게 동작하는가**만 더한다(N9.4).
* **위협 범위(N3.12.0)가 모든 규정의 전제다.** 규정은 '막는다' 행의 패턴을 막고, '드러나게 한다' 행의 행위는 §3.3 무결성 대조로 감지한다. 어떤 규정이 '드러나게 한다' 행위까지 막겠다고 적으면 그것은 과장이다.
* **기댄 실측**: hook 입력(`role_hook_input_probe.md`), git hook 발동(review28 §0, review30 H1: 병합의 hook 시점), gate `pre-receive` 동작과 우회(review29 §0 G1~G10·W1~W3·B1·A1·C1, review30 I2~I8·B1·J1), V4 (2) 검출기(§10, 실제 e329283 함수와 변환 test 입력). 실측이 없는 전제는 "0.5 실측으로 고정"이라고 표시한다.
* **규정은 산문이고, 게이트가 실제로 거부한다는 증거는 공격 재생의 실행 로그다**(WP-21·WP-02). 규정마다 증명하는 공격 번호를 붙인다(§13).
* 구성안: **B -- 계획서 표 직접 읽기**(사용자 선택) + **EL4 = 로컬 gate `pre-receive`**(사용자 결정) + **위협 범위 C**(사용자 결정).
* 명령의 `$PY`는 `C:\Python314\python.exe`다.

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
| gate `master` 참조 | `<gate_path>/gmid-accept-log`: 줄마다 `<old> <new> <시각>`, 첫 줄은 ④(b)에서 사용자가 쓴 `<baseline_commit> <baseline_commit> <시각>`. (가) **사슬**: 첫 줄의 old = new = `baseline_commit`, 각 줄 old = 앞 줄 new, 마지막 줄 new = 현재 gate `master`. (나) **구간 재판정**(review30 I6b): 줄마다 `old..new`를 그 `old` 판 게이트 코드의 `merge_gate.py receive --old <old> --new <new>`로 **데이터만** 다시 판정(§9.1-3과 같은 방식 -- 실행하는 코드는 이미 반영된 게이트 코드뿐). **생략 캐시를 두지 않는다**(review31 N-06: 같은 계정이 쓸 수 있는 생략 목록에 한 줄을 적으면 재판정이 무력화된다) -- 세션마다 전 구간을 재판정하고 비용(로그 줄 수 × 데이터만의 `merge_gate.py` 한 번)은 ⑤에서 재서 기록한다. 표지 뒤 로그가 없거나 비면 실패(review30 I6c) | (가) EL1 `git push gate` 직전·`gate-runner.py` 시작, (가)(나) 세션 시작 |
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
    condition: str    # "없음" | "자기 변경 id" | "게이트 변경" | "부트스트랩" | "승인 기록" | "status 전이만" | "판정 환경"

def read_write_paths(plan_text: str) -> tuple[PathRule, ...]: ...
def match_glob(pattern: str, rel_path: str, change_id: str | None) -> bool: ...
def allowed(actor: str, rel_path: str, ctx: WriteContext) -> Verdict: ...     # Verdict(ok, reason, rule)
def overlaps_any(rel_path: str) -> bool: ...
```

* 표 읽기(절 제목 `#### N3.12.2 `, 이스케이프 안 된 `|`, 셀 수 검사)는 `merge_gate.read_plan_tables`와 **같은 함수**다. '주체'·'조건' 값 집합 밖이면 표 파손과 같이 거부.
* **`match_glob`**: `<id>`는 조각 안의 부분 문자열 토큰 -- `change_id`로 치환(없으면 그 패턴은 맞지 않음). `change_id`는 `00-common` §8.1 `id` 형식. 조각 나누기는 `/`, `**`는 0개 이상 조각, 나머지 조각은 `fnmatch.fnmatchcase`. 대소문자 구분.
* **상대 경로 기준**(review29 Q-11, 계획 N3.12.2 "해당 worktree 루트"): 대상 경로가 속한 worktree의 루트 기준. 루트는 `git -C <대상의 가장 가까운 존재하는 조상 디렉터리> rev-parse --show-toplevel`. 루트와 대상의 접두 비교는 `os.path.normcase` 뒤에 한다(Windows는 대소문자를 무시, review29 B1). 어느 worktree에도 속하지 않는 경로(`$TEMP` 등)는 `overlaps_any` 거짓.
* **`allowed`**: 그 주체의 행 중 하나에 경로 glob으로 맞고 제외 glob에 맞지 않으며 조건이 참이면 허용.
  * `부트스트랩`: 부트스트랩 완료 표지(§3.3)가 있으면 거짓.
  * `승인 기록`·`status 전이만`: EL1은 허용하고 EL3·EL4가 내용으로 판정(§8.2-5).
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

**분해기**(review30 P1·P2 -- `shlex`는 쓰지 않는다: 따옴표 밖 줄바꿈을 공백으로 보고 `$'…'`를 못 읽는다): 따옴표와 이스케이프 상태를 추적하며 **따옴표 밖의** `;`·`&&`·`||`·`|`·`&`·줄바꿈에서만 단순 명령으로 나눈다. 단 리다이렉트 연산자 안의 `&`는 구분자가 아니다(review31 N-08): `>&`, `<&`, `&>`, `&>>`, `N>&M`, `N<&M`(예: `2>&1`, `>&2`). 리다이렉트 연산자 전체는 `>`, `>>`, `>|`, `<`, `<<`(heredoc), `<<-`, `<<<`, `&>`, `&>>`와 앞에 붙는 파일 기술자 번호이고, 대상 토큰은 연산자 바로 뒤 토큰(`&M` 형태는 대상 없음). 따옴표 안의 줄바꿈은 인자의 일부다(§12-6의 두 줄 `-m`). 이스케이프 규칙은 셸을 따른다 -- Bash: 따옴표 밖 역슬래시는 다음 문자를 그대로(그래서 따옴표 없는 `C:\…`는 bash에서도 역슬래시가 사라진다), 작은따옴표 안은 모두 그대로, 큰따옴표 안은 `$`·백틱·`"`·역슬래시·줄바꿈 앞에서만 이스케이프. **역슬래시-줄바꿈(줄 이음)은 따옴표 밖과 큰따옴표 안에서 둘 다 지운다**(bash와 같다, review31 N-08). PowerShell: 이스케이프는 백틱, 역슬래시는 그대로. 토큰의 경로는 `\`를 `/`로 바꾼 뒤 판정한다.
* 명령 치환 `$(…)`·백틱·프로세스 치환 `<(…)`·`>(…)`, PowerShell `$(…)`·`@(…)`는 안쪽을 같은 분해기로 재귀 분해해 판정한다. heredoc(`<<`, `<<-`)은 구분자 줄까지를 데이터로 건너뛴다(따옴표 없는 구분자의 본문은 명령 치환만 재귀 판정).
* 거부(분해하지 않음): `$'…'`, 닫히지 않은 따옴표·괄호, 구분자를 찾지 못한 heredoc. 거부 메시지는 분해하지 못한 위치를 적는다.

| 규칙 | 주체 | 거부 대상 |
|---|---|---|
| 검사 끄기 | 전부 | `--no-verify`, `git commit -n`, `core.hooksPath` 변경 전부, `GIT_CONFIG_*`·`GIT_CONFIG_PARAMETERS` 환경 변수, `git -c alias.*` |
| git 설정 쓰기 | 전부 | `git config`의 쓰기 전부(`--get*`·`--list` 외), `git remote add/set-url/rename/remove` -- 부트스트랩 ④(b)의 `git remote add gate` 한 번은 hook 설치 전이다(review29 Q-01) |
| 저장소 내부 | 전부 | `<git-common-dir>/**`, `<gate_path>/**`를 가리키는 인자·`--git-dir`·리다이렉트·도구 대상. 예외(review31 N-07): 게이트 코드 캐시 `<git-common-dir>/gmid-gate-cache/<커밋 id>/`를 **읽기·실행**하는 두 형태 -- `$PY <캐시>/<이름>.py …`의 스크립트 인자와 `PYTHONPATH=<캐시>` 환경 값(§12-0·§12-7, `00-common` §8.1). 캐시를 쓰기 대상으로 가리키는 것(리다이렉트, `cp`·`mv`·`rm` 대상, 도구 쓰기)은 거부 |
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
* 역할 worktree(`role/<역할>/*` 체크아웃) 각각의 `git status --porcelain=v1 -z --untracked-files=all`에서 무시 목록(`git check-ignore` 참 + `__pycache__/`·`.pytest_cache/`)을 빼고 남은 경로마다 `allowed`.
* **메인 worktree에 역할이 만든 변경**: PreToolUse에서 `tool_use_id`별로 메인 worktree의 (경로, 상태, blob) 중 쓰기 경로표와 겹치는 것의 집합을 `<git-common-dir>/gmid-gate-cache/status-<tool_use_id>.json`에 쓰고, PostToolUse에서 다시 구한 집합과의 차이(새로 생기거나 바뀐 것)가 있으면 위반. 비교 뒤 파일 삭제. 남은 파일은 세션 시작 때 지운다(상한, review29 Q-14).
* **SubagentStop**: `agent_type`의 역할 worktree(브랜치 `role/<역할 짧은 이름>/<id>`)에서 **역할별 범위**의 커밋이 전부 `Role: <그 역할>`·`Change-Id: <id>`이고 병합 커밋이 아닌지 본다(도구 호출 밖에서 만든 커밋도 여기서 드러난다, review29 Q-04). 범위(review30 E2 -- 다른 역할의 커밋을 넣지 않는다): test = `gate/master..HEAD`, code = `role/test/<id>..HEAD`, audit = M이 있으면 `M..HEAD`, 없으면 `role/test/<id>..HEAD`(M = `git rev-list --merges -n 1 HEAD`이고 `role/test/<id>`의 후손일 때 -- test-only는 병합이 없다). audit 범위의 커밋은 **최대 1개**다(review31 N-02: v3.1은 병합이 없으면 '비어 있어야 한다'고 적어 test-only의 auditor 종료를 매번 거부했다). 정상 흐름의 오거부 0은 공격 20 (e)(세 판정 유형 각각)와 ⑤가 보인다.
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
2. **트레일러**(commit-msg): `git interpret-trailers --parse`로 읽은 트레일러에 `Role: code|test|audit|doc|user` 정확히 하나. `code`·`test`·`audit`과 병합 커밋은 `Change-Id` 정확히 하나. 트레일러는 **메시지 마지막 문단**이어야 한다(`-m "요약" -m "Role: …" -m "Change-Id: …"`처럼 나누면 앞 문단은 트레일러가 아니다 -- review29 G10; 명령은 `--trailer` 형식으로 쓴다).
3. **병합 커밋**(commit-msg에서 `MERGE_HEAD`가 있을 때): (가) 트레일러 `Role: doc`·`Change-Id: <id>` (나) 현재 worktree 브랜치 = `role/audit/<id>`, `HEAD` = `role/test/<id>` 끝, `MERGE_HEAD` = `role/code/<id>` 끝 (다) **staged 트리 = `MERGE_HEAD` 트리**(`git diff --cached --quiet MERGE_HEAD`) -- 병합 커밋이 code 끝(K)과 다른 내용을 들일 수 없다(review29 G9·Q-03). (라) **역할 밖 병합**(review31 N-01): 위 (나)에 해당하지 않는 병합은 staged 트리와 `HEAD` 트리가 `overlaps_any` 경로 전부에서 같을 때만 통과(트레일러 불필요 -- 다른 skill·RTL 작업의 병합). 그 밖의 병합은 차단(review30 A19b: 조상에서 갈라진 문서 부모로 되돌리는 병합은 역할 경로를 첫 부모와 다르게 만든다). 병합 커밋에는 4의 경로 권한을 적용하지 않는다 -- 트리가 K와 같고 K까지의 커밋은 커밋마다 검사됐다(review30 C5: 적용하면 정상 병합이 `Role: doc`의 소스 변경으로 막힌다).
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
3. **커밋 전수**(`git rev-list --reverse <old>..<new>`, `baseline_commit`의 조상 제외): **병합 아닌** 커밋마다 첫 부모 대비로 §8.2의 2·4·5를 다시 적용(역할 밖 경로만 바꾼 커밋은 통과). **병합 커밋은 4의 M이거나 역할 밖 병합(병합 트리와 첫 부모 트리가 `overlaps_any` 경로 전부에서 같다, §8.2-3 (라))일 때만 허용**하고 그 밖의 병합은 모두 거부한다(review30 A19b: 역할 커밋 없는 `Role: doc` 병합이 조상 트리로 되돌려 test·`gate_config.json`을 지운 실측 -- 역할 경로가 첫 부모와 달라 역할 밖 병합이 아니다). M에는 경로 권한을 적용하지 않는다(트리 = K, K까지 커밋마다 검사됨 -- review30 C5).
4. **변경 한 건 구조**(review29 Q-03·Q-04·Q-13, review30 R-01·R-07): 역할 커밋(`Role` ∈ {code, test, audit})이 없는 push는 3으로만 판정한다(병합 아닌 커밋은 트레일러와 경로로, 병합은 역할 밖 병합일 때만 -- review31 N-01). 역할 커밋이 있는 push에는 역할 밖 병합이 끼지 못한다. 역할 커밋이 있으면 그 `Change-Id`는 **정확히 하나**이고, `old` 트리에 `docs/02-design/specs/<id>.spec.md`가 있어야 한다. `evidence_type`은 spec card에서 읽는다. `old..new`의 커밋 집합이 아래 모양과 **정확히** 같아야 한다(다른 커밋이 끼면 거부):

   | `evidence_type` | 모양 | T, K |
   |---|---|---|
   | red-green | ① `old..M^1`은 첫 부모 사슬이고 전부 `Role: test`(1개 이상) ② `M^1..M^2`는 전부 `Role: code`(1개 이상, 병합 없음)이고 M^2는 M^1의 후손 ③ M: 부모 둘(M^1, M^2), `Role: doc`, 트리 = M^2 트리 ④ `new`는 부모가 M인 `Role: audit` 1개(판정 기록 추가) | T = M^1, K = M^2 |
   | equivalence | 같음, 단 ①의 `Role: test`가 0개면 M^1 = `old` | 같음 |
   | test-only | `old..new^`는 첫 부모 사슬이고 전부 `Role: test`(1개 이상), `new`는 `Role: audit` 1개, 병합 없음 | T = `new^`, K 없음 |

   ②가 code 쪽에 끼운 `Role: test` 커밋 T'(M^1의 후손이자 M^2의 조상, review30 A20)를 거부한다 -- 그것을 두면 병합본의 test가 auditor가 3에서 고정한 T가 아니게 된다.

5. **판정 기록**: audit 커밋 트리의 `.ai/verification/<id>.json`을 `00-common` §8.1 로더 규칙 1~10으로 읽고, `test_commit` = T, `code_commit` = K(test-only면 `null`), `evidence_type` = spec card 값, `base_commit`이 `old`이거나 그 조상.
6. **증거**: gate는 증거를 다시 실행하지 않는다(§3.2). 판정 기록의 `red.failure_hashes`·`equivalence.outputs_hash`는 auditor가 **격리 복제본**(§12-7)에서 잰 값이고, gate는 로더 규칙(형식·길이)만 판정한다. **이 항목은 형식 검사이지 증거의 증명이 아니다**(review30 R-13) -- 증거의 신뢰는 측정 주체가 작성자와 다르다는 것(N3.12.1)과 V1~V10이 격리 복제본에서 돈다는 것(§12-7)에 기댄다.
7. **엄격 집합**(`00-common` §9.3): 같은 Phase의 병합된 spec card `activated_ic_case` ∪ 이번 필드와 `auditor_run.commands`의 `V1: ` 원소(정확히 하나) 대조. **CC-3 병합 전 판정식**(review29 Q-19): `old` 트리의 `skills/analog-gmid-design/assets/tests/conftest.py`가 AST에서 `addoption("--gmid-phase", …)` 호출을 가지면 CC-3 병합 뒤다.
8. **auditor 판정**: `checks`에 FAIL 없음, N/A는 로더 규칙 10.
9. **승인이 필요한 변경**: V5 기준 약화 승인 기록(auditor가 `checks.V5`에 적은 diff 해시가 승인 기록 `target`과 같음), topology·structure·계획서 판정 표·`Role: user` 조건(§8.2-5, `staged_diff`는 (첫 부모, 그 커밋)으로 다시 계산).
10. **의존성**: `importlib.metadata.version("jsonschema")` = `tools/gates/requirements.txt`의 고정 판.

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
| `mutate_changed.py`(V3) | 뮤테이션 | ① diff가 닿은 `def` 중 `ast.dump`(docstring 제외) 해시가 base와 다른 것 ② 연산자: 비교 뒤집기, 산술 교체(`+↔-`, `*↔/`), 상수 변경(정수 ±1, 실수는 표기된 마지막 자릿수 한 단위 ±), 문장 삭제, 조기 `return`, `except` 본문 삭제 ③ 인벤토리 = 정적 호출 그래프(V7과 같은 그래프)에서 그 함수에 도달하는 test 함수(계획 N4.2 V3 v5.19) ④ 변이마다 임시 복사본에서 그 test만 ⑤ 살아남은 변이가 있으면 FAIL. 변이 id = `<모듈>:<함수 qualname>:<연산자>:<AST 노드 경로>`. 등가 변이 면제는 `target_kind: decision`, `target` = 변이 id 목록인 승인 기록. 자체 AST 변이기(DEC-39) |
| `test_lint.py`(V4) | 자기참조 | 계획 N4.2 V4 (1)~(5). **(2) 확실한 복사 검출**(사용자 결정 (c), review30 R-05·R-06): ① assert 비교(`abs(a - b) <`·`<= tol`, 상대 오차 `abs((a - b) / c) <`·`<= tol`, `==`(어느 쪽이든 `pytest.approx`), `math.isclose`(어느 순서든))에서 피검 함수(interface card 심볼) 호출이 든 쪽과 기대식 X를 가른다. 양쪽 모두 test 함수의 지역 대입(`Assign`·`AnnAssign`)을 **그 assert 시점의 값으로**(본문 순서대로) 인라인한다. 비교 쌍을 못 만들거나 호출 인자를 결합하지 못한 assert(`**kw` 등)는 `UNJUDGED`로 출력한다 ② 피검 함수의 return마다 그 경로의 지역 대입을 인라인하고 test의 호출 인자를 매개변수에 결합(기본값 포함)해 E_i를 만든다. 분기 안에서 바뀐 이름·루프·튜플 대입은 불투명 이름으로 둔다 ③ 같은 모듈 함수 호출은 양쪽 모두 return 변형으로 재귀 인라인 ④ 정규화: 덧셈·뺄셈·곱셈·나눗셈 평탄화와 피연산자 정렬, 정수 거듭제곱(음수 지수 포함) → 곱, 항등원(`+0`·`*1`·`/1`) 제거, 숫자는 float 값, **부호는 밖으로**(음수 숫자 인자와 단항 마이너스를 곱 전체의 부호로 모은다), 곱에 이름·식 인자가 있으면 숫자 인자를 계수 하나로(`x/2` = `x*0.5`). **숫자만의 곱과 합은 접지 않는다**(접으면 재서술 `2e-3*50e3`가 리터럴과 구별되지 않고, 올바른 리터럴 기대값이 전부 FAIL) ⑤ **연산자를 하나 이상 가진** E_i 중 정규화한 X와 같은 것이 있으면 FAIL -- 잎 하나(매개변수·상수)로 끝나는 return 경로는 비교하지 않는다(review31 N-03: `clamp(5, 0, 10) == 5`, `area(0) == 0.0` 같은 명세 리터럴이 FAIL이 되던 거짓 양성. 그런 경로의 복사는 V3가 맡는다). **FAIL은 확실한 복사이고 PASS는 독립의 증거가 아니다.** 알려진 놓침: F1 손으로 계산한 리터럴과 숫자만의 식끼리의 접기 차이(`3.0/2` 대 `3.0*0.5`), F2 분배·약분 등 대수 변형, F3 모듈 밖 함수·자료구조(`sum([...])`, 사전 조회, 튜플 반환 풀기)를 거친 식, F4 잎 하나 return 경로의 복사, F5 `UNJUDGED` assert -- auditor의 oracle 대조(`checks.V4.basis`의 `oracle 대조:` 줄, `UNJUDGED` assert 전부 포함, `00-common` §8.1 로더 규칙 10)와 V3(뮤테이션)가 맡는다. **실측**(`docs/03-analysis/gain-budget-gmid-sizing-function-audit/v4_rule_probe/v4.py` -- 입력은 `git show e329283`의 실제 `estimate_area_budget` 본문과 §13.3 규칙으로 변환한 실제 self-test 섹션, 결과 `v4.out.txt`): 케이스 31개가 모두 기대와 같다 -- FAIL 20: 실제 e329283 첫 assert와 그 변형 6(교환 재배열, `1.0*` 감싸기, `<=`, 상대 오차, `approx` 왼쪽, 주석 달린 대입), `vov*vov` 대 `0.2**2`와 그 반대, `gm*ro` 대 `2e-3*50e3`(재서술 -- 계획 N4.2 V4 (2) 목적), 병렬 저항 같은 식, KCL 합, 같은 모듈 보조 함수 경유, 단항 마이너스 두 위치, `a - b*c` 대 `-b*c + a`, `x/2` 대 `x*0.5`, `1/x` 대 `x**-1`, 키워드 전용 기본값, assert 뒤 재대입(데이터 흐름); PASS 6: `gm*ro` 대 리터럴 `100.0`, 병렬 저항 대 컨덕턴스 합(다른 폐형식), `clamp` 통과·하한 리터럴, `area(0) == 0.0`, 단위 이득; known_limit 4(F1 접은 리터럴, F2 α 상쇄 풀어 쓰기, F3 `sum()`·튜플 반환); `UNJUDGED` 1(`**kw`, 예외 없음). R-05의 네 조합: test 쪽을 인라인하지 않으면 실제값이 변수라 피검 호출을 찾지 못하고, 피검 쪽을 인라인하지 않으면 PASS -- 둘 다 인라인할 때만 FAIL. e329283의 두 번째 assert(`_a1d_demo / 0.731` 대 사전 조회를 거친 첫 return)는 F3로 PASS다. 부트스트랩 ①에서 probe의 규칙 함수를 `test_lint.py`로 옮기고 probe는 지운다(WP-01) |
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
| 7 | auditor | **격리 복제본**: `git clone --no-hardlinks --no-local <audit worktree 경로> <TEMP>/<id>-iso` → `git -C <TEMP>/<id>-iso remote remove origin`(복제본의 `origin`이 작업 저장소를 가리킨다 -- review30 R-09 실측) 후 그 안에서 V1~V10과 증거 측정(red 재현·equivalence 명령). 게이트 코드(red 수집 플러그인 포함)는 복제본의 것이 아니라 base 판(§4.4 캐시)을 `PYTHONPATH` 맨 앞에 두고 쓴다. `auditor_run.commands`에 `V1: …`와 격리 명령을 적는다. 판정 기록을 `$W/<id>-audit/.ai/verification/<id>.json`에 쓰고 `--trailer "Role: audit" --trailer "Change-Id: <id>"` 커밋 |
| 8 | 오케스트레이터 | `git -C $W/<id>-audit push gate role/audit/<id>:master`(gate `pre-receive`가 §9.2로 판정) → `git fetch gate` → 메인 worktree에서 `git merge --ff-only gate/master` |
| 정리 | 오케스트레이터 | `git worktree remove $W/<id>-{test,code,audit}`, `git branch -D role/{test,code,audit}/<id>` |
| 재시도 | 오케스트레이터 | auditor FAIL·dispute·push 거부 뒤에는 정리 형태로 세 worktree·브랜치를 지우고 같은 id로 1부터 다시 한다(거부된 push는 gate에 흔적이 없다). 부분 되돌리기(`reset`·`rebase`)는 쓰지 않는다. **dispute가 있으면 정리 전에**(review30 R-16: dispute는 code worktree에만 있어 정리가 지운다) 오케스트레이터가 그 파일을 읽어 메인 worktree의 spec card 개정에 `## dispute 기록` 절(원문 인용 + blob id)로 남겨 커밋하고, 사용자 결정은 `target_kind: decision` 승인 기록으로 받는다. 이 커밋 전에는 EL1이 code worktree 정리를 거부한다(§6.2). spec card 개정의 gate push는 정리 뒤에 한다(진행 중 push 거부) |

---

## 13. 부트스트랩과 거부 증명 (N3.12.6, N4.3)

### 13.1 부트스트랩 ①~⑤

| 단계 | 할 일 | 산출 |
|---|---|---|
| ① | 오케스트레이터가 §3~§11의 코드, `gate_config.json`(`gate_path`, `workspace_path`, `reachability_roots`, `audit_tail_lines`는 사용자가 정할 자리, `bootstrapped`는 아직 없음), `requirements.txt`, `tools/gates/gate/*`, 양식, agent 정의 3개, `hooks/role_*.json`, `redteam/` 데이터를 쓴다. `.gitignore`에 `library/*.search_archive/`, `runs/`(사용자 승인). 커밋(`Role: doc`) | 커밋 |
| ② | hook 입력 실측 -- 했다(`role_hook_input_probe.md`) | -- |
| ③ | 공격 재생(§13.2 `--mode direct`: 게이트 함수를 직접 불러)과 사례 5건 재생을 실행해 로그를 사용자에게 제시. 사용자 확인 뒤 승인 기록 두 개: 부트스트랩 승인(`diff`, ① 산출 전부) + 최초 판정 표 승인(`plan_tables`) | 거부 로그, 승인 기록 |
| ④ | (a) `.githooks/{pre-commit,commit-msg,pre-merge-commit}` 갱신 커밋(사용자 경로 -- 승인 기록과 함께 한 번) (b) **사용자가**: `git init --bare <gate_path>` → `<gate_path>/hooks/*.sample` 삭제(review30 B1: 남으면 행 4가 첫 판정 push를 거부) → 작업 저장소에 `git remote add gate <gate_path 절대 경로>` → `git push gate master:master`(`pre-receive` 없음 -- 이 커밋이 `baseline_commit`) → `<gate_path>/gmid-accept-log`에 첫 줄 `<baseline_commit> <baseline_commit> <시각>`(§3.3 행 3) → `tools/gates/gate/*`를 gate에 복사(`hooks/pre-receive`, `gate-runner.py`) (c) `gate_config.json`에 `baseline_commit`과 `"bootstrapped": true`를 적은 문서 커밋을 gate로 push(이제 `pre-receive`가 판정한다) (d) `python install.py --only agents --project .`, `python install.py --only hooks --project .`(DEC-41). 옆 `.json`으로 event·matcher가 한 번에 정해지게 하고, 등록 뒤 `.claude/settings.json`을 대조해 다르면 **사용자가 고친다**(hook 등록 뒤에는 EL1이 `.claude/**` 쓰기를 거부한다, review29 Q-17). `--only hooks`가 `hooks/*.py` 전부를 프로젝트 설정에 등록하는 것을 허용할지 ④ 전에 사용자 확인 | 설치 로그, 대조 결과 |
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
| 10b | 메인 세션이 `$TEMP`·다른 skill 디렉터리 쓰기 / 트레일러 없는 역할 밖 커밋과 역할 밖 병합의 gate push(review31 N-01) | 통과(오거부 0). 단 `판정 환경` 행의 이름(`conftest.py`·`pyproject.toml` 등)은 저장소 어디서나 사용자만 쓴다 -- 다른 skill에서도 통과가 아니다(review31 N-12) | direct, installed |
| 10c | 게이트 코드 import 실패(캐시 파일 훼손) / 캐시를 읽기·실행하는 §12-0·§12-7 명령(허용) / 캐시로 리다이렉트·`cp`(거부)(review31 N-07) | 캐시 대조가 다시 풀거나 EL1 exit 2 / 허용 / EL1 exit 2 | direct, installed |
| 11 | RTL agent가 RTL 파일 `Edit` | hook 출력 없음, exit 0 | installed |
| 15 | 판정 기록·승인 기록 형식 위반(케이스 `attacks/15-records/cases/*.json`, 각 `expect`) | EL4 로더 거부 / 올바른 기록 3종 통과 | direct |
| 16 | (i) 승인 없는 판정 표·쓰기 경로표 변경 (a) 직접 커밋 (b) push (ii) 깨진 표 (a)(b) (iii) 흐름 밖에서 깨진 old | (a) EL3 차단 (b) EL4 거부 (iii) EL4 판정 거부. 오거부 0: 승인 있는 개정, 표 값이 안 바뀌는 문장 수정 | direct, installed |
| 17 | 판정 환경 조작(review29 C1·A1, review30 J1): code-author가 `assets/conftest.py`로 실패를 통과로 / 루트 `conftest.py` / `skills/conftest.py` / `skills/analog-gmid-design/pytest.ini`(`addopts = -k …`) / `assets/tests/tools/conftest.py` / `sitecustomize.py`·`*.pth` / `.gitattributes`에 `export-ignore` / test-author가 `assets/tests/pytest.ini` 추가 / test-author가 `assets/tests/conftest.py` 변경 | 앞 여덟: EL1 거부(`판정 환경` 행 우선), 트레일러 없는 커밋으로도 EL3 차단·EL4 거부. 마지막: V5 FAIL(승인 기록 없음). 더해 `pytest.toml`·`.pytest.toml`·`.pytest.ini`(review31 N-05, pytest 9.0.2 실측 `1 deselected`)와 **후보 대조**: `requirements.txt`에 고정한 pytest 판의 `_pytest/config/findpaths.py` `locate_config` 후보 이름(AST의 문자열 상수)이 모두 `판정 환경` 행에 있어야 한다(pytest 판을 올리면 다시 돈다). 재생 데이터는 이 이름의 파일을 저장소에 둘 수 없으므로(판정 환경 우선) 실행 중 임시 저장소에 만든다(review31 N-12) | direct, installed |
| 18 | test-author가 `Read`·`Grep`·`Glob`로 소스 열람(메인·code worktree) | EL1 exit 2 | installed |
| 19 | 흐름 밖 병합: (a) `merge --no-commit` 뒤 내용 추가 (b) 역할 커밋 없는 `Role: doc` 병합(review29 G9) (c) 조상에서 갈라진 문서 커밋을 둘째 부모로 둔 병합 -- test 삭제·엔진 되돌림·`gate_config.json` 삭제(review30 A19b) (d) §12-6 정상 병합 (e) 역할 밖 병합(두 부모가 역할 밖 경로만 바꿈) | (a)~(c) EL3 차단(commit-msg), EL4 거부 / (d)(e) 통과(오거부 0) | direct, installed |
| 20 | 트레일러·역할 흉내: (a) code-author가 `Role: test`·남의 `Change-Id` 커밋 (b) 오케스트레이터가 역할 worktree에서 `Role: code` 커밋 (c) 한 push에 id 둘 (d) code 쪽에 `Role: test` 커밋 T' 끼우기(review30 A20) (e) 세 역할의 정상 종료 -- auditor는 red-green·equivalence·test-only 각각(review31 N-02) | (a)(b) EL1 거부, EL2(SubagentStop) 거부 / (a)~(d) EL4 거부 / (e) 통과(오거부 0) | direct, installed |
| 21 | 원격 설정 조작 뒤 `git push gate`: (a) `git config remote.gate.receivepack …`(review29 G8) (b) `.git/config` 직접 편집 (c) global 설정·`include.path` 파일·`config.worktree`에 같은 키(review30 I2~I4) | (a) EL1이 `git config` 쓰기 거부 / (b)(c) EL1 push 직전·EL3의 행 2 대조 실패 → 거부 | installed |
| 22 | gate 훼손: (a) gate `pre-receive` 덮어쓰기(review29 G6·G7 형태) (b) gate `master` 직접 이동(review30 I6a) (c) 이동 뒤 accept-log에 줄 덧붙이기(I6b) (d) accept-log 비우기(I6c) (e) gate `core.hooksPath`(I8) (f) (c) 뒤 캐시·보조 파일에 그 구간을 적어 두기(review31 N-06 -- 생략 캐시가 없으므로 효과 없음을 보인다) | (a) 행 1: EL1 push 직전·EL3·`gate-runner.py` 시작 (b) 행 3(가): EL1 push 직전·`gate-runner.py`·세션 시작 (c) 행 3(나): 세션 시작 재판정 (d) 행 3 빈 로그 (e) 행 4: EL1 push 직전·EL3·세션 시작 -- 모두 대조 실패 → 모든 게이트 거부, 사용자 알림 | installed |
| 23 | V4 (2) 판정 경계: `v4_rule_probe/v4.py`의 케이스 31개 전부(§10 실측) -- FAIL 기대 20, PASS 기대 6(잎 하나 return의 명세 리터럴 4 포함), known_limit 4, `UNJUDGED` 1 | 기대대로 | direct |
| 24 | EL1 명령 분해(review30 P1·P2, review31 N-08): (a) §12-6 두 줄 `-m` 병합 (b) `echo a` 줄바꿈 `git push gate …` (c) `$(git push gate …)` 안쪽 (d) heredoc 본문의 `git push` 글자 (e) `$'…'` 인자 (f) `git status 2>&1 \| head` (g) 줄 이음 뒤 대상 `cp a \`⏎`<엔진 소스>` | (a)(d)(f) 허용 / (b)(c) push 규칙으로 판정·거부 / (e) 거부 / (g) 대상을 엔진 소스로 판정해 거부 | direct, installed |
| 25 | dispute 기록 없이 code worktree 정리(review30 R-16) | EL1 거부 / 기록 뒤 정리 허용 | direct, installed |
| 12·13·14 | GB0 로드 게이트 | 6a(계획 N4.3) | -- |

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
| 병합 커밋 | 변경 한 건의 M일 때만: 부모 = (T 끝, K), 트리 = K 트리. 그 밖의 병합 거부 | §8.2-3, §9.2-3·4 |
| 판정 환경 우선 | 경로가 `판정 환경` 행에 맞음 ∧ 주체 ≠ `사용자` → 거부 | §4.1 |
| SubagentStop 범위 | test `gate/master..HEAD`, code `role/test/<id>..HEAD`, audit `M..HEAD`(병합 없으면 `role/test/<id>..HEAD`, 최대 1개) | §7 |
| 역할 밖 병합 | 병합 트리 = 첫 부모 트리 (`overlaps_any` 경로 전부에서) ∧ 같은 push에 역할 커밋 없음 | §8.2-3 (라), §9.2-3 |
| 판정 표 변경 | `plan_tables_hash(앞) ≠ plan_tables_hash(뒤)` | §15.2 |
| 변경 한 건 구조 | spec card `evidence_type`의 모양과 커밋 집합이 정확히 같음 | §9.2-4 |
| 무결성 | §3.3 표의 대조 전부 일치 | §3.3 |
| V4 (2) | 정규화(X) ∈ {정규화(E_i) : E_i에 연산자 ≥ 1} -- X와 E_i는 인라인·인자 결합·같은 모듈 인라인 뒤, 숫자만의 식은 접지 않음 | §10 |
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

Phase 0.5는 부트스트랩이라 spec card가 없다(산출물은 §13.1의 커밋과 승인 기록). ⑤ 뒤 게이트 변경은 spec card로 한다(red-green, oracle (a) -- 공격 케이스는 구성으로 정답이 정해진 합성 입력).

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
* 이 문서의 승인 기록이 함께 덮는 개정(계획 v5.19, 이 문서 작성 중 반영): N3.12.0 위협 범위 신설, N3.12.2 표(기계 판독·설정 파일·`판정 환경` 조건과 행·`tools/gates/gate/**` 행·부트스트랩 조건 정의), hook 판정 범위, N3.12.3 1·3·5·6·7, N3.12.4 EL1·EL2·EL3·EL4, N3.12.6 ④ 순서·⑤·산출물(세션 시작 hook), N4.2 V3·V4 (2)(확실한 복사 + oracle 대조)·V5, N4.3 공격 목록(28건, 1b·10b·10c·17~25), N6.1 0.5 행, N6.2 0.5 문구(25건), N7.2 U-15 닫힘·U-39, N9.1 05 행, `00-common` v1.8(§8.1 증거 소비자·red 플러그인 위치·로더 규칙 10의 V4 oracle 대조, §8.2 `staged_diff`, CC-1 행). review31 반영(v3.2): N3.12.2 `판정 환경` 행 3개 추가, N4.2 V4 (2) 문구, N4.3 공격 24, N7.2 U-15 `cwd` 기술.
* 열린 질문: U-39(계획 N7.2). "0.5 실측으로 고정" 전제 하나 -- `gmid-*` `agent_type` 값 -- 는 ③·⑤가 실측을 겸하고, 다르면 이 문서를 고친다. review30 S3 중 남은 것(이 판에서 R-18·R-19·R-20·R-22는 반영): **R-17** ④(d) `install.py --only hooks`가 `hooks/`·`bkit/hooks/`의 모든 `.py`를 등록하고 sidecar `.json` 파싱 실패를 조용히 기본값으로 둔다 -- 역할 hook만 설치하는 옵션을 ① 산출물에 넣을지 ④ 전에 사용자 확인. **R-21** 부트스트랩의 게이트 코드와 공격 기대(`expect.json`)를 같은 주체가 쓴다 -- 기대값 파일을 독립 검증 agent가 검토하게 할지 ③ 전에 정한다.
