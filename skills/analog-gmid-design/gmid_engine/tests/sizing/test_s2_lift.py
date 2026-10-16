"""`lift_s1(s1graph) -> GraphSnapshot` -- CONTRACT 1.5: 결과 writers == S2_WRITERS, S1 필드 값·block_version 이 원본과 같고
(그래서 S1 블록을 다시 부르면 reuse). [2026-10-08 O7 닫음, 사용자 승인 1] 레코드 객체를 원본과 공유하고(`is`) 필드 메타
(writer·input_version·write_count)·fp 가 원본과 같다. S1Graph 아님 또는 권한표가 S1_WRITERS 를 덮지 않음 -> TypeError
([U17 ①-b] 설계 40 v1.9.1 §2.4.1: S0 수준 스냅샷처럼 넓은 표는 받는다), 돌지 않은 S1 writer 가 있으면 ValueError.
"""
import pytest

from gmid_engine.core import GraphSnapshot, WriterTable, fp_of
from gmid_engine.graph import S1Graph, S1_WRITERS, build_s1, s1_gs_groups, s1_rel_vgs, s1_structure
from gmid_engine.sizing import S2_WRITERS, lift_s1

from gmid_engine.search import open_run

from .conftest import SUPPLIES, block_row, circuit_cs_pmos_load, circuit_cs_res, load_doc


@pytest.fixture(params=["C", "A"])
def s1(request, tmp_path):
    doc = circuit_cs_pmos_load() if request.param == "C" else circuit_cs_res()
    donors, counters = open_run()
    return build_s1(load_doc(tmp_path, doc), dict(SUPPLIES), donors=donors, counters=counters)


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
    # oracle 대조: card B C4 판정 1(같은 lineage -> reuse) -- 새 실행 계수(C1)에서 그 블록 행 = (calls 1, reuses 1, computes 0)
    lifted = lift_s1(s1)
    for blk in (s1_gs_groups, s1_rel_vgs):
        donors, counters = open_run()
        out = blk(lifted, donors=donors, counters=counters)
        assert out is lifted
        assert block_row(counters, blk.name) == (1, 1, 0, 0, 0, 0)


@pytest.mark.parametrize("bad", [None, "s1", 3])
def test_type_error_non_s1graph(bad):
    with pytest.raises(TypeError):
        lift_s1(bad)


def _without_one_s1_entry():
    (kind, field), _writer = S1_WRITERS.entries[0]
    return WriterTable([(k, f, w) for (k, f), w in S1_WRITERS.entries if (k, f) != (kind, field)])


@pytest.mark.parametrize("table", [
    pytest.param(lambda: WriterTable([("node", "terminals", "someone_else")]), id="s1_field_other_writer"),
    pytest.param(_without_one_s1_entry, id="s1_entry_missing"),
])
def test_type_error_table_not_covering_s1(s1, table):
    # [U17 ①-b 기준 변경, 설계 40 v1.9.1 §2.4.1 '설계점 층(S2)… 평가마다 S0 수준 스냅샷 위에 쓴다' + graph CONTRACT 10.1 '권한표가
    #  S1_WRITERS 를 덮는 스냅샷'] 거부 대상 = 권한표가 S1_WRITERS 를 덮지 않는 S1Graph(옛 '권한표가 S1_WRITERS 와 같지 않음'에서 좁아짐).
    # oracle (a) 구성: (1) S1 필드 node.terminals 를 다른 writer 가 가진 표 (2) S1_WRITERS 에서 항목 하나를 뺀 표 -- 둘 다 S1 을 덮지 않는다.
    other = S1Graph(s1.key, GraphSnapshot.empty(table()))
    with pytest.raises(TypeError):
        lift_s1(other)


def test_wider_table_covering_s1_is_accepted(s1):
    # [U17 ①-b, §2.4.1] S0 수준 스냅샷(권한표가 S1_WRITERS 보다 넓다 -- 여기서는 lift 결과 S2_WRITERS)도 받는다. 옛 test 는 이것을 TypeError 로 봤다.
    # oracle (a): 결과 권한표 = S2_WRITERS(넓은 표 ∪ S2 = S2), S1 필드 값·block_version 은 원본 그대로.
    wide = lift_s1(s1)
    again = lift_s1(S1Graph(s1.key, wide))
    assert again.writers == S2_WRITERS
    for (kind, field), writer in S1_WRITERS.entries:
        assert again.column(kind, field) == s1.snapshot.column(kind, field)
        assert again.block_version(writer) == s1.snapshot.block_version(writer)


def test_value_error_when_s1_writer_not_run(tmp_path):
    td = load_doc(tmp_path, circuit_cs_pmos_load())
    donors, counters = open_run()
    full = build_s1(td, dict(SUPPLIES), donors=donors, counters=counters)
    rails = tuple(sorted(td.rails))
    partial = s1_structure(GraphSnapshot.empty(S1_WRITERS), td.devices, td.passives, td.sources, rails, td.ports,
                           donors=donors, counters=counters)
    assert partial.block_version("s1_bulk") is None
    with pytest.raises(ValueError):
        lift_s1(S1Graph(full.key, partial))


def test_lift_is_deterministic(s1):
    assert fp_of(lift_s1(s1).fp) == fp_of(lift_s1(s1).fp)
