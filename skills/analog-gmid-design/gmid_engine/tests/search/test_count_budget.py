"""search/count_budget.py -- `count_budget(lut, kinds, declared=None) -> int` (search CONTRACT U9 절, 설계 41 0절 N_S, D-NS).

oracle (b) 다른 방법의 직접 집계: N_S = Σ_kind Σ_(그 kind 의 폭 슬라이스) |L|·|VGS|·|VDS|·|VS| 를 이 test 가 npz 축 배열 길이로 직접 곱해 더한다
(엔진 LUT 로더·피검 함수 미사용). oracle (d): spec `structure_count_budget{value, source}` 선언이 있으면 그 값이 대체한다(41 0절 '선언값').
정의역: kind 가 비거나 그 kind 의 슬라이스가 없으면 `ValueError`(계약 U9).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pytest

from gmid_engine.authoring import CountBudgetDecl
from gmid_engine.search import count_budget

TESTS = Path(__file__).resolve().parents[1]
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))
from metrics.gb4_hand import GRIDS, write_lut  # noqa: E402

PER_SLICE = int(np.prod([len(g) for g in GRIDS]))          # 2·19·7·6 = 1596


@pytest.fixture(scope="module")
def toy(tmp_path_factory):
    # nmos 슬라이스 2 개(폭 1 µm, 2 µm), pmos 1 개
    return write_lut(tmp_path_factory.mktemp("cb_toy"), slices=(("nmos", 1e-6, 1.0), ("nmos", 2e-6, 1.0), ("pmos", 1e-6, 1.0)))


def test_toy_counts_by_kind(toy):
    assert PER_SLICE == 1596
    assert count_budget(toy, ("nmos",)) == 2 * PER_SLICE
    assert count_budget(toy, ("pmos",)) == PER_SLICE
    assert count_budget(toy, ("nmos", "pmos")) == 3 * PER_SLICE


def test_additive_over_kinds_and_order_free(toy):
    assert count_budget(toy, ("pmos", "nmos")) == count_budget(toy, ("nmos",)) + count_budget(toy, ("pmos",))


def test_declared_value_overrides(toy):
    assert count_budget(toy, ("nmos",), CountBudgetDecl(7, None)) == 7
    assert count_budget(toy, ("nmos", "pmos"), CountBudgetDecl(10 ** 9, None)) == 10 ** 9


def test_undefined_domain_raises(toy):
    with pytest.raises(ValueError):
        count_budget(toy, ())
    with pytest.raises(ValueError):
        count_budget(toy, ("nonexistent_kind",))


def test_deterministic(toy):
    assert count_budget(toy, ("nmos", "pmos")) == count_budget(toy, ("nmos", "pmos"))


def test_real_lut_matches_npz_axis_lengths():
    """실 LUT(데이터 없으면 FAIL). 기대값 = manifest 슬라이스 npz 축 길이 곱의 합(kind 별)."""
    from gmid_engine.lut import LutSpec, load_lut_set, resolve_lut_location
    skill = Path(__file__).resolve().parents[3]
    loc = resolve_lut_location(str(skill / "assets" / "lut_v2_location.json"), os.environ)
    man = json.loads(Path(loc.manifest_path).read_text(encoding="utf-8"))
    dk = (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos"))
    names = dict(dk)
    direct = {"nmos": 0, "pmos": 0}
    from pdk_min_w import min_finger_w_m
    mins = min_finger_w_m(names.values())      # PDK 선언 양(card 20261104-wb1)
    root = Path(loc.manifest_path).parent
    for e in man["slices"]:
        with np.load(root / e["file"]) as z:
            direct[names[e["device"]]] += len(z["L"]) * len(z["VGS"]) * len(z["VDS"]) * len(z["VS"])
    lut = load_lut_set(loc.manifest_path, loc.cap_npz_path,
                       LutSpec(float(man.get("manufacturing_grid_m", 5e-9)), tuple(sorted(mins.items())), dk, (("nmos", "_n"), ("pmos", "_p"))),
                       pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_paths, bin_rule=loc.bin_rule_path)
    assert count_budget(lut, ("nmos",)) == direct["nmos"]
    assert count_budget(lut, ("pmos",)) == direct["pmos"]
    assert count_budget(lut, ("nmos", "pmos")) == direct["nmos"] + direct["pmos"]
