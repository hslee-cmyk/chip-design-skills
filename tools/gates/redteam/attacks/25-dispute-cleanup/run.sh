#!/usr/bin/env bash
# 공격 25: dispute 기록 없이 code worktree 정리 / 기록 뒤 정리 허용
# 기대 근거: 05 §13.2 #25, §6.2 '정리 전 dispute 보존'(review30 R-16), §12 재시도
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt hook attack-remove-worktree --kind attack --event PreToolUse --agent none --tool Bash --input-file inputs/attack-remove-worktree.json
rt hook attack-delete-branch --kind attack --event PreToolUse --agent none --tool Bash --input-file inputs/attack-delete-branch.json
rt git --save DBLOB '@{CODEWT}' hash-object 'docs/02-design/disputes/20260921-rt-rg.md'
rt write '@{WORK}/docs/02-design/specs/20260921-rt-rg.spec.md' --append --jtext '"## dispute 기록\n> 문제의 test x\nblob: @{DBLOB}\n"'
rt git '@{WORK}' add -A
rt git '@{WORK}' commit -q -m 'spec dispute record' --trailer 'Role: doc'
rt hook control-remove-worktree-after-record --kind control --event PreToolUse --agent none --tool Bash --input-file inputs/control-remove-worktree-after-record.json
rt hook control-delete-branch-after-record --kind control --event PreToolUse --agent none --tool Bash --input-file inputs/control-delete-branch-after-record.json
