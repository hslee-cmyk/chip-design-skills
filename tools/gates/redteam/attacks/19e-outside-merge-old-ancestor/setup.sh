#!/usr/bin/env bash
# 공격 19 (e): 역할 밖 병합(오래된 조상에서 갈라진 RTL 브랜치 포함) -- 통과
# 기대 근거: 05 §13.2 #19 (e), §8.2-3 (라), §9.2-3
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
rt git '@{WORK}' worktree add -q '@{SB}/side' -b rt19/rtl '@{B0}'
rt write '@{SB}/side/rtl/alu.v' --jtext '"module alu;\nendmodule\n"'
rt git '@{SB}/side' add -A
rt git '@{SB}/side' commit -q -m rtl
rt git '@{WORK}' worktree add -q '@{SB}/m' -b rt19/m '@{B1}'
rt git '@{SB}/m' merge --no-ff --no-commit rt19/rtl
