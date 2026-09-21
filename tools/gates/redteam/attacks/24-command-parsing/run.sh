#!/usr/bin/env bash
# 공격 24: EL1 명령 분해
# 기대 근거: 05 §13.2 #24, §6.2 분해기(review30 P1·P2, review31 N-08)
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt hook a-two-line-m-merge --kind control --event PreToolUse --agent none --tool Bash --input-file inputs/a-two-line-m-merge.json
rt hook b-newline-then-push --kind attack --event PreToolUse --agent none --tool Bash --input-file inputs/b-newline-then-push.json
rt hook b-control-echo --kind control --event PreToolUse --agent none --tool Bash --input-file inputs/b-control-echo.json
rt hook c-subst-push --kind attack --event PreToolUse --agent none --tool Bash --input-file inputs/c-subst-push.json
rt hook d-heredoc-body --kind control --event PreToolUse --agent none --tool Bash --input-file inputs/d-heredoc-body.json
rt hook e-ansi-c-quote --kind attack --event PreToolUse --agent none --tool Bash --input-file inputs/e-ansi-c-quote.json
rt hook f-redirect-amp --kind control --event PreToolUse --agent none --tool Bash --input-file inputs/f-redirect-amp.json
rt hook g-line-continuation-target --kind attack --event PreToolUse --agent none --tool Bash --input-file inputs/g-line-continuation-target.json
rt hook g-control-continuation-temp --kind control --event PreToolUse --agent none --tool Bash --input-file inputs/g-control-continuation-temp.json
