"""graph/columns.py -- `s1_columns`: 레일 쌍 노드-단순 경로 기둥·쌍 요약·orphan·열거 상한(계약 4.3, 1절 column_limit, 7.3, 7.6).

기대값 = 독립 oracle(가지 그래프에서 레일 쌍마다 DFS 노드-단순 경로를 test 쪽에서 다시 열거)과 계약 7.3 표
(기둥 합침 / 따로 = Σ parallel_expansion, 파일럿 41/62).
"""
from __future__ import annotations

import math

import pytest

from gmid_engine.core import ComputeBlock
from gmid_engine.graph import (
    S1_COLUMNS_WRITER,
    Column,
    ColumnOrphan,
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
)

SIX = (
    "common_gate_amplifier", "current_reuse_telescopic_ota", "ngcc_3stage_ff",
    "pushpull_follower_buffer", "sf_pushpull_output_opamp", "two_stage_ota_sf",
)
NINE = tuple(sorted(SIX + ("folded_cascode", "nmcnr_amplifier", "two_stage_ota")))
# 계약 7.3 표: (기둥 합침, 따로, column_pairs, orphan 수)
TABLE = {
    "common_gate_amplifier": (1, 1, (("gnd", "vdd", 1),), 0),
    "current_reuse_telescopic_ota": (41, 62, (("gnd", "vdd", 41),), 0),
    "folded_cascode": (7, 7, (("gnd", "vdd", 7),), 0),
    "ngcc_3stage_ff": (6, 9, (("gnd", "vdd", 6),), 0),
    "nmcnr_amplifier": (9, 10, (("vdd", "vss", 9),), 0),
    "pushpull_follower_buffer": (3, 3, (("agnd", "vdd", 0), ("agnd", "vss", 0), ("vdd", "vss", 3)), 0),
    "sf_pushpull_output_opamp": (8, 8, (("agnd", "vdd", 0), ("agnd", "vss", 0), ("vdd", "vss", 8)), 0),
    "two_stage_ota": (3, 3, (("gnd", "vdd", 3),), 0),
    "two_stage_ota_sf": (4, 4, (("gnd", "vdd", 4),), 0),
}
BLOCKS = (s1_structure, s1_bulk, s1_dc_conduction, s1_gs_groups, s1_branches, s1_dc_roles, s1_rel_vgs,
          s1_rel_matching, s1_matching_groups, s1_gvgs, s1_columns, s1_rel_kcl)


def _s1(gh, name, **kw):
    return build_s1(gh.load_lib(name), gh.supplies_for(name), **kw)


def _stats():
    return {b.name: b.stats() for b in BLOCKS}


def _delta(before, after):
    return {k: (after[k].calls - before[k].calls, after[k].reuses - before[k].reuses,
                after[k].computes - before[k].computes) for k in before}


@pytest.mark.parametrize("name", NINE)
def test_oracle_matches_contract_table(gh, name):
    raw = gh.raw(name)
    o, split = gh.oracle(raw), gh.oracle(raw, merge=False)
    n_m, n_s, pairs, orph = TABLE[name]
    assert len(o.columns) == n_m
    assert sum(c[3] for c in o.columns) == n_s == len(split.columns)   # Σ parallel_expansion = 따로 센 기둥 수
    assert o.column_pairs == pairs
    assert len(o.column_orphans) == orph


@pytest.mark.parametrize("name", NINE)
def test_columns_match_oracle(gh, name):
    o = gh.oracle(gh.raw(name))
    s1 = _s1(gh, name)
    cols = gh.gval(s1, "columns")
    assert all(isinstance(c, Column) for c in cols)
    assert tuple(gh.column_plain(c) for c in cols) == o.columns
    assert gh.gval(s1, "column_pairs") == o.column_pairs
    orphans = gh.gval(s1, "column_orphans")
    assert all(isinstance(x, ColumnOrphan) for x in orphans)
    assert tuple(gh.astuple(x) for x in orphans) == o.column_orphans


@pytest.mark.parametrize("name", NINE)
def test_column_invariants(gh, name):
    # 7.3 불변식: 연속 가지가 넷을 공유, 내부 노드 레일 아님, r1 에서 시작 r2 에서 끝. 기둥끼리 같은 경로 없음.
    s1 = _s1(gh, name)
    agg = gh.agg(gh.raw(name))
    brs = {b.id: b for b in gh.gval(s1, "branches")}
    seen = set()
    for c in gh.gval(s1, "columns"):
        r1, r2 = c.rails
        assert r1 < r2 and r1 in agg.rails and r2 in agg.rails
        cur, visited = r1, {r1}
        for bid in c.branch_order:
            a, b = brs[bid].ends
            assert cur in (a, b) and a != b
            cur = b if a == cur else a
            assert cur not in visited
            visited.add(cur)
            if bid != c.branch_order[-1]:
                assert cur not in agg.rails
        assert cur == r2
        assert c.parallel_expansion == math.prod(len(s.elements) for bid in c.branch_order for s in brs[bid].segments)
        assert c.status == "derived" and c.evidence.rule == "rail_pair_simple_path" and c.evidence.nets == (r1, r2)
        src = any(brs[bid].has_ideal_source for bid in c.branch_order)
        assert c.evidence.basis == ("J13-a", "J13-b", "J13-c") + (("J13-d",) if src else ())
        assert (c.rails, c.branch_order) not in seen
        seen.add((c.rails, c.branch_order))
    assert [c.id for c in gh.gval(s1, "columns")] == list(range(len(seen)))


