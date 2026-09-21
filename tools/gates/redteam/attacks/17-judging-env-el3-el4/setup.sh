#!/usr/bin/env bash
# 공격 17 (EL3·EL4): 트레일러 없는 커밋으로 넣은 판정 환경 파일·판정 트리 새 파일
# 기대 근거: 05 §13.2 #17 '트레일러 없는 커밋으로도 EL3 차단·EL4 거부', §4.1, 계획 N3.12.2
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt sandbox
