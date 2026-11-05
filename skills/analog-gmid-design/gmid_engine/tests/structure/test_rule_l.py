"""규칙 L -- 현재 엔진 판정(interface card '현재 엔진 test' 1~5).

oracle (c)/(d): 기대는 `rule_l_tables.BASELINE`·`rule_l_debt.DEBT`(7620f5ee 독립 측정, baseline_items.jsonl을 그대로
옮김)와 card가 적은 키(F-G13 8자리, O-27·O-36)다. 지문 값 비교는 여기 두지 않는다(검증자가 판정 기록과 대조, GD §3).
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import rule_l_checks  # noqa: E402
from rule_l_checks import check_debt, check_rule_l  # noqa: E402
from rule_l_debt import DEBT  # noqa: E402
from rule_l_tables import BASELINE, PARAMS  # noqa: E402

# F-G13 8자리(card 현재 엔진 test 3) -- 한 파일의 cells.py 두 자리는 함수가 달라 항목 둘
F_G13 = (
    ("L-5", "diode", "metrics/block_gain_model.py", "block_gain_model_of"),
    ("L-5", "diode", "metrics/ls_swing.py", "_constraints"),
    ("L-5", "diode", "graph/cells.py", "_signal_cells"),
    ("L-5", "diode", "graph/cells.py", "classify_cells"),
    ("L-5", "diode", "graph/net_model.py", "net_model"),
    ("L-5", "diode", "graph/node_impedance.py", "node_impedance"),
    ("L-5", "same_vgs", "metrics/block_gain_model.py", "block_gain_model_of"),
    ("L-5", "same_vgs", "sizing/writer_plan.py", "dc_writer_plan"),
)
# O-27·O-36 (card 현재 엔진 test 4)
O27_O36 = (
    ("L-5", "op_copy", "convergence/layout_input.py", "layout_input_of"),
    ("L-5", "op_copy", "layout/run.py", "_input_columns"),
    ("L-1x", "sizing.size_and_seal_local.size_and_seal_local"),
)


def test_rule_l_current_engine_no_violation_beyond_debt(engine_root, report):
    """1: check_rule_l(엔진)과 check_debt(.., DEBT, BASELINE)의 네 칸이 모두 빈 tuple."""
    violations = check_rule_l(engine_root, PARAMS)
    rep = check_debt(violations, DEBT, BASELINE)
    report(len(violations), len(rep.missing) + len(rep.stale) + len(rep.outside_baseline) + len(rep.bad_items))
    assert rep.missing == ()
    assert rep.stale == ()
    assert rep.outside_baseline == ()
    assert rep.bad_items == ()


def test_rule_l_baseline_sorted_and_unique():
    """2: BASELINE은 정렬된 tuple이고 중복이 없다. DEBT 키 집합과 같다."""
    assert isinstance(BASELINE, tuple)
    assert BASELINE == tuple(sorted(BASELINE))
    assert len(set(BASELINE)) == len(BASELINE)
    assert set(DEBT) == set(BASELINE)


def test_rule_l_baseline_has_fg13_eight_sites():
    """3: F-G13 8자리 키가 BASELINE에 있다(패턴을 넓혀도 이 자리를 조용히 빼지 않는다)."""
    assert len(F_G13) == 8
    assert [k for k in F_G13 if k not in set(BASELINE)] == []


def test_rule_l_baseline_has_o27_o36_keys():
    """4: O-27(layout 동작점 사본 둘)·O-36(호출자 0 size_and_seal_local) 키가 BASELINE에 있다."""
    assert [k for k in O27_O36 if k not in set(BASELINE)] == []


def test_rule_l_checks_does_not_import_structure_checks():
    """5: rule_l_checks.py에 structure_checks import 0(GD §1). AST로 import 대상 이름을 본다."""
    tree = ast.parse(Path(rule_l_checks.__file__).read_text(encoding="utf-8"))
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            names += [node.module or ""] + [a.name for a in node.names]
    assert [n for n in names if "structure_checks" in n] == []
