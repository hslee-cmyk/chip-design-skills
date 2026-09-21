#!/usr/bin/env bash
# 공격 26: 게이트 진입점 출력 인코딩(cp949·로캘 기본 환경의 파이프 실행)
# 기대 근거: spec card 20260921-gate-output-utf8 '관찰 가능한 계약' 1~4, '거부해야 할 입력'
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt sandbox
