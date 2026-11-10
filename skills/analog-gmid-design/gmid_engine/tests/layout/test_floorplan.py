"""CONTRACT 4.10 `floorplan_of(rows, bodies, pdk) -> FloorplanSummary` (Q8 (vii), 판정 축 면적).

행마다 블록 폭 = 행 폭 + 2 x dummy(행 끝 dummy 양끝), 높이 = finger_w. [U12, LY10] body tap 은 행마다가 아니라 행 그룹 경계에만 --
그룹 외곽 오른쪽에 폭 tap_w, 높이 = 그룹 높이인 띠(`tap:<행 그룹>`). body 가 둘 이상이면 body 묶음 사이 간격
max(row_gap, well_spacing). included 항목은 pdk.rule_ids 의 규칙 번호를 단다. ΔA_tie 재료는 `grid_m`(옛 area_tie_m2 = g² 삭제, D-LY1).
"""
from __future__ import annotations

import pytest

from gmid_engine.layout.contract_output import FloorplanSummary, RowLayout
from gmid_engine.layout.floorplan import floorplan_of

from .conftest import rule_ids, toy_pdk

RULES = rule_ids()
RULE = dict(RULES)


def row(rid, group, width, fw=1e-6, key=100, devices=(("M", 1),), kind="nmos"):
    seq = tuple(n for n, k in devices for _ in range(k))
    return RowLayout(rid, group, kind, key, fw, width, tuple(devices), seq, ("a",) * (len(seq) + 1),
                     ((seq, ("a",) * (len(seq) + 1)),), "euler", 0, 1, True, None, False)


