"""`vgs_for_gm_id` -- CONTRACT 3절·4.1 표 [r5]: 곡선 마디 gm/ID 에서 분지(정점 이상) 가장 오른쪽 칸을 고르고, 칸 안 근 =
그 칸 VGS Hermite 의 미분이 목표인 VGS. 실패: NaN 마디 -> lut_curve_undefined, 해 없음 -> lut_no_strong_inversion_root,
고른 칸 단조 위반 -> lut_hermite_nonmonotone_cell. 결과 VGS 의 op_point gm/ID 는 목표와 부동소수 분해능 안에서 같다.

누설 분지 결함 회귀: 옛 엔진(로그 바닥 1e-18·1e-30 + 전 구간 가장 오른쪽 구간)이 정점 왼쪽 누설 분지 해를 내던 실제 사례를
npz 에서 골라 고정한다(tol_v_measurement.md 의 분지 점프 사례와 같은 곡선: pmos L 1 µm, VDS 0.525 V, VS 0.4 V).
"""
import math

import numpy as np
import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.lut import op_point, vgs_for_gm_id

from .conftest import (R5_A, R5_B, RefSlice, anchor_w, branch_solve_vgs, detail_of, l_weights, legacy_solve_vgs,
                       log_floor, rel_close, sir_ref_b)


def _toy_ref(arrays, iL, vds, vsb, t):
    """(상태, 근, 근 차 상한, 왕복 상한) -- 독립 곡선 마디 + conftest γ_n 유도 상한."""
    rs = RefSlice(arrays)
    V, S, ok = rs.curve(anchor_w(iL), vds, vsb)
    dV, dS = rs.curve_err(anchor_w(iL), vds, vsb)
    return sir_ref_b(rs.grids[1], V, S, t, ok, with_residual=True, dV=dV, dS=dS)


def _assert_root(memo, arrays, L, iL, vds, vsb, t, closed=None):
    v = vgs_for_gm_id(memo, "nmos", 100, t, L, vds, vsb)
    st, exp, rb, resb = _toy_ref(arrays, iL, vds, vsb, t)
    assert st == "ok" and abs(v - exp) <= rb, (t, v, exp, rb)
    if closed is not None:
        # 닫힌 값과의 차 ≤ 엔진 경로 오차(≤ 두 경로 상한 rb) -- 독립 구현도 같은 상한 안이어야 한다
        assert abs(v - closed) <= rb and abs(exp - closed) <= rb, (t, v, closed, rb)
    back = op_point(memo, "nmos", 100, L, v, vds, vsb).gm_over_id
    assert abs(back - t) <= resb, (t, back, resb)
    return v


def test_contract_toy_rows(toy_memo):
    from .conftest import toy_slice_arrays
    a = toy_slice_arrays(1e-6)
    _assert_root(toy_memo, a, 1e-6, 0, 0.5, 0.0, 15.0, closed=5.0 / 12.0)
    _assert_root(toy_memo, a, 2e-6, 1, 0.8, 0.3, 11.0, closed=0.75)
    with pytest.raises(SealViolationError) as ei:
        vgs_for_gm_id(toy_memo, "nmos", 100, 25.0, 1e-6, 0.5, 0.0)
    det = detail_of(ei.value)
    assert det["reason"] == "lut_no_strong_inversion_root"
    assert det["peak_vgs"] == 0.0
    assert det["gm_id"] == 25.0 and det["L"] == 1e-6 and det["vds"] == 0.5 and det["vsb"] == 0.0
    assert det["kind"] == "nmos" and det["w_key"] == 100
    assert rel_close(det["branch_gm_id_max"], 20.0, 1e-12) and rel_close(det["branch_gm_id_min"], 8.0, 1e-12)


