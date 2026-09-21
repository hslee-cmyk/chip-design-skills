#!/usr/bin/env bash
# 공격 17 (review33·34 로그 항목): 격리 실행이 복제본 부모의 pytest.ini·conftest.py, 루트의 merge_gate.py·pytest.py, 커밋된 .pyc를 읽지 않음
# 기대 근거: 05 §12-7, 00-common §8.1 red 수집 명령, §13.2 #17 '로그로'
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt isolated-run isolated
