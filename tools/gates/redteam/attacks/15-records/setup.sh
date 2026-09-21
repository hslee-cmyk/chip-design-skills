#!/usr/bin/env bash
# 공격 15: 판정 기록·승인 기록 형식 위반(EL4 로더 거부) / 올바른 기록 3종 통과 / staged_diff
# 기대 근거: 05 §13.2 #15·주석(review30 R-14), §9.2-5~9, §9.3, 00-common §8.1 로더 규칙 1~10·§8.2, 계획 N4.3 #15, review21 C-08·review22 §5·review23 §5 케이스
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt sandbox
