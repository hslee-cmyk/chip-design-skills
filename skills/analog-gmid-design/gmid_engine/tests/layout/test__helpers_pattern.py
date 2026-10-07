"""CONTRACT 4.0 `_helpers_pattern.py` 공용 helper -- `orient`(4.5 1 hub-leaf 전제), `offsets`(4.5 4 dx·dy), `pattern_rows`(4.5 4 정규화).

반환 모양(계약에 형식 문장이 없어 관찰로 고정): `orient` -> (((이름, source, drain), ...) | None, 사유 ""|사유),
`offsets` -> (dx, dy) 정확한 유리수, `pattern_rows` -> `PatternRow` tuple.
"""
from __future__ import annotations

from fractions import Fraction

import pytest

from gmid_engine.layout._helpers_pattern import offsets, orient, pattern_rows
from gmid_engine.layout.canonical_rows import canonical_row
from gmid_engine.layout.contract_output import PatternRow
from gmid_engine.layout.transistor import Transistor as T

from .conftest import centroid_offsets, dev, mg


def _devs(*ds):
    return {d.name: d for d in ds}


def test_orient_hub_becomes_source():
    A = dev("A", "h", "da", 1e-6)
    B = dev("B", "db", "h", 1e-6)          # hub 가 drain -> 뒤집어 hub 가 source
    trs, reason = orient(mg("g1", ("A", "B"), "diff_pair", "h"), _devs(A, B))
    assert reason == ""
    assert tuple(trs) == (("A", "h", "da"), ("B", "h", "db"))


@pytest.mark.parametrize("hub, devs, reason", [
    (None, (("A", "h", "da"), ("B", "h", "db")), "no_hub_net"),
    ("h", (("A", "h", "da"), ("B", "x", "db")), "member_not_on_hub:B"),
    ("h", (("A", "h", "d1"), ("B", "d1", "h")), "leaf_net_shared"),
])
def test_orient_preconditions(hub, devs, reason):
    ds = [dev(n, s, d, 1e-6) for n, s, d in devs]
    trs, why = orient(mg("g1", tuple(d.name for d in ds), "mirror", hub), _devs(*ds))
    assert trs is None
    assert why == reason


@pytest.mark.parametrize("rows", [
    [("A", "B"), ("B", "A")],
    [("A", "B")],
    [("A", "A", "B"), ("B", "A", "A")],
    [("A", "B", "B", "A")],
    [("E", "E", "F"), ("F", "E"), ("E", "F", "F")],
    [("A", "B", "C"), ("C", "A", "B"), ("B", "C", "A")],
])
def test_offsets_formula(rows):
    members = tuple(sorted({n for r in rows for n in r}))
    prs = tuple(PatternRow(tuple(r), (), (), ()) for r in rows)
    dx, dy = offsets(prs, members)
    assert (Fraction(dx), Fraction(dy)) == centroid_offsets(rows, members)


def test_offsets_hand():
    R = lambda s: PatternRow(tuple(s), (), (), ())        # noqa: E731
    assert offsets((R("AB"), R("BA")), ("A", "B")) == (0, 0)
    assert offsets((R("AB"),), ("A", "B")) == (1, 0)


def test_pattern_rows_canonicalised():
    trs = [T("A", "nmos", "h", "da", 2), T("B", "nmos", "h", "db", 2)]
    raw = {"rows": [{"transistor_sequence": ["A", "B"], "node_sequence": ["junk"], "crossover_after": []},
                    {"transistor_sequence": ["B", "A"], "node_sequence": ["junk"]}]}
    got = pattern_rows(raw, trs)
    assert isinstance(got, tuple) and all(isinstance(r, PatternRow) for r in got)
    for r, src in zip(got, raw["rows"]):
        exp = canonical_row(src, trs)
        assert r.transistor_sequence == tuple(exp["transistor_sequence"])
        assert r.node_sequence == tuple(exp["node_sequence"])
    assert got[0].node_sequence == ("da", "h", "db")
    assert got[1].node_sequence == ("db", "h", "da")
    assert raw["rows"][0]["node_sequence"] == ["junk"]       # 입력 불변
