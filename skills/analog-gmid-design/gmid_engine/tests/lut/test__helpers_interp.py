"""`_helpers_interp` (multilinear_interp·multilinear_interp_point_multi) -- CONTRACT 6절 복사본 AST 해시와,
공개 조회(op_point·gm_id_curve)가 [r2] L 앵커 한 장에서 (VGS, VDS, VS) 다중선형 보간(로그공간)을 하는지 독립 구현과 대조한다
(독립 4축 구현에 L = 앵커를 넣으면 L 가중치 (1, 0) 이라 앵커 한 장 3축 보간과 같은 식).
"""
import math

import numpy as np
import pytest

from gmid_engine.lut import gm_id_curve, op_point

from .conftest import (LEGACY_SR, LUT_SRC, TOY_L, TOY_VDS, TOY_VGS, TOY_VS, ast_sha,
                       function_body, interp4, log_floor, rel_close, toy_slice_arrays)

H_INTERP = "d6bfc65c25e6e68f6b5f820c3a5a53ed6ed2429db00dc640ba15615dc7d69c54"
H_POINT_MULTI = "76e24d9d66e06b760dc79b9d69ac51143cec7238046f9ed3ffd27a4b624c7cba"


@pytest.mark.parametrize("old_name,new_name,expected,n_stmts", [
    ("_multilinear_interp", "multilinear_interp", H_INTERP, 8),
    ("_multilinear_interp_point_multi", "multilinear_interp_point_multi", H_POINT_MULTI, 7),
])
def test_copy_ast_hash(old_name, new_name, expected, n_stmts):
    old = function_body(LEGACY_SR, old_name)
    new = function_body(LUT_SRC / "_helpers_interp.py", new_name)
    assert len(old) == n_stmts and len(new) == n_stmts
    assert ast_sha(old) == expected, "옛 본문 해시가 계약 표와 다르다(해시 방법 확인용)"
    assert ast_sha(new) == expected


def _toy_logs(scale=1.0, W=1e-6):
    a = toy_slice_arrays(W, scale)
    return a, log_floor(a["ID"])[0], log_floor(a["GM"])[0], log_floor(a["GDS"])[0]


@pytest.mark.parametrize("pt", [
    (2e-6, 0.25, 0.75, 0.25),
    (3e-6, 0.9, 0.6, 0.1),
    (1e-6, 0.1, 1.0, 0.5),
    (3e-6, 1.0, 0.5, 0.0),
])
def test_op_point_offgrid_matches_independent_multilinear_toy(toy_memo, pt):
    a, lI, lG, lD = _toy_logs()
    grids = (TOY_L, TOY_VGS, TOY_VDS, TOY_VS)
    li, lg, ld = interp4(grids, lI, pt), interp4(grids, lG, pt), interp4(grids, lD, pt)
    vth = interp4(grids, a["VTH"], pt)
    op = op_point(toy_memo, "nmos", 100, *pt)
    w = 1e-6
    assert rel_close(op.IDu, math.exp(li) * pt[0] / w, 1e-12)
    assert rel_close(op.gm_over_id, math.exp(lg - li), 1e-12)
    assert rel_close(op.gm_gds, math.exp(lg - ld), 1e-12)
    assert rel_close(op.gds_per_w, math.exp(ld) / w, 1e-12)
    assert rel_close(op.vth, vth, 1e-12)


def test_gm_id_curve_offgrid_matches_independent_multilinear_toy(toy_memo):
    a, lI, lG, _ = _toy_logs()
    grids = (TOY_L, TOY_VGS, TOY_VDS, TOY_VS)
    L, vds, vsb = 2e-6, 0.8, 0.3
    c = gm_id_curve(toy_memo, "nmos", 100, L, vds, vsb)
    for j, v in enumerate(TOY_VGS):
        li = interp4(grids, lI, (L, v, vds, vsb))
        lg = interp4(grids, lG, (L, v, vds, vsb))
        assert rel_close(float(c.id_vals[j]), math.exp(li), 1e-12)
        assert rel_close(float(c.gm_id_vals[j]), math.exp(lg - li), 1e-12)


@pytest.mark.lut_realdata
def test_op_point_offgrid_matches_independent_multilinear_real(real_memo, raw_slice):
    rng = np.random.default_rng(474)
    for kind, wk in (("nmos", 72), ("pmos", 1000)):
        z = raw_slice(kind, wk)
        grids = (z["L"], z["VGS"], z["VDS"], z["VS"])
        lI, lG, lD = log_floor(z["ID"])[0], log_floor(z["GM"])[0], log_floor(z["GDS"])[0]
        W = float(z["W"])
        for _ in range(25):
            pt = (float(z["L"][int(rng.integers(0, len(z["L"])))]),) + tuple(
                float(rng.uniform(g[0], g[-1])) for g in grids[1:])
            li, lg, ld = interp4(grids, lI, pt), interp4(grids, lG, pt), interp4(grids, lD, pt)
            op = op_point(real_memo, kind, wk, *pt)
            assert rel_close(op.IDu, math.exp(li) * pt[0] / W, 1e-10), (kind, pt)
            assert rel_close(op.gm_over_id, math.exp(lg - li), 1e-10), (kind, pt)
            assert rel_close(op.gm_gds, math.exp(lg - ld), 1e-10), (kind, pt)
            assert rel_close(op.gds_per_w, math.exp(ld) / W, 1e-10), (kind, pt)
            assert rel_close(op.vth, interp4(grids, z["VTH"], pt), 1e-12), (kind, pt)
