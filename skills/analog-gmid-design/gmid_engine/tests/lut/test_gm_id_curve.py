"""`gm_id_curve` -- CONTRACT 4절: VGS 격자 전체에서 lnID·lnGM 보간, id_vals = exp(lnID)(폭 w_m 의 A),
gm_id_vals = exp(lnGM − lnID), vgs_grid = 슬라이스 VGS 축, 배열 읽기 전용. 6절 `_curve_arrays` 블록 복사 해시.
"""
import math

import numpy as np
import pytest

from gmid_engine.lut import Curve, gm_id_curve

from .conftest import LEGACY_SR, LUT_SRC, TOY_VGS, anchored_block, ast_sha, rel_close

H_CURVE = "a84728e5e100c2c99d70529188915128fcf02ed5b8fa660c7bcf85941718743f"


def test_copy_block_ast_hash():
    first, last = "n = len(", "result = (id_vals, gm_id_vals)"
    old = anchored_block(LEGACY_SR, "_gm_id_curve", first, last)
    new = anchored_block(LUT_SRC / "gm_id_curve.py", "_curve_arrays", first, last)
    assert len(old) == 7 and len(new) == 7
    names = {"self": "sl", "_multilinear_interp": "multilinear_interp"}
    attrs = {"_grids_list": "grids_list", "_log_ID": "log_ID", "_log_GM": "log_GM"}
    assert ast_sha(old, names, attrs) == H_CURVE, "옛 구간(이름 바꿈 적용) 해시가 계약 표와 다르다"
    assert ast_sha(new) == H_CURVE


@pytest.mark.parametrize("w_key,scale", [(100, 1.0), (200, 2.0)])
def test_toy_grid_curve(toy_memo, w_key, scale):
    c = gm_id_curve(toy_memo, "nmos", w_key, 1e-6, 0.5, 0.0)
    assert isinstance(c, Curve)
    assert tuple(float(v) for v in c.vgs_grid) == TOY_VGS
    for got, exp in zip(c.id_vals, (1e-7, 1e-6, 1e-5)):
        assert rel_close(float(got), exp * scale, 1e-12)
    for got, exp in zip(c.gm_id_vals, (20.0, 10.0, 4.0)):
        assert rel_close(float(got), exp, 1e-12)
    # VS 0.5: ID 절반, gm/ID 같음 / L 3e-6: ID 1/3
    c2 = gm_id_curve(toy_memo, "nmos", w_key, 3e-6, 1.0, 0.5)
    for got, exp in zip(c2.id_vals, (1e-7, 1e-6, 1e-5)):
        assert rel_close(float(got), exp * scale * 0.5 / 3.0, 1e-12)


def test_arrays_read_only(toy_memo):
    c = gm_id_curve(toy_memo, "nmos", 100, 1e-6, 0.5, 0.0)
    for arr in (c.id_vals, c.gm_id_vals):
        with pytest.raises((ValueError, TypeError)):
            arr[0] = 1.0
    assert float(c.id_vals[0]) == pytest.approx(1e-7, rel=1e-12)


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
        for _ in range(12):
            iL, k, s = int(rng.integers(0, 12)), int(rng.integers(1, 49)), int(rng.integers(0, 10))
            I, G = z["ID"][iL, :, k, s], z["GM"][iL, :, k, s]
            c = gm_id_curve(real_memo, kind, wk, float(z["L"][iL]), float(z["VDS"][k]), float(z["VS"][s]))
            assert np.array_equal(np.asarray(c.vgs_grid, dtype=float), z["VGS"])
            pos = (I > 0) & (G > 0)
            assert pos.any()
            np.testing.assert_allclose(np.asarray(c.id_vals)[pos], I[pos], rtol=1e-12)
            np.testing.assert_allclose(np.asarray(c.gm_id_vals)[pos], (G / np.where(I > 0, I, 1))[pos], rtol=1e-11)
