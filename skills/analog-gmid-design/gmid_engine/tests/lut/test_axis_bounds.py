"""`lut_axis_bounds(memo, kind, w_key) -> ((축, 첫 값, 끝 값), ...)` -- interface card 20261104-eo1r4-sf1l §2 '축 끝 읽기'.

oracle (손): 합성 LUT 의 격자를 이 파일이 정해 npz 로 쓴다(conftest `write_r4_lut` 의 `grids`) -- 기대값은 그 격자 리터럴의 첫·끝 값이다.
축 순서 = lut `AXES` 순서(L, VGS, VDS, VS). 없는 슬라이스는 KeyError.
"""
import pytest

from gmid_engine.lut import LutMemo, lut_axis_bounds

from sizing.conftest import R4_GRIDS, W_KEY, write_r4_lut

AXES_ORDER = ("L", "VGS", "VDS", "VS")
CUSTOM = ((1e-6, 3e-6), (0.0, 0.25, 0.5), (0.125, 1.0), (-0.25, 0.0, 0.75))


def _memo(tmp_path, grids):
    lut = write_r4_lut(tmp_path / "lut", grids=grids)
    return LutMemo(lut, point=64, curve=64, root=64)


def test_axis_bounds_r4_grid_first_and_last_of_every_axis(tmp_path):
    memo = _memo(tmp_path, R4_GRIDS)
    # R4 격자(conftest 리터럴): L 1e-6..2e-6, VGS 0..2.0, VDS 0..2.0, VS -0.5..2.0
    want = (("L", 1e-6, 2e-6), ("VGS", 0.0, 2.0), ("VDS", 0.0, 2.0), ("VS", -0.5, 2.0))
    for kind in ("nmos", "pmos"):
        assert tuple(tuple(r) for r in lut_axis_bounds(memo, kind, W_KEY)) == want


def test_axis_bounds_custom_grid_distinguishes_axes(tmp_path):
    """서로 다른 첫·끝 값을 가진 격자라 축 순서를 바꾸거나 같은 축을 두 번 읽으면 틀린다."""
    memo = _memo(tmp_path, CUSTOM)
    got = tuple(tuple(r) for r in lut_axis_bounds(memo, "nmos", W_KEY))
    assert got == (("L", 1e-6, 3e-6), ("VGS", 0.0, 0.5), ("VDS", 0.125, 1.0), ("VS", -0.25, 0.75))
    assert tuple(r[0] for r in got) == AXES_ORDER


@pytest.mark.parametrize("kind,w_key", [("nmos", 7), ("pmos", 7), ("nmos", W_KEY + 1)])
def test_axis_bounds_missing_slice_is_key_error(tmp_path, kind, w_key):
    memo = _memo(tmp_path, R4_GRIDS)
    with pytest.raises(KeyError):
        lut_axis_bounds(memo, kind, w_key)
