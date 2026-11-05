"""`_helpers_anchor` (l_position) -- CONTRACT 4.0 [r4]: L = 앵커(|L − a| ≤ ulp(a), 범위 검사보다 먼저) 또는 같은 모델 bin 의
양옆 앵커 사이 보간(L 두 장 다중선형, L 값은 조회 L 그대로). bin 경계를 건너면 거부 -- lut_l_outside_model_bins /
lut_l_bin_unbracketed / lut_l_cross_bin(4.0 의 detail), 빈 bin 지도면 lut_l_not_anchor(bins "unavailable").
범위 밖 -> lut_axis_out_of_range(axis "L"). 공개 조회 전부로 확인한다(TolVTable.at 은 test_tolerance).
앵커 전용 toy(빈 지도) 행은 r2/r3 그대로, bin toy 행(conftest 머리 표)은 npz 배열에서 독립 계산한 기대값과 대조한다.
"""
import bisect
import math

import numpy as np
import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.lut import caps, gm_id_curve, gm_id_for_target, gmb, op_point, vgs_for_gm_id

from .conftest import (BIN_L, RefSlice, bin_cap_arrays, bin_toy_raw, detail_of, expected_op, gmb_column_ref, interp4,
                       new_memo,
                       rel_close, same_bounds, sir_ref_b, target_ref, two_sheet, um)

ULP = math.ulp(1e-6)

CALLS = {
    "op_point": lambda m, L: op_point(m, "nmos", 100, L, 0.5, 0.5, 0.0),
    "gmb": lambda m, L: gmb(m, "nmos", 100, L, 0.5, 0.5, 0.25),
    "gm_id_curve": lambda m, L: gm_id_curve(m, "nmos", 100, L, 0.5, 0.0),
    "vgs_for_gm_id": lambda m, L: vgs_for_gm_id(m, "nmos", 100, 15.0, L, 0.5, 0.0),
    "gm_id_for_target": lambda m, L: gm_id_for_target(m, "nmos", 100, L, 0.5, 0.0, W=2e-6, current=2e-6),
    "caps": lambda m, L: caps(m, "nmos", L, 0.5, 0.5, 0.0, 3e-6),
}


def _ctx_ok(name, det):
    assert det["kind"] == "nmos"
    if name == "caps":
        assert det["table"] == "cap" and "w_key" not in det
    else:
        assert det["w_key"] == 100


@pytest.mark.parametrize("name", sorted(CALLS))
@pytest.mark.parametrize("L,below,above", [
    (1.5e-6, 1e-6, 2e-6),                     # 계약 7절
    (1e-6 + 1e-8, 1e-6, 2e-6),                # [WB-1] 옛 '2 ulp' 행: 한 격자 간격 위(정수 101 != 앵커 100)는 앵커 아님
    (2.9e-6, 2e-6, 3e-6),
    (3e-6 - 1e-8, 2e-6, 3e-6),                # [WB-1] 옛 '2 ulp 아래' 행: 한 격자 간격 아래(정수 299 != 300)
])
def test_non_anchor_rejected(toy_empty_memo, name, L, below, above):
    # [WB-1 §4] 앵커 전용(빈 지도) toy = bin 블록 없는 합성 모델 파일(`toy_empty_memo`)
    toy_memo = toy_empty_memo
    with pytest.raises(SealViolationError) as ei:
        CALLS[name](toy_memo, L)
    det = detail_of(ei.value)
    assert det["reason"] == "lut_l_not_anchor"
    assert det["value"] == L and det["below"] == below and det["above"] == above
    assert det["bins"] == "unavailable"                     # [r4] 빈 지도 경로(toy 는 모델 파일 기록 없음)
    _ctx_ok(name, det)


@pytest.mark.parametrize("name", sorted(CALLS))
@pytest.mark.parametrize("L", [0.5e-6, 4e-6, float("nan")])
def test_out_of_range_l(toy_memo, name, L):
    with pytest.raises(SealViolationError) as ei:
        CALLS[name](toy_memo, L)
    det = detail_of(ei.value)
    assert det["reason"] == "lut_axis_out_of_range" and det["axis"] == "L"
    _ctx_ok(name, det)


