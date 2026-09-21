#!/usr/bin/env bash
# 공격 1: code-author가 tests 경로를 Write/Edit
# 기대 근거: 05 §13.2 #1(EL1 exit 2), §4.1 allowed, 계획 N3.12.2(tests/**는 test-author)
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt hook control-write-engine --kind control --event PreToolUse --agent gmid-code-author --tool Write --input-file inputs/control-write-engine.json
rt hook attack-write-tests --kind attack --event PreToolUse --agent gmid-code-author --tool Write --input-file inputs/attack-write-tests.json
rt hook attack-edit-tests --kind attack --event PreToolUse --agent gmid-code-author --tool Edit --input-file inputs/attack-edit-tests.json
