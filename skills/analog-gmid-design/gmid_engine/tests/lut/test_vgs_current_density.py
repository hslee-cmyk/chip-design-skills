"""`vgs_for_current_density` -- CONTRACT 3.1 [r7], 계획 DEC-88(쓰기 소자 독립 좌표 ln IDu, VGS 는 강반전 분지 위 단조 역산),
DEC-87(역산은 같은 Hermite 칸 안 bisection), 설계 41 §4.1(칸 분류 -> 단조 칸만 역산, 위반 칸 `lut_hermite_nonmonotone_cell`).

oracle:
- (a) r5 toy 닫힌 식: L = 1e-6 장에서 ln IDu = ln ID = ln 1e-7 + 20v − 6v² + 0.1·d + ln(0.5)·s/0.5 (w_m = L = 1e-6) ->
  목표 ln IDu 의 근 v = (20 − √(400 − 24·c))/12, c = ln IDu − ln 1e-7 − 0.1·d − ln(0.5)·s/0.5 (2차식 근의 공식 -- toy 구성에서 유도).
  분지 = 정점(gm/ID 최대 = VGS 0 마디)부터 전부.
- (a) 합성 곡선(conftest `curve_lut`): 마디 ID·gm/ID 를 정해 분지·단조 구간을 손으로 정한다.
- (c) 실데이터: 격자 마디 ln IDu(npz 직접) 를 목표로 주면 그 마디 VGS 가 나와야 한다(칸 끝 근).
"""
import math

import numpy as np
import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.lut import vgs_for_current_density

from .conftest import detail_of


def _c(lnidu, d, s):
    return lnidu - math.log(1e-7) - 0.1 * d - math.log(0.5) * s / 0.5


def _root(lnidu, d, s):
    c = _c(lnidu, d, s)
    return (20.0 - math.sqrt(400.0 - 24.0 * c)) / 12.0


@pytest.mark.parametrize("v,d,s", [(0.25, 0.5, 0.0), (0.7, 0.8, 0.3), (0.1, 1.0, 0.5), (0.95, 0.6, 0.1)])
def test_closed_form_root(toy_memo, v, d, s):
    lnidu = math.log(1e-7) + 20 * v - 6 * v * v + 0.1 * d + math.log(0.5) * s / 0.5
    got = vgs_for_current_density(toy_memo, "nmos", 100, lnidu, 1e-6, d, s)
    assert abs(got - _root(lnidu, d, s)) <= 1e-12
    assert abs(got - v) <= 1e-12


def test_width_independent_coordinate(toy_memo):
    """ln IDu 는 폭 무관 좌표(IDu = ID·L/w_m): w_key 200(ID 2배, w_m 2배) 도 같은 VGS."""
    lnidu = math.log(1e-7) + 20 * 0.4 - 6 * 0.16 + 0.05
    a = vgs_for_current_density(toy_memo, "nmos", 100, lnidu, 1e-6, 0.5, 0.0)
    b = vgs_for_current_density(toy_memo, "nmos", 200, lnidu, 1e-6, 0.5, 0.0)
    assert abs(a - 0.4) <= 1e-12 and abs(b - 0.4) <= 1e-12


def test_L_scaling(toy_memo):
    """ln IDu = ln ID + ln L − ln w_m: L = 2e-6 장은 ID 가 1/2(1e-6/L)이고 L 이 2배라 IDu 는 L = 1e-6 과 같다 -> 같은 VGS."""
    lnidu = math.log(1e-7) + 20 * 0.6 - 6 * 0.36 + 0.05
    assert abs(vgs_for_current_density(toy_memo, "nmos", 100, lnidu, 2e-6, 0.5, 0.0) - 0.6) <= 1e-12


@pytest.mark.parametrize("j", [0, 1, 2])
def test_node_target_returns_node(toy_memo, j):
    v = (0.0, 0.5, 1.0)[j]
    lnidu = math.log(1e-7) + 20 * v - 6 * v * v + 0.05
    assert vgs_for_current_density(toy_memo, "nmos", 100, lnidu, 1e-6, 0.5, 0.0) == pytest.approx(v, abs=1e-12)


@pytest.mark.parametrize("delta", [1e-3, -1e-3])
def test_out_of_range(toy_memo, delta):
    """분지 ln ID 범위 [ln ID(0), ln ID(1)] 밖 -> `lut_target_out_of_range`, target·branch_max 는 같은 단위(ln ID)."""
    lo = math.log(1e-7) + 0.05
    hi = math.log(1e-7) + 14 + 0.05
    x = hi + delta if delta > 0 else lo + delta
    with pytest.raises(SealViolationError) as ei:
        vgs_for_current_density(toy_memo, "nmos", 100, x, 1e-6, 0.5, 0.0)
    d = detail_of(ei.value)
    assert d["reason"] == "lut_target_out_of_range" and d["quantity"] == "ln_idu"
    assert (d["target"] > d["branch_max"]) == (delta > 0)
    assert abs(d["branch_max"] - hi) <= 1e-12 and abs(d["branch_min"] - lo) <= 1e-12


