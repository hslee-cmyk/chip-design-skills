#!/usr/bin/env bash
# 사례: 면적 식 α 상쇄 -- 자기참조 기대값
# 기대 근거: 05 §13.3 e329283 (V4 FAIL 규칙 (2)), 계획 N4.3 과거 사례
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt vcase v.json
