#!/usr/bin/env bash
# 공격 19 (e): 역할 밖 병합(오래된 조상에서 갈라진 RTL 브랜치 포함) -- 통과
# 기대 근거: 05 §13.2 #19 (e), §8.2-3 (라), §9.2-3
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt el3 control-el3 --kind control --cwd '@{SB}/m' --msg 'merge rtl'
rt git '@{SB}/m' commit -q -m 'merge rtl'
rt el4 control-el4 --kind control --old '@{B1}' --new rt19/m
