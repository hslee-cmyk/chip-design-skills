from dataclasses import dataclass
from gmid_engine.valtypes import Pt, Zed


@dataclass
class Loose2:
    a: Pt
    b: tuple[Zed, ...] = ()
    c = Pt(1.0)
    d: int = 3

    def m(self, x):
        self.p: Pt = x
        self.q = Pt(1.0)
        self.r = [Zed(1.0)]
        self.s = 3
        t: Pt = x
        u = Pt(1.0)
        return u


class Plain:
    v: Zed
    w = (Pt(1.0), Pt(2.0))

    def n(self):
        return Pt(1.0)


def func(a: Pt, b: tuple[Zed, ...]) -> Pt:
    loc: Pt = a
    z = Pt(1.0)
    return z
