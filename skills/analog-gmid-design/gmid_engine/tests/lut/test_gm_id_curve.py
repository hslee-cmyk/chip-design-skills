"""`gm_id_curve` -- CONTRACT 4.1 표 [r5]: VGS 격자 마디마다 4.2 의 마디 값 -- `log_id_vals` = V_a, `id_vals = exp(V_a)`(폭 w_m 의 A),
`gm_id_vals` = S_a(정의 안 되면 NaN), `cell_ok` = VGS 칸 단조 조건, `vgs_grid` = 슬라이스 VGS 축, 배열 읽기 전용.
6절 [r5]: 옛 `_curve_arrays` 블록 복사는 패키지에서 빠졌다.
"""
import math

import numpy as np
import pytest

from gmid_engine.lut import Curve, gm_id_curve

from .conftest import (LEGACY_SR, R5_A, R5_B, TOY_VGS, RefSlice, anchor_w, anchored_block, ast_sha,
                       lut_package_window_hashes, r5_toy_lnid, rel_close)

H_CURVE = "a84728e5e100c2c99d70529188915128fcf02ed5b8fa660c7bcf85941718743f"


def test_legacy_curve_block_copy_removed():
    first, last = "n = len(", "result = (id_vals, gm_id_vals)"
    old = anchored_block(LEGACY_SR, "_gm_id_curve", first, last)
    assert len(old) == 7
    names = {"self": "sl", "_multilinear_interp": "multilinear_interp"}
    attrs = {"_grids_list": "grids_list", "_log_ID": "log_ID", "_log_GM": "log_GM"}
    assert ast_sha(old, names, attrs) == H_CURVE, "옛 구간(이름 바꿈 적용) 해시가 기록값과 다르다"
    hits = lut_package_window_hashes(7).get(H_CURVE, [])
    assert hits == [], "옛 _gm_id_curve 블록 복사가 패키지에 남아 있다: %r" % (hits,)


@pytest.mark.parametrize("w_key,scale", [(100, 1.0), (200, 2.0)])
def test_toy_grid_curve(toy_memo, w_key, scale):
    """CONTRACT 7.1 행: gm_id_vals = (20, 14, 8), log_id_vals − ln(1e-7) = (0.05, 8.55, 14.05), cell_ok (True, True)."""
    c = gm_id_curve(toy_memo, "nmos", w_key, 1e-6, 0.5, 0.0)
    assert isinstance(c, Curve)
    assert tuple(float(v) for v in c.vgs_grid) == TOY_VGS
    for got, exp in zip(c.gm_id_vals, (20.0, 14.0, 8.0)):
        assert rel_close(float(got), exp, 1e-12)
    for got, exp in zip(c.log_id_vals, (0.05, 8.55, 14.05)):
        assert abs(float(got) - math.log(scale) - math.log(1e-7) - exp) <= 1e-12
    for got, exp in zip(c.id_vals, (0.05, 8.55, 14.05)):
        assert rel_close(float(got), scale * 1e-7 * math.exp(exp), 1e-12)
    assert tuple(bool(x) for x in c.cell_ok) == (True, True)
    # VS 0.5: ID 절반, gm/ID 같음 / L 3e-6: ID 1/3
    c2 = gm_id_curve(toy_memo, "nmos", w_key, 3e-6, 1.0, 0.5)
    for j, v in enumerate(TOY_VGS):
        assert rel_close(float(c2.id_vals[j]), scale * math.exp(r5_toy_lnid(v, 1.0, 0.5, 3e-6)), 1e-12)
        assert rel_close(float(c2.gm_id_vals[j]), R5_A - 2 * R5_B * v, 1e-12)


def test_r4_toy_cell_ok(r4toy_memo):
    """CONTRACT 7.2: VGS 칸 0 위반·칸 1 단조 -> cell_ok (False, True). 마디 gm/ID = 저장 GM/ID = (20, 4, 1.5)
    (oracle (a): conftest r4 toy 구성 R4_GM_RATIO -- [r7] 1.4 단위 검사와 맞는 판, 손계산은 conftest R4_* 주석)."""
    c = gm_id_curve(r4toy_memo, "nmos", 100, 1e-6, 0.5, 0.0)
    assert tuple(bool(x) for x in c.cell_ok) == (False, True)
    assert len(c.cell_ok) == len(c.vgs_grid) - 1
    for got, exp in zip(c.gm_id_vals, (20.0, 4.0, 1.5)):
        assert rel_close(float(got), exp, 1e-12)


def test_undefined_node_is_nan(curve_lut):
    """4.1 표: on_mask 거짓 마디(ID 0)의 gm_id_vals 는 NaN, log_id_vals 는 1.4 바닥값의 로그."""
    vgs = (0.0, 0.5, 1.0)
    ids = (0.0, 1e-6, 1e-5)
    memo, _ = curve_lut(vgs, ids, (20.0, 10.0, 4.0))
    c = gm_id_curve(memo, "nmos", 100, 1e-6, 0.5, 0.0)
    assert math.isnan(float(c.gm_id_vals[0]))
    assert rel_close(float(c.gm_id_vals[1]), 10.0, 1e-12)
    assert rel_close(float(c.log_id_vals[0]), math.log(1e-6), 1e-15)        # 바닥 = 최소 양수 ID


def test_arrays_read_only(toy_memo):
    c = gm_id_curve(toy_memo, "nmos", 100, 1e-6, 0.5, 0.0)
    for arr in (c.id_vals, c.gm_id_vals, c.log_id_vals):
        with pytest.raises((ValueError, TypeError)):
            arr[0] = 1.0
    assert float(c.id_vals[0]) == pytest.approx(1e-7 * math.exp(0.05), rel=1e-12)


