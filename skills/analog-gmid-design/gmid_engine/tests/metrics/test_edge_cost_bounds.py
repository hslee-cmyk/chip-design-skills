"""metrics/edge_cost_bounds.py -- `edge_costs(memo, kind, w_key) -> EdgeCost` (metrics CONTRACT 10.6, 설계 41 4.6 '|VGS|_min·VDSAT_min 은
그 kind 의 LUT 격자 전수 최솟값', D-GB4f).

oracle (a) 성질(구성으로 정해진 합성 입력):
- VGS 비용은 강반전 분지·전도 봉인을 지키는 격자 마디 VGS 의 최솟값(마디 사이 보간 해상도로 한 마디 아래로 내림, 계약 10.6) -> LUT VGS 격자 값 중 하나,
  `vgs_min_v` = `vgs_min_by_bin` 의 최솟값. bin 지도가 없는 toy(모델 파일 기록 없음)는 bin 하나.
- VDS 비용 = (분지·전도 마디의 VDSAT 최솟값, 열이 없으면 0) + (tol_vdsat 최솟값, 표를 못 만들면 0):
  · VDSAT 열 없는 toy -> 0 + 0 = 0.
  · VDSAT = 0.1 + 0.2·VGS(VGS 1차, VS·VDS 무관 -> 선형 LOO 차 0 이라 tol_vdsat 최솟값 0, lut 7.1 '선형 자료 0 수준') -> VDS 비용 =
    0.1 + 0.2·v_c, v_c = 전도를 처음 지키는 마디 = VGS 비용 마디 또는 그 한 마디 위.
- 실 LUT: `vgs_min_by_bin` 의 bin 번호 = 그 슬라이스 L 앵커의 bin 번호 집합(lut 1.4 `DcSlice.l_bins.anchor_bin`).
"""
from __future__ import annotations

import pytest

from gmid_engine.metrics import EdgeCost, edge_costs

from .gb4_hand import VGS_GRID, W_KEY, memo_of, write_lut

H = VGS_GRID[1] - VGS_GRID[0]


@pytest.fixture(scope="module")
def plain(tmp_path_factory):
    return memo_of(write_lut(tmp_path_factory.mktemp("ec_plain")))


@pytest.fixture(scope="module")
def with_vdsat(tmp_path_factory):
    return memo_of(write_lut(tmp_path_factory.mktemp("ec_vdsat"), vdsat=lambda g, s: 0.1 + 0.2 * g + 0.0 * s))


def _on_grid(v):
    return min(abs(v - g) for g in VGS_GRID) <= 1e-12


@pytest.mark.parametrize("kind", ["nmos", "pmos"])
def test_vgs_cost_is_a_grid_node_and_bin_minimum(plain, kind):
    e = edge_costs(plain, kind, W_KEY)
    assert isinstance(e, EdgeCost)
    assert (e.kind, e.w_key) == (kind, W_KEY)
    assert _on_grid(e.vgs_min_v) and e.vgs_min_v >= 0.0
    assert len(e.vgs_min_by_bin) == 1                                # bin 지도 없음 -> bin 하나
    assert e.vgs_min_v == pytest.approx(min(v for _, v in e.vgs_min_by_bin), abs=0)


@pytest.mark.parametrize("kind", ["nmos", "pmos"])
def test_vds_cost_is_zero_without_vdsat_column(plain, kind):
    assert edge_costs(plain, kind, W_KEY).vds_min_v == 0.0


@pytest.mark.parametrize("kind", ["nmos", "pmos"])
def test_vds_cost_is_vdsat_at_first_conducting_node(with_vdsat, kind):
    e = edge_costs(with_vdsat, kind, W_KEY)
    cands = (0.1 + 0.2 * e.vgs_min_v, 0.1 + 0.2 * (e.vgs_min_v + H))
    assert min(abs(e.vds_min_v - c) for c in cands) <= 1e-9, (e.vds_min_v, cands)
    assert e.vds_min_v >= 0.1 - 1e-12                               # VDSAT 열 최솟값(VGS = 0)보다 작을 수 없다


def test_best_row_names_the_lut_coordinates(plain):
    e = edge_costs(plain, "nmos", W_KEY)
    keys = {k for k, _ in e.best_row}
    assert {"L", "VDS", "VS", "gm_id"} <= keys
    row = dict(e.best_row)
    # gm/ID 는 해석식 B − C·VGS(VGS = 비용 마디 또는 한 마디 위)
    assert min(abs(row["gm_id"] - (20.0 - 8.0 * v)) for v in (e.vgs_min_v, e.vgs_min_v + H)) <= 1e-9


def test_deterministic(plain):
    assert edge_costs(plain, "nmos", W_KEY) == edge_costs(plain, "nmos", W_KEY)


def test_real_lut_bins_follow_slice_anchor_bins():
    import json
    import os
    from pathlib import Path
    from gmid_engine.lut import LutSpec, load_lut_set, resolve_lut_location
    skill = Path(__file__).resolve().parents[3]
    loc = resolve_lut_location(str(skill / "assets" / "lut_v2_location.json"), os.environ)
    man = json.loads(Path(loc.manifest_path).read_text(encoding="utf-8"))
    dk = (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos"))
    mins = {}
    for en in man["slices"]:
        k = dict(dk)[en["device"]]
        mins[k] = min(en["w_um"] * 1e-6, mins.get(k, float("inf")))
    lut = load_lut_set(loc.manifest_path, loc.cap_npz_path,
                       LutSpec(float(man.get("manufacturing_grid_m", 5e-9)), tuple(sorted(mins.items())), dk, (("nmos", "_n"), ("pmos", "_p"))),
                       pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path)
    memo = memo_of(lut, 1 << 15)
    for kind in ("nmos", "pmos"):
        w_key = 1000                                                  # 레이아웃 전 폭 = 5 µm (sizing 1.3, lut 1.4 실측)
        e = edge_costs(memo, kind, w_key)
        anchors = set(lut.slice_map[(kind, w_key)].l_bins.anchor_bin)
        assert {b for b, _ in e.vgs_min_by_bin} == anchors
        assert e.vgs_min_v == min(v for _, v in e.vgs_min_by_bin)
        grid = lut.slice_map[(kind, w_key)].grids[1]
        assert min(abs(e.vgs_min_v - g) for g in grid) <= 1e-12
