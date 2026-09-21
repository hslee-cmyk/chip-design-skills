#!/usr/bin/env bash
# 공격 19 (a): merge --no-commit 뒤 내용 추가
# 기대 근거: 05 §13.2 #19, §8.2-3 (다) staged 트리 = MERGE_HEAD 트리, §9.2-4 ③ 트리 = M^2 트리
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt el3 control-clean-merge-state --kind control --cwd '@{W}/20260921-rt-rg-audit' --msg 'merge 20260921-rt-rg\n\nRole: doc\nChange-Id: 20260921-rt-rg'
rt write '@{W}/20260921-rt-rg-audit/skills/analog-gmid-design/assets/rt_engine.py' --append --jtext '"# smuggled after merge\n"'
rt git '@{W}/20260921-rt-rg-audit' add -A
rt el3 attack-el3 --kind attack --cwd '@{W}/20260921-rt-rg-audit' --msg 'merge 20260921-rt-rg\n\nRole: doc\nChange-Id: 20260921-rt-rg'
rt git '@{W}/20260921-rt-rg-audit' commit -q -m 'merge 20260921-rt-rg' --trailer 'Role: doc' --trailer 'Change-Id: 20260921-rt-rg'
rt git --save 20260921-rt-rg.M '@{W}/20260921-rt-rg-audit' rev-parse HEAD
rt flow-step audit 20260921-rt-rg --et red-green
rt el4 attack-el4 --kind attack --old '@{20260921-rt-rg.OLD}' --new '@{20260921-rt-rg.NEW}'
