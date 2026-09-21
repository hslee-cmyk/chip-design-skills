#!/usr/bin/env bash
# 공격 27a: 다른 역할 worktree의 미커밋 경로 -- 주인에게 허용된 base_check.json은 통과, 주인에게도 안 되는 엔진 소스는 거부(D-7)
# 기대 근거: spec card 20260921-gate-flow-liveness 계약 1(D-7), design 05 §7 '다른 역할의 worktree' 문장, §12-3(base_check.json 미커밋), oracle (a)
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
rt flow-step code 20260921-rt-rg
# §12-3: auditor가 base 대비 확인 결과를 audit worktree에 커밋 없이 둔다
rt write '@{AUDITWT}/.ai/verification/20260921-rt-rg/base_check.json' --jtext '"{\"id\": \"20260921-rt-rg\", \"red\": \"rt\"}\n"'
