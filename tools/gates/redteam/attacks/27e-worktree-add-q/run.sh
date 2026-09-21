#!/usr/bin/env bash
# 공격 27e: §12-1 `git worktree add`에 `-q`를 더해도 같은 판정(D-6)
# 기대 근거: spec card 20260921-gate-flow-liveness 계약 5(D-6), design 05 §12-1(`git worktree add $W/<id>-test -b role/test/<id> gate/master`), §6.2 'worktree 관리'(역할 전부 거부, 오케스트레이터는 §12 형태만), oracle (a)
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt hook control-main-worktree-add --kind control --event PreToolUse --agent none --tool Bash --input-file inputs/add.json
rt hook control-main-worktree-add-q --kind control --event PreToolUse --agent none --tool Bash --input-file inputs/add-q.json
rt hook attack-main-worktree-add-q-outside --kind attack --event PreToolUse --agent none --tool Bash --input-file inputs/add-q-outside.json
rt hook attack-code-author-worktree-add-q --kind attack --event PreToolUse --agent gmid-code-author --tool Bash --input-file inputs/add-q.json
