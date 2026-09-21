#!/usr/bin/env bash
# 공격 17: 후보 대조 -- 고정 pytest 판 locate_config의 config_names가 모두 판정 환경 파일 이름
# 기대 근거: 05 §13.2 #17 '후보 대조'(review31 N-05, review32 M-08), §9.2-10
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt pytest-candidates candidates
