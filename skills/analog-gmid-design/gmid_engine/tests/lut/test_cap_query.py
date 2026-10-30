"""`caps` -- CONTRACT 4절: 기준 LUT 열 선형 보간 × W / w_ref_m, CGS·CGB 열 유무로 model 결정, 축은 기준 LUT 축."""
import numpy as np
import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.lut import Caps, caps, op_point

from .conftest import (TOY_L, TOY_VDS, TOY_VGS, TOY_VS, detail_of, interp4, new_memo, rel_close,
                       toy_cap_arrays)


def test_contract_toy_row(toy_memo):
    c = caps(toy_memo, "nmos", 1e-6, 0.5, 0.5, 0.0, 3e-6)
    assert isinstance(c, Caps)
    assert rel_close(c.cgg, 3e-15, 1e-12)
    assert rel_close(c.cgd, 6e-16, 1e-12)
    assert rel_close(c.cgs, 2.4e-15, 1e-12)
    assert c.cgb == 0.0
    assert c.model == "cgg_minus_cgd_at_gs"


def test_lut_cgs_cgb_model_when_columns_present(toy_build):
    cap = toy_cap_arrays()
    cap["CGS_n"] = np.full((3, 3, 2, 2), 5e-16)
    cap["CGB_n"] = np.full((3, 3, 2, 2), 1e-16)
    m = new_memo(toy_build(cap=cap).load())
    c = caps(m, "nmos", 2e-6, 0.3, 0.7, 0.1, 2e-6)       # L 앵커
    assert c.model == "lut_cgs_cgb"
    assert rel_close(c.cgs, 1e-15, 1e-12)
    assert rel_close(c.cgb, 2e-16, 1e-12)
    assert rel_close(c.cgg, 2e-15, 1e-12)


def test_linear_not_log_interpolation(toy_build):
    cap = toy_cap_arrays()
    cgg = np.empty((3, 3, 2, 2))
    cgg[...] = np.asarray((1e-15, 2e-15, 4e-15))[None, :, None, None]
    cap["CGG_n"] = cgg
    m = new_memo(toy_build(cap=cap).load())
    pt = (3e-6, 0.25, 0.6, 0.3)
    c = caps(m, "nmos", *pt, 1e-6)
    hand = 1.5e-15                                               # 선형: (1+2)/2, 로그면 √2
    assert rel_close(c.cgg, hand, 1e-12)
    assert rel_close(c.cgg, interp4((TOY_L, TOY_VGS, TOY_VDS, TOY_VS), cgg, pt), 1e-12)
    assert rel_close(c.cgs, hand - 2e-16, 1e-12)


def test_out_of_range_uses_cap_table_detail(toy_memo):
    with pytest.raises(SealViolationError) as ei:
        caps(toy_memo, "nmos", 1e-6, 0.5, 0.5, 0.6, 1e-6)
    det = detail_of(ei.value)
    assert det["reason"] == "lut_axis_out_of_range"
    assert det["axis"] == "VS" and det["table"] == "cap" and det["kind"] == "nmos"
    assert "w_key" not in det


def test_unknown_kind_keyerror(toy_memo):
    with pytest.raises(KeyError):
        caps(toy_memo, "pmos", 1e-6, 0.5, 0.5, 0.0, 1e-6)


@pytest.mark.lut_realdata
def test_real_grid_points_match_npz(real_memo, real_lut, raw_cap):
    """[r6] LUT v2: 기준 LUT 에 w_ref_m(5e-06) 기록 -> 그 값, CGS·CGB·CDD·CSS 열 -> model "lut_cgs_cgb", 값은 저장 부호 그대로 × W/w_ref_m."""
    rng = np.random.default_rng(7)
    w_rec = float(raw_cap["w_ref_m"])
    for kind, suf in (("nmos", "_n"), ("pmos", "_p")):
        w_ref = real_lut.cap_map[kind].w_ref_m
        assert w_ref == w_rec
        for _ in range(20):
            iL, iG, k, s = (int(rng.integers(0, n)) for n in raw_cap["CGG" + suf].shape)
            pt = (float(raw_cap["L"][iL]), float(raw_cap["VGS"][iG]), float(raw_cap["VDS"][k]), float(raw_cap["VS"][s]))
            W = 2.5e-6
            c = caps(real_memo, kind, *pt, W)
            assert c.model == "lut_cgs_cgb"
            for attr, col in (("cgg", "CGG"), ("cgd", "CGD"), ("cgs", "CGS"), ("cgb", "CGB"), ("cdd", "CDD"), ("css", "CSS")):
                exp = float(raw_cap[col + suf][iL, iG, k, s]) * W / w_ref
                assert rel_close(getattr(c, attr), exp, 1e-12) or getattr(c, attr) == exp == 0.0, (kind, attr)


@pytest.mark.lut_realdata
@pytest.mark.parametrize("kind,suf,col", [("nmos", "_n", "CGB"), ("pmos", "_p", "CGB"), ("pmos", "_p", "CSS"),
                                          ("pmos", "_p", "CGD"), ("nmos", "_n", "CGS")])
