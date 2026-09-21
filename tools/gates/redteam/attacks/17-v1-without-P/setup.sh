#!/usr/bin/env bash
# 공격 17 (review33): 판정 기록 V1 명령에 -P가 없으면 EL4 거부
# 기대 근거: 05 §9.2-7 V1 명령 형태, §13.2 #17
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt sandbox
