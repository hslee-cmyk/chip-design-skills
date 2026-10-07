"""`_helpers_anchor` (l_anchor_index) -- CONTRACT 4.0 [r2]: L 은 L 축 격자의 앵커 이산 키. |L − a| ≤ ulp(a) 이면 앵커 a 값을 쓰고,
범위 안 비앵커 -> SealViolationError(lut_l_not_anchor, detail value·below·above + context), 범위 밖 -> lut_axis_out_of_range(axis "L").
L 방향 보간은 어떤 조회 경로에도 없다. 공개 조회 전부로 확인한다(TolVTable.at 은 test_tolerance).
"""
import math

import numpy as np
import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.lut import caps, gm_id_curve, gm_id_for_target, gmb, op_point, vgs_for_gm_id

from .conftest import detail_of, rel_close

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
    (1e-6 + 2 * ULP, 1e-6, 2e-6),             # 계약 7절: 2 ulp 는 실패
    (2.9e-6, 2e-6, 3e-6),
    (math.nextafter(3e-6, 0.0) - 2 * math.ulp(3e-6), 2e-6, 3e-6),
])
def test_non_anchor_rejected(toy_memo, name, L, below, above):
    with pytest.raises(SealViolationError) as ei:
        CALLS[name](toy_memo, L)
    det = detail_of(ei.value)
    assert det["reason"] == "lut_l_not_anchor"
    assert det["value"] == L and det["below"] == below and det["above"] == above
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
def test_real_non_anchor_rejected(real_memo, raw_slice):
    z = raw_slice("nmos", 1000)
    L = [float(x) for x in z["L"]]
    # [code author 조정 2026-10-07, 사용자 결정 'L 은 같은 모델 bin 안에서만 보간'] 옛 판정(실데이터 비앵커 전부
    # lut_l_not_anchor)은 r2 앵커 전용 규칙을 그대로 적은 것이라 폐기. 남긴 것: 거부되는 중점은 bin 사유 키와 양옆 앵커를
    # 싣는다. bin 별 기대(어느 중점이 보간되는지)는 CONTRACT 4.0 기준으로 test 작성자가 새로 쓴다.
    for i in range(len(L) - 1):
        mid = 0.5 * (L[i] + L[i + 1])
        try:
            op_point(real_memo, "nmos", 1000, mid, 0.9, 0.9, 0.0)
        except SealViolationError as e:
            det = detail_of(e)
            assert det["reason"] in ("lut_l_cross_bin", "lut_l_bin_unbracketed", "lut_l_outside_model_bins")
            assert det["below"] == L[i] and det["above"] == L[i + 1]


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
    L = a + sign * 2 * math.ulp(a)
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
        t.at(a + sign * 2 * math.ulp(a), 0.75, "gm_id_inverse")
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
            op_point(real_memo, "pmos", 1000, a + sign * 2 * math.ulp(a), 0.9, 0.9, 0.2)
        assert detail_of(ei.value)["reason"] == "lut_axis_out_of_range"