def test_toy_round_trip_and_below_branch(toy_memo):
    from .conftest import toy_slice_arrays
    a = toy_slice_arrays(1e-6)
    for t in (19.0, 12.5, 14.0, 10.0, 8.5):
        _assert_root(toy_memo, a, 2e-6, 1, 0.7, 0.3, t, closed=(R5_A - t) / (2 * R5_B))   # 닫힌 식 gm/ID = 20 − 12v
    with pytest.raises(SealViolationError):
        vgs_for_gm_id(toy_memo, "nmos", 100, 7.9, 1e-6, 0.5, 0.0)


def test_r4_toy_rows(r4toy_memo):
    """r4 toy([r7] 1.4 단위 검사와 맞는 판, 마디 gm/ID (20, 4, 1.5)): 목표 15·7 -> 고른 칸 [0, 0.5] 위반 -> lut_hermite_nonmonotone_cell,
    목표 3 -> 단조 칸 [0.5, 1] 의 Hermite 미분 근(아래 손계산)."""
    with pytest.raises(SealViolationError) as ei:
        vgs_for_gm_id(r4toy_memo, "nmos", 100, 15.0, 1e-6, 0.5, 0.0)
    det = detail_of(ei.value)
    assert det["reason"] == "lut_hermite_nonmonotone_cell"
    assert det["axis"] == "VGS" and det["cell_lo"] == 0.0 and det["cell_hi"] == 0.5
    assert (det["gm_id"], det["L"], det["vds"], det["vsb"], det["kind"], det["w_key"]) == (15.0, 1e-6, 0.5, 0.0, "nmos", 100)
    with pytest.raises(SealViolationError) as ei:
        vgs_for_gm_id(r4toy_memo, "nmos", 100, 7.0, 1e-6, 0.5, 0.0)          # 7 ∈ (4, 20) -> 같은 위반 칸
    assert detail_of(ei.value)["reason"] == "lut_hermite_nonmonotone_cell"
    from .conftest import r4_toy_slice_arrays
    v = vgs_for_gm_id(r4toy_memo, "nmos", 100, 3.0, 1e-6, 0.5, 0.0)
    # 손계산(oracle (a)): 칸 [0.5, 1] 의 ln ID 차 δ = 1.5, h 0.5, m0 4, m1 1.5 -> p'(t) = 6δt(1−t)/h + m0(1−4t+3t²) + m1(3t²−2t) = 3
    #   -> a t² + b t + c = 0, a = −18 + 12 + 4.5 = −1.5, b = 18 − 16 − 3 = −1, c = 4 − 3 = 1 -> 1.5t² + t − 1 = 0 의 [0, 1] 근 t = (√7 − 1)/3
    d, h, m0, m1 = 1.5, 0.5, 4.0, 1.5
    a = -6 * d / h + 3 * m0 + 3 * m1
    b = 6 * d / h - 4 * m0 - 2 * m1
    c = m0 - 3.0
    assert (a, b, c) == (-1.5, -1.0, 1.0)
    t = (math.sqrt(7.0) - 1.0) / 3.0
    assert abs(a * t * t + b * t + c) <= 4 * math.ulp(1.0) and 0 < t < 1
    v2 = _assert_root(r4toy_memo, r4_toy_slice_arrays(1e-6), 1e-6, 0, 0.5, 0.0, 3.0, closed=0.5 + 0.5 * t)
    assert v2 == v


def test_curve_undefined(curve_lut):
    """[r5] 곡선에 gm/ID 정의 안 된 마디 -> lut_curve_undefined(detail n_undefined)."""
    memo, _ = curve_lut((0.0, 0.25, 0.5, 1.0), (1e-7, 0.0, 0.0, 1e-5), (20.0, 15.0, 10.0, 4.0))
    with pytest.raises(SealViolationError) as ei:
        vgs_for_gm_id(memo, "nmos", 100, 6.0, 1e-6, 0.5, 0.0)
    det = detail_of(ei.value)
    assert det["reason"] == "lut_curve_undefined" and det["n_undefined"] == 2
    assert (det["gm_id"], det["L"], det["vds"], det["vsb"], det["kind"], det["w_key"]) == (6.0, 1e-6, 0.5, 0.0, "nmos", 100)


