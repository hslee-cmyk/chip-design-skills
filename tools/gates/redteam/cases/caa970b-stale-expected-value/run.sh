#!/usr/bin/env bash
# 사례: 재검증 누락 기대값 박제(caa970b L4 self-test) -- base에서 통과해 red가 되지 못한다
# 기대 근거: 05 §13.3 재생 Phase 1(V2 red 부재), 10-test-separation §6.9 (C10)
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt redrun red.json