def test_curve_memo_region(toy_memo):
    a = gm_id_curve(toy_memo, "nmos", 100, 2e-6, 0.7, 0.2)
    b = gm_id_curve(toy_memo, "nmos", 100, 2e-6, 0.7, 0.2)
    assert a is b
    # [r2] memo 키에 앵커 index: 1 ulp 이내 L 은 같은 키
    c = gm_id_curve(toy_memo, "nmos", 100, math.nextafter(2e-6, 1.0), 0.7, 0.2)
    assert c is a
    st = dict(toy_memo.stats())["curve"]
    assert st.misses == 1 and st.hits == 2


def test_missing_width_keyerror(toy_memo):
    with pytest.raises(KeyError):
        gm_id_curve(toy_memo, "nmos", 150, 1e-6, 0.5, 0.0)


@pytest.mark.lut_realdata
def test_real_grid_curves_match_npz(real_memo, raw_slice):
    rng = np.random.default_rng(11)
    for kind, wk in (("nmos", 72), ("nmos", 1000), ("pmos", 1000), ("pmos", 84)):
        z = raw_slice(kind, wk)
        rs = RefSlice(z)
        for _ in range(12):
            iL, k, s = int(rng.integers(0, 12)), int(rng.integers(1, 49)), int(rng.integers(0, 10))
            I, G = z["ID"][iL, :, k, s], z["GM"][iL, :, k, s]
            c = gm_id_curve(real_memo, kind, wk, float(z["L"][iL]), float(z["VDS"][k]), float(z["VS"][s]))
            assert np.array_equal(np.asarray(c.vgs_grid, dtype=float), z["VGS"])
            pos = (I > 0) & (G > 0)
            assert pos.any()
            np.testing.assert_allclose(np.asarray(c.id_vals)[pos], I[pos], rtol=1e-12)
            np.testing.assert_allclose(np.asarray(c.gm_id_vals)[pos], (G / np.where(I > 0, I, 1))[pos], rtol=1e-11)
            # [r5] cell_ok = 격자 곡선의 FC 표(독립)
            assert tuple(bool(x) for x in c.cell_ok) == tuple(bool(x) for x in rs.fc_vgs[iL, :, k, s])


@pytest.mark.lut_realdata
def test_real_offgrid_curves_match_independent_hermite(real_memo, raw_slice):
    """VDS·VS 격자 밖 곡선 마디 = 4.2 의 V_a(VDS Hermite/선형)·S_a(선형)·cell_ok(모서리 FC) 독립 구현."""
    rng = np.random.default_rng(12)
    for kind, wk in (("nmos", 1000), ("pmos", 1000)):
        z = raw_slice(kind, wk)
        rs = RefSlice(z)
        for _ in range(10):
            iL = int(rng.integers(0, 12))
            vds = float(rng.uniform(0.05, 1.79))
            vsb = float(rng.uniform(0.0, 1.79))
            c = gm_id_curve(real_memo, kind, wk, float(z["L"][iL]), vds, vsb)
            V, S, ok = rs.curve(anchor_w(iL), vds, vsb)
            np.testing.assert_allclose(np.asarray(c.log_id_vals), V, rtol=1e-12)
            fin = np.isfinite(S)
            assert np.array_equal(np.isfinite(np.asarray(c.gm_id_vals)), fin)
            np.testing.assert_allclose(np.asarray(c.gm_id_vals)[fin], S[fin], rtol=1e-12)
            assert tuple(bool(x) for x in c.cell_ok) == ok


# ---------------------------------------------------------------- [r7] 칸 분류 `Curve.cell_class` (설계 41 §4.1 해법 매핑, CONTRACT 4.1 [r7])

from gmid_engine.lut import CLASS_HERMITE  # noqa: E402


def test_cell_class_r5_toy_all_hermite(toy_memo):
    c = gm_id_curve(toy_memo, "nmos", 100, 1e-6, 0.5, 0.0)
    assert tuple(c.cell_class) == (CLASS_HERMITE, CLASS_HERMITE) == ("hermite", "hermite")


def test_cell_class_r4_toy_fc_violation(r4toy_memo):
    """r4 toy 손계산(conftest R4_* 주석): VGS 칸 0 위반(b1² = 25.9 > 20), 칸 1 단조(b1 = 1.75 ≥ 0) -> ('fc_violation', 'hermite'),
    cell_ok 와 일치."""
    c = gm_id_curve(r4toy_memo, "nmos", 100, 1e-6, 0.5, 0.0)
    assert tuple(c.cell_class) == ("fc_violation", "hermite")
    assert tuple(bool(x) for x in c.cell_ok) == (False, True)


def test_cell_class_slope_undefined(curve_lut):
    """마디 2 의 GM = 0(gm/ID 정의 안 됨) -> 칸 1 은 끝 기울기가 없어 'slope_undefined'(선형 칸), 칸 0 은 단조 Hermite.
    칸 0: 마디 gm/ID (8, 5), h 0.5, Δln ID = 3(현 6 ∈ [5, 8] -- [r7] 1.4 단위 검사 일관; 옛 Δln ID = ln10 은 현 4.6 이 밖)
    -> b0 = 4, b2 = 2.5, b1 = 9 − 6.5 = 2.5 ≥ 0 (CONTRACT 1.4 조건 손계산)."""
    memo, _ = curve_lut((0.0, 0.5, 1.0), (1e-6, 1e-6 * math.exp(3.0), 1e-6 * math.exp(5.0)), (8.0, 5.0, 0.0))
    c = gm_id_curve(memo, "nmos", 100, 1e-6, 0.5, 0.0)
    assert tuple(c.cell_class) == ("hermite", "slope_undefined")
