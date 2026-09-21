#!/usr/bin/env bash
# 공격 17 (EL1): 판정 환경 파일·판정 트리 기본 거부 대상의 도구 쓰기
# 기대 근거: 05 §13.2 #17, §4.1 '판정 환경 행 우선'·'판정 트리 기본 거부'·casefold, 계획 N3.12.2
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt hook attack-code-assets-conftest --kind attack --event PreToolUse --agent gmid-code-author --tool Write --input-file inputs/attack-code-assets-conftest.json
rt hook attack-code-root-conftest --kind attack --event PreToolUse --agent gmid-code-author --tool Write --input-file inputs/attack-code-root-conftest.json
rt hook attack-code-skills-conftest --kind attack --event PreToolUse --agent gmid-code-author --tool Write --input-file inputs/attack-code-skills-conftest.json
rt hook attack-code-skill-pytest-ini --kind attack --event PreToolUse --agent gmid-code-author --tool Write --input-file inputs/attack-code-skill-pytest-ini.json
rt hook attack-code-tests-tools-conftest --kind attack --event PreToolUse --agent gmid-code-author --tool Write --input-file inputs/attack-code-tests-tools-conftest.json
rt hook attack-code-sitecustomize --kind attack --event PreToolUse --agent gmid-code-author --tool Write --input-file inputs/attack-code-sitecustomize.json
rt hook attack-code-pth --kind attack --event PreToolUse --agent gmid-code-author --tool Write --input-file inputs/attack-code-pth.json
rt hook attack-code-gitattributes --kind attack --event PreToolUse --agent gmid-code-author --tool Write --input-file inputs/attack-code-gitattributes.json
rt hook attack-code-numpy-shadow-pkg --kind attack --event PreToolUse --agent gmid-code-author --tool Write --input-file inputs/attack-code-numpy-shadow-pkg.json
rt hook attack-code-eng-shadow-pkg --kind attack --event PreToolUse --agent gmid-code-author --tool Write --input-file inputs/attack-code-eng-shadow-pkg.json
rt hook attack-code-pyc --kind attack --event PreToolUse --agent gmid-code-author --tool Write --input-file inputs/attack-code-pyc.json
rt hook attack-code-workspaces-py --kind attack --event PreToolUse --agent gmid-code-author --tool Write --input-file inputs/attack-code-workspaces-py.json
rt hook attack-test-tests-pytest-ini --kind attack --event PreToolUse --agent gmid-test-author --tool Write --input-file inputs/attack-test-tests-pytest-ini.json
rt hook attack-test-tests-pytest-toml --kind attack --event PreToolUse --agent gmid-test-author --tool Write --input-file inputs/attack-test-tests-pytest-toml.json
rt hook attack-test-tests-dot-pytest-toml --kind attack --event PreToolUse --agent gmid-test-author --tool Write --input-file inputs/attack-test-tests-dot-pytest-toml.json
rt hook attack-test-tests-dot-pytest-ini --kind attack --event PreToolUse --agent gmid-test-author --tool Write --input-file inputs/attack-test-tests-dot-pytest-ini.json
rt hook attack-test-tests-Pytest-ini-case --kind attack --event PreToolUse --agent gmid-test-author --tool Write --input-file inputs/attack-test-tests-Pytest-ini-case.json
rt hook attack-test-tests-PYTEST-INI-case --kind attack --event PreToolUse --agent gmid-test-author --tool Write --input-file inputs/attack-test-tests-PYTEST-INI-case.json
rt hook attack-test-tests-Setup-cfg-case --kind attack --event PreToolUse --agent gmid-test-author --tool Write --input-file inputs/attack-test-tests-Setup-cfg-case.json
rt hook control-code-engine --kind control --event PreToolUse --agent gmid-code-author --tool Write --input-file inputs/control-code-engine.json
rt hook control-code-tests-tools --kind control --event PreToolUse --agent gmid-code-author --tool Write --input-file inputs/control-code-tests-tools.json
rt hook control-test-new-test --kind control --event PreToolUse --agent gmid-test-author --tool Write --input-file inputs/control-test-new-test.json
rt hook record-code-workspaces-pyw --kind record --event PreToolUse --agent gmid-code-author --tool Write --input-file inputs/record-code-workspaces-pyw.json
