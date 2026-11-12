# 키트 프로젝트 Claude Code 훅 (정본 = 이 폴더, git 관리)

이 키트 루트에서 Claude Code 세션을 열 때 적용되는 PreToolUse 훅이다. 스크립트는 모든 머신에서 같은 파일을 쓴다.
머신마다 다른 것(python 경로·점검 폴더 위치)은 git 밖의 `.claude/settings.json`에서 **환경 변수**로 넘긴다.

| 훅 | matcher | 하는 일 | 의존 |
|---|---|---|---|
| `ask_gate.py` | `AskUserQuestion` | 원칙 26 보고 형식 점검 파일이 없거나 불완전하면 거부(fail-closed). 키트 루트 안에서만 적용 | `ask_gate_rules.py`, `ask_gate_extra.json` (`ask_gate_template.py` = 점검 파일 틀 생성) |
| `append_guard.py` | `Bash\|PowerShell` | 임시 폴더 밖 파일에 셸 추가 쓰기(`>>`, `tee -a`, heredoc 파일 쓰기 등) 거부 (원칙 29) | — |

자가 점검: `python ask_gate_selftest.py`, `python append_guard_selftest.py` (Linux에서 append 쪽은 `TEMP=/tmp TMP=/tmp`로 실행).

## 머신별 `.claude/settings.json` (git 밖)
환경 변수: `ASK_GATE_PRINCIPLES`(원칙 26 정본 = skill `.claude/skills/report-bundle/SKILL.md`, 기본값이 이 저장소 상대 경로라 보통 지정하지 않는다), `ASK_GATE_REPO`(적용 루트 = 키트 루트),
`ASK_GATE_DIR`(점검 폴더 `wt/_drafts/ask_gates`), `ASK_GATE_BASE`(`wt/_drafts/...` 상대 경로 기준 = `wt`의 부모),
`APPEND_GUARD_ALLOW`(추가 허용 루트, os.pathsep 구분). 미지정 시 스크립트 기본값(Windows 경로)을 쓴다.

Windows (python `C:\Python314\python.exe`, 기본값 경로 그대로):
```json
{"hooks": {"PreToolUse": [
  {"matcher": "AskUserQuestion", "hooks": [{"type": "command", "command": "\"C:\\Python314\\python.exe\" \"<키트>\\.claude\\hooks\\ask_gate.py\""}]},
  {"matcher": "Bash|PowerShell", "hooks": [{"type": "command", "command": "\"C:\\Python314\\python.exe\" \"<키트>\\.claude\\hooks\\append_guard.py\""}]}
]}}
```
Linux (예: cloud0 — `~/claude.run/wt -> worktrees` 링크로 `wt/_drafts` 경로를 맞춘다):
```json
{"hooks": {"PreToolUse": [
  {"matcher": "AskUserQuestion", "hooks": [{"type": "command", "command": "ASK_GATE_REPO=\"$HOME/claude.run/chip-design-skills\" ASK_GATE_DIR=\"$HOME/claude.run/wt/_drafts/ask_gates\" ASK_GATE_BASE=\"$HOME/claude.run\" \"/opt/mcp-env/bin/python3\" \"$CLAUDE_PROJECT_DIR/.claude/hooks/ask_gate.py\""}]},
  {"matcher": "Bash|PowerShell", "hooks": [{"type": "command", "command": "APPEND_GUARD_ALLOW=\"/tmp:/var/tmp\" \"/opt/mcp-env/bin/python3\" \"$CLAUDE_PROJECT_DIR/.claude/hooks/append_guard.py\""}]}
]}}
```
- `ask_gate`의 근거 경로 인식: Windows 드라이브 경로·`wt/_drafts/...`, Linux에서는 POSIX 절대경로도(2026-11-11 결정 A).
  알려진 기존 오탐: 드라이브 패턴이 URL의 `s://`를 경로로 잡는다(미수정).
- 전역 훅(`guard-bash-nul`, `guard-submodule-formal`)은 정본이 키트 `hooks/`이고 `~/.claude/hooks`에 설치된다(별개).
