"""graph/s1_model.py -- `S1Graph(key, snapshot)` 질의(계약 5절).

- column: snapshot.column 과 같은 key 정렬 tuple. value: 값, 레코드·필드 없음 KeyError.
- (kind, field) 가 S1_WRITERS 밖 -> KeyError, writer 미계산 -> FieldNotComputed(빈 tuple 아님). build_s1 결과는 모든 권한표 필드가 계산돼 있다(C2: 예약 필드 없음).
- 결정론: snapshot.fp 가 프로세스·PYTHONHASHSEED·netlist 순서와 무관.
"""
from __future__ import annotations

import dataclasses
import json
import os
import subprocess
import sys

import pytest

from gmid_engine.core import GraphSnapshot, fp_of
from gmid_engine.graph import (
    GRAPH_KEY,
    S1_BULK_WRITER,
    S1_STRUCTURE_WRITER,
    S1_WRITERS,
    FieldNotComputed,
    S1Graph,
    build_s1,
    s1_structure,
)

SIX = (
    "common_gate_amplifier", "current_reuse_telescopic_ota", "ngcc_3stage_ff",
    "pushpull_follower_buffer", "sf_pushpull_output_opamp", "two_stage_ota_sf",
)

# 9회로 전부(2026-10-07 topology 정정 b9c7042 뒤 모두 load 통과) -- JSON 직접 집계 대조용
NINE = tuple(sorted(SIX + ("folded_cascode", "nmcnr_amplifier", "two_stage_ota")))


def _build(*args, **kw):
    """`build_s1(..., donors=, counters=)` -- [XRUN-F1 card B C0·C6] 부를 때마다 새 실행 하나(새 open_run() 쌍)."""
    from gmid_engine.search import open_run
    donors, counters = open_run()
    return build_s1(*args, donors=donors, counters=counters, **kw)


def _s1(gh, name):
    return _build(gh.load_lib(name), gh.supplies_for(name))


def test_frozen_and_fields(gh):
    s1 = _s1(gh, "common_gate_amplifier")
    assert [f.name for f in dataclasses.fields(S1Graph)] == ["key", "snapshot"]
    assert isinstance(s1.snapshot, GraphSnapshot)
    assert s1.snapshot.writers == S1_WRITERS
    with pytest.raises(dataclasses.FrozenInstanceError):
        s1.key = None  # type: ignore[misc]


@pytest.mark.parametrize("name", NINE)
def test_column_equals_snapshot_column_sorted_tuple(gh, name):
    s1 = _s1(gh, name)
    for (kind, field), writer in S1_WRITERS.entries:
        col = s1.column(kind, field)
        assert isinstance(col, tuple)
        assert col == s1.snapshot.column(kind, field)
        keys = [k for k, _ in col]
        assert keys == sorted(keys)
        for k, v in col:
            assert s1.value(kind, k, field) == v


@pytest.mark.parametrize("name", NINE)
def test_every_writer_field_computed_after_build(gh, name):
    s1 = _s1(gh, name)
    writers = {w for _, w in S1_WRITERS.entries}
    for w in writers:
        assert s1.snapshot.block_version(w) is not None, w
    for (kind, field), _w in S1_WRITERS.entries:
        s1.column(kind, field)                          # FieldNotComputed 없음
        if kind == "graph":
            assert s1.snapshot.keys("graph") == (GRAPH_KEY,)
            assert s1.value("graph", GRAPH_KEY, field) == dict(s1.column("graph", field))[GRAPH_KEY]


def test_old_reserved_rows_gone(gh):
    # C2: 옛 예약 (edge, relation) 은 권한표 밖 -> KeyError(FieldNotComputed 아님)
    s1 = _s1(gh, "ngcc_3stage_ff")
    with pytest.raises(KeyError) as ei:
        s1.column("edge", "relation")
    assert not isinstance(ei.value, FieldNotComputed)


def test_outside_writer_table_key_error(gh):
    s1 = _s1(gh, "ngcc_3stage_ff")
    for kind, field in (("device", "w"), ("node", "voltage"), ("graph", "terminals"), ("device", "dc_roles")):
        with pytest.raises(KeyError) as ei:
            s1.column(kind, field)
        assert not isinstance(ei.value, FieldNotComputed)
        with pytest.raises(KeyError) as ei:
            s1.value(kind, "M0", field)
        assert not isinstance(ei.value, FieldNotComputed)


def test_value_missing_record_or_field_key_error(gh):
    s1 = _s1(gh, "ngcc_3stage_ff")
    agg = gh.agg(gh.raw("ngcc_3stage_ff"))
    with pytest.raises(KeyError):
        s1.value("device", "NO_SUCH_DEVICE", "kind")
    with pytest.raises(KeyError):
        s1.value("node", "NO_SUCH_NET", "is_rail")
    cap = sorted(agg.passives)[0]
    with pytest.raises(KeyError):
        s1.value("device", cap, "is_diode")          # 수동소자에는 MOS 전용 필드 없음
    with pytest.raises(KeyError):
        s1.value("device", cap, "bulk")


