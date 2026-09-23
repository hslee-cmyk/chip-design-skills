#!/usr/bin/env bash
# 공격 29: target_kind: decision 승인 기록으로 V4 규칙 (1) 면제(C13) -- 승인 밖은 그대로 적발
# 기대 근거: spec card 20260923-v4-decision-exempt 계약 1~4, oracle (a)(구성으로 정답이 정해진 합성 저장소 -- 합성 승인 기록은 실행 중 합성 저장소의 head 커밋에 쓴다, 커밋하지 않는다), 00-common §8.2 decision 머리, 05-role-separation §10 V4, 계획 N4.2 V4 (1)
# 합성 저장소(승인 기록 포함)는 lib/rt.py build_vrepo가 $WORK 아래에 실행 중 만든다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt vcase v.json
