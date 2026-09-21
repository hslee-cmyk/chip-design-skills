#!/usr/bin/env bash
# 공격 5: commit-tree로 만든 커밋 push(트레일러 없음 / Role: code가 .ai/approvals 추가)
# 기대 근거: 05 §13.2 #5(EL4 거부), §9.2-3
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt mkcommit --parent '@{B0}' --file 'skills/analog-gmid-design/assets/rt_engine.py="def rt_gain(gm, ro):\n    return 0\n"' --msg '"no trailer\n"' --save C5A
rt el4 attack-no-trailer --kind attack --old '@{B0}' --new '@{C5A}'
rt mkcommit --parent '@{B0}' --file '.ai/approvals/x.md="x\n"' --msg '"x\n\nRole: code\nChange-Id: 20260921-rt-rg\n"' --save C5B
rt el4 attack-role-code-approvals --kind attack --old '@{B0}' --new '@{C5B}'
rt mkcommit --parent '@{B0}' --file 'rtl/core.v="module core2;\nendmodule\n"' --msg '"rtl only\n"' --save C5C
rt el4 control-role-outside-commit-tree --kind control --old '@{B0}' --new '@{C5C}'
