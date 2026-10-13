"""graph/s1_build.py -- `build_s1(doc, supplies_v=None, previous=None, column_limit=None)` (계약 1절: 순서·재사용·실패).

필드=캐시 대원칙(확정 사항 1·2·5)을 계수로 확인한다: compute_block 계수는 모듈 전역 블록 객체에 누적되므로
항상 호출 전후 차이로 본다.
"""
from __future__ import annotations

import pytest

from gmid_engine.core import GraphSnapshot, SchemaRejectedError, WriterTable
from gmid_engine.graph import (
    S1_WRITERS,
    S1Graph,
    build_s1,
    s1_branches,
    s1_bulk,
    s1_columns,
    s1_dc_conduction,
    s1_dc_roles,
    s1_gs_groups,
    s1_gvgs,
    s1_matching_groups,
    s1_rel_kcl,
    s1_rel_matching,
    s1_rel_vgs,
    s1_structure,
    s1_symmetry,
)

SIX = (
    "common_gate_amplifier", "current_reuse_telescopic_ota", "ngcc_3stage_ff",
    "pushpull_follower_buffer", "sf_pushpull_output_opamp", "two_stage_ota_sf",
)

# 9회로 전부(2026-10-07 topology 정정 b9c7042 뒤 모두 load 통과) -- JSON 직접 집계 대조용
NINE = tuple(sorted(SIX + ("folded_cascode", "nmcnr_amplifier", "two_stage_ota")))
FIELDS = ("calls", "reuses", "computes", "recomputes_same_input")
# 계약 1절 빌드 순서의 블록 13개 -- [U17 ①-d] 40 v1.8 §6-8·§2.4.8: 대칭 블록 s1_symmetry 가 build_s1 마지막(graph/s1 orbits·current_symmetry)
ALL_BLOCKS = (s1_structure, s1_bulk, s1_dc_conduction, s1_gs_groups, s1_branches, s1_dc_roles, s1_rel_vgs,
              s1_rel_matching, s1_matching_groups, s1_gvgs, s1_columns, s1_rel_kcl, s1_symmetry)
U_BLOCKS = tuple(b for b in ALL_BLOCKS if b not in (s1_structure, s1_bulk, s1_symmetry))   # U2~U4(대칭 블록은 bulk 엣지 b·레일 전위 표시를 읽는다, CONTRACT 4.8)
# [U17 ①-d] 대칭 블록의 노드 선언 표시 = 레일 전위(40 §6-8 '노드 색(레일, 포트 role, 선언 표시)') -> supplies_v 값이 바뀌면 그 블록은 다시 계산한다.
# 그 블록이 쓰는 필드(SYMMETRY_WRITES)는 supplies 재사용 판정에서 뺀다 -- 나머지 U2~U4 필드는 여전히 구조 공유(같은 값 객체).
SYMMETRY_FIELDS = {("node", "dc_colour"), ("device", "dc_colour"), ("graph", "orbits"), ("graph", "current_symmetry")}


def _same_except_symmetry(s2, s1, kind, key):
    r1, r2 = s1.snapshot.record(kind, key), s2.snapshot.record(kind, key)
    names = [f for f in r1.field_names() if (kind, f) not in SYMMETRY_FIELDS]
    assert names == [f for f in r2.field_names() if (kind, f) not in SYMMETRY_FIELDS]
    for f in names:
        assert s2.snapshot.field(kind, key, f) is s1.snapshot.field(kind, key, f), (kind, key, f)


def _stats():
    a, b = s1_structure.stats(), s1_bulk.stats()
    return {"structure": tuple(getattr(a, f) for f in FIELDS), "bulk": tuple(getattr(b, f) for f in FIELDS)}


def _all_stats():
    return {b.name: tuple(getattr(b.stats(), f) for f in FIELDS) for b in ALL_BLOCKS}


def _delta(before, after):
    return {k: tuple(y - x for x, y in zip(before[k], after[k])) for k in before}


def _bulk(s1):
    return {k: (v.net, v.origin, v.reason) for k, v in s1.column("device", "bulk")}


@pytest.mark.parametrize("name", NINE)
def test_same_inputs_with_previous_returns_same_object(gh, name):
    doc = gh.load_lib(name)
    sv = gh.supplies_for(name)
    s1 = build_s1(doc, sv)
    before = _stats()
    again = build_s1(doc, sv, previous=s1)
    assert again is s1
    assert _delta(before, _stats()) == {"structure": (0, 0, 0, 0), "bulk": (0, 0, 0, 0)}   # 블록 호출 0


