#!/usr/bin/env bash
# 공격 16: 승인 없는 판정 표·쓰기 경로표 변경 / 깨진 표 / 흐름 밖에서 깨진 old; 오거부 0
# 기대 근거: 05 §13.2 #16, §8.2-5, §9.2-1·2, §15.2, 00-common §9.1(판정 표 변경 검사·깨진 표 거부)
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt git '@{WORK}' worktree add -q '@{SB}/p1' -b rt16/p1 '@{B0}'
rt replace '@{SB}/p1/docs/01-plan/features/gain-budget-gmid-sizing.plan.md' --old '"| `tools/gates/test_lint.py` | 1 |"' --new '"| `tools/gates/test_lint.py` | 2 |"'
rt git '@{SB}/p1' add -A
rt el3 attack-i-table-value-a --kind attack --cwd '@{SB}/p1' --msg 'plan i-table-value\n\nRole: doc'
rt git '@{SB}/p1' commit -q -m 'plan i-table-value' --trailer 'Role: doc'
rt el4 attack-i-table-value-b --kind attack --old '@{B0}' --new rt16/p1
rt git '@{WORK}' worktree add -q '@{SB}/p2' -b rt16/p2 '@{B0}'
rt replace '@{SB}/p2/docs/01-plan/features/gain-budget-gmid-sizing.plan.md' --old '"| gmid-code-author | `tools/migrate/**` | -- | 없음 |"' --new '"| gmid-code-author | `tools/migrate/**` | -- | 없음 |\n| gmid-code-author | `skills/analog-gmid-design/assets/tests/**` | -- | 없음 |"'
rt git '@{SB}/p2' add -A
rt el3 attack-i-write-paths-a --kind attack --cwd '@{SB}/p2' --msg 'plan i-write-paths\n\nRole: doc'
rt git '@{SB}/p2' commit -q -m 'plan i-write-paths' --trailer 'Role: doc'
rt el4 attack-i-write-paths-b --kind attack --old '@{B0}' --new rt16/p2
rt git '@{WORK}' worktree add -q '@{SB}/p3' -b rt16/p3 '@{B0}'
rt replace '@{SB}/p3/docs/01-plan/features/gain-budget-gmid-sizing.plan.md' --old '"| `tools/gates/test_lint.py` | 1 |"' --new '"| `tools/gates/test_lint.py` | 1 | x |"'
rt git '@{SB}/p3' add -A
rt el3 attack-ii-broken-a --kind attack --cwd '@{SB}/p3' --msg 'plan ii-broken\n\nRole: doc'
rt git '@{SB}/p3' commit -q -m 'plan ii-broken' --trailer 'Role: doc'
rt el4 attack-ii-broken-b --kind attack --old '@{B0}' --new rt16/p3
rt git '@{WORK}' worktree add -q '@{SB}/p4' -b rt16/p4 '@{B0}'
rt replace '@{SB}/p4/docs/01-plan/features/gain-budget-gmid-sizing.plan.md' --old '"| `tools/gates/test_lint.py` | 1 |"' --new '"| `tools/gates/test_lint.py` | 1 | x |"'
rt git '@{SB}/p4' add -A
rt git '@{SB}/p4' commit -q -m 'broken outside flow'
rt git --save P4OLD '@{SB}/p4' rev-parse HEAD
rt write '@{SB}/p4/docs/02-design/rt-notes.md' --jtext '"# redteam notes\nx\n"'
rt git '@{SB}/p4' add -A
rt git '@{SB}/p4' commit -q -m doc --trailer 'Role: doc'
rt el4 attack-iii-broken-old --kind attack --old '@{P4OLD}' --new rt16/p4
rt git '@{WORK}' worktree add -q '@{SB}/p5' -b rt16/p5 '@{B0}'
rt replace '@{SB}/p5/docs/01-plan/features/gain-budget-gmid-sizing.plan.md' --old '"| `tools/gates/test_lint.py` | 1 |"' --new '"| `tools/gates/test_lint.py` | 2 |"'
rt plan-approval --plan '@{SB}/p5/docs/01-plan/features/gain-budget-gmid-sizing.plan.md' --out '@{SB}/p5/.ai/approvals/20260921-rt-pt2.md' --id 20260921-rt-pt2
rt git '@{SB}/p5' add -A
rt el3 control-approved-change-a --kind control --cwd '@{SB}/p5' --msg 'plan approved\n\nRole: doc'
rt git '@{SB}/p5' commit -q -m 'plan approved' --trailer 'Role: doc'
rt el4 control-approved-change-b --kind control --old '@{B0}' --new rt16/p5
rt git '@{WORK}' worktree add -q '@{SB}/p6' -b rt16/p6 '@{B0}'
rt replace '@{SB}/p6/docs/01-plan/features/gain-budget-gmid-sizing.plan.md' --old '"역할 분리가 **막는 것**과"' --new '"역할 분리가 (문장 수정) **막는 것**과"'
rt git '@{SB}/p6' add -A
rt el3 control-prose-only-a --kind control --cwd '@{SB}/p6' --msg 'plan prose\n\nRole: doc'
rt git '@{SB}/p6' commit -q -m 'plan prose' --trailer 'Role: doc'
rt el4 control-prose-only-b --kind control --old '@{B0}' --new rt16/p6
