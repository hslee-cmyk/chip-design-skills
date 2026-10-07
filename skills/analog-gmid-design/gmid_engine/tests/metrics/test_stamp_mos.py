"""CONTRACT 3.1: mos_stamps -- KCL 행 = 노드에서 나가는 전류. drain 행 (d,d,gds)(d,g,gm)(d,b,gmb)(d,s,−(gm+gmb+gds)),
source 행은 부호 반대, 용량 cgs·cgd·cgb·cdb·csb 는 2단자 4항목, 값 0 항목은 내지 않는다, 다른 형식은 TypeError."""
from collections import Counter, defaultdict

import pytest

from gmid_engine.metrics import Capacitor, MosSmallSignal, Resistor, StampSet, mos_stamps

D, G, S, B = 1, 2, 3, 4
GM, GMB, GDS = 1e-3, 2e-4, 1e-5
CAPS = dict(cgs=1e-15, cgd=2e-16, cgb=3e-17, cdb=4e-16, csb=5e-16)


def _acc(entries):
    out = defaultdict(float)
    for r, c, v in entries:
        out[(r, c)] += v
    return dict(out)


def _expected_g():
    tot = GM + GMB + GDS
    return [(D, D, GDS), (D, G, GM), (D, B, GMB), (D, S, -tot), (S, D, -GDS), (S, G, -GM), (S, B, -GMB), (S, S, tot)]


def _expected_c():
    out = defaultdict(float)
    for (a, b), c in (((G, S), CAPS["cgs"]), ((G, D), CAPS["cgd"]), ((G, B), CAPS["cgb"]),
                      ((D, B), CAPS["cdb"]), ((S, B), CAPS["csb"])):
        out[(a, a)] += c
        out[(b, b)] += c
        out[(a, b)] -= c
        out[(b, a)] -= c
    return dict(out)


def test_returns_stampset_of_triples():
    st = mos_stamps(MosSmallSignal(D, G, S, B, GM, GMB, GDS, **CAPS))
    assert isinstance(st, StampSet)
    for e in st.g + st.c:
        assert isinstance(e, tuple) and len(e) == 3


def test_g_entries_exact_contract():
    st = mos_stamps(MosSmallSignal(D, G, S, B, GM, GMB, GDS))
    got = sorted(((r, c), v) for r, c, v in st.g)
    exp = sorted(((r, c), v) for r, c, v in _expected_g())
    assert [k for k, _ in got] == [k for k, _ in exp]
    for (_, gv), (_, ev) in zip(got, exp):
        assert gv == pytest.approx(ev, rel=1e-15)
    assert st.c == ()


def test_g_rows_sum_to_zero_and_source_is_negated_drain():
    st = mos_stamps(MosSmallSignal(D, G, S, B, GM, GMB, GDS))
    acc = _acc(st.g)
    for row in (D, S):
        assert sum(v for (r, _), v in acc.items() if r == row) == pytest.approx(0.0, abs=1e-18)
    for col in (D, G, S, B):
        assert acc[(S, col)] == pytest.approx(-acc[(D, col)], rel=1e-15)


def test_capacitance_entries():
    st = mos_stamps(MosSmallSignal(D, G, S, B, GM, GMB, GDS, **CAPS))
    acc = _acc(st.c)
    exp = _expected_c()
    assert set(acc) == set(exp)
    for k in exp:
        assert acc[k] == pytest.approx(exp[k], rel=1e-15)


def test_zero_values_not_emitted():
    st = mos_stamps(MosSmallSignal(D, G, S, B, GM, 0.0, GDS, cgd=1e-16))
    assert all(v != 0.0 for _, _, v in st.g + st.c)
    assert all(c != B for _, c, _ in st.g)          # gmb = 0 -> (d,b)·(s,b) 항목 없음
    assert len(st.c) == 4                           # cgd 만 -> 2단자 4항목
    assert {(r, c) for r, c, _ in st.c} == {(G, G), (D, D), (G, D), (D, G)}


def test_all_zero_device_emits_nothing():
    st = mos_stamps(MosSmallSignal(D, G, S, B, 0.0, 0.0, 0.0))
    assert st.g == () and st.c == ()


def test_pmos_same_formula_positive_magnitudes():
    # NMOS·PMOS 같은 식: 단자만 바꿔 놓은 소자도 같은 규칙(source=레일 노드 7)
    st = mos_stamps(MosSmallSignal(5, 6, 7, 7, GM, GMB, GDS))
    acc = _acc(st.g)
    assert acc[(5, 5)] == pytest.approx(GDS)
    assert acc[(5, 6)] == pytest.approx(GM)
    assert acc[(5, 7)] == pytest.approx(GMB - (GM + GMB + GDS))   # (d,b)+(d,s), b = s
    assert acc[(7, 6)] == pytest.approx(-GM)


@pytest.mark.parametrize("bad", [Resistor(1, 2, 1e3), Capacitor(1, 2, 1e-12), (1, 2, 3), None])
def test_other_type_rejected(bad):
    with pytest.raises(TypeError):
        mos_stamps(bad)


def test_multiset_has_no_duplicate_g_entries_for_distinct_nodes():
    st = mos_stamps(MosSmallSignal(D, G, S, B, GM, GMB, GDS))
    assert max(Counter((r, c) for r, c, _ in st.g).values()) == 1
