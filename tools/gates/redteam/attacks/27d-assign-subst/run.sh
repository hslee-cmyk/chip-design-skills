#!/usr/bin/env bash
# 공격 27d: 대입 안 명령 치환(`NAME=…$(cmd)…`)을 예외 없이 판정(D-10)
# 기대 근거: spec card 20260921-gate-flow-liveness 계약 4(D-10), design 05 §6.2 분해기('명령 치환 `$(…)` … 안쪽을 같은 분해기로 재귀 분해해 판정'), 05 README('예외로 끝난 fail-closed는 판정이 아니다'), oracle (a)
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt hook control-assign-subst-path --kind control --event PreToolUse --agent none --tool Bash --input-file inputs/assign-subst-path.json
rt hook control-assign-subst-suffix --kind control --event PreToolUse --agent none --tool Bash --input-file inputs/assign-subst-suffix.json
rt hook attack-assign-subst-push --kind attack --event PreToolUse --agent none --tool Bash --input-file inputs/assign-subst-push.json
rt hook attack-echo-subst-push --kind attack --event PreToolUse --agent none --tool Bash --input-file inputs/echo-subst-push.json
rt hook control-assign-subst-cache-script --kind control --event PreToolUse --agent none --tool Bash --input-file inputs/assign-subst-cache-script.json
rt hook control-assign-subst-temp-script --kind control --event PreToolUse --agent none --tool Bash --input-file inputs/assign-subst-temp-script.json