def test_real_signed_caps_pass_through(real_memo, real_lut, raw_cap, kind, suf, col):
    """[r6] 1.2·4.1 caps: 용량은 부호 보존(CGB·CGS·CSS·CGD(pfet) 에 음수 점) -- 엔진은 로그·절댓값을 쓰지 않는다.
    저장값이 음수인 격자점에서 caps 의 그 필드 = 음수 저장값 × W/w_ref_m (npz 직접)."""
    arr = raw_cap[col + suf]
    neg = np.argwhere(arr < 0)
    assert len(neg) > 0, "전제: 음수 점이 있어야 한다(계약 1.2)"
    w_ref = real_lut.cap_map[kind].w_ref_m
    attr = col.lower()
    for idx in (neg[0], neg[len(neg) // 2], neg[-1]):
        iL, iG, k, s = (int(x) for x in idx)
        pt = (float(raw_cap["L"][iL]), float(raw_cap["VGS"][iG]), float(raw_cap["VDS"][k]), float(raw_cap["VS"][s]))
        c = caps(real_memo, kind, *pt, 3e-6)
        exp = float(arr[iL, iG, k, s]) * 3e-6 / w_ref
        assert exp < 0 and getattr(c, attr) < 0
        assert rel_close(getattr(c, attr), exp, 1e-12), (kind, col, idx)


@pytest.mark.lut_realdata
def test_real_cap_vs_axis_limit(real_memo, raw_cap):
    """[r6] LUT v2 기준 LUT VS 축 0~1.8: vsb 0.9 는 용량도 성공, 1.8 초과는 용량·DC 모두 축 밖."""
    assert float(raw_cap["VS"][-1]) == 1.8
    caps(real_memo, "nmos", 1e-6, 0.9, 0.9, 0.9, 1e-6)
    hi = float(np.nextafter(1.8, 2.0))
    with pytest.raises(SealViolationError) as ei:
        caps(real_memo, "nmos", 1e-6, 0.9, 0.9, hi, 1e-6)
    det = detail_of(ei.value)
    assert det["table"] == "cap" and det["axis"] == "VS" and det["hi"] == 1.8
    with pytest.raises(SealViolationError):
        op_point(real_memo, "nmos", 1000, 1e-6, 0.9, 0.9, hi)


# ---------------------------------------------------------------------------
# [r6] cdd·css 필드, 부호 보존 (toy)
# ---------------------------------------------------------------------------

def test_contract_toy_r6_cdd_css_none(toy_memo):
    """7.1 r6 표: r5 toy(CDD·CSS 없음) -> r5 값 + cdd None, css None."""
    c = caps(toy_memo, "nmos", 1e-6, 0.5, 0.5, 0.0, 3e-6)
    assert c.cdd is None and c.css is None
    assert rel_close(c.cgg, 3e-15, 1e-12) and c.model == "cgg_minus_cgd_at_gs"


def test_cdd_css_interpolated_and_negative_passthrough(toy_build):
    """CDD·CSS 열 = 같은 선형 보간 × W/w_ref_m. 음수 저장값(CGB·CSS)은 부호 그대로 -- 로그 공간이면 정의 불가,
    절댓값이면 부호가 바뀐다(판별)."""
    cap = toy_cap_arrays()
    shp = (3, 3, 2, 2)
    cgb = np.empty(shp)
    cgb[...] = np.asarray((-1e-16, -3e-16, 2e-16))[None, :, None, None]
    css = np.empty(shp)
    css[...] = np.asarray((-4e-16, -2e-16))[None, None, None, :]
    cap.update({"CGS_n": np.full(shp, 5e-16), "CGB_n": cgb, "CDD_n": np.full(shp, 7e-16), "CSS_n": css})
    m = new_memo(toy_build("signed", cap=cap).load())
    pt = (2e-6, 0.25, 0.7, 0.25)
    c = caps(m, "nmos", *pt, 2e-6)
    grids = (TOY_L, TOY_VGS, TOY_VDS, TOY_VS)
    assert c.model == "lut_cgs_cgb"
    assert rel_close(c.cgb, interp4(grids, cgb, pt) * 2.0, 1e-12) and rel_close(c.cgb, -4e-16, 1e-12)
    assert rel_close(c.css, interp4(grids, css, pt) * 2.0, 1e-12) and rel_close(c.css, -6e-16, 1e-12)
    assert rel_close(c.cdd, 1.4e-15, 1e-12)
    # 격자점: 음수 저장값 그대로
    c0 = caps(m, "nmos", 1e-6, 0.0, 0.5, 0.0, 1e-6)
    assert c0.cgb == -1e-16 and c0.css == -4e-16


def test_cdd_without_css(toy_build):
    cap = toy_cap_arrays()
    cap["CDD_n"] = np.full((3, 3, 2, 2), 7e-16)
    c = caps(new_memo(toy_build("cddonly", cap=cap).load()), "nmos", 1e-6, 0.5, 0.5, 0.0, 1e-6)
    assert rel_close(c.cdd, 7e-16, 1e-12) and c.css is None
