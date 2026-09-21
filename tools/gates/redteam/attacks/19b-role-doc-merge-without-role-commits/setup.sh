#!/usr/bin/env bash
# 공격 19 (b): 역할 커밋 없는 Role: doc 병합(review29 G9)
# 기대 근거: 05 §13.2 #19, §8.2-3 (나)(라), §9.2-3·4
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt sandbox
rt write '@{WORK}/skills/analog-gmid-design/assets/tests/test_rt_b1.py' --jtext '"def test_b1():\n    assert 2 + 2 == 4\n"'
rt write '@{WORK}/skills/analog-gmid-design/assets/rt_engine.py' --append --jtext '"\n\ndef rt_b1():\n    return 0\n"'
rt git '@{WORK}' add -A
rt git '@{WORK}' commit -q -m 'B1 (준비: gate master 전진)' --trailer 'Role: user'
rt git --save B1 '@{WORK}' rev-parse HEAD
rt advance '@{B1}'
rt git '@{WORK}' worktree add -q '@{SB}/side' -b rt19/side '@{B1}'
rt write '@{SB}/side/skills/analog-gmid-design/assets/rt_engine.py' --append --jtext '"# side change\n"'
rt git '@{SB}/side' add -A
rt git '@{SB}/side' commit -q -m side --trailer 'Role: doc'
rt git '@{WORK}' worktree add -q '@{SB}/m' -b rt19/m '@{B1}'
rt git '@{SB}/m' merge --no-ff --no-commit rt19/side