def test_single_row_includes_dummies_and_tap(toy_lut):
    pdk = toy_pdk(toy_lut, overhead=0.05e-6, gap=0.3e-6, dummy=0.2e-6, tap=0.3e-6, well=1.0e-6)
    fp = floorplan_of((row("r/w100", "r", 3e-6),), {"r": "sub"}, pdk)
    assert isinstance(fp, FloorplanSummary)
    # oracle (a) 구성: 행 블록 3 + 2 x 0.2 µm, 행 그룹 하나라 tap 띠 하나(0.3 µm, 높이 = 그룹 높이 1 µm)가 오른쪽에 붙는다(CONTRACT 4.10 LY10)
    w_row = 3e-6 + 2 * 0.2e-6
    w = w_row + 0.3e-6
    assert fp.bbox_width_m == pytest.approx(w, rel=1e-9)
    assert fp.bbox_height_m == pytest.approx(1e-6, rel=1e-9)
    assert fp.outline_area_m2 == pytest.approx(w * 1e-6, rel=1e-9)
    assert fp.grid_m == 1e-8                                                # [U12] 제조 격자(toy GRID) -- ΔA_tie 재료
    assert fp.aspect_ratio == pytest.approx(w / 1e-6, rel=1e-9)
    assert fp.packing_density == pytest.approx(1.0, rel=1e-9)
    assert fp.passive_area_m2 == 0.0
    P = {p[0]: p for p in fp.placements}
    assert set(P) == {"r/w100", "tap:r"}
    _, x, y, pw, ph = P["r/w100"]
    assert (x, y) == (0.0, 0.0)
    assert pw == pytest.approx(w_row, rel=1e-9) and ph == pytest.approx(1e-6, rel=1e-9)
    _, tx, ty, tw, th = P["tap:r"]
    assert tx == pytest.approx(w_row, rel=1e-9) and ty == pytest.approx(0.0, abs=1e-15)
    assert tw == pytest.approx(0.3e-6, rel=1e-9) and th == pytest.approx(1e-6, rel=1e-9)
    assert fp.included == (
        ("finger_pitch_overhead", pytest.approx(0.05e-6), RULE["finger_pitch_overhead_m"]),
        ("row_end_dummy_x2_per_row", pytest.approx(0.2e-6), RULE["dummy_w_m"]),
        ("body_tap_per_group", pytest.approx(0.3e-6), RULE["tap_w_m"]),
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
    assert [i[0] for i in one.included] == ["finger_pitch_overhead", "row_end_dummy_x2_per_row", "body_tap_per_group", "row_gap"]
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


# --- [2026-10-08] well 묶음 = (행 kind, 행 그룹 body 넷) -- 4.10 개정 ----------------------------------------------------
# sky130 ratify 값(core 9.4 표): row_gap 0.47 µm, well 1.63 µm. dummy·tap 0 으로 두어 블록 = 행 그대로(간격만 본다).

GAP, WELL = 0.47e-6, 1.63e-6


def well_pdk(toy_lut):
    return toy_pdk(toy_lut, gap=GAP, well=WELL)


def separation(a, b):
    """두 배치 사각형 (id, x, y, w, h) 사이 간격: 한 축으로 겹치면 다른 축 거리, 아니면 대각 거리."""
    dx = max(b[1] - (a[1] + a[3]), a[1] - (b[1] + b[3]), 0.0)
    dy = max(b[2] - (a[2] + a[4]), a[2] - (b[2] + b[4]), 0.0)
    return (dx * dx + dy * dy) ** 0.5


def place(fp):
    return {p[0]: p for p in fp.placements}


def test_same_well_two_row_groups_row_gap_only(toy_lut):
    rows = (row("ra/w", "ra", 10e-6), row("rb/w", "rb", 10e-6))
    fp = floorplan_of(rows, {"ra": "sub", "rb": "sub"}, well_pdk(toy_lut))
    assert "well_spacing_between_bodies" not in [i[0] for i in fp.included]
    P = place(fp)
    assert separation(P["ra/w"], P["rb/w"]) == pytest.approx(GAP, rel=1e-9)        # 같은 well -> 행 간격만
    assert fp.bbox_height_m == pytest.approx(2e-6 + GAP, rel=1e-9)


@pytest.mark.parametrize("bodies", [{"rn": "b", "rp": "b"},          # nmos·pmos 같은 body 넷 이름(개정 전 결함 사례)
                                    {"rn": "vss", "rp": "vdd"}])     # nmos·pmos 다른 body 넷
def test_nmos_pmos_get_well_spacing(toy_lut, bodies):
    rows = (row("rn/w", "rn", 10e-6, kind="nmos"), row("rp/w", "rp", 10e-6, kind="pmos"))
    fp = floorplan_of(rows, bodies, well_pdk(toy_lut))
    assert fp.included[-1] == ("well_spacing_between_bodies", pytest.approx(WELL), RULE["well_spacing_m"])
    P = place(fp)
    assert separation(P["rn/w"], P["rp/w"]) == pytest.approx(max(GAP, WELL), rel=1e-9)
    assert P["rn/w"][1] == P["rp/w"][1]                                              # 10 µm 행 둘은 위아래로 쌓인다
    assert fp.bbox_height_m == pytest.approx(3.63e-6, rel=1e-9)                       # 1 + 1.63 + 1 µm
    assert fp.outline_area_m2 == pytest.approx(fp.bbox_width_m * fp.bbox_height_m, rel=1e-12)


def test_nmos_pmos_same_body_name_matches_distinct_names(toy_lut):
    rows = (row("rn/w", "rn", 10e-6, kind="nmos"), row("rp/w", "rp", 10e-6, kind="pmos"))
    same = floorplan_of(rows, {"rn": "b", "rp": "b"}, well_pdk(toy_lut))
    diff = floorplan_of(rows, {"rn": "vss", "rp": "vdd"}, well_pdk(toy_lut))
    assert same.outline_area_m2 == pytest.approx(diff.outline_area_m2, rel=1e-12)    # 이름이 같아도 kind 가 다르면 다른 well


def test_same_kind_different_body_well_spacing(toy_lut):
    rows = (row("ra/w", "ra", 10e-6), row("rb/w", "rb", 10e-6))
    fp = floorplan_of(rows, {"ra": "sub", "rb": "iso"}, well_pdk(toy_lut))
    assert "well_spacing_between_bodies" in [i[0] for i in fp.included]
    P = place(fp)
    assert separation(P["ra/w"], P["rb/w"]) == pytest.approx(WELL, rel=1e-9)


def test_three_or_more_wells_uniform_spacing(toy_lut):
    rows = (row("n1/w", "n1", 10e-6), row("n2/w", "n2", 10e-6),                       # nmos sub 두 행 그룹 = 한 well
            row("p/w", "p", 10e-6, kind="pmos"), row("i/w", "i", 10e-6))               # pmos vdd, nmos iso = 다른 well 둘
    bodies = {"n1": "sub", "n2": "sub", "p": "vdd", "i": "iso"}
    fp = floorplan_of(rows, bodies, well_pdk(toy_lut))
    assert "well_spacing_between_bodies" in [i[0] for i in fp.included]
    well_of = {"n1/w": ("nmos", "sub"), "n2/w": ("nmos", "sub"), "p/w": ("pmos", "vdd"), "i/w": ("nmos", "iso")}
    P = place(fp)
    ids = sorted(P)
    for a in range(len(ids)):
        for b in range(a + 1, len(ids)):
            s = separation(P[ids[a]], P[ids[b]])
            if well_of[ids[a]] != well_of[ids[b]]:
                assert s >= WELL * (1 - 1e-9), (ids[a], ids[b], s)                    # 다른 well 쌍은 모두 well 간격 이상
            else:
                assert s >= GAP * (1 - 1e-9)
    assert separation(P["n1/w"], P["n2/w"]) == pytest.approx(GAP, rel=1e-9)          # 같은 well 은 행 간격만
    nearest = min(separation(P[x], P[y]) for x in ids for y in ids if well_of[x] != well_of[y])
    assert nearest == pytest.approx(WELL, rel=1e-9)                                  # 다른 well 묶음 사이 간격 = well 간격


# --- 행 끝 dummy 폭 해석(4.10, core 9.4 ratify) -- 선언 원본 csv 에서 직접 계산한 값으로 소비 확인 ----------------------

def _periphery_rules():
    """`assets/sky130_pdk_decl.json` 의 `periphery_rules` 원본(rule_table_csv)을 core 계약 9.1 형식대로 직접 읽는다(core 함수 미사용)."""
    import csv
    import json
    import re
    from pathlib import Path
    skill = Path(__file__).resolve().parents[3]
    decl = json.loads((skill / "assets" / "sky130_pdk_decl.json").read_text(encoding="utf-8"))
    src = decl["sources"]["periphery_rules"]
    from pdk_root import effective_pdk_root
    path = Path(effective_pdk_root(decl["pdk_root"])) / src["path"]
    if not path.is_file():
        pytest.fail("PDK 규칙 원본 없음: %s -- skip 하지 않는다" % path, pytrace=False)
    pat = re.compile(src["section_pattern"])
    rules, prefix = {}, None
    with open(path, encoding=src["encoding"], newline="") as f:
        for r in csv.reader(f):
            def cell(i):
                return r[i].strip() if i < len(r) else ""
            m = pat.match(cell(src["section_column"]))
            if m:
                prefix = m.group(1)
                continue
            if prefix and cell(src["id_column"]):
                rid = prefix + "." + cell(src["id_column"])
                unit = cell(src["unit_column"])
                if unit in src["units_m"]:
                    try:
                        rules.setdefault(rid, float(cell(src["value_column"])) * src["units_m"][unit])
                    except ValueError:
                        pass
    return rules


def test_dummy_width_formula_consumed(toy_lut):
    R = _periphery_rules()
    overhead = max(R["poly.2"], R["licon.1"] + 2 * R["licon.11"])
    dummy = R["poly.1a"] + R["poly.7"] + overhead / 2
    tap = R["difftap.3"] + max(R["difftap.1"], R["licon.1"] + 2 * R["licon.7"])
    gap = max(R["difftap.3"], R["poly.8"] + R["poly.2"] + R["poly.8"])
    well = max(R["nwell.2a"] + 2 * R["difftap.8"], R["difftap.9"] + R["difftap.8"])
    # core 9.4 표의 ratify 값과 같은지(계산 경로 확인)
    assert (overhead, gap, dummy, tap, well) == pytest.approx((2.8e-7, 4.7e-7, 5.4e-7, 6.8e-7, 1.63e-6), rel=1e-9)
    pdk = toy_pdk(toy_lut, overhead=overhead, gap=gap, dummy=dummy, tap=tap, well=well)
    nf, L = 4, 1e-6
    width = nf * (L + overhead)                                                       # 행 폭 = Σ nf x (L + overhead)
    fp = floorplan_of((row("r/w100", "r", width, devices=(("M", nf),)),), {"r": "sub"}, pdk)
    P = {p[0]: p for p in fp.placements}
    _, _, _, pw, ph = P["r/w100"]
    assert pw == pytest.approx(width + 2 * dummy, rel=1e-9)                            # + 2 x dummy_w (tap 은 그룹 띠, U12 LY10)
    assert ph == pytest.approx(1e-6, rel=1e-9)
    assert P["tap:r"][3] == pytest.approx(tap, rel=1e-9)                               # 그룹 경계 tap 띠 폭 = tap_w
    assert fp.bbox_width_m == pytest.approx(width + 2 * dummy + tap, rel=1e-9)
    assert dict((i[0], i[1]) for i in fp.included)["row_end_dummy_x2_per_row"] == pytest.approx(dummy)


# --- [U12] 그룹 경계 tap(LY10)·수동소자 블록(D-LY4) -- CONTRACT 4.10 개정 ------------------------------------------------
# oracle (a) 구성: 배치 기하 불변식(띠 = 그룹 외곽 오른쪽, 높이 = 그룹 높이, 그룹 하나에 띠 하나, 블록 겹침 없음)과
# 손계산 격자 블록(폭 max(1, ceil(sqrt(A/g²))) 칸 x 높이 ceil((A/g²)/폭) 칸, g = toy GRID 1e-8).

from gmid_engine.layout.contract_input import LayoutPassive  # noqa: E402

TAP = 0.68e-6


def _rows_two_groups():
    return (row("ra/1", "ra", 3e-6), row("ra/2", "ra", 3e-6), row("rb/1", "rb", 5e-6))


def _overlap_free(P):
    P = list(P)
    for i in range(len(P)):
        for j in range(i + 1, len(P)):
            a, b = P[i], P[j]
            ox = min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1])
            oy = min(a[2] + a[4], b[2] + b[4]) - max(a[2], b[2])
            assert ox <= 1e-15 or oy <= 1e-15, (a, b)


