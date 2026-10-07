"""`check_axes` -- CONTRACT 4절 축 검사: 격자 최소·최대 밖(NaN 포함) -> SealViolationError(lut_axis_out_of_range),
detail axis·value·lo·hi + context. 클램프·외삽 없음, 끝점 자체는 축 안.
"""
import math

import numpy as np
import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.lut import AXES, check_axes, gm_id_curve, gmb, op_point

from .conftest import TOY_L, TOY_VDS, TOY_VGS, TOY_VS, detail_of

GRIDS = (TOY_L, TOY_VGS, TOY_VDS, TOY_VS)


def test_inside_and_exact_endpoints_pass():
    assert check_axes(GRIDS, AXES, (1.5e-6, 0.3, 0.7, 0.2)) is None
    for lo_hi in (0, -1):
        pt = tuple(g[lo_hi] for g in GRIDS)
        assert check_axes(GRIDS, AXES, pt) is None


@pytest.mark.parametrize("axis_i", range(4))
@pytest.mark.parametrize("side", ("lo", "hi"))
def test_outside_each_axis_rejected_with_detail(axis_i, side):
    g = GRIDS[axis_i]
    bad = math.nextafter(g[0], -math.inf) if side == "lo" else math.nextafter(g[-1], math.inf)
    pt = [x[0] for x in GRIDS]
    pt[axis_i] = bad
    with pytest.raises(SealViolationError) as ei:
        check_axes(GRIDS, AXES, tuple(pt), context=(("kind", "nmos"), ("w_key", 100)))
    det = detail_of(ei.value)
    assert det["reason"] == "lut_axis_out_of_range"
    assert det["axis"] == AXES[axis_i]
    assert det["value"] == bad
    assert det["lo"] == g[0] and det["hi"] == g[-1]
    assert det["kind"] == "nmos" and det["w_key"] == 100


def test_nan_rejected():
    with pytest.raises(SealViolationError) as ei:
        check_axes(GRIDS, AXES, (1e-6, float("nan"), 0.5, 0.0))
    det = detail_of(ei.value)
    assert det["axis"] == "VGS" and math.isnan(det["value"])


def test_numeric_inputs_converted_with_float():
    assert check_axes(GRIDS, AXES, (np.float32(2e-6), 1, np.float64(1.0), 0)) is None


@pytest.mark.parametrize("args", [
    (0.9e-6, 0.25, 0.5, 0.0),     # L 아래
    (3.1e-6, 0.25, 0.5, 0.0),     # L 위
    (1e-6, -0.01, 0.5, 0.0),      # VGS 아래
    (1e-6, 1.01, 0.5, 0.0),       # VGS 위
    (1e-6, 0.25, 0.49, 0.0),      # VDS 아래
    (1e-6, 0.25, 1.0, 0.500001),  # VS 위
])
def test_op_point_and_gmb_no_clamp(toy_memo, args):
    for fn in (op_point, gmb):
        with pytest.raises(SealViolationError) as ei:
            fn(toy_memo, "nmos", 100, *args)
        det = detail_of(ei.value)
        assert det["reason"] == "lut_axis_out_of_range"
        assert det["kind"] == "nmos" and det["w_key"] == 100


def test_contract_example_vsb(toy_memo):
    with pytest.raises(SealViolationError) as ei:
        op_point(toy_memo, "nmos", 100, 1e-6, 0.25, 0.5, 0.6)
    det = detail_of(ei.value)
    assert det["axis"] == "VS" and det["lo"] == 0.0 and det["hi"] == 0.5 and det["value"] == 0.6


def test_gm_id_curve_checks_l_vds_vs_but_not_vgs(toy_memo):
    with pytest.raises(SealViolationError) as ei:
        gm_id_curve(toy_memo, "nmos", 100, 1e-6, 1.2, 0.0)
    assert detail_of(ei.value)["axis"] == "VDS"
    c = gm_id_curve(toy_memo, "nmos", 100, 3e-6, 1.0, 0.5)     # 끝점 축 안
    assert tuple(c.vgs_grid) == TOY_VGS
