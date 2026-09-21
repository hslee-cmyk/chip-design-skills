#!/usr/bin/env bash
# 공격 25: dispute 기록 없이 code worktree 정리 / 기록 뒤 정리 허용
# 기대 근거: 05 §13.2 #25, §6.2 '정리 전 dispute 보존'(review30 R-16), §12 재시도
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt sandbox
rt flow-step start 20260921-rt-rg
rt flow-step test 20260921-rt-rg
rt flow-step worktrees 20260921-rt-rg
rt set CODEWT '@{W}/20260921-rt-rg-code'
rt write '@{CODEWT}/docs/02-design/disputes/20260921-rt-rg.md' --jtext '"---\nid: 20260921-rt-rg\nspec_card: docs/02-design/specs/20260921-rt-rg.spec.md\ntest_id: x\n---\n## 문제의 test\nx\n"'
rt git '@{CODEWT}' add -A
rt git '@{CODEWT}' commit -q -m dispute --trailer 'Role: code' --trailer 'Change-Id: 20260921-rt-rg'
