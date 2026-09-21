#!/usr/bin/env bash
# V3 거부 증명: 살아남는 변이(0 입력만 보는 test)
# 기대 근거: 05 §10 '거부 증명: V3 -> redteam/v3_survivor', 계획 N4.2 V3
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt vcase v.json
