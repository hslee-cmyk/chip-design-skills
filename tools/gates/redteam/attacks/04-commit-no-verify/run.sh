#!/usr/bin/env bash
# 공격 4: git commit --no-verify / -n
# 기대 근거: 05 §13.2 #4, §6.2 '검사 끄기' 규칙
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt hook control-proper-commit --kind control --event PreToolUse --agent gmid-code-author --tool Bash --input-file inputs/control-proper-commit.json
rt hook attack-no-verify --kind attack --event PreToolUse --agent gmid-code-author --tool Bash --input-file inputs/attack-no-verify.json
rt hook attack-dash-n --kind attack --event PreToolUse --agent gmid-code-author --tool Bash --input-file inputs/attack-dash-n.json
rt hook attack-main-no-verify --kind attack --event PreToolUse --agent none --tool Bash --input-file inputs/attack-main-no-verify.json
