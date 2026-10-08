"""`mismatch_dvgs` -- CONTRACT 10.2 [r7], 설계 41 §6.4-2b API `mismatch_dvgs(kind, w_key, L, VGS, VDS, VS) -> MismatchSens{dvgs, slope_ref}`.

oracle: (a) DVGS 가 모든 축 1차식인 합성 입력 -> 보간(모든 축 선형)이 정확히 재현하므로 격자 밖 기대값은 닫힌 식;
(c) 실데이터 격자점 = r1 npz 원소 그대로, 칸 중앙 = npz 의 4축 다중선형(conftest `interp4`, 독립 구현).
"""
import math

import numpy as np
import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.lut import MismatchSens, mismatch_dvgs

from .conftest import MISMATCH_SLOPE_REF, TOY_SHAPE, MismatchToy, detail_of, interp4, new_memo, toy_grid_mesh

COEF = {"vth0": (1e-3, 2e-4, 1e-4, -3e-4), "toxe": (2e-3, 1e-3, 0.0, 5e-4), "voff": (5e-4, -1e-4, 2e-4, 1e-4)}


def _lin(c, v, d, s):
    return c[0] + c[1] * v + c[2] * d + c[3] * s


@pytest.fixture
def lin_mm(tmp_path):
    L, v, d, s = toy_grid_mesh()
    t = MismatchToy(tmp_path / "m", {p: _lin(c, v, d, s) for p, c in COEF.items()})
    return new_memo(t.load())


@pytest.mark.parametrize("pt", [(0.5, 0.5, 0.0), (0.25, 0.75, 0.25), (0.9, 0.6, 0.45), (1.0, 1.0, 0.5)])
def test_off_grid_closed_form(lin_mm, pt):
    v, d, s = pt
    r = mismatch_dvgs(lin_mm, "nmos", 100, 2e-6, v, d, s)
    assert isinstance(r, MismatchSens)
    assert set(r.dvgs) == set(COEF)
    for p, c in COEF.items():
        assert math.isclose(r.dvgs[p], _lin(c, v, d, s), rel_tol=1e-12, abs_tol=1e-18), p
    assert dict(r.slope_ref) == MISMATCH_SLOPE_REF
    assert r.w_m == pytest.approx(1e-6, rel=1e-15)
    with pytest.raises(TypeError):
        r.dvgs["vth0"] = 0.0                                  # 읽기 전용 매핑


def test_slope_ref_zero_for_unused_variable(tmp_path):
    """CONTRACT 10.2: 기준 bin 이 변수를 안 쓰면 slope_ref 0.0 (meta 값 None)."""
    L, v, d, s = toy_grid_mesh()
    t = MismatchToy(tmp_path / "z", {p: _lin(c, v, d, s) for p, c in COEF.items()},
                    slope_ref={"vth0": 3e-3, "toxe": 2e-3, "voff": None})
    r = mismatch_dvgs(new_memo(t.load()), "nmos", 100, 1e-6, 0.5, 0.5, 0.0)
    assert r.slope_ref["voff"] == 0.0


def test_nan_corner_with_weight_rejected_zero_weight_ok(tmp_path):
    """CONTRACT 10.2: 가중치 0 이 아닌 모서리에 NaN -> `lut_mismatch_undefined`(detail parameters); 가중치 0 인 모서리의 NaN 은 읽지 않는다."""
    L, v, d, s = toy_grid_mesh()
    dv = {p: _lin(c, v, d, s) for p, c in COEF.items()}
    dv["voff"] = np.where(v == 1.0, np.nan, dv["voff"])
    m = new_memo(MismatchToy(tmp_path / "n", dv).load())
    with pytest.raises(SealViolationError) as ei:
        mismatch_dvgs(m, "nmos", 100, 1e-6, 0.75, 0.5, 0.0)
    det = detail_of(ei.value)
    assert det["reason"] == "lut_mismatch_undefined" and "voff" in det["parameters"]
    ok = mismatch_dvgs(m, "nmos", 100, 1e-6, 0.5, 0.5, 0.0)       # VGS 격자점 0.5 -> 1.0 행 가중치 0
    assert math.isclose(ok.dvgs["voff"], _lin(COEF["voff"], 0.5, 0.5, 0.0), rel_tol=1e-12)


def test_unavailable_and_other_width(lin_mm, toy_memo):
    with pytest.raises(SealViolationError) as ei:
        mismatch_dvgs(toy_memo, "nmos", 100, 1e-6, 0.5, 0.5, 0.0)
    assert detail_of(ei.value)["reason"] == "lut_mismatch_unavailable"
    with pytest.raises(SealViolationError) as ei:
        mismatch_dvgs(lin_mm, "nmos", 200, 1e-6, 0.5, 0.5, 0.0)
    d = detail_of(ei.value)
    assert d["reason"] == "lut_column_unavailable" and d["column"] == "DVGS"


@pytest.mark.parametrize("args,axis", [((1e-6, 0.5, 0.5, 0.51), "VS"), ((1e-6, -0.01, 0.5, 0.0), "VGS"),
                                       ((0.5e-6, 0.5, 0.5, 0.0), "L")])
def test_axis_out_of_range(lin_mm, args, axis):
    with pytest.raises(SealViolationError) as ei:
        mismatch_dvgs(lin_mm, "nmos", 100, *args)
    d = detail_of(ei.value)
    assert d["reason"] == "lut_axis_out_of_range" and d["axis"] == axis and d["table"] == "mismatch"


@pytest.mark.lut_realdata
def test_real_grid_and_cell_centre_match_npz(real_nm_memo, raw_mismatch, real_nm_lut):
    """(c) 실데이터: 격자점은 npz 원소 그대로(비트 동일), VGS·VDS·VS 칸 중앙(L 앵커)은 npz 의 4축 다중선형(독립 구현)과 상대 1e-12."""
    g = tuple(np.asarray(raw_mismatch[a], dtype=float) for a in ("L", "VGS", "VDS", "VS"))
    rng = np.random.default_rng(20261008)
    for kind, suf in (("nmos", "_n"), ("pmos", "_p")):
        params = real_nm_lut.mismatch[kind].params
        n = 0
        while n < 40:
            i, a, k, s = (int(rng.integers(len(g[0]))), int(rng.integers(8, 47)), int(rng.integers(2, 47)),
                          int(rng.integers(0, 9)))
            arrs = {p: raw_mismatch["DVGS_%s%s" % (p, suf)] for p in params}
            blk = [arrs[p][i, a:a + 2, k:k + 2, s:s + 2] for p in params]
            if not all(np.isfinite(b).all() for b in blk):
                continue
            n += 1
            r = mismatch_dvgs(real_nm_memo, kind, 1000, float(g[0][i]), float(g[1][a]), float(g[2][k]), float(g[3][s]))
            for p in params:
                assert r.dvgs[p] == float(arrs[p][i, a, k, s])
            pt = (float(g[0][i]), 0.5 * (g[1][a] + g[1][a + 1]), 0.5 * (g[2][k] + g[2][k + 1]), 0.5 * (g[3][s] + g[3][s + 1]))
            r = mismatch_dvgs(real_nm_memo, kind, 1000, *pt)
            for p in params:
                assert math.isclose(r.dvgs[p], interp4(g, arrs[p], pt), rel_tol=1e-12, abs_tol=1e-20)