def test_pilot_41_62(gh):
    s1 = _s1(gh, "current_reuse_telescopic_ota")
    cols = gh.gval(s1, "columns")
    assert len(cols) == 41
    assert sum(c.parallel_expansion for c in cols) == 62


def test_orphan_branch_recorded_not_stopped(gh, tmp_path):
    # 레일에서 막다른 MOS 잎(dleaf)으로 가는 가지는 어느 레일 쌍 경로에도 없다 -> orphan(review_needed)
    raw = gh.raw("pushpull_follower_buffer")
    gate = next(e["gate"] for e in raw["netlist"] if e["kind"] == "nmos")
    raw["netlist"].append({"name": "Mleaf", "kind": "nmos", "drain": "dleaf", "gate": gate, "source": "vss"})
    o = gh.oracle(raw)
    s1 = build_s1(gh.load_raw(tmp_path, raw), gh.supplies_for("pushpull_follower_buffer"))
    orphans = gh.gval(s1, "column_orphans")
    assert tuple(gh.astuple(x) for x in orphans) == o.column_orphans
    assert len(orphans) == 1 and gh.astuple(orphans[0])[1] == "review_needed"
    leaf_branch = gh.astuple(orphans[0])[0]
    b = next(b for b in gh.gval(s1, "branches") if b.id == leaf_branch)
    assert set(b.ends) == {"dleaf", "vss"}
    assert len(gh.gval(s1, "columns")) == 3                          # 기둥 수는 그대로


# ------------------------------------------------------------------ column_limit


@pytest.mark.parametrize("name,limit,stops", [
    ("two_stage_ota", 1, True), ("two_stage_ota", 2, True), ("two_stage_ota", 3, False), ("two_stage_ota", 30, False),
    ("current_reuse_telescopic_ota", 40, True), ("current_reuse_telescopic_ota", 41, False),
    ("pushpull_follower_buffer", 0, True), ("pushpull_follower_buffer", 2, True),
])
def test_column_limit_boundary(gh, name, limit, stops):
    raw = gh.raw(name)
    if not stops:
        s1 = _s1(gh, name, column_limit=limit)
        assert len(gh.gval(s1, "columns")) == len(gh.oracle(raw).columns) <= limit
        return
    o_err = pytest.raises(gh.StopExpected, gh.oracle, raw, True, limit).value
    d, devices = gh.stop(lambda: _s1(gh, name, column_limit=limit))
    assert d["rule_branch"] == "column_enumeration_over_budget"
    assert devices == ()
    assert d["limit"] == limit
    assert d["rails"] == o_err.detail["rails"]


@pytest.mark.parametrize("bad", [True, False, -1, 1.5, "3", (3,)])
def test_column_limit_type_error(gh, bad):
    with pytest.raises(TypeError):
        _s1(gh, "two_stage_ota", column_limit=bad)


def test_column_limit_not_in_key(gh):
    a = _s1(gh, "two_stage_ota")
    b = _s1(gh, "two_stage_ota", column_limit=3)
    assert a.key == b.key and a.snapshot.fp == b.snapshot.fp


def test_previous_and_column_limit(gh):
    # 7.6: limit 없이 만든 S1 을 previous 로 limit=1 -> 반환하지 않고 정지(s1_columns 만 compute), limit=3 -> 같은 객체
    doc = gh.load_lib("two_stage_ota")
    sv = gh.supplies_for("two_stage_ota")
    s1 = build_s1(doc, sv)
    before = _stats()
    assert build_s1(doc, sv, previous=s1, column_limit=3) is s1
    assert all(v == (0, 0, 0) for v in _delta(before, _stats()).values())
    before = _stats()
    d, _ = gh.stop(lambda: build_s1(doc, sv, previous=s1, column_limit=1))
    assert d["rule_branch"] == "column_enumeration_over_budget"
    delta = _delta(before, _stats())
    assert delta["s1_columns"] == (1, 0, 1)
    for name, v in delta.items():
        if name not in ("s1_columns", "s1_rel_kcl"):
            assert v == (1, 1, 0), name                 # 앞 블록은 모두 reuse
    assert delta["s1_rel_kcl"] == (0, 0, 0)            # 정지 뒤 블록은 불리지 않는다


def test_block_declaration():
    assert isinstance(s1_columns, ComputeBlock)
    assert s1_columns.name == S1_COLUMNS_WRITER
    assert set(s1_columns.reads) == {("graph", "branches"), ("node", "is_rail")}
    assert set(s1_columns.writes) == {("graph", "columns"), ("graph", "column_pairs"), ("graph", "column_orphans")}


def test_direct_call_extras(gh):
    s1 = _s1(gh, "two_stage_ota")
    before = s1_columns.stats()
    assert s1_columns(s1.snapshot, None) is s1.snapshot                 # 같은 extras -> reuse
    after = s1_columns.stats()
    assert (after.reuses - before.reuses, after.computes - before.computes) == (1, 0)
    snap = s1_columns(s1.snapshot, 10)                                   # extras 다르면 재계산, 값은 같다
    assert snap.value("graph", "s1", "columns") == gh.gval(s1, "columns")
    with pytest.raises(TypeError):
        s1_columns(s1.snapshot, [3])
