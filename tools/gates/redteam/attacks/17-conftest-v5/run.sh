#!/usr/bin/env bash
# 공격 17: test-author가 assets/tests/conftest.py 변경 -> V5 FAIL(승인 기록 없음)
# 기대 근거: 05 §13.2 #17 마지막, §10 V5 'conftest.py는 무조건 승인 기록 요구'(review30 J1)
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt vcase v.json