@pytest.mark.parametrize("name", sorted(CALLS))
@pytest.mark.parametrize("a,cands", [
    (1e-6, (1e-6 + ULP, 1e-6 - ULP)),                                       # 계약 7절 + [r3] 첫 앵커 아래 1 ulp
    (3e-6, (3e-6 + math.ulp(3e-6), 3e-6 - math.ulp(3e-6))),                 # [r3] 마지막 앵커 위 1 ulp
    (2e-6, (math.nextafter(2e-6, 1.0), math.nextafter(2e-6, 0.0))),         # 내부 앵커 양쪽 1 ulp
])
def test_within_one_ulp_is_anchor(toy_memo, name, a, cands):
    exact = CALLS[name](toy_memo, a)
    for L in cands:
        assert L != a and abs(L - a) <= math.ulp(a)
        got = CALLS[name](toy_memo, L)
        if name == "gm_id_curve":
            assert np.array_equal(np.asarray(got.id_vals), np.asarray(exact.id_vals))
            assert np.array_equal(np.asarray(got.gm_id_vals), np.asarray(exact.gm_id_vals))
        else:
            assert got == exact, name


def test_anchor_value_used_for_l_dependent_outputs(toy_memo):
    # IDu = ID·a/w_m, id_a = IDu·W/a -- 입력 L 이 아니라 앵커 a 값
    L = 1e-6 + ULP
    op = op_point(toy_memo, "nmos", 100, L, 0.5, 0.5, 0.0)
    assert op.IDu == op_point(toy_memo, "nmos", 100, 1e-6, 0.5, 0.5, 0.0).IDu
    # [r5] r5 toy: ID(1e-6, 0.5, 0.5, 0) = 1e-7·e^(10 − 1.5 + 0.05), IDu = ID·a/w_m
    assert rel_close(op.IDu, 1e-7 * math.exp(8.55) * 1e-6 / 1e-6, 1e-12)
    r = gm_id_for_target(toy_memo, "nmos", 100, L, 0.5, 0.0, W=2e-6, current=2e-6)
    assert rel_close(r.id_a, 2e-6, 1e-12)
    r0 = gm_id_for_target(toy_memo, "nmos", 100, 1e-6, 0.5, 0.0, W=2e-6, current=2e-6)
    assert r == r0


def test_point_memo_key_shared_within_ulp(toy_memo):
    a = op_point(toy_memo, "nmos", 100, 2e-6, 0.3, 0.6, 0.2)
    b = op_point(toy_memo, "nmos", 100, math.nextafter(2e-6, 1.0), 0.3, 0.6, 0.2)
    assert a is b
    st = dict(toy_memo.stats())["point"]
    assert st.misses == 1 and st.hits == 1


def test_no_l_interpolation_anywhere(toy_memo):
    """앵커 위 값은 그 앵커 한 장만으로 정해진다: L=2e-6 의 IDu 는 이웃 앵커 값과 무관
    ([r5] r5 toy 손계산 ID·L/w = (1/2)·1e-7·e^8.55·2)."""
    op = op_point(toy_memo, "nmos", 100, 2e-6, 0.5, 0.5, 0.0)
    assert rel_close(op.IDu, 0.5 * 1e-7 * math.exp(8.55) * 2e-6 / 1e-6, 1e-12)


@pytest.mark.lut_realdata
@pytest.mark.parametrize("kind,device", [("nmos", "nfet_01v8"), ("pmos", "pfet_01v8")])
def test_real_non_anchor_midpoints(real_lut, raw_slice, ngspice_bins, kind, device):
    """[r4, test author 복원] 모든 이웃 앵커 중점: 기대 결과를 ngspice showmod(앵커·중점의 실제 bin)로 독립으로 정해 **모든 중점**을
    판정한다(성공도 침묵 통과가 아니라 값 대조). 같은 bin 쌍 -> 보간값 = npz 두 장 독립 보간, 아니면 중점 bin 의 앵커 수로 사유 키."""
    memo = new_memo(real_lut, 4096)
    z = raw_slice(kind, 1000)
    W = um(float(z["W"]))
    L = [float(x) for x in z["L"]]
    mids = [0.5 * (L[i] + L[i + 1]) for i in range(len(L) - 1)]
    q = ngspice_bins.query(device, [(W, um(a)) for a in L] + [(W, um(m)) for m in mids])
    ga, gm = q[:len(L)], q[len(L):]
    seen = set()
    g = real_lut.spec.manufacturing_grid_m
    for i, mid in enumerate(mids):
        if round(mid / g) in (round(L[i] / g), round(L[i + 1] / g)):
            # [WB-1 §1] 격자 정수 비교: 이웃 앵커가 한 격자 간격이면 중점이 앵커로 반올림된다 -> 두 앵커 중 하나의 값
            got = op_point(memo, kind, 1000, mid, 0.9, 0.9, 0.0)
            assert got in (op_point(memo, kind, 1000, L[i], 0.9, 0.9, 0.0), op_point(memo, kind, 1000, L[i + 1], 0.9, 0.9, 0.0))
            continue
        if same_bounds(ga[i], ga[i + 1]):
            op = op_point(memo, kind, 1000, mid, 0.9, 0.9, 0.0)
            exp = expected_op(z, mid, 0.9, 0.9, 0.0)
            for f, v in exp.items():
                assert rel_close(getattr(op, f), v, 1e-11), (mid, f, getattr(op, f), v)
            seen.add("interp")
            continue
        with pytest.raises(SealViolationError) as ei:
            op_point(memo, kind, 1000, mid, 0.9, 0.9, 0.0)
        det = detail_of(ei.value)
        in_bin = tuple(a for a, g in zip(L, ga) if same_bounds(g, gm[i]))
        if gm[i] is None:
            want = "lut_l_outside_model_bins"
        else:
            want = "lut_l_bin_unbracketed" if len(in_bin) <= 1 else "lut_l_cross_bin"
        assert det["reason"] == want, (mid, det)
        assert det["below"] == L[i] and det["above"] == L[i + 1] and det["value"] == mid
        assert det["kind"] == kind and det["w_key"] == 1000
        if gm[i] is not None:
            assert tuple(det["bin_anchors"]) == in_bin
        seen.add(want)
    # 실데이터 중점은 보간·두 거부 사유를 모두 지난다(경로가 실제로 쓰였다)
    assert seen == {"interp", "lut_l_bin_unbracketed", "lut_l_cross_bin"}, seen


