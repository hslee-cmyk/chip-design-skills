"""CONTRACT 3.14·예 5: area_search -- Σ W·L + Σ(값 × 단위 면적, 선언된 것만), 미선언 label 은 passive_area_undeclared(정렬)."""
import pytest

from gmid_engine.metrics import AreaSearch, GateArea, PassiveArea, area_search


def test_ex5_hand_value():
    a = area_search((GateArea(10e-6, 0.5e-6), GateArea(4e-6, 1e-6)),
                    (PassiveArea("cc", 0.5e-12, 5e2), PassiveArea("rz", 5e3, None)))
    assert isinstance(a, AreaSearch)
    assert a.gate_area_m2 == pytest.approx(9e-12, rel=1e-12)
    assert a.passive_area_m2 == pytest.approx(2.5e-10, rel=1e-12)
    assert a.area_search_m2 == pytest.approx(2.59e-10, rel=1e-12)
    assert tuple(a.passive_area_undeclared) == ("rz",)


def test_undeclared_sorted():
    a = area_search((), (PassiveArea("zeta", 1.0, None), PassiveArea("alpha", 1.0, None), PassiveArea("mid", 2.0, 1e-12)))
    assert tuple(a.passive_area_undeclared) == ("alpha", "zeta")
    assert a.area_search_m2 == pytest.approx(2e-12, rel=1e-12)


def test_empty_is_zero():
    a = area_search((), ())
    assert a.area_search_m2 == 0.0 and tuple(a.passive_area_undeclared) == ()


def test_order_independent():
    g = (GateArea(1e-6, 2e-7), GateArea(3e-6, 1e-7), GateArea(7e-6, 5e-7))
    p = (PassiveArea("a", 1e-12, 1e2), PassiveArea("b", 2e3, 1e-14))
    x = area_search(g, p)
    y = area_search(tuple(reversed(g)), tuple(reversed(p)))
    assert x.area_search_m2 == pytest.approx(y.area_search_m2, rel=1e-15)
    assert x.area_search_m2 == pytest.approx(1e-6 * 2e-7 + 3e-6 * 1e-7 + 7e-6 * 5e-7 + 1e-12 * 1e2 + 2e3 * 1e-14, rel=1e-12)
