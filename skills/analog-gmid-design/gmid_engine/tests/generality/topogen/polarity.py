"""극성 뒤집기: nmos <-> pmos, 두 레일 넷을 서로 바꾼다(거울 회로). 다른 kind·이름·값은 그대로다.

레일이 정확히 2개인 doc 에만 정의된다(어느 레일이 '위'인지는 topology 에 없으므로 두 레일을 맞바꾼다).
두 번 적용하면 원래 doc 과 같다.
"""
from __future__ import annotations

from ._doc_walk import map_nets

KIND_SWAP = (("nmos", "pmos"), ("pmos", "nmos"))     # DEC-68 극성 어휘


def flip_polarity(doc):
    """(새 doc, 레일 치환표 {a: b, b: a})."""
    rails = list(doc["supply_nets"])
    if len(rails) != 2 or rails[0] == rails[1]:
        raise ValueError("flip_polarity 는 서로 다른 레일 2개인 doc 만: %r" % (rails,))
    swap = {rails[0]: rails[1], rails[1]: rails[0]}
    kinds = dict(KIND_SWAP)
    out = map_nets(doc, lambda n: swap.get(n, n))
    out["netlist"] = [dict(e, kind=kinds.get(e["kind"], e["kind"])) for e in out["netlist"]]
    return out, swap
