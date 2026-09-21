#!/usr/bin/env bash
# 공격 1b: code-author의 자기 id / 남의 id dispute
# 기대 근거: 05 §13.2 #1b(허용 / EL1 거부), N3.12.2 `docs/02-design/disputes/<id>.md` 자기 변경 id
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
