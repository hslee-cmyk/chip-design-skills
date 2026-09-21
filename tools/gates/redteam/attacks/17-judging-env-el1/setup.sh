#!/usr/bin/env bash
# 공격 17 (EL1): 판정 환경 파일·판정 트리 기본 거부 대상의 도구 쓰기
# 기대 근거: 05 §13.2 #17, §4.1 '판정 환경 행 우선'·'판정 트리 기본 거부'·casefold, 계획 N3.12.2
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt sandbox
rt flow-step start 20260921-rt-rg
rt flow-step test 20260921-rt-rg
rt flow-step worktrees 20260921-rt-rg
rt set CODEWT '@{W}/20260921-rt-rg-code'
rt set TESTWT '@{W}/20260921-rt-rg-test'
rt set AUDITWT '@{W}/20260921-rt-rg-audit'
