#!/usr/bin/env bash
# 공격 27b: 오케스트레이터의 §12 정리(merge --abort, remove --force) 허용 / 역할·다른 경로·dispute 미기록은 거부(D-3)
# 기대 근거: spec card 20260921-gate-flow-liveness 계약 2(D-3), design 05 §12 '정리' 행(`git worktree remove [--force] $W/<id>-{test,code,audit}`, `git -C $W/<id>-audit merge --abort`, `--force`는 이 세 경로에만), §6.2 '정리 전 dispute 보존'·'worktree 관리'(역할은 전부 거부), oracle (a)
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt hook control-main-merge-abort-audit --kind control --event PreToolUse --agent none --tool Bash --input-file inputs/merge-abort-audit.json
rt hook control-main-remove-force-audit --kind control --event PreToolUse --agent none --tool Bash --input-file inputs/remove-force-audit.json
rt hook control-main-remove-force-test --kind control --event PreToolUse --agent none --tool Bash --input-file inputs/remove-force-test.json
rt hook attack-code-author-merge-abort --kind attack --event PreToolUse --agent gmid-code-author --tool Bash --input-file inputs/merge-abort-audit.json
rt hook attack-code-author-remove-force-audit --kind attack --event PreToolUse --agent gmid-code-author --tool Bash --input-file inputs/remove-force-audit.json
rt hook attack-test-author-remove-force-test --kind attack --event PreToolUse --agent gmid-test-author --tool Bash --input-file inputs/remove-force-test.json
rt hook attack-main-merge-abort-code --kind attack --event PreToolUse --agent none --tool Bash --input-file inputs/merge-abort-code.json
rt hook attack-main-remove-force-outside-name --kind attack --event PreToolUse --agent none --tool Bash --input-file inputs/remove-force-outside.json
rt hook attack-main-remove-force-outside-dir --kind attack --event PreToolUse --agent none --tool Bash --input-file inputs/remove-force-sb.json
rt hook attack-main-remove-force-code-no-record --kind attack --event PreToolUse --agent none --tool Bash --input-file inputs/remove-force-code.json
# dispute 기록(공격 25와 같은 절차) 뒤 code worktree --force 정리
rt git --save DBLOB '@{CODEWT}' hash-object 'docs/02-design/disputes/20260921-rt-rg.md'
rt write '@{WORK}/docs/02-design/specs/20260921-rt-rg.spec.md' --append --jtext '"## dispute 기록\n> 문제의 test x\nblob: @{DBLOB}\n"'
rt git '@{WORK}' add -A
rt git '@{WORK}' commit -q -m 'spec dispute record' --trailer 'Role: doc'
rt hook control-main-remove-force-code-after-record --kind control --event PreToolUse --agent none --tool Bash --input-file inputs/remove-force-code.json
