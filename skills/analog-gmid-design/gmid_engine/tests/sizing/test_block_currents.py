"""`dc_currents(snapshot, theta_currents)` -- CONTRACT 5.2(r2): reads graph.dc_current_basis.

- 키 집합 ≠ free -> ValueError. 원소 전류 = Σ (num/den)·전류(원천)(유리수 합 뒤 float).
- [r2] MOS 전류 ≤ 0 -> ValueError(정의역 밖 θ 로 블록을 직접 부른 호출 계약 위반). 옛 SealViolationError 는 없다.
- writes dc_current(+ 가지치기 저항 0.0), dc_drop_current(= dc_current 중 resistors ∪ pruned).
θ 성분은 손으로 정한 원소 전류 전체(KCL 만족)에서 기저 free 만 골라 넘기고(conftest free_currents), 결과가 그 전체와 같은지 본다.
"""
from fractions import Fraction

import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.sizing import DC_KEY, dc_currents

from .conftest import block_row, build_ctx, mos, row_delta, run_of, topo, two


def two_src_circuit():
    """n 넷: I1·I2(고정) 가 들어오고 M1·M2 가 나간다 -> M1 + M2 = I1 + I2."""
    return topo("hand_two_src_cur",
                [mos("M1", "nmos", "n", "in", "gnd"), mos("M2", "nmos", "n", "b2", "gnd")],
                {"in": ("input", "x"), "n": ("output", "y")},
                sources=[two("I1", "current_source", "vdd", "n"), two("I2", "current_source", "vdd", "n")],
                bias=["b2"])                                                                 # b2: M2 gate 에만


@pytest.fixture
def ctx2(tmp_path, toy_access):
    return build_ctx(tmp_path, two_src_circuit(), toy_access, element_values=(("I1", 1e-5), ("I2", 2e-5)))[2]


def theta_for(ctx, targets):
    basis = ctx.base.value("graph", DC_KEY, "dc_current_basis")
    return tuple((k, targets[k]) for k in basis.free)


def test_free_is_one_of_the_mos(ctx2):
    basis = ctx2.base.value("graph", DC_KEY, "dc_current_basis")
    assert len(basis.free) == 1 and basis.free[0] in ("M1", "M2")


def test_currents_from_basis(ctx2):
    tg = {"I1": 1e-5, "I2": 2e-5, "M1": 2e-5, "M2": 1e-5}
    out = dc_currents(ctx2.base, theta_for(ctx2, tg), **run_of(ctx2))
    cur = dict(out.column("device", "dc_current"))
    assert set(cur) == set(tg)
    for k, v in tg.items():
        assert cur[k] == float(Fraction(v)) or abs(cur[k] - v) <= 1e-20
    assert dict(out.column("device", "dc_drop_current")) == {}          # 저항 없음


def test_rational_sum_then_float(ctx2):
    basis = ctx2.base.value("graph", DC_KEY, "dc_current_basis")
    (f,) = basis.free
    other = "M1" if f == "M2" else "M2"
    i = 3e-5 - 1e-6
    out = dc_currents(ctx2.base, ((f, i),), **run_of(ctx2))
    got = dict(out.column("device", "dc_current"))[other]
    assert got == float(Fraction(1e-5) + Fraction(2e-5) - Fraction(i))


def test_nonpositive_mos_current_value_error(ctx2):
    basis = ctx2.base.value("graph", DC_KEY, "dc_current_basis")
    (f,) = basis.free
    # 다른 MOS 음수 / 자기 0 / 자기 음수. (3e-5 는 float 1e-5 + 2e-5 − 3e-5 의 정확 유리수 합이 0 이 아니라 뺀다)
    for val in (4e-5, 3.0000001e-5, 0.0, -1e-6):
        with pytest.raises(ValueError) as ei:
            dc_currents(ctx2.base, ((f, val),), **run_of(ctx2))
        assert not isinstance(ei.value, SealViolationError)


def test_key_set_must_equal_free(ctx2):
    basis = ctx2.base.value("graph", DC_KEY, "dc_current_basis")
    (f,) = basis.free
    with pytest.raises(ValueError):
        dc_currents(ctx2.base, (), **run_of(ctx2))
    with pytest.raises(ValueError):
        dc_currents(ctx2.base, ((f, 1e-5), ("I1", 1e-5)), **run_of(ctx2))
    with pytest.raises(ValueError):
        dc_currents(ctx2.base, (("I1", 1e-5),), **run_of(ctx2))


def test_resistor_and_pruned_drop_currents(tmp_path, toy_access):
    doc = topo("hand_pruned_cur", [mos("M1", "nmos", "out", "in", "gnd")],
               {"in": ("input", "x"), "out": ("output", "y")},
               passives=[two("R1", "resistor", "vdd", "out"), two("R2", "resistor", "out", "leaf"),
                         two("C1", "capacitor", "out", "gnd")])
    ctx = build_ctx(tmp_path, doc, toy_access)[2]
    out = dc_currents(ctx.base, theta_for(ctx, {"M1": 2e-5, "R1": 2e-5}), **run_of(ctx))
    assert dict(out.column("device", "dc_current")) == {"M1": 2e-5, "R1": 2e-5, "R2": 0.0}
    assert dict(out.column("device", "dc_drop_current")) == {"R1": 2e-5, "R2": 0.0}
    for name in ("M1", "R1", "R2"):
        assert out.field("device", name, "dc_current").writer == "dc_currents"


def test_negative_resistor_current_allowed_when_mos_positive(tmp_path, toy_access):
    """R1 (out, vdd) 방향: M1 = −R1 -> R1 < 0 이어야 MOS 양수(저항 전류 부호는 제한 없음)."""
    doc = topo("hand_rev_cur", [mos("M1", "nmos", "out", "in", "gnd")],
               {"in": ("input", "x"), "out": ("output", "y")}, passives=[two("R1", "resistor", "out", "vdd")])
    ctx = build_ctx(tmp_path, doc, toy_access)[2]
    out = dc_currents(ctx.base, theta_for(ctx, {"M1": 2e-5, "R1": -2e-5}), **run_of(ctx))
    assert dict(out.column("device", "dc_current")) == {"M1": 2e-5, "R1": -2e-5}
    with pytest.raises(ValueError):
        dc_currents(ctx.base, theta_for(ctx, {"M1": -2e-5, "R1": 2e-5}), **run_of(ctx))


def test_reuse_same_input(ctx2):
    # oracle 대조: card B C4 판정 1(같은 lineage -> reuse, 블록 함수 0)·판정 4(compute) -- 실행 계수 C1 행의 이 test 구간 증분
    th = theta_for(ctx2, {"M1": 2e-5, "M2": 1e-5})
    before = block_row(ctx2.counters, "dc_currents")
    a = dc_currents(ctx2.base, th, **run_of(ctx2))
    b = dc_currents(a, th, **run_of(ctx2))
    assert b is a
    assert row_delta(block_row(ctx2.counters, "dc_currents"), before) == (2, 1, 0, 0, 1, 0)
