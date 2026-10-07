"""단 복제: 회로 전체를 한 벌 더 만들어 직렬로 잇는다(앞 단 출력 -> 뒷 단 입력).

- 뒷 단 원소 이름·넷 이름 = 원래 이름 + suffix. 레일(supply_nets)은 두 단이 공유한다.
- 앞 단의 출력 포트 넷(정확히 1개여야 함)이 뒷 단의 첫 입력 포트 넷(이름순 첫째) 자리에 들어간다.
- 포트: 앞 단 포트 중 출력 포트를 뺀 것 + 뒷 단 포트 중 이어진 입력 포트를 뺀 것(나머지 입력은 그대로 입력).
- topology_name 은 그대로, 그 밖 최상위 키는 앞 단 것을 쓴다.
"""
from __future__ import annotations

from ._doc_walk import COMMENT_PREFIX, ELEMENT_LISTS, map_element_names, map_nets


def _ports_by(doc, direction):
    return sorted(k for k, v in doc["ports"].items()
                  if not k.startswith(COMMENT_PREFIX) and isinstance(v, dict) and v.get("direction") == direction)


def duplicate_stage(doc, suffix):
    """(새 doc, 이어진 넷). suffix 는 비어 있지 않아야 한다."""
    if not suffix:
        raise ValueError("suffix 가 비었다")
    outputs, inputs = _ports_by(doc, "output"), _ports_by(doc, "input")
    if len(outputs) != 1 or not inputs:
        raise ValueError("출력 포트 1개·입력 포트 1개 이상인 doc 만: out=%r in=%r" % (outputs, inputs))
    link, first_in = outputs[0], inputs[0]
    rails = set(doc["supply_nets"])

    def net_fn(n):
        if n in rails:
            return n
        return link if n == first_in else n + suffix

    copy = map_element_names(map_nets(doc, net_fn), lambda name: name + suffix)
    out = dict(doc)
    for key in ELEMENT_LISTS:
        if key in doc:
            out[key] = list(doc[key]) + list(copy[key])
    ports = {k: v for k, v in doc["ports"].items() if k != link}
    ports.update((k, v) for k, v in copy["ports"].items() if k != link and not k.startswith(COMMENT_PREFIX))
    out["ports"] = ports
    return out, link
