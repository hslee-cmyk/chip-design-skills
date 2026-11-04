"""판정 탐침(복제본 전용): T-E3 S3 줄 실패 원인 -- 두 부분 스냅샷의 필드별 차이."""
import json
import os
import shutil
import tempfile

import pytest

from gmid_engine.search import STATUS_FAILED, evaluate

from .conftest import CELLS_C, build_case, circuit_c, theta_r4c
from .test_kernel import th_sorted
from .test_it2e_partial_snapshot import _failed, TARGETS

OUT = os.environ["PROBE_OUT"]


def _fields(snap):
    out = {}
    for kind in snap.kinds():
        for key in snap.keys(kind):
            rec = snap.record(kind, key)
            for name in rec.field_names():
                fv = rec.get(name)
                out[(kind, key, name)] = (fv.value_fp, fv.writer, repr(fv.value)[:300])
    return out


@pytest.mark.parametrize("target", TARGETS)
def test_diag(tmp_path, lut_sealed, monkeypatch, target):
    src = build_case(tmp_path / "src", circuit_c(), lut_sealed)
    bad = evaluate(src.sctx, th_sorted(theta_r4c(y=0.1, v1=1.5)), CELLS_C)
    assert bad.status == STATUS_FAILED
    root_a, root_b = tempfile.mkdtemp(prefix="s6e"), tempfile.mkdtemp(prefix="s6f")
    try:
        ra, la = _failed(tmp_path / "a", lut_sealed, root_a, bad.failure, target, True, monkeypatch)
        rb, lb = _failed(tmp_path / "b", lut_sealed, root_b, bad.failure, target, False, monkeypatch)
    finally:
        shutil.rmtree(root_a, ignore_errors=True)
        shutil.rmtree(root_b, ignore_errors=True)
    fa, fb = _fields(ra.partial), _fields(rb.partial)
    rows = {"target": target, "fp_same": ra.partial.fp == rb.partial.fp, "only_a": sorted(map(str, set(fa) - set(fb))), "only_b": sorted(map(str, set(fb) - set(fa))),
            "ver_a": sorted(ra.partial.block_versions), "ver_b": sorted(rb.partial.block_versions), "theta_same": ra.theta == rb.theta, "theta_a": repr(ra.theta), "theta_b": repr(rb.theta)}
    rows["diff"] = [(str(k), fa[k][1], fa[k][2], fb[k][2]) for k in sorted(set(fa) & set(fb), key=str) if fa[k][0] != fb[k][0]]
    with open(OUT, "ab") as f:
        f.write((json.dumps(rows, ensure_ascii=False, default=str) + "\n").encode("utf-8"))
