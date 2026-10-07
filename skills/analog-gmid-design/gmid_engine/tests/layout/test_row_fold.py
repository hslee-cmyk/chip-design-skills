"""layout/row_fold.py -- `apply_explicit_row_split` 복사. 기대값: 손계산(divmod 균등 분할, 앞 조각 +1, 0개 조각 없음, 총 finger 보존) + 옛 SD 대조."""
from __future__ import annotations

from collections import Counter

import pytest

from gmid_engine.layout.row_fold import apply_explicit_row_split
from gmid_engine.layout.transistor import Transistor


def T(name, nf, s="h", d=None):
    return Transistor(name, "nmos", source=s, drain=d or ("d" + name), n_fingers=nf)


def shape(rows):
    return {sid: [(t.name, t.n_fingers, t.stack_id) for t in devs] for sid, devs in rows.items()}


def test_hand_split_two():
    rows = {"s": [T("A", 5), T("B", 2)], "t": [T("C", 3)]}
    out = apply_explicit_row_split(rows, {"s": 2})
    assert list(out) == ["s_split0", "s_split1", "t"]
    assert shape(out) == {
        "s_split0": [("A", 3, "s_split0"), ("B", 1, "s_split0")],
        "s_split1": [("A", 2, "s_split1"), ("B", 1, "s_split1")],
        "t": [("C", 3, None)],
    }


def test_hand_fewer_fingers_than_rows():
    out = apply_explicit_row_split({"s": [T("A", 1), T("B", 3)]}, {"s": 3})
    assert shape(out) == {
        "s_split0": [("A", 1, "s_split0"), ("B", 1, "s_split0")],
        "s_split1": [("B", 1, "s_split1")],
        "s_split2": [("B", 1, "s_split2")],
    }


@pytest.mark.parametrize("n", [None, 0, 1])
def test_no_split_when_n_rows_le_one(n):
    rows = {"s": [T("A", 4)]}
    out = apply_explicit_row_split(rows, {} if n is None else {"s": n})
    assert shape(out) == {"s": [("A", 4, None)]}
    assert out["s"] is not rows["s"]                      # 새 list


def test_total_fingers_preserved_and_input_untouched():
    rows = {"s": [T("A", 7), T("B", 4)], "u": [T("C", 5)]}
    before = shape(rows)
    out = apply_explicit_row_split(rows, {"s": 3, "u": 2})
    assert shape(rows) == before
    total = Counter()
    for devs in out.values():
        for t in devs:
            total[t.name] += t.n_fingers
            assert t.n_fingers >= 1
    assert total == Counter({"A": 7, "B": 4, "C": 5})


@pytest.mark.parametrize("specs,split", [
    ({"s": [("A", 5), ("B", 2)], "t": [("C", 3)]}, {"s": 2}),
    ({"s": [("A", 1), ("B", 3)]}, {"s": 3}),
    ({"s": [("A", 7), ("B", 4)], "u": [("C", 5)]}, {"s": 3, "u": 2}),
])
def test_same_as_oracle(specs, split, sd, serialize):
    new = apply_explicit_row_split({k: [T(n, nf) for n, nf in v] for k, v in specs.items()}, split)
    old = sd.apply_explicit_row_split(
        {k: [sd.Transistor(n, "nmos", source="h", drain="d" + n, n_fingers=nf) for n, nf in v] for k, v in specs.items()},
        split)
    assert serialize(new) == serialize(old)
