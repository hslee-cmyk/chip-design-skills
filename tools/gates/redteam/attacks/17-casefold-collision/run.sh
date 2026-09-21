#!/usr/bin/env bash
# 공격 17 (review33): casefold하면 기존 경로와 같아지는 `Skills/…` 경로를 더하는 커밋
# 기대 근거: 05 §4.1 'EL3·EL4는 casefold 충돌 경로를 더하는 커밋을 거부', §13.2 #17
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt el3 control-code-commit --kind control --cwd '@{CODEWT}' --msg 'code 20260921-rt-rg\n\nRole: code\nChange-Id: 20260921-rt-rg'
rt write '@{SB}/shadow.py' --jtext '"def rt_gain(gm, ro):\n    return 0\n"'
rt git --save SHBLOB '@{CODEWT}' hash-object -w '@{SB}/shadow.py'
rt git '@{CODEWT}' update-index --add --cacheinfo '100644,@{SHBLOB},Skills/analog-gmid-design/assets/rt_engine.py'
rt el3 attack-el3 --kind attack --cwd '@{CODEWT}' --msg 'code 20260921-rt-rg\n\nRole: code\nChange-Id: 20260921-rt-rg'
rt git '@{CODEWT}' commit -q -m code --trailer 'Role: code' --trailer 'Change-Id: 20260921-rt-rg'
rt flow-step merge 20260921-rt-rg
rt flow-step audit 20260921-rt-rg --et red-green
rt el4 attack-el4 --kind attack --old '@{20260921-rt-rg.OLD}' --new '@{20260921-rt-rg.NEW}'
