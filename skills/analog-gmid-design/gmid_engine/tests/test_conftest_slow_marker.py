"""[NFR-4 card 2, N-T19] tests/conftest.py 의 무거운 test 마커 `slow` + 옵션 `--run-slow` 동작 (interface card C6, 사용자 결정 N-2).

규칙 H 예외(interface card 3.1 N-T19): 대상이 엔진 원본 파일이 아니라 `tests/conftest.py` 동작이고, 규칙 H 검사기는 `tests/` 바로 아래 파일을
짝·고아 검사에서 뺀다.

oracle (독립, 하위 프로세스 pytest 수집 출력): `python -m pytest --collect-only -q gmid_engine/tests/integration/test_blas_thread_determinism.py`
를 `--run-slow` 없이·있이 돌린다(수집만 -- 무거운 실행 없음, 임시 test 파일 없음).
- 없으면: 그 파일 항목이 하나도 수집 목록(`::` 줄)에 없고, 요약의 deselected 수 = `--run-slow` 로 수집된 항목 수(전부 deselected).
- 있으면: 그 파일 항목이 1개 이상 수집되고 deselected 가 없다.
기대값은 계약 문장(C6) 그대로다. 두 실행의 항목 수를 서로 맞대는 것은 '같은 수집 두 출력 비교'다(피검 conftest 가 만든 수를 기대값으로 쓰지 않는다 --
`--run-slow` 쪽 수는 pytest 자체 수집 결과).
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[2]
TARGET = "gmid_engine/tests/integration/test_blas_thread_determinism.py"


def _collect(*extra):
    proc = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", TARGET, *extra],
                          cwd=str(SKILL), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
    out = proc.stdout + proc.stderr
    ids = [ln.strip() for ln in proc.stdout.splitlines() if "::" in ln and ln.strip().startswith("gmid_engine")]
    m = re.search(r"(\d+) deselected", out)
    return proc.returncode, ids, (int(m.group(1)) if m else 0), out


def test_slow_marker_deselects_without_option_and_collects_with_it():
    rc_on, ids_on, desel_on, out_on = _collect("--run-slow")
    assert rc_on == 0, out_on[-3000:]                                       # 옵션이 등록돼 있다(없으면 usage error 4)
    assert len(ids_on) >= 1 and desel_on == 0, out_on[-3000:]              # 있으면 그 파일 항목 전부 수집
    assert all(i.startswith(TARGET + "::") for i in ids_on), ids_on
    rc_off, ids_off, desel_off, out_off = _collect()
    assert rc_off in (0, 5), out_off[-3000:]                                # 5 = 수집 항목 0(전부 deselected)
    assert ids_off == [], ids_off                                           # 없으면 그 파일 항목이 하나도 남지 않는다
    assert desel_off == len(ids_on), out_off[-3000:]                        # 요약에 deselected 로 보이고, 수 = 전부


def test_slow_marker_independent_of_m_expression():
    """C6 '`-m` 식과 무관': `-m` 을 줘도(규칙 H 마커 식) `--run-slow` 없으면 slow 항목은 deselected 다."""
    rc_on, ids_on, _d, out_on = _collect("--run-slow")
    assert rc_on == 0 and ids_on, out_on[-3000:]
    rc, ids, desel, out = _collect("-m", "not structure_test_mapping")
    assert rc in (0, 5), out[-3000:]
    assert ids == [] and desel == len(ids_on), out[-3000:]
