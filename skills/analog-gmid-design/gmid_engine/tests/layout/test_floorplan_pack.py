"""layout/floorplan_pack.py -- `pack_floorplan_grouped`(+ 정의 14개) 복사.

기대값: 손계산(skyline 배치 2블록, diffusion 안전 분할점, 지배 블록 판정, 배치 겹침 없음·좌우 거울 배치) + 옛 SD 대조.
"""
from __future__ import annotations

import itertools

import pytest

from gmid_engine.layout.floorplan_pack import (FloorplanBlock, FloorplanResult, PlacedBlock,
                                               evaluate_row_split_candidates, find_diffusion_safe_split_points,
                                               pack_floorplan, pack_floorplan_grouped, pack_group_as_unit,
                                               pack_to_height, skyline_pack, skyline_pack_best_width)

FB = FloorplanBlock


# ---- skyline_pack 손계산 ----
def test_skyline_two_unit_blocks_side_by_side():
    placements, bw, bh = skyline_pack([FB("a", 1, 1), FB("b", 1, 1)], max_width=3, gap=0)
    assert (placements["a"].x, placements["a"].y) == (0.0, 0.0)
    assert (placements["b"].x, placements["b"].y) == (1.0, 0.0)
    assert (bw, bh) == (1 + 1, 1)


def test_skyline_narrow_container_stacks():
    placements, bw, bh = skyline_pack([FB("a", 1, 1), FB("b", 1, 1)], max_width=1.5, gap=0)
    assert (placements["b"].x, placements["b"].y) == (0.0, 1.0)
    assert (bw, bh) == (1, 2.0)


def test_skyline_too_wide_block_returns_none():
    assert skyline_pack([FB("a", 5, 1)], max_width=4) is None


def test_skyline_taller_first():
    placements, _, _ = skyline_pack([FB("lo", 1, 1), FB("hi", 1, 3)], max_width=10, gap=0)
    assert (placements["hi"].x, placements["hi"].y) == (0.0, 0.0)      # 높이 큰 것 먼저
    assert placements["lo"].x == 1.0


# ---- find_diffusion_safe_split_points ----
@pytest.mark.parametrize("seq,expected", [
    (["A", "A", "B", "B"], [2]),
    (["A", "B", "A"], []),
    (["A", "B", "C"], [1, 2]),
    (["M6", "M6", "M7", "M6", "M7"], []),
    ([], []),
    (["A"], []),
])
def test_safe_split_points_hand(seq, expected):
    assert find_diffusion_safe_split_points(seq) == expected


# ---- evaluate_row_split_candidates ----
def test_row_split_candidates_hand():
    blocks = [FB("a", 8, 1), FB("b", 2, 1)]
    c = evaluate_row_split_candidates(blocks, bbox_width=10, bbox_height=2)
    assert len(c) == 1                                   # a: 8 >= 0.6*10, b: 2 < 6, 높이 1 < 1.2
    assert {k: c[0][k] for k in ("name", "dimension", "value", "bbox", "diffusion_check", "splittable")} == {
        "name": "a", "dimension": "width", "value": 8, "bbox": 10, "diffusion_check": "not_verified", "splittable": None}
    c2 = evaluate_row_split_candidates(blocks, 10, 2, transistor_sequences={"a": ["A", "A", "B", "B"]})
    assert (c2[0]["diffusion_check"], c2[0]["splittable"], c2[0]["safe_split_points"]) == ("verified", True, [2])
    c3 = evaluate_row_split_candidates(blocks, 10, 2, transistor_sequences={"a": ["A", "B", "A"]})
    assert (c3[0]["splittable"], c3[0]["safe_split_points"]) == (False, [])


# ---- pack_floorplan_grouped 성질(손 정의) ----
def _rects_disjoint(placements):
    eps = 1e-9
    for p, q in itertools.combinations(placements.values(), 2):
        overlap_x = min(p.x + p.width, q.x + q.width) - max(p.x, q.x)
        overlap_y = min(p.y + p.height, q.y + q.height) - max(p.y, q.y)
        if overlap_x > eps and overlap_y > eps:
            return False
    return True


