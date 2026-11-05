"""CONTRACT 3.1: two_terminal_stamps -- 저항 = 1/R 의 2단자 4항목(g), 커패시터 = C 의 4항목(c), 다른 형식은 TypeError."""
import pytest

from gmid_engine.metrics import Capacitor, MosSmallSignal, Resistor, StampSet, two_terminal_stamps


def test_resistor_four_entries():
    st = two_terminal_stamps(Resistor(1, 2, 1e3))
    assert isinstance(st, StampSet)
    assert st.c == ()
    g = 1.0 / 1e3
    assert sorted(st.g) == sorted([(1, 1, g), (1, 2, -g), (2, 1, -g), (2, 2, g)])


def test_capacitor_four_entries():
    st = two_terminal_stamps(Capacitor(3, 0, 2e-12))
    assert st.g == ()
    c = 2e-12
    assert sorted(st.c) == sorted([(3, 3, c), (3, 0, -c), (0, 3, -c), (0, 0, c)])


def test_large_node_numbers():
    st = two_terminal_stamps(Resistor(1000, 7, 50.0))
    assert {(r, c) for r, c, _ in st.g} == {(1000, 1000), (1000, 7), (7, 1000), (7, 7)}


@pytest.mark.parametrize("bad", [MosSmallSignal(2, 1, 0, 0, 1e-3, 0.0, 1e-5), (1, 2, 1e3), "R", None])
def test_other_type_rejected(bad):
    with pytest.raises(TypeError):
        two_terminal_stamps(bad)


def test_it2c_g_ops_resistor_one_per_net_and_capacitor_empty():
    """oracle 대조: (손) [IT-2c T-L10 `g_ops`] interface: 저항 g_ops = 넷 각 1(1/R 나눗셈 한 번), 용량은 g 가 비어 g_ops 도 빈 값."""
    st = two_terminal_stamps(Resistor(1, 2, 1e3))
    assert len(st.g_ops) == len(st.g) == 4 and set(st.g_ops) == {1} and st.g_ops == (1, 1, 1, 1)
    cs = two_terminal_stamps(Capacitor(3, 0, 2e-12))
    assert cs.g == () and cs.g_ops == ()