def test_tap_one_strip_per_row_group_at_group_right_edge(toy_lut):
    fp = floorplan_of(_rows_two_groups(), {"ra": "sub", "rb": "sub"}, toy_pdk(toy_lut, gap=GAP, tap=TAP))
    P = place(fp)
    taps = sorted(k for k in P if k.startswith("tap:"))
    assert taps == ["tap:ra", "tap:rb"]                                       # 행 그룹마다 하나(행마다가 아님)
    for gid, members in (("ra", ("ra/1", "ra/2")), ("rb", ("rb/1",))):
        rows_ = [P[m] for m in members]
        gx1 = max(r[1] + r[3] for r in rows_)
        gy0 = min(r[2] for r in rows_)
        gy1 = max(r[2] + r[4] for r in rows_)
        _, tx, ty, tw, th = P["tap:" + gid]
        assert tw == pytest.approx(TAP, rel=1e-9)
        assert tx == pytest.approx(gx1, rel=1e-9)                              # 그룹 외곽 오른쪽에 붙는다
        assert ty == pytest.approx(gy0, abs=1e-15)
        assert th == pytest.approx(gy1 - gy0, rel=1e-9)                        # 높이 = 그룹 높이
    _overlap_free(fp.placements)
    assert dict((i[0], i[1]) for i in fp.included)["body_tap_per_group"] == pytest.approx(TAP)


