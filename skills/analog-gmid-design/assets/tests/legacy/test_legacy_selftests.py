"""이관된 인라인 self-test 4종을 그대로 실행한다(20260922-ts1-legacy-move, 계획 N3.11 TS1).

이관본 `selftest_<m>.py`는 `tools/migrate/extract_selftest.py extract` 출력 그대로다(손 편집 없음).

oracle 대조: (c) 이관 전 출력(동작 보존) -- 판정 기준은 base 소스의 self-test 자체다. 이관본은 base 소스의
`if __name__ == "__main__":` 블록 본문을 그대로 옮긴 것이라, 그 블록 안의 판정(assert·실패 시 비정상 종료)이
기대값의 출처다. 이 test는 이관본이 끝까지 돈다(returncode == 0)만 판정하고, stdout 동등성(20쌍)은
auditor의 E1이 판정한다(spec card 'oracle 종류와 출처').
"""
import os
import subprocess
import sys

import pytest

_LEGACY_DIR = os.path.dirname(os.path.abspath(__file__))
_ASSETS_DIR = os.path.abspath(os.path.join(_LEGACY_DIR, "..", ".."))

_MODULES = ("sizing_recipe", "stick_diagram", "design_report", "topology_library")


@pytest.mark.parametrize("module", _MODULES)
def test_legacy_selftest_exits_zero(module):
    script = os.path.join(_LEGACY_DIR, f"selftest_{module}.py")
    env = {**os.environ, "PYTHONHASHSEED": "1", "PYTHONDONTWRITEBYTECODE": "1"}
    result = subprocess.run(
        [sys.executable, script, _ASSETS_DIR],
        cwd=_ASSETS_DIR,
        env=env,
        capture_output=True,
    )
    # oracle (c): base self-test 블록의 자체 판정 -- 정상 종료(0)가 이관 전 동작이다.
    assert result.returncode == 0, (
        f"selftest_{module} returncode={result.returncode}\n"
        f"stderr tail:\n{result.stderr.decode('utf-8', 'replace')[-4000:]}"
    )
