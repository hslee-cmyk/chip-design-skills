"""`relaxation_records(first_seen, final_layout, relaxed) -> tuple[Relaxation]` (CONTRACT 6절, 계획 LY5 '조용한 완화 금지', CONTRACT 11절 불변식 6).

oracle (a): 손으로 만든 완화 전 GroupLayout 과 최종 레이아웃에서 기록 필드를 손으로 읽는다.
"""
from __future__ import annotations

from gmid_engine.convergence import RELAX_NOT_AVAILABLE, RELAX_NOT_PLACED, RELAX_PLACED, Relaxation, relaxation_records

from .conftest import attempt, glay, layout


def test_three_outcomes_in_gid_order():
    a1, a2 = attempt(1e-6, (2, 2), reason="cc_same_W_not_adjustable"), attempt(2e-6, (1, 1), reason="w_request_rejected")
    first = {
        "z_placed": glay("z_placed", "diff_pair", ("A", "B"), reason="no_common_width", attempts=(a1,)),
        "m_failed": glay("m_failed", "diff_pair", ("C", "D"), reason="w_request_rejected", attempts=(a1, a2)),
        "a_bs": glay("a_bs", "branch_symmetric", ("E", "F"), reason="not_adjustable", attempts=(a2,)),
    }
    final = layout(groups=(
        glay("z_placed", "mirror", ("A", "B"), pattern="interdigitation", dx=0.0, dy=0.5, ok=False),
        glay("m_failed", "mirror", ("C", "D")),
        glay("a_bs", "branch_symmetric", ("E", "F")),
    ))
    recs = relaxation_records(first, final, frozenset({"z_placed", "m_failed"}))
    assert recs == (
        Relaxation("a_bs", "branch_symmetric", ("E", "F"), "not_adjustable", (a2,), RELAX_NOT_AVAILABLE, None, None, None, False),
        Relaxation("m_failed", "diff_pair", ("C", "D"), "w_request_rejected", (a1, a2), RELAX_NOT_PLACED, None, None, None, False),
        Relaxation("z_placed", "diff_pair", ("A", "B"), "no_common_width", (a1,), RELAX_PLACED, "interdigitation", 0.0, 0.5, False),
    )


def test_placed_and_centroid_matched_records_ok():
    first = {"g": glay("g", "diff_pair", ("A", "B"), reason="r")}
    final = layout(groups=(glay("g", "mirror", ("A", "B"), pattern="interdigitation", dx=0.0, dy=0.0, ok=True),))
    (rec,) = relaxation_records(first, final, frozenset({"g"}))
    assert (rec.outcome, rec.role, rec.pattern, rec.dx, rec.dy, rec.ok) == (RELAX_PLACED, "diff_pair", "interdigitation", 0.0, 0.0, True)


def test_relaxed_group_missing_from_final_layout_is_not_placed():
    first = {"g": glay("g", "diff_pair", ("A", "B"), reason="r")}
    (rec,) = relaxation_records(first, layout(groups=()), frozenset({"g"}))
    assert rec.outcome == RELAX_NOT_PLACED and rec.pattern is None and rec.ok is False


def test_no_first_seen_no_records():
    assert relaxation_records({}, layout(), frozenset()) == ()
