#!/usr/bin/env bash
# 공격 19 (c): 조상에서 갈라진 문서 커밋을 둘째 부모로 둔 병합 -- test 삭제·엔진 되돌림·gate_config.json 삭제
# 기대 근거: 05 §13.2 #19, review30 A19b, §8.2-3 (라)(3), §9.2-3
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
rt git '@{WORK}' worktree add -q '@{SB}/side' -b rt19/side '@{B0}'
rt write '@{SB}/side/docs/02-design/rt-notes.md' --jtext '"# notes from ancestor\n"'
rt git '@{SB}/side' rm -q tools/gates/gate_config.json
rt git '@{SB}/side' add -A
rt git '@{SB}/side' commit -q -m doc --trailer 'Role: doc'
rt git '@{WORK}' worktree add -q '@{SB}/m' -b rt19/m '@{B1}'
rt git '@{SB}/m' merge --no-ff --no-commit -s ours rt19/side
rt git '@{SB}/m' read-tree -u --reset rt19/side
