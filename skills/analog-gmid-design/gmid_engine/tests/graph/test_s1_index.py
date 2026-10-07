"""graph/s1_index.py -- `terminal_index(devices, passives, sources)` (계약 6절).

넷 이름순 ((넷, ((원소, 단자), ...)), ...), bulk 미포함. 기대값 = topology JSON 직접 집계.
"""
from __future__ import annotations

import pytest

from gmid_engine.graph import terminal_index

SIX = (
    "common_gate_amplifier", "current_reuse_telescopic_ota", "ngcc_3stage_ff",
    "pushpull_follower_buffer", "sf_pushpull_output_opamp", "two_stage_ota_sf",
)


@pytest.mark.parametrize("name", SIX)
def test_index_matches_json_terminals(gh, name):
    agg = gh.agg(gh.raw(name))
    doc = gh.load_lib(name)
    idx = terminal_index(doc.devices, doc.passives, doc.sources)
    assert isinstance(idx, tuple)
    assert [n for n, _ in idx] == sorted(agg.terminals)
    assert dict(idx) == agg.terminals
    for _, ts in idx:
        assert isinstance(ts, tuple) and list(ts) == sorted(ts)
    # 모든 MOS 단자 3개 + 2단자 2개가 정확히 한 번씩
    n_entries = sum(len(ts) for _, ts in idx)
    assert n_entries == 3 * len(agg.mos) + 2 * (len(agg.passives) + len(agg.sources))


def test_bulk_not_indexed(gh, tmp_path):
    raw = gh.raw("common_gate_amplifier")
    for e in raw["netlist"]:
        e["bulk"] = "VB_well" if e["kind"] == "pmos" else "gnd"
    doc = gh.load_raw(tmp_path, raw)
    idx = dict(terminal_index(doc.devices, doc.passives, doc.sources))
    assert "VB_well" not in idx
    assert all(t in ("d", "g", "s") for ts in idx.values() for _, t in ts)
    assert idx["gnd"] == (("M1", "s"),)          # bulk 선언 gnd 는 단자로 세지 않는다


def test_input_order_irrelevant(gh):
    doc = gh.load_lib("sf_pushpull_output_opamp")
    a = terminal_index(doc.devices, doc.passives, doc.sources)
    b = terminal_index(tuple(reversed(doc.devices)), tuple(reversed(doc.passives)), tuple(reversed(doc.sources)))
    assert a == b


def test_two_terminal_order_follows_document(gh, tmp_path):
    raw = gh.raw("pushpull_follower_buffer")
    cl = next(e for e in raw["passive_elements"] if e["name"] == "CL")
    t0, t1 = cl["terminals"]
    doc = gh.load_raw(tmp_path, raw)
    idx = dict(terminal_index(doc.devices, doc.passives, doc.sources))
    assert ("CL", "t0") in idx[t0] and ("CL", "t1") in idx[t1]
    cl["terminals"] = [t1, t0]
    doc2 = gh.load_raw(tmp_path, raw, "swapped")
    idx2 = dict(terminal_index(doc2.devices, doc2.passives, doc2.sources))
    assert ("CL", "t1") in idx2[t0] and ("CL", "t0") in idx2[t1]


def test_empty_inputs():
    assert terminal_index((), (), ()) == ()
