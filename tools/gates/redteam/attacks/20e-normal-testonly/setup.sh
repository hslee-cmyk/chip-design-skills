#!/usr/bin/env bash
# 공격 20 (e): 세 역할 정상 종료 -- test-only (오거부 0)
# 기대 근거: 05 §13.2 #20 (e), §7 SubagentStop 범위(review30 E2, review31 N-02, review33 M2-08), §9.2-4 표
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt sandbox
