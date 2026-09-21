#!/usr/bin/env bash
# 공격 20 (a): code-author가 Role: test·남의 Change-Id 커밋
# 기대 근거: 05 §13.2 #20 (a): EL1 거부, EL2(SubagentStop) 거부, EL4 거부. §6.2 커밋 트레일러, §7 SubagentStop, §9.2-4
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt hook control-el1 --kind control --event PreToolUse --agent gmid-code-author --tool Bash --input-file inputs/control-el1.json
rt hook attack-el1-role-test --kind attack --event PreToolUse --agent gmid-code-author --tool Bash --input-file inputs/attack-el1-role-test.json
rt hook attack-el1-other-id --kind attack --event PreToolUse --agent gmid-code-author --tool Bash --input-file inputs/attack-el1-other-id.json
rt write '@{CODEWT}/skills/analog-gmid-design/assets/rt_engine.py' --append --jtext '"# x\n"'
rt git '@{CODEWT}' add -A
rt git '@{CODEWT}' commit -q -m code --trailer 'Role: code' --trailer 'Change-Id: 20260921-rt-rg'
rt hook control-el2-stop --kind control --event SubagentStop --agent gmid-code-author
rt write '@{CODEWT}/skills/analog-gmid-design/assets/rt_engine.py' --append --jtext '"# y\n"'
rt git '@{CODEWT}' add -A
rt git '@{CODEWT}' commit -q -m code2 --trailer 'Role: test' --trailer 'Change-Id: 20260921-rt-rg'
rt hook attack-el2-stop --kind attack --event SubagentStop --agent gmid-code-author
rt flow rg2 --code-role test
rt el4 attack-el4-role-test --kind attack --old '@{20260921-rt-rg2.OLD}' --new '@{20260921-rt-rg2.NEW}'
rt flow rg2 --cid 20260921-rt-rg3 --et red-green --code-change-id 20260920-rt-other
rt el4 attack-el4-other-id --kind attack --old '@{20260921-rt-rg3.OLD}' --new '@{20260921-rt-rg3.NEW}'
