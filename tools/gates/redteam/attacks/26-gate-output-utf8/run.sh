#!/usr/bin/env bash
# 공격 26: 게이트 진입점 16개를 PYTHONIOENCODING=cp949 / 인코딩 변수 없는 환경에서 파이프 실행 -- 출력 전체 UTF-8, 한글 유지, exit 불변
# 기대 근거: spec card 20260921-gate-output-utf8 '관찰 가능한 계약' 1~4, '거부해야 할 입력', oracle (a)
# run_all.py가 넣는 PYTHONIOENCODING=utf-8을 `rt enc --env`가 단계마다 덮어쓰거나(cp949) 지운다(unset) -- 이 결함을 가린 변수다.
# 관찰값(strict UTF-8 디코드, 한글 음절, JSON 줄)은 lib/rt.py a_enc가 바이트에서 구해 steps.jsonl의 observed에 남긴다.
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt enc el1-main-write-engine-cp949 --env cp949 --script hooks/role_guard.py --event PreToolUse --agent none --tool Write --input-file inputs/main-write-engine.json
rt enc el1-main-write-engine-unset --env unset --script hooks/role_guard.py --event PreToolUse --agent none --tool Write --input-file inputs/main-write-engine.json
rt enc el1-unknown-gmid-agent-cp949 --env cp949 --script hooks/role_guard.py --event PreToolUse --agent gmid-rt-unknown --tool Write --input-file inputs/unknown-gmid-write-doc.json
rt enc el1-unknown-gmid-agent-unset --env unset --script hooks/role_guard.py --event PreToolUse --agent gmid-rt-unknown --tool Write --input-file inputs/unknown-gmid-write-doc.json
rt enc el1-fail-closed-cp949 --env cp949 --script hooks/role_guard.py --stdin-text '"rt not json {"'
rt enc el1-fail-closed-unset --env unset --script hooks/role_guard.py --stdin-text '"rt not json {"'
rt enc el2bash-unknown-gmid-agent-cp949 --env cp949 --script hooks/role_diff_guard_bash.py --event PostToolUse --agent gmid-rt-unknown --tool Bash --input-file inputs/bash-echo.json
rt enc el2bash-unknown-gmid-agent-unset --env unset --script hooks/role_diff_guard_bash.py --event PostToolUse --agent gmid-rt-unknown --tool Bash --input-file inputs/bash-echo.json
rt enc el2bash-fail-closed-cp949 --env cp949 --script hooks/role_diff_guard_bash.py --stdin-text '"rt not json {"'
rt enc el2bash-fail-closed-unset --env unset --script hooks/role_diff_guard_bash.py --stdin-text '"rt not json {"'
rt enc el2stop-unknown-gmid-agent-cp949 --env cp949 --script hooks/role_diff_guard_stop.py --event SubagentStop --agent gmid-rt-unknown
rt enc el2stop-unknown-gmid-agent-unset --env unset --script hooks/role_diff_guard_stop.py --event SubagentStop --agent gmid-rt-unknown
rt enc el2stop-fail-closed-cp949 --env cp949 --script hooks/role_diff_guard_stop.py --stdin-text '"rt not json {"'
rt enc el2stop-fail-closed-unset --env unset --script hooks/role_diff_guard_stop.py --stdin-text '"rt not json {"'
rt enc session-startup-cp949 --env cp949 --script hooks/role_session_start.py --event SessionStart
rt enc session-startup-unset --env unset --script hooks/role_session_start.py --event SessionStart
rt enc session-fail-closed-cp949 --env cp949 --script hooks/role_session_start.py --stdin-text '"rt not json {"'
rt enc session-fail-closed-unset --env unset --script hooks/role_session_start.py --stdin-text '"rt not json {"'
rt enc gmid-gate-unknown-hook-cp949 --env cp949 --script tools/gates/githooks/gmid_gate.py --arg rt-unknown-hook
rt enc gmid-gate-unknown-hook-unset --env unset --script tools/gates/githooks/gmid_gate.py --arg rt-unknown-hook
rt enc gate-runner-direct-cp949 --env cp949 --script tools/gates/gate/gate-runner.py --cwd '@{GATE}' --stdin-text '"0000000000000000000000000000000000000000 1111111111111111111111111111111111111111 refs/heads/master\n"'
rt enc gate-runner-direct-unset --env unset --script tools/gates/gate/gate-runner.py --cwd '@{GATE}' --stdin-text '"0000000000000000000000000000000000000000 1111111111111111111111111111111111111111 refs/heads/master\n"'
rt enc integrity-check-session-cp949 --env cp949 --script tools/gates/integrity.py --arg check --arg=--scope --arg session
rt enc integrity-check-session-unset --env unset --script tools/gates/integrity.py --arg check --arg=--scope --arg session
rt enc merge-gate-bad-old-cp949 --env cp949 --script tools/gates/merge_gate.py --cwd '@{GATE}' --arg receive --arg=--old --arg rtbad1 --arg=--new --arg rtbad2
rt enc merge-gate-bad-old-unset --env unset --script tools/gates/merge_gate.py --cwd '@{GATE}' --arg receive --arg=--old --arg rtbad1 --arg=--new --arg rtbad2
rt enc role-commit-gate-usage-cp949 --env cp949 --script tools/gates/role_commit_gate.py
rt enc role-commit-gate-usage-unset --env unset --script tools/gates/role_commit_gate.py
rt enc interface-card-missing-spec-cp949 --env cp949 --script tools/gates/interface_card.py --arg docs/02-design/specs/rt-missing.spec.md
rt enc interface-card-missing-spec-unset --env unset --script tools/gates/interface_card.py --arg docs/02-design/specs/rt-missing.spec.md
rt enc v5-bad-revisions-cp949 --env cp949 --script tools/gates/weakening_diff.py --arg=--root --arg '@{WORK}' --arg=--base --arg rtbad1 --arg=--head --arg rtbad2
rt enc v5-bad-revisions-unset --env unset --script tools/gates/weakening_diff.py --arg=--root --arg '@{WORK}' --arg=--base --arg rtbad1 --arg=--head --arg rtbad2
rt enc v4-bad-revisions-cp949 --env cp949 --script tools/gates/test_lint.py --arg=--root --arg '@{WORK}' --arg=--base --arg rtbad1 --arg=--head --arg rtbad2
rt enc v4-bad-revisions-unset --env unset --script tools/gates/test_lint.py --arg=--root --arg '@{WORK}' --arg=--base --arg rtbad1 --arg=--head --arg rtbad2
rt enc v6-bad-revisions-cp949 --env cp949 --script tools/gates/source_lint.py --arg=--root --arg '@{WORK}' --arg=--base --arg rtbad1 --arg=--head --arg rtbad2
rt enc v6-bad-revisions-unset --env unset --script tools/gates/source_lint.py --arg=--root --arg '@{WORK}' --arg=--base --arg rtbad1 --arg=--head --arg rtbad2
rt enc v7-bad-revisions-cp949 --env cp949 --script tools/gates/reachability.py --arg=--root --arg '@{WORK}' --arg=--base --arg rtbad1 --arg=--head --arg rtbad2
rt enc v7-bad-revisions-unset --env unset --script tools/gates/reachability.py --arg=--root --arg '@{WORK}' --arg=--base --arg rtbad1 --arg=--head --arg rtbad2
rt enc v3-bad-revisions-cp949 --env cp949 --script tools/gates/mutate_changed.py --arg=--root --arg '@{WORK}' --arg=--base --arg rtbad1 --arg=--head --arg rtbad2 --arg=--pytest-ini --arg '@{WORK}/tools/gates/pytest_gate.ini'
rt enc v3-bad-revisions-unset --env unset --script tools/gates/mutate_changed.py --arg=--root --arg '@{WORK}' --arg=--base --arg rtbad1 --arg=--head --arg rtbad2 --arg=--pytest-ini --arg '@{WORK}/tools/gates/pytest_gate.ini'
rt enc import-layering-plan-without-section-cp949 --env cp949 --script tools/gates/import_layering.py --arg=--root --arg '@{WORK}' --arg=--plan --arg '@{WORK}/docs/02-design/rt-notes.md'
rt enc import-layering-plan-without-section-unset --env unset --script tools/gates/import_layering.py --arg=--root --arg '@{WORK}' --arg=--plan --arg '@{WORK}/docs/02-design/rt-notes.md'
