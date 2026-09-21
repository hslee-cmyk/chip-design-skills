#!/usr/bin/env bash
# 공격 3: 한 커밋에 소스+tests
# 기대 근거: 05 §13.2 #3(EL3 차단, EL4 거부), §8.2-4 '소스와 test 함께면 차단', 계획 N3.12.4 EL3
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
rt write '@{CODEWT}/skills/analog-gmid-design/assets/rt_engine.py' --append --jtext '"\n\ndef rt_scale(x):\n    return 3.0 * x\n"'
rt git '@{CODEWT}' add -A
