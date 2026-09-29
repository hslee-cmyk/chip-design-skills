#!/usr/bin/env bash
# 공격 22: gate 훼손(pre-receive 덮어쓰기·master 직접 이동·accept-log 덧붙이기·비우기·core.hooksPath·재판정 통과 캐시에 위조 구간 기재) (드러내는 증거, installed 전용)
# 기대 근거: 05 §13.2 #22, §3.3 무결성 대조 행 1~4(행 3(나) 2026-09-29 개정), §13.5 review31 N-06, N3.12.0 '드러나게 한다'
# (f)는 두 형태: 마지막 줄 위조 구간(f-skip-cache-file, 대조 실패 기대) / 마지막이 아닌 위조 구간(f-skip-cache-file-nonlast, 알려진 한계 기록).
# 행 3(나) 캐시 동작의 direct 재생은 공격 30(30-rejudge-cache)이다.
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt not-implemented attack