def test_not_computed_on_empty_snapshot(gh):
    key = _s1(gh, "common_gate_amplifier").key
    empty = S1Graph(key, GraphSnapshot.empty(S1_WRITERS))
    for kind, field in (("node", "terminals"), ("device", "bulk"), ("device", "pins")):
        with pytest.raises(FieldNotComputed):
            empty.column(kind, field)
        with pytest.raises(FieldNotComputed):
            empty.value(kind, "x", field)


def test_structure_only_snapshot_bulk_not_computed(gh):
    # s1_structure 만 돈 스냅샷: 구조 필드는 질의되고 bulk 는 FieldNotComputed(빈 tuple 아님)
    doc = gh.load_lib("pushpull_follower_buffer")
    snap = s1_structure(GraphSnapshot.empty(S1_WRITERS), doc.devices, doc.passives, doc.sources,
                        tuple(sorted(doc.rails)), doc.ports, **gh.fresh_run())
    g = S1Graph(_build(doc, None).key, snap)
    assert len(g.column("node", "terminals")) == len(gh.agg(gh.raw("pushpull_follower_buffer")).nodes)
    with pytest.raises(FieldNotComputed):
        g.column("device", "bulk")
    for kind, field in (("graph", "dc_segments"), ("graph", "columns"), ("device", "dc_role"), ("graph", "gvgs_summary")):
        with pytest.raises(FieldNotComputed):
            g.column(kind, field)
        with pytest.raises(FieldNotComputed):
            g.value(kind, GRAPH_KEY, field)


# ------------------------------------------------------------------ 결정론


_DET_SCRIPT = r"""
import json, random, sys
sys.path.insert(0, sys.argv[1])
from gmid_engine.authoring import load_topology
from gmid_engine.graph import build_s1
from gmid_engine.search import open_run
lib, out_dir = sys.argv[2], sys.argv[3]
spec = json.loads(sys.argv[4])
res = {}
for name, sv in spec.items():
    p = lib + "/" + name + ".topology.json"
    raw = json.load(open(p, encoding="utf-8"))
    random.Random(int(sys.argv[5])).shuffle(raw["netlist"])
    q = out_dir + "/" + name + ".shuf.topology.json"
    open(q, "w", encoding="utf-8").write(json.dumps(raw))
    for tag, path in (("orig", p), ("shuf", q)):
        donors, counters = open_run()   # [XRUN-F1 card B C6] S1 하나 = 새 실행 하나
        s1 = build_s1(load_topology(path), sv, donors=donors, counters=counters)
        res[name + "/" + tag] = [s1.snapshot.fp, s1.key.topology_fp, s1.key.rule_fp, s1.key.supplies_v_fp]
print(json.dumps(res, sort_keys=True))
"""


def test_snapshot_fp_deterministic_across_hash_seeds_and_order(gh, tmp_path):
    spec = {n: gh.supplies_for(n) for n in NINE}
    results = []
    for i, seed in enumerate(("0", "1", "31337", "random")):
        d = tmp_path / ("run%d" % i)
        d.mkdir()
        env = dict(os.environ, PYTHONHASHSEED=seed, PYTHONDONTWRITEBYTECODE="1")
        out = subprocess.run(
            [sys.executable, "-c", _DET_SCRIPT, str(gh.SKILL_DIR), str(gh.LIBRARY), str(d), json.dumps(spec), str(i + 3)],
            capture_output=True, text=True, env=env, check=True)
        results.append(json.loads(out.stdout))
    assert all(r == results[0] for r in results)
    for name in NINE:
        assert results[0][name + "/orig"] == results[0][name + "/shuf"]
    # 이 프로세스 값과도 같다
    for name in NINE:
        s1 = _s1(gh, name)
        assert results[0][name + "/orig"][0] == s1.snapshot.fp


def test_different_circuits_different_fp(gh):
    fps = {_s1(gh, n).snapshot.fp for n in NINE}
    assert len(fps) == len(NINE)


def test_key_fp_equal_for_equal_inputs(gh):
    # 같은 doc·supplies_v 로 별도 빌드한 키는 == 이고 fp_of 도 같다. supplies 유무가 다르면 다르다.
    name = "two_stage_ota_sf"
    s1 = _s1(gh, name)
    again = _build(gh.load_lib(name), gh.supplies_for(name)).key
    assert s1.key == again and fp_of(s1.key) == fp_of(again)
    assert fp_of(s1.key) != fp_of(_build(gh.load_lib(name), None).key)
