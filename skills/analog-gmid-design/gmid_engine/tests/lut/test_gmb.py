"""`gmb` -- CONTRACT 4.1 표 [r5]: VS 칸 k = min(bisect_right(VS, vsb) − 1, len(VS) − 2),
gmb = −ID(점) · (ln IDu(VS[k+1]) − ln IDu(VS[k])) / (VS[k+1] − VS[k]), 세 값 모두 같은 (L, vgs, vds) 의 op_point(4.2 보간),
ID(점) = IDu·w_m/L. 폭 w_m 기준.
[r6] 4.4: GMBS 열이 있으면(열 출처 4.3, required=False) gmb = ID(점) × r, r = 파생 열 GMBS_PER_ID 의 L 장 + 모든 축 선형 보간
(r 이 NaN 이면 GMBS 의 같은 선형 보간). 열이 없으면 위 r5 할선. memo: 열 경로의 compute 는 op_point 1회(2절).
"""
import bisect
import math

import numpy as np
import pytest

from gmid_engine.lut import gmb, op_point

from .conftest import (BIN_L, TOY_L, RefSlice, anchor_w, gamma_n, gmb_column_ref, l_weights, log_floor, mid_gmbs_per_id,
                       mid_toy_arrays, new_memo, r5_toy_lnid, r6_toy_cap_arrays, rel_close, toy_slice_arrays)


def _col_rel_bound(lnid):
    """열 경로 대 독립 경로의 상대 차 상한(conftest γ_n 유도와 같은 규칙): ID(점) = exp(lnID) 의 상대 반올림 |lnID|·u 를
    두 경로분, 보간 합·곱·나눗셈의 γ_n 두 경로분 -> 2·γ_n·(|lnID| + 1)."""
    return 2 * gamma_n() * (abs(lnid) + 1.0)


def test_contract_toy_row(toy_memo):
    v = gmb(toy_memo, "nmos", 100, 1e-6, 0.5, 0.5, 0.25)
    ID = 1e-7 * math.exp(8.55) * math.sqrt(0.5)
    hand = -ID * math.log(0.5) / 0.5
    assert rel_close(v, 5.064753e-4, 1e-6)
    assert rel_close(v, hand, 1e-12)


def test_toy_width_scaling_and_upper_vs_edge(toy_memo):
    # 폭 200 슬라이스는 ID 2 배 -> gmb 2 배(폭 w_m 기준 값)
    assert rel_close(gmb(toy_memo, "nmos", 200, 1e-6, 0.5, 0.5, 0.25),
                     2 * gmb(toy_memo, "nmos", 100, 1e-6, 0.5, 0.5, 0.25), 1e-12)
    # vsb = VS 끝값 0.5: k = len(VS) − 2 = 0, ID(점) = 0.5·1e-7·e^8.55
    v = gmb(toy_memo, "nmos", 100, 1e-6, 0.5, 0.5, 0.5)
    assert rel_close(v, -0.5 * 1e-7 * math.exp(8.55) * math.log(0.5) / 0.5, 1e-12)


@pytest.mark.parametrize("pt", [(2e-6, 0.7, 0.8, 0.1), (3e-6, 0.31, 0.66, 0.42), (1e-6, 0.95, 0.55, 0.0)])
def test_toy_offgrid_other_axes(toy_memo, pt):
    """[r5] VGS·VDS 격자 밖: ln ID 는 4.2 Hermite(r5 toy 에서 닫힌 식과 같다), VS 방향 기울기 = ln(0.5)/0.5."""
    L, vgs, vds, vsb = pt
    ID = math.exp(r5_toy_lnid(vgs, vds, vsb, L))
    hand = -ID * math.log(0.5) / 0.5
    assert rel_close(gmb(toy_memo, "nmos", 100, *pt), hand, 1e-12)
    # 독립 Hermite 구현으로 같은 식
    rs = RefSlice(toy_slice_arrays(1e-6))
    Lw = anchor_w(TOY_L.index(L))
    l0 = rs.op(Lw, L, vgs, vds, 0.0)["lnID"]
    l1 = rs.op(Lw, L, vgs, vds, 0.5)["lnID"]
    idp = math.exp(rs.op(Lw, L, vgs, vds, vsb)["lnID"])
    assert rel_close(gmb(toy_memo, "nmos", 100, *pt), -idp * (l1 - l0) / 0.5, 1e-12)