# ---------------------------------------------------------------------------
# [r3] 양끝 앵커: 앵커 일치 검사가 범위 검사보다 먼저 -- 격자 밖 쪽 1 ulp 는 그 앵커, 2 ulp 는 축 밖
# ---------------------------------------------------------------------------

EDGES = (("first", 1e-6, -1.0), ("last", 3e-6, 1.0))


@pytest.mark.parametrize("name", sorted(CALLS))
@pytest.mark.parametrize("edge,a,sign", EDGES)
def test_edge_anchor_one_ulp_outside_accepted(toy_memo, name, edge, a, sign):
    L = a + sign * math.ulp(a)
    assert (L < 1e-6) if edge == "first" else (L > 3e-6)          # 격자 범위 밖 쪽
    exact = CALLS[name](toy_memo, a)
    got = CALLS[name](toy_memo, L)
    if name == "gm_id_curve":
        assert np.array_equal(np.asarray(got.id_vals), np.asarray(exact.id_vals))
        assert np.array_equal(np.asarray(got.gm_id_vals), np.asarray(exact.gm_id_vals))
    else:
        assert got == exact, name


@pytest.mark.parametrize("name", sorted(CALLS))
@pytest.mark.parametrize("edge,a,sign", EDGES)
def test_edge_two_ulp_outside_rejected(toy_memo, name, edge, a, sign):
    # [WB-1 §1 격자 정수 비교] 옛 '2 ulp 밖' -> 한 격자 간격 밖(round(L/g) != 양끝 앵커 정수 -> 축 밖). 2 ulp 는 앵커로 받아들인다(위 test)
    L = a + sign * 1e-8
    with pytest.raises(SealViolationError) as ei:
        CALLS[name](toy_memo, L)
    det = detail_of(ei.value)
    assert det["reason"] == "lut_axis_out_of_range" and det["axis"] == "L" and det["value"] == L
    assert det["lo"] == 1e-6 and det["hi"] == 3e-6
    _ctx_ok(name, det)


@pytest.mark.parametrize("edge,a,sign", EDGES)
def test_edge_one_ulp_shares_memo_key(toy, edge, a, sign):
    from .conftest import new_memo
    m = new_memo(toy)
    p0 = op_point(m, "nmos", 100, a, 0.3, 0.6, 0.2)
    p1 = op_point(m, "nmos", 100, a + sign * math.ulp(a), 0.3, 0.6, 0.2)
    assert p1 is p0
    c0 = gm_id_curve(m, "nmos", 100, a, 0.6, 0.2)
    c1 = gm_id_curve(m, "nmos", 100, a + sign * math.ulp(a), 0.6, 0.2)
    assert c1 is c0
    st = dict(m.stats())
    assert (st["point"].misses, st["point"].hits) == (1, 1)
    assert (st["curve"].misses, st["curve"].hits) == (1, 1)


