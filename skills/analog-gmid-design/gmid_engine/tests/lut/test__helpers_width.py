"""`_helpers_width` (width_key) -- CONTRACT 1.3·1.4 [r6], 공개 API 경유(`load_lut_set` 의 `CapTable.w_key`·`CapTable.l_bins`, `caps`).

- 폭 키 규칙 한 곳: 키 = round(W / grid), |W/grid − 키| ≤ 2·ulp(W/grid) 이면 격자 위(위·아래 대칭). 슬라이스 키와 기준 LUT 키가 같은 규칙.
- `CapTable.w_key` = width_key(w_ref_m, grid) 의 키(격자 밖이면 None).
- [r6 결함 수정] `CapTable.l_bins` = 그 kind 슬라이스 중 **w_key == CapTable.w_key** 인 것의 지도(r5 의 float `w_m == w_ref_m` 비교는
  LUT v2 의 w_ref_m 5e-06 대 슬라이스 W 4.9999999999999996e-06 에서 빈 지도 -> 비앵커 L 의 caps 가 lut_l_not_anchor).
- 기대값: conftest `width_key_ref`(1.3 규칙의 독립 구현), bin toy 손계산 bin 표(conftest 머리), 실데이터 npz 의 W·w_ref_m.
"""
import math

import numpy as np
import pytest

from gmid_engine.core import SchemaRejectedError, SealViolationError
from gmid_engine.lut import LBinMap, caps

from .conftest import (BIN_L, bin_cap_arrays, detail_of, interp4, new_memo, rel_close, width_key_ref)

GRID = 1e-8                                           # TOY_SPEC 의 제조 격자


def _bin_toy_with_wref(bin_toy_build, sub, w_ref):
    bt = bin_toy_build(sub)
    cap = bin_cap_arrays()
    cap["w_ref_m"] = np.float64(w_ref)
    np.savez(bt.build.cap, **cap)
    return bt.load()


def _w_below(W, n):
    for _ in range(n):
        W = float(np.nextafter(W, 0.0))
    return W


def _w_above(W, n):
    for _ in range(n):
        W = float(np.nextafter(W, 1.0))
    return W


# 기준 LUT w_ref_m 을 1e-6 에서 n ulp 씩 옮긴 값들 -- 기대 키는 width_key_ref(독립)로 정한다
W_CASES = [("below", n) for n in range(0, 7)] + [("above", n) for n in range(1, 7)]


def _w_case(direction, n):
    return _w_below(1e-6, n) if direction == "below" else _w_above(1e-6, n)


def test_w_cases_cover_both_sides_of_rule():
    """전제: 고른 값들이 2 ulp 규칙의 양쪽(격자 위·밖)을 모두 포함한다(판별력)."""
    res = [width_key_ref(_w_case(d, n), GRID)[1] for d, n in W_CASES]
    assert any(res) and not all(res)


@pytest.mark.parametrize("direction,n", W_CASES)
def test_cap_w_key_follows_width_rule(bin_toy_build, direction, n):
    w_ref = _w_case(direction, n)
    key, on = width_key_ref(w_ref, GRID)
    lut = _bin_toy_with_wref(bin_toy_build, "w%s%d" % (direction, n), w_ref)
    cap = lut.cap_map["nmos"]
    assert cap.w_ref_m == w_ref                                     # 기록값 그대로(basis recorded)
    if on:
        assert cap.w_key == key == 100
        # 폭 키 비교: float 가 달라도(w_m 1e-6 ≠ w_ref_m) 같은 키의 슬라이스 지도
        assert cap.l_bins == lut.slice_map[("nmos", 100)].l_bins
        assert cap.l_bins.bins != ()
    else:
        assert cap.w_key is None
        assert cap.l_bins == LBinMap((), None, (), ())


def test_cap_l_bins_by_key_not_float_equality(bin_toy_build):
    """결함 재현 모양: w_ref_m 이 슬라이스 W 와 float 로 다르고(1 ulp) 같은 키 -> 비앵커 L 의 caps 가 같은 bin 보간으로 성공.
    값 = 기준 LUT 두 장 선형 보간 × W / w_ref_m (독립 interp4)."""
    w_ref = _w_above(1e-6, 1)
    assert w_ref != 1e-6 and width_key_ref(w_ref, GRID) == (100, True)
    lut = _bin_toy_with_wref(bin_toy_build, "fix", w_ref)
    m = new_memo(lut)
    L = 1.25e-6                                                      # bin A [1, 2] 의 앵커 1·1.5 사이
    c = caps(m, "nmos", L, 0.25, 0.75, 0.1, 3e-6)
    z = bin_cap_arrays()
    lo, hi = 0, 1
    grids = ((BIN_L[lo], BIN_L[hi]), tuple(z["VGS"]), tuple(z["VDS"]), tuple(z["VS"]))
    exp = interp4(grids, z["CGG_n"][lo:hi + 1], (L, 0.25, 0.75, 0.1)) * 3e-6 / w_ref
    assert rel_close(c.cgg, exp, 1e-12)


