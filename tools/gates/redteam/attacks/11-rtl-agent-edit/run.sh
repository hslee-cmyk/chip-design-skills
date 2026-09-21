#!/usr/bin/env bash
# 공격 11: RTL agent가 RTL 파일 Edit -- hook 출력 없음, exit 0
# 기대 근거: 05 §13.2 #11(installed 전용), N4.3 #11
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt not-implemented attack
