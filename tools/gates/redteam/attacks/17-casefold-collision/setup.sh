#!/usr/bin/env bash
# 공격 17 (review33): casefold하면 기존 경로와 같아지는 `Skills/…` 경로를 더하는 커밋
# 기대 근거: 05 §4.1 'EL3·EL4는 casefold 충돌 경로를 더하는 커밋을 거부', §13.2 #17
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
