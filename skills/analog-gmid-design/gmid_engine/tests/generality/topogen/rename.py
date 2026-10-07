"""이름 치환: topology_name·원소 이름·넷 이름을 mapping(없는 이름은 그대로)으로 바꾼다. 연결 구조는 그대로다."""
from __future__ import annotations

from ._doc_walk import map_element_names, map_nets


def rename(doc, mapping):
    """mapping 으로 이름을 바꾼 새 doc. 원소 이름과 넷 이름이 같은 문자열이면 둘 다 같은 새 이름이 된다."""
    def fn(name):
        return mapping.get(name, name)

    out = map_element_names(map_nets(doc, fn), fn)
    out["topology_name"] = fn(doc["topology_name"])
    return out