@pytest.mark.parametrize("edge,a,sign", EDGES)
def test_edge_tol_v_at(toy_memo, edge, a, sign):
    from gmid_engine.lut import tol_v_table
    t = tol_v_table(toy_memo, "nmos", 100)
    for metric in ("gm_id_inverse", "id_equivalent"):
        assert t.at(a + sign * math.ulp(a), 0.75, metric) == t.at(a, 0.75, metric)
    with pytest.raises(SealViolationError) as ei:
        t.at(a + sign * 1e-8, 0.75, "gm_id_inverse")                       # [WB-1] 옛 2 ulp -> 한 격자 간격(격자 정수 비교)
    det = detail_of(ei.value)
    assert det["reason"] == "lut_axis_out_of_range" and det["axis"] == "L" and det["table"] == "tol_v"


@pytest.mark.lut_realdata
def test_real_edge_anchors(real_memo, raw_slice):
    z = raw_slice("pmos", 1000)
    lo, hi = float(z["L"][0]), float(z["L"][-1])
    for a, sign in ((lo, -1.0), (hi, 1.0)):
        exact = op_point(real_memo, "pmos", 1000, a, 0.9, 0.9, 0.2)
        assert op_point(real_memo, "pmos", 1000, a + sign * math.ulp(a), 0.9, 0.9, 0.2) is exact
        with pytest.raises(SealViolationError) as ei:
            op_point(real_memo, "pmos", 1000, a + sign * 5e-9, 0.9, 0.9, 0.2)      # [WB-1] 옛 2 ulp -> 실 LUT 격자 5 nm 한 칸
        assert detail_of(ei.value)["reason"] == "lut_axis_out_of_range"


# ---------------------------------------------------------------------------
# [r4] bin toy: 같은 bin 보간 값(npz 두 장 독립 계산)과 bin 경계 거부 -- 모든 조회 진입점
# ---------------------------------------------------------------------------

def _lw(z, L):
    """4.0 L 위치(앵커 또는 같은 bin 두 장)의 선형 가중치 -- 가중치 0 인 장은 뺀다."""
    lo, hi = two_sheet(z["L"], L)
    Lg = [float(x) for x in z["L"]]
    if hi >= len(Lg):
        return ((lo, 1.0),)
    t = (L - Lg[lo]) / (Lg[hi] - Lg[lo])
    return tuple((i, w) for i, w in ((lo, 1.0 - t), (hi, t)) if w != 0.0)


def exp_curve(z, L, vds, vs):
    """[r5] 곡선 마디 기대값(4.2: V_a·S_a·cell_ok) + 마디 두 경로 차 상한(dV, dS)."""
    rs = RefSlice(z)
    Lw = _lw(z, L)
    V, S, ok = rs.curve(Lw, vds, vs)
    dV, dS = rs.curve_err(Lw, vds, vs)
    return V, S, ok, dV, dS


def exp_gmb(z, L, vgs, vds, vs):
    """[r5] gmb = −ID(점)·(ln IDu(VS[k+1]) − ln IDu(VS[k]))/ΔVS, ln ID 는 4.2 축별 보간(RefSlice).
    [r6] 슬라이스에 GMBS 열이 있으면 4.4 정본(ID(점) × GMBS/ID 선형 보간 -- conftest gmb_column_ref)."""
    rs = RefSlice(z)
    Lw = _lw(z, L)
    if "GMBS" in z:
        return gmb_column_ref(z, Lw, vgs, vds, vs)
    VS = list(rs.grids[3])
    k = min(bisect.bisect_right(VS, vs) - 1, len(VS) - 2)
    d = rs.op(Lw, L, vgs, vds, VS[k + 1])["lnID"] - rs.op(Lw, L, vgs, vds, VS[k])["lnID"]
    return -math.exp(rs.op(Lw, L, vgs, vds, vs)["lnID"]) * d / (VS[k + 1] - VS[k])


def check_root_in_bin(memo, wk, z, L, vds, vs, target):
    """[r5] vgs_for_gm_id 기대: 독립 칸 선택(3절) -- 칸 단조 위반이면 lut_hermite_nonmonotone_cell, 해 없음이면
    lut_no_strong_inversion_root, 그 밖은 독립 Hermite 근과 유도 상한(conftest) 안에서 같다."""
    V, S, ok, dV, dS = exp_curve(z, L, vds, vs)
    st, v, rb = sir_ref_b(z["VGS"], V, S, target, ok, dV=dV, dS=dS)
    if st == "ok":
        got = vgs_for_gm_id(memo, "nmos", wk, target, L, vds, vs)
        assert abs(got - v) <= rb, (L, target, got, v, rb)
        return got
    with pytest.raises(SealViolationError) as ei:
        vgs_for_gm_id(memo, "nmos", wk, target, L, vds, vs)
    assert detail_of(ei.value)["reason"] == {"nonmono": "lut_hermite_nonmonotone_cell",
                                             "none": "lut_no_strong_inversion_root"}[st]
    return None


