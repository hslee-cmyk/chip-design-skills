from dataclasses import dataclass
from gmid_engine.valtypes import Pt


@dataclass(frozen=True)
class OnlyAllowed:
    v: float


BAD: Pt = None
BAD2 = Pt(1.0)