def test_tap_strip_height_covers_stacked_rows(toy_lut):
    # 같은 그룹 행 둘 -> 띠 하나가 두 행(+ 행 간격)을 덮는다. 옛 행마다 tap 이면 두 행 각각 폭이 늘었다.
    fp = floorplan_of((row("r/1", "r", 3e-6), row("r/2", "r", 3e-6)), {"r": "sub"}, toy_pdk(toy_lut, gap=GAP, tap=TAP))
    P = place(fp)
    assert [k for k in P if k.startswith("tap:")] == ["tap:r"]
    rows_ = (P["r/1"], P["r/2"])
    span = max(r[2] + r[4] for r in rows_) - min(r[2] for r in rows_)
    assert P["tap:r"][4] == pytest.approx(span, rel=1e-9)
    assert P["r/1"][3] == pytest.approx(3e-6, rel=1e-9) and P["r/2"][3] == pytest.approx(3e-6, rel=1e-9)   # 행 폭에 tap 없음


def test_no_tap_strip_when_tap_zero(toy_lut):
    fp = floorplan_of(_rows_two_groups(), {"ra": "sub", "rb": "sub"}, toy_pdk(toy_lut, gap=GAP))
    assert not [p for p in fp.placements if p[0].startswith("tap:")]


# 손계산 격자 블록(g = 1e-8 m, 칸 = 1e-16 m²):
#   A = 2.5e-10 m² = 2.5e6 칸 -> 폭 ceil(1581.14) = 1582, 높이 ceil(2.5e6/1582 = 1580.28) = 1581 -> 2 501 142 칸
#   A = 3e-12 m²   = 3e4 칸   -> 폭 ceil(173.205) = 174,  높이 ceil(3e4/174 = 172.41) = 173    -> 30 102 칸
#   A = 5e-17 m²   = 0.5 칸   -> 폭 max(1, ceil(0.707)) = 1, 높이 ceil(0.5) = 1                -> 1 칸
PASSIVE_HAND = (("Cc", 2.5e-10, 1582, 1581), ("R1", 3e-12, 174, 173), ("Rt", 5e-17, 1, 1))


