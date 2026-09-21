#!/usr/bin/env bash
# 공격 8: 허용오차 확대 (V5, 승인 기록 없음)
# 기대 근거: 계획 N4.2 V5, N0.4 기준 약화 '허용오차 확대'·'비교 완화', 05 §10 V5 판정식
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt vcase v.json
