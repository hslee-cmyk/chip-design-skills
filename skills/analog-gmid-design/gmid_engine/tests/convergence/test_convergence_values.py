"""`convergence_values.py` -- MOD8 값 레코드·상태 상수 (CONTRACT 0절 표, 9절 결과 필드, 11절).

oracle (d): CONTRACT 0절·7절·9절이 선언한 필드·상태 낱말과 공개 API(`__all__` = 진입점 16개 + 데이터 타입·상수).
"""
from __future__ import annotations

import dataclasses

import pytest

import gmid_engine.convergence as conv
from gmid_engine.convergence import (
    STATUS_CONVERGED,
    STATUS_INFEASIBLE,
    STATUS_NONCONVERGENT,
    STATUS_UNPLACEABLE,
    STATUSES,
    ConvergedFront,
    ConvergedPoint,
    DroppedPoint,
    Iteration,
    JunctionChange,
    Placement,
    PlacedLayout,
    Relaxation,
)

ENTRY_POINTS = ("layout_input_of", "effective_placement", "key_exclusion", "layout_score", "realized_geometry",
                "w_loop_bound", "junction_change", "relaxation_decision", "relaxation_records", "refilter", "admit_candidates",
                "alternation_bound", "place_layout", "converge_point", "converge")          # CONTRACT 0절 표 진입점 15개 (WB-1: kind 키 운반 `kernel_` + `keys` 삭제로 16 -> 15)


def fields(cls):
    return [f.name for f in dataclasses.fields(cls)]


def test_public_api_has_15_entry_points_and_records():
    assert len(ENTRY_POINTS) == 15
    for name in ENTRY_POINTS:
        assert name in conv.__all__ and callable(getattr(conv, name))
    for name in ("ConvergedFront", "ConvergedPoint", "DroppedPoint", "Iteration", "JunctionChange", "Placement", "PlacedLayout",
                 "Relaxation", "STATUSES", "STATUS_CONVERGED", "STATUS_NONCONVERGENT", "STATUS_INFEASIBLE", "STATUS_UNPLACEABLE",
                 "DROP_DOMINATED", "DROP_FOLDED", "DROP_NONCONVERGED", "RELAX_PLACED", "RELAX_NOT_PLACED", "RELAX_NOT_AVAILABLE"):
        assert name in conv.__all__


def test_statuses_are_four_distinct_words():
    assert STATUSES == (STATUS_CONVERGED, STATUS_NONCONVERGENT, STATUS_INFEASIBLE, STATUS_UNPLACEABLE)
    assert len(set(STATUSES)) == 4
    drops = {conv.DROP_DOMINATED, conv.DROP_FOLDED, conv.DROP_NONCONVERGED}
    relax = {conv.RELAX_PLACED, conv.RELAX_NOT_PLACED, conv.RELAX_NOT_AVAILABLE}
    assert len(drops) == 3 and len(relax) == 3


def test_record_fields_follow_contract():
    # CONTRACT 2절 Placement(name, key, finger_w_m, n_fingers, W_m, pending, tol_effective)
    assert fields(Placement) == ["name", "key", "finger_w_m", "n_fingers", "W_m", "pending", "tol_effective"]
    # CONTRACT 4절 JunctionChange(device, cdb_before, csb_before, cdb_after, csb_after)
    assert fields(JunctionChange) == ["device", "cdb_before", "csb_before", "cdb_after", "csb_after"]
    # CONTRACT 6절 Relaxation(gid, role, members, reason, attempts, outcome, pattern, dx, dy, ok)
    assert fields(Relaxation) == ["gid", "role", "members", "reason", "attempts", "outcome", "pattern", "dx", "dy", "ok"]
    # CONTRACT 9절 DroppedPoint(id, 사유, by)
    assert fields(DroppedPoint) == ["point_id", "reason", "by"]
    # CONTRACT 7절 PlacedLayout (WB-1: 좁히기 칸 narrowed·kind 키 칸 keys 삭제), 9절 ConvergedFront 결과 필드
    assert fields(PlacedLayout) == ["layout", "undelivered", "placements", "unplaced", "pdk", "relaxed", "first_seen", "layout_calls"]
    assert {"front", "dropped", "nonconverged", "points", "rounds", "k_alt", "admitted", "perf", "notes"} == set(fields(ConvergedFront))
    # CONTRACT 7절 ConvergedPoint 결과 필드
    assert {"result", "layout", "geometry", "layout_area_m2", "search_area_m2", "power_w", "power_resolution_w", "iterations",
            "rejected", "narrowed", "junction", "unmatched", "undelivered", "relaxations", "kernel_calls", "layout_calls",
            "failure", "notes", "k_max", "status", "point_id", "excluded"} <= set(fields(ConvergedPoint))
    # Iteration: excluded 기본값 () (제외 재시도 기록, CONTRACT 7절)
    it = Iteration(1, (), (), (), "sealed", 1, 1e-10, 0.0, None)
    assert it.excluded == ()


@pytest.mark.parametrize("cls, args", [
    (Placement, ("M1", 10, 1e-7, 2, 2e-7, False, 0.01)),
    (JunctionChange, ("M1", 1e-15, 2e-15, 3e-15, 4e-15)),
    (DroppedPoint, ("p", "x", None)),
])
def test_records_are_frozen(cls, args):
    rec = cls(*args)
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(rec, fields(cls)[0], "other")
