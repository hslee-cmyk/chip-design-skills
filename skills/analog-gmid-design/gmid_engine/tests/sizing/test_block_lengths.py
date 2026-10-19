"""`dc_lengths(snapshot, theta_lengths)` -- CONTRACT 5.3: reads device.element_class; 키 ≠ MOS 집합 -> ValueError;
writes dc_L (모든 MOS). [XRUN-F1 card B C4] 블록 호출은 ctx 의 실행 두 객체(run_of)로."""
import pytest

from gmid_engine.sizing import dc_lengths

from .conftest import run_of


def test_writes_all_mos(ctx_a):
    base = ctx_a[2].base
    out = dc_lengths(base, (("M1", 2e-6),), **run_of(ctx_a[2]))
    assert dict(out.column("device", "dc_L")) == {"M1": 2e-6}
    assert out.field("device", "M1", "dc_L").writer == "dc_lengths"


def test_two_mos(ctx_c):
    out = dc_lengths(ctx_c[2].base, (("M1", 1e-6), ("M2", 2e-6)), **run_of(ctx_c[2]))
    assert dict(out.column("device", "dc_L")) == {"M1": 1e-6, "M2": 2e-6}


@pytest.mark.parametrize("bad", [
    (),
    (("M1", 1e-6),),                              # M2 빠짐
    (("M1", 1e-6), ("M2", 2e-6), ("M3", 1e-6)),   # 남음
    (("M1", 1e-6), ("R1", 1e-6)),                 # MOS 아님
])
def test_key_set_must_equal_mos(ctx_c, bad):
    with pytest.raises(ValueError):
        dc_lengths(ctx_c[2].base, bad, **run_of(ctx_c[2]))


def test_resistor_not_a_length_key(ctx_a):
    with pytest.raises(ValueError):
        dc_lengths(ctx_a[2].base, (("M1", 1e-6), ("R1", 1e-6)), **run_of(ctx_a[2]))
