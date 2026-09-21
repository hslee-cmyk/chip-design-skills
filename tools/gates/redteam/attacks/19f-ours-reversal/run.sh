#!/usr/bin/env bash
# 공격 19 (f): 조상 위에서 merge --no-ff -s ours master 뒤 --ff-only(부모를 뒤집은 되돌림 병합)
# 기대 근거: 05 §13.2 #19 (f), review32 M-01, §8.2-3 (라)(2), §9.2-3
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt el3 attack-el3 --kind attack --cwd '@{SB}/f' --msg 'merge master'
rt git '@{SB}/f' commit -q -m 'merge master'
rt el4 attack-el4 --kind attack --old '@{B1}' --new rt19/f
