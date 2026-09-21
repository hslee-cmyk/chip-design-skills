#!/usr/bin/env bash
# 공격 19 (b): 역할 커밋 없는 Role: doc 병합(review29 G9)
# 기대 근거: 05 §13.2 #19, §8.2-3 (나)(라), §9.2-3·4
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt el3 attack-el3 --kind attack --cwd '@{SB}/m' --msg 'merge 20260921-rt-rg\n\nRole: doc\nChange-Id: 20260921-rt-rg'
rt git '@{SB}/m' commit -q -m 'merge' --trailer 'Role: doc' --trailer 'Change-Id: 20260921-rt-rg'
rt el4 attack-el4 --kind attack --old '@{B1}' --new rt19/m
