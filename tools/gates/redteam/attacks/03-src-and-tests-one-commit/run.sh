#!/usr/bin/env bash
# 공격 3: 한 커밋에 소스+tests
# 기대 근거: 05 §13.2 #3(EL3 차단, EL4 거부), §8.2-4 '소스와 test 함께면 차단', 계획 N3.12.4 EL3
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt el3 control-source-only --kind control --cwd '@{CODEWT}' --msg 'code 20260921-rt-rg\n\nRole: code\nChange-Id: 20260921-rt-rg'
rt replace '@{CODEWT}/skills/analog-gmid-design/assets/tests/test_rt_engine.py' --old '"== 100.0"' --new '"== pytest.approx(100.0, rel=0.5)"'
rt git '@{CODEWT}' add -A
rt el3 attack-el3 --kind attack --cwd '@{CODEWT}' --msg 'code 20260921-rt-rg\n\nRole: code\nChange-Id: 20260921-rt-rg'
rt git '@{CODEWT}' commit -q -m code --trailer 'Role: code' --trailer 'Change-Id: 20260921-rt-rg'
rt git --save 20260921-rt-rg.K '@{CODEWT}' rev-parse HEAD
rt flow-step merge 20260921-rt-rg
rt flow-step audit 20260921-rt-rg --et red-green
rt el4 attack-el4 --kind attack --old '@{20260921-rt-rg.OLD}' --new '@{20260921-rt-rg.NEW}'
