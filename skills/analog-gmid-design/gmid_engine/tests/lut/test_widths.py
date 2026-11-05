"""`widths` -- CONTRACT 1.6: kind 슬라이스 폭 키 중 w_key·grid ≥ min_finger_w_m[kind] 인 것의 오름차순,
근접 폭 대체·보간 없음. min_finger_w_m 에 kind 없음 -> KeyError, 슬라이스 없는 kind -> ().
"""
import pytest

from gmid_engine.lut import LutSpec, widths

from .conftest import standard_toy_slices, toy_slice_arrays


def test_contract_toy(toy):
    assert widths(toy, "nmos") == (200,)


# [WB-1 §1 widths] w_key >= round(w_min / grid) 정수 비교(oracle (식)): 1.0000001e-6 / 1e-8 = 100.00001 -> 100 -> 키 100 포함,
# 2.0000001e-6 / 1e-8 = 200.00001 -> 200 -> 키 200 포함. (옛 float 비교 기대 (200,)·() 는 반올림 규칙과 충돌 -- 격자 밖 1e-13 m 은 격자 정수를 못 바꾼다)
@pytest.mark.parametrize("min_w,expect", [(1e-6, (100, 200)), (0.5e-6, (100, 200)), (1.0000001e-6, (100, 200)),
                                          (2e-6, (200,)), (2.0000001e-6, (200,))])
def test_threshold_inclusive(toy_build, min_w, expect):
    spec = LutSpec(1e-8, (("nmos", min_w),), (("toyn", "nmos"),), (("nmos", "_n"),))
    assert widths(toy_build().load(spec), "nmos") == expect


def test_sorted_ascending(toy_build):
    sl = standard_toy_slices() + [("toy_w150.npz", "toyn", toy_slice_arrays(1.5e-6, 1.5))]
    sl = [sl[1], sl[2], sl[0]]
    spec = LutSpec(1e-8, (("nmos", 1e-6),), (("toyn", "nmos"),), (("nmos", "_n"),))
    assert widths(toy_build(slices=sl).load(spec), "nmos") == (100, 150, 200)


def test_kind_without_min_finger_keyerror(toy):
    with pytest.raises(KeyError):
        widths(toy, "pmos")


def test_kind_without_slices_is_empty(toy_build):
    spec = LutSpec(1e-8, (("nmos", 1.5e-6), ("pmos", 1e-6)), (("toyn", "nmos"),), (("nmos", "_n"),))
    lut = toy_build().load(spec)
    assert widths(lut, "pmos") == ()


@pytest.mark.lut_realdata
def test_real_widths(real_lut, real_slice_files, real_spec, real_paths):
    grid = real_spec.manufacturing_grid_m
    mins = dict(real_spec.min_finger_w_m)
    for kind in ("nmos", "pmos"):
        exp = tuple(sorted(wk for k, _, _, wk, _ in real_slice_files if k == kind and wk * grid >= mins[kind]))
        assert widths(real_lut, kind) == exp
        assert len(exp) == {"nmos": 20, "pmos": 12}[kind]     # LUT v2 도 같은 폭 집합(슬라이스 32개)
    # 하한을 0.6 µm 로 올리면 그 미만 폭이 빠진다(대체 없음)
    spec = LutSpec(grid, (("nmos", 0.6e-6), ("pmos", 0.6e-6)), real_spec.device_kinds, real_spec.cap_column_suffix)
    from .conftest import load_real
    lut2 = load_real(real_paths, spec)                     # [r6] 1.8 '쓰는 법'(pdk_root·verify_midpoints)
    assert widths(lut2, "nmos")[0] == 120 and 116 not in widths(lut2, "nmos")
    assert widths(lut2, "pmos")[0] == 128
