#!/usr/bin/env bash
# 공격 6: 기대값을 피검 함수로 만든 test (V4 (1))
# 기대 근거: 05 §13.2 #6~9, 계획 N4.2 V4 (1), N4.3 #6
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt vcase v.json
