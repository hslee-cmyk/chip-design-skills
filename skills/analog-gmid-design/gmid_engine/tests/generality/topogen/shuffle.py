"""순서 섞기: 원소 목록·supply_nets·포트·JSON 키 순서를 섞는다. 이름·값·연결은 그대로다.

2단자 원소의 terminals 순서는 섞지 않는다 -- 계약상 문서 순서 그대로 투영된다(authoring CONTRACT 2절
"terminals = 문서의 두 넷 순서 그대로"), 즉 순서가 아니라 내용이다.
"""
from __future__ import annotations

import random

LIST_KEYS = ("netlist", "passive_elements", "ideal_sources", "supply_nets")


def _shuffled_dict(d, rng):
    items = list(d.items())
    rng.shuffle(items)
    return dict(items)


def shuffle_order(doc, seed):
    """seed 로 섞은 새 doc(입력은 바꾸지 않는다)."""
    rng = random.Random(seed)
    out = {}
    for key, value in doc.items():
        if key in LIST_KEYS and isinstance(value, list):
            value = [(_shuffled_dict(e, rng) if isinstance(e, dict) else e) for e in value]
            rng.shuffle(value)
        elif key == "ports" and isinstance(value, dict):
            value = _shuffled_dict({k: (_shuffled_dict(v, rng) if isinstance(v, dict) else v)
                                    for k, v in value.items()}, rng)
        out[key] = value
    return _shuffled_dict(out, rng)
