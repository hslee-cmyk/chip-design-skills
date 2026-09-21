#!/usr/bin/env bash
# 공격 27b: 오케스트레이터의 §12 정리(merge --abort, remove --force) 허용 / 역할·다른 경로·dispute 미기록은 거부(D-3)
# 기대 근거: spec card 20260921-gate-flow-liveness 계약 2(D-3), design 05 §12 '정리' 행(`git worktree remove [--force] $W/<id>-{test,code,audit}`, `git -C $W/<id>-audit merge --abort`, `--force`는 이 세 경로에만), §6.2 '정리 전 dispute 보존'·'worktree 관리'(역할은 전부 거부), oracle (a)
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt sandbox
rt flow-step start 20260921-rt-rg
rt flow-step test 20260921-rt-rg
rt flow-step worktrees 20260921-rt-rg
rt set CODEWT '@{W}/20260921-rt-rg-code'
rt set TESTWT '@{W}/20260921-rt-rg-test'
rt set AUDITWT '@{W}/20260921-rt-rg-audit'
rt write '@{CODEWT}/docs/02-design/disputes/20260921-rt-rg.md' --jtext '"---\nid: 20260921-rt-rg\nspec_card: docs/02-design/specs/20260921-rt-rg.spec.md\ntest_id: x\n---\n## 문제의 test\nx\n"'
rt git '@{CODEWT}' add -A
rt git '@{CODEWT}' commit -q -m dispute --trailer 'Role: code' --trailer 'Change-Id: 20260921-rt-rg'
