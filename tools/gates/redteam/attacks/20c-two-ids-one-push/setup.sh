#!/usr/bin/env bash
# 공격 20 (c): 한 push에 Change-Id 둘
# 기대 근거: 05 §13.2 #20 (c), §9.2-4 'Change-Id는 정확히 하나'
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt sandbox
rt flow rg
rt flow rg2 --base '@{20260921-rt-rg.NEW}'