GROUPS = {"n": [FB("r1", 4, 1), FB("r2", 3, 1)], "p": [FB("r3", 5, 1)]}
PAIRS = [(FB("mr", 2, 1), FB("ml", 2, 1)), (FB("kr", 1, 2), FB("kl", 1.5, 2))]


def test_grouped_properties():
    res = pack_floorplan_grouped(GROUPS, PAIRS, gap=0.5)
    assert isinstance(res, FloorplanResult)
    assert set(res.placements) == {"r1", "r2", "r3", "mr", "ml", "kr", "kl"}     # 그룹 이름이 아니라 개별 block 이름
    assert all(isinstance(p, PlacedBlock) for p in res.placements.values())
    assert _rects_disjoint(res.placements)
    mr, ml = res.placements["mr"], res.placements["ml"]
    assert ml.y == mr.y and ml.x + ml.width == pytest.approx(-mr.x)             # x=0 축 거울 배치
    assert res.symmetry_max_error == pytest.approx(0.5)                          # |1-1.5| + |2-2|
    # 밀도 분자는 개별 block 이 아니라 그룹 block(내부 gap 포함) 면적이라 손 정의로 고정하지 않는다(값은 옛 SD 대조가 본다).
    assert 0.0 < res.packing_density <= 1.0
    assert res.bbox_width > 0 and res.bbox_height > 0
    assert res.aspect_ratio == pytest.approx(max(res.bbox_width, res.bbox_height) / min(res.bbox_width, res.bbox_height))


def test_group_as_unit_single_block():
    blk, internal = pack_group_as_unit("g", [FB("a", 3, 2)])
    assert (blk.name, blk.width, blk.height) == ("g", 3, 2)
    assert internal == {"a": PlacedBlock("a", 0.0, 0.0, 3, 2)}


# ---- 옛 SD 대조 ----
def _to(mod, groups, pairs):
    g = {k: [mod.FloorplanBlock(b.name, b.width, b.height) for b in v] for k, v in groups.items()}
    p = [(mod.FloorplanBlock(r.name, r.width, r.height), mod.FloorplanBlock(l.name, l.width, l.height)) for r, l in pairs]
    return g, p


@pytest.mark.parametrize("kwargs", [
    dict(gap=0.5),
    dict(gap=0.2, transistor_sequences={"mr": ["A", "A", "B"]}, net_weights={"n": {"mr": 2.0}}),
    dict(gap=0.3, sub_kinds={"n": {"r1": "nmos", "r2": "pmos"}}),
])
def test_grouped_same_as_oracle(kwargs, sd, serialize):
    import gmid_engine.layout.floorplan_pack as new_mod
    g_new, p_new = _to(new_mod, GROUPS, PAIRS)
    g_old, p_old = _to(sd, GROUPS, PAIRS)
    assert serialize(pack_floorplan_grouped(g_new, p_new, **kwargs)) == serialize(sd.pack_floorplan_grouped(g_old, p_old, **kwargs))


BLOCKS = [("a", 4, 1), ("b", 3, 2), ("c", 2, 2), ("d", 1, 3), ("e", 2.5, 1)]


def test_flat_packers_same_as_oracle(sd, serialize):
    nb = [FB(*b) for b in BLOCKS]
    ob = [sd.FloorplanBlock(*b) for b in BLOCKS]
    assert serialize(skyline_pack(nb, 6, gap=0.5)) == serialize(sd.skyline_pack(ob, 6, gap=0.5))
    assert serialize(skyline_pack_best_width(nb, gap=0.5)) == serialize(sd.skyline_pack_best_width(ob, gap=0.5))
    conn = {"a": {"d": 1.0}}
    assert serialize(pack_to_height(nb, 4.0, gap=0.5, connections=conn, width_tolerance=2.0)) == serialize(
        sd.pack_to_height(ob, 4.0, gap=0.5, connections=conn, width_tolerance=2.0))
    pairs_n = [(FB("mr", 2, 1), FB("ml", 2, 1))]
    pairs_o = [(sd.FloorplanBlock("mr", 2, 1), sd.FloorplanBlock("ml", 2, 1))]
    assert serialize(pack_floorplan(nb, pairs_n, gap=0.5)) == serialize(sd.pack_floorplan(ob, pairs_o, gap=0.5))
