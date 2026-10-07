"""CONTRACT §5.7 CanonPointer -- 현재 정본 포인터, 채택 이력(fp), 비스냅샷 TypeError, 다른 권한표 ValueError(current 불변)."""
import pytest

from gmid_engine.core import CanonPointer, GraphSnapshot, WriterTable

ENTRIES = [("node", "v", "bias"), ("device", "w", "sizer")]
TABLE = WriterTable(ENTRIES)


def _s(v):
    return GraphSnapshot.empty(TABLE).write("bias", "i", {("node", "v"): {"a": v}})


def test_initial():
    s0 = GraphSnapshot.empty(TABLE)
    p = CanonPointer(s0)
    assert p.current is s0
    assert p.history == (s0.fp,)


def test_adopt_returns_snapshot_and_moves_current():
    s0 = GraphSnapshot.empty(TABLE)
    s1 = _s(1.0)
    p = CanonPointer(s0)
    fp_before = s1.fp
    assert p.adopt(s1) is s1
    assert p.current is s1
    assert p.history == (s0.fp, s1.fp)
    assert s1.fp == fp_before
    assert s1.value("node", "a", "v") == 1.0


def test_readopt_recorded_again():
    s0, s1 = _s(1.0), _s(2.0)
    p = CanonPointer(s0)
    p.adopt(s1)
    p.adopt(s1)
    p.adopt(s0)
    assert p.history == (s0.fp, s1.fp, s1.fp, s0.fp)
    assert p.current is s0


def test_equal_table_built_separately_ok():
    other = GraphSnapshot.empty(WriterTable(list(reversed(ENTRIES))))
    p = CanonPointer(_s(1.0))
    assert p.adopt(other) is other


@pytest.mark.parametrize("bad", [None, "snap", {"node": ()}, TABLE])
def test_non_snapshot_init_rejected(bad):
    with pytest.raises(TypeError):
        CanonPointer(bad)


@pytest.mark.parametrize("bad", [None, "snap", 1, TABLE])
def test_non_snapshot_adopt_rejected(bad):
    s0 = _s(1.0)
    p = CanonPointer(s0)
    with pytest.raises(TypeError):
        p.adopt(bad)
    assert p.current is s0
    assert p.history == (s0.fp,)


def test_different_writer_table_rejected_current_unchanged():
    s0 = _s(1.0)
    p = CanonPointer(s0)
    foreign = GraphSnapshot.empty(WriterTable([("node", "v", "someone_else")]))
    with pytest.raises(ValueError):
        p.adopt(foreign)
    assert p.current is s0
    assert p.history == (s0.fp,)