def test_cap_l_bins_empty_when_no_slice_has_cap_key(bin_toy_build):
    """음성 대조: w_ref_m 1.5e-6 (키 150, 같은 키 슬라이스 없음) -> 빈 지도 -> 비앵커 L 의 caps 는 lut_l_not_anchor(bins unavailable).
    같은 L 앵커 조회는 된다."""
    lut = _bin_toy_with_wref(bin_toy_build, "nokey", 1.5e-6)
    cap = lut.cap_map["nmos"]
    assert cap.w_key == 150
    assert cap.l_bins == LBinMap((), None, (), ())
    m = new_memo(lut)
    caps(m, "nmos", 1.5e-6, 0.25, 0.75, 0.1, 3e-6)
    with pytest.raises(SealViolationError) as ei:
        caps(m, "nmos", 1.25e-6, 0.25, 0.75, 0.1, 3e-6)
    det = detail_of(ei.value)
    assert det["reason"] == "lut_l_not_anchor" and det["bins"] == "unavailable" and det["table"] == "cap"


def test_slice_key_uses_same_rule(toy_build):
    """슬라이스 W 도 같은 규칙: 격자 위로 판정되는 가장 먼 값은 로드, 그 다음 값은 lut_width_off_grid."""
    from .conftest import toy_slice_arrays
    last_on = None
    first_off = None
    for n in range(0, 8):
        W = _w_below(1e-6, n)
        if width_key_ref(W, GRID)[1]:
            last_on = W
        elif first_off is None:
            first_off = W
    assert last_on is not None and first_off is not None
    ok = toy_build("on", slices=[("a.npz", "toyn", toy_slice_arrays(last_on, 1.0)),
                                 ("b.npz", "toyn", toy_slice_arrays(2e-6, 2.0))]).load()
    assert ok.slice_map[("nmos", 100)].w_m == last_on
    with pytest.raises(SchemaRejectedError) as ei:
        toy_build("off", slices=[("a.npz", "toyn", toy_slice_arrays(first_off, 1.0)),
                                 ("b.npz", "toyn", toy_slice_arrays(2e-6, 2.0))]).load()
    assert detail_of(ei.value)["reason"] == "lut_width_off_grid"


@pytest.mark.lut_realdata
def test_real_v2_cap_key_and_bins(real_lut, raw_cap, raw_slice, real_spec):
    """LUT v2: 기록 w_ref_m 5e-06 과 슬라이스 W(npz) 가 float 로 다르고 키는 둘 다 1000 -> CapTable.l_bins = 슬라이스 지도(비어 있지 않음)."""
    grid = real_spec.manufacturing_grid_m
    w_ref = float(raw_cap["w_ref_m"])
    for kind in ("nmos", "pmos"):
        W = float(raw_slice(kind, 1000)["W"])
        assert W != w_ref                                             # 결함 전제(계약 1.4: 4.9999999999999996e-06 대 5e-06)
        assert width_key_ref(W, grid) == width_key_ref(w_ref, grid) == (1000, True)
        cap = real_lut.cap_map[kind]
        assert cap.w_key == 1000 and cap.w_ref_m == w_ref
        assert dict(cap.basis)["method"] == "recorded_w_ref_m"
        assert cap.l_bins == real_lut.slice_map[(kind, 1000)].l_bins and cap.l_bins.bins != ()


@pytest.mark.lut_realdata
def test_real_v2_caps_non_anchor_l_interpolates(real_memo, raw_cap):
    """결함 수정의 실데이터 확인: L 0.3875 µm(앵커 0.35·0.425, 같은 bin) 의 caps = 기준 LUT 두 장 선형 × W/w_ref_m (r5 는 lut_l_not_anchor)."""
    L = 0.3875e-6
    Lg = [float(x) for x in raw_cap["L"]]
    lo = Lg.index(0.35e-6) if 0.35e-6 in Lg else min(range(len(Lg)), key=lambda i: abs(Lg[i] - 0.35e-6))
    hi = lo + 1
    assert abs(Lg[hi] - 0.425e-6) <= math.ulp(0.425e-6)
    w_ref = float(raw_cap["w_ref_m"])
    pt = (L, 0.9, 0.9, 0.0)
    for kind, suf in (("nmos", "_n"), ("pmos", "_p")):
        c = caps(real_memo, kind, *pt, 2e-6)
        grids = ((Lg[lo], Lg[hi]), tuple(raw_cap["VGS"]), tuple(raw_cap["VDS"]), tuple(raw_cap["VS"]))
        for name, attr in (("CGG", "cgg"), ("CGD", "cgd"), ("CGS", "cgs"), ("CGB", "cgb")):
            exp = interp4(grids, raw_cap[name + suf][lo:hi + 1], pt) * 2e-6 / w_ref
            assert rel_close(getattr(c, attr), exp, 1e-12), (kind, name)
        assert c.model == "lut_cgs_cgb"
