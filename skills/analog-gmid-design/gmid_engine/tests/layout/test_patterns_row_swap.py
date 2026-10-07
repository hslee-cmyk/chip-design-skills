"""CONTRACT 4.6 `row_swap_layout(transistors, n_rows, matching_pairs, pair_sensitivity) -> dict` (Q8 (ii), branch_symmetric).

조각 분할(앞 조각부터 +1, 0 조각 없음) -> 행 r 마다 row_euler segment 를 r 칸 순환 회전 -> canonical_row. dx·dy 는 독립 계산.
"""
from __future__ import annotations

from collections import Counter
from fractions import Fraction

import pytest

from gmid_engine.layout.patterns_row_swap import row_swap_layout
from gmid_engine.layout.transistor import Transistor as T

from .conftest import centroid_offsets
from .test_row_euler import valid_starts, walk_ok


def ef(nf_e, nf_f):
    return [T("E", "nmos", "p", "q", nf_e, gate="gc"), T("F", "nmos", "r", "t", nf_f, gate="gc")]


def split(nf, n_rows):
    base, extra = divmod(nf, n_rows)
    return [p for p in (base + (1 if i < extra else 0) for i in range(n_rows)) if p > 0]


def test_hand_2x2_two_rows():
    res = row_swap_layout(ef(2, 2), 2, [("E", "F")], {("E", "F"): "ratio"})
    assert res["method"] == "row_swap"
    rows = res["rows"]
    assert [tuple(r["transistor_sequence"]) for r in rows] == [("E", "F"), ("F", "E")]
    for r in rows:
        assert len(r["segments"]) == 2
        assert list(r["crossover_after"]) == [0]
    assert list(rows[0]["node_sequence"]) == ["p", "q", "r", "t"]
    assert list(rows[1]["node_sequence"]) == ["r", "t", "p", "q"]
    assert centroid_offsets([r["transistor_sequence"] for r in rows], ("E", "F")) == (0, 0)
    assert res["crossover_count"] == 0
    assert res["isolated_pairs"] == 0
    assert res["residual"] == pytest.approx(0.0)


def test_hand_1x1_only_one_piece_row():
    res = row_swap_layout(ef(1, 1), 2, [("E", "F")], {("E", "F"): "ratio"})
    rows = res["rows"]
    assert [tuple(r["transistor_sequence"]) for r in rows] == [("E", "F")]
    assert centroid_offsets([r["transistor_sequence"] for r in rows], ("E", "F")) == (1, 0)


@pytest.mark.parametrize("nf_e, nf_f, n_rows", [(3, 3, 2), (4, 4, 3), (5, 3, 2), (4, 4, 4), (6, 6, 3)])
def test_split_rotation_and_walk(nf_e, nf_f, n_rows):
    trs = ef(nf_e, nf_f)
    res = row_swap_layout(trs, n_rows, [("E", "F")], {("E", "F"): "ratio"})
    rows = res["rows"]
    pe, pf = split(nf_e, n_rows), split(nf_f, n_rows)
    assert len(rows) == max(len(pe), len(pf))
    total = Counter()
    for r_idx, r in enumerate(rows):
        cnt = Counter(r["transistor_sequence"])
        total += cnt
        assert cnt["E"] == (pe[r_idx] if r_idx < len(pe) else 0)
        assert cnt["F"] == (pf[r_idx] if r_idx < len(pf) else 0)
        segs = r["segments"]
        k = len(segs)
        # 회전: 이 행 segment 첫 소자 순서 = 섬 순서(E, F 중 이 행에 있는 것)를 r % k 칸 회전
        present = [n for n in ("E", "F") if cnt[n]]
        rot = r_idx % k
        assert [s["transistor_sequence"][0] for s in segs] == present[rot:] + present[:rot]
        flat_t, flat_n, ends = [], [], []
        for s in segs:
            assert walk_ok(s["transistor_sequence"], s["node_sequence"], trs)
            assert s["node_sequence"][0] == valid_starts(s["transistor_sequence"], trs)[0]
            flat_t += list(s["transistor_sequence"])
            flat_n += list(s["node_sequence"])
            ends.append(len(flat_t) - 1)
        assert list(r["transistor_sequence"]) == flat_t
        assert list(r["node_sequence"]) == flat_n
        assert list(r["crossover_after"]) == ends[:-1]
    assert total == Counter({"E": nf_e, "F": nf_f})                     # finger 수 불변
    assert res["crossover_count"] == 0                                   # 섬마다 Euler(같은 소자 finger 사슬)


def test_rows_are_deterministic_dicts():
    a = row_swap_layout(ef(4, 4), 2, [("E", "F")], {("E", "F"): "ratio"})
    b = row_swap_layout(list(reversed(ef(4, 4))), 2, [("E", "F")], {("E", "F"): "ratio"})
    assert a == b
    dx, dy = centroid_offsets([r["transistor_sequence"] for r in a["rows"]], ("E", "F"))
    assert (dx, dy) == (Fraction(0), Fraction(0))
