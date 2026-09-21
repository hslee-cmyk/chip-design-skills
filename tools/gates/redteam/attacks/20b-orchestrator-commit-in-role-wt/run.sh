#!/usr/bin/env bash
# 공격 20 (b): 오케스트레이터가 역할 worktree에서 커밋
# 기대 근거: 05 §13.2 #20 (b), §6.2 '역할 worktree 커밋'(오케스트레이터), §5.1, §7, §9.2-4
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt hook attack-el1-main-commit-role-code --kind attack --event PreToolUse --agent none --tool Bash --input-file inputs/attack-el1-main-commit-role-code.json
rt hook attack-el1-main-commit-role-doc --kind attack --event PreToolUse --agent none --tool Bash --input-file inputs/attack-el1-main-commit-role-doc.json
rt write '@{CODEWT}/docs/02-design/rt-notes.md' --jtext '"# orch\n"'
rt git '@{CODEWT}' add -A
rt git '@{CODEWT}' commit -q -m orch --trailer 'Role: doc'
rt hook attack-el2-stop --kind attack --event SubagentStop --agent gmid-code-author
rt flow rg2 --code-role doc
rt el4 attack-el4 --kind attack --old '@{20260921-rt-rg2.OLD}' --new '@{20260921-rt-rg2.NEW}'
