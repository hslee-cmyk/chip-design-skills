#!/usr/bin/env bash
# V7 거부 증명: 어디서도 부르지 않는 새 def
# 기대 근거: 05 §10 '거부 증명: V7 -> redteam/v7_unwired', 계획 N4.2 V7
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt vcase v.json