def exp_caps(cap, L, vgs, vds, vs, W):
    lo, hi = two_sheet(cap["L"], L)
    grids = ((float(cap["L"][lo]), float(cap["L"][hi])), tuple(cap["VGS"]), tuple(cap["VDS"]), tuple(cap["VS"]))
    cgg = interp4(grids, cap["CGG_n"][lo:hi + 1], (L, vgs, vds, vs)) * W / float(cap["w_ref_m"])
    cgd = interp4(grids, cap["CGD_n"][lo:hi + 1], (L, vgs, vds, vs)) * W / float(cap["w_ref_m"])
    return cgg, cgd


def check_target_in_bin(memo, wk, z, L, vds, vs, W):
    """[r5] gm_id_for_target(current) 기대: 목표 = Q[p]·Q[p+1] 기하 평균(분지 첫 칸 안). 독립 target_ref 가
    칸 단조 위반이면 그 사유로 실패, 그 밖은 근 차·왕복 차 ≤ 유도 상한, gm_id·id_a = 그 vgs 의 독립 op 값."""
    V, S, ok, dV, dS = exp_curve(z, L, vds, vs)
    w = float(z["W"])
    Q = np.exp(V) * W / w
    p = int(np.argmax(S))
    T = math.sqrt(Q[p] * Q[p + 1])
    res = target_ref(z["VGS"], V, S, ok, w, W, "current", T, with_bound=True, dV=dV, dS=dS)
    if res[0] != "ok":
        with pytest.raises(SealViolationError) as ei:
            gm_id_for_target(memo, "nmos", wk, L, vds, vs, W=W, current=T)
        assert detail_of(ei.value)["reason"] == res[0]
        return None
    _, vgs, rb, tb = res
    r = gm_id_for_target(memo, "nmos", wk, L, vds, vs, W=W, current=T)
    assert abs(r.vgs - vgs) <= rb, (L, r.vgs, vgs, rb)
    assert abs(math.log(r.id_a) - math.log(T)) <= tb
    op = op_point(memo, "nmos", wk, L, r.vgs, vds, vs)
    assert r.gm_id == op.gm_over_id and r.id_a == op.IDu * W / L and r.gm_s == r.gm_id * r.id_a
    return r


IN_BIN_L = (1.25e-6, 1.75e-6, 3.5e-6, 7.5e-6)          # A·A·B·D 안 (같은 bin 양옆 앵커)


@pytest.mark.parametrize("L", IN_BIN_L)
def test_bin_op_point_interpolates_in_bin(bin_memo, L):
    z = bin_toy_raw()
    op = op_point(bin_memo, "nmos", 100, L, 0.3, 0.7, 0.2)
    for f, v in expected_op(z, L, 0.3, 0.7, 0.2).items():
        assert rel_close(getattr(op, f), v, 1e-12), (f, getattr(op, f), v)
    # 보간이 실제로 L 두 장을 섞었다: 이웃 앵커 값 어느 쪽과도 다르다(VTH 는 L² 이라 선형 보간 ≠ 정확값)
    lo, hi = two_sheet(z["L"], L)
    for a in (BIN_L[lo], BIN_L[hi]):
        assert op.vth != op_point(bin_memo, "nmos", 100, a, 0.3, 0.7, 0.2).vth
    assert not rel_close(op.vth, 0.4 + 0.01 * (L / 1e-6) ** 2, 1e-6)


