"""`gm_id_for_target` -- CONTRACT 4.1 표 [r5]: Q = id_vals·W/w_m(current) 또는 id_vals·gm_id_vals·W/w_m(gm) -- 마디 값.
분지 index p 부터 마디 Q 가 엄격히 증가하는 첫 구간 [p, e] 에서 칸 j = p + max(searchsorted(Q[p..e], 목표, left) − 1, 0).
j = e 면 VGS[e], 아니면 칸 [j, j+1] 의 VGS Hermite 로 ln Q(vgs) = ln 목표(current: p(v) + ln(W/w_m), gm: p(v) + ln p'(v) + ln(W/w_m)).
gm_id = op_point(vgs).gm_over_id, id_a = IDu·W/L, gm_s = gm_id·id_a. 실패: 범위 밖 / 단조 구간 밖 / NaN 마디(lut_curve_undefined) /
칸 단조 위반(lut_hermite_nonmonotone_cell), 인자 오류 ValueError.
"""
import math

import numpy as np
import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.lut import TargetSolution, gm_id_for_target, op_point

from .conftest import R5_A, R5_B, RefSlice, anchor_w, detail_of, r5_toy_lnid, rel_close, target_ref


def _solve(m, **kw):
    return gm_id_for_target(m, "nmos", 100, 1e-6, 0.5, 0.0, **kw)


def _q_cur(v, W=2e-6):
    return (W / 1e-6) * math.exp(r5_toy_lnid(v, 0.5, 0.0))


def test_contract_toy_row(toy_memo):
    t = 2 * 1e-7 * math.exp(4.675)
    r = _solve(toy_memo, W=2e-6, current=t)
    assert isinstance(r, TargetSolution)
    assert rel_close(r.vgs, 0.25, 1e-12)
    assert rel_close(r.gm_id, 17.0, 1e-12)
    assert rel_close(r.id_a, 2.144651e-5, 1e-6) and rel_close(r.id_a, t, 1e-12)
    assert rel_close(r.gm_s, 3.645907e-4, 1e-6) and rel_close(r.gm_s, 17.0 * r.id_a, 1e-15)
    # gm 목표 3.645907e-4(= 17·id_a) 도 같은 vgs
    r2 = _solve(toy_memo, W=2e-6, gm=17.0 * t)
    assert rel_close(r2.vgs, 0.25, 1e-12) and rel_close(r2.gm_s, 17.0 * t, 1e-12)
    r3 = _solve(toy_memo, W=2e-6, gm=3.645907e-4)
    assert abs(r3.vgs - 0.25) < 1e-7


@pytest.mark.parametrize("v", [0.1, 0.4, 0.5, 0.8, 0.97])
def test_toy_current_hermite_exact(toy_memo, v):
    """r5 toy: ln Q 가 VGS 의 2차식이라 Hermite 가 정확 -> 목표 = Q(v) 면 vgs = v."""
    t = _q_cur(v)
    r = _solve(toy_memo, W=2e-6, current=t)
    assert abs(r.vgs - v) <= 1e-12
    assert rel_close(r.gm_id, R5_A - 2 * R5_B * v, 1e-11)
    assert rel_close(r.id_a, t, 1e-12)
    assert rel_close(r.gm_s, r.gm_id * r.id_a, 1e-15)


@pytest.mark.parametrize("v", [0.2, 0.5, 0.75])
def test_toy_gm_target(toy_memo, v):
    # gm: ln Q = p(v) + ln p'(v) + ln(W/w_m), p' = 20 − 12v (정확)
    t = _q_cur(v) * (R5_A - 2 * R5_B * v)
    r = _solve(toy_memo, W=2e-6, gm=t)
    assert abs(r.vgs - v) <= 1e-12
    assert rel_close(r.gm_s, t, 1e-12)


