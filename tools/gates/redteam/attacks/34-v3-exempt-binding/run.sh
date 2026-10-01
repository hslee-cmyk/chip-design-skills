#!/usr/bin/env bash
# 공격 34: V3 등가 변이 면제가 변이 id@def 묶기 해시에 묶인다 -- 해시 없음·다름·다른 def·docstring 밀림·형식 오류 원소는 적용하지 않고 exempt_ignored에 싣는다
# 기대 근거: spec card 20260930-v3-exempt-binding 계약 1~6·9, oracle (a)(구성으로 정답이 정해진 합성 저장소 -- X = rt_engine:rt_scale:stmt_delete:body[1]가 rt_scale 대상 변이 중 유일 생존인 def와 test, 합성 decision 승인 기록은 V 케이스 base/head 사전의 파일, 묶기 해시는 lib/rt.py @bindhash가 계약 머리 정의로 독립 계산)
# 합성 저장소(승인 기록 포함)는 lib/rt.py build_vrepo가 $WORK 아래에 실행 중 만든다. 원소의 해시는 @bindhash(<base|head>:<경로>:<qualname>) 자리표시자로
# build_vrepo 둘째 단계에서 넣는다. bound-exempt 단계는 "observe": "out_jsonl"로 도구 --out 기록을 관찰한다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt vcase v.json
