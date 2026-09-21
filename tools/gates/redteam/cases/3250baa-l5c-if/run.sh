#!/usr/bin/env bash
# 사례: L5c assert를 `if _l5c_result is not None:` 아래로
# 기대 근거: 05 §13.3 3250baa (V4 FAIL 규칙 (3))
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt vcase v.json
