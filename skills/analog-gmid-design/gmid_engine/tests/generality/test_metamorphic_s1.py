"""metamorphic: S1 구조 유도(U2~U4, `gmid_engine.graph.build_s1`)가 이름·순서·극성 변형을 따라가는가.

graph CONTRACT 머리 '대원칙': 규칙은 connectivity·선언만으로 판정하고, 이름은 결정론적 순서 tie-break 로만 쓴다 --
개수·불변량은 이름과 무관하다. 그래서
- 이름 치환(random_renaming): 유도 결과를 이름 무관 정준형(집합·다중집합)으로 풀면 '원래 결과에 치환표를 적용한 것'과 같다.
  id·걷는 방향·사이클 대표 소자처럼 이름 tie-break 로 정해지는 것은 정준형에서 뺀다(사이클은 개수·규칙 분포로만).
- 순서 섞기(shuffle_order)·태그 잡음: 스냅샷 지문(`snapshot.fp`)까지 그대로.
- 극성 뒤집기(flip_polarity): nmos<->pmos·레일 맞바꿈을 적용한 같은 구조(역할·순환수 그대로).
- 지원 밖 원소(syn_cascode 의 이상 전압원)는 변형 뒤에도 같은 분기로 정지하고 devices 가 치환표로 옮겨진다.
library 회로(9회로 중 큰 것)에도 같은 이름 치환을 건다.
"""
from __future__ import annotations

import collections
import dataclasses
import json
from pathlib import Path

import pytest

from gmid_engine.authoring import load_topology
from gmid_engine.core import StructureUnresolvedError
from gmid_engine.graph import GRAPH_KEY, build_s1

from .topogen import add_tag_noise, flip_polarity, random_renaming, rename, shuffle_order, synthetic_topologies

LIBRARY = Path(__file__).resolve().parents[3] / "assets" / "library"
SYNTH = sorted(synthetic_topologies())
STOPPING = {"syn_cascode": ("source_kind_unsupported", ("Vbn", "Vbp", "Vbq"))}   # 이상 전압원 3개(circuits.py 표)
BUILDING = [n for n in SYNTH if n not in STOPPING]
LIB = ("current_reuse_telescopic_ota", "ngcc_3stage_ff", "nmcnr_amplifier", "sf_pushpull_output_opamp",
       "pushpull_follower_buffer")
SEEDS = range(3)
KIND_SWAP = {"nmos": "pmos", "pmos": "nmos"}


def _lib(name):
    return json.loads((LIBRARY / (name + ".topology.json")).read_text(encoding="utf-8"))


def _build_doc(td):
    from gmid_engine.search import open_run
    donors, counters = open_run()          # [XRUN-F1 card B C0·C6] 변형마다 새 실행 하나
    return build_s1(td, None, donors=donors, counters=counters)


def _build(topo, doc):
    return _build_doc(topo.load(doc))


def _g(s1, f):
    return s1.value("graph", GRAPH_KEY, f)


def canon(s1, nm=lambda x: x, km=lambda k: k):
    """이름 무관 정준형. nm = 이름 치환, km = MOS kind 치환."""
    fs = lambda xs: frozenset(nm(x) for x in xs)  # noqa: E731
    seg = lambda s: (fs(s.nets), fs(s.elements))  # noqa: E731
    brs = {b.id: (fs(b.ends), frozenset(seg(s) for s in b.segments), b.has_ideal_source) for b in _g(s1, "branches")}
    ms = collections.Counter
    out = {
        "dc_pruned": frozenset((nm(e), r) for e, r in _g(s1, "dc_pruned")),
        "segments": frozenset(seg(s) for s in _g(s1, "dc_segments")),
        "branches": ms(brs.values()),
        "branch_nodes": frozenset(nm(k) for k, v in s1.column("node", "dc_branch_node") if v),
        "columns": ms((fs(c.rails), frozenset(brs[i] for i in c.branch_order), c.parallel_expansion, c.status,
                       c.evidence.basis) for c in _g(s1, "columns")),
        "column_pairs": {fs(p[:2]): p[2] for p in _g(s1, "column_pairs")},
        "orphans": ms(brs[dataclass_first(o)] for o in _g(s1, "column_orphans")),
        "gs_groups": frozenset((km(g.kind), nm(g.gate), nm(g.source), fs(g.members)) for g in _g(s1, "gs_groups")),
        "dc_role": {nm(k): (r.role, r.status, r.evidence.rule, tuple(nm(x) for x in r.evidence.nets),
                            fs(r.evidence.group), r.evidence.basis) for k, r in s1.column("device", "dc_role")},
    }
    for f in ("rel_equal_vgs", "rel_vds_eq_vgs", "rel_matching_ratio", "rel_l_class", "rel_matching_offset"):
        out[f] = ms((r.type, r.domain, fs(r.members), r.status, r.evidence.rule, fs(r.evidence.nets), r.evidence.basis)
                    for r in _g(s1, f))
    out["rel_kcl_group"] = ms((frozenset(fs(m) for m in r.members), fs(r.evidence.nets)) for r in _g(s1, "rel_kcl_group"))
    gv = _g(s1, "gvgs_summary")
    out["gvgs"] = (gv.cyclomatic, gv.v2_port0, gv.v2_port1, gv.v1, fs(gv.fixed_vgs), len(gv.port_diff))
    out["kvl"] = ms((r.evidence.rule, len(r.members)) for r in _g(s1, "rel_kvl_branch"))
    out["vds_sat"] = ms((nm(r.members[0]), len(r.members)) for r in gv.vds_saturation)
    return out


