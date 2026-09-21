#!/usr/bin/env bash
# 공격 10: 메인 세션 Edit / PowerShell Set-Content / general-purpose agent Edit (엔진 소스)
# 기대 근거: 05 §13.2 #10(EL1 exit 2), §5 오케스트레이터 판정 범위(overlaps_any), N3.12.1(오케스트레이터는 엔진 소스 쓰기 불가)
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt sandbox
