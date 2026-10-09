"""metrics/curve_checks.py -- `curve_checks(lut) -> CurveChecks` (metrics CONTRACT 10.2, 설계 41 4.1, D-GB4a).

oracle (a): 해석식 toy LUT 의 칸 분류를 손으로 센다.
- VGS(ln ID 2차, 기울기 = 정확한 미분) -> 모든 칸 Hermite·단조. VDS(1차) -> 모든 칸 Hermite·단조.
- VS: 기울기 −GMBS/ID = −2A·VS 는 GMBS/ID > 0(VS > 0) 인 점에서만 정의 -> 두 끝 VS > 0 인 칸 3 개(0.45-0.9, 0.9-1.35, 1.35-1.8)만 Hermite,
  나머지 2 개(−0.45-0, 0-0.45)는 기울기 미정의(선형 칸).
- 한 격자점 (iL, iG, iD, iS) 의 GM 을 5 배로 키우면 그 점을 끝으로 갖는 VGS 칸 두 개(iG−1, iG)가 Fritsch–Carlson 위반이다
  (b0 = m0·h, b2 = 5·m·h, b1 ≈ 3·m·h − b0 − b2 < 0, b1² > b0·b2 -- lut 1.4 [r5] 단조 조건을 손으로 대입).
oracle (b): 실 LUT(sky130 v2)에서는 lut 1.4 [r5]·[r7] 정의를 이 test 가 numpy 로 다시 구현해(`gb4_hand.curve_counts`) 슬라이스 npz 원시 배열에서
(kind, w_key, 축)별 칸 수·Hermite 칸 수·위반 칸 수를 직접 센다.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pytest

from gmid_engine.metrics import CurveCheck, CurveChecks, SliceCurveCheck, curve_checks

from .gb4_hand import GRIDS, L_GRID, VDS_GRID, VGS_GRID, VS_GRID, W_KEY, curve_counts, write_lut

NL, NG, ND, NS = (len(g) for g in GRIDS)
SPIKE = (1, 7, 3, 4)                     # (iL, iG, iD, iS) -- GM × 5


@pytest.fixture(scope="module")
def toy(tmp_path_factory):
    return write_lut(tmp_path_factory.mktemp("cc_toy"), gm_scale_at={"nmos": (SPIKE + (5.0,),)})


def _slices(cc):
    return {(s.kind, s.w_key, s.axis): s for s in cc.slices}


def test_toy_cell_counts_by_hand(toy):
    cc = curve_checks(toy)
    assert isinstance(cc, CurveChecks)
    s = _slices(cc)
    assert set(s) == {(k, W_KEY, ax) for k in ("nmos", "pmos") for ax in ("VGS", "VDS", "VS")}
    for kind in ("nmos", "pmos"):
        vgs, vds, vs = s[(kind, W_KEY, "VGS")], s[(kind, W_KEY, "VDS")], s[(kind, W_KEY, "VS")]
        assert isinstance(vgs, SliceCurveCheck)
        assert (vgs.n_cells, vgs.n_hermite, vgs.n_slope_undefined) == (NL * (NG - 1) * ND * NS, NL * (NG - 1) * ND * NS, 0)
        assert (vds.n_cells, vds.n_hermite, vds.n_violation, vds.n_slope_undefined) == (NL * NG * (ND - 1) * NS,) * 2 + (0, 0)
        assert (vs.n_cells, vs.n_hermite, vs.n_violation, vs.n_slope_undefined) == \
            (NL * NG * ND * (NS - 1), NL * NG * ND * 3, 0, NL * NG * ND * 2)
    assert s[("nmos", W_KEY, "VGS")].n_violation == 2
    assert s[("pmos", W_KEY, "VGS")].n_violation == 0
    assert cc.n_unit_mismatch == 0
    assert cc.lut_fp == toy.fp


def test_fc_violation_rows_point_at_the_two_cells(toy):
    cc = curve_checks(toy)
    rows = [r for r in cc.grid_only if r.kind == "nmos"]
    assert all(isinstance(r, CurveCheck) for r in cc.grid_only)
    iL, iG, iD, iS = SPIKE
    assert sorted(r.cell for r in rows) == [iG - 1, iG]
    for r in rows:
        assert (r.axis, r.reason, r.method) == ("VGS", "fc_violation", "grid_only")
        assert r.w_key == W_KEY
        assert r.L == pytest.approx(L_GRID[iL]) and r.vds == pytest.approx(VDS_GRID[iD]) and r.vs == pytest.approx(VS_GRID[iS])
    # 손 위반 칸은 독립 FC 판정과도 같다
    _, viol = curve_counts(_toy_arrays())
    assert sorted(v[1] for v in viol) == [iG - 1, iG]


def _toy_arrays():
    from .gb4_hand import slice_arrays
    return slice_arrays("nmos", gm_scale_at=(SPIKE + (5.0,),))


def test_deterministic(toy):
    assert curve_checks(toy) == curve_checks(toy)


# ---------------------------------------------------------------- 실 LUT (oracle (b))

DEVICE_KINDS = (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos"))
SKILL = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def real():
    """실 LUT(데이터가 없으면 FAIL -- skip 아님, tests/pipeline conftest 와 같은 정책)."""
    from gmid_engine.lut import LutSpec, load_lut_set, resolve_lut_location
    loc = resolve_lut_location(str(SKILL / "assets" / "lut_v2_location.json"), os.environ)
    man = json.loads(Path(loc.manifest_path).read_text(encoding="utf-8"))
    kinds = dict(DEVICE_KINDS)
    mins = {}
    for e in man["slices"]:
        mins[kinds[e["device"]]] = min(e["w_um"] * 1e-6, mins.get(kinds[e["device"]], float("inf")))
    spec = LutSpec(float(man.get("manufacturing_grid_m", 5e-9)), tuple(sorted(mins.items())), DEVICE_KINDS, (("nmos", "_n"), ("pmos", "_p")))
    lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, spec, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path)
    return lut, loc, man


def test_real_lut_counts_match_independent_numpy_fc(real):
    lut, loc, man = real
    cc = curve_checks(lut)
    got = {(s.kind, s.w_key, s.axis): (s.n_cells, s.n_hermite, s.n_violation) for s in cc.slices}
    kinds = dict(DEVICE_KINDS)
    root = Path(loc.manifest_path).parent
    grid = lut.spec.manufacturing_grid_m
    want = {}
    for e in man["slices"]:
        with np.load(root / e["file"]) as z:
            arrays = {k: np.asarray(z[k]) for k in ("ID", "GM", "GDS", "GMBS", "VGS", "VDS", "VS") if k in z.files}
            w_key = int(round(float(z["W"]) / grid))
        counts, _ = curve_counts(arrays)
        for ax, v in counts.items():
            want[(kinds[e["device"]], w_key, ax)] = v
    assert set(got) == set(want)
    assert got == want
    # 격자 전용 행 수 = FC 위반 칸 수 합
    assert len(cc.grid_only) == sum(v[2] for v in want.values())
