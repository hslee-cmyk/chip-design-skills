"""CONTRACT 3.17 `node_across_front(front, node, archive=None)` + I-9(커널 호출 0).

기대값: 각 front 점 스냅샷의 입력 열(dc_v·dc_rail_v·dc_writer·pins·dc_op)을 test 가 직접 읽는다.
"""
import json
from pathlib import Path

import pytest

from gmid_engine.search import NodeRow, find_front, node_across_front

from .conftest import build_case, circuit_c, col, node_v, theta_r4c

OP_FIELDS = ("vgs", "vds", "vsb", "current", "gm_id", "W", "L")


@pytest.fixture(scope="module")
def run(tmp_path_factory, lut_sealed):
    import os
    import shutil
    import tempfile
    root = tempfile.mkdtemp(prefix="s6q", dir=os.environ.get("TEMP") or None)
    case = build_case(tmp_path_factory.mktemp("fq"), circuit_c(), lut_sealed, eval_budget=40, archive_root=root)
    fr = find_front(case.sctx, [theta_r4c()])
    assert len(fr.front) >= 1
    runs = [json.loads(x) for x in (Path(root) / case.sctx.context_fp / "runs.jsonl").read_text(encoding="utf-8")
            .splitlines() if x.strip()]
    yield case, fr, runs[-1]
    shutil.rmtree(root, ignore_errors=True)


def expect_row(snap, node):
    V = node_v(snap)
    pins = dict(snap.column("device", "pins"))
    ops = col(snap, "device", "dc_op")
    devs = []
    for m in sorted(ops):
        terms = tuple(t for t, n in dict(pins[m]).items() if n == node)
        if terms:
            devs.append((m, tuple(sorted(terms)), tuple((f, getattr(ops[m], f)) for f in OP_FIELDS)))
    return V[node], col(snap, "node", "dc_writer")[node].tier, devs


def _norm(devices):
    out = []
    for m, terms, pairs in devices:
        out.append((m, tuple(sorted(terms)), tuple((k, v) for k, v in pairs)))
    return sorted(out)


@pytest.mark.parametrize("node", ["out", "vdd", "in"])
def test_memory_front_rows(run, node):
    case, fr, _ = run
    before = dict(case.sctx.counters)
    rows = node_across_front(fr.front, node)
    assert dict(case.sctx.counters) == before                              # I-9
    assert len(rows) == len(fr.front)
    for row, p in zip(rows, fr.front):
        assert isinstance(row, NodeRow)
        assert row.point_id == p.point_id and row.status == p.result.status
        v, tier, devs = expect_row(p.result.evaluation.snapshot, node)
        assert row.voltage == v and row.tier == tier
        assert _norm(row.devices) == sorted(devs)


def test_missing_node_key_error(run):
    _, fr, _ = run
    with pytest.raises(KeyError):
        node_across_front(fr.front, "no_such_node")


def test_archive_entries_match_memory(run):
    case, fr, rec = run
    mem = node_across_front(fr.front, "out")
    disk = node_across_front(tuple(rec["front"]), "out", case.sctx.archive)
    assert [(r.point_id, r.voltage, r.tier) for r in disk] == [(r.point_id, r.voltage, r.tier) for r in mem]
    assert [_norm(r.devices) for r in disk] == [_norm(r.devices) for r in mem]


def test_archive_entries_need_archive(run):
    _, _, rec = run
    with pytest.raises(ValueError):
        node_across_front(tuple(rec["front"]), "out")
