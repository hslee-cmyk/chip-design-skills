"""`tol_mismatch_table` -- CONTRACT 10.3 [r7], 설계 41 §6.4-2b 'tol: 칸별 tol_mismatch 를 LOO 로(DEC-87 방법)'.

oracle (a): DVGS_vth0 = c·v² (V) -> VGS 간격 0.5 선형 LOO 오차 = c·h², ÷ 2² = c·h²/4(값 공간, V); 1차식 변수 -> 0.
"""
import numpy as np
import pytest

from gmid_engine.lut import TolMismatchTable, tol_mismatch_table

from .conftest import TOY_L, TOY_SHAPE, MismatchToy, new_memo, toy_grid_mesh

C = 4e-3


@pytest.fixture
def quad_mm(tmp_path):
    L, v, d, s = toy_grid_mesh()
    t = MismatchToy(tmp_path / "q", {"vth0": C * v * v, "toxe": 1e-3 + 2e-3 * v + 1e-3 * d, "voff": np.full(TOY_SHAPE, 1e-3)})
    return new_memo(t.load())


def test_quadratic_variable_cell_value(quad_mm):
    T = tol_mismatch_table(quad_mm, "nmos")
    assert isinstance(T, TolMismatchTable)
    assert set(T.params) == {"toxe", "voff", "vth0"}
    for L in TOY_L:
        for vds in (0.5, 0.7, 1.0):
            assert abs(T.at(L, vds, "vth0") - C * 0.25 / 4) <= 1e-15
            assert abs(T.at(L, vds, "toxe")) <= 1e-15
            assert abs(T.at(L, vds, "voff")) <= 1e-15


def test_unknown_param_rejected(quad_mm):
    with pytest.raises(ValueError):
        tol_mismatch_table(quad_mm, "nmos").at(1e-6, 0.5, "nfactor")


def test_nan_points_skipped(tmp_path):
    """NaN 칸은 LOO 점에서 빠진다: 모든 점이 NaN 인 변수의 셀 값은 None."""
    L, v, d, s = toy_grid_mesh()
    t = MismatchToy(tmp_path / "n", {"vth0": C * v * v, "toxe": np.full(TOY_SHAPE, np.nan), "voff": 0 * v})
    T = tol_mismatch_table(new_memo(t.load()), "nmos")
    assert T.at(1e-6, 0.5, "toxe") is None
    assert abs(T.at(1e-6, 0.5, "vth0") - C * 0.25 / 4) <= 1e-15
