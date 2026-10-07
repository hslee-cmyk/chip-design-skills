"""CONTRACT 4.10 `floorplan_of(rows, bodies, pdk) -> FloorplanSummary` (Q8 (vii), 판정 축 면적).

행마다 블록 폭 = 행 폭 + 2 x dummy + tap(행 끝 dummy 양끝 + 행마다 body tap), 높이 = finger_w. body 가 둘 이상이면 body 묶음 사이 간격
max(row_gap, well_spacing). included 항목은 pdk.rule_ids 의 규칙 번호를 단다.
"""
from __future__ import annotations

import pytest

from gmid_engine.layout.contract_output import FloorplanSummary, RowLayout
from gmid_engine.layout.floorplan import floorplan_of

from .conftest import rule_ids, toy_pdk

RULES = rule_ids()
RULE = dict(RULES)


def row(rid, group, width, fw=1e-6, key=100, devices=(("M", 1),)):
    seq = tuple(n for n, k in devices for _ in range(k))
    return RowLayout(rid, group, "nmos", key, fw, width, tuple(devices), seq, ("a",) * (len(seq) + 1),
                     ((seq, ("a",) * (len(seq) + 1)),), "euler", 0, 1, True, None, False)


def test_single_row_includes_dummies_and_tap(toy_lut):
    pdk = toy_pdk(toy_lut, overhead=0.05e-6, gap=0.3e-6, dummy=0.2e-6, tap=0.3e-6, well=1.0e-6)
    fp = floorplan_of((row("r/w100", "r", 3e-6),), {"r": "sub"}, pdk)
    assert isinstance(fp, FloorplanSummary)
    w = 3e-6 + 2 * 0.2e-6 + 0.3e-6
    assert fp.bbox_width_m == pytest.approx(w, rel=1e-9)
    assert fp.bbox_height_m == pytest.approx(1e-6, rel=1e-9)
    assert fp.outline_area_m2 == pytest.approx(w * 1e-6, rel=1e-9)
    assert fp.area_tie_m2 == pytest.approx(1e-16, rel=1e-12)              # g^2
    assert fp.aspect_ratio == pytest.approx(w / 1e-6, rel=1e-9)
    assert fp.packing_density == pytest.approx(1.0, rel=1e-9)
    assert len(fp.placements) == 1
    pid, x, y, pw, ph = fp.placements[0]
    assert (pid, x, y) == ("r/w100", 0.0, 0.0)
    assert pw == pytest.approx(w, rel=1e-9) and ph == pytest.approx(1e-6, rel=1e-9)
    assert fp.included == (
        ("finger_pitch_overhead", pytest.approx(0.05e-6), RULE["finger_pitch_overhead_m"]),
        ("row_end_dummy_x2_per_row", pytest.approx(0.2e-6), RULE["dummy_w_m"]),
        ("body_tap_per_row", pytest.approx(0.3e-6), RULE["tap_w_m"]),
        ("row_gap", pytest.approx(0.3e-6), RULE["row_gap_m"]),
    )


@pytest.mark.parametrize("kw", [{"dummy": 0.5e-6}, {"tap": 0.5e-6}])
def test_area_grows_with_row_end_items(toy_lut, kw):
    rows = (row("r/w100", "r", 3e-6), row("r/w200", "r", 2e-6, fw=2e-6, key=200))
    base = floorplan_of(rows, {"r": "sub"}, toy_pdk(toy_lut)).outline_area_m2
    more = floorplan_of(rows, {"r": "sub"}, toy_pdk(toy_lut, **kw)).outline_area_m2
    assert more > base


def test_row_gap_inside_body(toy_lut):
    rows = (row("r/a", "r", 3e-6), row("r/b", "r", 3e-6))
    a0 = floorplan_of(rows, {"r": "sub"}, toy_pdk(toy_lut)).outline_area_m2
    a1 = floorplan_of(rows, {"r": "sub"}, toy_pdk(toy_lut, gap=1e-6)).outline_area_m2
    assert a0 == pytest.approx(6e-12, rel=1e-9)                       # 3 x 1 두 개, 빈틈 없음 -> 6e-12 가 하한이자 정확값
    assert a1 > a0


def test_well_spacing_only_between_bodies(toy_lut):
    rows = (row("ra/w100", "ra", 3e-6), row("rb/w100", "rb", 3e-6))
    one = floorplan_of(rows, {"ra": "sub", "rb": "sub"}, toy_pdk(toy_lut, well=5e-6))
    assert [i[0] for i in one.included] == ["finger_pitch_overhead", "row_end_dummy_x2_per_row", "body_tap_per_row", "row_gap"]
    assert one.outline_area_m2 == pytest.approx(6e-12, rel=1e-9)     # body 하나 -> well 간격 없음
    bodies = {"ra": "sub", "rb": "nw"}
    two0 = floorplan_of(rows, bodies, toy_pdk(toy_lut, well=0.0))
    two = floorplan_of(rows, bodies, toy_pdk(toy_lut, well=2e-6))
    assert two.included[-1] == ("well_spacing_between_bodies", pytest.approx(2e-6), RULE["well_spacing_m"])
    assert len(two.included) == 5
    assert two.outline_area_m2 > two0.outline_area_m2
    # body 사이 간격 = max(row_gap, well): row_gap 이 더 크면 well 을 바꿔도 같다(각 body 행 1개라 body 안 간격 없음)
    g_big_w_small = floorplan_of(rows, bodies, toy_pdk(toy_lut, gap=3e-6, well=1e-6)).outline_area_m2
    g_big_w_same = floorplan_of(rows, bodies, toy_pdk(toy_lut, gap=3e-6, well=3e-6)).outline_area_m2
    assert g_big_w_small == pytest.approx(g_big_w_same, rel=1e-12)


def test_placements_sorted_and_density(toy_lut):
    rows = (row("r/z", "r", 1e-6), row("r/a", "r", 3e-6), row("q/m", "q", 2e-6, fw=2e-6, key=200))
    fp = floorplan_of(rows, {"r": "sub", "q": "sub"}, toy_pdk(toy_lut, dummy=0.1e-6))
    ids = [p[0] for p in fp.placements]
    assert ids == sorted(ids) == ["q/m", "r/a", "r/z"]
    block_area = sum(p[3] * p[4] for p in fp.placements)
    assert fp.packing_density == pytest.approx(block_area / fp.outline_area_m2, rel=1e-9)
    assert fp.outline_area_m2 == pytest.approx(fp.bbox_width_m * fp.bbox_height_m, rel=1e-12)
    assert fp.aspect_ratio == pytest.approx(max(fp.bbox_width_m, fp.bbox_height_m) / min(fp.bbox_width_m, fp.bbox_height_m))
    for _, x, y, w, h in fp.placements:
        assert x >= -1e-15 and y >= -1e-15
        assert x + w <= fp.bbox_width_m + 1e-15 and y + h <= fp.bbox_height_m + 1e-15
    # 블록 겹침 없음
    P = fp.placements
    for i in range(len(P)):
        for j in range(i + 1, len(P)):
            a, b = P[i], P[j]
            overlap_x = min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1])
            overlap_y = min(a[2] + a[4], b[2] + b[4]) - max(a[2], b[2])
            assert overlap_x <= 1e-15 or overlap_y <= 1e-15