@pytest.mark.parametrize("kw,quantity", [
    (dict(W=2e-6, current=1.0), "current"),
    (dict(W=2e-6, current=1e-7), "current"),
    (dict(W=2e-6, gm=10.0), "gm"),
])
def test_out_of_range(toy_memo, kw, quantity):
    with pytest.raises(SealViolationError) as ei:
        _solve(toy_memo, **kw)
    det = detail_of(ei.value)
    assert det["reason"] == "lut_target_out_of_range"
    for key in ("quantity", "target", "W", "L", "vds", "vsb", "kind", "w_key", "branch_min", "branch_max",
                "monotone_lo", "monotone_hi"):
        assert key in det, key
    assert det["quantity"] == quantity
    if quantity == "current":
        assert rel_close(det["branch_min"], _q_cur(0.0), 1e-12) and rel_close(det["branch_max"], _q_cur(1.0), 1e-12)
        assert rel_close(det["branch_max"], 0.253, 2e-3)          # 계약 7.1: 마디 Q 최대 ≈ 0.253


@pytest.mark.parametrize("kw", [
    dict(W=1e-6),
    dict(W=1e-6, gm=1e-5, current=1e-6),
    dict(W=0.0, current=1e-6),
    dict(W=-1e-6, current=1e-6),
])
def test_bad_arguments_valueerror(toy_memo, kw):
    with pytest.raises(ValueError) as ei:
        _solve(toy_memo, **kw)
    assert not isinstance(ei.value, SealViolationError)


def test_non_monotonic_vs_out_of_range(curve_lut):
    # 정점 index 0, 칸 [0,1] 은 자료가 맞는 단조 칸(ln ID 차 7.5, 기울기 20·10, h 0.5 -> b1 = 7.5 ≥ 0),
    # 마디 Q(current, W = w) = (1e-7, 1e-7·e^7.5, 5e-8): 단조 구간 [0, 1], 분지 범위 [5e-8, 1e-7·e^7.5]
    vgs = (0.0, 0.5, 1.0)
    ids = (1e-7, 1e-7 * math.exp(7.5), 5e-8)
    memo, _ = curve_lut(vgs, ids, (20.0, 10.0, 4.0))
    with pytest.raises(SealViolationError) as ei:
        gm_id_for_target(memo, "nmos", 100, 1e-6, 0.5, 0.0, W=1e-6, current=7e-8)
    det = detail_of(ei.value)
    assert det["reason"] == "lut_target_non_monotonic"
    assert rel_close(det["monotone_lo"], 1e-7, 1e-12) and rel_close(det["monotone_hi"], ids[1], 1e-12)
    assert rel_close(det["branch_min"], 5e-8, 1e-12) and rel_close(det["branch_max"], ids[1], 1e-12)
    for t in (3e-8, 2e-4):
        with pytest.raises(SealViolationError) as ei:
            gm_id_for_target(memo, "nmos", 100, 1e-6, 0.5, 0.0, W=1e-6, current=t)
        assert detail_of(ei.value)["reason"] == "lut_target_out_of_range"
    # 단조 구간 안 목표는 칸 [0,1] Hermite 로 푼다: 목표 = 칸 중앙 Hermite 값 -> vgs 0.25
    lnmid = 0.5 * (math.log(1e-7) + math.log(ids[1])) + 0.5 * (20.0 - 10.0) / 8
    r = gm_id_for_target(memo, "nmos", 100, 1e-6, 0.5, 0.0, W=1e-6, current=math.exp(lnmid))
    assert abs(r.vgs - 0.25) <= 1e-12
    # 그 해의 gm/ID = Hermite 미분(t = ½): 1.5·δ/h − (m0 + m1)/4 = 1.5·7.5/0.5 − 7.5
    assert rel_close(r.gm_id, 1.5 * 7.5 / 0.5 - 7.5, 1e-11)


def test_r4_toy_nonmonotone_cell(r4toy_memo):
    """CONTRACT 7.2 행: 마디 Q = (2e-7, 2e-6, 2e-5), 칸 j = 0 위반 -> lut_hermite_nonmonotone_cell."""
    with pytest.raises(SealViolationError) as ei:
        gm_id_for_target(r4toy_memo, "nmos", 100, 1e-6, 0.5, 0.0, W=2e-6, current=2e-6)
    det = detail_of(ei.value)
    assert det["reason"] == "lut_hermite_nonmonotone_cell"
    assert det["axis"] == "VGS" and det["cell_lo"] == 0.0 and det["cell_hi"] == 0.5
    for key in ("quantity", "target", "W", "L", "vds", "vsb", "kind", "w_key"):
        assert key in det, key
    assert (det["quantity"], det["target"], det["W"], det["kind"], det["w_key"]) == ("current", 2e-6, 2e-6, "nmos", 100)
    # 단조 칸 [0.5, 1] 의 목표는 푼다 -- 독립 구현
    rs_V = np.log(np.array([2e-7, 2e-6, 2e-5]) / 2.0)
    st, v = target_ref((0.0, 0.5, 1.0), rs_V, (20.0, 10.0, 4.0), (False, True), 1e-6, 2e-6, "current", 6e-6)
    r = gm_id_for_target(r4toy_memo, "nmos", 100, 1e-6, 0.5, 0.0, W=2e-6, current=6e-6)
    assert st == "ok" and abs(r.vgs - v) <= 1e-12 and 0.5 < r.vgs < 1.0
    assert rel_close(r.id_a, 6e-6, 1e-12)


