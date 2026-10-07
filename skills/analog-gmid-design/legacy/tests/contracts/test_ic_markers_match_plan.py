"""표식-계획서 대조 test(20260922-ts7-ic-xfail, `00-common` §9.3 '표식과 계획서 대조', design §6.5, 판정식 K).

K: ∀ IC: `ic_test[IC]` 함수에 달린 `gmid_ic` 표식(데코레이터와 `pytest.param(..., marks=...)` 모두)의 phase 집합
== `{p.phase for p in ic_parts[IC]}`. 표식이 계획서에 없는 Phase를 달거나 계획서 Phase에 표식이 없으면 FAIL.

oracle 대조:
* test_markers_match_plan -- (d) 계획서 N4.1(승인 판)을 게이트 코드 `read_plan_tables`로 읽은 값. 표식은
  `A/tests/contracts/*.py`를 AST로만 읽는다(test를 import·실행하지 않는다).
* test_plan_declares_eleven_ics -- (d) spec card 계약 3 'IC 11개 모두'.
* test_judge_rejects_* -- (a) 구성으로 정답이 정해진 합성 소스: 표식 phase를 계획서 밖 값으로 바꾸거나 표식을
  빼서 만든 소스라 판정기가 거부해야 한다는 것이 구성으로 정해진다.
* test_judge_accepts_matching_source -- (a) 계획서 Phase 그대로 표식을 단 합성 소스라 거부 0이 구성으로 정해진다.
"""
import ast
import pathlib
import sys

_CONTRACTS_DIR = pathlib.Path(__file__).resolve().parent
# contracts -> tests -> assets -> analog-gmid-design -> skills -> 저장소 루트
_REPO_ROOT = _CONTRACTS_DIR.parents[4]
_GATES_DIR = str(_REPO_ROOT / "tools" / "gates")
if _GATES_DIR not in sys.path:
    sys.path.append(_GATES_DIR)  # 끝에 -- V1은 게이트 코드 캐시를 PYTHONPATH 맨 앞에 둔다(05 §12-7)

import merge_gate  # noqa: E402


def _dotted(node):
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return None


def _gmid_ic_calls(func_def):
    """함수 데코레이터 식 안의 모든 `pytest.mark.gmid_ic(...)` 호출(parametrize의 pytest.param marks 포함)."""
    out = []
    for deco in func_def.decorator_list:
        for node in ast.walk(deco):
            if isinstance(node, ast.Call) and _dotted(node.func) == "pytest.mark.gmid_ic":
                out.append(node)
    return out


def _marker_ic_phase(call):
    """(ic, phase) -- 문자열 상수가 아니면 None을 그 자리에 둔다(판정기가 불일치로 거부)."""
    ic = call.args[0].value if (len(call.args) == 1 and isinstance(call.args[0], ast.Constant)
                                and isinstance(call.args[0].value, str)) else None
    phase = None
    for kw in call.keywords:
        if kw.arg == "phase" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
            phase = kw.value.value
    return ic, phase


def judge_markers(sources, ic_test, ic_parts):
    """sources: {파일 이름: 소스 텍스트}. 거부 사유 목록(빈 목록 = 판정식 K 성립)."""
    defs = {}
    for fname, text in sorted(sources.items()):
        for node in ast.parse(text).body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                defs.setdefault(node.name, []).append((fname, node))
    problems = []
    for ic in sorted(ic_test):
        name = ic_test[ic]
        want = {p.phase for p in ic_parts[ic]}
        found = defs.get(name, [])
        if len(found) != 1:
            problems.append(f"{ic}: 함수 {name} 정의가 {len(found)}개(정확히 하나)")
            continue
        fname, func_def = found[0]
        pairs = [_marker_ic_phase(c) for c in _gmid_ic_calls(func_def)]
        wrong_ic = sorted({str(i) for i, _ in pairs if i != ic})
        if wrong_ic:
            problems.append(f"{ic}: {fname}::{name} 표식 IC 불일치 {wrong_ic}")
        got = {p for _, p in pairs}
        if got != want:
            problems.append(f"{ic}: {fname}::{name} 표식 phase {sorted(map(str, got))} != 계획서 {sorted(want)}")
    return problems


