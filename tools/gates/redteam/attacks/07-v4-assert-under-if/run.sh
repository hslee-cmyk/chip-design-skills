#!/usr/bin/env bash
# 공격 7: assert를 `if result is not None:` 아래로 (V4 (3))
# 기대 근거: 계획 N4.2 V4 (3), N4.3 #7
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt vcase v.json