def test_same_inputs_reloaded_doc_previous_still_same(gh):
    # 같은 파일을 다시 읽은 별개의 TopologyDoc 객체여도 키가 같으면 previous 그대로
    name = "sf_pushpull_output_opamp"
    sv = gh.supplies_for(name)
    s1 = build_s1(gh.load_lib(name), sv)
    assert build_s1(gh.load_lib(name), sv, previous=s1) is s1


@pytest.mark.parametrize("name,sv1,sv2", [
    ("pushpull_follower_buffer", "lib", {"vdd": 0.9, "vss": -0.9, "agnd": 0.0}),
    ("sf_pushpull_output_opamp", "lib", {"vdd": 3.3, "vss": 0.0, "agnd": 1.65}),
    ("current_reuse_telescopic_ota", "lib", {"vdd": 0.9, "gnd": -0.9}),
    ("two_stage_ota_sf", None, {"vdd": 1.8, "gnd": 0.0}),    # None -> 값: bulk 만 다시
    ("nmcnr_amplifier", "lib", {"vdd": 0.9, "vss": -0.9, "agnd": 0.0}),    # 0/1.8/0.9 -> ±0.9/0 원점 이동(Q8 뒤 3레일)
])
def test_supplies_only_change_reuses_structure(gh, name, sv1, sv2):
    doc = gh.load_lib(name)
    agg = gh.agg(gh.raw(name))
    s1 = build_s1(doc, gh.supplies_for(name) if sv1 == "lib" else sv1)
    before = _stats()
    s2 = build_s1(doc, sv2, previous=s1)
    d = _delta(before, _stats())
    assert d["structure"] == (1, 1, 0, 0)          # 호출 1, reuse 1, compute 0
    assert d["bulk"][0] == 1 and d["bulk"][2] == 1 and d["bulk"][1] == 0
    assert s2 is not s1
    assert s2.key.topology_fp == s1.key.topology_fp and s2.key.supplies_v_fp != s1.key.supplies_v_fp
    # node 레코드의 대칭 블록 밖 필드는 전부 같은 객체([U17 ①-d] node.dc_colour 는 대칭 블록이 다시 쓴다)
    assert s2.snapshot.keys("node") == s1.snapshot.keys("node")
    for k in s1.snapshot.keys("node"):
        _same_except_symmetry(s2, s1, "node", k)
    # MOS 레코드는 bulk 가 새로 쓰여 새 객체, 2단자 레코드(bulk 없음)는 그대로(core 5.6 구조 공유)
    for k in agg.mos:
        assert s2.snapshot.record("device", k) is not s1.snapshot.record("device", k)
    for k in list(agg.passives) + list(agg.sources):
        _same_except_symmetry(s2, s1, "device", k)
    # 결과는 previous 없이 새로 만든 것과 같은 내용
    fresh = build_s1(doc, sv2)
    assert fresh.snapshot.fp == s2.snapshot.fp
    assert _bulk(s2) == agg.expected_bulk(sv2)


def test_no_previous_recomputes_and_is_counted(gh):
    name = "ngcc_3stage_ff"
    doc = gh.load_lib(name)
    sv = gh.supplies_for(name)
    first = build_s1(doc, sv)
    before = _stats()
    second = build_s1(doc, sv)
    d = _delta(before, _stats())
    assert second is not first
    assert second.snapshot.fp == first.snapshot.fp and second.key == first.key
    assert d["structure"] == (1, 0, 1, 1)          # 두 번 계산, recomputes_same_input +1
    assert d["bulk"] == (1, 0, 1, 1)


def test_no_previous_every_block_recomputes_same_input(gh):
    name = "current_reuse_telescopic_ota"
    doc = gh.load_lib(name)
    sv = gh.supplies_for(name)
    build_s1(doc, sv)
    before = _all_stats()
    build_s1(doc, sv)
    d = _delta(before, _all_stats())
    assert set(d) == {b.name for b in ALL_BLOCKS} and len(d) == 13
    assert all(v == (1, 0, 1, 1) for v in d.values()), d


