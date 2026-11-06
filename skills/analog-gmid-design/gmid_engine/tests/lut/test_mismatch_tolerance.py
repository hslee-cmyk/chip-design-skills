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


# ---------------------------------------------------------------------------
# [LM-1e §5 M-0·M-1] 셀 결합 `TolMismatchTable.at(L, vds, param)` -- `table_at` 하나를 쓴다(결합 셀이 모두 정의되면 max, 하나라도 None 이면 None).
# toy M: `MismatchToy`(DVGS 변수별 TOY_SHAPE 배열) -- 격자 TOY_L (1, 2, 3) µm, TOY_VGS (0, 0.5, 1), TOY_VDS (0.5, 1.0), TOY_VS (0, 0.5).
# vth0 = C·v² 에서 VDS index 0 열 전부 NaN(정의 없음) -- 실 LUT 의 '꺼진 VDS 열' 모양; voff 는 상수 1e-3.
# VDS 칸이 [0.5, 1.0] 하나라서 어느 조회 VDS 든 결합 셀 = 그 행의 VDS index 0·1 두 셀이다.
# 셀 손 값(위 모듈 oracle (a)): VGS 간격 h = 0.5 선형 LOO 오차 c·h², Richardson ÷ 2² -> C·0.25/4; 상수 변수 -> 0.
# ---------------------------------------------------------------------------

def _cell_of(T, i, b, param):
    return dict(T.cells[i][b].params)[param]                           # 변수 순서에 기대지 않는다


@pytest.fixture
def first_vds_off_table(tmp_path):
    L, v, d, s = toy_grid_mesh()
    vth0 = np.array(C * v * v, dtype=float)
    vth0[:, :, 0, :] = np.nan
    t = MismatchToy(tmp_path / "m", {"vth0": vth0, "voff": np.full(TOY_SHAPE, 1e-3)})
    return tol_mismatch_table(new_memo(t.load()), "nmos")


def test_cell_combine_m0_premise(first_vds_off_table):
    """M-0 전제(안 서면 M-1 이 이 입력으로 성립하지 않는다 -- 적재 거부 포함): 모든 행에서 vth0 셀 0 = None, 셀 1 = C·0.25/4, voff 셀 0·1 = 0.0."""
    T = first_vds_off_table
    assert len(T.cells) == len(TOY_L)
    for i in range(len(TOY_L)):
        assert _cell_of(T, i, 0, "vth0") is None
        assert abs(_cell_of(T, i, 1, "vth0") - C * 0.25 / 4) <= 1e-15
        assert _cell_of(T, i, 0, "voff") == 0.0 and _cell_of(T, i, 1, "voff") == 0.0


def test_cell_combine_m1_none_cell_makes_none(first_vds_off_table):
    """M-1: 결합 셀 일부가 None 인 변수(vth0)는 None(옛 규칙은 셀 1 값 C·0.25/4), 모두 정의인 변수(voff)는 max = 0.0, 모르는 변수는 ValueError."""
    T = first_vds_off_table
    for L in TOY_L:
        for vds in (0.5, 0.7, 1.0):
            assert T.at(L, vds, "vth0") is None, (L, vds)
            assert T.at(L, vds, "voff") == 0.0, (L, vds)
    with pytest.raises(ValueError):
        T.at(1e-6, 0.5, "nfactor")
