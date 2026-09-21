#!/usr/bin/env bash
# 공격 23: V4 (2) 판정 경계 -- probe 67 케이스·누적 회귀 코퍼스 94·실제 엔진 전수
# 기대 근거: 05 §13.2 #23, §10 V4 실측(v4_rule_probe, 고정 커밋 4fd0fd8의 blob을 읽는다 -- 복사하지 않는다)
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt v4probe