def test_curve_undefined(curve_lut):
    """[r5] NaN 마디(on_mask 거짓) -> lut_curve_undefined, n_undefined = NaN 마디 수."""
    memo, _ = curve_lut((0.0, 0.5, 1.0), (0.0, 1e-6, 1e-5), (20.0, 10.0, 4.0))
    with pytest.raises(SealViolationError) as ei:
        gm_id_for_target(memo, "nmos", 100, 1e-6, 0.5, 0.0, W=1e-6, current=3e-6)
    det = detail_of(ei.value)
    assert det["reason"] == "lut_curve_undefined" and det["n_undefined"] == 1
    for key in ("quantity", "target", "W", "L", "vds", "vsb", "kind", "w_key"):
        assert key in det, key


def test_root_memo_region(toy_memo):
    a = _solve(toy_memo, W=2e-6, current=2e-6)
    b = _solve(toy_memo, W=2e-6, current=2e-6)
    assert a is b
    st = dict(toy_memo.stats())["root"]
    assert st.misses == 1 and st.hits == 1


@pytest.mark.lut_realdata
@pytest.mark.parametrize("quantity", ["current", "gm"])
def test_real_round_trip(real_memo, raw_slice, quantity):
    """독립 Hermite 경로(target_ref)와 같은 vgs, op_point 와 같은 gm_id·id_a, 목표로 되돌아옴(왕복)."""
    rng = np.random.default_rng(21 if quantity == "current" else 22)
    for kind, wk in (("nmos", 1000), ("pmos", 84)):
        z = raw_slice(kind, wk)
        rs = RefSlice(z)
        w = rs.w_m
        VGS = rs.grids[1]
        done = 0
        while done < 8:
            iL, k, s = int(rng.integers(0, 12)), int(rng.integers(4, 49)), int(rng.integers(0, 10))
            if not rs.on[iL, :, k, s].all():
                continue
            L, vds, vsb = rs.grids[0][iL], rs.grids[2][k], rs.grids[3][s]
            V, S, ok = rs.curve(anchor_w(iL), vds, vsb)
            p = int(np.argmax(S))
            W = float(rng.uniform(0.5e-6, 20e-6))
            Q = np.exp(V) * W / w * (1.0 if quantity == "current" else S)
            e = p
            while e + 1 < len(Q) and Q[e + 1] > Q[e]:
                e += 1
            if e == p:
                continue
            j = int(rng.integers(p, e))
            t = math.exp(0.5 * (math.log(Q[j]) + math.log(Q[j + 1])))
            st, vgs_hand = target_ref(VGS, V, S, ok, w, W, quantity, t)
            r = gm_id_for_target(real_memo, kind, wk, L, vds, vsb, W=W, **{quantity: t})
            assert st == "ok"
            assert abs(r.vgs - vgs_hand) <= 1e-9, (kind, wk, iL, k, s, j)
            op = op_point(real_memo, kind, wk, L, r.vgs, vds, vsb)
            assert r.gm_id == op.gm_over_id
            assert rel_close(r.id_a, op.IDu * W / L, 1e-15)
            ref = rs.op(anchor_w(iL), L, r.vgs, vds, vsb)
            assert rel_close(r.gm_id, ref["gm_over_id"], 1e-9)
            got = r.id_a if quantity == "current" else r.gm_s
            assert rel_close(got, t, 1e-9), "왕복: 목표 %s 로 되돌아오지 않는다" % quantity
            done += 1
