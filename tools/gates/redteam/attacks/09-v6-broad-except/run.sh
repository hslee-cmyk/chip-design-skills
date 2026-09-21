#!/usr/bin/env bash
# 공격 9: `except Exception: return` 추가 (V6)
# 기대 근거: 계획 N4.2 V6, N4.3 #9
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt vcase v.json
