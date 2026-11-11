---
name: wrap
description: |
  작업을 닫을 때 단기기억(작업메모리 `.ai/working/<slug>.md`)을 증류하는 skill — 교훈은 장기기억으로 **제안**하고,
  일회성 경과(결정·실패·결과)는 일화 기록(`.ai/episodes/`)으로 남긴 뒤 작업 파일과 ACTIVE.md 줄을 정리한다.
  ai-memory Phase 8(단기기억 운용 자동화)의 W3. 프로젝트 무관(작업메모리가 있는 모든 repo).
  다음 상황에서 사용:
  (1) 작업메모리의 작업이 끝났을 때 — "이 작업 끝", "마무리해", "wrap", "작업 닫아"
  (2) Stop hook이 "끝난 일이면 /wrap으로 교훈만 남긴다"고 안내했을 때
  (3) 긴 작업의 한 phase를 닫고 경과를 남길 때
  작업메모리가 없는 프로젝트, 진행 중인 작업을 잠시 멈추는 경우(그때는 작업 파일만 갱신)에는 쓰지 않는다.
  트리거: wrap, /wrap, 작업 종료, 작업 마무리, 작업 닫기, 증류, 일화 기록, episode, close task.
allowed-tools:
  - Read
  - Write
  - Bash
  - Grep
---

# wrap — 작업 종료 증류 (단기기억 → 장기기억 + 일화)

단기기억은 끝나면 **두 갈래로 나뉜다**: 다시 쓸 교훈 → 장기기억(사람 승인), 일회성 경과 → 일화 기록(검색 가능).
결정적인 부분(수집·형식 검사·정리)은 스크립트가, 판단(분류·요약)은 이 skill(AI)이 한다.

**기존 skill과의 관계 — 이 skill은 앞단 분배기다. 교훈 자산화를 다시 구현하지 않는다.**
| skill | 입력 → 출력 | 시점 |
|---|---|---|
| `/wrap` (이것) | 작업메모리(`.ai/working`) → 갈래 분류 + 일화 기록 + 작업 파일 정리 | 작업을 닫을 때 |
| `/solution-capture` | 대화 → `docs/solutions` (해결한 버그 자산) | 버그를 고친 직후, 또는 /wrap이 넘길 때 |
| `/kb-promote` | `docs/solutions` → critical-patterns [A] / ai-memory [B] | 솔루션이 반복·일반화될 때 |

**경로**: `AM = ${AI_MEMORY_REPO:-~/ai-memory}`. `PY` = 표준 라이브러리 python 아무것이나
(`~/.claude/settings.json`의 `wm_*.py` hook 명령에 쓰인 python과 같은 것을 권장).

## 절차

### 1. 수집
```bash
"$PY" "$AM/tools/wm_wrap.py" gather [--slug <slug>]     # 진행 중 작업이 하나면 slug 생략
```
JSON: 작업 파일 본문, 시작일 이후 commit, 미commit 변경, transcript 경로(머신 로컬), `episode_id`·`episode_path`.

### 2. 분류 — 작업 파일·commit·이번 대화에서 항목을 뽑아 셋으로 나눈다
| 갈래 | 기준 | 보낼 곳 |
|---|---|---|
| **해결한 비자명 버그** | 이 repo 코드가 있어야 이해되는 버그·근본원인·수정 | `/solution-capture` → `docs/solutions` (그 skill이 있는 프로젝트) |
| **일반화되는 교훈** | 다른 프로젝트에도 통하는 원칙·툴 노하우·선호 | 이미 `docs/solutions`에 있는 솔루션이 출처면 `/kb-promote` [B], 아니면 ai-memory `memory_propose` → `inbox/` (사람 승인 후 반영). ID 항목이면 `<!-- rel: … -->` 주석 포함 |
| **일회성 경과** | 이번 작업에서만 의미 있는 결정·실패·결과 | 3단계 일화 기록 |

같은 내용을 두 갈래에 쓰지 않는다. 일화에는 교훈을 **링크**로만 남긴다(예: "→ inbox/20261111-xxx.md 제안").

### 3. 일화 기록 작성 — `episode_path`에 쓴다(60줄 이하)
```markdown
---
kind: episode
id: <episode_id>                 # gather 출력 그대로 (^EP-[0-9a-z-]+$)
project: <project>
date: YYYY-MM-DD
slug: <slug>
commits: [<hash>, ...]
transcript: <gather의 transcript 또는 null>   # 머신 로컬 경로 — 원문을 붙이지 않는다
---
<!-- rel: about=<관련 의미론 노드 ID, 예: T4,FORMAL,P-FIFOSW>; alias=<검색 단서 2~5개> -->

# <작업 제목>

## 목표
<한두 줄>

## 결정 (사용자 원문 인용)
- <결정> — "<사용자 원문>"

## 실패와 원인
- <시도> → <실패 요지> → <원인·판단>

## 결과
- <commit·산출물·수치>
- 교훈 제안: <inbox/… 또는 docs/solutions/… 경로, 없으면 "없음">
```
- `about` 노드는 `memory_search`로 찾는다(결과의 `nodes`). 맞는 노드가 없으면 가장 가까운 Pattern·FailureClass·Rule.
- 외부 문서(이슈 본문·로그 원문)는 붙이지 않는다 — 요약만(작업메모리와 같은 규칙).
- 형식 검사: `"$PY" "$AM/tools/wm_wrap.py" check --episode <episode_path>` → `OK`가 나올 때까지 고친다.

### 4. 사용자 확인 → 닫기
분류 결과(제안 목록·일화 경로)를 표로 보여 주고 **확인을 받은 뒤**:
```bash
"$PY" "$AM/tools/wm_wrap.py" close --slug <slug>    # 작업 파일 삭제 + ACTIVE.md 줄 삭제
```
commit은 그 프로젝트 규칙대로(사용자가 요청할 때). 일화 기록은 commit 대상이다(다른 PC·AI가 회수).

## 하지 않는 것
- ai-memory `memory/`를 직접 고치지 않는다(제안만, `inbox/`).
- transcript 원문을 일화나 장기기억에 넣지 않는다.
- 사용자 확인 없이 `close`하지 않는다.
