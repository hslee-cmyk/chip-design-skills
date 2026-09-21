#!/usr/bin/env bash
# 공격 20 (b): 오케스트레이터가 역할 worktree에서 커밋
# 기대 근거: 05 §13.2 #20 (b), §6.2 '역할 worktree 커밋'(오케스트레이터), §5.1, §7, §9.2-4
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt sandbox
rt flow-step start 20260921-rt-rg
rt flow-step test 20260921-rt-rg
rt flow-step worktrees 20260921-rt-rg
rt set CODEWT '@{W}/20260921-rt-rg-code'
