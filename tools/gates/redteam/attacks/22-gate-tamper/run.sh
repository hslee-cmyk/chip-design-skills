#!/usr/bin/env bash
# 공격 22: gate 훼손(pre-receive 덮어쓰기·master 직접 이동·accept-log 덧붙이기·비우기·core.hooksPath·생략 캐시) (드러내는 증거, installed 전용)
# 기대 근거: 05 §13.2 #22, §3.3 무결성 대조 행 1~4, N3.12.0 '드러나게 한다'
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt not-implemented attack
