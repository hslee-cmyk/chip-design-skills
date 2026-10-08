"""`ft_curve` -- CONTRACT 4.5 [r7], 설계 40 §11 U3 '`ft_curve`', 41 §6.4-4(f_T(gm/ID, L) 로 속도 상한).

oracle:
- (a) r5 toy 닫힌 식: 분지 = 정점(gm/ID 최대, VGS 0)부터 모든 마디. 마디 gm/ID = 20 − 12v, ID(w_m) = 1e-7·exp(20v − 6v² + 0.1d)·0.5^(s/0.5)
  (L = 1e-6), Cgg(W = w_m) = 1e-15 (기준 LUT 상수, w_ref = w_m = 1e-6) -> f_T = gm/(2π·Cgg) = (gm/ID)·ID/(2π·1e-15).
- (a) 폭 무관: w_key 200 은 ID·Cgg 가 모두 2배 -> 같은 f_T.
- (c) 실데이터: 마디 값 = 슬라이스 GM(직접)/(2π·기준 LUT CGG(직접)) -- w_key 1000(기준 폭)에서 격자점 곡선.
"""
import math

import numpy as np
import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.lut import CURVE_QUANTITIES, GmIdAxisCurve, ft_curve

from .conftest import detail_of


def _toy_ft(v, d=0.5, s=0.0):
    idv = 1e-7 * math.exp(20 * v - 6 * v * v + 0.1 * d) * 0.5 ** (s / 0.5)
    return (20 - 12 * v) * idv / (2 * math.pi * 1e-15)


def test_curve_quantities_vocabulary():
    assert "ft_hz" in CURVE_QUANTITIES


@pytest.mark.parametrize("w_key", [100, 200])
def test_toy_closed_form(toy_memo, w_key):
    c = ft_curve(toy_memo, "nmos", w_key, 1e-6, 0.5, 0.0)
    assert isinstance(c, GmIdAxisCurve)
    assert c.quantity == "ft_hz" and c.kind == "nmos" and c.w_key == w_key
    assert tuple(c.vgs) == (0.0, 0.5, 1.0)
    assert np.allclose(c.gm_id, [20.0, 14.0, 8.0], rtol=1e-12, atol=0)
    assert np.allclose(c.values, [_toy_ft(v) for v in (0.0, 0.5, 1.0)], rtol=1e-12, atol=0)
    assert tuple(bool(x) for x in c.cell_ok) == (True, True)
    assert c.monotone is True
    with pytest.raises(ValueError):
        np.asarray(c.values)[0] = 0.0                        # 읽기 전용 배열


def test_off_grid_vds_vs(toy_memo):
    """VDS·VS 가 격자 밖이어도 마디 값은 4.2 마디 값(VDS Hermite·VS 선형이 이 toy 에선 정확) -> 닫힌 식."""
    c = ft_curve(toy_memo, "nmos", 100, 1e-6, 0.8, 0.3)
    assert np.allclose(c.values, [_toy_ft(v, 0.8, 0.3) for v in (0.0, 0.5, 1.0)], rtol=1e-12, atol=0)


def test_nonpositive_cgg_node_undefined(toy_build):
    """Cgg ≤ 0 마디 -> `lut_curve_undefined`(계약 4.5)."""
    from .conftest import toy_cap_arrays
    cap = toy_cap_arrays()
    cap["CGG_n"][:, 2] = 0.0
    lut = toy_build("cgg0", cap=cap).load()
    from .conftest import new_memo
    with pytest.raises(SealViolationError) as ei:
        ft_curve(new_memo(lut), "nmos", 100, 1e-6, 0.5, 0.0)
    assert detail_of(ei.value)["reason"] == "lut_curve_undefined"


def test_curve_memo_region(toy_memo):
    a = ft_curve(toy_memo, "nmos", 100, 1e-6, 0.5, 0.0)
    before = dict(toy_memo.stats())["curve"]
    b = ft_curve(toy_memo, "nmos", 100, 1e-6, 0.5, 0.0)
    after = dict(toy_memo.stats())["curve"]
    # 두 번째 호출은 다시 계산하지 않는다(같은 객체, misses 불변). 곡선 표 조회 전에 gm_id_curve(같은 curve 영역)를 거칠 수 있어
    # hits 증가 수는 고정하지 않는다.
    assert b is a and after.misses == before.misses and after.hits > before.hits


@pytest.mark.lut_realdata
def test_real_nodes_equal_gm_over_two_pi_cgg(real_memo, raw_slice, raw_cap):
    rng = np.random.default_rng(20261008)
    for kind, suf in (("nmos", "_n"), ("pmos", "_p")):
        z = raw_slice(kind, 1000)
        for _ in range(10):
            i, k, s = int(rng.integers(len(z["L"]))), int(rng.integers(4, len(z["VDS"]))), int(rng.integers(len(z["VS"])))
            c = ft_curve(real_memo, kind, 1000, float(z["L"][i]), float(z["VDS"][k]), float(z["VS"][s]))
            j = np.searchsorted(z["VGS"], np.asarray(c.vgs))
            assert np.array_equal(z["VGS"][j], np.asarray(c.vgs))
            exp = z["GM"][i, j, k, s] / (2 * math.pi * raw_cap["CGG" + suf][i, j, k, s])
            # 슬라이스 W 는 5 µm 의 부동소수(4.9999999999999996e-06)이고 Cgg 는 기준 LUT(w_ref 5e-06) -- 폭 비 1 ± 1 ulp
            assert np.allclose(np.asarray(c.values), exp, rtol=1e-12, atol=0)
            g = z["GM"][i, :, k, s] / z["ID"][i, :, k, s]
            assert int(j[0]) == int(np.argmax(g))                       # 분지 = 정점부터
            assert len(j) == len(z["VGS"]) - int(np.argmax(g))
