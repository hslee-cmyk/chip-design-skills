"""CONTRACT 4.0·4.4~4.14 출력 계약(`contract_output.py`) -- 데이터 선언의 필드 순서·frozen·상수."""
from __future__ import annotations

import dataclasses

import pytest

from gmid_engine.layout import LayoutOutputs, LayoutResult
from gmid_engine.layout import contract_output as co


def names(c):
    return [f.name for f in dataclasses.fields(c)]


def test_layout_result_declares_only_snapshot():
    # [U17 1-e] design 40 v1.6 §2.4.7 `LayoutResult` 행: 결과 값 사본 칸 없음. 칸 이름 `snapshot` 은 as-built.
    # 사용자 결정 O-17 (3)(2026-10-19): '이번 호출에서 계산·이식한 writer'(옛 `computed_blocks`)의 정본은 RunCounters 행(perf 행) -- 사본 칸 삭제.
    assert names(LayoutResult) == ["snapshot"]
    assert LayoutResult.__dataclass_params__.frozen


def test_layout_outputs_review_needed_first():
    # Q8 (iv): review_needed 가 첫 필드 -- [U17 1-e] 옛 `LayoutResult` 결과 칸은 필드 파생 출력 `LayoutOutputs`(4.12 5~8) 로 옮겨졌다.
    # groups·dispositions·rows·box·folds·merges·floorplan·diffusion 은 스냅샷 필드로 읽으므로 여기 없다(4.12 7).
    assert names(LayoutOutputs) == ["review_needed", "devices", "coverage_ok", "coverage_missing", "w_requests", "w_invariant_ok",
                                    "revalidation"]
    assert LayoutOutputs.__dataclass_params__.frozen
    assert co.LayoutOutputs is LayoutOutputs


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
                        "gm_id", "L_m", "vds_V", "vsb_V", "recalibrate_id", "recompute_node_voltages", "diffusion"]),
    # [U12] CONTRACT 4.10a: DeviceDiffusion(name, finger_w_m, n_fingers, ad_m2, as_m2, pd_m, ps_m)
    ("DeviceDiffusion", ["name", "finger_w_m", "n_fingers", "ad_m2", "as_m2", "pd_m", "ps_m"]),
    # [U12] CONTRACT 4.10: area_tie_m2 필드를 지우고 grid_m, passive_area_m2 를 둔다
    ("FloorplanSummary", ["bbox_width_m", "bbox_height_m", "outline_area_m2", "grid_m", "aspect_ratio", "packing_density",
                          "placements", "included", "passive_area_m2"]),
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
            co.AREA_ITEM_WELL_SPACING, co.AREA_ITEM_PASSIVES} == {
        # [U12] CONTRACT 4.10: tap 은 행 그룹 경계에만(LY10) -> "body_tap_per_group", 수동소자 블록 항목 추가(D-LY4)
        "finger_pitch_overhead", "row_end_dummy_x2_per_row", "body_tap_per_group", "row_gap", "well_spacing_between_bodies",
        "passive_blocks_mim_poly_resistor"}


def test_group_layout_has_no_relaxed_and_records_l_mismatch():
    # [U12] CONTRACT 4.5 6 (iii)·LY5 마지막 문장: `relaxed` 필드 삭제(즉시 완화 없음, D-LY2/R21), LY4 `l_mismatch` 기록 추가
    fields = names(co.GroupLayout)
    assert "relaxed" not in fields
    assert "l_mismatch" in fields
    assert co.GroupLayout.__dataclass_fields__["l_mismatch"].default == ()
