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
    return memo_of(write_lut(tmp_path_factory.mktemp("df_plain"), empty_bins=True))     # [WB-1 §4] bin 지도 없는 toy(한 bin 가정 test)


@pytest.fixture(scope="module")
def with_vdsat(tmp_path_factory):
    return memo_of(write_lut(tmp_path_factory.mktemp("df_vdsat"), vdsat=lambda g, s: 0.1 + 0.2 * g + 0.0 * s))


def _on_grid(v):
    return min(abs(v - g) for g in VGS_GRID) <= 1e-12


def test_function_names():
    # [card 20261104-hcs 계약 변경 -- 승인 대기] tol_vdsat_max 는 삭제(card §1·S8: 판정 여유에 tol 을 더하지 않고 sat_threshold 가 정본), vds_floor 가 옮겨 온다.
    assert {name for name, _region, _fn in DERIVED_FUNCTIONS} == {"edge_costs", "reference_vds", "param_row", "vds_floor"}


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


def test_tol_vdsat_max_is_removed_and_unknown_to_derived(plain):
    # [card 20261104-hcs 계약 변경 -- 승인 대기] 옛 '표 없으면 0' test 의 대체: 삭제된 이름은 모르는 이름이라 KeyError(0 으로 바꾸지 않는다).
    with pytest.raises(KeyError):
        derived(plain, "tol_vdsat_max", "nmos", W_KEY, 1e-6, 0.9)


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
    from pdk_min_w import min_finger_w_m
    mins = min_finger_w_m(k for _, k in dk)      # PDK 선언 양(card 20261104-wb1)
    lut = load_lut_set(loc.manifest_path, loc.cap_npz_path,
                       LutSpec(float(man.get("manufacturing_grid_m", 5e-9)), tuple(sorted(mins.items())), dk, (("nmos", "_n"), ("pmos", "_p"))),
                       pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_paths, bin_rule=loc.bin_rule_path)
    memo = memo_of(lut, 1 << 15)
    for kind in ("nmos", "pmos"):
        w_key = 1000                                                  # 레이아웃 전 폭 = 5 µm (sizing 1.3, lut 1.4 실측)
        e = derived(memo, "edge_costs", kind, w_key)
        anchors = set(lut.slice_map[(kind, w_key)].l_bins.anchor_bin)
        assert {b for b, _ in e.vgs_min_by_bin} == anchors
        assert e.vgs_min_v == min(v for _, v in e.vgs_min_by_bin)
        grid = lut.slice_map[(kind, w_key)].grids[1]
        assert min(abs(e.vgs_min_v - g) for g in grid) <= 1e-12


# ===========================================================================
# [card 20261104-hcs] S3 / S7 / S7b -- edge_costs.vds_min_v 는 포화 가능 점의 VDSAT 최솟값(tol 합 없음), vds_floor 는 derived 표
# oracle: (손) 아래 VDSAT 배열 지정으로 정답이 정해지는 합성 입력 / (b) vds_floor 는 sizing conftest `r4_vds_floor`(npz 직접).
# ===========================================================================
import numpy as np  # noqa: E402

from gmid_engine.lut import DERIVED_TABLES  # noqa: E402

from sizing.conftest import r4_arrays, r4_vds_floor, write_r4_lut  # noqa: E402

from .hcs_cases import memo_of as r4_memo_of, write_lut_with_vdsat  # noqa: E402

R4_W_KEY = 100


def _unsat_min_lut(root):
    """VDSAT = 0.5 + 0.0625·VGS, 단 VDS 열 0 은 0.125 + 0.0625·VGS. gm/ID = 20 − 8·VGS 단조라 마스크 전 칸 참, 분지 = 전부.
    VDS 격자 0.25 간격: VDS 0 열은 VDSAT 이 가장 작지만(0.125) 0 < 0.125 라 포화 아님; VDS 0.25 는 0.25 < 0.5 포화 아님; VDS 0.5 는 0.5 ≥ 0.5
    (VGS = 0, 등호 경계) -> 포화 가능 점의 VDSAT 최솟값 = 0.5 (손). 비포화 점까지 보면 0.125."""
    def fn(kind, a):
        v = 0.5 + 0.0625 * a["VGS"][None, :, None, None] + np.zeros(a["ID"].shape)
        v[:, :, 0, :] = 0.125 + 0.0625 * a["VGS"][None, :, None]
        return v
    return write_lut_with_vdsat(root, fn)


@pytest.mark.parametrize("kind", ["nmos", "pmos"])
def test_vds_cost_is_min_vdsat_over_saturable_points_not_unsaturated_ones(tmp_path, kind):
    e = derived(r4_memo_of(_unsat_min_lut(tmp_path)), "edge_costs", kind, R4_W_KEY)
    assert e.vds_min_v == 0.5                                       # 이진 분수라 정확(손)
    assert e.vds_min_v != 0.125


@pytest.mark.parametrize("kind", ["nmos", "pmos"])
def test_vds_cost_zero_and_no_saturation_filter_without_vdsat_column(tmp_path, kind):
    """S3: 열 없음 -> vds_min_v = 0.0 (사유 없는 0 이 정의, 포화 거르기 없음). 거르지 않으므로 VGS 비용은 '모든 점이 포화 가능'한 같은 LUT(VDSAT = 0)와 같다."""
    nocol = r4_memo_of(write_r4_lut(tmp_path / "n", vdsat=()))
    zero = r4_memo_of(write_lut_with_vdsat(tmp_path / "z", lambda k, a: np.zeros(a["ID"].shape)))
    en, ez = derived(nocol, "edge_costs", kind, R4_W_KEY), derived(zero, "edge_costs", kind, R4_W_KEY)
    assert en.vds_min_v == 0.0 and ez.vds_min_v == 0.0
    assert en.vgs_min_v == ez.vgs_min_v and en.vgs_min_by_bin == ez.vgs_min_by_bin


def test_vds_floor_is_registered_after_existing_derived_tables():
    assert "vds_floor" in DERIVED_TABLES and DERIVED_TABLES[-1] == "vds_floor"
    assert DERIVED_TABLES[:-1] == ("curve_report", "edge_costs", "midpoint_l_bin_checks", "noise_planes", "tol_mismatch_table",
                                   "tol_noise_table", "tol_v_table", "tol_vdsat_table")           # 기존 항목 그대로, 뒤에 추가


@pytest.mark.parametrize("kind,off_cols,off_points,want", [
    ("nmos", 0, (), 0.0),                                          # 꺼진 곳 없음 -> VDS 격자 최소
    ("nmos", 2, (), 0.5),                                          # VDS 열 0·1 꺼짐 -> 첫 켜진 열 0.5
    ("pmos", 1, (), 0.25),
    ("nmos", 0, ((0, 3, 5, 2),), 1.5),                             # VDS 열 5 의 한 점 GM = 0 -> 그 열 이후 전부 참인 첫 열 = 6 -> 1.5
])
def test_vds_floor_matches_independent_closed_form(tmp_path, kind, off_cols, off_points, want):
    assert "vds_floor" in DERIVED_TABLES                           # 신규 이름 등록(없으면 derived 가 KeyError 라 먼저 단언으로 거른다)
    lut = write_r4_lut(tmp_path, off_cols={kind: off_cols}, off_points={kind: off_points})
    got = derived(r4_memo_of(lut), "vds_floor", kind, R4_W_KEY)
    ref = r4_vds_floor(r4_arrays(kind, off_cols=off_cols, off_points=off_points))      # oracle (b)
    assert ref == want                                                                  # 입력 검사
    assert got == ref
