"""CONTRACT §8 Projection -- 선언 열만 담고, fp 는 (열 값, extras) 지문이며 reads 선언 순서 무관, 선언 밖 열·없는 key 는 KeyError."""
import pytest

from gmid_engine.core import GraphSnapshot, Projection, WriterTable

TABLE = WriterTable([
    ("node", "v", "bias"),
    ("node", "u", "other"),
    ("device", "w", "sizer"),
])


def _snap(v=None, u=None, w=None, iv="i1"):
    s = GraphSnapshot.empty(TABLE)
    if v is not None:
        s = s.write("bias", iv, {("node", "v"): v})
    if u is not None:
        s = s.write("other", iv, {("node", "u"): u})
    if w is not None:
        s = s.write("sizer", iv, {("device", "w"): w})
    return s


READS = (("node", "v"), ("device", "w"))


def test_column_matches_snapshot_column():
    s = _snap(v={"b": 2.0, "a": 1.0}, w={"m1": 3.0}, u={"a": 9.0})
    p = Projection.from_snapshot(s, READS)
    assert p.column("node", "v") == (("a", 1.0), ("b", 2.0)) == s.column("node", "v")
    assert p.column("device", "w") == (("m1", 3.0),)


def test_empty_declared_column_is_empty_tuple():
    s = _snap(v={"a": 1.0})
    p = Projection.from_snapshot(s, READS)
    assert p.column("device", "w") == ()


def test_undeclared_column_key_error():
    s = _snap(v={"a": 1.0}, u={"a": 2.0})
    p = Projection.from_snapshot(s, READS)
    with pytest.raises(KeyError):
        p.column("node", "u")
    with pytest.raises(KeyError):
        p.value("node", "a", "u")


def test_value():
    s = _snap(v={"a": 1.0, "b": 2.0})
    p = Projection.from_snapshot(s, READS)
    assert p.value("node", "b", "v") == 2.0
    with pytest.raises(KeyError):
        p.value("node", "zz", "v")
    with pytest.raises(KeyError):
        p.value("device", "m1", "w")  # 선언했지만 빈 열


def test_extras_default_and_given():
    s = _snap(v={"a": 1.0})
    assert Projection.from_snapshot(s, READS).extras == ()
    p = Projection.from_snapshot(s, READS, (1, "x", (2.0,)))
    assert p.extras == (1, "x", (2.0,))


def test_fp_reads_order_independent():
    s = _snap(v={"a": 1.0}, w={"m1": 3.0})
    p1 = Projection.from_snapshot(s, READS)
    p2 = Projection.from_snapshot(s, tuple(reversed(READS)))
    assert p1.fp == p2.fp


def test_fp_same_values_different_snapshots():
    s1 = _snap(v={"a": 1.0}, w={"m1": 3.0}, iv="i1")
    s2 = _snap(v={"a": 1.0}, w={"m1": 3.0}, u={"a": 5.0}, iv="other_version")
    assert Projection.from_snapshot(s1, READS).fp == Projection.from_snapshot(s2, READS).fp


def test_fp_changes_with_declared_value_or_extras():
    s1 = _snap(v={"a": 1.0}, w={"m1": 3.0})
    base = Projection.from_snapshot(s1, READS).fp
    assert Projection.from_snapshot(_snap(v={"a": 1.5}, w={"m1": 3.0}), READS).fp != base
    assert Projection.from_snapshot(_snap(v={"a": 1.0, "b": 0.0}, w={"m1": 3.0}), READS).fp != base
    assert Projection.from_snapshot(s1, READS, (1,)).fp != base
    assert Projection.from_snapshot(s1, READS, (1,)).fp != Projection.from_snapshot(s1, READS, (2,)).fp
    assert Projection.from_snapshot(s1, READS, (0.0,)).fp != Projection.from_snapshot(s1, READS, (-0.0,)).fp


def test_fp_ignores_undeclared_columns():
    s1 = _snap(v={"a": 1.0}, u={"a": 1.0})
    s2 = _snap(v={"a": 1.0}, u={"a": 2.0})
    assert Projection.from_snapshot(s1, READS).fp == Projection.from_snapshot(s2, READS).fp


def test_fp_empty_reads_vs_column_differs():
    s = _snap(v={"a": 1.0})
    assert Projection.from_snapshot(s, (("node", "v"),)).fp != Projection.from_snapshot(s, (("device", "w"),)).fp


@pytest.mark.parametrize("extras", [([1],), ({"a": 1},), ({1},), (object(),)],
                         ids=["list", "dict", "set", "object"])
def test_mutable_extras_rejected(extras):
    s = _snap(v={"a": 1.0})
    with pytest.raises(TypeError):
        Projection.from_snapshot(s, READS, extras)
