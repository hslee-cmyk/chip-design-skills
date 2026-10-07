"""CONTRACT 4.0·4.4~4.14 출력 계약(`contract_output.py`) -- 데이터 선언의 필드 순서·frozen·상수."""
from __future__ import annotations

import dataclasses

import pytest

from gmid_engine.layout import LayoutResult
from gmid_engine.layout import contract_output as co


def names(c):
    return [f.name for f in dataclasses.fields(c)]


def test_layout_result_review_needed_first():
    # Q8 (iv): review_needed 가 결과 첫 필드
    assert names(LayoutResult)[0] == "review_needed"
    assert set(names(LayoutResult)) >= {"devices", "groups", "matching_dispositions", "rows", "box", "fold_attempts",
                                        "merge_decisions", "floorplan", "coverage_ok", "coverage_missing", "w_requests",
                                        "w_invariant_ok", "revalidation", "computed_blocks", "snapshot"}


@pytest.mark.parametrize("cls, fields", [
    ("SliceDensity", None),
    ("WTolerance", ["lower", "upper", "effective", "grid_dominated"]),
    ("WRequest", None),
    ("ReviewItem", ["gid", "role", "reason", "dx", "dy"]),
    ("MatchingDisposition", ["gid", "role", "members", "disposition", "reason"]),
    ("GroupAttempt", ["step", "pattern", "finger_w_m", "n_fingers", "W_realized_m", "method", "dx", "dy", "ok", "reason"]),
    ("BoxVerdict", ["width_ratio", "elongation", "total_width_m", "total_height_m", "widest_row", "narrowest_row", "folds"]),
    ("FoldAttempt", None),
    ("MergeDecision", None),
    ("GroupRebuild", ["gid", "n_rows", "method", "dx", "dy"]),
    ("RowsLayout", ["rows", "box", "fold_attempts", "merge_decisions", "rebuilt_groups"]),
    ("RealizedDevice", ["name", "kind", "finger_w_key", "finger_w_m", "n_fingers", "W_need_m", "W_realized_m", "ID_A",
                        "gm_id", "L_m", "vds_V", "vsb_V", "recalibrate_id", "recompute_node_voltages"]),
    ("Revalidation", ["required", "status", "seals", "devices", "consumer", "reason"]),
])
def test_declared_fields(cls, fields):
    c = getattr(co, cls)
    assert dataclasses.is_dataclass(c)
    assert c.__dataclass_params__.frozen
    if fields is not None:
        assert names(c) == fields
    # 계약이 위치로 적은 클래스는 개수만 확인
    expected_len = {"SliceDensity": 7, "WRequest": 5, "FoldAttempt": 8, "MergeDecision": 7}
    if cls in expected_len:
        assert len(names(c)) == expected_len[cls]


def test_counted_positional_classes():
    # 4.4 FingerCandidate 11칸, 4.7 DeviceFinger 15칸, 4.12 DeviceLayout 14칸(W_m 은 다섯째)
    assert len(names(co.FingerCandidate)) == 11
    assert len(names(co.DeviceFinger)) == 15
    dl = names(co.DeviceLayout)
    assert len(dl) == 14 and dl[4] == "W_m" and dl[-1] == "excluded_slices"
    assert "ok" not in names(co.BoxVerdict)


def test_constants():
    assert co.REVALIDATION_PENDING == "pending_wiring"
    assert co.REVALIDATION_SEALS == tuple("seal_%d" % i for i in range(1, 9))
    assert isinstance(co.REVALIDATION_CONSUMER, str) and co.REVALIDATION_CONSUMER
    assert isinstance(co.REVALIDATION_PENDING_REASON, str) and co.REVALIDATION_PENDING_REASON
    assert isinstance(co.MERGE_NOISE_NOTE, str) and co.MERGE_NOISE_NOTE
    assert {co.AREA_ITEM_FINGER_OVERHEAD, co.AREA_ITEM_ROW_END_DUMMY, co.AREA_ITEM_TAP, co.AREA_ITEM_ROW_GAP,
            co.AREA_ITEM_WELL_SPACING} == {"finger_pitch_overhead", "row_end_dummy_x2_per_row", "body_tap_per_row", "row_gap",
                                          "well_spacing_between_bodies"}
