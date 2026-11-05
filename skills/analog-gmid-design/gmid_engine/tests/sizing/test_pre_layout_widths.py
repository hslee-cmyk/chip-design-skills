"""`pre_layout_lut_access(memo) -> LutAccess` -- CONTRACT 1.3 [r2]: kind 마다 w_key = round(cap_map[kind].w_ref_m / grid),
kind 는 cap_map 키 정렬, 그 슬라이스가 slice_map 에 없으면 ValueError.
기대값: toy LUT 을 쓸 때 정한 w_ref_m(npz 기록값)과 grid 로 손계산."""
import pytest

from gmid_engine.core import fp_of
from gmid_engine.lut import LutMemo, load_lut_set
from gmid_engine.sizing import LutAccess, build_kernel_context, pre_layout_lut_access

from .conftest import GRID_M, TOY_SPEC, bin_rule_of, build_ctx, circuit_cs_pmos_load, write_toy_lut


def _memo(root, **kw):
    m, c = write_toy_lut(root, **kw)
    return LutMemo(load_lut_set(str(m), str(c), TOY_SPEC, bin_rule=bin_rule_of(m)), point=64, curve=64, root=64)


def test_toy_w_ref_gives_w_key_100(tmp_path):
    memo = _memo(tmp_path / "a")
    acc = pre_layout_lut_access(memo)
    assert isinstance(acc, LutAccess)
    assert acc.memo is memo
    assert acc.w_keys == (("nmos", 100), ("pmos", 100))           # round(1e-6 / 1e-8)


def test_w_ref_picks_matching_slice_among_two(tmp_path):
    memo = _memo(tmp_path / "b", w_ref_m=2e-6, extra_width=2e-6)
    assert set(memo.lut.slice_map) == {("nmos", 100), ("nmos", 200), ("pmos", 100), ("pmos", 200)}
    assert pre_layout_lut_access(memo).w_keys == (("nmos", 200), ("pmos", 200))
    assert round(2e-6 / GRID_M) == 200


def test_missing_slice_value_error(tmp_path):
    memo = _memo(tmp_path / "c", w_ref_m=2e-6)                      # 폭 2e-6 슬라이스 없음
    with pytest.raises(ValueError):
        pre_layout_lut_access(memo)


def test_fp_follows_lut_and_w_keys(tmp_path):
    a = pre_layout_lut_access(_memo(tmp_path / "d"))
    b = LutAccess(a.memo, (("nmos", 100), ("pmos", 100)))
    assert fp_of(a) == fp_of(b)


def test_usable_for_kernel_context(tmp_path):
    acc = pre_layout_lut_access(_memo(tmp_path / "e"))
    _, _, ctx = build_ctx(tmp_path, circuit_cs_pmos_load(), acc)
    assert ctx.lut is acc
