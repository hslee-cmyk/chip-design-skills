#!/usr/bin/env bash
# 사례: NameError를 광범위 except로 삼킨 게이트(재구성 패치 -- ③ 사용자 확인 항목)
# 기대 근거: 05 §13.3 1b9b4ea (V6 FAIL). 원 커밋에 결함 코드 없음 -- 1b9b4ea 판 계획서 §'게이트를 만들자마자…'의 코드 블록대로 재구성
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt vcase v.json