def dataclass_first(o):
    return dataclasses.astuple(o)[0]


# ------------------------------------------------------------------ 이름 치환


@pytest.mark.parametrize("name", BUILDING)
@pytest.mark.parametrize("seed", SEEDS)
def test_synthetic_renaming_follows_mapping(topo, name, seed):
    doc = synthetic_topologies()[name]
    m = random_renaming(doc, seed)
    a = _build(topo, doc)
    b = _build(topo, rename(doc, m))
    assert canon(b) == canon(a, nm=lambda x: m.get(x, x))
    assert canon(b) != canon(a)                     # 정준형이 이름을 실제로 담는다(공허한 비교 아님)


@pytest.mark.parametrize("name", LIB)
def test_library_renaming_follows_mapping(topo, name):
    doc = _lib(name)
    m = random_renaming(doc, 11)
    a = _build(topo, doc)
    b = _build(topo, rename(doc, m))
    ca, cb = canon(a, nm=lambda x: m.get(x, x)), canon(b)
    assert cb == ca
    # 이름 치환 뒤에도 기둥 수·따로 센 기둥 수는 그대로(파일럿 41/62 포함)
    assert len(_g(b, "columns")) == len(_g(a, "columns"))
    assert sum(c.parallel_expansion for c in _g(b, "columns")) == sum(c.parallel_expansion for c in _g(a, "columns"))


# ------------------------------------------------------------------ 순서 섞기·태그 잡음


@pytest.mark.parametrize("name", BUILDING + list(LIB))
@pytest.mark.parametrize("seed", SEEDS)
def test_shuffle_and_tag_noise_keep_snapshot(topo, name, seed):
    doc = synthetic_topologies()[name] if name in SYNTH else _lib(name)
    a = _build(topo, doc)
    b = _build(topo, add_tag_noise(shuffle_order(doc, seed), seed))
    assert b.key == a.key and b.snapshot.fp == a.snapshot.fp
    for f in ("dc_segments", "branches", "columns", "gs_groups", "rel_kvl_branch", "gvgs_summary"):
        assert _g(b, f) == _g(a, f)


# ------------------------------------------------------------------ 극성 뒤집기


@pytest.mark.parametrize("name", BUILDING)
def test_polarity_flip_mirrors_structure(topo, name):
    doc = synthetic_topologies()[name]
    flipped, swap = flip_polarity(doc)
    a = _build(topo, doc)
    b = _build(topo, flipped)
    assert canon(b) == canon(a, nm=lambda x: swap.get(x, x), km=lambda k: KIND_SWAP.get(k, k))
    twice, _ = flip_polarity(flipped)
    assert _build(topo, twice).snapshot.fp == a.snapshot.fp


def test_polarity_flip_library_two_rail(topo):
    doc = _lib("current_reuse_telescopic_ota")
    flipped, swap = flip_polarity(doc)
    a, b = _build(topo, doc), _build(topo, flipped)
    assert canon(b) == canon(a, nm=lambda x: swap.get(x, x), km=lambda k: KIND_SWAP.get(k, k))


# ------------------------------------------------------------------ 정지도 변형을 따라간다


@pytest.mark.parametrize("name", sorted(STOPPING))
@pytest.mark.parametrize("seed", SEEDS)
def test_unsupported_stop_follows_renaming_and_shuffle(topo, name, seed):
    doc = synthetic_topologies()[name]
    branch, devices = STOPPING[name]
    m = random_renaming(doc, seed)
    for variant, expect in ((doc, devices), (shuffle_order(doc, seed), devices),
                            (rename(doc, m), tuple(sorted(m[d] for d in devices))),
                            (flip_polarity(doc)[0], devices)):
        with pytest.raises(StructureUnresolvedError) as ei:
            _build_doc(load_topology(topo.write(variant)))
        d = dict(ei.value.record.detail)
        assert d["rule_branch"] == branch
        assert ei.value.record.devices == expect


def test_synthetic_inputs_are_nontrivial(topo):
    # 공허한 통과 방지: 합성 회로들이 실제로 기둥·gs 묶음·DC 역할을 만든다
    total_cols = total_groups = 0
    for name in BUILDING:
        s1 = _build(topo, synthetic_topologies()[name])
        total_cols += len(_g(s1, "columns"))
        total_groups += len(_g(s1, "gs_groups"))
        assert s1.column("device", "dc_role")
    assert total_cols >= len(BUILDING) and total_groups >= 1
