#!/usr/bin/env bash
# 공격 17 (EL3·EL4): 트레일러 없는 커밋으로 넣은 판정 환경 파일·판정 트리 새 파일
# 기대 근거: 05 §13.2 #17 '트레일러 없는 커밋으로도 EL3 차단·EL4 거부', §4.1, 계획 N3.12.2
# @{VAR}·@win(...)은 lib/rt.py가 상태 변수로 치환한다. 모든 git 상태는 $WORK(%TEMP%) 아래 새 저장소다.
set -e
rt() { "$PY" -B "$RT" "$@"; }

rt trailerless assets-conftest --kind attack --path skills/analog-gmid-design/assets/conftest.py --jtext '"import pytest\n"'
rt trailerless root-conftest --kind attack --path conftest.py --jtext '"x = 1\n"'
rt trailerless skills-conftest --kind attack --path skills/conftest.py --jtext '"x = 1\n"'
rt trailerless skill-pytest-ini-k --kind attack --path skills/analog-gmid-design/pytest.ini --jtext '"[pytest]\naddopts = -k nothing\n"'
rt trailerless tests-tools-conftest --kind attack --path skills/analog-gmid-design/assets/tests/tools/conftest.py --jtext '"x = 1\n"'
rt trailerless sitecustomize --kind attack --path skills/analog-gmid-design/assets/sitecustomize.py --jtext '"x = 1\n"'
rt trailerless pth --kind attack --path skills/analog-gmid-design/assets/rt.pth --jtext '"import os\n"'
rt trailerless gitattributes-export-ignore --kind attack --path .gitattributes --jtext '"tools/gates/** export-ignore\n"'
rt trailerless tests-pytest-ini --kind attack --path skills/analog-gmid-design/assets/tests/pytest.ini --jtext '"[pytest]\n"'
rt trailerless pytest-toml --kind attack --path skills/analog-gmid-design/assets/tests/pytest.toml --jtext '"[pytest]\n"'
rt trailerless dot-pytest-toml --kind attack --path skills/analog-gmid-design/assets/tests/.pytest.toml --jtext '"[pytest]\n"'
rt trailerless dot-pytest-ini --kind attack --path skills/analog-gmid-design/assets/tests/.pytest.ini --jtext '"[pytest]\n"'
rt trailerless Pytest-ini-deselect --kind attack --path skills/analog-gmid-design/assets/tests/Pytest.ini --jtext '"[pytest]\naddopts = --deselect tests/test_rt_engine.py::test_rt_gain\n"'
rt trailerless PYTEST-INI --kind attack --path skills/analog-gmid-design/assets/tests/PYTEST.INI --jtext '"[pytest]\n"'
rt trailerless Setup-cfg --kind attack --path skills/analog-gmid-design/assets/tests/Setup.cfg --jtext '"[tool:pytest]\n"'
rt trailerless numpy-shadow-pkg --kind attack --path skills/analog-gmid-design/assets/numpy/__init__.py --jtext '"x = 1\n"'
rt trailerless eng-shadow-pkg --kind attack --path skills/analog-gmid-design/assets/eng/__init__.py --jtext '"x = 1\n"'
rt trailerless pyc-add-f --kind attack --path skills/analog-gmid-design/assets/__pycache__/rt_engine.cpython-314.pyc --jtext '"not really bytecode\n"'
rt trailerless workspaces-py --kind attack --path workspaces/rtmod.py --jtext '"x = 1\n"'
rt trailerless record-workspaces-pyw --kind record --path workspaces/numpy.pyw --jtext '"x = 1\n"'
rt trailerless control-rtl --kind control --path rtl/core.v --jtext '"module core;\n// x\nendmodule\n"'