@pytest.mark.parametrize("L", IN_BIN_L)
def test_bin_gmb_curve_root_caps_interpolate_in_bin(bin_memo, bin_toy_build, L):
    z = bin_toy_raw()
    assert rel_close(gmb(bin_memo, "nmos", 100, L, 0.3, 0.7, 0.2), exp_gmb(z, L, 0.3, 0.7, 0.2), 1e-12)
    c = gm_id_curve(bin_memo, "nmos", 100, L, 0.7, 0.2)
    V, S, ok, _, _ = exp_curve(z, L, 0.7, 0.2)
    assert np.allclose(np.asarray(c.id_vals), np.exp(V), rtol=1e-12, atol=0)
    assert np.allclose(np.asarray(c.gm_id_vals), S, rtol=1e-12, atol=0)
    assert tuple(bool(x) for x in c.cell_ok) == ok
    assert tuple(float(v) for v in c.vgs_grid) == tuple(float(v) for v in z["VGS"])
    # [r5] 기본 bin toy 는 r4 toy 의 VGS 자료(칸 0 FC 위반) -- 역산은 독립 칸 선택대로 실패 또는 근
    check_root_in_bin(bin_memo, 100, z, L, 0.7, 0.2, 15.0)
    check_target_in_bin(bin_memo, 100, z, L, 0.7, 0.2, 2e-6)
    # 기울기 자료가 맞는 bin toy: 같은 bin 보간 곡선에서 실제 근(독립 Hermite·유도 상한)
    zc = bin_toy_raw(consistent=True)
    mc = new_memo(bin_toy_build("bt_cons", consistent=True).load())
    _, Sc, _, _, _ = exp_curve(zc, L, 0.7, 0.2)
    tgt = 0.5 * (float(Sc[1]) + float(Sc[2]))                       # 분지 안 칸 [1, 2] 의 목표
    assert check_root_in_bin(mc, 100, zc, L, 0.7, 0.2, tgt) is not None
    assert check_target_in_bin(mc, 100, zc, L, 0.7, 0.2, 2e-6) is not None
    cp = caps(bin_memo, "nmos", L, 0.3, 0.7, 0.2, 3e-6)
    cgg, cgd = exp_caps(bin_cap_arrays(), L, 0.3, 0.7, 0.2, 3e-6)
    assert rel_close(cp.cgg, cgg, 1e-12) and rel_close(cp.cgd, cgd, 1e-12)
    assert rel_close(cp.cgs, cgg - cgd, 1e-12) and cp.cgb == 0.0
    assert not rel_close(cp.cgg, 1e-15 * (L / 1e-6) ** 2 * 3, 1e-6)          # 선형 보간(정확값 L² 아님)


def test_bin_anchor_exact_on_bin_toy(bin_memo):
    z = bin_toy_raw()
    op = op_point(bin_memo, "nmos", 100, 3e-6, 0.5, 0.5, 0.0)
    assert rel_close(op.IDu, float(z["ID"][3, 1, 0, 0]) * 3e-6 / 1e-6, 1e-12)   # 로그공간 왕복(exp∘ln)만큼
    assert rel_close(op.vth, float(z["VTH"][3, 1, 0, 0]), 1e-14)
    assert op_point(bin_memo, "nmos", 100, math.nextafter(3e-6, 1.0), 0.5, 0.5, 0.0) is op


def test_bin_upper_width_map_used(bin_memo):
    """폭 키 200(위 W 범위: A' [1, 4]) 은 2.5 µm 를 보간하고, 폭 키 100(아래 범위: A·B 경계 2 µm) 은 거부한다."""
    z2 = bin_toy_raw(2.0, 2e-6)
    op = op_point(bin_memo, "nmos", 200, 2.5e-6, 0.3, 0.7, 0.2)
    for f, v in expected_op(z2, 2.5e-6, 0.3, 0.7, 0.2).items():
        assert rel_close(getattr(op, f), v, 1e-12), f
    with pytest.raises(SealViolationError) as ei:
        op_point(bin_memo, "nmos", 100, 2.5e-6, 0.3, 0.7, 0.2)
    assert detail_of(ei.value)["reason"] == "lut_l_cross_bin"
    with pytest.raises(SealViolationError) as ei:
        op_point(bin_memo, "nmos", 200, 5.5e-6, 0.3, 0.7, 0.2)        # 4(A')·7(D') 사이, D' 앵커 3개
    det = detail_of(ei.value)
    assert det["reason"] == "lut_l_cross_bin" and det["bin"] == "toyn__model.6" and det["w_key"] == 200


BIN_CALLS = {
    "op_point": lambda m, L: op_point(m, "nmos", 100, L, 0.3, 0.7, 0.2),
    "gmb": lambda m, L: gmb(m, "nmos", 100, L, 0.3, 0.7, 0.2),
    "gm_id_curve": lambda m, L: gm_id_curve(m, "nmos", 100, L, 0.7, 0.2),
    "vgs_for_gm_id": lambda m, L: vgs_for_gm_id(m, "nmos", 100, 15.0, L, 0.7, 0.2),
    "gm_id_for_target": lambda m, L: gm_id_for_target(m, "nmos", 100, L, 0.7, 0.2, W=2e-6, current=1e-7),
    "caps": lambda m, L: caps(m, "nmos", L, 0.3, 0.7, 0.2, 3e-6),
}

