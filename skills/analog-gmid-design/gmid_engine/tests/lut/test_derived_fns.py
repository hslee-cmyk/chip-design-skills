"""lut/derived_fns.py -- `derived(memo, name, *args)` LUT 파생 함수 (설계 40 v1.9.1 §2.4.6 'memo 로 옮기는 것' 표, §2.4.8 (a) 행 D10, 41 §4.6·§6).

[U17 ①-b] 옛 `metrics/edge_cost_bounds.py`(`edge_costs`)·`search/iv_curves.py`(`CurveBook.ref_vds`·`tol_vdsat`)·`ParamTables._load` 의 LUT 파생이
이 모듈의 memo 함수로 옮겨 왔다. 옛 tests/metrics/test_edge_cost_bounds.py·tests/search/test_iv_curves.py 의 **독립 기대값**(손 해석식)을 그대로 옮긴다:

oracle (a) 구성으로 정답이 정해진 합성 입력(tests/metrics/gb4_hand 해석식 toy: gm/ID = 20 − 8·VGS, gds/ID = LAM = 0.1, gmb/ID = 2A·VS (A = 2)):
- edge_costs: VGS 비용은 LUT VGS 격자 마디 하나이고 bin 별 최솟값의 최솟값, bin 지도 없는 toy 는 bin 하나. VDS 비용 = VDSAT 최솟값 + tol_vdsat 최솟값:
  VDSAT 열 없는 toy -> 0, VDSAT = 0.1 + 0.2·VGS(선형 -> tol_vdsat 0) -> 0.1 + 0.2·v_c (v_c = 비용 마디 또는 한 마디 위). best_row 의 gm_id = 20 − 8·VGS.
  실 LUT: bin 번호 = 슬라이스 L 앵커 bin 집합(lut 1.4).
- param_row: 강반전 분지 마디마다 x = 20 − 8·VGS, y = 0.1, z = 4·VS (gb4_hand 머리 '닫힌 식').
- tol_vdsat_max: 표를 못 만들면(VDSAT 열 없음) 0, 선형 VDSAT 은 tol_vdsat 0 수준(lut 7.1) -> 0.
- reference_vds: tests/search/u13_hand toy(VDSAT = 2/(gm/ID), 최솟값 0.1 V)에서 VDS 격자(0, 0.3, ...) 중 포화 경계 이상 첫 점 = 0.3 V(옛 test_iv_curves).
- memo: 같은 인자는 같은 객체(한 번 계산), 모르는 이름은 KeyError(모듈 docstring 계약). `EdgeCost` 는 frozen dataclass(lut 값 형식).
"""
from __future__ import annotations

import dataclasses
import sys
from pathlib import Path

import pytest

from gmid_engine.lut import DERIVED_FUNCTIONS, EdgeCost, derived

_TESTS = str(Path(__file__).resolve().parents[1])
if _TESTS not in sys.path:
    sys.path.insert(0, _TESTS)

from metrics.gb4_hand import A, LAM, VGS_GRID, VS_GRID, W_KEY, memo_of, write_lut  # noqa: E402

H = VGS_GRID[1] - VGS_GRID[0]


@pytest.fixture(scope="module")
def plain(tmp_path_factory):
    return memo_of(write_lut(tmp_path_factory.mktemp("df_plain")))


@pytest.fixture(scope="module")
def with_vdsat(tmp_path_factory):
    return memo_of(write_lut(tmp_path_factory.mktemp("df_vdsat"), vdsat=lambda g, s: 0.1 + 0.2 * g + 0.0 * s))


def _on_grid(v):
    return min(abs(v - g) for g in VGS_GRID) <= 1e-12


def test_function_names():
    assert {name for name, _region, _fn in DERIVED_FUNCTIONS} == {"edge_costs", "reference_vds", "tol_vdsat_max", "param_row"}


def test_edge_cost_is_frozen_lut_value_type():
    assert dataclasses.is_dataclass(EdgeCost) and EdgeCost.__dataclass_params__.frozen


@pytest.mark.parametrize("kind", ["nmos", "pmos"])
def test_vgs_cost_is_a_grid_node_and_bin_minimum(plain, kind):
    e = derived(plain, "edge_costs", kind, W_KEY)
    assert isinstance(e, EdgeCost)
    assert (e.kind, e.w_key) == (kind, W_KEY)
    assert _on_grid(e.vgs_min_v) and e.vgs_min_v >= 0.0
    assert len(e.vgs_min_by_bin) == 1
    assert e.vgs_min_v == min(v for _, v in e.vgs_min_by_bin)


