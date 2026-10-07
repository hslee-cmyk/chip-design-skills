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
    # w_ref_m: 기준 LUT 에 w_ref_m 이 없어 slice_id_match -> 5 µm 슬라이스(test_lut_set 이 독립으로 확인)
    rng = np.random.default_rng(7)
    for kind, suf in (("nmos", "_n"), ("pmos", "_p")):
        w_ref = real_lut.cap_map[kind].w_ref_m
        assert rel_close(w_ref, 5e-6, 1e-9)
        for _ in range(20):
            iL, iG, k, s = (int(rng.integers(0, n)) for n in raw_cap["CGG" + suf].shape)
            pt = (float(raw_cap["L"][iL]), float(raw_cap["VGS"][iG]), float(raw_cap["VDS"][k]), float(raw_cap["VS"][s]))
            W = 2.5e-6
            c = caps(real_memo, kind, *pt, W)
            cgg = float(raw_cap["CGG" + suf][iL, iG, k, s]) * W / w_ref
            cgd = float(raw_cap["CGD" + suf][iL, iG, k, s]) * W / w_ref
            assert rel_close(c.cgg, cgg, 1e-12) and rel_close(c.cgd, cgd, 1e-12)
            assert c.model == "cgg_minus_cgd_at_gs" and c.cgb == 0.0
            assert rel_close(c.cgs, cgg - cgd, 1e-9)


@pytest.mark.lut_realdata
def test_real_cap_vs_axis_limit(real_memo):
    # 기준 LUT VS 축 0~0.8: vsb 0.9 는 용량 실패, DC 조회(슬라이스 VS 0~1.8)는 성공
    op_point(real_memo, "nmos", 1000, 1e-6, 0.9, 0.9, 0.9)
    with pytest.raises(SealViolationError) as ei:
        caps(real_memo, "nmos", 1e-6, 0.9, 0.9, 0.9, 1e-6)
    det = detail_of(ei.value)
    assert det["table"] == "cap" and det["axis"] == "VS" and det["hi"] == 0.8