def _secant_grid(z, iL, iG, k, s):
    VS = [float(x) for x in z["VS"]]
    lI = log_floor(z["ID"])[0]
    kk = min(bisect.bisect_right(VS, VS[s]) - 1, len(VS) - 2)
    return -float(z["ID"][iL, iG, k, s]) * (lI[iL, iG, k, kk + 1] - lI[iL, iG, k, kk]) / (VS[kk + 1] - VS[kk])


@pytest.mark.lut_realdata
def test_real_grid_points_column_definition(real_memo, raw_slice):
    """[r6] LUT v2(재생성 슬라이스, 열 출처 "slice"): 격자점 gmb = 저장 GMBS(= ID × GMBS/ID). 판별: r5 할선과는 다르다
    (계약 4.4 실측 상대차 p50 ≈ 2 %)."""
    rng = np.random.default_rng(3)
    for kind, wk in (("nmos", 1000), ("pmos", 84), ("nmos", 72)):
        z = raw_slice(kind, wk)
        nL = len(z["L"])
        n = n_diff = 0
        while n < 20:
            iL, iG, k, s = int(rng.integers(0, nL)), int(rng.integers(10, 49)), int(rng.integers(1, 49)), int(rng.integers(0, 10))
            I = float(z["ID"][iL, iG, k, s])
            if not np.all(z["ID"][iL, iG, k, :] > 0):
                continue
            got = gmb(real_memo, kind, wk, float(z["L"][iL]), float(z["VGS"][iG]), float(z["VDS"][k]), float(z["VS"][s]))
            exp = float(z["GMBS"][iL, iG, k, s])
            assert abs(got - exp) <= _col_rel_bound(math.log(I)) * abs(exp), (kind, wk, iL, iG, k, s, got, exp)
            n_diff += not rel_close(got, _secant_grid(z, iL, iG, k, s), 1e-6)
            n += 1
        assert n_diff > n // 2, (kind, wk, n_diff)                    # 할선 정의였다면 이 test 는 실패한다


@pytest.mark.lut_realdata
def test_real_offgrid_matches_independent_column(real_memo, real_lut, raw_slice):
    """[r6] 격자 밖(L 같은 bin 보간 포함): gmb = 독립 4.4 구현(conftest gmb_column_ref -- 4.2 lnID 의 exp × GMBS/ID 선형 보간)."""
    rng = np.random.default_rng(31)
    for kind, wk in (("nmos", 1000), ("pmos", 1000), ("pmos", 84)):
        z = raw_slice(kind, wk)
        rs = RefSlice(z)
        ab = tuple(real_lut.slice_map[(kind, wk)].l_bins.anchor_bin)
        Lg = rs.grids[0]
        n = 0
        while n < 15:
            iL = int(rng.integers(0, len(Lg) - 1))
            L = Lg[iL] if n % 2 == 0 else float(Lg[iL] + 0.4 * (Lg[iL + 1] - Lg[iL]))
            pos = l_weights(Lg, ab, L)
            if pos is None:
                continue
            vgs, vds, vsb = float(rng.uniform(0.6, 1.79)), float(rng.uniform(0.1, 1.79)), float(rng.uniform(0, 1.79))
            lnid = rs.op(pos[0], L, vgs, vds, vsb)["lnID"]
            exp = gmb_column_ref(z, pos[0], vgs, vds, vsb)
            got = gmb(real_memo, kind, wk, L, vgs, vds, vsb)
            assert abs(got - exp) <= _col_rel_bound(lnid) * abs(exp) + 0.0, (kind, wk, L, vgs, vds, vsb, got, exp)
            n += 1


@pytest.mark.lut_realdata
def test_real_column_vs_cap_table_gmbs(real_memo, raw_slice, raw_cap):
    """기록(판정 아님 -- 계약 4.4 실측 '열 경로 대 기준 LUT 저장 GMBS 최대 4.9e-7'): w_key 1000 격자점에서 슬라이스 열 경로 gmb 와
    기준 LUT GMBS 의 상대차. 판정은 '같은 자릿수' 대신 슬라이스 GMBS 와의 일치(위 test)로 한다."""
    z = raw_slice("nmos", 1000)
    rng = np.random.default_rng(5)
    worst = 0.0
    for _ in range(30):
        iL, iG, k, s = int(rng.integers(0, len(z["L"]))), int(rng.integers(20, 49)), int(rng.integers(5, 49)), int(rng.integers(0, 10))
        got = gmb(real_memo, "nmos", 1000, float(z["L"][iL]), float(z["VGS"][iG]), float(z["VDS"][k]), float(z["VS"][s]))
        ref = float(raw_cap["GMBS_n"][iL, iG, k, s])
        worst = max(worst, abs(got - ref) / abs(ref))
    print("gmb 열 경로 대 기준 LUT GMBS 상대차 최대 %.3g (계약 실측 4.9e-7)" % worst)


