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
    (1e-6, (1e-6 + ULP,)),                                                   # 계약 7절 (첫 앵커: 위쪽만 -- 아래는 축 밖)
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
    assert rel_close(op.IDu, 1e-6 * 1e-6 / 1e-6, 1e-12)
    r = gm_id_for_target(toy_memo, "nmos", 100, L, 0.5, 0.0, W=2e-6, current=2e-6)
    assert rel_close(r.id_a, 2e-6, 1e-12)


def test_point_memo_key_shared_within_ulp(toy_memo):
    a = op_point(toy_memo, "nmos", 100, 2e-6, 0.3, 0.6, 0.2)
    b = op_point(toy_memo, "nmos", 100, math.nextafter(2e-6, 1.0), 0.3, 0.6, 0.2)
    assert a is b
    st = dict(toy_memo.stats())["point"]
    assert st.misses == 1 and st.hits == 1


def test_no_l_interpolation_anywhere(toy_memo):
    """앵커 위 값은 그 앵커 한 장만으로 정해진다: L=2e-6 의 IDu 는 이웃 앵커 값과 무관(손계산 ID·L/w = (1/2)·1e-6·2)."""
    op = op_point(toy_memo, "nmos", 100, 2e-6, 0.5, 0.5, 0.0)
    assert rel_close(op.IDu, 0.5 * 1e-6 * 2e-6 / 1e-6, 1e-12)


@pytest.mark.lut_realdata
def test_real_non_anchor_rejected(real_memo, raw_slice):
    z = raw_slice("nmos", 1000)
    L = [float(x) for x in z["L"]]
    for i in range(len(L) - 1):
        mid = 0.5 * (L[i] + L[i + 1])
        with pytest.raises(SealViolationError) as ei:
            op_point(real_memo, "nmos", 1000, mid, 0.9, 0.9, 0.0)
        det = detail_of(ei.value)
        assert det["reason"] == "lut_l_not_anchor" and det["below"] == L[i] and det["above"] == L[i + 1]