# (L, 사유, bin, bin_lmin, bin_lmax, bin 앵커, below, above, below_bin, above_bin) -- conftest 머리 표에서 손으로
M = "toyn__model."
BIN_REJECTS = [
    (2.5e-6, "lut_l_cross_bin", M + "1", 2e-6, 4e-6, (3e-6, 4e-6), 2e-6, 3e-6, M + "0", M + "1"),
    (6.5e-6, "lut_l_cross_bin", M + "3", 6e-6, 8e-6, (7e-6, 8e-6), 4e-6, 7e-6, M + "1", M + "3"),
    (4.5e-6, "lut_l_bin_unbracketed", M + "2", 4e-6, 5e-6, (), 4e-6, 7e-6, M + "1", M + "3"),
    (8.5e-6, "lut_l_bin_unbracketed", M + "4", 8e-6, 10e-6, (9e-6,), 8e-6, 9e-6, M + "3", M + "4"),
    (5.5e-6, "lut_l_outside_model_bins", None, None, None, None, 4e-6, 7e-6, M + "1", M + "3"),
]


@pytest.mark.parametrize("name", sorted(BIN_CALLS))
@pytest.mark.parametrize("row", BIN_REJECTS, ids=lambda r: "%s@%g" % (r[1], r[0]))
def test_bin_crossing_rejected_every_entry(bin_memo, name, row):
    """음성 확인: bin 경계를 건너는 L 은 어느 진입점에서도 값이 나오지 않고 거부된다(4.0 detail 전부)."""
    L, reason, b, blo, bhi, banc, below, above, bb, ab = row
    with pytest.raises(SealViolationError) as ei:
        BIN_CALLS[name](bin_memo, L)
    det = detail_of(ei.value)
    assert det["reason"] == reason
    assert det["value"] == L and det["below"] == below and det["above"] == above
    assert det["below_bin"] == bb and det["above_bin"] == ab
    if b is None:
        for key in ("bin", "bin_lmin", "bin_lmax", "bin_anchors"):
            assert key not in det
    else:
        assert det["bin"] == b and det["bin_lmin"] == blo and det["bin_lmax"] == bhi
        assert tuple(det["bin_anchors"]) == banc
    _ctx_ok(name, det)
    assert "bins" not in det                                # 'unavailable' 은 빈 지도 경로에만


@pytest.mark.parametrize("name", sorted(BIN_CALLS))
def test_bin_failed_lookup_not_memoized(bin_toy, name):
    m = new_memo(bin_toy)
    for _ in range(2):
        with pytest.raises(SealViolationError):
            BIN_CALLS[name](m, 2.5e-6)
    region = {"caps": "point", "op_point": "point", "gmb": "point", "gm_id_curve": "curve"}.get(name, "root")
    assert dict(m.stats())[region].hits == 0


def test_bin_in_bin_memo_hit(bin_toy):
    m = new_memo(bin_toy)
    a = op_point(m, "nmos", 100, 1.25e-6, 0.3, 0.7, 0.2)
    assert op_point(m, "nmos", 100, 1.25e-6, 0.3, 0.7, 0.2) is a
    b = op_point(m, "nmos", 100, 1.3e-6, 0.3, 0.7, 0.2)
    assert b is not a and b.IDu != a.IDu
    st = dict(m.stats())["point"]
    assert (st.misses, st.hits) == (2, 1)


# ---------------------------------------------------------------------------
# [r4] 실데이터: CONTRACT 4.0 실측 행(nmos w_key 1000, VGS = VDS = 0.9, VS = 0) -- 모든 진입점
# ---------------------------------------------------------------------------

REAL_CALLS = {
    "op_point": lambda m, L: op_point(m, "nmos", 1000, L, 0.9, 0.9, 0.0),
    "gmb": lambda m, L: gmb(m, "nmos", 1000, L, 0.9, 0.9, 0.2),
    "gm_id_curve": lambda m, L: gm_id_curve(m, "nmos", 1000, L, 0.9, 0.0),
    "vgs_for_gm_id": lambda m, L: vgs_for_gm_id(m, "nmos", 1000, 8.0, L, 0.9, 0.0),
    "gm_id_for_target": lambda m, L: gm_id_for_target(m, "nmos", 1000, L, 0.9, 0.0, W=5e-6, current=1e-4),
    "caps": lambda m, L: caps(m, "nmos", L, 0.9, 0.9, 0.0, 5e-6),
}


