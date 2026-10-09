"""metrics/area_lower_bound.py -- `area_lower_bound(lut, mos_kind, basis_rows, fixed, caps, budget_m2, b_a_m2) -> AreaBound`
(metrics CONTRACT 10.5, 설계 41 4.4, 결정 11, D-GB4d).

oracle (a): A_lb = Σ_k I_k,cert · L_min,k² / IDu_max,k + Σ_c C_c,min · (면적/용량)_c 를 해석식 toy LUT 에서 손으로 계산한다.
- IDu = ID·L/w_m = 밀도·I0·exp(f(VGS) + LAM·VDS − A·VS²) 의 격자 최댓값(모든 폭 슬라이스) -- 이 test 가 격자 배열 식으로 직접 구한다.
  toy: nmos 슬라이스 두 개(폭 1 µm 밀도 1, 폭 2 µm 밀도 3) -> IDu_max = 3·I0·exp(max f + LAM·1.8) (밀도가 큰 슬라이스가 정한다).
- L_min = LUT L 격자 최솟값 1 µm.
- I_cert = 값 선언 이상 전류원만 읽는 전류식의 |Σ 계수·값|; θ 원소를 읽으면 0 이고 not_certified 에 (소자, current_depends_on_theta).
- 판정: A_lb > B + b_A -> infeasible(area_budget_below_lower_bound), 아니면 not_excluded, 예산 없으면 no_target.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from gmid_engine.metrics import AreaBound, area_lower_bound

from .gb4_hand import A, GRIDS, I0, L_GRID, LAM, VDS_GRID, VGS_GRID, VS_GRID, f_default, write_lut


@pytest.fixture(scope="module")
def lut(tmp_path_factory):
    return write_lut(tmp_path_factory.mktemp("area_toy"),
                     slices=(("nmos", 1e-6, 1.0), ("nmos", 2e-6, 3.0), ("pmos", 1e-6, 1.0)))


def _idu_max(kind, density):
    g = np.asarray(VGS_GRID)[:, None, None]
    d = np.asarray(VDS_GRID)[None, :, None]
    s = np.asarray(VS_GRID)[None, None, :]
    return density * I0[kind] * float(np.exp(f_default(g) + LAM * d - A * s * s).max())


L_MIN = min(L_GRID)
K_N = L_MIN ** 2 / _idu_max("nmos", 3.0)          # m²/A
K_P = L_MIN ** 2 / _idu_max("pmos", 1.0)


def test_certified_current_and_capacitor_terms(lut):
    r = area_lower_bound(lut, {"M1": "nmos"}, {"M1": (("I1", 1.0),)}, {"I1": 1e-4}, (("C1", 1e-12, 250.0),), None, 5e-15)
    assert isinstance(r, AreaBound)
    terms = dict(r.terms)
    assert terms["M1"] == pytest.approx(1e-4 * K_N, rel=1e-9)
    assert terms["C1"] == pytest.approx(1e-12 * 250.0, rel=1e-12)
    assert r.a_lb_m2 == pytest.approx(1e-4 * K_N + 2.5e-10, rel=1e-9)
    assert r.verdict == "no_target" and r.budget_m2 is None
    assert r.b_a_m2 == 5e-15
    assert tuple(r.not_certified) == ()


def test_coefficients_are_summed_with_sign_then_absolute(lut):
    # |2·I1 − 0.5·I2| = |2e-4 − 1.5e-4| = 5e-5 (pmos)
    r = area_lower_bound(lut, {"MP": "pmos"}, {"MP": (("I1", 2.0), ("I2", -0.5))}, {"I1": 1e-4, "I2": 3e-4}, (), None, 0.0)
    assert dict(r.terms)["MP"] == pytest.approx(5e-5 * K_P, rel=1e-9)


def test_theta_dependent_current_is_not_certified(lut):
    r = area_lower_bound(lut, {"M1": "nmos", "M2": "nmos"},
                         {"M1": (("I1", 1.0), ("Ith", 1.0)), "M2": (("I1", 1.0),)}, {"I1": 1e-4}, (), None, 0.0)
    assert r.a_lb_m2 == pytest.approx(1e-4 * K_N, rel=1e-9)          # M1 은 0(보수), M2 만
    assert ("M1", "current_depends_on_theta") in tuple(r.not_certified)
    assert dict(r.terms).get("M1", 0.0) == 0.0


def test_budget_verdicts(lut):
    caps = (("C1", 1e-12, 250.0),)
    lb = 2.5e-10
    over = area_lower_bound(lut, {}, {}, {}, caps, lb * (1 - 1e-9), 0.0)
    assert over.verdict == "infeasible"
    under = area_lower_bound(lut, {}, {}, {}, caps, lb * (1 + 1e-9), 0.0)
    assert under.verdict == "not_excluded"
    # b_A 가 차이를 덮으면 정지하지 않는다(A_lb > B + b_A 일 때만)
    rescued = area_lower_bound(lut, {}, {}, {}, caps, lb * (1 - 1e-9), 1e-15)
    assert rescued.verdict == "not_excluded"
    assert over.budget_m2 == lb * (1 - 1e-9)


def test_empty_inputs_give_zero_lower_bound(lut):
    r = area_lower_bound(lut, {"M1": "nmos"}, {"M1": ()}, {}, (), 1e-12, 0.0)
    assert r.a_lb_m2 == 0.0
    assert r.verdict == "not_excluded"


def test_deterministic(lut):
    args = (lut, {"M1": "nmos"}, {"M1": (("I1", 1.0),)}, {"I1": 1e-4}, (("C1", 1e-12, 250.0),), 1e-9, 5e-15)
    assert area_lower_bound(*args) == area_lower_bound(*args)
