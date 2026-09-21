#!/usr/bin/env bash
# 공격 19 (f): 조상 위에서 merge --no-ff -s ours master 뒤 --ff-only(부모를 뒤집은 되돌림 병합)
# 기대 근거: 05 §13.2 #19 (f), review32 M-01, §8.2-3 (라)(2), §9.2-3
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
rt git '@{WORK}' worktree add -q '@{SB}/f' -b rt19/f '@{B0}'
rt git '@{SB}/f' merge --no-ff --no-commit -s ours gate/master
