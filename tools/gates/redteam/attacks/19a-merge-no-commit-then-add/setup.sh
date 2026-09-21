#!/usr/bin/env bash
# 공격 19 (a): merge --no-commit 뒤 내용 추가
# 기대 근거: 05 §13.2 #19, §8.2-3 (다) staged 트리 = MERGE_HEAD 트리, §9.2-4 ③ 트리 = M^2 트리
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
rt flow-step start 20260921-rt-rg
rt flow-step test 20260921-rt-rg
rt flow-step code 20260921-rt-rg
rt flow-step merge 20260921-rt-rg --no-commit
