"""D0a 시제품 test(측정 전용 -- 역할 산출물 아님, test-author 열람 금지). 계약 10(도구 존재·JSON 첫 줄)과 v7 필수 합성 단계
`import-time-high` (i)~(v)만 담았다 -- V4 모양 사전 점검과 red(도구 없는 base에서 test 실패, 수집 오류 아님) 확인용.
기대값은 합성 구성이 정한다(design 30 §6.2·card 계약 2 문장을 손으로 적용).
"""
import json
import pathlib
import shutil
import subprocess
import sys

import pytest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[5]
_TOOL = _REPO_ROOT / "tools" / "migrate" / "move_plan.py"
_GATES = _REPO_ROOT / "tools" / "gates"
_A = "skills/analog-gmid-design/assets/"
_PLAN = """# 가짜 계획

### N3.10 모듈 표

| ID | 파일 | 책임 | 대표 대상 |
|---|---|---|---|
| MOD1 | `lowmod.py` | 낮은 층 | `g0` |
| MOD2 | `lmod.py` | 위쪽 재수출 모듈 | `lmod.py` |
| MOD3 | `jmod.py` | 중간 | `Jcls`, `g` |
| MOD4 | `kmod.py` | 높은 층 | `f`, `TABLE` |
"""
_REG = """# 가짜 레지스트리

| 함수 | 책임 | 이관 목적지 | 비고 |
|---|---|---|---|
| `f` | 가짜 | kmod.py | |
"""
_FUT = "from __future__ import annotations\n\n"
_CLS = "class Jcls:\n    def m(self):\n        return 1\n\n\ndef f(x: Jcls):\n    return x\n"
_STAGES = [
    ("i", "from lmod import C\n\n\ndef f(x=C):\n    return x\n", 1, [["src.py::f", "C"]]),
    ("ii", "from lmod import C\n\n\ndef f(x):\n    return x + C\n", 0, []),
    ("iii_a", _CLS, 1, [["src.py::f", "Jcls"]]),
    ("iii_b", _FUT + _CLS, 0, []),
    ("iv", "def g():\n    return 1\n\n\nTABLE = {\"a\": g}\n", 1, [["src.py::TABLE", "g"]]),
    ("v", "def g0():\n    return 1\n\n\nTABLE = {\"a\": g0}\n", 0, []),
]


def _git(d, *args):
    subprocess.run(["git", "-C", str(d)] + list(args), check=True, capture_output=True)


def _repo(tmp_path, src):
    d = tmp_path / "r"
    shutil.copytree(_GATES, d / "tools" / "gates", ignore=shutil.ignore_patterns("redteam", "__pycache__"))
    for rel, text in (("docs/plan.md", _PLAN), ("docs/registry.md", _REG), (_A + "src.py", src), (_A + "lmod.py", "C = 1\n")):
        p = d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8", newline="\n")
    _git(d, "init", "-q")
    _git(d, "add", "-A")
    _git(d, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "s")
    return d


def _plan(d):
    assert _TOOL.is_file(), f"도구가 없다: {_TOOL}"
    r = subprocess.run([sys.executable, "-B", str(_TOOL), "plan", "--root", str(d), "--plan", "docs/plan.md",
                        "--registry", "docs/registry.md", "--split", "src.py", "lmod.py"], capture_output=True)
    first = r.stdout.decode("utf-8").splitlines()[0]
    out = json.loads(first)
    assert out["tool"] == "move_plan"
    return r.returncode, out


@pytest.mark.parametrize("sid,src,exp_exit,exp_ith", _STAGES, ids=[s[0] for s in _STAGES])
def test_import_time_high_stage(tmp_path, sid, src, exp_exit, exp_ith):
    code, out = _plan(_repo(tmp_path, src))
    assert code == exp_exit
    assert sorted([x["unit"], x["name"]] for x in out["import_time_high"]) == exp_ith
    assert out["upward"] == [] and out["unassigned"] == [] and out["conflicts"] == [] and out["reg_mismatch"] == []
