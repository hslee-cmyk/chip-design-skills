from typing import Optional
import gmid_engine.valtypes as mod
from gmid_engine.valtypes import Pt, Zed, Holder, Loose, Named, NotFrozen


A: Pt = None
B: tuple[Pt, ...] = ()
C: dict[str, Zed] = {}
D: Optional[Holder] = None
E: "Pt" = None
F: mod.Pt = None
G: int = 3
H: Loose = None
I: Named = None
J: tuple[int, ...] = ()
K: Pt = Pt(1.0)
L: tuple[Zed, Pt, Holder] = ()
M: NotFrozen = None
