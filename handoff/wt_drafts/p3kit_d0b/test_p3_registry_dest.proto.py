"""D0b 계약 test 모양 시제품(측정 전용 -- test-author에게 건네지 않는다, 작성자 != 검증자).

red 모양(base에서 AssertionError, 수집 오류 아님)과 무거운 실행 비용(plan 한 번을 모듈 범위로 캐시)을 확인하려는 것이다.
도구 경로는 환경 변수 P3RD_TOOL(시제품 move_plan_proto.py) -- 실제 test는 <저장소>/tools/migrate/move_plan.py를 부른다.
"""
import functools
import json
import os
import pathlib
import re
import subprocess
import sys

_ROOT = pathlib.Path(os.environ["P3RD_ROOT"])
_TOOL = os.environ["P3RD_TOOL"]
_REG = "docs/03-analysis/gain-budget-gmid-sizing.function-registry.md"
_ARGS = ["--plan", "docs/01-plan/features/gain-budget-gmid-sizing.plan.md", "--registry", _REG,
         "--split", "sizing_recipe.py", "stick_diagram.py", "topology_library.py", "design_report.py", "audit_current_forced.py",
         "--keep", "audit_current_forced.py", "--aliases", '{"optimizer": "theta_search.py"}']


@functools.lru_cache(maxsize=1)
def _p3rd_plan():
    assert pathlib.Path(_TOOL).is_file(), "도구가 없다"
    r = subprocess.run([sys.executable, "-B", _TOOL, "plan", "--root", str(_ROOT), "--rev", "HEAD"] + _ARGS,
                       capture_output=True, text=True, encoding="utf-8")
    first = r.stdout.splitlines()[0] if r.stdout else ""
    out = json.loads(first)
    assert out.get("tool") == "move_plan"
    return r.returncode, out


def test_p3rd_plan_exit_0():
    rc, out = _p3rd_plan()
    assert rc == 0, {k: len(out.get(k, [])) for k in ("upward", "cycles", "unassigned", "conflicts", "reg_mismatch", "import_time_high")}


def test_p3rd_reg_mismatch_empty():
    _, out = _p3rd_plan()
    assert out["reg_mismatch"] == []


def test_p3rd_layer_empty():
    _, out = _p3rd_plan()
    assert out["upward"] == [] and out["cycles"] == []


def test_p3rd_import_time_high_empty():
    _, out = _p3rd_plan()
    assert out["import_time_high"] == []


def test_p3rd_mod7_only_its_file():
    _, out = _p3rd_plan()
    bad = [u for u, v in out["assignment"].items() if v["mod"] == "stick_diagram.py" and not u.startswith("stick_diagram.py::")]
    assert bad == []


def test_p3rd_rule_column_exists():
    text = (_ROOT / _REG).read_text(encoding="utf-8")
    heads = [ln for ln in text.splitlines() if ln.startswith("|") and "이관 목적지" in ln and "함수" in ln]
    assert heads and all("근거 규칙" in h for h in heads)


def test_p3rd_no_phase3_hold():
    text = (_ROOT / _REG).read_text(encoding="utf-8")
    assert re.findall(r"보류\(Phase 3\)", text) == []
