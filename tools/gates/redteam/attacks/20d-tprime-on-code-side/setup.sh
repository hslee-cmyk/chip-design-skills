#!/usr/bin/env bash
# 공격 20 (d): code 쪽에 Role: test 커밋 T' 끼우기(review30 A20)
# 기대 근거: 05 §13.2 #20 (d), §9.2-4 ②
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt sandbox
rt flow rg --extra-role-test
