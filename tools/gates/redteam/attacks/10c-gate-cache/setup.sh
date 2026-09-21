#!/usr/bin/env bash
# 공격 10c: 캐시 훼손 / 캐시 읽기·실행(허용) / 캐시로 리다이렉트·cp(거부)
# 기대 근거: 05 §13.2 #10c, §4.4 캐시 대조, §6.2 저장소 내부 규칙 예외(review31 N-07·review32 M-09)
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt sandbox
rt flow-step start 20260921-rt-rg
rt flow-step test 20260921-rt-rg
rt flow-step worktrees 20260921-rt-rg
rt set CODEWT '@{W}/20260921-rt-rg-code'
rt set TESTWT '@{W}/20260921-rt-rg-test'
rt set AUDITWT '@{W}/20260921-rt-rg-audit'
