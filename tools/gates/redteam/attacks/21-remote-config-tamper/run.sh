#!/usr/bin/env bash
# 공격 21: 원격 설정 조작 뒤 git push gate (드러내는 증거, installed 전용)
# 기대 근거: 05 §13.2 #21, §3.3 무결성 대조 행 1~4, N3.12.0 '드러나게 한다'
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt not-implemented attack
