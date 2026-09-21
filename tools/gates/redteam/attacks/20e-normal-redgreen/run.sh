#!/usr/bin/env bash
# 공격 20 (e): 세 역할 정상 종료 -- red-green (오거부 0)
# 기대 근거: 05 §13.2 #20 (e), §7 SubagentStop 범위(review30 E2, review31 N-02, review33 M2-08), §9.2-4 표
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt flow-step start 20260921-rt-rg
rt flow-step test 20260921-rt-rg
rt hook control-test-author-stop --kind control --event SubagentStop --agent gmid-test-author
rt flow-step code 20260921-rt-rg
rt hook control-code-author-stop --kind control --event SubagentStop --agent gmid-code-author
rt flow-step merge 20260921-rt-rg
rt flow-step audit 20260921-rt-rg --et red-green
rt hook control-auditor-stop --kind control --event SubagentStop --agent gmid-verification-auditor
rt el4 control-el4 --kind control --old '@{20260921-rt-rg.OLD}' --new '@{20260921-rt-rg.NEW}'
