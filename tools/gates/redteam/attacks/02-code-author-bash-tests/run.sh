#!/usr/bin/env bash
# 공격 2: code-author가 Bash(파이썬)로 tests 파일 생성
# 기대 근거: 05 §13.2 #2(EL2 exit 2), §7 역할 worktree status 대조
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt hook control-pre --kind record --event PreToolUse --agent gmid-code-author --tool Bash --input-file inputs/control-pre.json --tool-use-id toolu_rt2a
rt sh '@{CODEWT}' --command-file cmd-control.sh
rt hook control-post --kind control --event PostToolUse --agent gmid-code-author --tool Bash --input-file inputs/control-post.json --tool-use-id toolu_rt2a
rt hook attack-pre --kind record --event PreToolUse --agent gmid-code-author --tool Bash --input-file inputs/attack-pre.json --tool-use-id toolu_rt2b
rt sh '@{CODEWT}' --command-file cmd-attack.sh
rt hook attack-post --kind attack --event PostToolUse --agent gmid-code-author --tool Bash --input-file inputs/attack-post.json --tool-use-id toolu_rt2b
