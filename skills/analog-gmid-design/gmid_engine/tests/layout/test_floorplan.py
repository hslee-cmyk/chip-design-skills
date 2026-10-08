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


def row(rid, group, width, fw=1e-6, key=100, devices=(("M", 1),), kind="nmos"):
    seq = tuple(n for n, k in devices for _ in range(k))
    return RowLayout(rid, group, kind, key, fw, width, tuple(devices), seq, ("a",) * (len(seq) + 1),
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
    path = Path(decl["pdk_root"]) / src["path"]
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
    _, _, _, pw, ph = fp.placements[0]
    assert pw == pytest.approx(width + 2 * dummy + tap, rel=1e-9)                     # + 2 x dummy_w + tap_w
    assert ph == pytest.approx(1e-6, rel=1e-9)
    assert dict((i[0], i[1]) for i in fp.included)["row_end_dummy_x2_per_row"] == pytest.approx(dummy)
