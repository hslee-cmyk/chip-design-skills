"""`_helpers_stamp.admittance_pair` (비공개) -- 공개 경로(two_terminal_stamps·mos_stamps 용량)로 확인한다.
2단자 어드미턴스 y 의 스탬프 = (a,a,y)(a,b,−y)(b,a,−y)(b,b,y): 대칭이고 행·열 합 0."""
from collections import defaultdict

import pytest

from gmid_engine.metrics import Capacitor, MosSmallSignal, Resistor, mos_stamps, two_terminal_stamps


def _acc(entries):
    out = defaultdict(float)
    for r, c, v in entries:
        out[(r, c)] += v
    return dict(out)


@pytest.mark.parametrize(
    "entries",
    [
        two_terminal_stamps(Resistor(4, 9, 330.0)).g,
        two_terminal_stamps(Capacitor(4, 9, 1e-13)).c,
        mos_stamps(MosSmallSignal(1, 2, 3, 4, 0.0, 0.0, 0.0, cgs=1e-15, cgd=2e-15, cgb=3e-15, cdb=4e-15, csb=5e-15)).c,
    ],
    ids=["resistor", "capacitor", "mos_caps"],
)
def test_pair_stamp_symmetric_zero_sum(entries):
    acc = _acc(entries)
    nodes = {r for r, _ in acc} | {c for _, c in acc}
    for (r, c), v in acc.items():
        assert acc.get((c, r)) == pytest.approx(v, rel=1e-15)
    for n in nodes:
        assert sum(v for (r, _), v in acc.items() if r == n) == pytest.approx(0.0, abs=1e-25)
        assert sum(v for (_, c), v in acc.items() if c == n) == pytest.approx(0.0, abs=1e-25)
    for n in nodes:
        assert acc[(n, n)] > 0.0


def test_pair_values_exact():
    y = 1.0 / 330.0
    acc = _acc(two_terminal_stamps(Resistor(4, 9, 330.0)).g)
    assert acc == {(4, 4): y, (4, 9): -y, (9, 4): -y, (9, 9): y}
