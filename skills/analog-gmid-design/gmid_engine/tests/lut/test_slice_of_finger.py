"""FS-1 §2 C-2·C-3 -- `slice_of_finger(lut, kind, w_f_m)` (L 인자 삭제, interface card 20261107-fs1 §2). 손 stub.
oracle (손): 격자 g = 1e-8, 키 = 폭/g 정수. 후보 = `widths(lut, kind)` (min finger 이상 키)."""
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
    assert slice_of_finger(lut, "nmos", 5e-6) == 500
    assert slice_of_finger(lut, "nmos", 7e-6) == 700          # 상한 없음: 키가 있으면 통과


def test_slice_of_finger_no_L_argument():
    """C-2: 서명에서 L 삭제 -- 옛 4인자 호출은 TypeError (양성 대조: 새 3인자는 통과)."""
    lut = make_lut({200, 500, 700})
    assert slice_of_finger(lut, "nmos", 2e-6) == 200
    with pytest.raises(TypeError):
        slice_of_finger(lut, "nmos", 1e-6, 5e-6)


@pytest.mark.parametrize("w", [4e-6, 5.000000001e-6])
def test_slice_of_finger_missing(w):
    """C-3: 키 없음 -> slice_missing, detail 키 = {reason, kind, w_f_m} (L 없음)."""
    lut = make_lut({200, 500, 700})
    assert slice_of_finger(lut, "nmos", 5e-6) == 500           # 호출 >= 1 (공허 방지)
    with pytest.raises(SealViolationError) as ei:
        slice_of_finger(lut, "nmos", w)                        # 4e-6 -> 키 400 없음, 두번째 = 격자 밖
    d = dict(ei.value.record.detail)
    assert d["reason"] == "slice_missing" and d["kind"] == "nmos" and d["w_f_m"] == w
    assert set(d) == {"reason", "kind", "w_f_m"}


def test_slice_of_finger_below_w_min_missing():
    lut = make_lut({50, 200, 500, 700})
    assert slice_of_finger(lut, "nmos", 2e-6) == 200
    with pytest.raises(SealViolationError) as ei:
        slice_of_finger(lut, "nmos", 5e-7)                      # 키 50 은 슬라이스지만 W_min(100) 밖
    assert dict(ei.value.record.detail)["reason"] == "slice_missing"