@pytest.mark.lut_realdata
@pytest.mark.parametrize("name", sorted(REAL_CALLS))
@pytest.mark.parametrize("L,reason", [
    # [r6] LUT v2 앵커 18개(CONTRACT 5절 r6 실측 bin 상태: .26 = 0.15·0.18, .25 = 0.185·0.2·0.25, .24 = 0.255~0.5,
    # .23 = 0.7·1, .22 = 1.5·2, .21 = 2.5·4, .20 = 8, .19 = 20). 옛 12-L 의 0.17 µm(unbracketed)는 v2 에서 .26 안 보간,
    # 1.2 µm 는 .22 에 앵커 2개(1.5·2)가 생겨 cross_bin. 앵커 1개 bin 사이는 5 µm(.20)·12 µm(.19).
    (0.6e-6, "lut_l_cross_bin"), (1.2e-6, "lut_l_cross_bin"),     # [WB-1] 0.182 µm 행 삭제: 격자 5 nm 에서 0.18·0.185 사이 점은 둘 중 앵커로 반올림된다(사이 격자점 없음)
    (5e-6, "lut_l_bin_unbracketed"), (12e-6, "lut_l_bin_unbracketed")])
def test_real_cross_bin_rejected_every_entry(real_memo, name, L, reason):
    with pytest.raises(SealViolationError) as ei:
        REAL_CALLS[name](real_memo, L)
    det = detail_of(ei.value)
    assert det["reason"] == reason and det["value"] == L
    assert det["kind"] == "nmos"
    if name == "caps":
        assert det["table"] == "cap"
    else:
        assert det["w_key"] == 1000


@pytest.mark.lut_realdata
@pytest.mark.parametrize("L", [0.3125e-6, 0.3875e-6, 0.45e-6, 0.22e-6, 0.85e-6, 3e-6, 0.17e-6, 1.75e-6])
def test_real_in_bin_values(real_memo, real_lut, raw_slice, raw_cap, L):
    z = raw_slice("nmos", 1000)
    op = op_point(real_memo, "nmos", 1000, L, 0.9, 0.9, 0.0)
    for f, v in expected_op(z, L, 0.9, 0.9, 0.0).items():
        assert rel_close(getattr(op, f), v, 1e-11), (L, f)
    assert rel_close(gmb(real_memo, "nmos", 1000, L, 0.9, 0.9, 0.3), exp_gmb(z, L, 0.9, 0.9, 0.3), 1e-10)
    c = gm_id_curve(real_memo, "nmos", 1000, L, 0.9, 0.0)
    V, S, ok, _, _ = exp_curve(z, L, 0.9, 0.0)
    fin = np.isfinite(S)
    assert np.allclose(np.asarray(c.id_vals), np.exp(V), rtol=1e-11, atol=0)
    assert np.allclose(np.asarray(c.gm_id_vals)[fin], S[fin], rtol=1e-11, atol=0)
    assert tuple(bool(x) for x in c.cell_ok) == ok
    assert check_root_in_bin(real_memo, 1000, z, L, 0.9, 0.0, 8.0) is not None
    cp = caps(real_memo, "nmos", L, 0.9, 0.9, 0.0, 5e-6)
    cap = {"L": raw_cap["L"], "VGS": raw_cap["VGS"], "VDS": raw_cap["VDS"], "VS": raw_cap["VS"],
           "CGG_n": raw_cap["CGG_n"], "CGD_n": raw_cap["CGD_n"], "w_ref_m": real_lut.cap_map["nmos"].w_ref_m}
    cgg, cgd = exp_caps(cap, L, 0.9, 0.9, 0.0, 5e-6)
    assert rel_close(cp.cgg, cgg, 1e-11) and rel_close(cp.cgd, cgd, 1e-11)


@pytest.mark.lut_realdata
def test_real_contract_gm_id_row(real_memo, raw_slice):
    """CONTRACT 4.0 실측: 0.35·0.425 µm 값 6.7234·6.5923(격자점 -- r4·r5 같은 저장값), 0.3875 µm 는 그 사이.
    [r5] 0.3875 µm 값은 r4 실측 6.6575(로그공간 다선형)가 아니라 4.2 정의(VGS 격자점이라 마디 기울기 S = 두 L 장 gm/ID 의
    선형 가중합) -- 기대값 = 독립 구현(RefSlice)."""
    g = [op_point(real_memo, "nmos", 1000, L, 0.9, 0.9, 0.0).gm_over_id for L in (0.35e-6, 0.3875e-6, 0.425e-6)]
    assert g[0] == pytest.approx(6.7234, abs=5e-5) and g[2] == pytest.approx(6.5923, abs=5e-5)
    assert g[2] < g[1] < g[0]
    exp = expected_op(raw_slice("nmos", 1000), 0.3875e-6, 0.9, 0.9, 0.0)["gm_over_id"]
    assert rel_close(g[1], exp, 1e-11)
