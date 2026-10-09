"""search/iv_curves.py -- `CurveBook(memo, w_keys)`: U3 곡선 API(ft·intrinsic_gain·vdsat·idu)를 gm/ID 축으로 읽는 층 (설계 41 §6, lut CONTRACT 4.5).

oracle (a) toy LUT 구성 식(u13_hand 머리) -- 마디(VGS 격자점)에서 정확:
  gm/ID = 20 − 8·VGS, VDSAT = 2/(gm/ID), 진성 이득 = (gm/ID)/LAM, IDu = I0·exp(f(VGS) + LAM·VDS − A·VS²),
  f_T = (gm/ID)·IDu·W_ref/(2π·CGG_ref·L)  (lut 4.5: gm/(2π·Cgg), Cgg 는 폭에 비례하므로 폭 무관).
- 기준 VDS(CurveBook docstring·CONTRACT): 포화 경계 = VDS 격자 중 VDSAT 최솟값(0.1 V) + tol 이상인 첫 점 -> toy 격자(0, 0.3, ...)에서 0.3 V.
"""
import math

import pytest

from gmid_engine.search.iv_curves import QUANTITY_FT, QUANTITY_GAIN, QUANTITY_IDU, QUANTITY_VDSAT, QUANTITY_VGS, CurveBook

from .u13_hand import A, B, C, CGG_REF, I0, LAM, W_M, memo_of, toy_env

W_KEYS = {"nmos": 100, "pmos": 100}          # 폭 1e-6 m / 제조 격자 1e-8 m


def _f(v):
    return B * v - 0.5 * C * v * v


@pytest.fixture(scope="module")
def book():
    return CurveBook(memo_of(toy_env(1.0).lut), W_KEYS)


@pytest.mark.parametrize("kind", ["nmos", "pmos"])
@pytest.mark.parametrize("vgs", [0.3, 1.0, 1.5])
def test_values_at_nodes_match_construction(book, kind, vgs):
    L, vds, vsb = 1e-6, 0.9, 0.45
    bundle = book.bundle(kind, L, vds, vsb)
    g = B - C * vgs
    assert book.value(bundle, QUANTITY_VDSAT, g) == pytest.approx(2.0 / g, rel=1e-9)
    assert book.value(bundle, QUANTITY_GAIN, g) == pytest.approx(g / LAM, rel=1e-9)
    idu = I0[kind] * math.exp(_f(vgs) + LAM * vds - A * vsb * vsb)
    assert book.value(bundle, QUANTITY_IDU, g) == pytest.approx(idu, rel=1e-9)
    ft = g * idu * W_M / (2 * math.pi * CGG_REF * L)
    assert book.value(bundle, QUANTITY_FT, g) == pytest.approx(ft, rel=1e-9)
    assert book.value(bundle, QUANTITY_VGS, g) == pytest.approx(vgs, abs=1e-12)


@pytest.mark.parametrize("kind", ["nmos", "pmos"])
def test_reference_vds_is_first_saturated_grid_point(book, kind):
    assert book.ref_vds(kind, 1e-6) == pytest.approx(0.3, abs=1e-12)


def test_ft_decreases_with_gm_id(book):
    # (a) 물리 단조: 같은 (L, VDS, VS) 에서 약반전(gm/ID 큼)일수록 f_T 가 낮다
    bundle = book.bundle("nmos", 1e-6, 0.9, 0.0)
    gs = [B - C * v for v in (1.7, 1.2, 0.7, 0.2)]
    fts = [book.value(bundle, QUANTITY_FT, g) for g in gs]
    assert all(a > b for a, b in zip(fts, fts[1:]))
