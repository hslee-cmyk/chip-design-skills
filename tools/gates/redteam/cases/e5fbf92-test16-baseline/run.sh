#!/usr/bin/env bash
# 사례: stick_diagram Test 16 FAIL 박제 -- print 판정 + 기준선 .log 변경
# 기대 근거: 05 §13.3 e5fbf92 (V4 FAIL 규칙 (5), V5 기준선 변경)
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt vcase v.json
