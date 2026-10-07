"""`lift_s1(s1graph) -> GraphSnapshot` -- CONTRACT 1.5: 결과 writers == S2_WRITERS, S1 필드 값·block_version 이 원본과 같고
(그래서 S1 블록을 다시 부르면 reuse), 레코드 객체는 공유하지 않는다. S1_WRITERS 의 S1Graph 아님 -> TypeError, 돌지 않은 S1
writer 가 있으면 ValueError.
"""
import pytest

from gmid_engine.core import GraphSnapshot, fp_of
from gmid_engine.graph import S1Graph, S1_WRITERS, build_s1, s1_gs_groups, s1_rel_vgs, s1_structure
from gmid_engine.sizing import S2_WRITERS, lift_s1

from .conftest import SUPPLIES, circuit_cs_pmos_load, circuit_cs_res, load_doc


@pytest.fixture(params=["C", "A"])
def s1(request, tmp_path):
    doc = circuit_cs_pmos_load() if request.param == "C" else circuit_cs_res()
    return build_s1(load_doc(tmp_path, doc), dict(SUPPLIES))


def test_writers_are_s2(s1):
    lifted = lift_s1(s1)
    assert isinstance(lifted, GraphSnapshot)
    assert lifted.writers == S2_WRITERS


def test_all_s1_fields_equal_and_versions_equal(s1):
    src = s1.snapshot
    lifted = lift_s1(s1)
    n = 0
    for (kind, field), writer in S1_WRITERS.entries:
        assert lifted.column(kind, field) == src.column(kind, field)
        n += len(src.column(kind, field))
        for key, _ in src.column(kind, field):
            assert lifted.field(kind, key, field).writer == writer
    assert n > 0
    for _, writer in S1_WRITERS.entries:
        assert lifted.block_version(writer) == src.block_version(writer)
    assert lifted.fp == src.fp
    # S1 필드 밖(= S2 dc 필드)은 아직 없다
    s1_fields = {k for k, _ in S1_WRITERS.entries}
    for kind in lifted.kinds():
        for key in lifted.keys(kind):
            assert {(kind, f) for f in lifted.record(kind, key).field_names()} <= s1_fields


def test_records_not_shared(s1):
    src = s1.snapshot
    lifted = lift_s1(s1)
    for kind in src.kinds():
        for key in src.keys(kind):
            assert lifted.record(kind, key) is not src.record(kind, key)


def test_s1_block_on_lifted_snapshot_is_reused(s1):
    lifted = lift_s1(s1)
    for blk in (s1_gs_groups, s1_rel_vgs):
        blk.reset_stats()
        out = blk(lifted)
        assert out is lifted
        st = blk.stats()
        assert (st.calls, st.reuses, st.computes) == (1, 1, 0)


@pytest.mark.parametrize("bad", [None, "s1", 3])
def test_type_error_non_s1graph(bad):
    with pytest.raises(TypeError):
        lift_s1(bad)


def test_type_error_other_writer_table(s1):
    other = S1Graph(s1.key, lift_s1(s1))            # 권한표가 S2_WRITERS 인 스냅샷
    with pytest.raises(TypeError):
        lift_s1(other)


def test_value_error_when_s1_writer_not_run(tmp_path):
    td = load_doc(tmp_path, circuit_cs_pmos_load())
    full = build_s1(td, dict(SUPPLIES))
    rails = tuple(sorted(td.rails))
    partial = s1_structure(GraphSnapshot.empty(S1_WRITERS), td.devices, td.passives, td.sources, rails, td.ports)
    assert partial.block_version("s1_bulk") is None
    with pytest.raises(ValueError):
        lift_s1(S1Graph(full.key, partial))


def test_lift_is_deterministic(s1):
    assert fp_of(lift_s1(s1).fp) == fp_of(lift_s1(s1).fp)