def _plan():
    return merge_gate.read_plan_tables(str(_REPO_ROOT / merge_gate.PLAN_PATH))


def _contract_sources():
    return {p.name: p.read_text(encoding="utf-8") for p in sorted(_CONTRACTS_DIR.glob("*.py"))}


def test_plan_declares_eleven_ics():
    plan = _plan()
    # oracle (d): spec card 계약 3 -- 계획서 N4.1의 IC는 IC1~IC11 11개.
    assert set(plan.ic_parts) == {f"IC{i}" for i in range(1, 12)}
    assert set(plan.ic_test) == set(plan.ic_parts)


def test_markers_match_plan():
    plan = _plan()
    # oracle (d): 계획서 N4.1 -- 표식 phase 집합 == ic_parts[IC]의 phase 집합, IC 11개 모두.
    assert judge_markers(_contract_sources(), plan.ic_test, plan.ic_parts) == []


_SYN_IC_TEST = {"IC3": "test_syn_single", "IC7": "test_syn_cases"}
_SYN_IC_PARTS = {"IC3": (merge_gate.ICPart("1", False),),
                 "IC7": (merge_gate.ICPart("6a", False), merge_gate.ICPart("6c", True))}

_SYN_OK = '''
import pytest

@pytest.mark.gmid_ic("IC3", phase="1", case="")
def test_syn_single():
    pytest.fail()

@pytest.mark.parametrize("case", [
    pytest.param("run", marks=pytest.mark.gmid_ic("IC7", phase="6a", case="run")),
    pytest.param("stop", marks=pytest.mark.gmid_ic("IC7", phase="6c", case="stop")),
])
def test_syn_cases(case):
    pytest.fail()
'''


def test_judge_accepts_matching_source():
    # oracle (a): 합성 계획의 Phase 그대로 표식을 단 소스 -- 거부 사유 0.
    assert judge_markers({"syn.py": _SYN_OK}, _SYN_IC_TEST, _SYN_IC_PARTS) == []


def test_judge_rejects_phase_not_in_plan():
    # oracle (a): IC3 표식 phase를 합성 계획에 없는 "4"로 바꾼 소스 -- IC3 한 건 거부.
    src = _SYN_OK.replace('gmid_ic("IC3", phase="1"', 'gmid_ic("IC3", phase="4"')
    problems = judge_markers({"syn.py": src}, _SYN_IC_TEST, _SYN_IC_PARTS)
    assert len(problems) == 1
    assert problems[0].startswith("IC3: ")


def test_judge_rejects_plan_phase_without_marker():
    # oracle (a): IC7의 계획 Phase 6c 케이스 표식을 뺀 소스, IC3 데코레이터를 뺀 소스 -- 각각 그 IC 한 건 거부.
    no_stop = _SYN_OK.replace(
        '    pytest.param("stop", marks=pytest.mark.gmid_ic("IC7", phase="6c", case="stop")),\n', '')
    problems = judge_markers({"syn.py": no_stop}, _SYN_IC_TEST, _SYN_IC_PARTS)
    assert len(problems) == 1
    assert problems[0].startswith("IC7: ")
    no_deco = _SYN_OK.replace('@pytest.mark.gmid_ic("IC3", phase="1", case="")\n', '')
    problems = judge_markers({"syn.py": no_deco}, _SYN_IC_TEST, _SYN_IC_PARTS)
    assert len(problems) == 1
    assert problems[0].startswith("IC3: ")


def test_judge_rejects_real_plan_mismatch():
    # oracle (a)+(d): 실제 계획서 표로, 실제 IC7 뼈대에서 계획 Phase 6c 케이스 표식을 뺀 합성 소스 -- IC7 거부.
    plan = _plan()
    sources = _contract_sources()
    real = sources["test_ic7.py"]
    line = '    pytest.param("stop", marks=pytest.mark.gmid_ic("IC7", phase="6c", case="stop")),\n'
    assert line in real
    sources["test_ic7.py"] = real.replace(line, "")
    problems = judge_markers(sources, plan.ic_test, plan.ic_parts)
    assert [p.split(":")[0] for p in problems] == ["IC7"]