@pytest.mark.parametrize("kind", ["nmos", "pmos"])
def test_vds_cost_is_zero_without_vdsat_column(plain, kind):
    assert derived(plain, "edge_costs", kind, W_KEY).vds_min_v == 0.0


@pytest.mark.parametrize("kind", ["nmos", "pmos"])
def test_vds_cost_is_vdsat_at_first_conducting_node(with_vdsat, kind):
    e = derived(with_vdsat, "edge_costs", kind, W_KEY)
    cands = (0.1 + 0.2 * e.vgs_min_v, 0.1 + 0.2 * (e.vgs_min_v + H))
    assert min(abs(e.vds_min_v - c) for c in cands) <= 1e-9, (e.vds_min_v, cands)
    assert e.vds_min_v >= 0.1 - 1e-12


def test_best_row_names_the_lut_coordinates(plain):
    e = derived(plain, "edge_costs", "nmos", W_KEY)
    assert {"L", "VDS", "VS", "gm_id"} <= {k for k, _ in e.best_row}
    row = dict(e.best_row)
    assert min(abs(row["gm_id"] - (20.0 - 8.0 * v)) for v in (e.vgs_min_v, e.vgs_min_v + H)) <= 1e-9


def test_memoised_and_deterministic(plain):
    a = derived(plain, "edge_costs", "nmos", W_KEY)
    assert derived(plain, "edge_costs", "nmos", W_KEY) is a
    assert a == derived(memo_of(plain.lut), "edge_costs", "nmos", W_KEY)


def test_unknown_name_is_keyerror(plain):
    with pytest.raises(KeyError):
        derived(plain, "no_such_function", "nmos", W_KEY)


@pytest.mark.parametrize("kind", ["nmos", "pmos"])
@pytest.mark.parametrize("vsb", [0.0, 0.45, 0.9])
def test_param_row_closed_forms(plain, kind, vsb):
    row = derived(plain, "param_row", kind, W_KEY, 1e-6, 0.9, vsb)
    assert row is not None
    vgs, x, y, z = row
    assert vgs and len(vgs) == len(x) == len(y) == len(z)
    for v, xv, yv, zv in zip(vgs, x, y, z):
        assert _on_grid(v)
        assert xv == pytest.approx(20.0 - 8.0 * v, rel=1e-9)
        assert yv == pytest.approx(LAM, rel=1e-9)
        assert zv == pytest.approx(2.0 * A * vsb, abs=1e-9)


def test_param_row_vs_axis_is_lut_grid():
    assert 0.45 in VS_GRID and 0.9 in VS_GRID          # 위 매개변수는 LUT 격자 마디(닫힌 식이 정확한 곳)


def test_tol_vdsat_max_zero_without_table_and_for_linear_vdsat(plain, with_vdsat):
    assert derived(plain, "tol_vdsat_max", "nmos", W_KEY, 1e-6, 0.9) == 0.0
    assert derived(with_vdsat, "tol_vdsat_max", "nmos", W_KEY, 1e-6, 0.9) == pytest.approx(0.0, abs=1e-12)


@pytest.mark.parametrize("kind", ["nmos", "pmos"])
def test_reference_vds_is_first_saturated_grid_point(kind):
    from search.u13_hand import memo_of as u13_memo_of
    from search.u13_hand import toy_env
    memo = u13_memo_of(toy_env(1.0).lut)
    assert derived(memo, "reference_vds", kind, 100, 1e-6) == pytest.approx(0.3, abs=1e-12)


def test_real_lut_bins_follow_slice_anchor_bins():
    """옛 test_edge_cost_bounds 실 LUT 성질: `vgs_min_by_bin` 의 bin 번호 = 그 슬라이스 L 앵커의 bin 번호 집합(lut 1.4), 최솟값 = bin 최솟값의 최솟값, VGS 격자 마디."""
    import json
    import os
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
        e = derived(memo, "edge_costs", kind, w_key)
        anchors = set(lut.slice_map[(kind, w_key)].l_bins.anchor_bin)
        assert {b for b, _ in e.vgs_min_by_bin} == anchors
        assert e.vgs_min_v == min(v for _, v in e.vgs_min_by_bin)
        grid = lut.slice_map[(kind, w_key)].grids[1]
        assert min(abs(e.vgs_min_v - g) for g in grid) <= 1e-12
