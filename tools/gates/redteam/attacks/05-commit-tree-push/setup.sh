#!/usr/bin/env bash
# 공격 5: commit-tree로 만든 커밋 push(트레일러 없음 / Role: code가 .ai/approvals 추가)
# 기대 근거: 05 §13.2 #5(EL4 거부), §9.2-3
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt sandbox