def test_missing_width_keyerror(toy_memo):
    with pytest.raises(KeyError):
        vgs_for_gm_id(toy_memo, "nmos", 300, 15.0, 1e-6, 0.5, 0.0)


# ---------------------------------------------------------------------------
# 실데이터
# ---------------------------------------------------------------------------

LEAK = dict(kind="pmos", w_key=1000, L=1e-6, vds=0.525, vsb=0.4, target=2.0)


def _grid_index(axis, x):
    i = int(np.argmin(np.abs(axis - x)))
    assert math.isclose(axis[i], x, rel_tol=1e-9)
    return i


def _curves(z, iL, k, s):
    I, G = z["ID"][iL, :, k, s], z["GM"][iL, :, k, s]
    g_old = np.exp(np.log(np.clip(G, 1e-30, None)) - np.log(np.clip(I, 1e-18, None)))      # 옛 바닥
    lI, _ = log_floor(z["ID"])
    lG, _ = log_floor(z["GM"])
    g_new = np.exp(lG[iL, :, k, s] - lI[iL, :, k, s])                                     # 계약 1.4 바닥
    return g_old, g_new


@pytest.mark.lut_realdata
def test_leak_branch_regression_real(real_memo, raw_slice, raw_cap):
    z = raw_slice(LEAK["kind"], LEAK["w_key"])
    iL, k, s = _grid_index(z["L"], LEAK["L"]), _grid_index(z["VDS"], LEAK["vds"]), _grid_index(z["VS"], LEAK["vsb"])
    L, vds, vsb = float(z["L"][iL]), float(z["VDS"][k]), float(z["VS"][s])
    VGS = z["VGS"]
    g_old, g_new = _curves(z, iL, k, s)
    t = LEAK["target"]
    old = legacy_solve_vgs(g_old, VGS, t)
    p_new = int(np.argmax(g_new))
    assert old < 0.2 and old < VGS[int(np.argmax(g_old))], old
    Ir, Gr = raw_cap["ID_p"][iL, :, k, 2], raw_cap["GM_p"][iL, :, k, 2]
    g_ref_old = np.exp(np.log(np.clip(Gr, 1e-30, None)) - np.log(np.clip(Ir, 1e-18, None)))
    assert legacy_solve_vgs(g_ref_old, VGS, t) < 0.2
    assert branch_solve_vgs(g_new, VGS, t) is None
    assert t < g_new[p_new:].min()
    with pytest.raises(SealViolationError) as ei:
        vgs_for_gm_id(real_memo, LEAK["kind"], LEAK["w_key"], t, L, vds, vsb)
    det = detail_of(ei.value)
    assert det["reason"] == "lut_no_strong_inversion_root"
    assert det["peak_vgs"] == float(VGS[p_new])
    assert rel_close(det["branch_gm_id_min"], float(g_new[p_new:].min()), 1e-12)
    assert rel_close(det["branch_gm_id_max"], float(g_new[p_new:].max()), 1e-12)
    assert (det["kind"], det["w_key"], det["gm_id"]) == ("pmos", 1000, t)


