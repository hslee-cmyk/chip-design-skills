#!/usr/bin/env bash
# 공격 27f: 진입점 16개에 reconfigure를 감싼 `except Exception: pass`가 없다(V6 관찰)
# 기대 근거: spec card 20260921-gate-flow-liveness 계약 6(V6 관찰: `try: …reconfigure… except Exception: pass`를 광범위 except 없이), 진입점 16개 목록 = spec card 20260921-gate-output-utf8 '관찰 가능한 계약', 출력 계약은 공격 26이 계속 본다, oracle (a)(ast 구조 검사 -- 실행 출력에서 기대를 만들지 않는다)
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt ast-broad-except v6obs-role-guard --script hooks/role_guard.py
rt ast-broad-except v6obs-role-diff-guard-bash --script hooks/role_diff_guard_bash.py
rt ast-broad-except v6obs-role-diff-guard-stop --script hooks/role_diff_guard_stop.py
rt ast-broad-except v6obs-role-session-start --script hooks/role_session_start.py
rt ast-broad-except v6obs-gmid-gate --script tools/gates/githooks/gmid_gate.py
rt ast-broad-except v6obs-gate-runner --script tools/gates/gate/gate-runner.py
rt ast-broad-except v6obs-integrity --script tools/gates/integrity.py
rt ast-broad-except v6obs-merge-gate --script tools/gates/merge_gate.py
rt ast-broad-except v6obs-role-commit-gate --script tools/gates/role_commit_gate.py
rt ast-broad-except v6obs-interface-card --script tools/gates/interface_card.py
rt ast-broad-except v6obs-weakening-diff --script tools/gates/weakening_diff.py
rt ast-broad-except v6obs-test-lint --script tools/gates/test_lint.py
rt ast-broad-except v6obs-source-lint --script tools/gates/source_lint.py
rt ast-broad-except v6obs-reachability --script tools/gates/reachability.py
rt ast-broad-except v6obs-mutate-changed --script tools/gates/mutate_changed.py
rt ast-broad-except v6obs-import-layering --script tools/gates/import_layering.py
