#!/usr/bin/env bash
# 공격 19 (c): 조상에서 갈라진 문서 커밋을 둘째 부모로 둔 병합 -- test 삭제·엔진 되돌림·gate_config.json 삭제
# 기대 근거: 05 §13.2 #19, review30 A19b, §8.2-3 (라)(3), §9.2-3
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt el3 attack-el3 --kind attack --cwd '@{SB}/m' --msg 'merge doc\n\nRole: doc'
rt git '@{SB}/m' commit -q -m 'merge doc' --trailer 'Role: doc'
rt el4 attack-el4 --kind attack --old '@{B1}' --new rt19/m
