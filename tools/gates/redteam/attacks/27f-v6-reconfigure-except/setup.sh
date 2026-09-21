#!/usr/bin/env bash
# 공격 27f: 진입점 16개에 reconfigure를 감싼 `except Exception: pass`가 없다(V6 관찰)
# 기대 근거: spec card 20260921-gate-flow-liveness 계약 6(V6 관찰: `try: …reconfigure… except Exception: pass`를 광범위 except 없이), 진입점 16개 목록 = spec card 20260921-gate-output-utf8 '관찰 가능한 계약', 출력 계약은 공격 26이 계속 본다, oracle (a)(ast 구조 검사 -- 실행 출력에서 기대를 만들지 않는다)
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt sandbox
