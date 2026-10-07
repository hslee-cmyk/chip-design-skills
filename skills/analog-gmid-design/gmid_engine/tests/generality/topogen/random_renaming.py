"""무작위 이름 치환표: doc 의 모든 원소·넷 이름과 topology_name 을 서로 다른 무작위 이름으로 보내는 전단사.

새 이름은 글자로 시작하고(`_` 로 시작하면 포트 키가 주석이 된다) 소문자·숫자·`_`·`-`·`.` 로 이루어지며 길이도
무작위다. 소문자만 쓰므로 서로 다른 새 이름은 casefold 도 서로 다르다(이름 유일성 IC3 의 대소문자 충돌을 만들지 않는다).
새 이름은 옛 이름과도 겹치지 않는다(치환 도중 충돌 없음).
"""
from __future__ import annotations

import random
import string

from ._doc_walk import collect_names

_FIRST = string.ascii_lowercase
_REST = string.ascii_lowercase + string.digits + "_-."


def random_renaming(doc, seed):
    """{옛 이름: 새 이름}. 같은 seed·같은 doc 이면 같은 표(결정론)."""
    rng = random.Random(seed)
    elements, nets = collect_names(doc)
    old = sorted(elements | nets | {doc["topology_name"]})
    taken = {x.casefold() for x in old}
    mapping = {}
    for name in old:
        while True:
            new = rng.choice(_FIRST) + "".join(rng.choice(_REST) for _ in range(rng.randint(2, 11)))
            if new.casefold() not in taken:
                break
        taken.add(new.casefold())
        mapping[name] = new
    return mapping
