#!/usr/bin/env bash
# 공격 31: V3 도구가 test를 이력 있는 격리 복제본(origin 없음)에서 돌리고, 기준 실행 실패는 '생존'이 아니라 ERROR(exit 2)다(B28)
# 기대 근거: spec card 20260930-v3-history-clone 계약 1·2·3·5·7, oracle (a)(구성으로 정답이 정해진 합성 저장소 -- lib/rt.py build_vrepo의
# base 커밋 -> interface card 커밋 -> head 커밋 이력: root HEAD = --head, HEAD~1 = --base, 원격 없음)
# 합성 저장소는 lib/rt.py build_vrepo가 $WORK 아래에 실행 중 만든다. 도구의 임시 디렉터리는 v.json "tool_tmpdir"로 $WORK 아래 빈 디렉터리다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt vcase v.json
