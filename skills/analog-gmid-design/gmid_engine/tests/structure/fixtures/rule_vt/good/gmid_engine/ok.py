from dataclasses import dataclass
from gmid_engine.valtypes import Pt, Zed


def f(a: Pt) -> Pt:
    loc: Pt = a
    z = Pt(1.0)
    return z


@dataclass(frozen=True)
class Fz:
    p: Pt
    q: tuple[Zed, ...] = ()


N: int = 3
T = (1, 2.0, "a", None, True)
R = Pt
Z: tuple[int, ...] = ()


class Other:
    v: int = 3
