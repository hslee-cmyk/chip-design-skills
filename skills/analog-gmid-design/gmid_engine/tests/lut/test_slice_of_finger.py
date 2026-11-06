"""WB-1 F-2 -- `slice_of_finger` (interface card §2). 손 stub. oracle (손): 격자 g = 1e-8, 키 = 폭/g 정수."""
from types import SimpleNamespace

import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.lut import LBin, LBinMap, slice_of_finger

G = 1e-8


def make_lut(keys, ref_key=500):
    lb = LBinMap(model_files=(), w_bin=(1e-6, 5e-6), bins=(LBin("b", 5e-7, 3e-6),), anchor_bin=())
    return SimpleNamespace(
        spec=SimpleNamespace(manufacturing_grid_m=G, min_finger_w_m=(("nmos", 1e-6),)),
        slice_map={("nmos", k): SimpleNamespace(l_bins=lb) for k in keys},
        cap_map={"nmos": SimpleNamespace(w_key=ref_key)},
        bin_rule="lower")


def test_slice_of_finger_listed_keys():
    lut = make_lut({200, 500, 700})
    assert slice_of_finger(lut, "nmos", 1e-6, 5e-6) == 500
    assert slice_of_finger(lut, "nmos", 1e-6, 7e-6) == 700          # w_hi 위여도 키가 있으면 통과 (w_hi 안 씀)


@pytest.mark.parametrize("w", [4e-6, 5.000000001e-6])
def test_slice_of_finger_missing(w):
    lut = make_lut({200, 500, 700})
    assert slice_of_finger(lut, "nmos", 1e-6, 5e-6) == 500           # 호출 >= 1 (공허 방지)
    with pytest.raises(SealViolationError) as ei:
        slice_of_finger(lut, "nmos", 1e-6, w)                         # 4e-6 -> 키 400 없음, 두번째 = 격자 밖
    d = dict(ei.value.record.detail)
    assert d["reason"] == "slice_missing" and d["kind"] == "nmos" and d["w_f_m"] == w


def test_slice_of_finger_below_w_min_missing():
    lut = make_lut({50, 200, 500, 700})
    assert slice_of_finger(lut, "nmos", 1e-6, 2e-6) == 200
    with pytest.raises(SealViolationError) as ei:
        slice_of_finger(lut, "nmos", 1e-6, 5e-7)                      # 키 50 은 슬라이스지만 W_min(100) 밖
    assert dict(ei.value.record.detail)["reason"] == "slice_missing"
