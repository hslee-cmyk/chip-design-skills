#!/usr/bin/env bash
# 공격 19 (g): 부모 셋 이상인 역할 밖 병합
# 기대 근거: 05 §13.2 #19 (g), review32 M-07, §8.2-3 (라)(1), §9.2-3
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt el3 attack-el3 --kind attack --cwd '@{SB}/m' --msg octopus
rt git '@{SB}/m' commit -q -m octopus
rt el4 attack-el4 --kind attack --old '@{B1}' --new rt19/m