def _passives():
    return tuple(LayoutPassive(n, a) for n, a, _w, _h in PASSIVE_HAND)


def test_passive_blocks_hand_grid_shape(toy_lut):
    g = 1e-8
    fp = floorplan_of((row("r/w100", "r", 3e-6),), {"r": "sub"}, toy_pdk(toy_lut, gap=GAP, well=WELL), _passives())
    P = place(fp)
    total = 0.0
    for n, a, wc, hc in PASSIVE_HAND:
        _, _, _, w, h = P["passive:" + n]
        assert w == pytest.approx(wc * g, rel=1e-9) and h == pytest.approx(hc * g, rel=1e-9)
        assert w * h >= a * (1 - 1e-12)                                      # 블록 면적 >= 선언 면적 A
        total += wc * hc * g * g
    assert fp.passive_area_m2 == pytest.approx(total, rel=1e-9)
    assert fp.passive_area_m2 >= sum(a for _n, a, _w, _h in PASSIVE_HAND)
    assert fp.included[-1] == ("passive_blocks_mim_poly_resistor", pytest.approx(total, rel=1e-9),
                               "PassiveArea.area_m2 (PDK mim_cap_density_f_per_m2 / poly_res_*)")
    _overlap_free(fp.placements)
    for _, x, y, w, h in fp.placements:                                      # 외곽이 수동소자 블록을 포함한다
        assert x >= -1e-15 and y >= -1e-15
        assert x + w <= fp.bbox_width_m * (1 + 1e-12) and y + h <= fp.bbox_height_m * (1 + 1e-12)
    assert fp.outline_area_m2 == pytest.approx(fp.bbox_width_m * fp.bbox_height_m, rel=1e-12)
    assert fp.outline_area_m2 >= 3e-6 * 1e-6 + total


def test_passive_blocks_spaced_by_placement_gap(toy_lut):
    # MIM 배치 여유 = 블록 사이 배치 간격 max(row_gap, well_spacing)(CONTRACT 4.10 수동소자 블록)
    fp = floorplan_of((row("r/w100", "r", 3e-6),), {"r": "sub"}, toy_pdk(toy_lut, gap=GAP, well=WELL), _passives())
    P = place(fp)
    blocks = ["r/w100"] + ["passive:" + n for n, *_ in PASSIVE_HAND]
    for i in range(len(blocks)):
        for j in range(i + 1, len(blocks)):
            assert separation(P[blocks[i]], P[blocks[j]]) >= max(GAP, WELL) * (1 - 1e-9), (blocks[i], blocks[j])


def test_passive_area_grows_outline_and_order_invariant(toy_lut):
    pdk = toy_pdk(toy_lut, gap=GAP, well=WELL)
    rows = (row("r/w100", "r", 3e-6),)
    base = floorplan_of(rows, {"r": "sub"}, pdk)
    fwd = floorplan_of(rows, {"r": "sub"}, pdk, _passives())
    rev = floorplan_of(rows, {"r": "sub"}, pdk, tuple(reversed(_passives())))
    assert base.passive_area_m2 == 0.0
    assert "passive_blocks_mim_poly_resistor" not in [i[0] for i in base.included]
    assert fwd.outline_area_m2 > base.outline_area_m2
    assert fwd == rev                                                        # 입력 순서와 무관(이름순 정렬해 사용)

