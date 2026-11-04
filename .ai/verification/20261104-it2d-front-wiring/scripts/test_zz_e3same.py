"""판정 탐침(복제본 전용): 같은 PDK 선언 파일 자리에서 두 번 만들면 parent 경로와 대조 지문이 같은가(test 피검 코드·단언 그대로, tmp 자리만 같게)."""
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


@pytest.mark.parametrize("target", TARGETS)
def test_same(tmp_path, lut_sealed, monkeypatch, target):
    src = build_case(tmp_path / "src", circuit_c(), lut_sealed)
    bad = evaluate(src.sctx, th_sorted(theta_r4c(y=0.1, v1=1.5)), CELLS_C)
    assert bad.status == STATUS_FAILED
    root_a, root_b = tempfile.mkdtemp(prefix="s6e"), tempfile.mkdtemp(prefix="s6f")
    try:
        ra, la = _failed(tmp_path / "a", lut_sealed, root_a, bad.failure, target, True, monkeypatch)
        shutil.rmtree(tmp_path / "a", ignore_errors=True)
        rb, lb = _failed(tmp_path / "a", lut_sealed, root_b, bad.failure, target, False, monkeypatch)
    finally:
        shutil.rmtree(root_a, ignore_errors=True)
        shutil.rmtree(root_b, ignore_errors=True)
    row = {"target": target, "fp_same": ra.partial.fp == rb.partial.fp, "line_same": la["snapshot_fp"] == lb["snapshot_fp"], "obj_diff": ra.partial is not rb.partial}
    with open(OUT, "ab") as f:
        f.write((json.dumps(row) + "\n").encode("utf-8"))
