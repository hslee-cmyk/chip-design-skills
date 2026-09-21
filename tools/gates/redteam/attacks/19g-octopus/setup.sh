#!/usr/bin/env bash
# 공격 19 (g): 부모 셋 이상인 역할 밖 병합
# 기대 근거: 05 §13.2 #19 (g), review32 M-07, §8.2-3 (라)(1), §9.2-3
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
rt git '@{WORK}' worktree add -q '@{SB}/g1' -b rt19/g1 '@{B1}'
rt write '@{SB}/g1/rtl/a.v' --jtext '"module a;\nendmodule\n"'
rt git '@{SB}/g1' add -A
rt git '@{SB}/g1' commit -q -m a
rt git '@{WORK}' worktree add -q '@{SB}/g2' -b rt19/g2 '@{B1}'
rt write '@{SB}/g2/rtl/b.v' --jtext '"module b;\nendmodule\n"'
rt git '@{SB}/g2' add -A
rt git '@{SB}/g2' commit -q -m b
rt git '@{WORK}' worktree add -q '@{SB}/m' -b rt19/m '@{B1}'
rt git '@{SB}/m' merge --no-ff --no-commit rt19/g1 rt19/g2
