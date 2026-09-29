#!/usr/bin/env bash
# 공격 30: 행 3(나) 재판정 통과 캐시 `rejudged` -- 통과 구간 기록, 마지막이 아닌 캐시 구간 건너뜀, 마지막 줄은 항상 재판정, 실패·깨진 줄·로그 밖 쌍 제외
# 기대 근거: spec card 20260929-rejudge-cache '관찰 가능한 계약' 1~8, '거부해야 할 입력', '무동작 판정 입력', design 05 §3.3 행 3(나)(2026-09-29 개정)·§13.2 #22 (f)·§13.5 N-06, oracle (a)
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
#
# 구성(정답이 구성으로 정해지는 합성 입력):
#   B0 (sandbox 기준 커밋, accept-log 첫 줄 B0 B0)
#   C1 = B0 + 역할 밖 경로(rtl/core.v)만 바꾼 트레일러 없는 커밋 -> 재판정 통과(05 §13.2 #10b: 역할 밖 = 판정 트리 밖, 트레일러 없는 역할 밖 커밋 push 통과)
#   F  = C1 + 엔진 소스(assets/rt_engine.py)를 바꾼 트레일러 없는 커밋 -> 재판정 실패(05 §8.2-2·§9.2: 트레일러 없는 판정 트리 커밋은 EL4 거부) = 위조 구간
#   C3 = F + 역할 밖 경로만 바꾼 트레일러 없는 커밋 -> 재판정 통과(C1과 같은 근거)
# 커밋은 commit-tree로 만든다(hook 없음). gate master 이동·accept-log 덧붙이기는 공격 22 (b)(c) 형태(같은 계정의 직접 조작)다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt sandbox
rt mkcommit --parent '@{B0}' --file 'rtl/core.v="module core;\n// rt 30 c1\nendmodule\n"' --msg '"rt 30 c1: 역할 밖 경로만"' --save C1
rt mkcommit --parent '@{C1}' --file 'skills/analog-gmid-design/assets/rt_engine.py="def rt_gain(gm, ro):\n    return 0.0\n"' --msg '"rt 30 forged: 트레일러 없는 엔진 소스 변경"' --save F
rt mkcommit --parent '@{F}' --file 'rtl/core.v="module core;\n// rt 30 c3\nendmodule\n"' --msg '"rt 30 c3: 역할 밖 경로만"' --save C3
# 첫 구성: 로그 B0 B0 / B0 C1 / C1 F, gate master = F(위조 구간이 마지막 줄)
rt advance '@{F}'
rt write '@{GATE}/gmid-accept-log' --append --jtext '"@{B0} @{C1} 2026-09-29T10:00:00\n@{C1} @{F} 2026-09-29T10:01:00\n"'
