#!/usr/bin/env bash
# 사례: 격자 확대로 제약 통과(grid_points_per_theta 1 -> 3)
# 기대 근거: 05 §13.3 2e1944a (V5 FAIL, 원 diff 그대로 -- TS1 전 if __name__ 블록이 V5 입력)
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt vcase v.json