@pytest.mark.lut_realdata
def test_nocol_set_secant_and_cap_table_column(nocol_lut, nocol_raw_slice, raw_cap):
    """결정 B 이전 v2 슬라이스(GMBS 열 없음): w_key 84 는 r5 VS 할선(열 없음 -> 4.1 표 정의), w_key 1000 은 기준 LUT 열
    ("cap_table") -- 격자점에서 r·ID(점) = 저장 GMBS × (슬라이스 ID / 기준 LUT ID)(4.4)."""
    m = new_memo(nocol_lut, 1024)
    rng = np.random.default_rng(13)
    z = nocol_raw_slice("pmos", 84)
    n = 0
    while n < 10:
        iL, iG, k, s = int(rng.integers(0, len(z["L"]))), int(rng.integers(10, 49)), int(rng.integers(1, 49)), int(rng.integers(0, 10))
        if not np.all(z["ID"][iL, iG, k, :] > 0):
            continue
        got = gmb(m, "pmos", 84, float(z["L"][iL]), float(z["VGS"][iG]), float(z["VDS"][k]), float(z["VS"][s]))
        assert rel_close(got, _secant_grid(z, iL, iG, k, s), 1e-10)
        n += 1
    z = nocol_raw_slice("nmos", 1000)
    n = 0
    while n < 10:
        iL, iG, k, s = int(rng.integers(0, len(z["L"]))), int(rng.integers(10, 49)), int(rng.integers(1, 49)), int(rng.integers(0, 10))
        I, Ic = float(z["ID"][iL, iG, k, s]), float(raw_cap["ID_n"][iL, iG, k, s])
        if not (I > 0 and Ic > 0):
            continue
        got = gmb(m, "nmos", 1000, float(z["L"][iL]), float(z["VGS"][iG]), float(z["VDS"][k]), float(z["VS"][s]))
        exp = float(raw_cap["GMBS_n"][iL, iG, k, s]) * I / Ic
        assert abs(got - exp) <= _col_rel_bound(math.log(I)) * abs(exp), (iL, iG, k, s, got, exp)
        n += 1


# ---------------------------------------------------------------------------
# [r6] toy: 7.1 r6 표 마지막 행, 중점 toy(GMBS/ID 가 모든 축 선형 -> 닫힌 식), memo compute 횟수
# ---------------------------------------------------------------------------

def test_contract_toy_r6_row_cap_table_column(toy_build):
    """7.1 r6: 기준 LUT GMBS_n = 0.25·ID_n -> gmb(nmos, 100, 1e-6, 0.25, 0.5, 0.0) = 0.25·ID(점), ID(점) = op_point IDu·w_m/L
    (= 1e-7·e^4.675·e^0.05 -- r5 toy 닫힌 식)."""
    m = new_memo(toy_build("r6gmb", cap=r6_toy_cap_arrays()).load())
    L, vgs, vds, vsb = 1e-6, 0.25, 0.5, 0.0
    idp = op_point(m, "nmos", 100, L, vgs, vds, vsb).IDu * 1e-6 / L
    got = gmb(m, "nmos", 100, L, vgs, vds, vsb)
    assert rel_close(got, 0.25 * idp, 1e-12)
    assert rel_close(got, 0.25 * math.exp(r5_toy_lnid(vgs, vds, vsb)), 1e-12)
    # 판별: r5 할선(−ID·ln(0.5)/0.5 ≈ 1.386·ID)과 다르다
    assert not rel_close(got, -idp * math.log(0.5) / 0.5, 1e-3)


def test_contract_toy_r6_without_column_is_r5(toy_memo):
    """7.1 r6 표: GMBS 열 없음 -> r5 값 그대로."""
    assert rel_close(gmb(toy_memo, "nmos", 100, 1e-6, 0.5, 0.5, 0.25), 5.064753e-4, 1e-6)