@pytest.mark.parametrize("name", NINE)
def test_supplies_only_change_reuses_all_u2_u4_blocks(gh, name):
    # 계약 1절·7.6: supplies_v 만 바꿔(+0.5 V 원점 이동) previous 를 넘기면 U2~U4 compute 는 s1_bulk 1회뿐
    # [U17 ①-d] 대칭 블록은 레일 전위 표시가 바뀌어 1회 다시 계산한다(40 §6-8) -- 그 블록 필드 밖은 구조 공유
    doc = gh.load_lib(name)
    sv = gh.supplies_for(name)
    s1 = build_s1(doc, sv)
    before = _all_stats()
    s2 = build_s1(doc, {k: v + 0.5 for k, v in sv.items()}, previous=s1)
    d = _delta(before, _all_stats())
    assert d["s1_bulk"] == (1, 0, 1, 0)
    assert d["s1_symmetry"] == (1, 0, 1, 0)
    for b in ALL_BLOCKS:
        if b not in (s1_bulk, s1_symmetry):
            assert d[b.name] == (1, 1, 0, 0), b.name
    # graph 레코드(U2~U4 결과) 필드는 다시 쓰이지 않아 같은 객체(core 5.6 구조 공유), node 레코드도 -- 대칭 블록 필드 밖
    _same_except_symmetry(s2, s1, "graph", "s1")
    for k in s1.snapshot.keys("node"):
        _same_except_symmetry(s2, s1, "node", k)
    # 대칭 블록 결과(궤도)는 레일 전위의 원점 이동에 불변(같은 레일 쌍의 동치 관계가 같다)
    assert s2.value("graph", "s1", "orbits") == s1.value("graph", "s1", "orbits")
    assert s2.column("device", "dc_role") == s1.column("device", "dc_role")
    # 같은 인자로 한 번 더 -> 같은 객체, 계수 변화 0
    before = _all_stats()
    assert build_s1(doc, {k: v + 0.5 for k, v in sv.items()}, previous=s2) is s2
    assert all(v == (0, 0, 0, 0) for v in _delta(before, _all_stats()).values())


def test_u_blocks_do_not_read_bulk_or_supplies():
    # 계약 0절 끝: U2~U4 블록은 device.bulk·supplies 를 읽지 않는다(extras 는 s1_columns 의 column_limit 뿐)
    for b in U_BLOCKS:
        assert ("device", "bulk") not in b.reads, b.name


def test_previous_of_other_doc_gives_fresh_content(gh):
    # previous 가 다른 회로여도 열 교체로 결과는 새로 만든 것과 같다(이전 회로 레코드 잔존 없음)
    a = build_s1(gh.load_lib("current_reuse_telescopic_ota"), {"vdd": 1.8, "gnd": 0.0})
    doc_b = gh.load_lib("common_gate_amplifier")
    b = build_s1(doc_b, {"vdd": 1.8, "gnd": 0.0}, previous=a)
    fresh = build_s1(doc_b, {"vdd": 1.8, "gnd": 0.0})
    assert b.snapshot.fp == fresh.snapshot.fp
    assert b.snapshot.keys("device") == fresh.snapshot.keys("device")
    assert b.snapshot.keys("node") == fresh.snapshot.keys("node")
    assert b.key == fresh.key


def test_chain_back_to_original_supplies(gh):
    # A -> B -> A: 세 번째는 previous(B) 와 키가 달라 새 객체지만 내용은 첫 번째와 같고 structure 는 reuse
    name = "pushpull_follower_buffer"
    doc = gh.load_lib(name)
    sv = gh.supplies_for(name)
    s_a = build_s1(doc, sv)
    s_b = build_s1(doc, {"vdd": 2.5, "vss": 0.0, "agnd": 1.0}, previous=s_a)
    before = _stats()
    s_c = build_s1(doc, sv, previous=s_b)
    assert _delta(before, _stats())["structure"] == (1, 1, 0, 0)
    assert s_c.key == s_a.key and s_c.snapshot.fp == s_a.snapshot.fp
    assert build_s1(doc, sv, previous=s_c) is s_c


# ------------------------------------------------------------------ 실패


def test_doc_type_error(gh):
    raw = gh.raw("common_gate_amplifier")
    for bad in (raw, str(gh.LIBRARY / "common_gate_amplifier.topology.json"), None):
        with pytest.raises(TypeError):
            build_s1(bad, None)


def test_previous_type_error(gh):
    doc = gh.load_lib("common_gate_amplifier")
    s1 = build_s1(doc, None)
    for bad in (s1.snapshot, "previous", s1.key, GraphSnapshot.empty(S1_WRITERS)):
        with pytest.raises(TypeError):
            build_s1(doc, None, previous=bad)


def test_previous_with_other_writer_table_type_error(gh):
    doc = gh.load_lib("common_gate_amplifier")
    s1 = build_s1(doc, None)
    other = S1Graph(s1.key, GraphSnapshot.empty(WriterTable([("node", "terminals", "someone_else")])))
    with pytest.raises(TypeError):
        build_s1(doc, None, previous=other)
    # 키가 같아도 권한표가 다르면 그대로 돌려주지 않는다
    assert other.key == s1.key


def test_bad_supplies_rejected_before_blocks(gh):
    doc = gh.load_lib("common_gate_amplifier")
    before = _stats()
    with pytest.raises(SchemaRejectedError):
        build_s1(doc, {"vdd": "1.8", "gnd": 0.0})
    assert _delta(before, _stats()) == {"structure": (0, 0, 0, 0), "bulk": (0, 0, 0, 0)}