@pytest.mark.lut_realdata
def test_legacy_cell_choice_equal_when_legacy_root_in_branch_real(real_memo, raw_slice):
    """6절 [r5]: 옛 결과가 분지 안이면 칸 index 가 같고, 칸 안 근은 Hermite 미분 근(독립)이며 op_point gm/ID = 목표."""
    z = raw_slice(LEAK["kind"], LEAK["w_key"])
    iL, k, s = _grid_index(z["L"], LEAK["L"]), _grid_index(z["VDS"], LEAK["vds"]), _grid_index(z["VS"], LEAK["vsb"])
    VGS = z["VGS"]
    rs = RefSlice(z)
    L, vds, vsb = float(z["L"][iL]), float(z["VDS"][k]), float(z["VS"][s])
    V, S, ok = rs.curve(anchor_w(iL), vds, vsb)
    g_old, g_new = _curves(z, iL, k, s)
    p = int(np.argmax(g_new))
    assert np.array_equal(g_old[p + 4:], g_new[p + 4:])
    n = 0
    for t in np.linspace(2.5, 30.0, 23):
        t = float(t)
        old = legacy_solve_vgs(g_old, VGS, t)
        if old > VGS[p + 4]:
            d = g_old - t
            i_old = int(np.flatnonzero(d[:-1] * d[1:] <= 0.0)[-1])
            got = vgs_for_gm_id(real_memo, "pmos", 1000, t, L, vds, vsb)
            assert VGS[i_old] <= got <= VGS[i_old + 1], t
            st, exp, rb, resb = sir_ref_b(VGS, V, S, t, ok, with_residual=True)
            assert st == "ok" and abs(got - exp) <= rb, (t, got, exp, rb)
            assert abs(op_point(real_memo, "pmos", 1000, L, got, vds, vsb).gm_over_id - t) <= resb
            n += 1
    assert n >= 15


@pytest.mark.lut_realdata
def test_round_trip_against_independent_hermite(real_lut, real_memo, raw_slice):
    """vgs_for_gm_id 결과 = 독립 Hermite 경로(곡선 마디 4.2 + 3절 칸 선택 + 칸 안 미분 근), 그 VGS 의 op_point gm/ID = 목표.
    L 은 앵커와 같은 bin 안 보간, VDS·VS 는 격자점과 칸 안 모두."""
    rng = np.random.default_rng(5)
    for kind, wk in (("nmos", 72), ("nmos", 1000), ("pmos", 1000), ("pmos", 1400)):
        z = raw_slice(kind, wk)
        rs = RefSlice(z)
        ab = tuple(real_lut.slice_map[(kind, wk)].l_bins.anchor_bin)
        VGS = rs.grids[1]
        Lg = rs.grids[0]
        done = 0
        while done < 10:
            iL, k, s = int(rng.integers(0, 11)), int(rng.integers(4, 48)), int(rng.integers(0, 9))
            off_grid = done % 2 == 1
            L = Lg[iL]
            vds, vsb = rs.grids[2][k], rs.grids[3][s]
            if off_grid:
                vds = float(z["VDS"][k] + 0.37 * (z["VDS"][k + 1] - z["VDS"][k]))
                vsb = float(z["VS"][s] + 0.61 * (z["VS"][s + 1] - z["VS"][s]))
                if done % 4 == 3:
                    L = float(Lg[iL] + 0.5 * (Lg[iL + 1] - Lg[iL]))
            pos = l_weights(Lg, ab, L)
            if pos is None:
                continue
            V, S, ok = rs.curve(pos[0], vds, vsb)
            if not np.all(np.isfinite(S)):
                continue
            p = int(np.argmax(S))
            lo, hi = float(S[p:].min()), float(S[p])
            if hi - lo < 1.0:
                continue
            t = float(rng.uniform(lo + 0.05 * (hi - lo), hi - 0.05 * (hi - lo)))
            dV, dS = rs.curve_err(pos[0], vds, vsb)
            st, exp_v, rb, resb = sir_ref_b(VGS, V, S, t, ok, with_residual=True, dV=dV, dS=dS)
            if st != "ok":
                with pytest.raises(SealViolationError):
                    vgs_for_gm_id(real_memo, kind, wk, t, L, vds, vsb)
                continue
            v = vgs_for_gm_id(real_memo, kind, wk, t, L, vds, vsb)
            assert v >= VGS[p]
            assert abs(v - exp_v) <= rb, (kind, wk, L, vds, vsb, t, v, exp_v, rb)
            assert abs(op_point(real_memo, kind, wk, L, v, vds, vsb).gm_over_id - t) <= resb
            done += 1
