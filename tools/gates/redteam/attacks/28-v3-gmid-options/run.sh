#!/usr/bin/env bash
# 공격 28: V3 도구가 conftest의 --gmid-phase·--gmid-strict(인벤토리 표식 키만)를 넘긴다(C11)
# 기대 근거: spec card 20260922-v3-gmid-options 계약 1~4, design 10-test-separation §6.10 test (1)~(3), oracle (a)(구성으로 정답이 정해진 합성 저장소 -- 합성 conftest는 실행 중 합성 저장소에 쓴다, 커밋하지 않는다)
# 합성 저장소(conftest 포함)는 lib/rt.py build_vrepo가 $WORK 아래에 실행 중 만든다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt vcase v.json