@pytest.mark.parametrize("L", [3e-6, 3.5e-6, 1.25e-6, 7.25e-6])
def test_mid_toy_slice_column_closed_form(mid_toy_build, L):
    """중점 toy(슬라이스 GMBS 열, GMBS/ID = 0.3·(1 + 0.1v + 0.2d + 0.05vs) -- 모든 축 선형이라 r 보간이 정확):
    gmb = ID(점) × 0.3·(1 + 0.1·vgs + 0.2·vds + 0.05·vsb), ID(점) = op_point 값. L 은 앵커·같은 bin 보간 모두."""
    m = new_memo(mid_toy_build("g%d" % int(L * 1e8)).load())
    vgs, vds, vsb = 0.3, 0.6, 0.2
    idp = op_point(m, "nmos", 100, L, vgs, vds, vsb).IDu * 1e-6 / L
    r = 0.3 * (1 + 0.1 * vgs + 0.2 * vds + 0.05 * vsb)
    got = gmb(m, "nmos", 100, L, vgs, vds, vsb)
    assert rel_close(got, idp * r, 1e-12)
    z = mid_toy_arrays(1e-6, 1.0, {})
    lw = l_weights(BIN_L, (0, 0, 0, 1, 1, 3, 3, 4), L)
    assert rel_close(got, gmb_column_ref(z, lw[0], vgs, vds, vsb), 1e-12)


def test_column_nan_ratio_falls_back_to_gmbs_interpolation(toy_build):
    """4.4: r 이 NaN(가중치 ≠ 0 인 모서리에 ID ≤ 0)이면 GMBS 열 값의 같은 선형 보간. 기준 LUT ID_n 한 점을 0 으로 -> 그 점을
    모서리로 쓰는 조회는 GMBS 보간 × ... 이 아니라 GMBS 보간 그대로가 gmb."""
    cap = r6_toy_cap_arrays()
    cap["ID_n"] = cap["ID_n"].copy()
    cap["ID_n"][0, 1, 0, 0] = 0.0                                   # (L 1e-6, VGS 0.5, VDS 0.5, VS 0)
    m = new_memo(toy_build("nanr", cap=cap).load())
    L, vgs, vds, vsb = 1e-6, 0.25, 0.5, 0.0                          # VGS 칸 [0, 0.5] -> 모서리 (0, 1, 0, 0) 포함
    got = gmb(m, "nmos", 100, L, vgs, vds, vsb)
    G = cap["GMBS_n"]
    exp = 0.5 * float(G[0, 0, 0, 0]) + 0.5 * float(G[0, 1, 0, 0])
    assert rel_close(got, exp, 1e-12)
    # 그 모서리를 쓰지 않는 조회(VGS 칸 [0.5, 1] 의 t = 1 끝 -- 가중치 0 인 마디는 읽지 않음)는 r 경로
    got2 = gmb(m, "nmos", 100, L, 1.0, 0.5, 0.0)
    idp = op_point(m, "nmos", 100, L, 1.0, 0.5, 0.0).IDu * 1e-6 / L
    assert rel_close(got2, 0.25 * idp, 1e-12)


def test_memo_column_path_one_op_point(toy_build):
    """2절 [r6]: GMBS 열이 있으면 gmb compute 는 op_point 1회(조회점) -- 첫 호출 point misses = gmb 1 + op_point 1.
    열이 없으면(w_key 200) r5 그대로 op_point ≤ 3."""
    m = new_memo(toy_build("memo1", cap=r6_toy_cap_arrays()).load())
    gmb(m, "nmos", 100, 1e-6, 0.3, 0.6, 0.2)
    st = dict(m.stats())["point"]
    assert st.misses == 2 and st.hits == 0
    gmb(m, "nmos", 100, 1e-6, 0.3, 0.6, 0.2)
    st = dict(m.stats())["point"]
    assert st.misses == 2 and st.hits == 1
    m2 = new_memo(toy_build("memo2", cap=r6_toy_cap_arrays()).load())
    gmb(m2, "nmos", 200, 1e-6, 0.3, 0.6, 0.2)
    st2 = dict(m2.stats())["point"]
    assert st2.misses == 4                                           # gmb 1 + op_point 3 (VS 칸 양끝·조회점)
