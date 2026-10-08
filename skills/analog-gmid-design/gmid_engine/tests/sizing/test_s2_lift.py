"""`lift_s1(s1graph) -> GraphSnapshot` -- CONTRACT 1.5: 결과 writers == S2_WRITERS, S1 필드 값·block_version 이 원본과 같고
(그래서 S1 블록을 다시 부르면 reuse). [2026-10-08 O7 닫음, 사용자 승인 1] 레코드 객체를 원본과 공유하고(`is`) 필드 메타
(writer·input_version·write_count)·fp 가 원본과 같다. S1_WRITERS 의 S1Graph 아님 -> TypeError, 돌지 않은 S1 writer 가 있으면
ValueError.
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


def test_records_shared_with_source_and_meta_kept(s1):
    # [2026-10-08 승인된 동작 변경, sizing O7 닫음 -- 사용자 결정 1 "1은 승인"] CONTRACT 1.5: 결과 = S1 스냅샷의 extend_writers
    # -> 레코드를 원본과 공유(`is`), 필드 메타(writer·input_version·write_count)·fp 도 원본과 같다.
    # oracle (d): 사용자가 선언한 계약(1.5 개정문) -- 옛 'is not' 단언을 대체한다(기준 약화 아님: 단언 수는 늘었다).
    src = s1.snapshot
    lifted = lift_s1(s1)
    assert lifted.kinds() == src.kinds()
    n = 0
    for kind in src.kinds():
        assert lifted.keys(kind) == src.keys(kind)
        for key in src.keys(kind):
            rec = src.record(kind, key)
            assert lifted.record(kind, key) is rec
            for f in rec.field_names():
                a, b = lifted.field(kind, key, f), src.field(kind, key, f)
                assert (a.value_fp, a.writer, a.input_version, a.write_count) == (
                    b.value_fp, b.writer, b.input_version, b.write_count)
                n += 1
    assert n > 0
    assert lifted.fp == src.fp
    assert s1.snapshot.writers == S1_WRITERS                 # 원본 불변


def test_write_count_above_one_preserved(s1):
    # oracle (a): S1 열 하나를 같은 값·새 input_version 으로 다시 써서 write_count 를 2 로 만든다(core 5.6 '이전 + 1').
    # lift 결과의 그 필드도 2 여야 한다(1.5 '필드 메타 ... 원본과 같다'; r8 까지는 1 로 새로 시작했다).
    src = s1.snapshot
    kind, field, writer = next((k, f, w) for (k, f), w in S1_WRITERS.entries if src.column(k, f))
    bumped = src.write(writer, "test_rewrite_v2", {(kind, field): dict(src.column(kind, field))})
    keys = [k for k, _ in bumped.column(kind, field)]
    assert keys
    for key in keys:
        assert bumped.field(kind, key, field).write_count == 2
    lifted = lift_s1(S1Graph(s1.key, bumped))
    for key in keys:
        fv = lifted.field(kind, key, field)
        assert (fv.write_count, fv.input_version, fv.writer) == (2, "test_rewrite_v2", writer)
        assert lifted.record(kind, key) is bumped.record(kind, key)
    assert lifted.block_version(writer) == "test_rewrite_v2"


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