def test_nonmonotone_cell_rejected(r4toy_memo):
    """r4 toy(CONTRACT 7.2): VGS 칸 [0, 0.5] 이 FC 위반 -> 그 칸에 떨어지는 목표는 `lut_hermite_nonmonotone_cell`(axis VGS),
    단조 칸 [0.5, 1] 의 목표는 성공(설계 41 §4.1 해법 매핑)."""
    with pytest.raises(SealViolationError) as ei:
        vgs_for_current_density(r4toy_memo, "nmos", 100, math.log(3e-7), 1e-6, 0.5, 0.0)
    d = detail_of(ei.value)
    assert d["reason"] == "lut_hermite_nonmonotone_cell" and d["axis"] == "VGS"
    assert (d["cell_lo"], d["cell_hi"]) == (0.0, 0.5)
    v = vgs_for_current_density(r4toy_memo, "nmos", 100, math.log(3e-6), 1e-6, 0.5, 0.0)
    assert 0.5 < v < 1.0


def test_non_monotonic_branch(curve_lut):
    """합성 곡선: 마디 ID (1e-6, 1e-5, 1e-7), gm/ID (20, 10, 4) -> 정점 0, 단조 구간 [0, 1](ln ID 증가), 분지 범위 [1e-7, 1e-5].
    목표 5e-7 은 분지 범위 안이지만 단조 구간 밖 -> `lut_target_non_monotonic`."""
    memo, _ = curve_lut((0.0, 0.5, 1.0), (1e-6, 1e-5, 1e-7), (20.0, 10.0, 4.0))
    with pytest.raises(SealViolationError) as ei:
        vgs_for_current_density(memo, "nmos", 100, math.log(5e-7), 1e-6, 0.5, 0.0)
    d = detail_of(ei.value)
    assert d["reason"] == "lut_target_non_monotonic"
    assert math.isclose(d["monotone_lo"], math.log(1e-6), rel_tol=1e-12)
    assert math.isclose(d["monotone_hi"], math.log(1e-5), rel_tol=1e-12)


def test_branch_starts_at_peak(curve_lut):
    """정점이 마디 1(gm/ID (2, 6, 4)) -> 분지 = 마디 1, 2. 마디 0 의 ID 는 분지 밖이라 그 목표는 범위 밖.
    칸 [0.5, 1] 은 FC 단조(b0 = 3, b2 = 2, b1 = 3·ln10 − 5 = 1.9 ≥ 0 -- CONTRACT 1.4 조건을 손으로)."""
    memo, _ = curve_lut((0.0, 0.5, 1.0), (1e-7, 1e-6, 1e-5), (2.0, 6.0, 4.0))
    with pytest.raises(SealViolationError) as ei:
        vgs_for_current_density(memo, "nmos", 100, math.log(1e-7), 1e-6, 0.5, 0.0)
    assert detail_of(ei.value)["reason"] == "lut_target_out_of_range"
    assert vgs_for_current_density(memo, "nmos", 100, math.log(1e-6), 1e-6, 0.5, 0.0) == pytest.approx(0.5, abs=1e-12)


def test_undefined_node(curve_lut):
    """gm/ID 가 정의 안 된 마디(GM = 0 -> on_mask 거짓) -> `lut_curve_undefined`."""
    memo, _ = curve_lut((0.0, 0.5, 1.0), (1e-7, 1e-6, 1e-5), (20.0, 10.0, 0.0))
    with pytest.raises(SealViolationError) as ei:
        vgs_for_current_density(memo, "nmos", 100, math.log(2e-6), 1e-6, 0.5, 0.0)
    assert detail_of(ei.value)["reason"] == "lut_curve_undefined"


def test_root_memo_region(toy_memo):
    x = math.log(1e-7) + 5
    vgs_for_current_density(toy_memo, "nmos", 100, x, 1e-6, 0.5, 0.0)
    before = dict(toy_memo.stats())["root"]
    vgs_for_current_density(toy_memo, "nmos", 100, x, 1e-6, 0.5, 0.0)
    after = dict(toy_memo.stats())["root"]
    assert after.hits == before.hits + 1 and after.misses == before.misses


@pytest.mark.lut_realdata
def test_real_node_targets_return_grid_vgs(real_memo, raw_slice):
    """(c) 실데이터 nmos·pmos w_key 1000, L 앵커·VDS·VS 격자점 곡선: 강반전 분지(마디 gm/ID 최댓값 이후)이고 ln ID 가 엄격 증가하는 구간의
    마디 ln IDu(npz ID·L/W 직접)를 목표로 주면 그 마디 VGS(격자값, 상대 1e-12 -- exp·log 왕복 반올림 허용 2 ulp 은 계약 3.1)."""
    rng = np.random.default_rng(20261008)
    for kind in ("nmos", "pmos"):
        z = raw_slice(kind, 1000)
        W = float(z["W"])
        n = 0
        while n < 30:
            i, k, s = int(rng.integers(len(z["L"]))), int(rng.integers(8, len(z["VDS"]))), int(rng.integers(len(z["VS"])))
            ID, GM = z["ID"][i, :, k, s], z["GM"][i, :, k, s]
            if not ((ID > 0) & (GM > 0)).all():
                continue
            g = GM / ID
            p = int(np.argmax(g))
            e = p
            while e + 1 < len(ID) and ID[e + 1] > ID[e]:
                e += 1
            if e - p < 3:
                continue
            j = int(rng.integers(p + 1, e))
            L = float(z["L"][i])
            lnidu = math.log(float(ID[j]) * L / W)
            got = vgs_for_current_density(real_memo, kind, 1000, lnidu, L, float(z["VDS"][k]), float(z["VS"][s]))
            assert abs(got - float(z["VGS"][j])) <= 1e-9, (kind, i, j, k, s, got)
            n += 1
