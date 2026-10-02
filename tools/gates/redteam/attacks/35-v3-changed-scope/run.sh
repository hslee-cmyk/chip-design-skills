#!/usr/bin/env bash
# 공격 35: V3 대상이 해시가 바뀐 기존 def의 바뀐 문장과 그 주변으로 좁혀지고, 대상 밖 변이는 실행하지 않고 not_targeted로 싣는다
# 기대 근거: spec card 20260930-v3-changed-stmt-scope 계약 1~6·8·9, oracle (a)(구성으로 정답이 정해진 합성 저장소 -- 단계마다
# base def -> head def 한 곳만 바꾸고, 계약 1을 손으로 적용한 대상 변이 중 X가 유일 생존(attack)이거나 대상 생존 0(control))
# 합성 저장소는 lib/rt.py build_vrepo가 $WORK 아래에 실행 중 만든다. (a)·(k)는 "observe": "out_jsonl"로 도구 --out 기록을 관찰한다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt vcase v.json
