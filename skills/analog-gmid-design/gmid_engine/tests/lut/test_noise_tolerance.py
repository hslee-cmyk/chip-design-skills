"""`tol_noise_table` -- CONTRACT 9.4 [r7], 설계 41 §7.2 'tol: 칸별 tol_noise 를 LOO 로(DEC-87 방법)'.

oracle (a) 구성: ln S(f_lo) = ln 1e-12 + c·v² (+ 1e-7 이하 섭동), ln B = 1차식 ->
- flicker: VGS 간격 h = 0.5 의 선형 LOO 오차 = c·h² (2차식의 2계 차분), ÷ 2² -> c·h²/4. toy 는 VDS·VS 2점(내부점 없음)·빈 bin 지도(L LOO 없음)라
  모든 셀이 이 값이다.
- thermal: ln B 1차식 -> LOO 0(부동소수 수준).
"""
import math

import numpy as np
import pytest

from gmid_engine.lut import TOL_NOISE_METRICS, TolNoiseTable, tol_noise_table

from .conftest import NoiseToy, TOY_L, TOY_VDS, new_memo, toy_grid_mesh

C_QUAD = 1.0
H_VGS = 0.5


@pytest.fixture
def quad_memo(tmp_path):
    L, v, d, s = toy_grid_mesh()
    A = 1e-12 * np.exp(C_QUAD * v * v)
    B = 1e-19 * np.exp(0.5 * v + 0.3 * d)              # B/A ≤ 1.7e-7 -> ln S(f_lo) 섭동 ≤ 1.7e-7
    return new_memo(NoiseToy(tmp_path / "q", A, B, cgd=0.0).load())


def test_metrics_vocabulary():
    assert TOL_NOISE_METRICS == ("flicker", "thermal")


def test_flicker_is_quarter_second_difference(quad_memo):
    T = tol_noise_table(quad_memo, "nmos")
    assert isinstance(T, TolNoiseTable)
    exp = C_QUAD * H_VGS ** 2 / 4.0
    for L in TOY_L:
        for vds in (0.5, 0.75, 1.0):
            assert abs(T.at(L, vds, "flicker") - exp) <= 1e-6, (L, vds)


def test_thermal_zero_for_loglinear_floor(quad_memo):
    T = tol_noise_table(quad_memo, "nmos")
    for L in TOY_L:
        for vds in TOY_VDS:
            assert abs(T.at(L, vds, "thermal")) <= 1e-12


def test_unknown_metric_rejected(quad_memo):
    T = tol_noise_table(quad_memo, "nmos")
    with pytest.raises(ValueError):
        T.at(1e-6, 0.5, "gm_id_inverse")


def test_thermal_undefined_when_B_unknown(tmp_path):
    """B 가 모든 점에서 미상(B0 = 0 -> nonpositive)이면 thermal 은 정의되지 않는다(None)."""
    L, v, d, s = toy_grid_mesh()
    m = new_memo(NoiseToy(tmp_path / "z", 1e-12 * np.exp(v * v), np.zeros(v.shape), cgd=0.0).load())
    T = tol_noise_table(m, "nmos")
    assert T.at(1e-6, 0.5, "thermal") is None
    assert abs(T.at(1e-6, 0.5, "flicker") - 0.0625) <= 1e-9


def test_derived_memo_hit(quad_memo):
    t1 = tol_noise_table(quad_memo, "nmos")
    before = dict(quad_memo.stats())["derived"]
    t2 = tol_noise_table(quad_memo, "nmos")
    after = dict(quad_memo.stats())["derived"]
    # 두 번째 호출은 다시 계산하지 않는다(misses 불변, 같은 객체). 입력 면(noise_planes) 조회도 derived 적중으로 세어질 수 있어
    # hits 증가 수는 고정하지 않는다(계약 9.4 는 '디스크 캐시 대상' 만 말한다).
    assert t2 is t1 and after.misses == before.misses and after.hits > before.hits


@pytest.mark.lut_realdata
def test_real_flicker_cell_upper_bounds_pointwise_loo(real_nm_memo, raw_cap):
    """(c) 실데이터 nmos: 셀 값(flicker) ≥ 그 셀 VGS 방향 점별 선형 LOO/4(numpy 직접, on 점, VS 격자 전부) -- 셀 값은 셀 안 최댓값이다
    (CONTRACT 9.4). L 앵커 0.5 µm·1 µm, VDS 0.9 V."""
    T = tol_noise_table(real_nm_memo, "nmos")
    VGS = raw_cap["VGS"]
    VDS = list(raw_cap["VDS"])
    k = int(np.argmin(np.abs(np.asarray(VDS) - 0.9)))
    on = (raw_cap["ID_n"] > 0) & (raw_cap["GM_n"] > 0)
    lnS = np.log(raw_cap["SVG2_1HZ_n"])
    for L in (0.5e-6, 1e-6):
        i = int(np.argmin(np.abs(raw_cap["L"] - L)))
        c = lnS[i, :, k, :]
        o = on[i, :, k, :]
        t = ((VGS[1:-1] - VGS[:-2]) / (VGS[2:] - VGS[:-2]))[:, None]
        err = np.abs(c[:-2] + t * (c[2:] - c[:-2]) - c[1:-1]) / 4.0
        cond = o[:-2] & o[1:-1] & o[2:]
        pmax = float(err[cond].max())
        cell = T.at(float(raw_cap["L"][i]), float(VDS[k]), "flicker")
        assert cell is not None and cell >= pmax * (1 - 1e-12), (L, cell, pmax)
