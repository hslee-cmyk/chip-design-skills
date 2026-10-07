"""gmid_engine.layout test 공용 fixture -- 옛 엔진 오라클 적재, 결과 직렬화, PYTHONHASHSEED 별도 프로세스 실행.

- 오라클(SD) = `legacy/stick_diagram.py`(CONTRACT.md 머리 '옛 원본'). 피검이 아니라 기준선이다. `sys.path` 를 건드리지 않고
  파일 경로로 고유 모듈 이름 `_sd_oracle_stick_diagram` 에 적재한다.
- 직렬화(CONTRACT 1 불변식 6): dataclass 는 (클래스 이름, 필드 dict), dict 는 삽입 순서 그대로의 (키, 값) 목록, set 은 정렬 목록,
  float 는 repr 정확값. 순서까지 같아야 '같은 출력'이다.
"""
from __future__ import annotations

import dataclasses
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[3]          # tests/layout -> tests -> gmid_engine -> analog-gmid-design
SD_PATH = SKILL_DIR / "legacy" / "stick_diagram.py"
SD_MODULE_NAME = "_sd_oracle_stick_diagram"


def load_sd():
    if SD_MODULE_NAME in sys.modules:
        return sys.modules[SD_MODULE_NAME]
    if not SD_PATH.is_file():
        pytest.skip("옛 원본 stick_diagram.py 가 저장소에 없다(SD 삭제 뒤) -- 오라클 대조 불가")
    spec = importlib.util.spec_from_file_location(SD_MODULE_NAME, SD_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[SD_MODULE_NAME] = mod
    spec.loader.exec_module(mod)
    return mod


def ser(x):
    """비교용 정규 표현(순서 보존). dataclass 클래스는 이름으로만 비교 -- 옛/새 모듈의 같은 이름 클래스를 같게 본다."""
    if dataclasses.is_dataclass(x) and not isinstance(x, type):
        return ("dc", type(x).__name__, tuple((f.name, ser(getattr(x, f.name))) for f in dataclasses.fields(x)))
    if isinstance(x, dict):
        return ("dict", tuple((ser(k), ser(v)) for k, v in x.items()))
    if isinstance(x, (set, frozenset)):
        return ("set", tuple(sorted(repr(ser(v)) for v in x)))
    if isinstance(x, list):
        return ("list", tuple(ser(v) for v in x))
    if isinstance(x, tuple):
        return ("tuple", tuple(ser(v) for v in x))
    if isinstance(x, float):
        return ("float", repr(x))
    return (type(x).__name__, x)


@pytest.fixture(scope="session")
def sd():
    return load_sd()


@pytest.fixture(scope="session")
def serialize():
    return ser


def run_with_seed(code: str, seed: int) -> object:
    """`code` 를 PYTHONHASHSEED=seed 별도 프로세스에서 실행. code 는 마지막에 `RESULT` 를 JSON 직렬화 가능한 값으로 둔다."""
    prelude = (
        "import sys, json\n"
        f"sys.path.insert(0, {str(SKILL_DIR)!r})\n"
        f"sys.path.insert(0, {str(Path(__file__).resolve().parent)!r})\n"
        "from conftest import load_sd, ser\n"
    )
    epilogue = "\nprint('@@RESULT@@' + json.dumps(RESULT))\n"
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = str(seed)
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run([sys.executable, "-c", prelude + code + epilogue], cwd=str(SKILL_DIR), env=env,
                          capture_output=True, text=True, encoding="utf-8", timeout=600)
    assert proc.returncode == 0, "seed=%d 하위 프로세스 실패:\n%s\n%s" % (seed, proc.stdout, proc.stderr)
    line = [ln for ln in proc.stdout.splitlines() if ln.startswith("@@RESULT@@")]
    assert len(line) == 1, proc.stdout
    return json.loads(line[0][len("@@RESULT@@"):])


@pytest.fixture(scope="session")
def seed_runner():
    return run_with_seed
