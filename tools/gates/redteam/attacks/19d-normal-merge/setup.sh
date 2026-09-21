#!/usr/bin/env bash
# 공격 19 (d): §12-6 정상 병합 -- 통과(오거부 0)
# 기대 근거: 05 §13.2 #19 (d), §8.2-3 (가)~(다), §9.2-4
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt sandbox
rt flow-step start 20260921-rt-rg
rt flow-step test 20260921-rt-rg
rt flow-step code 20260921-rt-rg
rt flow-step merge 20260921-rt-rg --no-commit
