#!/usr/bin/env bash
# 공격 18: test-author가 Read·Grep·Glob로 소스 열람(메인·code worktree)
# 기대 근거: 05 §13.2 #18(installed 전용), §6.4 DEC-38
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt not-implemented attack
