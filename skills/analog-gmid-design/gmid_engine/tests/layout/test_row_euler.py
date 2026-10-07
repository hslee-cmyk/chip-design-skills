"""CONTRACT 4.8 `row_euler(transistors, matching_pairs, pair_sensitivity) -> dict` -- diffusion 섬 분할, Euler/mirror/crossover, walk 성질."""
from __future__ import annotations

from collections import Counter

import pytest

from gmid_engine.layout.row_euler import row_euler
from gmid_engine.layout.transistor import Transistor as T


def walk_ok(seq, nodes, trs):
    by = {t.name: t for t in trs}
    if len(nodes) != len(seq) + 1:
        return False
    return all({by[n].source, by[n].drain} == {nodes[i], nodes[i + 1]} for i, n in enumerate(seq))


def valid_starts(seq, trs):
    by = {t.name: t for t in trs}
    starts = sorted({x for n in seq for x in (by[n].source, by[n].drain)})
    ok = []
    for s in starts:
        cur, good = s, True
        for n in seq:
            t = by[n]
            if cur == t.source:
                cur = t.drain
            elif cur == t.drain:
                cur = t.source
            else:
                good = False
                break
        if good:
            ok.append(s)
    return ok


def check_common(res, trs):
    seq = list(res["transistor_sequence"])
    assert Counter(seq) == Counter({t.name: t.n_fingers for t in trs})        # finger 수 불변
    flat_t, flat_n = [], []
    ends = []
    for seg in res["segments"]:
        st, sn = list(seg["transistor_sequence"]), list(seg["node_sequence"])
        assert walk_ok(st, sn, trs)
        assert sn[0] == valid_starts(st, trs)[0]                              # canonical_row: 정렬 최소 유효 시작
        flat_t += st
        flat_n += sn
        ends.append(len(flat_t) - 1)
    assert flat_t == seq
    assert list(res["node_sequence"]) == flat_n
    assert list(res["crossover_after"]) == ends[:-1]


def test_single_island_euler():
    trs = [T("C", "nmos", "x", "y", 1), T("D", "nmos", "y", "z", 1)]
    res = row_euler(trs, [], None)
    check_common(res, trs)
    assert res["method"] == "euler"
    assert res["n_components"] == 1
    assert res["crossover_count"] == 0
    assert len(res["segments"]) == 1


def test_two_islands_ordered_by_first_name():
    trs = [T("F", "nmos", "r", "t", 1), T("E", "nmos", "p", "q", 2)]
    res = row_euler(trs, [], None)
    check_common(res, trs)
    assert res["n_components"] == 2
    assert [seg["transistor_sequence"][0] for seg in res["segments"]] == ["E", "F"]
    assert list(res["crossover_after"]) == [1]
    assert res["method"] == "euler"
    assert res["crossover_count"] == 0


def test_odd_island_uses_crossover():
    # 별 모양(hub 하나에 leaf 셋): 홀수 차수 노드 4개 -> Euler 불가 -> crossover
    trs = [T("A", "nmos", "h", "a", 1), T("B", "nmos", "h", "b", 1), T("C", "nmos", "h", "c", 1)]
    res = row_euler(trs, [], None)
    check_common(res, trs)
    assert res["method"] == "crossover"
    assert res["crossover_count"] >= 1
    assert res["n_components"] == 1


def test_mirror_trail_when_pair_in_island():
    trs = [T("A", "nmos", "h", "a", 2), T("B", "nmos", "h", "b", 2)]
    res = row_euler(trs, [("A", "B")], {("A", "B"): "offset"})
    check_common(res, trs)
    assert res["method"] == "mirror"
    assert res["crossover_count"] == 0


def test_method_priority_crossover_over_euler():
    # 섬 하나는 Euler, 다른 섬은 crossover -> 표기는 crossover
    trs = [T("A", "nmos", "h", "a", 1), T("B", "nmos", "h", "b", 1), T("C", "nmos", "h", "c", 1),
           T("D", "nmos", "u", "v", 1)]
    res = row_euler(trs, [], None)
    check_common(res, trs)
    assert res["method"] == "crossover"
    assert res["n_components"] == 2


@pytest.mark.parametrize("order", [0, 1])
def test_input_order_independent(order):
    trs = [T("C", "nmos", "x", "y", 2), T("D", "nmos", "y", "z", 1), T("G", "nmos", "y", "w", 1)]
    a = row_euler(trs if order == 0 else list(reversed(trs)), [], None)
    b = row_euler(trs, [], None)
    assert a == b
